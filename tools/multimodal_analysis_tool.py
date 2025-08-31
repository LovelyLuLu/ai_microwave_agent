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
你是一位资深的微波工程师和HFSS仿真分析专家，拥有丰富的射频/微波器件设计和分析经验。请基于提供的HFSS仿真结果图像，生成一份专业、详细的技术分析报告。

**分析要求**：
1. 仔细观察每张图像的坐标轴、数值范围、曲线形状和关键特征点
2. 提供具体的数值读取和技术解释
3. 基于工程实践给出专业评估和建议

请按照以下结构进行分析：

## 1. 图像识别与基本信息
- **图像类型识别**：明确识别每张图像对应的参数类型（S11、S21、S12、S22、VSWR等）
- **频率范围**：读取并报告仿真的频率范围（起始频率到终止频率）
- **数据完整性**：评估曲线的连续性和数据质量
- **坐标轴信息**：确认Y轴的单位和数值范围

## 2. S参数详细分析

### 2.1 反射参数分析（S11, S22）
- **回波损耗性能**：
  - 读取最小回波损耗值及其对应频率
  - 评估-10dB带宽（如适用）
  - 分析匹配性能的频率特性
- **谐振特性**：
  - 识别谐振频率点（回波损耗最小值点）
  - 计算谐振频率处的具体回波损耗值
  - 评估谐振的尖锐度和Q值特性
- **带宽分析**：
  - 计算-3dB带宽、-10dB带宽等关键指标
  - 评估带宽与中心频率的比值

### 2.2 传输参数分析（S21, S12）
- **插入损耗特性**：
  - 读取通带内的最大和最小插入损耗
  - 分析插入损耗的频率平坦度
- **传输特性**：
  - 评估通带和阻带性能
  - 识别传输零点和极点
- **对称性分析**：
  - 比较S21和S12的对称性（如果两者都存在）
  - 评估器件的互易性

## 3. VSWR深度分析
如果包含VSWR图像：
- **数值范围**：读取VSWR的最小值、最大值和典型工作频段的数值
- **匹配评估**：
  - 识别VSWR < 2的频率范围（良好匹配区域）
  - 评估VSWR < 1.5的频率范围（优秀匹配区域）
- **频率特性**：分析VSWR随频率的变化趋势和关键特征点

## 4. 器件类型推断与性能评估
- **器件类型判断**：基于S参数特征推断可能的器件类型（滤波器、耦合器、天线、传输线等）
- **性能等级评估**：
  - 与典型器件性能指标对比
  - 评估是否满足常见应用要求
- **优势与不足**：
  - 总结设计的优点
  - 指出可能的性能瓶颈或问题

## 5. 工程建议与优化方向
- **设计优化建议**：
  - 基于分析结果提出具体的结构优化建议
  - 建议可能的参数调整方向
- **应用适用性**：评估当前设计适合的应用场景和频段
- **进一步仿真建议**：建议可能需要的额外仿真分析

## 6. 技术结论与总结
- **关键性能指标汇总**：列出所有重要的数值指标
- **整体设计质量评价**：给出综合性能评估
- **应用前景**：评估设计的实用性和商业价值

**注意事项**：
- 请尽可能从图像中读取具体的数值
- 所有分析应基于实际观察到的图像特征
- 提供的建议应具有工程实践意义
- 使用专业的微波工程术语和标准
"""
    return prompt.strip()


def call_multimodal_model(images: List[str], prompt: str) -> str:
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
            # 处理返回结果格式
            if isinstance(content, list):
                # 如果返回的是列表，提取文本内容
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and 'text' in item:
                        text_parts.append(item['text'])
                    elif isinstance(item, str):
                        text_parts.append(item)
                return '\n'.join(text_parts)
            elif isinstance(content, str):
                return content
            else:
                return str(content)
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
        analysis_result = call_multimodal_model(images_to_analyze, prompt)
        
        # 构建结果
        result = {
            "timestamp": datetime.now().isoformat(),
            "analyzed_images": {
                "s_parameters": found_images['s_parameters'] if params.include_s_parameters else [],
                "vswr": found_images['vswr'] if params.include_vswr else []
            },
            "total_images": len(images_to_analyze),
            "analysis_report": analysis_result,
            "model_used": "qwen-vl-max"
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
            response_parts = [
                "🔍 多模态仿真结果图像分析完成！",
                f"\n📊 分析统计：",
                f"  - 分析图像数量: {result['total_images']}",
                f"  - S参数图像: {len(result['analyzed_images']['s_parameters'])}",
                f"  - VSWR图像: {len(result['analyzed_images']['vswr'])}",
                f"  - 使用模型: {result['model_used']}",
                f"  - 分析时间: {result['timestamp']}"
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