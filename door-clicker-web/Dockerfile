# ============================================================
# 多阶段构建 — door-clicker-web
# Stage 1: builder  — 安装编译依赖，构建 site-packages
# Stage 2: final    — 只拷贝运行时必需内容，非 root 用户启动
# ============================================================

# ---------- Builder ----------
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装编译 eventlet / gevent / cryptography 等可能需要的系统依赖
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libffi-dev \
        libssl-dev \
        python3-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# 分层缓存：requirements 不变时 pip install 命中缓存
COPY requirements.txt ./
RUN python -m pip install --prefix=/install --no-warn-script-location -r requirements.txt

# ---------- Final Runtime ----------
FROM python:3.12-slim-bookworm AS final

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_HOME=/app \
    PORT=5000

# 运行时的轻量系统依赖（保留 ca-certificates 让 SSL 正常）
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd -r app \
 && useradd  -r -g app -s /usr/sbin/nologin -d "$APP_HOME" app \
 && mkdir -p "$APP_HOME/data/logs" "$APP_HOME/src" \
 && chown -R app:app "$APP_HOME"

# 把 builder 阶段安装好的 site-packages 整份拷过来
COPY --from=builder /install /usr/local

WORKDIR $APP_HOME/src

# 拷贝应用源码（最后一步，改代码不影响依赖层缓存）
COPY --chown=app:app src/ ./

EXPOSE 5000

VOLUME ["$APP_HOME/data"]

USER app

# 生产默认：gunicorn + eventlet worker（WebSocket 正常工作）
# 开发模式下 compose 会通过 command 覆盖回 python app.py
CMD ["python", "-m", "gunicorn", \
     "-k", "eventlet", \
     "-w", "1", \
     "-b", "0.0.0.0:5000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:app"]
