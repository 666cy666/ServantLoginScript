import re
import base64
from typing import Optional

import requests
import ddddocr


class CaptchaOcr:
    """
    使用 ddddocr 进行验证码识别
    支持数字和字母组合的验证码
    """
    def __init__(self):
        """
        初始化 ddddocr 实例
        注意：只需初始化一次，不要重复初始化以提升性能
        """
        try:
            # 初始化 ddddocr，默认使用第一套 OCR 模型
            self._ocr = ddddocr.DdddOcr()
            print("[OCR] ddddocr 初始化成功")
        except Exception as e:
            print(f"[OCR] ddddocr 初始化失败: {e}")
            self._ocr = None

    def _get_image_bytes(self, input_data: bytes | str) -> Optional[bytes]:
        """
        将输入转换为图片字节数据
        支持：bytes、URL、base64、本地文件路径
        注意：对于需要浏览器会话的验证码图片URL，直接访问可能会失败（405错误）
        """
        try:
            if isinstance(input_data, bytes):
                return input_data
            elif isinstance(input_data, str):
                # URL
                if re.match(r'^https?://', input_data):
                    # 尝试添加基本的请求头，模拟浏览器访问
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                        'Accept-Language': 'zh-CN,zh;q=0.9',
                        'Referer': input_data.rsplit('/', 2)[0] if '/' in input_data else input_data
                    }
                    try:
                        resp = requests.get(input_data, headers=headers, timeout=10)
                        resp.raise_for_status()
                        return resp.content
                    except requests.exceptions.HTTPError as e:
                        # 如果是405或其他HTTP错误，说明需要浏览器会话，返回None让调用者使用截图方式
                        if e.response.status_code in (405, 403, 401):
                            print(f"[OCR] 图片URL需要浏览器会话，建议使用截图方式: {input_data[:50]}...")
                        raise
                # base64 格式 (data:image/...)
                elif input_data.startswith('data:image'):
                    header, encoded = input_data.split(',', 1)
                    return base64.b64decode(encoded)
                # 本地文件路径
                else:
                    with open(input_data, 'rb') as f:
                        return f.read()
            return None
        except Exception as e:
            print(f"[OCR] 图片数据获取失败: {e}")
            return None

    def recognize(self, input_data: bytes | str, 
                  char_ranges: Optional[int] = None,
                  use_beta: bool = False) -> Optional[str]:
        """
        识别验证码
        
        Args:
            input_data: 图片数据（bytes、URL、base64、文件路径）
            char_ranges: 字符范围限制（0-7，见下方说明）
                        0: 纯数字 0-9
                        4: 小写英文a-z + 数字0-9
                        5: 大写英文A-Z + 数字0-9
                        6: 小写英文a-z + 大写英文A-Z + 数字0-9 (推荐用于数字+字母组合)
                        7: 默认字符库 - 小写英文a-z - 大写英文A-Z - 数字0-9
                        None: 不限制（使用默认字符集）
            use_beta: 是否使用第二套OCR模型（beta版本）
        
        Returns:
            识别出的验证码文本，失败返回 None
        """
        if self._ocr is None:
            print("[OCR] OCR未初始化")
            return None
        
        try:
            # 获取图片字节数据
            image_bytes = self._get_image_bytes(input_data)
            if image_bytes is None:
                return None
            
            # 如果需要切换模型，需要重新初始化（不推荐频繁切换）
            ocr_instance = self._ocr
            if use_beta:
                # 仅在需要时创建 beta 实例
                if not hasattr(self, '_ocr_beta') or self._ocr_beta is None:
                    self._ocr_beta = ddddocr.DdddOcr(beta=True)
                ocr_instance = self._ocr_beta
            
            # 如果指定了字符范围，设置字符集限制
            # 对于数字+字母组合的验证码，推荐使用 char_ranges=0
            temp_ocr = ocr_instance
            if char_ranges is not None:
                # 创建一个临时实例来设置字符范围，避免影响全局实例
                temp_ocr = ddddocr.DdddOcr(beta=use_beta)
                temp_ocr.set_ranges(char_ranges)
            
            # 执行OCR识别
            result = temp_ocr.classification(image_bytes)
            
            text = result.strip() if result else None
            if text:
                print(f"[OCR] 识别结果: {text}")
            else:
                print("[OCR] 识别结果为空")
            return text
            
        except Exception as e:
            print(f"[OCR] 验证码识别失败: {e}")
            return None
