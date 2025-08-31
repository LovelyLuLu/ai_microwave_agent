# 多模态仿真结果图像分析工具使用指南

## 概述

多模态仿真结果图像分析工具是一个基于LangChain框架的专业工具，支持多种先进的多模态大模型对HFSS仿真结果图像进行智能分析。该工具能够自动识别和分析S参数图像、VSWR图像等仿真结果，生成详细的专业分析报告。

## 支持的模型

### 模型配置

工具支持两种多模态大模型：

1. **Qwen VL Max** (默认)
   - 阿里云通义千问视觉语言模型
   - 需要配置 `DASHSCOPE_API_KEY`
   - 性能稳定，响应速度快

2. **Gemini 2.0 Flash Exp**
   - Google最新的多模态模型
   - 需要配置 `GEMINI_API_KEY`
   - 分析能力强，支持复杂推理

**切换模型方法**：

在 `multimodal_analysis_tool.py` 文件的 `call_multimodal_model` 函数中修改 `model_name` 变量：

```python
# 使用Qwen模型（默认）
model_name = "qwen-vl-max"

# 切换到Gemini模型
model_name = "gemini-2.0-flash-exp"
```

## 主要功能

### 1. 智能图像识别
- 自动识别S参数图像（S11, S21, S12, S22）
- 自动识别VSWR图像
- 支持PNG、JPG、JPEG格式

### 2. 专业分析报告
- S参数性能分析（回波损耗、插入损耗、谐振频率等）
- VSWR特性分析
- 器件性能评估和设计建议
- 技术结论和改进方向
- 关键性能指标（KPI）摘要表

### 3. Token使用量统计
- 实时统计输入、输出和总Token数量
- 成本监控和使用追踪
- 报告中记录Token使用信息

### 4. 多格式输出
- Markdown格式报告
- JSON格式数据
- 自动保存到文件

## 环境配置

### 1. 安装依赖
```bash
pip install dashscope google-generativeai langchain pydantic python-dotenv
```

### 2. 环境变量配置
在项目根目录创建 `.env` 文件：

```env
# Qwen VL Max模型配置
DASHSCOPE_API_KEY=your_dashscope_api_key

# Gemini模型配置
GEMINI_API_KEY=your_gemini_api_key
```

## 使用方法

### 1. 基本使用（默认Qwen模型）
```python
from tools.multimodal_analysis_tool import MULTIMODAL_ANALYSIS

# 使用默认配置
result = MULTIMODAL_ANALYSIS._run('{}')
print(result)
```

### 2. 完整参数配置
```python
from tools.multimodal_analysis_tool import MULTIMODAL_ANALYSIS

# 完整配置
result = MULTIMODAL_ANALYSIS._run('{
    "results_dir": "results",
    "include_s_parameters": true,
    "include_vswr": true,
    "output_format": "markdown",
    "save_report": true,
    "report_filename": "custom_analysis_report"
}')
print(result)
```

## 参数说明

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `results_dir` | string | "results" | 仿真结果图像文件夹路径 |
| `include_s_parameters` | boolean | true | 是否分析S参数图像 |
| `include_vswr` | boolean | true | 是否分析VSWR图像 |
| `output_format` | string | "markdown" | 报告输出格式 |
| `save_report` | boolean | true | 是否保存报告到文件 |
| `report_filename` | string | null | 自定义报告文件名 |

## 输出示例

### 终端输出
```
正在调用gemini-2.0-flash-exp模型分析 5 张图像...
成功加载图像: S_1_1.png
成功加载图像: S_2_1.png
成功加载图像: S_1_2.png
成功加载图像: S_2_2.png
成功加载图像: VSWR.png

=== 多模态仿真结果图像分析报告 ===

📊 分析统计:
- 分析图像总数: 5
- S参数图像: 4 张
- VSWR图像: 1 张
- 使用模型: gemini-2.0-flash-exp

💰 Token使用量:
- 输入Token: 2668
- 输出Token: 1646
- 总Token: 4314

📄 分析报告已保存至: results/multimodal_analysis_report_20250831_190245.md

[详细分析报告内容...]
```

### 报告文件示例
```markdown
# 多模态仿真结果图像分析报告

**生成时间**: 2025-08-31T19:02:45.123456
**使用模型**: gemini-2.0-flash-exp
**分析图像数量**: 5

## Token使用量统计
- **输入Token**: 2668
- **输出Token**: 1646
- **总Token**: 4314

## 关键性能指标（KPI）摘要表
| 指标 | S11 | S21 | S12 | S22 | VSWR |
|------|-----|-----|-----|-----|------|
| 最小值(dB) | -25.3 | -0.8 | -45.2 | -23.1 | 1.12 |
| 工作频率(GHz) | 2.4-2.5 | 2.4-2.5 | 2.4-2.5 | 2.4-2.5 | 2.4-2.5 |

[详细分析内容...]
```

## 模型对比

### Qwen VL Max vs Gemini 2.0 Flash Exp

| 特性 | Qwen VL Max | Gemini 2.0 Flash Exp |
|------|-------------|----------------------|
| **响应速度** | 快 | 非常快 |
| **中文支持** | 优秀 | 良好 |
| **技术分析** | 专业 | 专业 |
| **成本** | 中等 | 较低 |
| **稳定性** | 高 | 高 |

### 选择建议

- **推荐Qwen VL Max**：需要中文技术报告，对分析深度要求高
- **推荐Gemini 2.0 Flash Exp**：需要快速响应，成本敏感的场景

### 切换方法

在代码中修改模型配置：
```python
# 在 multimodal_analysis_tool.py 的 call_multimodal_model 函数中
model_name = "qwen-vl-max"          # 使用Qwen模型
# model_name = "gemini-2.0-flash-exp"  # 切换到Gemini模型
```

## 故障排除

### 1. 模型调用失败
- 检查API密钥是否正确配置
- 确认网络连接正常
- 验证模型名称拼写正确

### 2. 图像加载失败
- 确认图像文件存在且格式支持
- 检查文件路径是否正确
- 验证图像文件未损坏

### 3. 依赖包问题
```bash
# 重新安装依赖
pip install --upgrade dashscope google-generativeai
```

## 更新日志

### v2.1.0 (2025-01-31)
- ✅ 简化模型配置方式
- ✅ 移除参数中的model_name字段
- ✅ 改为代码内直接配置模型
- ✅ 更新使用文档和示例
- ✅ 优化用户体验

### v2.0.0 (2025-01-31)
- ✅ 新增Gemini 2.0 Flash Exp模型支持
- ✅ 实现多模型选择功能
- ✅ 优化Token使用量统计
- ✅ 改进错误处理和日志输出
- ✅ 更新文档和使用指南

### v1.0.0 (2025-01-30)
- ✅ 初始版本发布
- ✅ 支持Qwen VL Max模型
- ✅ 实现S参数和VSWR图像分析
- ✅ 生成专业分析报告
- ✅ 支持Markdown和JSON输出格式

## 技术支持

如有问题或建议，请联系开发团队或提交Issue。