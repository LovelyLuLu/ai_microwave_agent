# AI-Microwave-Agent (最小可用骨架)

## 1) 准备
- 安装 Ansys Electronics Desktop (HFSS) 2024R2，并配置好授权
- Python 虚拟环境中安装依赖：
```bash
pip install -r requirements.txt
```
- 将你的 OPENAI_API_KEY 写入 `.env`（参考 `.env.example`）

## 2) 目录
```
AI-Microwave-Agent/
  app/agent_build.py        # LangChain 对话入口（CLI）
  tools/                    # 工具封装层
  scripts/                  # 你的原始 PyAEDT 脚本（已复制）
  config/config.yaml
  results/
```

## 3) 端到端最小验证
### 创建工程
```bash
python -m app.agent_build --input "请创建一个 2.45GHz 的 CSRR（RO4350B），并告诉我工程路径"
```
### 跑仿真
```bash
python -m app.agent_build --input "对上一个工程执行仿真"
```
或显式指定：
```bash
python -m app.agent_build --input "对 C:/Users/<you>/Documents/Ansoft/CSRR_Project_xxx.aedt 执行仿真"
```
### 看结果
```bash
python -m app.agent_build --input "提取 S21 与 VSWR，并给我图和CSV路径，报告谐振点"
```

## 4) 注意事项
- 当前建模调用的是 `scripts/CSRR.py` / `scripts/SRR.py` 作为独立进程执行；其内部会打开/保存HFSS工程。
- 仿真阶段使用 `scripts/setup.py` 的 `setup_hfss_analysis` 与 `setup_frequency_sweep` 来保证 Setup/Sweep 存在；随后调用 `analyze_setup`。
- 结果分析阶段使用 `scripts/result.py` 的各个函数，输出在 `results/<工程名>/`。

## 5) 下一步
- 将 `CSRR.py / SRR.py` 重构为函数式接口（而非脚本顶层执行），使工具可直接在同一会话内建模 -> 仿真 -> 后处理，避免多进程。
- 在建模阶段根据目标频率自动合成几何尺寸（闭环优化）。
