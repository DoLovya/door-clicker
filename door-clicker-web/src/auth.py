import hashlib
import os
import time
from functools import wraps

from flask import jsonify, redirect, render_template, request, session

from log_manager import LogManager


SESSION_TIMEOUT = 3600
DEFAULT_ADMIN_PASSWORD = "admin"

log_manager = LogManager()


def _hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _get_stored_hash(config_manager):
    config = config_manager.get_config()
    stored_hash = config.get("adminPasswordHash", "")
    if not stored_hash:
        default_hash = _hash_password(DEFAULT_ADMIN_PASSWORD)
        config_manager.update_config({
            "adminUser": config.get("adminUser", "admin"),
            "adminPasswordHash": default_hash,
        })
        return default_hash
    return stored_hash


def init_auth(app, config_manager):
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "door-clicker-secret-key-2024")
    app.config["PERMANENT_SESSION_LIFETIME"] = SESSION_TIMEOUT

    @app.route("/login", methods=["GET", "POST"])
    def login_page():
        if request.method == "GET":
            if session.get("authenticated"):
                return redirect("/config")
            return render_template("login.html", error=None)

        data = request.get_json(silent=True) or request.form
        username = data.get("username", "")
        password = data.get("password", "")

        if not username or not password:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Username and password required"}), 400
            return render_template("login.html", error="请输入用户名和密码")

        config = config_manager.get_config()
        admin_user = config.get("adminUser", "admin")
        stored_hash = _get_stored_hash(config_manager)

        if username == admin_user and _hash_password(password) == stored_hash:
            session.clear()
            session["authenticated"] = True
            session["username"] = username
            session["login_time"] = time.time()
            if request.path.startswith("/api/"):
                return jsonify({"success": True})
            return redirect("/config")

        if request.path.startswith("/api/"):
            return jsonify({"error": "Invalid username or password"}), 401
        return render_template("login.html", error="用户名或密码错误")

    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear()
        if request.accept_mimetypes.best == "application/json":
            return jsonify({"success": True})
        return redirect("/login")

    @app.route("/api/auth/login", methods=["POST"])
    def api_login():
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Invalid request"}), 400

        username = data.get("username", "")
        password = data.get("password", "")

        config = config_manager.get_config()
        admin_user = config.get("adminUser", "admin")
        stored_hash = _get_stored_hash(config_manager)

        if username == admin_user and _hash_password(password) == stored_hash:
            session.clear()
            session["authenticated"] = True
            session["username"] = username
            session["login_time"] = time.time()
            log_manager.log_info(f"用户登录成功: {username}")
            return jsonify({"success": True})

        log_manager.log_error(f"用户登录失败: {username}")
        return jsonify({"error": "Invalid username or password"}), 401

    @app.route("/api/auth/logout", methods=["POST"])
    def api_logout():
        username = session.get("username", "unknown")
        session.clear()
        log_manager.log_info(f"用户登出: {username}")
        return jsonify({"success": True})

    @app.route("/api/auth/status", methods=["GET"])
    def api_auth_status():
        if session.get("authenticated"):
            login_time = session.get("login_time", 0)
            remaining = SESSION_TIMEOUT - (time.time() - login_time)
            return jsonify({"authenticated": True, "remaining": max(0, int(remaining))})
        return jsonify({"authenticated": False})


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("authenticated"):
            session.clear()
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect("/login?next=" + request.path)

        login_time = session.get("login_time", 0)
        if time.time() - login_time > SESSION_TIMEOUT:
            session.clear()
            if request.path.startswith("/api/"):
                return jsonify({"error": "Session expired"}), 401
            return redirect("/login?next=" + request.path)

        session["login_time"] = time.time()
        return f(*args, **kwargs)
    return decorated_function
