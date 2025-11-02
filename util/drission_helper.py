from typing import Optional, Tuple

from DrissionPage._configs.chromium_options import ChromiumOptions
from DrissionPage._base.chromium import Chromium
from selenium.webdriver.common.by import By


class DrissionDriver:
    def __init__(self, headless: bool = False, browser: str = "chrome"):
        """
        初始化浏览器驱动
        
        Args:
            headless: 是否无头模式
            browser: 浏览器类型，支持 "chrome", "edge", "firefox"
        """
        # 设置启动端口，静音
        co = ChromiumOptions().set_address("127.0.0.1:9222").mute(True)
        if headless:
            co.headless()
        
        # 根据浏览器类型设置浏览器路径
        import os
        
        if browser == "edge":
            # Edge浏览器的常见路径
            edge_paths = [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\Application\msedge.exe"),
            ]
            driver_path = ""
            for path in edge_paths:
                if os.path.exists(path):
                    driver_path = path
                    break
            if driver_path:
                co.set_browser_path(driver_path)
        elif browser == "firefox":
            # Firefox浏览器的常见路径
            firefox_paths = [
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
                os.path.expanduser(r"~\AppData\Local\Mozilla Firefox\firefox.exe"),
            ]
            driver_path = ""
            for path in firefox_paths:
                if os.path.exists(path):
                    driver_path = path
                    break
            if driver_path:
                co.set_browser_path(driver_path)
            # Firefox可能需要使用Firefox驱动，但DrissionPage主要支持Chromium
            # 如果找不到Firefox，会回退到默认浏览器
        # chrome是默认值，不需要特别设置
        
        # 重新创建 Chromium 实例
        self._chromium = Chromium(addr_or_opts=co)
        # 挂载dom后加载
        self._chromium.set.load_mode.normal()
        self.page = self._chromium.latest_tab

    def goto(self, url: str) -> None:
        self.page.get(url)

    def find(self, selector: str, selector_type: str = 'xpath', timeout: float = 5):
        """查找元素，支持 css、xpath、class_name、id 等选择器类型"""
        if selector_type == 'css':
            return self.page.ele((By.CSS_SELECTOR, selector), timeout=timeout)
        elif selector_type == 'class_name' or selector_type == 'class':
            return self.page.ele((By.CLASS_NAME, selector), timeout=timeout)
        elif selector_type == 'id':
            return self.page.ele((By.ID, selector), timeout=timeout)
        elif selector_type == 'name':
            return self.page.ele((By.NAME, selector), timeout=timeout)
        elif selector_type == 'tag':
            return self.page.ele((By.TAG_NAME, selector), timeout=timeout)
        else:
            # 默认使用 xpath
            return self.page.ele((By.XPATH, selector), timeout=timeout)

    def text(self, selector: str, selector_type: str = 'xpath', timeout: float = 5) -> Optional[str]:
        ele = self.find(selector, selector_type, timeout)
        if not ele:
            return None
        value = (ele.text or '').strip()
        return value

    def input(self, selector: str, value: str, selector_type: str = 'xpath', clear: bool = True, timeout: float = 5) -> bool:
        """输入文本到元素"""
        ele = self.find(selector, selector_type, timeout)
        if not ele:
            return False
        try:
            if clear:
                try:
                    ele.clear()
                except Exception:
                    pass
            ele.input(value)
            return True
        except Exception as e:
            print(f"[DrissionDriver] 输入失败 {selector} ({selector_type}): {e}")
            return False

    def click(self, selector: str, selector_type: str = 'xpath', timeout: float = 5) -> bool:
        ele = self.find(selector, selector_type, timeout)
        if not ele:
            return False
        self.page.actions.click(ele)
        return True

    def double_click(self, x: int = None, y: int = None) -> bool:
        """
        双击鼠标左键
        
        Args:
            x: X坐标（可选，默认在页面任意位置）
            y: Y坐标（可选，默认在页面任意位置）
        """
        try:
            if x is not None and y is not None:
                # 在指定坐标双击
                self.page.actions.move_to(x, y).click().click()
            else:
                # 在页面任意位置双击（使用body元素或页面中心）
                try:
                    # 尝试在body元素上双击
                    body = self.page.ele('tag:body', timeout=0.5)
                    if body:
                        # 在body上双击两次
                        self.page.actions.double_click(body)
                    else:
                        # 备用方案：在页面中心双击
                        self.page.actions.click().click()
                except:
                    # 最终备用方案：直接执行双击动作
                    try:
                        self.page.actions.click().click()
                    except:
                        pass
            return True
        except Exception as e:
            # 静默处理错误，不影响流程
            return False

    def get_attr(self, selector: str, attr: str, selector_type: str = 'xpath', timeout: float = 5) -> Optional[str]:
        ele = self.find(selector, selector_type, timeout)
        if not ele:
            return None
        return ele.attr(attr)

    def get_src(self, selector: str, selector_type: str = 'xpath', timeout: float = 5, base64_to_bytes: bool = True) -> Optional[str | bytes]:
        """
        获取元素的src属性资源
        base64格式可转为bytes返回，其它的以str返回
        
        Args:
            selector: 元素选择器
            selector_type: 选择器类型
            timeout: 超时时间
            base64_to_bytes: 为True时，如果是base64数据，转换为bytes格式
        
        Returns:
            bytes: base64数据转换为的bytes（当base64_to_bytes=True）
            str: URL字符串或其他字符串
            None: 无资源时返回None
        """
        ele = self.find(selector, selector_type, timeout)
        if not ele:
            return None
        try:
            return ele.src(timeout=timeout, base64_to_bytes=base64_to_bytes)
        except Exception as e:
            print(f"[DrissionDriver] 获取src失败 {selector} ({selector_type}): {e}")
            return None

    def capture_element_png(self, selector: str, selector_type: str = 'xpath', timeout: float = 5) -> Optional[bytes]:
        ele = self.find(selector, selector_type, timeout)
        if not ele:
            return None
        try:
            return ele.screenshot(as_bytes=True)
        except Exception:
            return None

    def press_key(self, key: str) -> bool:
        """模拟按键操作
        
        Args:
            key: 按键名称，如 'Escape', 'Enter', 'Tab' 等
        """
        try:
            from selenium.webdriver.common.keys import Keys
            # 将字符串转换为Keys常量
            key_map = {
                'Escape': Keys.ESCAPE,
                'ESC': Keys.ESCAPE,
                'Enter': Keys.ENTER,
                'Tab': Keys.TAB,
                'Space': Keys.SPACE,
                'Backspace': Keys.BACKSPACE,
                'Delete': Keys.DELETE,
                'F1': Keys.F1,
                'F2': Keys.F2,
                'F3': Keys.F3,
                'F4': Keys.F4,
                'F5': Keys.F5,
                'F6': Keys.F6,
                'F7': Keys.F7,
                'F8': Keys.F8,
                'F9': Keys.F9,
                'F10': Keys.F10,
                'F11': Keys.F11,
                'F12': Keys.F12,
            }
            
            key_value = key_map.get(key, None)
            if key_value is None:
                # 如果不是特殊键，直接使用原字符串
                key_value = key
            
            # 使用页面对象发送按键
            self.page.key.press(key_value)
            return True
        except Exception as e:
            print(f"[DrissionDriver] 按键失败 {key}: {e}")
            return False

    def close(self) -> None:
        try:
            self.page.close()
        except Exception:
            pass


