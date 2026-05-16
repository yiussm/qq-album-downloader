# QQ相册批量原图下载工具

批量下载QQ空间相册原图，支持多相册选择、自动创建目录、多线程下载。

## 功能

- QQ空间Cookie登录
- 获取所有相册列表（含加密相册）
- 批量下载原图（非缩略图）
- 自动按相册创建文件夹
- 多线程下载 + 实时进度

## 安装依赖

```bash
pip install -r 源码/requirements.txt
```

## 使用

```bash
python3.11 源码/qq_photo_v4.py
```

1. 打开浏览器登录 qzone.qq.com
2. F12 → Network → 复制 Cookie
3. 粘贴 Cookie + 输入 QQ 号
4. 点击「获取相册列表」→ 勾选要下载的相册
5. 选择保存目录 → 「开始下载」

## 打包

```bash
./源码/build_macos.sh
```

## 技术说明

- API: mobile.qzone.qq.com / h5.qzone.qq.com
- 认证: p_skey → g_tk
- UI: customtkinter

## 自动构建

GitHub Actions 自动构建 macOS + Windows 版本。