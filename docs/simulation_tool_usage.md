# HFSS仿真工具使用指南

## 概述

本文档介绍如何使用新创建的HFSS仿真工具(`RUN_SIM`)对已创建的微波器件项目进行仿真分析。

## 工具功能

### 主要特性
- 自动查找并连接到最新创建的HFSS项目文件
- 配置分析设置（最大迭代次数、收敛误差等）
- 设置频率扫描参数（起始频率、截止频率、步长等）
- 支持多种扫频类型（Fast、Interpolating、Discrete）
- 实时进度监控
- 自动保存项目

### 适用场景
- 对SRR/CSRR结构进行S参数分析
- 频域响应特性仿真
- 谐振频率和品质因子计算
- 传输特性和反射特性分析

## 参数说明

### 必需参数
| 参数名 | 类型 | 描述 | 示例 |
|--------|------|------|------|
| `start_freq` | float | 扫频起始频率 (GHz) | 1.0 |
| `stop_freq` | float | 扫频截止频率 (GHz) | 10.0 |
| `step_freq` | float | 频率步长 (GHz) | 0.01 |

### 可选参数（有默认值）
| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `sweep_name` | str | "BroadbandSweep" | 扫频名称 |
| `sweep_type` | str | "Interpolating" | 扫频类型 |
| `max_passes` | int | 30 | 最大迭代次数 |
| `delta_s` | float | 0.02 | 收敛误差 |
| `setup_name` | str | "MainSetup" | 分析设置名称 |
| `project_name_prefix` | str | "CSRR_Project" | 项目名称前缀 |
| `non_graphical` | bool | False | 是否以非图形模式运行 |

## 使用示例

### 基本使用
```python
from tools.sim_tools import RUN_SIM

# 基本仿真（只需要必需参数）
result = RUN_SIM._run(
    start_freq=1.0,
    stop_freq=10.0,
    step_freq=0.01
)
print(result)
```

### 高级使用
```python
# 自定义仿真参数
result = RUN_SIM._run(
    start_freq=2.0,
    stop_freq=8.0,
    step_freq=0.005,
    sweep_name="HighResSweep",
    sweep_type="Fast",
    max_passes=50,
    delta_s=0.01,
    setup_name="CustomSetup"
)
print(result)
```

### 通过Agent调用
当通过AI Agent调用时，可以使用自然语言描述：

```
用户: "请对刚创建的CSRR结构进行仿真，频率范围1-10GHz，步长0.01GHz"

Agent会自动调用RUN_SIM工具，参数如下：
- start_freq: 1.0
- stop_freq: 10.0  
- step_freq: 0.01
- 其他参数使用默认值
```

## 扫频类型说明

| 类型 | 描述 | 适用场景 |
|------|------|----------|
| **Fast** | 快速扫频，计算速度快但精度较低 | 初步分析、快速预览 |
| **Interpolating** | 插值扫频，平衡速度和精度 | 一般分析（推荐） |
| **Discrete** | 离散扫频，精度最高但速度慢 | 精确分析、最终结果 |

## 工作流程

1. **项目查找**: 工具会自动在用户文档目录下查找最新创建的AEDT项目文件
2. **连接项目**: 连接到找到的HFSS项目
3. **配置分析**: 创建或更新分析设置
4. **配置扫频**: 创建或更新频率扫描设置
5. **执行仿真**: 启动仿真分析
6. **进度监控**: 实时显示仿真进度
7. **保存项目**: 仿真完成后自动保存项目

## 输出结果

成功执行后，工具会返回包含以下信息的字符串：

```
HFSS仿真分析完成！
项目名称: CSRR_Project_20240115_143022
设计名称: CSRR_Design
分析设置: MainSetup
扫频设置: BroadbandSweep
仿真用时: 125.67 秒
状态: 仿真完成，用时 125.67 秒
```

## 错误处理

常见错误及解决方案：

### 1. 项目文件未找到
```
错误: 未能找到最新的项目文件
```
**解决方案**: 确保已经使用CREATE_SRR或CREATE_CSRR工具创建了项目

### 2. 参数验证失败
```
错误: 1 validation error for SimulationParams
start_freq: Input should be greater than 0
```
**解决方案**: 检查输入参数是否符合要求（频率必须大于0）

### 3. HFSS连接失败
```
错误: 严重错误: 无法连接到HFSS
```
**解决方案**: 确保ANSYS Electronics Desktop已安装且可用

## 最佳实践

1. **频率范围选择**: 根据器件特性选择合适的频率范围，避免过宽或过窄
2. **步长设置**: 平衡仿真精度和计算时间，一般建议步长为频率范围的1/1000
3. **收敛设置**: 对于精确分析，可以降低delta_s值（如0.01）并增加max_passes
4. **扫频类型**: 初步分析使用Fast，最终结果使用Interpolating或Discrete
5. **监控进度**: 仿真过程中注意观察进度信息，及时发现问题

## 与其他工具的配合使用

### 完整工作流程
1. **设计阶段**: 使用`CREATE_SRR`或`CREATE_CSRR`创建器件模型
2. **仿真阶段**: 使用`RUN_SIM`进行仿真分析 ← **本工具**
3. **分析阶段**: 使用`ANALYZE_RESULTS`提取和分析仿真结果

### 示例对话流程
```
用户: "创建一个CSRR结构"
Agent: [调用CREATE_CSRR] → "CSRR结构已创建，需要现在开始仿真吗？"

用户: "是的，仿真频率范围1-10GHz"
Agent: [调用RUN_SIM] → "仿真已完成，需要分析结果吗？"

用户: "分析S参数"
Agent: [调用ANALYZE_RESULTS] → "S参数分析完成，结果已导出"
```

## 技术细节

### 依赖库
- `ansys.aedt.core`: PyAEDT核心库
- `pydantic`: 参数验证
- `langchain`: 工具框架
- `threading`: 多线程支持
- `numpy`: 数值计算（间接依赖）

### 文件结构
```
tools/
├── sim_tools.py          # 仿真工具主文件
├── srr_tool.py          # SRR创建工具
├── csrr_tool.py         # CSRR创建工具
└── result_tool.py       # 结果分析工具
```

### 监控功能
工具内置了实时进度监控功能，包括：
- 仿真状态检查
- 网格信息显示
- 运行时间统计
- 详细进度报告

## 故障排除

如果遇到问题，请按以下步骤排查：

1. **检查环境**: 确保ANSYS Electronics Desktop已正确安装
2. **检查项目**: 确认项目文件存在且可访问
3. **检查参数**: 验证所有输入参数的有效性
4. **查看日志**: 注意仿真过程中的错误信息
5. **重启AEDT**: 如果连接问题持续，尝试重启ANSYS Electronics Desktop

---

*本文档随工具更新而更新，如有疑问请参考源代码或联系开发团队。*