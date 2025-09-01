# AI微波器件智能设计代理 (AI-Microwave-Agent)

基于LangChain和HFSS的智能微波器件设计、仿真与分析系统，集成多模态AI分析能力，为微波工程师提供端到端的自动化设计流程。

## 🚀 核心特性

### 🎯 智能器件设计
- **CSRR结构设计**: 互补开口谐振环(Complementary Split Ring Resonator)自动建模
- **SRR结构设计**: 开口谐振环(Split Ring Resonator)参数化设计
- **参数化建模**: 支持几何参数、材料属性、边界条件的智能配置
- **自动网格划分**: 基于结构特征的自适应网格生成

### ⚡ 高效仿真引擎
- **HFSS集成**: 深度集成Ansys HFSS 2024R2仿真引擎
- **智能扫频**: 支持Fast、Interpolating、Discrete多种扫频模式
- **自动收敛**: 智能收敛控制和迭代优化
- **并行计算**: 支持多核并行加速仿真

### 📊 专业结果分析
- **S参数分析**: 全面的散射参数分析(S11, S21, S12, S22)
- **VSWR计算**: 电压驻波比和匹配特性分析
- **关键指标提取**: 谐振频率、品质因子、带宽等关键参数自动提取
- **数据导出**: 支持CSV、JSON多格式数据导出

### 🔧 智能优化算法
- **遗传算法(GA)**: 基于自然选择和遗传机制的全局优化算法
- **粒子群优化(PSO)**: 模拟鸟群觅食行为的群体智能优化算法
- **蚁群算法(ACO)**: 基于蚂蚁觅食路径的启发式优化算法
- **模拟退火(SA)**: 模拟金属退火过程的概率性优化算法
- **多目标优化**: 支持S参数、VSWR、带宽等多个性能指标同时优化
- **参数化优化**: 自动调整几何参数以达到最佳性能指标

### 🤖 多模态AI分析
- **图像智能识别**: 基于Qwen VL Max和Gemini 2.5 Pro的仿真结果图像分析
- **专业报告生成**: 自动生成技术分析报告和优化建议
- **器件类型推断**: 根据S参数特征智能识别器件类型
- **Token使用统计**: 实时监控AI调用成本

## 📁 项目结构

```
AI-Microwave-Agent/
├── app/
│   └── agent_build.py          # LangChain对话入口和Agent核心
├── tools/                      # LangChain工具集
│   ├── csrr_tool.py           # CSRR结构设计工具
│   ├── srr_tool.py            # SRR结构设计工具
│   ├── sim_tools.py           # HFSS仿真执行工具
│   ├── result_analysis_tool.py # 仿真结果分析工具
│   ├── optimization_tool.py   # 智能优化工具
│   └── multimodal_analysis_tool.py # 多模态AI分析工具
├── scripts/                    # 底层PyAEDT脚本
│   ├── CSRR.py                # CSRR建模脚本
│   ├── setup.py               # 仿真设置脚本
│   └── result.py              # 结果处理脚本
├── pyaedt_scripts/            # PyAEDT设备和仿真脚本
│   ├── devices/               # 器件建模脚本
│   └── simulation/            # 仿真配置脚本
├── docs/                      # 详细使用文档
│   ├── multimodal_analysis_tool_usage.md
│   ├── result_analysis_tool_usage.md
│   └── simulation_tool_usage.md
├── config/
│   └── config.yaml            # 系统配置文件
├── results/                   # 仿真结果和分析报告
└── requirements.txt           # Python依赖包
```

## 🛠️ 环境准备

### 1. 软件依赖
- **Ansys Electronics Desktop (HFSS) 2024R2** - 电磁仿真引擎
- **Python 3.8+** - 推荐使用虚拟环境
- **Git** - 版本控制

### 2. Python环境配置
```bash
# 克隆项目
git clone <repository-url>
cd AI-Microwave-Agent

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. API密钥配置
创建 `.env` 文件并配置必要的API密钥：
```bash
# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1

# 多模态分析API配置
DASHSCOPE_API_KEY=your_dashscope_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. HFSS许可证配置
确保Ansys HFSS 2024R2已正确安装并配置好许可证。

## 🎯 快速开始

### 端到端设计流程示例

#### 1. 创建CSRR结构
```bash
python app/agent_build.py --input "请创建一个CSRR结构，外环外半径3.5mm，环宽度0.6mm，开口宽度0.2mm，内外环间距0.7mm，微带线宽度1.4mm"
```

#### 2. 执行仿真分析
```bash
python app/agent_build.py --input "请对刚创建的CSRR结构进行仿真，频率范围1-10GHz，步长0.01GHz，使用Fast扫频"
```

#### 3. 结果分析与可视化
```bash
python app/agent_build.py --input "提取S21与VSWR，并给我图和CSV路径，报告谐振点"
```

#### 4. AI智能分析
```bash
python app/agent_build.py --input "使用多模态AI分析刚生成的仿真结果图像，生成专业技术报告"
```

#### 5. 智能参数优化
```bash
python app/agent_build.py --input "使用遗传算法优化CSRR结构参数，目标是在2.4GHz获得最小S21和最大S11"
```

```bash
python app/agent_build.py --input "使用粒子群优化算法优化当前设计，优化目标包括S21小于-20dB，VSWR小于2"
```

```bash
python app/agent_build.py --input "使用遗传算法优化CSRR结构,启用ANN代理模型，优化变量：外环半径2-5mm，环宽度0.2-1mm，开口宽度0.1-0.5mm，目标：最大化S21参数，种群大小5，迭代3次"
```

### 高级使用示例

#### 指定项目路径仿真
```bash
python app/agent_build.py --input "对 C:/Users/<username>/Documents/Ansoft/CSRR_Project_xxx.aedt 执行仿真"
```

#### 自定义分析参数
```bash
python app/agent_build.py --input "分析S参数，计算1-5GHz频段的插入损耗和回波损耗，导出详细数据"
```

#### 多目标优化设计
```bash
python app/agent_build.py --input "使用遗传算法优化CSRR参数，种群大小50，迭代100次，目标频率2.4GHz，S21<-30dB，S11>-3dB"
```

#### 约束条件优化
```bash
python app/agent_build.py --input "使用粒子群优化算法，优化外环半径在2-5mm范围内，环宽度0.3-1.0mm，目标VSWR<1.5"
```

## 🔧 配置说明

### config.yaml 配置文件
```yaml
defaults:
  aedt_version: "2024.2"        # AEDT版本
  non_graphical: false          # 是否使用非图形模式
  new_desktop: false            # 是否创建新的Desktop实例
  results_dir: "results"        # 结果输出目录

sim:
  setup_name: "MainSetup"       # 默认分析设置名称
  sweep_name: "BroadbandSweep"  # 默认扫频名称
  start_ghz: 1.0               # 默认起始频率(GHz)
  stop_ghz: 10.0               # 默认截止频率(GHz)
  step_ghz: 0.001              # 默认频率步长(GHz)
```

## 📚 详细文档

- [多模态分析工具使用指南](docs/multimodal_analysis_tool_usage.md)
- [仿真结果分析工具使用指南](docs/result_analysis_tool_usage.md)
- [HFSS仿真工具使用指南](docs/simulation_tool_usage.md)

## 🎨 主要工具介绍

### CREATE_CSRR - CSRR结构设计工具
- 参数化CSRR几何建模
- 自动材料和边界条件设置
- 智能网格划分
- 支持多层基板结构

### CREATE_SRR - SRR结构设计工具
- SRR几何参数化设计
- 灵活的开口配置
- 自适应仿真区域设置

### RUN_SIM - 仿真执行工具
- 智能项目管理和锁定处理
- 多种扫频模式支持
- 实时仿真进度监控
- 自动收敛控制

### ANALYZE_RESULTS - 结果分析工具
- 全面的S参数分析
- VSWR和匹配特性计算
- 关键性能指标提取
- 多格式数据导出

### MULTIMODAL_ANALYSIS - 多模态AI分析工具
- 基于Qwen VL Max和Gemini 2.5 Pro的图像分析
- 智能器件类型识别
- 专业技术报告生成
- 优化建议和改进方案

### OPTIMIZE_DESIGN - 智能优化工具
- 多种优化算法支持(GA、PSO、ACO、SA)
- 自动HFSS项目检测和参数提取
- 多目标优化(S参数、VSWR、带宽等)
- 实时优化进度监控和结果可视化
- 详细优化报告和参数推荐
- 支持用户自定义优化目标和约束条件

## 🔍 技术特点

### 智能化程度高
- 自然语言交互界面
- 智能参数推荐
- 自动错误检测和修复
- 上下文感知的对话系统

### 专业性强
- 基于工程实践的分析算法
- 符合IEEE标准的参数计算
- 专业级图表和报告生成
- 工业级精度和可靠性

### 扩展性好
- 模块化工具架构
- 标准LangChain接口
- 易于添加新的器件类型
- 支持自定义分析算法

## 🚨 注意事项

1. **HFSS许可证**: 确保有效的HFSS许可证，建议使用网络许可证以避免冲突
2. **内存要求**: 复杂结构仿真需要充足的内存，推荐16GB以上
3. **API配额**: 多模态分析功能需要消耗API配额，请合理使用
4. **文件路径**: Windows系统请使用正斜杠或双反斜杠表示路径
5. **版本兼容**: 当前版本针对HFSS 2024R2优化，其他版本可能需要调整

## 🔮 发展路线

### 近期计划
- [ ] 支持更多微波器件类型(贴片天线、巴伦，匹配电路，双工器，衰减器等)
- [x] 集成优化算法(遗传算法、粒子群优化、蚁群算法、模拟退火等)
- [ ] 增加实时仿真监控界面
- [ ] 支持批量设计和参数扫描
- [ ] 增强优化算法性能和收敛速度

### 长期规划
- [ ] 机器学习辅助设计
- [ ] 云端仿真支持
- [ ] 多物理场耦合分析
- [ ] 工艺容差分析

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目！

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request


## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者

---

**让AI赋能微波设计，让仿真更加智能！** 🚀
