#!/bin/bash
# scripts/build.sh

# 脚本出错时立即退出
set -e

# --- 步骤 1: 清理环境 ---
echo ">>> 步骤 1/3: 清理旧的构建产物..."
bash scripts/clean.sh

# --- 步骤 2: 打包 Python 应用 ---
echo ">>> 步骤 2/3: 打包 Python 后端..."
bash scripts/build-python.sh

# --- 步骤 3: 构建 Electron 应用 ---
echo ">>> 步骤 3/3: 构建 Electron 前端..."
bash scripts/build-electron.sh

# --- 完成 ---
echo "-------------------------------------"
echo "✅ 构建成功!"
echo "macOS 应用位于: electron-app/dist/"
echo "-------------------------------------"
