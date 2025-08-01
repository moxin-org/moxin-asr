#!/bin/bash
# scripts/build-python.sh

# 脚本出错时立即退出
set -e

# 激活Python虚拟环境
source .venv/bin/activate

# --- 配置 ---
# 应用名称
APP_NAME="voice_dialogue"
# PyInstaller 打包输出目录
PYINSTALLER_DIST_DIR="dist"
# Electron 应用中存放 Python 可执行文件的目录
ELECTRON_PYTHON_DIST_DIR="electron-app/python-dist"
# PyInstaller 构建目录
PYINSTALLER_BUILD_DIR="build/voice_dialogue"
# Spec 文件
SPEC_FILE="build/pyinstaller/${APP_NAME}.spec"

# --- 清理旧文件 ---
echo "--- 清理旧的 Python 构建文件 ---"
rm -rf "./${PYINSTALLER_DIST_DIR}"
rm -rf "./${PYINSTALLER_BUILD_DIR}"
rm -rf "./${ELECTRON_PYTHON_DIST_DIR}"
mkdir -p "./${ELECTRON_PYTHON_DIST_DIR}"

# --- 运行 PyInstaller ---
echo "--- 开始使用 PyInstaller 打包 Python 应用 ---"
pyinstaller --noconfirm \
    --clean \
    "${SPEC_FILE}"

# --- 复制可执行文件 ---
echo "--- 复制可执行文件到 Electron 目录 ---"
cp -r "./${PYINSTALLER_DIST_DIR}/${APP_NAME}/." "./${ELECTRON_PYTHON_DIST_DIR}/"
echo "可执行文件已复制到 ${ELECTRON_PYTHON_DIST_DIR}"


echo "--- Python 应用打包完成 ---"
