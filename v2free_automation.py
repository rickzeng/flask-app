"""
V2free 浏览器自动化模块
使用 Playwright 自动登录 V2free 并记录访问日志
"""

import os
import logging
from datetime import datetime
from typing import Dict, Optional
import json
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext

from v2free_config import V2freeConfig


class V2freeAutomation:
    """V2free 自动化操作类"""
    
    def __init__(self):
        """初始化自动化实例"""
        self.config = V2freeConfig()
        self.logger = self._setup_logger()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._keep_browser_open = False  # 标记是否需要保持浏览器打开
        self._create_directories()
    
    def _create_directories(self):
        """创建必要的目录"""
        os.makedirs(self.config.LOG_DIR, exist_ok=True)
        os.makedirs(self.config.SCREENSHOT_DIR, exist_ok=True)
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('V2freeAutomation')
        logger.setLevel(logging.INFO)
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 文件处理器（带轮转）
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            self.config.LOG_FILE,
            maxBytes=self.config.MAX_LOG_SIZE,
            backupCount=self.config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _get_proxy_config(self) -> Dict:
        """获取代理配置"""
        if self.config.USE_PROXY:
            return {
                'server': self.config.PROXY_SERVER
            }
        return None
    
    def start_browser(self) -> bool:
        """启动浏览器"""
        try:
            self.logger.info("正在启动 Playwright 浏览器...")
            
            playwright = sync_playwright().start()
            
            # 启动 Chromium 浏览器
            self.browser = playwright.chromium.launch(
                headless=self.config.BROWSER_HEADLESS,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            # 创建浏览器上下文（包含代理设置）
            proxy_config = self._get_proxy_config()
            self.context = self.browser.new_context(
                proxy=proxy_config,
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # 创建页面
            self.page = self.context.new_page()
            
            self.logger.info("浏览器启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"浏览器启动失败: {str(e)}")
            return False
    
    def stop_browser(self, force: bool = False) -> bool:
        """停止浏览器
        
        Args:
            force: 强制关闭浏览器（忽略 _keep_browser_open 标志）
        
        Returns:
            是否成功关闭
        """
        # 如果不需要强制关闭且浏览器需要保持打开，则跳过
        if not force and self._keep_browser_open:
            self.logger.info("浏览器保持打开状态")
            return True
        
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            
            self._keep_browser_open = False
            self.logger.info("浏览器已关闭")
            return True
            
        except Exception as e:
            self.logger.error(f"浏览器关闭失败: {str(e)}")
            return False
    
    def prepare_login_form(self) -> Dict:
        """
        准备登录表单（填写用户名和密码，截取验证码）
        
        Returns:
            包含准备结果的字典
        """
        result = {
            'success': False,
            'message': '',
            'timestamp': datetime.now().isoformat(),
            'page_title': '',
            'page_url': '',
            'screenshot': None,
            'captcha_image': None,
            'need_captcha': False
        }
        
        try:
            if not self.browser or not self.page:
                if not self.start_browser():
                    result['message'] = '浏览器启动失败'
                    return result
            
            self.logger.info(f"开始访问 {self.config.V2FREE_URL}")
            
            # 访问登录页面
            self.page.goto(
                self.config.V2FREE_URL,
                timeout=self.config.BROWSER_TIMEOUT
            )
            
            # 等待页面加载
            self.page.wait_for_load_state('networkidle')
            
            # 记录页面信息
            result['page_title'] = self.page.title()
            result['page_url'] = self.page.url
            self.logger.info(f"页面标题: {result['page_title']}")
            self.logger.info(f"页面 URL: {result['page_url']}")
            
            # 查找并填写用户名
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[placeholder*="email" i]',
                'input[placeholder*="邮箱" i]',
                '#email',
                '.email'
            ]
            
            email_input = None
            for selector in email_selectors:
                try:
                    email_input = self.page.wait_for_selector(selector, timeout=5000)
                    if email_input:
                        self.logger.info(f"找到用户名输入框: {selector}")
                        break
                except:
                    continue
            
            if email_input:
                email_input.fill(self.config.V2FREE_USERNAME)
                self.logger.info(f"已填写用户名: {self.config.V2FREE_USERNAME}")
            else:
                self.logger.warning("未找到用户名输入框")
            
            # 查找并填写密码
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder*="password" i]',
                'input[placeholder*="密码" i]',
                '#password',
                '.password'
            ]
            
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = self.page.wait_for_selector(selector, timeout=5000)
                    if password_input:
                        self.logger.info(f"找到密码输入框: {selector}")
                        break
                except:
                    continue
            
            if password_input:
                password_input.fill(self.config.V2FREE_PASSWORD)
                self.logger.info("已填写密码")
            else:
                self.logger.warning("未找到密码输入框")
            
            # 检查是否有验证码
            captcha_selectors = [
                '#code',  # V2free 两步验证码字段
                'input[placeholder*="验证码" i]',
                'input[placeholder*="captcha" i]',
                'input[placeholder*="code" i]',
                '#captcha',
                '.captcha'
            ]
            
            has_captcha = False
            for selector in captcha_selectors:
                try:
                    captcha_input = self.page.wait_for_selector(selector, timeout=3000)
                    if captcha_input:
                        self.logger.info(f"发现验证码字段: {selector}")
                        has_captcha = True
                        break
                except:
                    pass
            
            if has_captcha:
                result['need_captcha'] = True
                
                # 尝试获取验证码（文本或图片）
                # 方法1: 查找文本验证码
                captcha_text_selectors = [
                    '.captcha-display',
                    '#captcha-display',
                    '.captcha-text',
                    '#captcha-text',
                    '.verify-code',
                    '#verify-code',
                    '[class*="captcha"]',
                    '[id*="captcha"]'
                ]
                
                captcha_text = None
                for selector in captcha_text_selectors:
                    try:
                        captcha_element = self.page.wait_for_selector(selector, timeout=2000)
                        if captcha_element:
                            text = captcha_element.inner_text().strip()
                            if text and len(text) > 2:  # 至少2个字符
                                captcha_text = text
                                self.logger.info(f"找到文本验证码: {text}")
                                result['captcha_text'] = captcha_text
                                break
                    except:
                        pass
                
                # 方法2: 查找验证码图片元素
                if not captcha_text:
                    captcha_img_selectors = [
                        'img[src*="captcha"]',
                        'img[alt*="验证码" i]',
                        'img[alt*="captcha" i]',
                        '.captcha img',
                        '#captcha img'
                    ]
                    
                    captcha_image = None
                    for selector in captcha_img_selectors:
                        try:
                            captcha_img = self.page.wait_for_selector(selector, timeout=3000)
                            if captcha_img:
                                self.logger.info(f"找到验证码图片: {selector}")
                                
                                # 获取图片的 bounding box
                                box = captcha_img.bounding_box()
                                if box:
                                    # 截取验证码图片区域
                                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                    filename = f"captcha_{timestamp}.png"
                                    filepath = os.path.join(self.config.SCREENSHOT_DIR, filename)
                                    
                                    self.page.screenshot(
                                        path=filepath,
                                        clip=box
                                    )
                                    result['captcha_image'] = filename
                                    captcha_image = filename
                                    self.logger.info(f"验证码图片已保存: {filepath}")
                                break
                        except:
                            pass
                
                # 如果没有找到验证码，截取整个表单区域
                if not captcha_text and not captcha_image:
                    self.logger.info("未找到验证码元素，截取整个页面")
                    screenshot_path = self._save_screenshot('captcha_form')
                    result['screenshot'] = screenshot_path
            else:
                self.logger.info("未发现验证码字段")
            
            # 截取完整页面（用于参考）
            if self.config.SAVE_SCREENSHOT:
                screenshot_path = self._save_screenshot('before_submit')
                if not result.get('screenshot'):
                    result['screenshot'] = screenshot_path
            
            result['success'] = True
            result['message'] = '表单准备完成，等待验证码输入'
            
            # 保持浏览器打开，等待后续操作
            self._keep_browser_open = True
            
            return result
            
        except Exception as e:
            result['message'] = f"准备登录表单失败: {str(e)}"
            self.logger.error(f"准备登录表单失败: {str(e)}")
            
            # 失败时截图
            if self.config.SCREENSHOT_ON_ERROR:
                screenshot_path = self._save_screenshot('error')
                result['screenshot'] = screenshot_path
            
            return result
    
    def submit_login_with_captcha(self, captcha_code: str) -> Dict:
        """
        使用验证码提交登录
        
        Args:
            captcha_code: 用户输入的验证码
        
        Returns:
            包含登录结果的字典
        """
        result = {
            'success': False,
            'message': '',
            'timestamp': datetime.now().isoformat(),
            'page_title': '',
            'page_url': '',
            'screenshot': None
        }
        
        try:
            # 检查浏览器是否还在运行
            if not self.browser or not self.page:
                result['message'] = '浏览器已关闭，请重新准备登录表单'
                return result
            
            self.logger.info(f"使用验证码提交登录: {captcha_code}")
            
            # 查找验证码输入框（使用 #code 选择器）
            captcha_selectors = [
                '#code',
                'input[placeholder*="验证码" i]',
                'input[placeholder*="captcha" i]',
                'input[placeholder*="code" i]',
                '#captcha',
                '.captcha'
            ]
            
            captcha_input = None
            for selector in captcha_selectors:
                try:
                    captcha_input = self.page.wait_for_selector(selector, timeout=3000)
                    if captcha_input:
                        self.logger.info(f"找到验证码输入框: {selector}")
                        break
                except:
                    pass
            
            if captcha_input:
                # 只有当验证码不为空时才填写
                if captcha_code:
                    captcha_input.fill(captcha_code)
                    self.logger.info(f"已填写验证码: {captcha_code}")
                else:
                    self.logger.info("验证码为空，保持字段不填写")
            else:
                self.logger.warning("未找到验证码输入框")
            
            # 查找并点击登录按钮
            button_selectors = [
                'button:has-text("确认登录")',
                'button:has-text("登录")',
                'button:has-text("Login")',
                'button:has-text("Sign in")',
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("提交")',
                '#login',
                '#submit',
                '.login-button'
            ]
            
            login_button = None
            for selector in button_selectors:
                try:
                    login_button = self.page.wait_for_selector(selector, timeout=5000)
                    if login_button:
                        self.logger.info(f"找到登录按钮: {selector}")
                        break
                except:
                    continue
            
            if not login_button:
                raise Exception("未找到登录按钮")
            
            # 点击登录按钮
            login_button.click()
            self.logger.info("已点击登录按钮")
            
            # 等待登录完成
            self.page.wait_for_load_state('networkidle', timeout=10000)
            
            # 检查是否登录成功
            result['page_title'] = self.page.title()
            result['page_url'] = self.page.url
            self.logger.info(f"登录后页面标题: {result['page_title']}")
            self.logger.info(f"登录后页面 URL: {result['page_url']}")
            
            # 登录后截图
            if self.config.SAVE_SCREENSHOT:
                screenshot_path = self._save_screenshot('after_login')
                result['screenshot'] = screenshot_path
            
            # 检查是否有错误信息
            error_selectors = [
                '.error',
                '.alert-danger',
                '[class*="error"]',
                '[class*="alert"]',
                '.alert',
                '.message'
            ]
            
            for selector in error_selectors:
                try:
                    error_element = self.page.query_selector(selector)
                    if error_element:
                        error_text = error_element.inner_text()
                        if error_text and ('错误' in error_text or 'error' in error_text.lower() or 'invalid' in error_text.lower()):
                            result['message'] = f"登录失败: {error_text}"
                            self.logger.warning(f"发现错误信息: {error_text}")
                            return result
                except:
                    pass
            
            # 判断登录是否成功（根据页面 URL 或标题）
            if '/user' in result['page_url'] or 'dashboard' in result['page_url'].lower():
                result['success'] = True
                result['message'] = '登录成功'
                self.logger.info("登录成功")
            else:
                result['message'] = '登录状态未知，请检查页面'
                self.logger.warning("登录状态未知")
            
            # 记录访问日志
            self._log_access(result)
            
            return result
            
        except Exception as e:
            result['message'] = f"登录失败: {str(e)}"
            self.logger.error(f"登录失败: {str(e)}")
            
            # 失败时截图
            if self.config.SCREENSHOT_ON_ERROR:
                screenshot_path = self._save_screenshot('error')
                result['screenshot'] = screenshot_path
            
            # 记录访问日志
            self._log_access(result)
            
            return result
    
    def _save_screenshot(self, prefix: str) -> str:
        """
        保存截图
        
        Args:
            prefix: 文件名前缀
        
        Returns:
            截图文件名（不含路径）
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{timestamp}.png"
        filepath = os.path.join(self.config.SCREENSHOT_DIR, filename)
        
        try:
            self.page.screenshot(path=filepath, full_page=True)
            self.logger.info(f"截图已保存: {filepath}")
            return filename
        except Exception as e:
            self.logger.error(f"截图保存失败: {str(e)}")
            return None
    
    def _log_access(self, result: Dict):
        """
        记录访问日志
        
        Args:
            result: 访问结果字典
        """
        log_entry = {
            'timestamp': result['timestamp'],
            'url': self.config.V2FREE_URL,
            'username': self.config.V2FREE_USERNAME,
            'success': result['success'],
            'message': result['message'],
            'page_title': result.get('page_title', ''),
            'page_url': result.get('page_url', ''),
            'retry_count': result.get('retry_count', 0),
            'screenshot': result.get('screenshot', '')
        }
        
        # 写入 JSON 格式日志
        log_file = os.path.join(self.config.LOG_DIR, 'access_log.json')
        
        try:
            # 读取现有日志
            logs = []
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            
            # 添加新日志
            logs.append(log_entry)
            
            # 只保留最近 100 条记录
            logs = logs[-100:]
            
            # 写入日志
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
            
            self.logger.info("访问日志已记录")
            
        except Exception as e:
            self.logger.error(f"访问日志记录失败: {str(e)}")
    
    def get_access_logs(self, limit: int = 10) -> list:
        """
        获取访问日志
        
        Args:
            limit: 返回的日志数量
        
        Returns:
            日志列表
        """
        log_file = os.path.join(self.config.LOG_DIR, 'access_log.json')
        
        try:
            if not os.path.exists(log_file):
                return []
            
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            # 按时间倒序返回
            logs.reverse()
            return logs[:limit]
            
        except Exception as e:
            self.logger.error(f"读取访问日志失败: {str(e)}")
            return []


def run_login() -> Dict:
    """
    便捷函数：执行一次登录操作
    
    Returns:
        登录结果字典
    """
    automation = V2freeAutomation()
    
    try:
        result = automation.login()
        return result
    finally:
        automation.stop_browser()


if __name__ == '__main__':
    # 测试登录
    result = run_login()
    print(json.dumps(result, ensure_ascii=False, indent=2))
