"""HFSS仿真结果分析工具
基于 scripts/result.py 的 LangChain 工具实现
提供S参数分析、VSWR计算、回波损耗、插入损耗等无源器件分析功能
"""

import os
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from ansys.aedt.core import Hfss
from ansys.aedt.core.generic.general_methods import pyaedt_function_handler
import matplotlib.pyplot as plt



class ResultAnalysisParams(BaseModel):
    """HFSS仿真结果分析参数"""
    
    # 必需参数
    project_path: Optional[str] = Field(
        default=None,
        description="HFSS项目文件路径，如果为None则自动查找最新项目"
    )
    setup_name: str = Field(
        default="MainSetup",
        description="分析设置名称"
    )
    sweep_name: str = Field(
        default="BroadbandSweep", 
        description="扫频设置名称"
    )
    
    # S参数配置
    s_parameters: List[str] = Field(
        default=["S(1,1)", "S(2,1)", "S(1,2)", "S(2,2)"],
        description="要分析的S参数列表，例如['S(1,1)', 'S(2,1)']"
    )
    
    # 分析选项
    generate_plots: bool = Field(
        default=True,
        description="是否生成图表"
    )
    export_data: bool = Field(
        default=True,
        description="是否导出数据到CSV和JSON"
    )
    calculate_vswr: bool = Field(
        default=True,
        description="是否计算VSWR"
    )
    calculate_metrics: bool = Field(
        default=True,
        description="是否计算关键指标（回波损耗、插入损耗等）"
    )
    
    # 输出配置
    output_dir: Optional[str] = Field(
        default=None,
        description="结果输出目录，如果为None则使用项目根目录下的results文件夹"
    )


@pyaedt_function_handler
def get_hfss_solution_data(hfss_app, setup_name, sweep_name, expressions):
    """从HFSS获取指定的仿真结果数据"""
    print(f"正在从设置 '{setup_name}:{sweep_name}' 提取仿真结果...")
    
    try:
        solution = hfss_app.post.get_solution_data(
            expressions=expressions,
            setup_sweep_name=f"{setup_name} : {sweep_name}",
            domain="Sweep",
        )
        
        if solution:
            print("成功提取到仿真结果。")
        else:
            print("错误: 未能提取到仿真结果。")
            
        return solution
    except Exception as e:
        print(f"提取仿真结果时发生错误: {e}")
        return None


@pyaedt_function_handler
def plot_s_parameters(solution_data, s_param, file_path=None):
    """使用 Matplotlib 绘制S参数的幅度和相位图"""
    if not solution_data or s_param not in solution_data.expressions:
        print(f"错误: 无法绘制 '{s_param}'，数据不存在。")
        return False

    print(f"正在使用 Matplotlib 绘制 {s_param}...")

    try:
        # 获取数据
        freq = np.array(solution_data.primary_sweep_values)
        real_part = np.array(solution_data.data_real(s_param))
        imag_part = np.array(solution_data.data_imag(s_param))

        # 数据维度检查
        if freq.ndim != 1 or real_part.ndim != 1 or imag_part.ndim != 1:
            print(f"警告: {s_param} 的数据维度不匹配，跳过绘图。")
            return False

        # 计算幅度和相位
        mag = np.sqrt(real_part**2 + imag_part**2)
        mag_db = 20 * np.log10(np.maximum(mag, 1e-12))  # 避免log(0)
        phase_rad = np.arctan2(imag_part, real_part)
        phase_deg = np.rad2deg(phase_rad)

        # 创建 Matplotlib 图形
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle(f"S-Parameter Analysis: {s_param}", fontsize=16)

        # 绘制幅度
        ax1.plot(freq, mag_db, label=f"{s_param} Magnitude", linewidth=2)
        ax1.set_title("Magnitude (dB)")
        ax1.set_xlabel("Frequency (GHz)")
        ax1.set_ylabel("Magnitude (dB)")
        ax1.grid(True, which='both', linestyle='--', alpha=0.7)
        ax1.legend()

        # 绘制相位
        ax2.plot(freq, phase_deg, color='orange', label=f"{s_param} Phase", linewidth=2)
        ax2.set_title("Phase (degrees)")
        ax2.set_xlabel("Frequency (GHz)")
        ax2.set_ylabel("Phase (°)")
        ax2.grid(True, which='both', linestyle='--', alpha=0.7)
        ax2.legend()

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        if file_path:
            plt.savefig(file_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            print(f"成功将 {s_param} 图像保存到: {file_path}")
        else:
            plt.show()
            print(f"成功绘制 {s_param}。")
            
        return True

    except Exception as e:
        print(f"使用 Matplotlib 绘制 '{s_param}' 失败: {e}")
        return False


@pyaedt_function_handler
def plot_vswr(solution_data, reflection_params, file_path=None):
    """使用 Matplotlib 绘制VSWR（电压驻波比）图"""
    print(f"正在使用 Matplotlib 绘制 VSWR...")

    try:
        # 获取频率数据
        freq = np.array(solution_data.primary_sweep_values)
        
        # 创建 Matplotlib 图形
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        fig.suptitle("VSWR Analysis", fontsize=16)
        
        colors = ['blue', 'red', 'green', 'orange']
        all_vswr_values = []  # 收集所有VSWR值用于自适应Y轴缩放
        
        for i, s_param in enumerate(reflection_params):
            if s_param not in solution_data.expressions:
                print(f"警告: 参数 '{s_param}' 不存在于仿真结果中，跳过。")
                continue
                
            # 获取反射系数的实部和虚部
            real_part = np.array(solution_data.data_real(s_param))
            imag_part = np.array(solution_data.data_imag(s_param))
            
            # 数据维度检查
            if freq.ndim != 1 or real_part.ndim != 1 or imag_part.ndim != 1:
                print(f"警告: {s_param} 的数据维度不匹配，跳过。")
                continue
                
            # 计算反射系数的幅度
            reflection_mag = np.sqrt(real_part**2 + imag_part**2)
            
            # 计算VSWR: VSWR = (1 + |Γ|) / (1 - |Γ|)
            # 为避免除零错误，限制反射系数幅度的最大值
            reflection_mag = np.clip(reflection_mag, 0, 0.999)
            vswr = (1 + reflection_mag) / (1 - reflection_mag)
            
            # 收集VSWR值用于自适应缩放
            all_vswr_values.extend(vswr.tolist())
            
            # 绘制VSWR
            color = colors[i % len(colors)]
            ax.plot(freq, vswr, color=color, label=f"VSWR from {s_param}", linewidth=2)
        
        # 自适应Y轴缩放
        if all_vswr_values:
            min_vswr = max(1.0, min(all_vswr_values))  # VSWR最小值为1
            max_vswr = max(all_vswr_values)
            
            # 添加一些边距使图形更美观
            y_margin = (max_vswr - min_vswr) * 0.1
            y_min = max(1.0, min_vswr - y_margin)
            y_max = max_vswr + y_margin
            
            # 如果最大值过大，限制在合理范围内
            if y_max > 50:
                y_max = min(50, max_vswr * 1.1)
                
            ax.set_ylim(y_min, y_max)
        else:
            ax.set_ylim(1, 10)  # 如果没有数据，使用默认范围
        
        ax.set_title("Voltage Standing Wave Ratio (VSWR)")
        ax.set_xlabel("Frequency (GHz)")
        ax.set_ylabel("VSWR")
        ax.grid(True, which='both', linestyle='--', alpha=0.7)
        ax.legend()
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        if file_path:
            plt.savefig(file_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            print(f"成功将 VSWR 图像保存到: {file_path}")
        else:
            plt.show()
            print(f"成功绘制 VSWR。")
            
        return True

    except Exception as e:
        print(f"使用 Matplotlib 绘制 VSWR 失败: {e}")
        return False


@pyaedt_function_handler
def calculate_key_metrics(solution_data, s_parameters):
    """计算关键性能指标"""
    metrics = {}
    
    try:
        freq = np.array(solution_data.primary_sweep_values)
        
        for s_param in s_parameters:
            if s_param not in solution_data.expressions:
                continue
                
            real_part = np.array(solution_data.data_real(s_param))
            imag_part = np.array(solution_data.data_imag(s_param))
            
            # 计算幅度和dB值
            mag = np.sqrt(real_part**2 + imag_part**2)
            mag_db = 20 * np.log10(np.maximum(mag, 1e-12))
            
            param_metrics = {
                'min_db': float(np.min(mag_db)),
                'max_db': float(np.max(mag_db)),
                'mean_db': float(np.mean(mag_db))
            }
            
            # 对于反射参数（S11, S22等），计算回波损耗
            if s_param.startswith('S(') and s_param[2] == s_param[4]:  # 如S(1,1), S(2,2)
                return_loss_db = -mag_db  # 回波损耗 = -S11(dB)
                param_metrics.update({
                    'return_loss_min_db': float(np.min(return_loss_db)),
                    'return_loss_max_db': float(np.max(return_loss_db)),
                    'return_loss_mean_db': float(np.mean(return_loss_db))
                })
                
                # 计算VSWR
                reflection_mag = np.clip(mag, 0, 0.999)
                vswr = (1 + reflection_mag) / (1 - reflection_mag)
                param_metrics.update({
                    'vswr_min': float(np.min(vswr)),
                    'vswr_max': float(np.max(vswr)),
                    'vswr_mean': float(np.mean(vswr))
                })
            
            # 对于传输参数（S21, S12等），计算插入损耗
            elif s_param.startswith('S(') and s_param[2] != s_param[4]:  # 如S(2,1), S(1,2)
                insertion_loss_db = -mag_db  # 插入损耗 = -S21(dB)
                param_metrics.update({
                    'insertion_loss_min_db': float(np.min(insertion_loss_db)),
                    'insertion_loss_max_db': float(np.max(insertion_loss_db)),
                    'insertion_loss_mean_db': float(np.mean(insertion_loss_db))
                })
            
            # 查找谐振频率（最小值对应的频率）
            min_idx = np.argmin(mag_db)
            param_metrics['resonant_frequency_ghz'] = float(freq[min_idx])
            param_metrics['resonant_magnitude_db'] = float(mag_db[min_idx])
            
            metrics[s_param] = param_metrics
            
        return metrics
        
    except Exception as e:
        print(f"计算关键指标时发生错误: {e}")
        return {}


@pyaedt_function_handler
def export_data_to_files(solution_data, output_dir):
    """将仿真结果数据导出到CSV和JSON文件"""
    try:
        # 导出CSV
        csv_path = os.path.join(output_dir, "s_parameters.csv")
        solution_data.export_data_to_csv(csv_path)
        print(f"CSV文件导出成功: {csv_path}")
        
        # 导出JSON
        json_path = os.path.join(output_dir, "s_parameters.json")
        data_dict = {}
        for expr in solution_data.expressions:
            data_dict[expr] = {
                "frequency_ghz": solution_data.primary_sweep_values,
                "real": solution_data.data_real(expr),
                "imag": solution_data.data_imag(expr),
            }
            
        with open(json_path, 'w') as f:
            json.dump(data_dict, f, indent=4)
        print(f"JSON文件导出成功: {json_path}")
        
        return True
        
    except Exception as e:
        print(f"导出数据文件时发生错误: {e}")
        return False


def get_latest_project(projects_dir, project_name_prefix=""):
    """获取最新的项目文件"""
    try:
        if not os.path.exists(projects_dir):
            return None
            
        project_files = []
        for file in os.listdir(projects_dir):
            if file.endswith('.aedt') and file.startswith(project_name_prefix):
                full_path = os.path.join(projects_dir, file)
                project_files.append((full_path, os.path.getmtime(full_path)))
        
        if not project_files:
            return None
            
        # 按修改时间排序，返回最新的
        project_files.sort(key=lambda x: x[1], reverse=True)
        return project_files[0][0]
        
    except Exception as e:
        print(f"查找项目文件时发生错误: {e}")
        return None


def analyze_hfss_results(params: ResultAnalysisParams) -> Dict[str, Any]:
    """分析HFSS仿真结果的主函数"""
    result = {
        "success": False,
        "message": "",
        "project_path": "",
        "metrics": {},
        "generated_files": [],
        "error": None
    }
    
    hfss = None
    
    try:
        # 确定项目路径
        if params.project_path:
            project_path = params.project_path
        else:
            # 自动查找最新项目
            aedt_projects_path = os.path.join(os.path.expanduser("~"), "Documents", "Ansoft")
            project_path = get_latest_project(aedt_projects_path)
            
        if not project_path or not os.path.exists(project_path):
            result["error"] = "未找到有效的HFSS项目文件"
            return result
            
        result["project_path"] = project_path
        print(f"正在分析项目: {project_path}")
        
        # 连接到HFSS项目
        try:
            # 首先尝试连接到现有项目
            hfss = Hfss(
                project=project_path,
                non_graphical=True,
                new_desktop=False,
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "locked" in error_msg or "project is locked" in error_msg:
                print("项目被锁定，尝试使用新的Desktop实例...")
                try:
                    # 如果项目被锁定，尝试使用新的Desktop实例
                    from ansys.aedt.core import Desktop
                    # 先尝试关闭现有Desktop
                    try:
                        desktop = Desktop()
                        desktop.close_desktop()
                    except:
                        pass
                    
                    # 使用新的Desktop实例
                    hfss = Hfss(
                        project=project_path,
                        non_graphical=True,
                        new_desktop=True,
                    )
                    print("成功使用新Desktop实例连接到项目")
                except Exception as e2:
                    result["error"] = f"项目被锁定且无法创建新Desktop实例: {str(e2)}。请手动关闭AEDT后重试。"
                    return result
            else:
                result["error"] = f"连接HFSS项目时发生错误: {str(e)}"
                return result
        
        print(f"成功连接到项目: {hfss.project_name}")
        
        # 设置输出目录
        if params.output_dir:
            output_dir = params.output_dir
        else:
            # 使用项目根目录下的results文件夹
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            output_dir = os.path.join(project_root, "results")
            
        os.makedirs(output_dir, exist_ok=True)
        print(f"结果将保存到: {output_dir}")
        
        # 提取仿真结果数据
        solution_data = get_hfss_solution_data(
            hfss, params.setup_name, params.sweep_name, params.s_parameters
        )
        
        if not solution_data:
            result["error"] = "无法提取仿真结果数据"
            return result
            
        # 生成S参数图表
        if params.generate_plots:
            for s_param in params.s_parameters:
                if s_param in solution_data.expressions:
                    # 生成文件名（替换特殊字符）
                    safe_name = s_param.replace('(', '_').replace(',', '_').replace(')', '')
                    image_path = os.path.join(output_dir, f"{safe_name}.png")
                    
                    if plot_s_parameters(solution_data, s_param, file_path=image_path):
                        result["generated_files"].append(image_path)
            
            # 生成VSWR图表
            if params.calculate_vswr:
                reflection_params = [p for p in params.s_parameters 
                                   if p.startswith('S(') and len(p) >= 6 and p[2] == p[4]]
                if reflection_params:
                    vswr_path = os.path.join(output_dir, "VSWR.png")
                    if plot_vswr(solution_data, reflection_params, file_path=vswr_path):
                        result["generated_files"].append(vswr_path)
        
        # 计算关键指标
        if params.calculate_metrics:
            metrics = calculate_key_metrics(solution_data, params.s_parameters)
            result["metrics"] = metrics
            
            # 保存指标到JSON文件
            metrics_path = os.path.join(output_dir, "analysis_metrics.json")
            with open(metrics_path, 'w') as f:
                json.dump(metrics, f, indent=4)
            result["generated_files"].append(metrics_path)
        
        # 导出数据文件
        if params.export_data:
            if export_data_to_files(solution_data, output_dir):
                result["generated_files"].extend([
                    os.path.join(output_dir, "s_parameters.csv"),
                    os.path.join(output_dir, "s_parameters.json")
                ])
        
        result["success"] = True
        result["message"] = f"HFSS仿真结果分析完成，共生成 {len(result['generated_files'])} 个文件"
        

        
    except Exception as e:
        result["error"] = str(e)
        print(f"分析过程中发生错误: {e}")
        

        
    finally:
        # 最终的资源清理
        try:
            if hfss:
                print("\n最终资源清理...")
                hfss.close_project()
                print("最终资源清理完成")
        except Exception as final_error:
            print(f"最终资源清理失败: {final_error}")
            
    return result


class AnalyzeHFSSResultsTool(BaseTool):
    """HFSS仿真结果分析工具
    
    该工具可以分析HFSS仿真结果，提供以下功能：
    1. S参数分析和可视化（幅度、相位图）
    2. VSWR（电压驻波比）计算和绘图
    3. 关键性能指标计算（回波损耗、插入损耗、谐振频率等）
    4. 数据导出（CSV、JSON格式）
    5. 自动生成分析报告和图表
    
    适用场景：
    - 微波器件性能评估
    - 天线参数分析
    - 滤波器特性分析
    - 传输线特性分析
    - SRR/CSRR结构性能分析
    """
    
    name: str = "ANALYZE_HFSS_RESULTS"
    description: str = """对已完成的HFSS仿真项目进行结果分析，包括S参数分析、VSWR计算、关键指标提取等。
    
    **必需参数**：
    - setup_name: 分析设置名称（默认MainSetup）
    - sweep_name: 扫频设置名称（默认BroadbandSweep）
    
    **可选参数**：
    - project_path: HFSS项目文件路径（如果为空则自动查找最新项目）
    - s_parameters: 要分析的S参数列表（默认["S(1,1)", "S(2,1)", "S(1,2)", "S(2,2)"]）
    - generate_plots: 是否生成图表（默认true）
    - export_data: 是否导出数据文件（默认true）
    - calculate_vswr: 是否计算VSWR（默认true）
    - calculate_metrics: 是否计算关键指标（默认true）
    - output_dir: 结果输出目录（默认使用项目根目录下的results文件夹）
    """
    
    def _run(self, **kwargs) -> str:
        """执行HFSS结果分析"""
        try:
            # 处理LangChain传递的嵌套kwargs结构
            if 'kwargs' in kwargs:
                actual_kwargs = kwargs['kwargs']
            else:
                actual_kwargs = kwargs
            
            # 解析参数
            params = ResultAnalysisParams(**actual_kwargs)
            
            # 执行分析
            result = analyze_hfss_results(params)
            
            if result["success"]:
                response = f"""HFSS仿真结果分析完成！

📊 分析项目: {os.path.basename(result['project_path'])}
📁 结果目录: {os.path.dirname(result['generated_files'][0]) if result['generated_files'] else 'N/A'}
📈 生成文件数: {len(result['generated_files'])}

🔍 关键指标摘要:"""
                
                # 添加关键指标摘要
                if result.get('metrics'):
                    for s_param, metrics in result['metrics'].items():
                        response += f"\n\n📡 {s_param}:"
                        if 'return_loss_max_db' in metrics:
                            response += f"\n  • 最大回波损耗: {metrics['return_loss_max_db']:.2f} dB"
                        if 'insertion_loss_max_db' in metrics:
                            response += f"\n  • 最大插入损耗: {metrics['insertion_loss_max_db']:.2f} dB"
                        if 'vswr_max' in metrics:
                            response += f"\n  • 最大VSWR: {metrics['vswr_max']:.2f}"
                        if 'resonant_frequency_ghz' in metrics:
                            response += f"\n  • 谐振频率: {metrics['resonant_frequency_ghz']:.3f} GHz"
                
                response += f"\n\n✅ {result['message']}"
                return response
            else:
                return f"❌ HFSS结果分析失败: {result['error']}"
                
        except Exception as e:
            return f"❌ 参数解析或执行错误: {str(e)}"
    
    async def _arun(self, **kwargs) -> str:
        """异步执行（调用同步方法）"""
        return self._run(**kwargs)


# 创建工具实例
ANALYZE_RESULTS = AnalyzeHFSSResultsTool()