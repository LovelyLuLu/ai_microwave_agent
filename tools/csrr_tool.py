\
from __future__ import annotations
import os, re, json, subprocess, sys, time
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool

class BuildCSRROptions(BaseModel):
    target_freq_ghz: float = Field(2.45, description="目标工作频率（用于记录；当前建模脚本未自动尺寸合成）")
    substrate: str = Field("RO4350B", description="基板材料（当前脚本里默认FR4，可后续在建模中替换）")
    aedt_version: Optional[str] = Field(None, description="覆盖建模脚本中的 AEDT 版本")
    non_graphical: Optional[bool] = Field(None, description="以无图形方式运行")
    new_desktop: Optional[bool] = Field(None, description="是否新开桌面会话")

def _run_python(script_path: Path, env: dict | None = None) -> str:
    """Run a python script and return stdout as text."""
    proc = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, env=env)
    if proc.returncode != 0:
        raise RuntimeError(f"CSRR builder failed ({proc.returncode}). stderr:\n{proc.stderr}")
    return proc.stdout

def build_csrr_project(opts: BuildCSRROptions) -> Dict[str, Any]:
    """
    调用 scripts/CSRR.py 构建一个 CSRR 工程，并解析输出获取工程路径与设计名。
    返回 JSON 可序列化字典。
    """
    script = Path(__file__).resolve().parents[1] / "scripts" / "CSRR.py"
    if not script.exists():
        raise FileNotFoundError(f"脚本不存在: {script}")

    env = os.environ.copy()
    # 可选：通过环境变量影响脚本（当前CSRR.py未读取这些值；后续可在脚本中加读取）
    if opts.aedt_version:
        env["AEDT_VERSION"] = opts.aedt_version
    if opts.non_graphical is not None:
        env["AEDT_NON_GRAPHICAL"] = "1" if opts.non_graphical else "0"
    if opts.new_desktop is not None:
        env["AEDT_NEW_DESKTOP"] = "1" if opts.new_desktop else "0"

    out = _run_python(script, env)
    # 解析输出
    proj_file = None
    design_name = None
    project_name = None

    m = re.search(r"项目已保存:\s*(.+)", out)
    if m:
        proj_file = m.group(1).strip()
    m = re.search(r"设计名称:\s*(.+)", out)
    if m:
        design_name = m.group(1).strip()
    m = re.search(r"项目名称:\s*(.+)", out)
    if m:
        project_name = m.group(1).strip()

    return {
        "message": "CSRR project created via scripts/CSRR.py",
        "project_file": proj_file,
        "project_dir": str(Path(proj_file).parent if proj_file else ""),
        "project_name": project_name,
        "design_name": design_name,
        "target_freq_ghz": opts.target_freq_ghz,
        "notes": "如需根据目标频率自动合成尺寸，可在建模脚本中加入尺寸合成逻辑。"
    }

CREATE_CSRR = StructuredTool.from_function(
    name="create_csrr_hfss_project",
    description="创建一个CSRR工程（调用 scripts/CSRR.py），返回工程路径和设计名等信息。",
    func=lambda **kwargs: build_csrr_project(BuildCSRROptions(**kwargs)),
    args_schema=BuildCSRROptions,
)
