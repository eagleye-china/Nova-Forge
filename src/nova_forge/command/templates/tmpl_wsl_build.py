# src/nova_forge/command/templates/tmpl_wsl_build.py

WSL_BUILD_SCRIPT_TMPL = r"""#!/bin/bash
set -e

WIN_PATH="$1"
if [ -z "$WIN_PATH" ]; then
    echo "❌ 错误: 缺少项目路径参数。"
    exit 1
fi

PROJECT_NAME=$(basename "$WIN_PATH")
BUILD_DIR="$HOME/NovaBuildTemp/$PROJECT_NAME"
ENV_NAME="nova_env_311"
WHEEL_SRC="/root/Nova-Copilot"

echo "🚀 [Nova-Forge] 启动 APK 自动化打包任务..."
echo "📂 目标项目: $WIN_PATH"

# 1. 同步代码到 Linux 本地（避开 NTFS 权限坑）
echo "📦 正在将项目同步到 Linux 本地构建区..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude='.git' --exclude='.venv' --exclude='venv' "$WIN_PATH/" "$BUILD_DIR/"
else
    cp -r "$WIN_PATH/"* "$BUILD_DIR/" 2>/dev/null || true
    rm -rf "$BUILD_DIR/.git" "$BUILD_DIR/venv" "$BUILD_DIR/.venv"
fi

cd "$BUILD_DIR"

# 2. 准备 .whl 依赖包 (去核心库借)
if ! ls *.whl 1> /dev/null 2>&1; then
    echo "🔍 未发现 Android .whl 依赖，正在从核心库注入 6.12.0 轮子..."
    cp "$WHEEL_SRC"/*.whl . 2>/dev/null || true
fi

# 3. 激活纯净环境
echo "🐍 激活虚拟环境 ($ENV_NAME)..."
source "$HOME/$ENV_NAME/bin/activate"
export PATH="/root/$ENV_NAME/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# 4. 执行打包
echo "🔥 开始编译 APK (这可能需要几分钟)..."
pyside6-android-deploy \
  --ndk-path "$HOME/.pyside6-android-deploy/android-ndk/android-ndk-r28c" \
  --wheel-pyside pyside6-6.12.0-6.12.0-cp310-abi3-android_aarch64.whl \
  --wheel-shiboken shiboken6-6.12.0-6.12.0-cp310-abi3-android_aarch64.whl \
  --no-install

# 5. 抓取 APK 并回传 Windows
APK_FILE=$(find . -name "*.apk" | head -n 1)
if [ -n "$APK_FILE" ]; then
    echo "✅ 打包成功！APK 路径: $APK_FILE"
    cp "$APK_FILE" "$WIN_PATH/"
    echo "🎉 已将 APK 自动复制回 Windows 目录: $WIN_PATH"
else
    echo "❌ 打包失败，未找到 APK 文件。"
    exit 1
fi
"""
