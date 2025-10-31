import os
import sys
from pathlib import Path
from typing import Tuple


def _get_roots() -> Tuple[str, str]:
    if getattr(sys, 'frozen', False):
        root_dir = Path(sys.executable).parent
        package_dir = root_dir
    else:
        work_dir = Path(__file__).resolve().parent
        root_dir = work_dir.parent  # util 的上一层就是项目根目录（与 main.py 同级）
        package_dir = work_dir.parent
    return str(root_dir), str(package_dir)


ROOT_DIR, PACKAGE_DIR = _get_roots()

print(f"[路径] 项目根目录: {ROOT_DIR}")
print(f"[路径] 包目录: {PACKAGE_DIR}")

# 仅保留配置目录，避免生成无关目录（如 data、output 等）
CONFIG_DIR = str(Path(ROOT_DIR) / "config")
print(f"[路径] 配置目录: {CONFIG_DIR}")
os.makedirs(CONFIG_DIR, exist_ok=True)
print(f"[路径] 配置目录已确保存在: {CONFIG_DIR}")

# 用户数据文件（账号密码等记忆化信息）
USER_DATA_PATH = str(Path(CONFIG_DIR) / "user_data.json")
print(f"[路径] 用户数据文件路径: {USER_DATA_PATH}")

# 应用配置文件（选择器、URL等配置信息）
APP_CONFIG_PATH = str(Path(CONFIG_DIR) / "app_config.json")
print(f"[路径] 应用配置文件路径: {APP_CONFIG_PATH}")

# 保持向后兼容
USER_SETTINGS_PATH = USER_DATA_PATH


