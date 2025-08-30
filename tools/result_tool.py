\
from __future__ import annotations
import os, json
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool

import numpy as np
from ansys.aedt.core import Hfss
from scripts.result import get_hfss_solution_data, plot_s_parameters, plot_vswr, export_data_to_csv, export_data_to_json  # noqa

class AnalyzeOptions(BaseModel):
    project_file: str = Field(..., description="*.aedt 工程文件路径")
    setup_name: str = Field("MainSetup", description="分析设置名称")
    sweep_name: str = Field("BroadbandSweep", description="扫频名称")
    s_params: List[str] = Field(default_factory=lambda: ["S(1,1)", "S(2,1)"], description="要提取的S参数")
    export_csv: bool = True
    export_json: bool = True
    export_png: bool = True

def _ensure_dir(p: Path): 
    p.mkdir(parents=True, exist_ok=True)

def _find_resonance(freq, mag_db):
    # 简单求最小点（例如对 |S21|dB 取最小值）
    idx = int(np.argmin(mag_db))
    return float(freq[idx]), float(mag_db[idx]), int(idx)

def analyze_hfss_results(opts: AnalyzeOptions) -> Dict[str, Any]:
    proj = Path(opts.project_file)
    if not proj.exists():
        raise FileNotFoundError(f"工程不存在: {proj}")

    out_dir = Path(__file__).resolve().parents[1] / "results" / Path(proj).stem
    _ensure_dir(out_dir)

    hfss = None
    try:
        hfss = Hfss(project=str(proj), non_graphical=True, new_desktop=False)
        solution_data = get_hfss_solution_data(hfss, opts.setup_name, opts.sweep_name, opts.s_params)
        if solution_data is None:
            raise RuntimeError("未能提取到仿真数据")

        # 导出
        plots = {}
        if opts.export_png:
            for s in opts.s_params:
                png = out_dir / f"{s.replace('(', '_').replace(',', '_').replace(')', '')}.png"
                plot_s_parameters(solution_data, s, file_path=str(png))
                plots[s] = str(png)
            vswr_png = out_dir / "VSWR.png"
            plot_vswr(solution_data, ["S(1,1)", "S(2,2)"], file_path=str(vswr_png))
            plots["VSWR"] = str(vswr_png)

        csv_path = json_path = None
        if opts.export_csv:
            csv_path = out_dir / "s_params.csv"
            export_data_to_csv(solution_data, str(csv_path))
        if opts.export_json:
            json_path = out_dir / "s_params.json"
            export_data_to_json(solution_data, str(json_path))

        # 计算谐振点（以S(2,1)为例，若存在）
        metrics = {}
        if "S(2,1)" in opts.s_params:
            freq = np.array(solution_data.primary_sweep_values, dtype=float)
            mag = np.sqrt(np.array(solution_data.data_real("S(2,1)"))**2 + np.array(solution_data.data_imag("S(2,1)"))**2)
            mag_db = 20*np.log10(mag + 1e-12)
            f0, s21_min_db, idx = _find_resonance(freq, mag_db)
            metrics["resonance_S21_min_db"] = s21_min_db
            metrics["resonance_freq_ghz"] = f0

        return {
            "message": "Results analyzed",
            "project_file": str(proj),
            "plots": plots,
            "csv": str(csv_path) if csv_path else None,
            "json": str(json_path) if json_path else None,
            "metrics": metrics,
        }
    finally:
        if hfss:
            hfss.release_desktop(close_projects=False, close_desktop=False)

ANALYZE_RESULTS = StructuredTool.from_function(
    name="analyze_hfss_results",
    description="提取S参数/VSWR，导出CSV/JSON/PNG，并计算谐振点等关键指标。",
    func=lambda **kwargs: analyze_hfss_results(AnalyzeOptions(**kwargs)),
    args_schema=AnalyzeOptions,
)
