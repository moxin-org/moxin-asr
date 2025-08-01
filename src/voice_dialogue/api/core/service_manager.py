import time
from dataclasses import dataclass
from typing import Dict, List, Callable, Any, Optional

from voice_dialogue.utils.logger import logger


@dataclass
class ServiceDefinition:
    """服务定义类，用于配置化管理服务"""
    name: str
    factory: Callable[[], Any]
    dependencies: List[str] = None
    required: bool = True
    startup_timeout: int = 60  # 启动超时时间（秒）
    health_check: Optional[Callable[[Any], bool]] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class ServiceManager:
    """服务管理器，负责服务的统一启动、停止和监控"""

    def __init__(self):
        self.services: Dict[str, Any] = {}
        self.startup_errors: Dict[str, str] = {}
        self.startup_times: Dict[str, float] = {}
        self._shutdown_hooks: List[Callable] = []

    def add_shutdown_hook(self, hook: Callable):
        """添加关闭钩子函数"""
        self._shutdown_hooks.append(hook)

    def start_service(self, service_def: ServiceDefinition) -> bool:
        """启动单个服务"""
        start_time = time.time()
        try:
            logger.info(f"正在启动服务: {service_def.name}")

            # 检查依赖服务
            if not self._check_dependencies(service_def.dependencies):
                raise RuntimeError(f"服务 {service_def.name} 的依赖服务未就绪")

            service = service_def.factory()
            service.daemon = True
            service.start()

            # 等待服务就绪
            if not self._wait_for_service_ready(service, service_def):
                raise TimeoutError(f"服务 {service_def.name} 启动超时")

            # 健康检查
            if service_def.health_check and not service_def.health_check(service):
                raise RuntimeError(f"服务 {service_def.name} 健康检查失败")

            self.services[service_def.name] = service
            self.startup_times[service_def.name] = time.time() - start_time

            logger.info(f"服务 {service_def.name} 启动成功，耗时: {self.startup_times[service_def.name]:.2f}秒")
            return True

        except Exception as e:
            error_msg = f"服务 {service_def.name} 启动失败: {e}"
            logger.error(error_msg, exc_info=True)
            self.startup_errors[service_def.name] = error_msg

            if service_def.required:
                raise RuntimeError(error_msg)
            return False

    def _check_dependencies(self, dependencies: List[str]) -> bool:
        """检查依赖服务是否已启动并就绪"""
        for dep in dependencies:
            if dep not in self.services:
                logger.error(f"依赖服务 {dep} 未启动")
                return False
            if not self.services[dep].is_ready:
                logger.error(f"依赖服务 {dep} 未就绪")
                return False
        return True

    def _wait_for_service_ready(self, service: Any, service_def: ServiceDefinition) -> bool:
        """等待服务就绪"""
        timeout = service_def.startup_timeout
        start_time = time.time()

        while not service.is_ready and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        return service.is_ready

    def stop_all_services(self):
        """停止所有服务"""
        logger.info("正在停止所有服务...")

        # 执行关闭钩子
        for hook in self._shutdown_hooks:
            try:
                hook()
            except Exception as e:
                logger.error(f"执行关闭钩子时发生错误: {e}", exc_info=True)

        # 按启动顺序的逆序停止服务
        for service_name in reversed(list(self.services.keys())):
            self._stop_single_service(service_name)

        self.services.clear()

    def _stop_single_service(self, service_name: str):
        """停止单个服务"""
        try:
            service = self.services[service_name]
            logger.info(f"正在停止服务: {service_name}")

            service.exit()

            # 等待服务停止（最多等待5秒）
            timeout = 5
            start_time = time.time()
            while service.is_alive() and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            if service.is_alive():
                logger.warning(f"服务 {service_name} 未能在超时时间内停止")
            else:
                logger.info(f"服务 {service_name} 已停止")

        except Exception as e:
            logger.error(f"停止服务 {service_name} 时发生错误: {e}", exc_info=True)

    def get_service_status(self) -> dict:
        """获取所有服务状态"""
        return {
            "total_services": len(self.services),
            "startup_errors": len(self.startup_errors),
            "startup_times": self.startup_times.copy(),
            "errors": self.startup_errors.copy(),
            "services": {
                name: {
                    "running": service.is_alive(),
                    "ready": service.is_ready
                }
                for name, service in self.services.items()
            }
        }

    def get_service(self, name: str) -> Optional[Any]:
        """获取指定服务实例"""
        return self.services.get(name)

    def is_service_running(self, name: str) -> bool:
        """检查服务是否正在运行"""
        service = self.services.get(name)
        return service is not None and service.is_alive()
