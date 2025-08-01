"""Apple Silicon 芯片信息获取工具"""

import json
import subprocess
import platform
from typing import Dict, Optional
from dataclasses import dataclass

__all__ = ('AppleSiliconInfo', 'get_apple_silicon_info')


@dataclass
class AppleSiliconInfo:
    """Apple Silicon 芯片信息"""
    chip_name: str  # 如 "Apple M1", "Apple M1 Pro", "Apple M2 Max"
    total_cores: int  # 总核心数
    performance_cores: int  # 性能核心数（P-cores）
    efficiency_cores: int  # 效率核心数（E-cores）
    gpu_cores: int  # GPU核心数
    memory_gb: int  # 内存大小（GB）
    is_apple_silicon: bool  # 是否为Apple Silicon


def _get_system_profiler_info() -> Optional[Dict]:
    """通过system_profiler获取硬件信息"""
    try:
        # 获取硬件信息
        result = subprocess.run([
            'system_profiler', 'SPHardwareDataType', '-json'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get('SPHardwareDataType', [{}])[0]
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        pass
    return None


def _parse_cpu_info_from_sysctl() -> Optional[Dict]:
    """通过sysctl获取CPU信息"""
    try:
        # 获取CPU核心信息
        result = subprocess.run([
            'sysctl', '-n', 
            'hw.perflevel0.physicalcpu',  # 性能核心数
            'hw.perflevel1.physicalcpu',  # 效率核心数
            'hw.logicalcpu',              # 逻辑核心数
            'hw.memsize'                  # 内存大小
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 4:
                return {
                    'performance_cores': int(lines[0]) if lines[0].isdigit() else 0,
                    'efficiency_cores': int(lines[1]) if lines[1].isdigit() else 0,
                    'total_cores': int(lines[2]) if lines[2].isdigit() else 0,
                    'memory_bytes': int(lines[3]) if lines[3].isdigit() else 0
                }
    except (subprocess.TimeoutExpired, ValueError, IndexError, FileNotFoundError):
        pass
    return None


def _get_gpu_cores_from_system_profiler() -> int:
    """获取GPU核心数"""
    try:
        result = subprocess.run([
            'system_profiler', 'SPDisplaysDataType', '-json'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            displays = data.get('SPDisplaysDataType', [])
            for display in displays:
                if 'sppci_cores' in display:
                    return int(display['sppci_cores'])
                # 根据芯片名称估算GPU核心数
                model = display.get('sppci_model', '').lower()
                if 'm1 max' in model:
                    return 32
                elif 'm1 pro' in model:
                    return 16 if '16-core' in model else 14
                elif 'm1' in model:
                    return 8 if '8-core' in model else 7
                elif 'm2 max' in model:
                    return 38
                elif 'm2 pro' in model:
                    return 19 if '19-core' in model else 16
                elif 'm2' in model:
                    return 10 if '10-core' in model else 8
                elif 'm3 max' in model:
                    return 40
                elif 'm3 pro' in model:
                    return 18 if '18-core' in model else 14
                elif 'm3' in model:
                    return 10 if '10-core' in model else 8
    except (subprocess.TimeoutExpired, json.JSONDecodeError, ValueError, FileNotFoundError):
        pass
    return 8  # 默认值


def get_apple_silicon_info() -> AppleSiliconInfo:
    """
    获取Apple Silicon芯片信息
    
    Returns:
        AppleSiliconInfo: 芯片信息对象
    """
    # 检查是否为Apple Silicon
    machine = platform.machine()
    is_apple_silicon = machine in ('arm64', 'arm64e') and platform.system() == 'Darwin'
    
    if not is_apple_silicon:
        return AppleSiliconInfo(
            chip_name="非Apple Silicon",
            total_cores=1,
            performance_cores=1,
            efficiency_cores=0,
            gpu_cores=0,
            memory_gb=8,
            is_apple_silicon=False
        )
    
    # 获取系统信息
    hw_info = _get_system_profiler_info()
    cpu_info = _parse_cpu_info_from_sysctl()
    
    # 解析芯片名称
    chip_name = "Apple Silicon"
    if hw_info and 'chip_type' in hw_info:
        chip_name = hw_info['chip_type']
    elif hw_info and 'cpu_type' in hw_info:
        chip_name = hw_info['cpu_type']
    
    # 解析核心信息
    performance_cores = 4  # 默认值
    efficiency_cores = 4   # 默认值
    total_cores = 8        # 默认值
    
    if cpu_info:
        performance_cores = cpu_info.get('performance_cores', performance_cores)
        efficiency_cores = cpu_info.get('efficiency_cores', efficiency_cores)
        total_cores = cpu_info.get('total_cores', total_cores)
    
    # 如果sysctl失败，尝试从芯片名称推断
    if performance_cores == 0 and efficiency_cores == 0:
        chip_lower = chip_name.lower()
        if 'm1 max' in chip_lower:
            performance_cores, efficiency_cores = 8, 2
        elif 'm1 pro' in chip_lower:
            performance_cores, efficiency_cores = 8, 2
        elif 'm1' in chip_lower:
            performance_cores, efficiency_cores = 4, 4
        elif 'm2 max' in chip_lower:
            performance_cores, efficiency_cores = 8, 4
        elif 'm2 pro' in chip_lower:
            performance_cores, efficiency_cores = 8, 4
        elif 'm2' in chip_lower:
            performance_cores, efficiency_cores = 4, 4
        elif 'm3' in chip_lower:
            if 'max' in chip_lower:
                performance_cores, efficiency_cores = 12, 4
            elif 'pro' in chip_lower:
                performance_cores, efficiency_cores = 8, 4
            else:
                performance_cores, efficiency_cores = 4, 4
        
        total_cores = performance_cores + efficiency_cores
    
    # 获取内存大小
    memory_gb = 8  # 默认值
    if cpu_info and 'memory_bytes' in cpu_info:
        memory_gb = cpu_info['memory_bytes'] // (1024 ** 3)
    elif hw_info and 'physical_memory' in hw_info:
        memory_str = hw_info['physical_memory'].replace(' GB', '').replace(',', '')
        try:
            memory_gb = int(memory_str)
        except ValueError:
            pass
    
    # 获取GPU核心数
    gpu_cores = _get_gpu_cores_from_system_profiler()
    
    return AppleSiliconInfo(
        chip_name=chip_name,
        total_cores=total_cores,
        performance_cores=performance_cores,
        efficiency_cores=efficiency_cores,
        gpu_cores=gpu_cores,
        memory_gb=memory_gb,
        is_apple_silicon=True
    )


def get_optimal_llama_cpp_config() -> Dict[str, int]:
    """
    根据Apple Silicon芯片信息获取最优的llama.cpp配置
    
    Returns:
        Dict[str, int]: 包含n_threads和n_ctx的配置
    """
    chip_info = get_apple_silicon_info()
    
    if not chip_info.is_apple_silicon:
        # 非Apple Silicon系统的默认配置
        return {
            'n_threads': 4,
            'n_ctx': 2048
        }
    
    # 对于Apple Silicon，只使用性能核心（P-cores）
    # 避免混合使用效率核心，以获得最佳性能
    n_threads = chip_info.performance_cores
    
    # 根据内存大小调整上下文窗口
    if chip_info.memory_gb >= 32:
        n_ctx = 4096
    elif chip_info.memory_gb >= 16:
        n_ctx = 2048
    else:
        n_ctx = 1024
    
    return {
        'n_threads': n_threads,
        'n_ctx': n_ctx
    }


if __name__ == '__main__':
    # 测试功能
    info = get_apple_silicon_info()
    print(f"芯片信息: {info}")
    
    config = get_optimal_llama_cpp_config()
    print(f"推荐配置: {config}") 