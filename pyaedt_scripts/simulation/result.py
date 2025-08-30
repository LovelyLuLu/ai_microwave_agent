"""
HFSS 仿真结果后处理脚本
作者：PyAEDT自动化脚本
"""

import os
import json
import csv
import numpy as np
from ansys.aedt.core import Hfss
from ansys.aedt.core.generic.general_methods import pyaedt_function_handler
import matplotlib.pyplot as plt

# =============================================================================
# 结果处理核心功能函数
# =============================================================================

@pyaedt_function_handler
def get_hfss_solution_data(hfss_app, setup_name, sweep_name, expressions):
    """
    从HFSS获取指定的仿真结果数据。

    参数:
    - hfss_app (pyaedt.Hfss): 一个有效的Hfss应用实例。
    - setup_name (str): 分析设置的名称。
    - sweep_name (str): 扫频的名称。
    - expressions (list of str): 需要提取的结果表达式，例如 ["S(1,1)", "S(2,1)"]。

    返回:
    - pyaedt.modules.solutions.SolutionData: 包含仿真结果的SolutionData对象，失败则返回None。
    """
    print(f"正在从设置 '{setup_name}:{sweep_name}' 提取仿真结果...")
    
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

@pyaedt_function_handler
def plot_s_parameters(solution_data, s_param, file_path=None):
    """
    使用 Matplotlib 绘制S参数的幅度和相位图。

    参数:
    - solution_data: PyAEDT solution data 对象。
    - s_param (str): S参数名称，例如 'S(1,1)'。
    - file_path (str, optional): 图像保存路径. 如果提供, 图像将保存到文件而不是显示.
    """
    if not solution_data or s_param not in solution_data.expressions:
        print(f"错误: 无法绘制 '{s_param}'，数据不存在。")
        return

    print(f"正在使用 Matplotlib 绘制 {s_param}...")

    try:
        # 获取数据
        freq = np.array(solution_data.primary_sweep_values)
        real_part = np.array(solution_data.data_real(s_param))
        imag_part = np.array(solution_data.data_imag(s_param))

        # 数据维度检查
        if freq.ndim != 1 or real_part.ndim != 1 or imag_part.ndim != 1 or freq.shape != real_part.shape or freq.shape != imag_part.shape:
            print(f"警告: {s_param} 的数据维度不匹配或不是一维数组。将跳过绘图。")
            print(f"  频率维度: {freq.shape}, 实部维度: {real_part.shape}, 虚部维度: {imag_part.shape}")
            return

        # 计算幅度和相位
        mag = np.sqrt(real_part**2 + imag_part**2)
        mag_db = 20 * np.log10(mag)
        phase_rad = np.arctan2(imag_part, real_part)
        phase_deg = np.rad2deg(phase_rad)

        # 创建 Matplotlib 图形
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle(f"S-Parameter Analysis: {s_param}", fontsize=16)

        # 绘制幅度
        ax1.plot(freq, mag_db, label=f"{s_param} Magnitude")
        ax1.set_title("Magnitude (dB)")
        ax1.set_xlabel("Frequency (GHz)")
        ax1.set_ylabel("Magnitude (dB)")
        ax1.grid(True, which='both', linestyle='--')
        ax1.legend()

        # 绘制相位
        ax2.plot(freq, phase_deg, color='orange', label=f"{s_param} Phase")
        ax2.set_title("Phase (degrees)")
        ax2.set_xlabel("Frequency (GHz)")
        ax2.set_ylabel("Phase (°)")
        ax2.grid(True, which='both', linestyle='--')
        ax2.legend()

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        if file_path:
            plt.savefig(file_path)
            plt.close(fig)
            print(f"成功将 {s_param} 图像保存到: {file_path}")
        else:
            plt.show()
            print(f"成功绘制 {s_param}。")

    except Exception as e:
        print(f"使用 Matplotlib 绘制 '{s_param}' 失败: {e}")
        print("请检查数据是否有效以及 Matplotlib 是否正确安装。")

@pyaedt_function_handler
def export_data_to_csv(solution_data, file_path):
    """
    将仿真结果数据导出到CSV文件。

    参数:
    - solution_data (pyaedt.modules.solutions.SolutionData): 包含结果数据的对象。
    - file_path (str): CSV文件的保存路径。
    """
    print(f"正在将结果导出到CSV文件: {file_path}")
    try:
        solution_data.export_data_to_csv(file_path)
        print("CSV文件导出成功。")
    except Exception as e:
        print(f"错误: 导出到CSV失败。{e}")

@pyaedt_function_handler
def export_data_to_json(solution_data, file_path):
    """
    将仿真结果数据导出到JSON文件。

    参数:
    - solution_data (pyaedt.modules.solutions.SolutionData): 包含结果数据的对象。
    - file_path (str): JSON文件的保存路径。
    """
    print(f"正在将结果导出到JSON文件: {file_path}")
    data_dict = {}
    for expr in solution_data.expressions:
        data_dict[expr] = {
            "freq": solution_data.primary_sweep_values,
            "real": solution_data.data_real(expr),
            "imag": solution_data.data_imag(expr),
        }
        
    try:
        with open(file_path, 'w') as f:
            json.dump(data_dict, f, indent=4)
        print("JSON文件导出成功。")
    except Exception as e:
        print(f"错误: 导出到JSON失败。{e}")

@pyaedt_function_handler
def plot_vswr(solution_data, reflection_params, file_path=None):
    """
    使用 Matplotlib 绘制VSWR（电压驻波比）图。

    参数:
    - solution_data: PyAEDT solution data 对象。
    - reflection_params (list): 反射参数列表，例如 ['S(1,1)', 'S(2,2)']。
    - file_path (str, optional): 图像保存路径. 如果提供, 图像将保存到文件而不是显示.
    """
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
            plt.savefig(file_path)
            plt.close(fig)
            print(f"成功将 VSWR 图像保存到: {file_path}")
        else:
            plt.show()
            print(f"成功绘制 VSWR。")

    except Exception as e:
        print(f"使用 Matplotlib 绘制 VSWR 失败: {e}")
        print("请检查数据是否有效以及 Matplotlib 是否正确安装。")




# =============================================================================
# 主函数 (用于独立运行)
# =============================================================================

def main():
    """
    主函数，用于独立执行结果后处理。
    """
    print("="*70)
    print("开始执行HFSS仿真结果后处理...")
    print("="*70)

    # 与solve.py相同的项目路径逻辑
    aedt_projects_path = os.path.join(os.path.expanduser("~"), "Documents", "Ansoft")
    
    # 假设我们处理的是最新的CSRR项目
    from setup import get_latest_project
    latest_project_path = get_latest_project(aedt_projects_path, project_name_prefix="CSRR_Project")

    if not latest_project_path:
        print("未能找到最新的项目文件，脚本终止。")
        return

    hfss = None
    try:
        print(f"正在连接到项目: {latest_project_path}")
        hfss = Hfss(
            project=latest_project_path,
            non_graphical=False,
            new_desktop=False,
        )
        print(f"成功连接到项目: {hfss.project_name}")

        # --- 后处理参数 ---
        setup_name = "MainSetup"
        sweep_name = "BroadbandSweep"
        s_params_to_plot = ["S(1,1)", "S(2,1)", "S(1,2)", "S(2,2)"]

        
        # 1. 提取S参数
        solution_data = get_hfss_solution_data(hfss, setup_name, sweep_name, s_params_to_plot)

        if solution_data:
            # 2. 绘制S参数
            # 使用相对路径，在Python项目根目录下创建results文件夹
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(script_dir))  # 回到MCP目录
            results_dir = os.path.join(project_root, "results")
            os.makedirs(results_dir, exist_ok=True)
            
            for s_param in s_params_to_plot:
                image_path = os.path.join(results_dir, f"{s_param.replace('(', '_').replace(',', '_').replace(')', '')}.png")
                plot_s_parameters(solution_data, s_param, file_path=image_path)

            # 2.5. 绘制VSWR
            reflection_params = ["S(1,1)", "S(2,2)"]  # 使用反射参数计算VSWR
            vswr_image_path = os.path.join(results_dir, "VSWR.png")
            plot_vswr(solution_data, reflection_params, file_path=vswr_image_path)

            # 3. 导出数据
            export_data_to_csv(solution_data, os.path.join(results_dir, "s_params.csv"))
            export_data_to_json(solution_data, os.path.join(results_dir, "s_params.json"))



    except Exception as e:
        print(f"\n发生严重错误: {e}")

    finally:
        if hfss:
            # 保持AEDT打开
            pass

    print("="*70)
    print("HFSS结果后处理流程执行完毕。")
    print("="*70)

if __name__ == "__main__":
    main()