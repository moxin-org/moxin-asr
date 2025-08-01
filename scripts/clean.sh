#!/bin/bash
# scripts/clean.sh

echo "--- 开始清理项目 ---"

# 删除 PyInstaller 构建相关的文件
rm -rf ./dist
rm -rf ./build/voice_dialogue

# 删除 Electron 相关文件
rm -rf ./electron-app/dist
rm -rf ./electron-app/node_modules
rm -rf ./electron-app/python-dist
rm -f ./electron-app/package-lock.json

echo "--- 清理完成 ---"
