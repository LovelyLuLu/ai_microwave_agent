\
from __future__ import annotations
import os, re, subprocess, sys
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool

class BuildSRROptions(BaseModel):
    target_freq_ghz: float = Field(2.45, description="目标频率（记录用）")
    aedt_version: Optional[str] = None
    non_graphical: Optional[bool] = None
    new_desktop: Optional[bool] = None

def _run_python(script_path: Path, env: dict | None = None) -> str:
    proc = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, env=env)
    if proc.returncode != 0:
        raise RuntimeError(f"SRR builder failed ({proc.returncode}). stderr:\n{proc.stderr}")
    return proc.stdout

def build_srr_project(opts: BuildSRROptions) -> Dict[str, Any]:
    script = Path(__file__).resolve().parents[1] / "scripts" / "SRR.py"
    if not script.exists():
        raise FileNotFoundError(f"脚本不存在: {script}")
    env = os.environ.copy()
    if opts.aedt_version:
        env["AEDT_VERSION"] = opts.aedt_version
    if opts.non_graphical is not None:
        env["AEDT_NON_GRAPHICAL"] = "1" if opts.non_graphical else "0"
    if opts.new_desktop is not None:
        env["AEDT_NEW_DESKTOP"] = "1" if opts.new_desktop else "0"

    out = _run_python(script, env)
    proj_file = None
    design_name = None
    project_name = None

    import re
    m = re.search(r"项目已保存:\s*(.+)", out)
    if m: proj_file = m.group(1).strip()
    m = re.search(r"设计名称:\s*(.+)", out)
    if m: design_name = m.group(1).strip()
    m = re.search(r"项目名称:\s*(.+)", out)
    if m: project_name = m.group(1).strip()

    return {
        "message": "SRR project created via scripts/SRR.py",
        "project_file": proj_file,
        "project_dir": str(Path(proj_file).parent if proj_file else ""),
        "project_name": project_name,
        "design_name": design_name,
        "target_freq_ghz": opts.target_freq_ghz,
    }

CREATE_SRR = StructuredTool.from_function(
    name="create_srr_hfss_project",
    description="创建一个SRR工程（调用 scripts/SRR.py），返回工程路径和设计名等信息。",
    func=lambda **kwargs: build_srr_project(BuildSRROptions(**kwargs)),
    args_schema=BuildSRROptions,
)
