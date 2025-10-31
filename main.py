import threading
import time
import tkinter as tk
from tkinter import ttk
from typing import Any
from util.config_store import (
    load_user_data, load_app_config, update_user_data,
    update_config_from_url, load_settings, parse_selector_config
)


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("公务员网站自动登录助手")

        # 分别加载用户数据和配置
        self.user_data = load_user_data()
        self.app_config = load_app_config()
        self.settings = {**self.user_data, **self.app_config}  # 合并供兼容使用
        
        # 窗口置顶（从配置读取）
        topmost = self.user_data.get("topmost", True)
        self.root.attributes('-topmost', topmost)
        
        # 定死窗口大小
        window_width = 700
        window_height = 580
        self.root.resizable(False, False)
        # 计算窗口居中位置
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.driver = None
        self.ocr = None
        self.looping = False
        self.loop_stop = threading.Event()
        self.current_mode = self.user_data.get("mode", "bm")  # bm | kw

        # UI
        frm = ttk.Frame(root, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frm, text="账号").grid(row=0, column=0, sticky="w")
        self.var_account = tk.StringVar(value=self.user_data.get("account", ""))
        ent_account = ttk.Entry(frm, textvariable=self.var_account, width=32)
        ent_account.grid(row=0, column=1, sticky="we", padx=6, pady=4)

        ttk.Label(frm, text="密码").grid(row=1, column=0, sticky="w")
        self.var_password = tk.StringVar(value=self.user_data.get("password", ""))
        ent_password = ttk.Entry(frm, textvariable=self.var_password, show='*', width=32)
        ent_password.grid(row=1, column=1, sticky="we", padx=6, pady=4)

        # 序列号（考务使用）- 上移到账号密码一起
        ttk.Label(frm, text="序列号").grid(row=2, column=0, sticky="w")
        self.var_serial = tk.StringVar(value=self.user_data.get("kw_serial", ""))
        ent_serial = ttk.Entry(frm, textvariable=self.var_serial, width=32)
        ent_serial.grid(row=2, column=1, sticky="we", padx=6, pady=4)

        # 复选框（三个复选框放在一行）
        checkbox_frame = ttk.Frame(frm)
        checkbox_frame.grid(row=3, column=0, columnspan=2, sticky="w", pady=4)
        self.var_auto_ocr = tk.BooleanVar(value=self.user_data.get("auto_ocr", True))
        self.var_headless = tk.BooleanVar(value=self.user_data.get("headless", False))
        self.var_topmost = tk.BooleanVar(value=self.user_data.get("topmost", True))
        self.var_mode = tk.StringVar(value=self.current_mode)
        chk_ocr = ttk.Checkbutton(checkbox_frame, text="自动识别验证码", variable=self.var_auto_ocr)
        chk_headless = ttk.Checkbutton(checkbox_frame, text="后台登录(无头)", variable=self.var_headless)
        chk_topmost = ttk.Checkbutton(checkbox_frame, text="窗口置顶", variable=self.var_topmost, command=self.toggle_topmost)
        chk_ocr.grid(row=0, column=0, sticky="w", padx=(0, 15))
        chk_headless.grid(row=0, column=1, sticky="w", padx=(0, 15))
        chk_topmost.grid(row=0, column=2, sticky="w")

        # 配置更新区域
        config_update_frame = ttk.LabelFrame(frm, text="配置更新", padding=5)
        config_update_frame.grid(row=4, column=0, columnspan=2, sticky="we", pady=6)
        
        ttk.Label(config_update_frame, text="配置源:").grid(row=0, column=0, sticky="w", padx=4)
        self.var_config_url = tk.StringVar()
        config_sources = self.app_config.get("config_sources", [])
        if not config_sources:
            config_sources = ["https://example.com/config1.json", "https://example.com/config2.json"]
        self.combo_config_url = ttk.Combobox(config_update_frame, textvariable=self.var_config_url, 
                                             values=config_sources, width=35, state="readonly")
        if config_sources:
            self.var_config_url.set(config_sources[0])
        self.combo_config_url.grid(row=0, column=1, sticky="we", padx=4)
        ttk.Button(config_update_frame, text="更新配置", command=self.update_config).grid(row=0, column=2, padx=4)
        config_update_frame.columnconfigure(1, weight=1)

        # 按钮栏（一排7个）
        btn_bar = ttk.Frame(frm)
        btn_bar.grid(row=5, column=0, columnspan=2, sticky="we", pady=6)
        ttk.Button(btn_bar, text="打开报名界面", command=lambda: self.open_page("bm")).grid(row=0, column=0, padx=2)
        ttk.Button(btn_bar, text="打开考务界面", command=lambda: self.open_page("kw")).grid(row=0, column=1, padx=2)
        ttk.Button(btn_bar, text="刷新界面", command=self.refresh_page).grid(row=0, column=2, padx=2)
        ttk.Button(btn_bar, text="登录", command=self.login_once).grid(row=0, column=3, padx=2)
        ttk.Button(btn_bar, text="循环测试登录", command=self.loop_login).grid(row=0, column=4, padx=2)
        ttk.Button(btn_bar, text="停止循环", command=self.stop_loop).grid(row=0, column=5, padx=2)
        ttk.Button(btn_bar, text="测试验证码", command=self.test_captcha).grid(row=0, column=6, padx=2)

        # 日志区域
        self.txt = tk.Text(frm, height=12, wrap=tk.WORD)
        self.txt.grid(row=6, column=0, columnspan=2, sticky="nsew")

        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(6, weight=1)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        self.log("准备就绪。请在配置文件中设置登录URL与选择器。")

    def toggle_topmost(self):
        """切换窗口置顶状态"""
        topmost = self.var_topmost.get()
        self.root.attributes('-topmost', topmost)
        # 立即保存设置
        to_save = {
            "topmost": topmost
        }
        update_user_data(to_save)
    
    def save_current_settings(self):
        to_save = {
            "account": self.var_account.get().strip(),
            "password": self.var_password.get(),
            "auto_ocr": bool(self.var_auto_ocr.get()),
            "headless": bool(self.var_headless.get()),
            "topmost": bool(self.var_topmost.get()),
            "mode": self.current_mode,
            "kw_serial": self.var_serial.get().strip(),
        }
        self.user_data = update_user_data(to_save)
        # 更新合并的settings
        self.settings = {**self.user_data, **self.app_config}
        
    def reload_config(self):
        """重新加载配置（更新配置后调用）"""
        from util.config_store import load_app_config
        self.app_config = load_app_config()
        self.settings = {**self.user_data, **self.app_config}
        
    def update_config(self):
        """从URL更新配置"""
        url = self.var_config_url.get().strip()
        if not url:
            self.log("请选择配置源地址")
            return
        
        self.log(f"开始从 {url} 更新配置...")
        
        def worker():
            try:
                success = update_config_from_url(url)
                if success:
                    self.reload_config()
                    self.log("配置更新成功！请重启程序或重新打开页面以应用新配置。")
                else:
                    self.log("配置更新失败，请检查网络连接和URL是否正确")
            except Exception as e:
                self.log(f"配置更新出错: {e}")
        
        threading.Thread(target=worker, daemon=True).start()

    def ensure_driver(self):
        if self.driver is None:
            # 懶加載，減少GUI啟動時間
            from util.drission_helper import DrissionDriver
            self.driver = DrissionDriver(headless=bool(self.var_headless.get()))
        return self.driver

    def ensure_ocr(self):
        if self.ocr is None:
            # 懶加載OCR，避免導入大模型拖慢啟動
            from util.ocr_helper import CaptchaOcr
            self.ocr = CaptchaOcr()
        return self.ocr

    def log(self, msg: str):
        """线程安全的日志输出"""
        timestamp = time.strftime('%H:%M:%S')
        log_msg = f"{timestamp} - {msg}\n"
        # 使用 after 确保在主线程中更新 GUI
        self.root.after(0, lambda: self._log_impl(log_msg))
    
    def _log_impl(self, log_msg: str):
        """实际的日志输出实现（在主线程中执行）"""
        self.txt.insert('end', log_msg)
        self.txt.see('end')

    def open_page(self, mode: str):
        """打开页面（后台线程执行）"""
        # 設置當前模式
        self.current_mode = mode
        self.var_mode.set(mode)
        self.save_current_settings()
        login_cfg = self.settings.get("login", {}).get(mode, {})
        url = login_cfg.get("url")
        if not url:
            self.log(f"请在 config/app_config.json 填写 login.{mode}.url")
            return
        
        def worker():
            try:
                self.log(f"正在打开{ '报名' if mode=='bm' else '考务' }登录页...")
                drv = self.ensure_driver()
                drv.goto(url)
                self.log(f"已打开{ '报名' if mode=='bm' else '考务' }登录页: {url}")
            except Exception as e:
                self.log(f"打开页面失败: {e}")
        
        threading.Thread(target=worker, daemon=True).start()

    def refresh_page(self):
        """刷新页面（后台线程执行）"""
        if not self.driver:
            self.log("浏览器未启动。")
            return
        
        def worker():
            try:
                self.log("正在刷新页面...")
                self.driver.page.refresh()
                self.log("页面已刷新。")
            except Exception as e:
                self.log(f"刷新失败: {e}")
        
        threading.Thread(target=worker, daemon=True).start()

    def _fill_login_form(self, mode: str) -> bool:
        s = self.settings
        login_all = s.get("login", {})
        login = login_all.get(mode, {})
        default_selector_type = login.get("selector_type", "xpath")

        # 等待页面加载完成
        import time
        time.sleep(1)

        # 输入账号 - 使用灵活的选择器配置
        username_config = login.get("username", "")
        account_value = self.var_account.get().strip()
        if username_config:
            username_sel, username_type = parse_selector_config(username_config, default_selector_type)
            if username_sel:
                ok_u = self.driver.input(username_sel, account_value, username_type)
                if not ok_u:
                    self.log(f"账号输入框定位失败。选择器: {username_sel} ({username_type})")
                    return False
                self.log(f"已输入账号: {account_value}")
            else:
                self.log("账号选择器未配置")
                return False
        else:
            self.log("账号选择器未配置")
            return False

        # 输入密码 - 使用灵活的选择器配置
        ok_p = True
        password_config = login.get("password", "")
        if password_config:
            password_sel, password_type = parse_selector_config(password_config, default_selector_type)
            if password_sel:
                ok_p = self.driver.input(password_sel, self.var_password.get(), password_type)
                if not ok_p:
                    self.log(f"密码输入框定位失败。选择器: {password_sel} ({password_type})")
                    return False
                self.log("已输入密码")

        # 输入序列号（考务模式）- 当开启自动识别验证码时才输入
        ok_sn = True
        if mode == 'kw' and self.var_auto_ocr.get():
            serial_config = login.get("serial", "")
            if serial_config:
                serial_sel, serial_type = parse_selector_config(serial_config, default_selector_type)
                if serial_sel:
                    ok_sn = self.driver.input(serial_sel, self.var_serial.get().strip(), serial_type)
                    if not ok_sn:
                        self.log(f"序列号输入框定位失败。选择器: {serial_sel} ({serial_type})")
                        return False
                    self.log("已输入序列号")

        # 处理验证码 - 使用灵活的选择器配置
        if self.var_auto_ocr.get():
            captcha_img_config = login.get("captcha_image", "")
            captcha_input_config = login.get("captcha_input", "")
            if captcha_img_config and captcha_input_config:
                code = self._get_captcha_code(captcha_img_config, default_selector_type)
                if code:
                    captcha_input_sel, captcha_input_type = parse_selector_config(captcha_input_config, default_selector_type)
                    if captcha_input_sel:
                        if self.driver.input(captcha_input_sel, code, captcha_input_type):
                            self.log(f"验证码识别并输入: {code}")
                        else:
                            self.log(f"验证码输入框定位失败: {captcha_input_sel} ({captcha_input_type})")
                else:
                    self.log("验证码识别失败。")
        
        return True

    def _get_captcha_code(self, img_config: Any, default_selector_type: str) -> str | None:
        """
        获取验证码识别结果
        使用 ddddocr，限制字符范围为数字+字母组合（char_ranges=6）
        """
        ocr = self.ensure_ocr()
        if not ocr:
            return None
        
        # 解析选择器配置
        img_selector, selector_type = parse_selector_config(img_config, default_selector_type)
        if not img_selector:
            return None
            
        # 优先从图片 src 属性获取
        src = self.driver.get_attr(img_selector, 'src', selector_type)
        if src:
            # char_ranges=6 表示：小写英文a-z + 大写英文A-Z + 数字0-9
            code = ocr.recognize(src, char_ranges=6)
            if code:
                return code
        
        # 退化为截图方式获取
        data = self.driver.capture_element_png(img_selector, selector_type)
        if data:
            # 使用相同的字符范围限制
            code = ocr.recognize(data, char_ranges=6)
            if code:
                return code
        
        return None

    def _submit(self, mode: str) -> bool:
        login_all = self.settings.get("login", {})
        login = login_all.get(mode, {})
        default_selector_type = login.get("selector_type", "xpath")
        
        # 使用灵活的选择器配置
        submit_config = login.get("submit", "")
        if submit_config:
            submit_sel, submit_type = parse_selector_config(submit_config, default_selector_type)
            if submit_sel:
                ok = self.driver.click(submit_sel, submit_type)
                if not ok:
                    self.log(f"提交按钮定位失败。选择器: {submit_sel} ({submit_type})")
                return ok
        self.log("提交按钮选择器未配置")
        return False

    def _single_login_attempt(self, mode: str):
        try:
            if not self.driver:
                self.open_page(mode)
            if not self.driver:
                return
            if not self._fill_login_form(mode):
                return
            # 当未开启自动识别验证码时，仅输入账号密码（和可选序列号）但不提交
            if not self.var_auto_ocr.get():
                self.log("未开启自动识别验证码：已输入账号/密码（不提交登录）。")
                return
            if not self._submit(mode):
                return
            self.log("已尝试提交登录。")
        except Exception as e:
            self.log(f"登录流程失败: {e}")

    def login_once(self):
        """单次登录（后台线程执行）"""
        self.save_current_settings()
        mode = self.current_mode
        
        def worker():
            try:
                self._single_login_attempt(mode)
            except Exception as e:
                self.log(f"登录过程出错: {e}")
        
        threading.Thread(target=worker, daemon=True).start()

    def loop_login(self):
        self.save_current_settings()

        if self.looping:
            self.log("循环已在执行中。")
            return

        self.looping = True
        self.loop_stop.clear()
        attempts = int(self.settings.get("loop_attempts", 3))

        def worker():
            try:
                for i in range(attempts):
                    if self.loop_stop.is_set():
                        self.log("收到停止指令，终止循环。")
                        break
                    self.log(f"开始第 {i+1}/{attempts} 次登录尝试")
                    self._single_login_attempt(self.current_mode)
                    # 可中斷的睡眠
                    for _ in range(20):
                        if self.loop_stop.is_set():
                            break
                        time.sleep(0.1)
            finally:
                self.looping = False
                self.log("循环完成。")

        threading.Thread(target=worker, daemon=True).start()

    def stop_loop(self):
        if not self.looping:
            self.log("循环未在执行。")
            return
        self.loop_stop.set()
        self.log("已发送停止指令。")
    
    def test_captcha(self):
        """测试验证码识别功能（后台线程执行）"""
        mode = self.current_mode
        login_all = self.settings.get("login", {})
        login = login_all.get(mode, {})
        default_selector_type = login.get("selector_type", "xpath")
        captcha_img_config = login.get("captcha_image", "")
        
        if not captcha_img_config:
            self.log(f"[测试验证码] 当前模式({mode})未配置验证码图片选择器")
            return
        
        def worker():
            try:
                # 解析选择器配置
                captcha_img_sel, selector_type = parse_selector_config(captcha_img_config, default_selector_type)
                if not captcha_img_sel:
                    self.log(f"[测试验证码] 验证码图片选择器配置无效")
                    return
                
                # 如果浏览器未启动，先启动
                if not self.driver:
                    self.log("[测试验证码] 浏览器未启动，正在打开页面...")
                    # 在主线程中打开页面（这会启动浏览器）
                    self.root.after(0, lambda: self.open_page(mode))
                    time.sleep(3)  # 等待页面加载
                
                if not self.driver:
                    self.log("[测试验证码] 浏览器启动失败")
                    return
                
                self.log(f"[测试验证码] 开始测试验证码识别...")
                self.log(f"[测试验证码] 模式: {mode} ({'报名' if mode=='bm' else '考务'})")
                self.log(f"[测试验证码] 选择器: {captcha_img_sel}")
                self.log(f"[测试验证码] 选择器类型: {selector_type}")
                
                # 尝试获取图片地址
                img_url = None
                img_data = None
                
                try:
                    # 优先从 src 属性获取
                    img_src = self.driver.get_attr(captcha_img_sel, 'src', selector_type)
                    if img_src:
                        self.log(f"[测试验证码] 图片地址 (src): {img_src}")
                        img_url = img_src
                except Exception as e:
                    self.log(f"[测试验证码] 获取图片src失败: {e}")
                
                # 尝试截图
                try:
                    img_data = self.driver.capture_element_png(captcha_img_sel, selector_type)
                    if img_data:
                        img_size = len(img_data)
                        self.log(f"[测试验证码] 截图成功，图片大小: {img_size} 字节")
                except Exception as e:
                    self.log(f"[测试验证码] 截图失败: {e}")
                
                if not img_url and not img_data:
                    self.log("[测试验证码] ❌ 无法获取验证码图片（既无法获取src也无法截图）")
                    return
                
                # 进行OCR识别
                self.log("[测试验证码] 开始OCR识别...")
                ocr = self.ensure_ocr()
                if not ocr:
                    self.log("[测试验证码] ❌ OCR未初始化")
                    return
                
                try:
                    # 优先使用URL识别
                    result = None
                    if img_url:
                        self.log(f"[测试验证码] 使用图片URL进行识别...")
                        result = ocr.recognize(img_url, char_ranges=6)
                    
                    # 如果URL识别失败，使用截图
                    if not result and img_data:
                        self.log(f"[测试验证码] 使用截图进行识别...")
                        result = ocr.recognize(img_data, char_ranges=6)
                    
                    if result:
                        self.log(f"[测试验证码] ✅ 识别成功: {result}")
                    else:
                        self.log(f"[测试验证码] ❌ 识别失败: 未能识别出验证码")
                except Exception as e:
                    self.log(f"[测试验证码] ❌ 识别过程出错: {e}")
            except Exception as e:
                self.log(f"[测试验证码] ❌ 测试过程出错: {e}")
        
        threading.Thread(target=worker, daemon=True).start()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()


