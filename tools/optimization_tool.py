from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Callable
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from datetime import datetime
import numpy as np
import json
import os
import random
import time
from abc import ABC, abstractmethod
from pyaedt import Hfss
from pyaedt.generic.general_methods import pyaedt_function_handler

# ---------- 数据结构定义 ----------

class OptimizationVariable(BaseModel):
    """优化变量定义"""
    name: str = Field(description="变量名称")
    min_value: float = Field(description="最小值")
    max_value: float = Field(description="最大值")
    initial_value: Optional[float] = Field(default=None, description="初始值（可选）")
    description: Optional[str] = Field(default="", description="变量描述")

class OptimizationObjective(BaseModel):
    """优化目标定义"""
    name: str = Field(description="目标名称")
    target_type: str = Field(description="目标类型：minimize, maximize, target")
    target_value: Optional[float] = Field(default=None, description="目标值（当target_type为target时使用）")
    weight: float = Field(default=1.0, description="权重")
    description: Optional[str] = Field(default="", description="目标描述")

class OptimizationParams(BaseModel):
    """优化参数统一接口"""
    # 算法选择
    algorithm: str = Field(
        description="优化算法：GA（遗传算法）或PSO（粒子群算法）",
        default="GA"
    )
    
    # 优化变量
    variables: List[OptimizationVariable] = Field(
        description="优化变量列表"
    )
    
    # 优化目标
    objectives: List[OptimizationObjective] = Field(
        description="优化目标列表"
    )
    
    # 通用算法参数
    population_size: int = Field(
        default=50,
        description="种群大小",
        gt=0
    )
    max_iterations: int = Field(
        default=100,
        description="最大迭代次数",
        gt=0
    )
    convergence_threshold: float = Field(
        default=1e-6,
        description="收敛阈值"
    )
    
    # GA特有参数
    crossover_rate: float = Field(
        default=0.8,
        description="交叉概率（GA）",
        ge=0.0,
        le=1.0
    )
    mutation_rate: float = Field(
        default=0.1,
        description="变异概率（GA）",
        ge=0.0,
        le=1.0
    )
    
    # PSO特有参数
    inertia_weight: float = Field(
        default=0.9,
        description="惯性权重（PSO）",
        ge=0.0,
        le=1.0
    )
    cognitive_coefficient: float = Field(
        default=2.0,
        description="认知系数（PSO）",
        gt=0.0
    )
    social_coefficient: float = Field(
        default=2.0,
        description="社会系数（PSO）",
        gt=0.0
    )
    
    # 项目相关
    project_name: Optional[str] = Field(
        default=None,
        description="项目名称"
    )
    design_name: Optional[str] = Field(
        default=None,
        description="设计名称"
    )
    
    # 结果保存
    save_results: bool = Field(
        default=True,
        description="是否保存结果"
    )
    results_dir: str = Field(
        default="results",
        description="结果保存目录"
    )

class OptimizationResult(BaseModel):
    """优化结果统一接口"""
    # 基本信息
    algorithm: str = Field(description="使用的算法")
    success: bool = Field(description="优化是否成功")
    message: str = Field(description="结果消息")
    
    # 最优解
    best_solution: Dict[str, float] = Field(description="最优解变量值")
    best_fitness: float = Field(description="最优适应度值")
    
    # 优化过程信息
    iterations_completed: int = Field(description="完成的迭代次数")
    convergence_achieved: bool = Field(description="是否达到收敛")
    
    # 历史记录
    convergence_history: List[float] = Field(description="收敛历史")
    
    # 统计信息
    total_evaluations: int = Field(description="总评估次数")
    execution_time: float = Field(description="执行时间（秒）")
    
    # 文件信息
    result_file: Optional[str] = Field(default=None, description="结果文件路径")
    
    # 时间戳
    timestamp: str = Field(description="优化完成时间")

# ---------- 优化算法基类 ----------

class BaseOptimizer(ABC):
    """优化算法基类"""
    
    def __init__(self, params: OptimizationParams):
        self.params = params
        self.variables = params.variables
        self.objectives = params.objectives
        self.population_size = params.population_size
        self.max_iterations = params.max_iterations
        self.convergence_threshold = params.convergence_threshold
        
        # 初始化变量边界
        self.bounds = [(var.min_value, var.max_value) for var in self.variables]
        self.var_names = [var.name for var in self.variables]
        
        # 历史记录
        self.convergence_history = []
        self.total_evaluations = 0
        
        # 优化过程监控
        self.history = []
        self.best_fitness_history = []
        self.progress_callback = None
        
    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback
        
    def _log_progress(self, generation: int, best_fitness: float, best_solution: Dict[str, float]):
        """记录优化进度"""
        progress_info = {
            "generation": generation,
            "best_fitness": best_fitness,
            "best_solution": best_solution.copy(),
            "timestamp": datetime.now().isoformat()
        }
        self.history.append(progress_info)
        self.best_fitness_history.append(best_fitness)
        
        if self.progress_callback:
            self.progress_callback(progress_info)
    
    @abstractmethod
    def optimize(self, objective_function: Callable) -> OptimizationResult:
        """执行优化"""
        pass
    
    def evaluate_fitness(self, solution: np.ndarray, objective_function: Callable) -> float:
        """评估适应度"""
        self.total_evaluations += 1
        
        # 将解转换为字典格式
        solution_dict = {name: value for name, value in zip(self.var_names, solution)}
        
        # 调用目标函数
        try:
            objectives_values = objective_function(solution_dict)
            
            # 计算综合适应度（多目标加权求和）
            total_fitness = 0.0
            for i, obj in enumerate(self.objectives):
                obj_value = objectives_values.get(obj.name, 0.0)
                
                if obj.target_type == "minimize":
                    fitness_contribution = -obj_value * obj.weight
                elif obj.target_type == "maximize":
                    fitness_contribution = obj_value * obj.weight
                elif obj.target_type == "target":
                    # 目标值优化：距离目标值越近越好
                    fitness_contribution = -abs(obj_value - obj.target_value) * obj.weight
                else:
                    fitness_contribution = 0.0
                
                total_fitness += fitness_contribution
            
            return total_fitness
            
        except Exception as e:
            print(f"目标函数评估错误: {str(e)}")
            return float('-inf')  # 返回极小值表示无效解
    
    def generate_random_solution(self) -> np.ndarray:
        """生成随机解"""
        solution = np.zeros(len(self.variables))
        for i, (min_val, max_val) in enumerate(self.bounds):
            if self.variables[i].initial_value is not None:
                # 如果有初始值，在其附近生成
                initial = self.variables[i].initial_value
                range_size = (max_val - min_val) * 0.1  # 10%的范围
                solution[i] = np.clip(
                    np.random.normal(initial, range_size/3),
                    min_val, max_val
                )
            else:
                solution[i] = np.random.uniform(min_val, max_val)
        return solution
    
    def clip_solution(self, solution: np.ndarray) -> np.ndarray:
        """将解限制在边界内"""
        clipped = np.zeros_like(solution)
        for i, (min_val, max_val) in enumerate(self.bounds):
            clipped[i] = np.clip(solution[i], min_val, max_val)
        return clipped

# ---------- 遗传算法实现 ----------

class GeneticAlgorithm(BaseOptimizer):
    """遗传算法优化器"""
    
    def __init__(self, params: OptimizationParams):
        super().__init__(params)
        self.crossover_rate = params.crossover_rate
        self.mutation_rate = params.mutation_rate
    
    def optimize(self, objective_function: Callable) -> OptimizationResult:
        """执行遗传算法优化"""
        start_time = datetime.now()
        
        # 初始化种群
        population = np.array([self.generate_random_solution() for _ in range(self.population_size)])
        fitness_values = np.array([self.evaluate_fitness(ind, objective_function) for ind in population])
        
        # 记录最优解
        best_idx = np.argmax(fitness_values)
        best_solution = population[best_idx].copy()
        best_fitness = fitness_values[best_idx]
        
        self.convergence_history.append(best_fitness)
        
        # 记录初始进度
        best_solution_dict = {name: value for name, value in zip(self.var_names, best_solution)}
        self._log_progress(0, best_fitness, best_solution_dict)
        
        # 迭代优化
        for generation in range(self.max_iterations):
            # 选择
            selected_population = self._selection(population, fitness_values)
            
            # 交叉和变异
            new_population = []
            for i in range(0, self.population_size, 2):
                parent1 = selected_population[i]
                parent2 = selected_population[min(i+1, self.population_size-1)]
                
                # 交叉
                if np.random.random() < self.crossover_rate:
                    child1, child2 = self._crossover(parent1, parent2)
                else:
                    child1, child2 = parent1.copy(), parent2.copy()
                
                # 变异
                child1 = self._mutation(child1)
                child2 = self._mutation(child2)
                
                new_population.extend([child1, child2])
            
            # 更新种群
            population = np.array(new_population[:self.population_size])
            fitness_values = np.array([self.evaluate_fitness(ind, objective_function) for ind in population])
            
            # 更新最优解
            current_best_idx = np.argmax(fitness_values)
            if fitness_values[current_best_idx] > best_fitness:
                best_solution = population[current_best_idx].copy()
                best_fitness = fitness_values[current_best_idx]
            
            self.convergence_history.append(best_fitness)
            
            # 记录进度
            best_solution_dict = {name: value for name, value in zip(self.var_names, best_solution)}
            self._log_progress(generation + 1, best_fitness, best_solution_dict)
            
            # 检查收敛
            if len(self.convergence_history) > 10:
                recent_improvement = abs(self.convergence_history[-1] - self.convergence_history[-10])
                if recent_improvement < self.convergence_threshold:
                    break
        
        # 构建结果
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        best_solution_dict = {name: value for name, value in zip(self.var_names, best_solution)}
        
        result = OptimizationResult(
            algorithm="GA",
            success=True,
            message=f"遗传算法优化完成，共进行{generation+1}代进化",
            best_solution=best_solution_dict,
            best_fitness=best_fitness,
            iterations_completed=generation+1,
            convergence_achieved=recent_improvement < self.convergence_threshold if 'recent_improvement' in locals() else False,
            convergence_history=self.convergence_history,
            total_evaluations=self.total_evaluations,
            execution_time=execution_time,
            timestamp=end_time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return result
    
    def _selection(self, population: np.ndarray, fitness_values: np.ndarray) -> np.ndarray:
        """锦标赛选择"""
        selected = []
        tournament_size = 3
        
        for _ in range(self.population_size):
            # 随机选择tournament_size个个体
            tournament_indices = np.random.choice(len(population), tournament_size, replace=False)
            tournament_fitness = fitness_values[tournament_indices]
            
            # 选择最优个体
            winner_idx = tournament_indices[np.argmax(tournament_fitness)]
            selected.append(population[winner_idx].copy())
        
        return np.array(selected)
    
    def _crossover(self, parent1: np.ndarray, parent2: np.ndarray) -> tuple:
        """单点交叉"""
        crossover_point = np.random.randint(1, len(parent1))
        
        child1 = np.concatenate([parent1[:crossover_point], parent2[crossover_point:]])
        child2 = np.concatenate([parent2[:crossover_point], parent1[crossover_point:]])
        
        return self.clip_solution(child1), self.clip_solution(child2)
    
    def _mutation(self, individual: np.ndarray) -> np.ndarray:
        """高斯变异"""
        mutated = individual.copy()
        
        for i in range(len(individual)):
            if np.random.random() < self.mutation_rate:
                # 高斯变异
                min_val, max_val = self.bounds[i]
                mutation_strength = (max_val - min_val) * 0.1  # 10%的变异强度
                mutated[i] += np.random.normal(0, mutation_strength)
        
        return self.clip_solution(mutated)

# ---------- 粒子群算法实现 ----------

class ParticleSwarmOptimization(BaseOptimizer):
    """粒子群优化算法"""
    
    def __init__(self, params: OptimizationParams):
        super().__init__(params)
        self.inertia_weight = params.inertia_weight
        self.cognitive_coefficient = params.cognitive_coefficient
        self.social_coefficient = params.social_coefficient
    
    def optimize(self, objective_function: Callable) -> OptimizationResult:
        """执行粒子群优化"""
        start_time = datetime.now()
        
        # 初始化粒子群
        particles = np.array([self.generate_random_solution() for _ in range(self.population_size)])
        velocities = np.zeros_like(particles)
        
        # 记录个体最优和全局最优
        personal_best_positions = particles.copy()
        personal_best_fitness = np.array([self.evaluate_fitness(p, objective_function) for p in particles])
        
        global_best_idx = np.argmax(personal_best_fitness)
        global_best_position = particles[global_best_idx].copy()
        global_best_fitness = personal_best_fitness[global_best_idx]
        
        self.convergence_history.append(global_best_fitness)
        
        # 记录初始进度
        best_solution_dict = {name: value for name, value in zip(self.var_names, global_best_position)}
        self._log_progress(0, global_best_fitness, best_solution_dict)
        
        # 迭代优化
        for iteration in range(self.max_iterations):
            for i in range(self.population_size):
                # 更新速度
                r1, r2 = np.random.random(2)
                
                cognitive_component = self.cognitive_coefficient * r1 * (personal_best_positions[i] - particles[i])
                social_component = self.social_coefficient * r2 * (global_best_position - particles[i])
                
                velocities[i] = (self.inertia_weight * velocities[i] + 
                               cognitive_component + social_component)
                
                # 更新位置
                particles[i] = particles[i] + velocities[i]
                particles[i] = self.clip_solution(particles[i])
                
                # 评估适应度
                current_fitness = self.evaluate_fitness(particles[i], objective_function)
                
                # 更新个体最优
                if current_fitness > personal_best_fitness[i]:
                    personal_best_positions[i] = particles[i].copy()
                    personal_best_fitness[i] = current_fitness
                    
                    # 更新全局最优
                    if current_fitness > global_best_fitness:
                        global_best_position = particles[i].copy()
                        global_best_fitness = current_fitness
            
            self.convergence_history.append(global_best_fitness)
            
            # 记录进度
            best_solution_dict = {name: value for name, value in zip(self.var_names, global_best_position)}
            self._log_progress(iteration + 1, global_best_fitness, best_solution_dict)
            
            # 检查收敛
            if len(self.convergence_history) > 10:
                recent_improvement = abs(self.convergence_history[-1] - self.convergence_history[-10])
                if recent_improvement < self.convergence_threshold:
                    break
        
        # 构建结果
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        best_solution_dict = {name: value for name, value in zip(self.var_names, global_best_position)}
        
        result = OptimizationResult(
            algorithm="PSO",
            success=True,
            message=f"粒子群优化完成，共进行{iteration+1}次迭代",
            best_solution=best_solution_dict,
            best_fitness=global_best_fitness,
            iterations_completed=iteration+1,
            convergence_achieved=recent_improvement < self.convergence_threshold if 'recent_improvement' in locals() else False,
            convergence_history=self.convergence_history,
            total_evaluations=self.total_evaluations,
            execution_time=execution_time,
            timestamp=end_time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return result

# ---------- 优化工具类 ----------

class OptimizationTool(BaseTool):
    """统一优化工具"""
    
    name: str = "optimization_tool"
    description: str = """微波器件设计优化工具，支持遗传算法(GA)和粒子群优化(PSO)算法。
    
    **功能特点**：
    - 支持多变量、多目标优化
    - 提供GA和PSO两种优化算法
    - 自动保存优化结果和收敛历史
    - 支持目标函数的最小化、最大化和目标值优化
    
    **输入参数**：
    - algorithm: 优化算法（"GA"或"PSO"）
    - variables: 优化变量列表，每个变量包含name、min_value、max_value等
    - objectives: 优化目标列表，每个目标包含name、target_type、weight等
    - population_size: 种群大小（默认50）
    - max_iterations: 最大迭代次数（默认100）
    - 其他算法特定参数
    
    **使用示例**：
    适用于滤波器、天线、耦合器等微波器件的参数优化，如优化S参数、VSWR、带宽等性能指标。
    """
    
    args_schema: type = OptimizationParams
    
    def _run(self, **kwargs) -> str:
        """执行优化"""
        try:
            # 处理LangChain传递的参数
            if 'kwargs' in kwargs:
                actual_kwargs = kwargs['kwargs']
            else:
                actual_kwargs = kwargs
            
            # 解析参数
            params = OptimizationParams(**actual_kwargs)
            
            # 验证参数
            if not params.variables:
                return "错误：未定义优化变量"
            
            if not params.objectives:
                return "错误：未定义优化目标"
            
            # 创建优化器
            if params.algorithm.upper() == "GA":
                optimizer = GeneticAlgorithm(params)
            elif params.algorithm.upper() == "PSO":
                optimizer = ParticleSwarmOptimization(params)
            else:
                return f"错误：不支持的优化算法 '{params.algorithm}'。支持的算法：GA, PSO"
            
            # 设置进度监控回调
            def progress_callback(progress_info):
                generation = progress_info['generation']
                best_fitness = progress_info['best_fitness']
                print(f"第 {generation} 代: 最优适应度 = {best_fitness:.6f}")
                
                # 每10代显示一次最优解
                if generation % 10 == 0 and generation > 0:
                    print(f"  当前最优解: {progress_info['best_solution']}")
            
            optimizer.set_progress_callback(progress_callback)
            
            print(f"开始执行 {params.algorithm} 优化...")
            print(f"种群大小: {params.population_size}, 最大迭代次数: {params.max_iterations}")
            
            # 定义真实的HFSS仿真目标函数
            def hfss_objective_function(solution_dict: Dict[str, float]) -> Dict[str, float]:
                """真实的HFSS仿真目标函数评估"""
                try:
                    # 查找最新的HFSS项目
                    project_path = self._find_latest_hfss_project()
                    if not project_path:
                        raise Exception("未找到HFSS项目文件")
                    
                    # 连接到HFSS项目并更新参数
                    hfss = None
                    try:
                        hfss = Hfss(project=project_path, non_graphical=True, new_desktop=False)
                        
                        # 更新设计参数
                        for param_name, param_value in solution_dict.items():
                            if param_name in hfss.variable_manager.variables:
                                hfss[param_name] = f"{param_value}mm"
                        
                        # 运行仿真
                        setup_name = "MainSetup"
                        if setup_name in [s.name for s in hfss.setups]:
                            setup = hfss.get_setup(setup_name)
                            setup.analyze()
                        
                        # 提取S参数数据
                        sweep_name = "BroadbandSweep"
                        solution_data = hfss.post.get_solution_data(
                            expressions=["S(1,1)", "S(2,1)"],
                            setup_sweep_name=f"{setup_name} : {sweep_name}"
                        )
                        
                        if solution_data:
                            # 计算性能指标
                            freq = np.array(solution_data.primary_sweep_values)
                            s11_real = np.array(solution_data.data_real("S(1,1)"))
                            s11_imag = np.array(solution_data.data_imag("S(1,1)"))
                            s21_real = np.array(solution_data.data_real("S(2,1)"))
                            s21_imag = np.array(solution_data.data_imag("S(2,1)"))
                            
                            # 计算幅度（dB）
                            s11_mag = 20 * np.log10(np.sqrt(s11_real**2 + s11_imag**2))
                            s21_mag = 20 * np.log10(np.sqrt(s21_real**2 + s21_imag**2))
                            
                            # 计算VSWR
                            s11_linear = np.sqrt(s11_real**2 + s11_imag**2)
                            vswr = (1 + s11_linear) / (1 - s11_linear + 1e-12)
                            
                            # 计算目标值（在工作频段内）
                            work_band_mask = (freq >= 2.0e9) & (freq <= 8.0e9)  # 2-8 GHz工作频段
                            
                            # S21目标：通带内插入损耗最小（越接近0dB越好）
                            s21_target = -np.mean(np.abs(s21_mag[work_band_mask]))
                            
                            # S11目标：回波损耗最大（越负越好）
                            s11_target = np.mean(s11_mag[work_band_mask])
                            
                            # VSWR目标：最小化
                            vswr_target = np.mean(vswr[work_band_mask])
                            
                            return {
                                "S21": float(s21_target),
                                "S11": float(s11_target), 
                                "VSWR": float(vswr_target)
                            }
                        else:
                            raise Exception("无法获取仿真数据")
                            
                    finally:
                        if hfss:
                            hfss.close_project()
                            
                except Exception as e:
                    print(f"HFSS仿真评估失败: {e}")
                    # 返回惩罚值
                    return {
                        "S21": -100.0,
                        "S11": 0.0,
                        "VSWR": 10.0
                    }
            
            # 验证HFSS项目是否存在
            project_path = self._find_latest_hfss_project()
            if not project_path:
                return "❌ 错误：未找到HFSS项目文件，请先创建并仿真一个HFSS项目"
            
            print(f"找到HFSS项目: {project_path}")
            
            # 执行优化
            result = optimizer.optimize(hfss_objective_function)
            
            # 保存结果
            if params.save_results:
                result_file = self._save_results(result, params)
                result.result_file = result_file
            
            # 格式化返回消息
            return self._format_result_message(result)
            
        except Exception as e:
            return f"优化执行错误: {str(e)}"
    
    async def _arun(self, **kwargs) -> str:
        """异步执行（调用同步方法）"""
        return self._run(**kwargs)
    
    def _save_results(self, result: OptimizationResult, params: OptimizationParams) -> str:
        """保存优化结果"""
        try:
            # 确保结果目录存在
            results_dir = Path(params.results_dir)
            results_dir.mkdir(exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"optimization_result_{result.algorithm.lower()}_{timestamp}.json"
            filepath = results_dir / filename
            
            # 保存结果
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result.dict(), f, ensure_ascii=False, indent=2)
            
            # 生成详细报告
            self._generate_detailed_report(result, params, results_dir, timestamp)
            
            print(f"优化结果已保存到: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"保存结果失败: {str(e)}")
            return ""
    
    def _generate_detailed_report(self, result: OptimizationResult, params: OptimizationParams, results_dir: Path, timestamp: str):
        """生成详细的优化报告"""
        try:
            report_filename = f"optimization_report_{result.algorithm.lower()}_{timestamp}.md"
            report_filepath = results_dir / report_filename
            
            with open(report_filepath, 'w', encoding='utf-8') as f:
                f.write(f"# 优化报告 - {result.algorithm}\n\n")
                f.write(f"**生成时间**: {result.timestamp}\n\n")
                
                # 优化配置
                f.write("## 优化配置\n\n")
                f.write(f"- **算法**: {result.algorithm}\n")
                f.write(f"- **种群大小**: {params.population_size}\n")
                f.write(f"- **最大迭代次数**: {params.max_iterations}\n")
                f.write(f"- **收敛阈值**: {params.convergence_threshold}\n\n")
                
                # 优化变量
                f.write("## 优化变量\n\n")
                f.write("| 变量名 | 最小值 | 最大值 | 初始值 | 描述 |\n")
                f.write("|--------|--------|--------|--------|------|\n")
                for var in params.variables:
                    initial = var.initial_value if var.initial_value is not None else "N/A"
                    f.write(f"| {var.name} | {var.min_value} | {var.max_value} | {initial} | {var.description} |\n")
                f.write("\n")
                
                # 优化目标
                f.write("## 优化目标\n\n")
                f.write("| 目标名 | 类型 | 目标值 | 权重 | 描述 |\n")
                f.write("|--------|------|--------|------|------|\n")
                for obj in params.objectives:
                    target = obj.target_value if obj.target_value is not None else "N/A"
                    f.write(f"| {obj.name} | {obj.target_type} | {target} | {obj.weight} | {obj.description} |\n")
                f.write("\n")
                
                # 优化结果
                f.write("## 优化结果\n\n")
                f.write(f"- **状态**: {'成功' if result.success else '失败'}\n")
                f.write(f"- **迭代次数**: {result.iterations_completed}\n")
                f.write(f"- **收敛状态**: {'已收敛' if result.convergence_achieved else '未完全收敛'}\n")
                f.write(f"- **执行时间**: {result.execution_time:.2f}秒\n")
                f.write(f"- **总评估次数**: {result.total_evaluations}\n")
                f.write(f"- **最优适应度**: {result.best_fitness:.6f}\n\n")
                
                # 最优解
                f.write("## 最优解\n\n")
                f.write("| 变量名 | 最优值 |\n")
                f.write("|--------|--------|\n")
                for var_name, var_value in result.best_solution.items():
                    f.write(f"| {var_name} | {var_value:.6f} |\n")
                f.write("\n")
                
                # 收敛历史
                f.write("## 收敛历史\n\n")
                f.write("```\n")
                for i, fitness in enumerate(result.convergence_history):
                    f.write(f"Generation {i}: {fitness:.6f}\n")
                f.write("```\n")
            
            print(f"详细报告已保存到: {report_filepath}")
            
        except Exception as e:
            print(f"生成详细报告失败: {str(e)}")
    
    def _find_latest_hfss_project(self) -> Optional[str]:
        """查找最新的HFSS项目文件"""
        try:
            # 在当前目录和子目录中查找.aedt文件
            current_dir = Path.cwd()
            aedt_files = list(current_dir.rglob("*.aedt"))
            
            if not aedt_files:
                return None
            
            # 返回最新修改的项目文件
            latest_file = max(aedt_files, key=lambda f: f.stat().st_mtime)
            return str(latest_file)
            
        except Exception as e:
            print(f"查找HFSS项目文件失败: {e}")
            return None
    
    def _format_result_message(self, result: OptimizationResult) -> str:
        """格式化结果消息"""
        message = f"""🎯 {result.algorithm}优化完成！

📊 **优化结果**：
- 算法：{result.algorithm}
- 状态：{'✅ 成功' if result.success else '❌ 失败'}
- 迭代次数：{result.iterations_completed}/{result.iterations_completed}
- 收敛状态：{'✅ 已收敛' if result.convergence_achieved else '⏳ 未完全收敛'}
- 执行时间：{result.execution_time:.2f}秒
- 总评估次数：{result.total_evaluations}

🏆 **最优解**：
"""
        
        for var_name, var_value in result.best_solution.items():
            message += f"- {var_name}: {var_value:.6f}\n"
        
        message += f"\n📈 **最优适应度**: {result.best_fitness:.6f}\n"
        
        if result.result_file:
            message += f"\n💾 **结果文件**: {result.result_file}\n"
            message += f"📋 **详细报告已生成**，包含完整的优化历史和分析\n"
        
        message += f"\n⏰ **完成时间**: {result.timestamp}"
        
        return message

# 创建工具实例
OPTIMIZE_DESIGN = OptimizationTool()