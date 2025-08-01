"""
API服务器启动器

提供API服务器的启动和配置功能
"""

import uvicorn

from voice_dialogue.utils.logger import logger


def launch_api_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    启动API服务器

    Args:
        host (str): 服务器主机地址，默认为 "0.0.0.0"
        port (int): 服务器端口，默认为 8000
        reload (bool): 是否启用热重载，默认为 False
    """
    logger.info(f'{"=" * 80}')
    logger.info(f'正在启动API服务器...')
    logger.info(f"服务器地址: http://{host}:{port}")
    logger.info(f"API文档: http://{host}:{port}/docs")
    logger.info(f"热重载: {'启用' if reload else '禁用'}")
    logger.info(f'{"=" * 80}')

    uvicorn_config = uvicorn.Config(
        "voice_dialogue.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        log_config=None,  # 不使用uvicorn的日志配置文件
        use_colors=True,  # 启用彩色日志
    )
    server = uvicorn.Server(uvicorn_config)
    server.run()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="VoiceDialogue API服务器")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机地址")
    parser.add_argument("--port", "-p", type=int, default=8000, help="服务器端口")
    parser.add_argument("--reload", action="store_true", help="启用热重载")

    args = parser.parse_args()
    launch_api_server(args.host, args.port, args.reload)
