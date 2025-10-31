from typing import Optional, Tuple

from DrissionPage._configs.chromium_options import ChromiumOptions
from DrissionPage._base.chromium import Chromium
from selenium.webdriver.common.by import By


class DrissionDriver:
    def __init__(self, headless: bool = False):
        co = ChromiumOptions().mute(True)
        if headless:
            co.headless()
        self._chromium = Chromium(addr_or_opts=co)
        self.page = self._chromium.latest_tab
        self.page.set.load_mode.normal()

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

    def get_attr(self, selector: str, attr: str, selector_type: str = 'xpath', timeout: float = 5) -> Optional[str]:
        ele = self.find(selector, selector_type, timeout)
        if not ele:
            return None
        return ele.attr(attr)

    def capture_element_png(self, selector: str, selector_type: str = 'xpath', timeout: float = 5) -> Optional[bytes]:
        ele = self.find(selector, selector_type, timeout)
        if not ele:
            return None
        try:
            return ele.screenshot(as_bytes=True)
        except Exception:
            return None

    def close(self) -> None:
        try:
            self.page.close()
        except Exception:
            pass


