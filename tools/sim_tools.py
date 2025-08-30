\
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool

from ansys.aedt.core import Hfss

# We re-use your setup helpers
from scripts.setup import setup_hfss_analysis, setup_frequency_sweep  # noqa

class RunSimOptions(BaseModel):
    project_file: str = Field(..., description="*.aedt 工程文件路径")
    setup_name: str = Field("MainSetup", description="分析设置名称")
    sweep_name: str = Field("BroadbandSweep", description="扫频名称")
    non_graphical: bool = Field(False, description="是否以无图形方式运行")

def run_hfss_simulation(opts: RunSimOptions) -> Dict[str, Any]:
    """
    打开指定工程，确保存在Setup/Sweep，运行求解。
    """
    proj = Path(opts.project_file)
    if not proj.exists():
        raise FileNotFoundError(f"工程不存在: {proj}")

    hfss = None
    try:
        hfss = Hfss(project=str(proj), non_graphical=opts.non_graphical, new_desktop=False)
        # Ensure setup & sweep
        setup = setup_hfss_analysis(hfss, setup_name=opts.setup_name)
        sweep = setup_frequency_sweep(hfss, setup_name=opts.setup_name, sweep_name=opts.sweep_name)
        # Analyze
        try:
            hfss.analyze_setup(opts.setup_name)
        except Exception:
            hfss.analyze()
        hfss.save_project()
        return {
            "message": "Simulation completed",
            "project_file": str(proj),
            "setup": opts.setup_name,
            "sweep": opts.sweep_name,
        }
    finally:
        if hfss:
            # keep open for inspection; set to True to fully close
            hfss.release_desktop(close_projects=False, close_desktop=False)

RUN_SIM = StructuredTool.from_function(
    name="run_hfss_simulation",
    description="对给定工程运行HFSS仿真并保存工程（会自动创建/更新Setup与Sweep）",
    func=lambda **kwargs: run_hfss_simulation(RunSimOptions(**kwargs)),
    args_schema=RunSimOptions,
)
