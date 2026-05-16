#!/bin/bash
# QQ相册下载工具 - macOS打包脚本

echo "=== QQ相册下载工具 - macOS打包 ==="
echo ""

# 检查依赖
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

if ! python3 -c "import customtkinter" 2>/dev/null; then
    echo "安装依赖..."
    pip3 install -r requirements.txt
fi

if ! command -v pyinstaller &> /dev/null; then
    echo "安装 PyInstaller..."
    pip3 install pyinstaller
fi

# 打包（使用 onedir 模式生成 .app 包）
echo ""
echo "开始打包..."
pyinstaller --name "QQ相册下载工具" \
             --windowed \
             --clean \
             --add-data "qq_album_downloader.py:." \
             qq_album_downloader.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ 打包成功！"
    echo "APP位置: dist/QQ相册下载工具.app"
else
    echo ""
    echo "✗ 打包失败"
    exit 1
fi
