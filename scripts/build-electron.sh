#!/bin/bash
# scripts/build-electron.sh

# 脚本出错时立即退出
set -e

# 进入 Electron 应用目录
cd electron-app

# --- 安装依赖 ---
echo "--- 安装 Node.js 依赖 ---"
npm install

# --- 构建 Electron 应用 ---
echo "--- 开始构建 Electron 应用 (macOS) ---"
npm run build-mac

echo "--- Electron 应用构建完成 ---"
# 构建产物位于 electron-app/dist/ 目录
