import json
import os
import requests
from typing import Any, Dict

from .paths import USER_DATA_PATH, APP_CONFIG_PATH


# 默认用户数据（账号密码等记忆化信息）
DEFAULT_USER_DATA: Dict[str, Any] = {
    "account": "",
    "password": "",
    "auto_ocr": True,
    "headless": False,
    "topmost": True,  # 窗口是否置顶
    "mode": "bm",  # 当前模式：bm(报名) | kw(考务)
    "kw_serial": "",  # 考务序列号
}

# 默认应用配置（选择器、URL等配置信息）
# 注意：每个选择器可以是字符串（使用默认selector_type）或对象（指定selector和selector_type）
DEFAULT_APP_CONFIG: Dict[str, Any] = {
    "login": {
        "bm": {
            "url": "http://bm.scs.gov.cn/pp/gkweb/core/web/ui/business/auth/login.html",
            "selector_type": "css",  # 默认选择器类型（向后兼容）
            "username": {
                "selector": ".input240",
                "selector_type": "css"
            },
            "password": {
                "selector": ".input240.password",
                "selector_type": "css"
            },
            "captcha_image": {
                "selector": "#captchaImg",
                "selector_type": "css"
            },
            "captcha_input": {
                "selector": "#captchaWord",
                "selector_type": "css"
            },
            "submit": {
                "selector": ".register_btn",
                "selector_type": "css"
            }
        },
        "kw": {
            "url": "",
            "selector_type": "css",  # 默认选择器类型（向后兼容）
            "username": "",
            "password": "",
            "serial": "",
            "captcha_image": "",
            "captcha_input": "",
            "submit": ""
        }
    },
    "loop_attempts": 3,
    # 配置更新源地址
    "config_sources": [
        "https://example.com/config1.json",
        "https://example.com/config2.json"
    ]
}


def _ensure_file(file_path: str, default_data: Dict[str, Any], file_name: str) -> None:
    """确保文件存在，不存在则创建默认文件"""
    settings_dir = os.path.dirname(file_path)
    print(f"[配置] {file_name}目录: {settings_dir}")
    os.makedirs(settings_dir, exist_ok=True)
    print(f"[配置] 目录已确保存在: {settings_dir}")
    print(f"[配置] {file_name}路径: {file_path}")
    if not os.path.exists(file_path):
        print(f"[配置] {file_name}不存在，创建默认配置...")
        _save_json(file_path, default_data)
        print(f"[配置] 默认{file_name}已保存到: {file_path}")
    else:
        print(f"[配置] {file_name}已存在: {file_path}")


def _load_json(file_path: str, default_data: Dict[str, Any], file_name: str) -> Dict[str, Any]:
    """加载JSON文件"""
    _ensure_file(file_path, default_data, file_name)
    try:
        print(f"[配置] 正在读取{file_name}: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"[配置] {file_name}读取成功: {file_path}")
        return data
    except Exception as e:
        print(f"[配置] {file_name}读取失败: {e}，使用默认配置")
        return dict(default_data)


def _save_json(file_path: str, data: Dict[str, Any]) -> None:
    """保存JSON文件"""
    try:
        print(f"[配置] 正在保存配置到: {file_path}")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[配置] 配置保存成功: {file_path}")
    except Exception as e:
        print(f"[配置] 配置保存失败: {e}，路径: {file_path}")


def _deep_merge(default: Dict[str, Any], got: Dict[str, Any]) -> Dict[str, Any]:
    """深度合并字典"""
    out = dict(default)
    for k, v in got.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


# ============ 辅助函数：解析选择器配置 ============

def parse_selector_config(element_config: Any, default_selector_type: str) -> tuple[str, str]:
    """
    解析选择器配置，支持两种格式：
    1. 字符串格式（向后兼容）："input240" -> ("input240", default_selector_type)
    2. 对象格式（新格式）：{"selector": "input240", "selector_type": "class_name"} -> ("input240", "class_name")
    
    Args:
        element_config: 元素配置（字符串或对象）
        default_selector_type: 默认选择器类型
    
    Returns:
        (selector, selector_type) 元组
    """
    if isinstance(element_config, str):
        # 字符串格式（向后兼容）
        return (element_config, default_selector_type)
    elif isinstance(element_config, dict):
        # 对象格式
        selector = element_config.get("selector", "")
        selector_type = element_config.get("selector_type", default_selector_type)
        return (selector, selector_type)
    else:
        # 空值或其他类型
        return ("", default_selector_type)


# ============ 用户数据操作 ============

def load_user_data() -> Dict[str, Any]:
    """加载用户数据"""
    data = _load_json(USER_DATA_PATH, DEFAULT_USER_DATA, "用户数据文件")
    return _deep_merge(DEFAULT_USER_DATA, data)


def save_user_data(data: Dict[str, Any]) -> None:
    """保存用户数据"""
    _save_json(USER_DATA_PATH, data)


def update_user_data(patch: Dict[str, Any]) -> Dict[str, Any]:
    """更新用户数据"""
    current = load_user_data()
    merged = _deep_merge(current, patch)
    print(f"[配置] 更新用户数据项: {list(patch.keys())}")
    save_user_data(merged)
    return merged


# ============ 应用配置操作 ============

def load_app_config() -> Dict[str, Any]:
    """加载应用配置"""
    data = _load_json(APP_CONFIG_PATH, DEFAULT_APP_CONFIG, "应用配置文件")
    return _deep_merge(DEFAULT_APP_CONFIG, data)


def save_app_config(config: Dict[str, Any]) -> None:
    """保存应用配置"""
    _save_json(APP_CONFIG_PATH, config)


def update_app_config(patch: Dict[str, Any]) -> Dict[str, Any]:
    """更新应用配置"""
    current = load_app_config()
    merged = _deep_merge(current, patch)
    print(f"[配置] 更新应用配置项: {list(patch.keys())}")
    save_app_config(merged)
    return merged


def download_config(url: str, timeout: int = 10) -> Dict[str, Any] | None:
    """从URL下载配置文件"""
    try:
        print(f"[配置] 正在从 {url} 下载配置...")
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        config = response.json()
        print(f"[配置] 配置下载成功: {url}")
        return config
    except Exception as e:
        print(f"[配置] 配置下载失败: {e}")
        return None


def update_config_from_url(url: str) -> bool:
    """从URL下载并更新配置文件"""
    config = download_config(url)
    if config is None:
        return False
    
    try:
        # 验证配置结构
        if not isinstance(config, dict):
            print("[配置] 下载的配置格式错误：不是JSON对象")
            return False
        
        # 合并并保存
        current = load_app_config()
        merged = _deep_merge(current, config)
        save_app_config(merged)
        print(f"[配置] 配置已从 {url} 更新成功")
        return True
    except Exception as e:
        print(f"[配置] 更新配置失败: {e}")
        return False


# ============ 兼容性函数（向后兼容）============

def load_settings() -> Dict[str, Any]:
    """加载所有设置（兼容旧接口）"""
    user_data = load_user_data()
    app_config = load_app_config()
    # 合并返回
    result = {**user_data, **app_config}
    return result


def update_settings(patch: Dict[str, Any]) -> Dict[str, Any]:
    """更新设置（兼容旧接口，自动判断类型）"""
    user_data_keys = set(DEFAULT_USER_DATA.keys())
    patch_user_data = {k: v for k, v in patch.items() if k in user_data_keys}
    patch_app_config = {k: v for k, v in patch.items() if k not in user_data_keys}
    
    result_user = load_user_data()
    result_config = load_app_config()
    
    if patch_user_data:
        result_user = update_user_data(patch_user_data)
    if patch_app_config:
        result_config = update_app_config(patch_app_config)
    
    return {**result_user, **result_config}
