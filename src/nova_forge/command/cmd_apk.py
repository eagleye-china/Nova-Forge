# src/nova_forge/command/cmd_apk.py
# 创建时间：星期二 2026-11-24 21:39

import base64
import os
import subprocess
import sys
from pathlib import Path

# ✅ 导入抽离出来的脚本模板
from ..templates.tmpl_wsl_build import WSL_BUILD_SCRIPT_TMPL


def _win_to_wsl_path(win_path: str) -> str:
    p = Path(win_path).resolve()
    drive = p.drive[0].lower()
    parts = p.parts[1:]
    return f"/mnt/{drive}/" + "/".join(parts)


def inject_wsl_script():
    """将打包脚本无感写入 WSL 并赋权"""
    print("🛠️ [Nova-Forge] 正在同步 WSL 核心构建引擎...")
    # 使用抽离出来的模板
    b64_script = base64.b64encode(WSL_BUILD_SCRIPT_TMPL.encode('utf-8')).decode('utf-8')
    cmd = f"echo '{b64_script}' | base64 -d > ~/wsl_build_apk.sh && chmod +x ~/wsl_build_apk.sh"
    subprocess.run(["wsl", "-e", "bash", "-c", cmd], check=True, capture_output=True)


def check_wsl_prerequisites():
    """检查并自动配置 WSL 环境"""
    print("🔍 [Nova-Forge] 正在扫描 WSL2 运行环境...")
    try:
        # 1. 检查 WSL 是否连通
        subprocess.run(["wsl", "-e", "echo", "ok"], check=True, capture_output=True, timeout=5)

        # 2. 检查并自动创建虚拟环境
        res = subprocess.run(["wsl", "-e", "bash", "-c", "test -d ~/nova_env_311 && echo 'yes' || echo 'no'"],
                             capture_output=True, text=True)
        if "yes" not in res.stdout:
            print("⚙️ [环境配置] 发现 WSL 缺少虚拟环境，正在自动为您创建 (nova_env_311) 并安装依赖...")
            create_cmd = "python3 -m venv ~/nova_env_311 && source ~/nova_env_311/bin/activate && pip install --upgrade pip && pip install buildozer cython==0.29.33 -i https://pypi.org/simple/"
            subprocess.run(["wsl", "-e", "bash", "-c", create_cmd], check=True)
            print("✅ 虚拟环境 nova_env_311 已成功创建并初始化！")
        else:
            print("✅ [环境检查] WSL 虚拟环境 (nova_env_311) 已存在，跳过创建。")

        # 3. 无感注入最新打包脚本
        inject_wsl_script()
        return True, "环境检查通过"
    except FileNotFoundError:
        return False, "未检测到 WSL 命令，请确保 Windows 已安装 WSL2 并添加了 Ubuntu 发行版。"
    except subprocess.TimeoutExpired:
        return False, "WSL 响应超时，请尝试在 PowerShell 中执行 'wsl --shutdown' 后重试。"
    except Exception as e:
        return False, f"检查环境时出错: {e}"


def run_apk_build_interactive():
    """交互式执行 APK 自动化构建"""
    print("\n" + "=" * 60)
    print("🔥 欢迎使用 Nova-Forge 安卓 APK 自动化锻造流水线")
    print("=" * 60)
    print("📋 【起飞前安全检查清单】")
    print("  [系统] Windows WSL2 运行环境")
    print("  [环境] Python3 虚拟环境 & 核心编译链 (自动检测/安装)")
    print("  [依赖] Android NDK 及 6.12.0 本地轮子包 (自动寻找/注入)")
    print("-" * 60)

    is_ready, msg = check_wsl_prerequisites()
    if not is_ready:
        print(f"❌ [环境异常] {msg}")
        print("💡 提示:请按照《Nova 安卓打包指南》确认基础环境。")
        print("=" * 60 + "\n")
        return

    print("\n✅ [Nova-Forge] 引擎自检完毕，随时可以起飞！\n")

    win_path_input = input("📱 请输入项目的完整 Windows 绝对路径 (如 D:\\MyProjects\\Nova-Copilot) []:\n> ").strip()
    win_path = win_path_input.strip('"').strip("'")

    if not win_path:
        print("❌ [Nova-Forge] 路径不能为空，已取消打包。")
        return

    win_path = os.path.abspath(win_path)
    if not os.path.exists(win_path):
        print(f"❌ [Nova-Forge] 错误:指定的 Windows 路径不存在 -> {win_path}")
        return

    print(f"\n🔄 [Nova-Forge] Windows 路径已锁定: {win_path}")
    wsl_path = _win_to_wsl_path(win_path)
    print(f"🐧 [Nova-Forge] 自动转换为 WSL 路径: {wsl_path}")

    bash_cmd = f"bash ~/wsl_build_apk.sh '{wsl_path}'"

    print("\n🚀 [Nova-Forge] 正在将任务移交 WSL 引擎执行，请稍候...\n" + "=" * 60)

    try:
        process = subprocess.Popen(
            ["wsl", "-e", "bash", "-c", bash_cmd],
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        process.wait()

        print("=" * 60)
        if process.returncode == 0:
            print("🎉 [Nova-Forge] APK 自动化构建流水线执行完毕！请前往项目根目录查看。")
        else:
            print("❌ [Nova-Forge] 打包过程中出现错误，请检查上方 WSL 日志。")

    except FileNotFoundError:
        print("❌ [Nova-Forge] 错误:未找到 wsl 命令。请确保您的系统已安装并配置好 WSL2。")
    except Exception as e:
        print(f"❌ [Nova-Forge] 发生未知异常: {e}")
    finally:
        print("\n🛑 [Nova-Forge] 正在关闭 WSL 后台引擎释放内存...")
        subprocess.run(["wsl", "--shutdown"], capture_output=True)
        print("✅ 已安全关闭 WSL。")
