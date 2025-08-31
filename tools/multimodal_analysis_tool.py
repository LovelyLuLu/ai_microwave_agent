"""多模态仿真结果图像分析工具
基于多模态大模型qwen_vl_max的LangChain工具实现
提供仿真结果图像识别和分析报告生成功能
"""

import os
import json
import base64
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
import dashscope
from dashscope import MultiModalConversation
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化DashScope API
def initialize_dashscope():
    """初始化DashScope API配置"""
    api_key = os.getenv('DASHSCOPE_API_KEY')
    if not api_key:
        raise Exception("未找到DASHSCOPE_API_KEY环境变量，请在.env文件中配置")
    dashscope.api_key = api_key


class MultimodalAnalysisParams(BaseModel):
    """多模态图像分析参数"""
    
    # 输入参数
    results_dir: str = Field(
        default="results",
        description="仿真结果图像文件夹路径，默认为results文件夹"
    )
    
    # 分析选项
    include_s_parameters: bool = Field(
        default=True,
        description="是否分析S参数图像（S11, S21, S12, S22）"
    )
    include_vswr: bool = Field(
        default=True,
        description="是否分析VSWR图像"
    )
    
    # 输出选项
    output_format: str = Field(
        default="markdown",
        description="报告输出格式，支持markdown或json"
    )
    save_report: bool = Field(
        default=True,
        description="是否保存分析报告到文件"
    )
    report_filename: Optional[str] = Field(
        default=None,
        description="报告文件名，如果为None则自动生成"
    )


def encode_image_to_base64(image_path: str) -> str:
    """将图像文件编码为base64格式
    
    Args:
        image_path: 图像文件路径
        
    Returns:
        base64编码的图像字符串
    """
    try:
        with open(image_path, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_string
    except Exception as e:
        raise Exception(f"图像编码失败: {str(e)}")


def find_simulation_images(results_dir: str) -> Dict[str, List[str]]:
    """查找仿真结果图像文件
    
    Args:
        results_dir: 结果文件夹路径
        
    Returns:
        按类型分类的图像文件路径字典
    """
    results_path = Path(results_dir)
    if not results_path.exists():
        raise FileNotFoundError(f"结果文件夹不存在: {results_dir}")
    
    # 定义图像类型和对应的文件名模式
    image_patterns = {
        's_parameters': ['S_1_1.png', 'S_2_1.png', 'S_1_2.png', 'S_2_2.png'],
        'vswr': ['VSWR.png']
    }
    
    found_images = {
        's_parameters': [],
        'vswr': []
    }
    
    # 查找S参数图像
    for pattern in image_patterns['s_parameters']:
        image_path = results_path / pattern
        if image_path.exists():
            found_images['s_parameters'].append(str(image_path))
    
    # 查找VSWR图像
    for pattern in image_patterns['vswr']:
        image_path = results_path / pattern
        if image_path.exists():
            found_images['vswr'].append(str(image_path))
    
    return found_images


def generate_analysis_prompt() -> str:
    """生成多模态分析的提示词模板
    
    Returns:
        分析提示词字符串
    """
    prompt = """
你是一位顶级的微波工程专家和HFSS仿真大师，拥有超过20年的复杂电磁问题分析经验。你的任务是基于提供的HFSS仿真结果图像，生成一份全面、深度、专业的分析报告，不仅要解读数据，更要提供富有洞察力的工程见解。

**分析原则**:
- **精准**: 所有数据读取必须精确，分析必须严谨。
- **深度**: 超越表面现象，揭示设计背后的物理意义和性能瓶颈。
- **专业**: 使用行业标准术语，展现专家级的知识和经验。
- **价值**: 提供切实可行、具有高工程价值的优化建议。

请严格按照以下结构和要求进行分析：

---

### **报告标题: HFSS仿真结果多模态深度分析报告**

---

### **1. 核心性能指标 (KPI) 摘要**
以表格形式汇总关键性能指标，提供快速概览。
| 性能指标 | 数值 | 频率 | 评估 |
| :--- | :--- | :--- | :--- |
| **最小回波损耗 (S11)** | (dB) | (GHz) | (优/良/中/差) |
| **-10dB 带宽** | (MHz/GHz) | (GHz) | (宽/中/窄) |
| **中心频率** | (GHz) | - | - |
| **最小插入损耗 (S21)** | (dB) | (GHz) | (优/良/中/差) |
| **通带平坦度** | (dB) | (GHz) | (优/良/中/差) |
| **VSWR < 2 的带宽** | (MHz/GHz) | (GHz) | (宽/中/窄) |
| **VSWR 最小值** | - | (GHz) | (优/良/中/差) |

---

### **2. 图像识别与仿真设置分析**
- **图像类型识别**: 准确识别每张图对应的参数（S11, S21, S12, S22, VSWR等）。
- **仿真频率范围**: 明确报告仿真的起始和终止频率。
- **坐标轴解读**: 确认X轴和Y轴的单位、刻度和范围，并评估其合理性。
- **数据质量评估**: 检查曲线的平滑度、连续性，判断是否存在仿真噪声或收敛问题。

---

### **3. S参数深度分析**

#### **3.1 反射/匹配性能 (S11, S22)**
- **回波损耗 (Return Loss)**:
  - **谐振点分析**: 精确读取谐振频率和对应的最小回波损耗值。
  - **带宽评估**: 计算并报告-10dB和-3dB带宽，并评估其相对带宽（带宽/中心频率）。
  - **带外抑制**: 分析工作频带之外的抑制性能。
- **匹配效率**:
  - 结合Smith圆图（如果可用）或基于S11数据，评估输入阻抗与系统阻抗（通常为50Ω）的匹配程度。

#### **3.2 传输/插入损耗性能 (S21, S12)**
- **插入损耗 (Insertion Loss)**:
  - **通带分析**: 读取通带内的最小、最大和平均插入损耗。评估通带平坦度。
  - **阻带分析**: 评估阻带的抑制深度和滚降速率。
- **隔离度 (Isolation)**: 如果是多端口器件，分析端口间的隔离度。
- **对称性与互易性**: 比较S21和S12曲线，评估器件的对称性和是否满足互易性。

---

### **4. VSWR 分析**
- **匹配带宽**:
  - **VSWR < 2**: 识别并报告此范围的频率带宽，这是大多数应用的最低要求。
  - **VSWR < 1.5**: 识别并报告此范围的频率带宽，代表高性能匹配。
- **频率特性**: 分析VSWR随频率变化的趋势，识别其最小值点和对应的频率。

---

### **5. 器件类型推断与性能评估**
- **器件类型判断**: 基于S参数的“指纹”特征，推断最可能的器件类型（例如：带通滤波器、低通滤波器、带阻滤波器、天线、耦合器、功分器等），并解释判断依据。
- **性能等级评估**:
  - **行业基准比较**: 将关键性能与该类型器件的行业典型指标进行比较。
  - **应用符合性**: 评估其是否满足特定应用（如5G、Wi-Fi、卫星通信等）的要求。
- **设计优缺点分析**:
  - **优点**: 总结该设计的突出优点（如：低损耗、宽带宽、高抑制等）。
  - **潜在问题**: 指出设计中可能存在的性能瓶颈或需要关注的问题。

---

### **6. 工程优化建议**
- **具体优化方向**:
  - **尺寸调整**: 提出具体的物理结构（如：谐振器长度、耦合间隙、馈线宽度等）调整建议，并说明其对性能的预期影响。
  - **材料选择**: 建议是否可以更换基板材料以改善性能（如：降低损耗、提高功率容量）。
- **进一步仿真建议**: 建议进行哪些额外的仿真分析（如：参数扫描、公差分析、场分布分析）来进一步验证和优化设计。

---

### **7. 结论与展望**
- **综合评估**: 对设计的整体性能给出一个明确、中肯的综合评价。
- **应用前景**: 评估该设计在实际工程应用中的潜力和价值。
- **创新性评估**: 简要评估该设计是否体现了新颖的思路或结构。

**最终要求**:
- 报告应以Markdown格式清晰呈现。
- 语言风格需专业、客观、精炼。
- 确保所有分析都基于图像数据，避免无根据的猜测。
"""
    return prompt.strip()


def call_multimodal_model(images: List[str], prompt: str) -> Dict[str, Any]:
    """调用多模态大模型进行图像分析
    
    Args:
        images: 图像文件路径列表
        prompt: 分析提示词
        
    Returns:
        模型分析结果
    """
    try:
        # 初始化API
        initialize_dashscope()
        
        # 验证图像文件
        valid_images = []
        for image_path in images:
            if not os.path.exists(image_path):
                print(f"警告: 图像文件不存在: {image_path}")
                continue
            if not image_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                print(f"警告: 不支持的图像格式: {image_path}")
                continue
            valid_images.append(image_path)
        
        if not valid_images:
            raise Exception("没有找到有效的图像文件")
        
        # 准备图像数据
        image_contents = []
        for image_path in valid_images:
            try:
                encoded_image = encode_image_to_base64(image_path)
                image_contents.append({
                    "image": f"data:image/png;base64,{encoded_image}"
                })
                print(f"成功加载图像: {os.path.basename(image_path)}")
            except Exception as e:
                print(f"警告: 图像编码失败 {image_path}: {str(e)}")
                continue
        
        if not image_contents:
            raise Exception("所有图像文件编码失败")
        
        # 构建消息
        messages = [{
            "role": "user",
            "content": [
                {"text": prompt}
            ] + image_contents
        }]
        
        print(f"正在调用qwen-vl-max模型分析 {len(image_contents)} 张图像...")
        
        # 调用模型
        response = MultiModalConversation.call(
            model='qwen-vl-max',
            messages=messages
        )
        
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            
            # 获取token使用量信息
            token_usage = {
                'input_tokens': response.usage.input_tokens if hasattr(response, 'usage') and hasattr(response.usage, 'input_tokens') else 0,
                'output_tokens': response.usage.output_tokens if hasattr(response, 'usage') and hasattr(response.usage, 'output_tokens') else 0,
                'total_tokens': response.usage.total_tokens if hasattr(response, 'usage') and hasattr(response.usage, 'total_tokens') else 0
            }
            
            # 处理返回结果格式
            if isinstance(content, list):
                # 如果返回的是列表，提取文本内容
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and 'text' in item:
                        text_parts.append(item['text'])
                    elif isinstance(item, str):
                        text_parts.append(item)
                analysis_text = '\n'.join(text_parts)
            elif isinstance(content, str):
                analysis_text = content
            else:
                analysis_text = str(content)
                
            return {
                'analysis_result': analysis_text,
                'token_usage': token_usage
            }
        else:
            raise Exception(f"模型调用失败 (状态码: {response.status_code}): {response.message}")
            
    except Exception as e:
        raise Exception(f"多模态模型调用错误: {str(e)}")


def analyze_simulation_images(params: MultimodalAnalysisParams) -> Dict[str, Any]:
    """分析仿真结果图像
    
    Args:
        params: 分析参数
        
    Returns:
        分析结果字典
    """
    try:
        # 查找图像文件
        found_images = find_simulation_images(params.results_dir)
        
        # 准备分析的图像列表
        images_to_analyze = []
        
        if params.include_s_parameters:
            images_to_analyze.extend(found_images['s_parameters'])
        
        if params.include_vswr:
            images_to_analyze.extend(found_images['vswr'])
        
        if not images_to_analyze:
            raise Exception("未找到可分析的图像文件")
        
        # 生成分析提示词
        prompt = generate_analysis_prompt()
        
        # 调用多模态模型
        model_response = call_multimodal_model(images_to_analyze, prompt)
        
        # 构建结果
        result = {
            "timestamp": datetime.now().isoformat(),
            "analyzed_images": {
                "s_parameters": found_images['s_parameters'] if params.include_s_parameters else [],
                "vswr": found_images['vswr'] if params.include_vswr else []
            },
            "total_images": len(images_to_analyze),
            "analysis_report": model_response['analysis_result'],
            "model_used": "qwen-vl-max",
            "token_usage": model_response['token_usage']
        }
        
        # 保存报告
        if params.save_report:
            save_analysis_report(result, params)
        
        return result
        
    except Exception as e:
        raise Exception(f"图像分析失败: {str(e)}")


def save_analysis_report(result: Dict[str, Any], params: MultimodalAnalysisParams) -> str:
    """保存分析报告到文件
    
    Args:
        result: 分析结果
        params: 分析参数
        
    Returns:
        保存的文件路径
    """
    try:
        # 确定文件名
        if params.report_filename:
            filename = params.report_filename
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if params.output_format == "json":
                filename = f"multimodal_analysis_report_{timestamp}.json"
            else:
                filename = f"multimodal_analysis_report_{timestamp}.md"
        
        # 确定保存路径
        results_path = Path(params.results_dir)
        results_path.mkdir(exist_ok=True)
        file_path = results_path / filename
        
        # 保存文件
        if params.output_format == "json":
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        else:
            # Markdown格式
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# 仿真结果多模态分析报告\n\n")
                f.write(f"**生成时间**: {result['timestamp']}\n\n")
                f.write(f"**分析模型**: {result['model_used']}\n\n")
                f.write(f"**分析图像数量**: {result['total_images']}\n\n")
                
                # 添加Token使用量信息
                token_info = result.get('token_usage', {})
                f.write(f"**Token使用量**:\n")
                f.write(f"- 输入Token: {token_info.get('input_tokens', 0)}\n")
                f.write(f"- 输出Token: {token_info.get('output_tokens', 0)}\n")
                f.write(f"- 总Token: {token_info.get('total_tokens', 0)}\n\n")
                
                f.write(f"## 分析结果\n\n")
                f.write(str(result['analysis_report']))
        
        return str(file_path)
        
    except Exception as e:
        raise Exception(f"报告保存失败: {str(e)}")


class MultimodalAnalysisTool(BaseTool):
    """多模态仿真结果图像分析工具"""
    
    name: str = "MULTIMODAL_ANALYSIS"
    description: str = """
    多模态仿真结果图像分析工具 - 使用qwen_vl_max模型分析HFSS仿真结果图像
    
    **功能描述**：
    1. 自动识别results文件夹中的仿真结果图像（S11、S21、S12、S22、VSWR等）
    2. 调用多模态大模型qwen_vl_max进行专业的图像分析
    3. 生成详细的仿真结果分析报告，包括性能评估和设计建议
    4. 支持Markdown和JSON格式的报告输出
    
    **主要分析内容**：
    - S参数性能分析（回波损耗、插入损耗、谐振频率等）
    - VSWR特性分析
    - 器件性能评估和设计建议
    - 技术结论和改进方向
    
    **必需参数**：
    无（使用默认配置即可）
    
    **可选参数**：
    - results_dir: 结果文件夹路径（默认"results"）
    - include_s_parameters: 是否分析S参数图像（默认true）
    - include_vswr: 是否分析VSWR图像（默认true）
    - output_format: 报告格式，markdown或json（默认"markdown"）
    - save_report: 是否保存报告文件（默认true）
    - report_filename: 自定义报告文件名（默认自动生成）
    
    **输出**：
    返回包含分析结果的详细报告，并可选择保存到文件。
    """
    
    def _run(self, **kwargs) -> str:
        """执行多模态图像分析"""
        try:
            # 解析参数
            params = MultimodalAnalysisParams(**kwargs)
            
            # 执行分析
            result = analyze_simulation_images(params)
            
            # 构建响应
            token_info = result.get('token_usage', {})
            response_parts = [
                "🔍 多模态仿真结果图像分析完成！",
                f"\n📊 分析统计：",
                f"  - 分析图像数量: {result['total_images']}",
                f"  - S参数图像: {len(result['analyzed_images']['s_parameters'])}",
                f"  - VSWR图像: {len(result['analyzed_images']['vswr'])}",
                f"  - 使用模型: {result['model_used']}",
                f"  - 分析时间: {result['timestamp']}",
                f"\n🔢 Token使用量：",
                f"  - 输入Token: {token_info.get('input_tokens', 0)}",
                f"  - 输出Token: {token_info.get('output_tokens', 0)}",
                f"  - 总Token: {token_info.get('total_tokens', 0)}"
            ]
            
            if params.save_report:
                response_parts.append(f"\n💾 分析报告已保存到results文件夹")
            
            response_parts.extend([
                f"\n📋 分析报告：",
                f"\n{result['analysis_report']}"
            ])
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"❌ 多模态图像分析失败: {str(e)}"
    
    async def _arun(self, **kwargs) -> str:
        """异步执行（调用同步方法）"""
        return self._run(**kwargs)


# 创建工具实例
MULTIMODAL_ANALYSIS = MultimodalAnalysisTool()