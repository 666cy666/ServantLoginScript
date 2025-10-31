# 公务员网站自动登录助手
(国考抢考场的小工具，就是给不会下油猴的哥们用的，大佬勿喷)
本项目是基于 Tkinter 图形界面、DrissionPage 浏览器自动化与 ddddocr 验证码识别的登录辅助工具。支持“报名( bm ) / 考务( kw )”两种模式、循环登录、停止循环、一键刷新、远程配置更新、灵活的元素选择器、验证码测试等功能。

## 功能
- 报名/考务模式切换（不同页面布局，登录逻辑自适应）
- 账号、密码、序列号（考务）填写
- 自动识别验证码（ddddocr，支持混合数字+字母）
- 循环登录与中断按钮
- 一键打开页面 / 刷新页面 / 单次登录
- 测试验证码识别（打印图片地址/截图大小与 OCR 结果）
- 配置拆分：用户数据 `user_data.json` 与应用配置 `app_config.json`
- 远程配置更新（下拉选择 URL + 按钮）
- 灵活选择器：每个元素可单独配置 `selector` 与 `selector_type`
- 懒加载浏览器与 OCR，提升 GUI 启动速度
- 浏览器操作后台线程执行，避免 GUI 卡顿
- 可选“窗口置顶”

## 目录结构
```
ServantLoginScript/
├─ main.py                    # 程序入口，Tkinter GUI 与业务逻辑
├─ util/
│  ├─ config_store.py         # 配置与用户数据的读取/保存/远程更新、选择器解析
│  ├─ drission_helper.py      # DrissionPage 封装（输入、点击、截图、属性获取）
│  └─ ocr_helper.py           # ddddocr 封装
├─ config/
│  ├─ app_config.json         # 应用配置（URL、选择器、循环次数、远程源）
│  └─ user_data.json          # 用户数据（账号、密码、置顶、无头、默认模式、序列号）
├─ README.md                  # 文档（本文件）
├─ requirements.txt           # 依赖清单
```

## 安装与运行
1. 安装 Python 3.10+ (Windows 推荐) 与 pip。
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 配置 `config/app_config.json` 中的登录 URL 与选择器（详见下文“配置说明”）。
4. 运行：
   ```bash
   python main.py
   ```

> 首次运行会自动生成 `config/user_data.json` 与 `config/app_config.json`（如不存在），并打印路径日志。

## 配置说明
- 用户数据：`config/user_data.json`
  - `account`, `password`: 账号/密码
  - `auto_ocr`: 是否自动识别验证码
  - `headless`: 是否无头模式运行浏览器
  - `topmost`: 窗口是否置顶
  - `mode`: 默认模式（`bm` 或 `kw`）
  - `kw_serial`: 考务登录时的序列号

- 应用配置：`config/app_config.json`
  - `login.bm` 与 `login.kw`：分别对应报名/考务页面
  - `selector_type`: 默认选择器类型（当某个元素仅写字符串选择器时使用）
  - 每个元素支持两种写法：
    1) 字符串（使用默认 `selector_type`）
    2) 对象：`{"selector": "...", "selector_type": "css|xpath|id|class_name|name|tag"}`
  - `loop_attempts`: 循环尝试次数
  - `config_sources`: 远程配置地址列表（GUI 下拉可选）

示例（节选）：
```json
{
  "login": {
    "bm": {
      "url": "http://bm.scs.gov.cn/pp/gkweb/core/web/ui/business/auth/login.html",
      "selector_type": "class_name",
      "username": { "selector": "input240", "selector_type": "class_name" },
      "password": { "selector": "input240 password", "selector_type": "class_name" },
      "captcha_image": { "selector": "captchaImg", "selector_type": "id" },
      "captcha_input": { "selector": "captchaWord", "selector_type": "id" },
      "submit": { "selector": "register_btn", "selector_type": "class_name" }
    },
    "kw": {
      "url": "",
      "selector_type": "css",
      "username": { "selector": "", "selector_type": "css" },
      "password": { "selector": "", "selector_type": "css" },
      "serial":   { "selector": "", "selector_type": "css" },
      "captcha_image": { "selector": "", "selector_type": "id" },
      "captcha_input": { "selector": "", "selector_type": "id" },
      "submit": { "selector": "", "selector_type": "css" }
    }
  },
  "loop_attempts": 3,
  "config_sources": [
    "http://napcat.666cy666.top/config.json",
    "https://example.com/config2.json"
  ]
}
```

## 使用说明
- 顶部依次输入：账号、密码、序列号（考务使用）
- 勾选：自动识别验证码 / 后台登录(无头) / 窗口置顶
- 配置更新：选择一个远程源后点击“更新配置”即可拉取并合并到本地 `app_config.json`
- 按钮栏（从左到右，一排 7 个）：
  1) 打开报名界面
  2) 打开考务界面
  3) 刷新界面
  4) 登录（按当前模式）
  5) 循环测试登录
  6) 停止循环
  7) 测试验证码（打印图片地址/截图大小与 OCR 结果）

> 所有浏览器操作均在后台线程执行，防止 GUI 卡顿。日志区域实时显示操作状态。

## 选择器类型支持
- `css`, `xpath`, `class_name`, `id`, `name`, `tag`

## 常见问题（FAQ）
- 启动慢？
  - 浏览器与 OCR 均已懒加载，仅在需要时初始化。
- GUI 卡顿？
  - 浏览器操作全部放在后台线程；日志更新通过 `after()` 保障线程安全。
- 验证码识别错误？
  - 使用“测试验证码”按钮查看图片地址/截图与识别结果，并适当调整页面选择器或多试几次。
- 配置未生效？
  - 查看控制台/日志输出中的路径提示，确认 `config` 文件位置与内容是否正确。

## 依赖
- Python 3.10+
- DrissionPage
- ddddocr
- requests

## 许可证
仅供学习与交流，请勿用于任何违反网站条款的用途。
