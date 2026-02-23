"""
V2free 浏览器自动化路由
提供独立的管理页面和API接口
"""

from flask import Blueprint, render_template, jsonify, request, send_file, session
import os
import json
from datetime import datetime
import threading
import uuid

# 全局变量，保持浏览器实例（使用会话ID作为键）
_browser_instances = {}
_browser_lock = threading.Lock()

# 尝试导入自动化模块
try:
    from app.v2free.automation import V2freeAutomation, run_login

    V2FREE_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入 V2free 自动化模块: {e}")
    V2FREE_AVAILABLE = False


def register_v2free_blueprint(app):
    """注册 V2free 蓝图"""

    if not V2FREE_AVAILABLE:
        app.logger.warning("V2free 自动化模块不可用，跳过注册")
        return False

    # 创建蓝图
    bp = Blueprint("v2free", __name__, url_prefix="/v2free")

    @bp.route("/")
    def index():
        """V2free 管理主页"""
        automation = V2freeAutomation()
        logs = automation.get_access_logs(limit=20)

        return render_template(
            "v2free/index.html",
            logs=logs,
            config_url=automation.config.V2FREE_URL,
            username=automation.config.V2FREE_USERNAME,
        )

    @bp.route("/screenshot/<path:filename>")
    def serve_screenshot(filename):
        """提供截图文件"""
        from app.v2free.config import V2freeConfig

        config = V2freeConfig()
        screenshot_path = os.path.join(config.SCREENSHOT_DIR, filename)

        if os.path.exists(screenshot_path):
            return send_file(screenshot_path, mimetype="image/png")
        else:
            return jsonify({"error": "File not found"}), 404

    @bp.route("/api/prepare", methods=["POST"])
    def api_prepare():
        """准备登录表单（填写用户名和密码，截取验证码）"""
        global _browser_instances

        if not V2FREE_AVAILABLE:
            return jsonify(
                {
                    "success": False,
                    "message": "V2free 自动化模块不可用",
                    "timestamp": datetime.now().isoformat(),
                }
            ), 500

        try:
            # 生成唯一的会话ID
            session_id = str(uuid.uuid4())

            # 创建新的自动化实例
            automation = V2freeAutomation()

            # 准备登录表单
            result = automation.prepare_login_form()

            # 将浏览器实例保存到全局字典中
            with _browser_lock:
                _browser_instances[session_id] = automation
                # 清理旧实例（保留最近10个）
                if len(_browser_instances) > 10:
                    old_keys = list(_browser_instances.keys())[:-10]
                    for key in old_keys:
                        try:
                            _browser_instances[key].stop_browser(force=True)
                            del _browser_instances[key]
                        except:
                            pass

            # 添加会话ID和截图 URL
            result["session_id"] = session_id
            if result.get("captcha_image"):
                result["captcha_image_url"] = (
                    f"/v2free/screenshot/{result['captcha_image']}"
                )
            if result.get("screenshot"):
                result["screenshot_url"] = f"/v2free/screenshot/{result['screenshot']}"

            return jsonify(result)

        except Exception as e:
            return jsonify(
                {
                    "success": False,
                    "message": f"准备登录表单失败: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                }
            ), 500

    @bp.route("/api/submit", methods=["POST"])
    def api_submit():
        """使用验证码提交登录"""
        global _browser_instances

        if not V2FREE_AVAILABLE:
            return jsonify(
                {
                    "success": False,
                    "message": "V2free 自动化模块不可用",
                    "timestamp": datetime.now().isoformat(),
                }
            ), 500

        try:
            # 获取会话ID和验证码
            data = request.get_json()
            session_id = data.get("session_id")
            captcha_code = data.get("captcha", "")

            if not session_id:
                return jsonify(
                    {
                        "success": False,
                        "message": "缺少会话ID",
                        "timestamp": datetime.now().isoformat(),
                    }
                ), 400

            with _browser_lock:
                if session_id not in _browser_instances:
                    return jsonify(
                        {
                            "success": False,
                            "message": "浏览器未准备，请先调用 /api/prepare",
                            "timestamp": datetime.now().isoformat(),
                        }
                    ), 400

                # 提交登录
                automation = _browser_instances[session_id]
                result = automation.submit_login_with_captcha(captcha_code)

                # 添加截图 URL
                if result.get("screenshot"):
                    result["screenshot_url"] = (
                        f"/v2free/screenshot/{result['screenshot']}"
                    )

                # 关闭浏览器并删除实例
                automation.stop_browser(force=True)
                del _browser_instances[session_id]

                return jsonify(result)

        except Exception as e:
            # 发生错误时关闭浏览器
            with _browser_lock:
                if session_id and session_id in _browser_instances:
                    _browser_instances[session_id].stop_browser(force=True)
                    del _browser_instances[session_id]

            return jsonify(
                {
                    "success": False,
                    "message": f"提交登录失败: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                }
            ), 500

    @bp.route("/api/cancel", methods=["POST"])
    def api_cancel():
        """取消登录操作并关闭浏览器"""
        global _browser_instances

        try:
            # 获取会话ID
            data = request.get_json()
            session_id = data.get("session_id") if data else None

            with _browser_lock:
                if session_id and session_id in _browser_instances:
                    _browser_instances[session_id].stop_browser(force=True)
                    del _browser_instances[session_id]
                else:
                    # 如果没有提供会话ID，关闭所有实例
                    for key in list(_browser_instances.keys()):
                        try:
                            _browser_instances[key].stop_browser(force=True)
                        except:
                            pass
                    _browser_instances.clear()

            return jsonify(
                {
                    "success": True,
                    "message": "已取消登录操作",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            return jsonify(
                {
                    "success": False,
                    "message": f"取消失败: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                }
            ), 500

    @bp.route("/api/login", methods=["POST"])
    def api_login():
        """执行登录API（保留旧的接口以兼容）"""
        if not V2FREE_AVAILABLE:
            return jsonify(
                {
                    "success": False,
                    "message": "V2free 自动化模块不可用",
                    "timestamp": datetime.now().isoformat(),
                }
            ), 500

        try:
            result = run_login()
            return jsonify(result)

        except Exception as e:
            return jsonify(
                {
                    "success": False,
                    "message": f"登录失败: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                }
            ), 500

    @bp.route("/api/logs")
    def api_logs():
        """获取访问日志API"""
        if not V2FREE_AVAILABLE:
            return jsonify(
                {"success": False, "message": "V2free 自动化模块不可用", "logs": []}
            ), 500

        try:
            limit = request.args.get("limit", 20, type=int)
            automation = V2freeAutomation()
            logs = automation.get_access_logs(limit=limit)

            return jsonify(
                {
                    "success": True,
                    "count": len(logs),
                    "logs": logs,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            return jsonify(
                {"success": False, "message": f"获取日志失败: {str(e)}", "logs": []}
            ), 500

    @bp.route("/api/config")
    def api_config():
        """获取配置信息API（隐藏密码）"""
        if not V2FREE_AVAILABLE:
            return jsonify(
                {"success": False, "message": "V2free 自动化模块不可用"}
            ), 500

        try:
            from app.v2free.config import V2freeConfig

            config = V2freeConfig()

            return jsonify(
                {
                    "success": True,
                    "config": {
                        "url": config.V2FREE_URL,
                        "username": config.V2FREE_USERNAME,
                        "headless": config.BROWSER_HEADLESS,
                        "timeout": config.BROWSER_TIMEOUT,
                        "use_proxy": config.USE_PROXY,
                        "proxy_server": config.PROXY_SERVER
                        if config.USE_PROXY
                        else None,
                    },
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            return jsonify(
                {"success": False, "message": f"获取配置失败: {str(e)}"}
            ), 500

    @bp.route("/api/health")
    def api_health():
        """健康检查API"""
        return jsonify(
            {
                "status": "healthy",
                "module": "v2free_automation",
                "available": V2FREE_AVAILABLE,
                "timestamp": datetime.now().isoformat(),
            }
        )

    # 注册蓝图到应用
    app.register_blueprint(bp)
    app.logger.info("V2free 自动化管理页面已注册到 /v2free/")

    return True


if __name__ == "__main__":
    # 测试代码
    from flask import Flask

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-key"
    app.template_folder = "templates"

    register_v2free_blueprint(app)

    with app.app_context():
        print("可用路由:")
        for rule in app.url_map.iter_rules():
            print(f"  {rule.endpoint}: {rule.rule}")
