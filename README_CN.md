# TTSFM

[![Docker Pulls](https://img.shields.io/docker/pulls/dbcccc/ttsfm?style=flat-square&logo=docker)](https://hub.docker.com/r/dbcccc/ttsfm)
[![License](https://img.shields.io/github/license/dbccccccc/ttsfm?style=flat-square)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/dbccccccc/ttsfm?style=social)](https://github.com/dbccccccc/ttsfm)

> ⚠️ **免责声明**  
> 本项目仅用于学习和测试目的。生产环境请使用 [OpenAI 官方 TTS 服务](https://platform.openai.com/docs/guides/audio)。

> 🚨 **重要开发通知** 🚨  
> ⚠️ v2 分支目前正在积极开发中，不建议用于生产环境。
> 📚 如需稳定的文档和使用说明，请参考 [v1 文档](v1/README_v1.md)。

[English](README.md) | 中文

## 🌟 项目概述

TTSFM 是一个完全兼容 OpenAI 文本转语音 (TTS) API 格式的服务器。

> 🎮 立即体验: [官方演示](https://ttsapi.site/)

## 🏗️ 项目结构

```text
ttsfm/
├── app.py              # Flask 主应用
├── celery_worker.py    # Celery 配置和任务
├── requirements.txt    # Python 依赖
├── static/            # 前端资源
│   ├── index.html     # 英文界面
│   ├── index_zh.html  # 中文界面
│   ├── script.js      # 前端 JavaScript
│   └── styles.css     # 前端样式
├── voices/            # 语音样本
├── Dockerfile         # Docker 配置
├── docker-entrypoint.sh # Docker 启动脚本
├── .env.example       # 环境变量模板
├── .env              # 环境变量
├── .gitignore        # Git 忽略规则
├── LICENSE           # MIT 许可证
├── README.md         # 英文文档
├── README_CN.md      # 中文文档
├── test_api.py       # API 测试套件
├── test_queue.py     # 队列测试套件
└── .github/          # GitHub 工作流
```

## 🚀 快速开始

### 系统要求
- Python 3.13 或更高版本
- Redis 服务器
- Docker (可选)

### 使用 Docker (推荐)
```bash
# 拉取最新镜像
docker pull dbcccc/ttsfm:latest

# 运行容器
docker run -d \
  --name ttsfm \
  -p 7000:7000 \
  -p 6379:6379 \
  -v $(pwd)/voices:/app/voices \
  dbcccc/ttsfm:latest
```

### 手动安装
1. 克隆仓库:
```bash
git clone https://github.com/dbccccccc/ttsfm.git
cd ttsfm
```

2. 安装依赖:
```bash
pip install -r requirements.txt
```

3. 启动 Redis 服务器:
```bash
# Windows
redis-server

# Linux/macOS
sudo service redis-server start
```

4. 启动 Celery 工作进程:
```bash
celery -A celery_worker.celery worker --pool=solo -l info
```

5. 启动服务器:
```bash
# 开发环境 (不推荐用于生产)
python app.py

# 生产环境 (推荐)
waitress-serve --host=0.0.0.0 --port=7000 app:app
```

### 环境变量
复制 `.env.example` 到 `.env` 并根据需要修改:
```bash
cp .env.example .env
```

## 🔧 配置

### 服务器配置
- `HOST`: 服务器主机 (默认: 0.0.0.0)
- `PORT`: 服务器端口 (默认: 7000)
- `VERIFY_SSL`: SSL 验证 (默认: true)
- `MAX_QUEUE_SIZE`: 最大队列大小 (默认: 100)
- `RATE_LIMIT_REQUESTS`: 时间窗口内的请求限制 (默认: 30)
- `RATE_LIMIT_WINDOW`: 速率限制时间窗口 (秒) (默认: 60)

### Celery 配置
- `CELERY_BROKER_URL`: Redis 代理 URL (默认: redis://localhost:6379/0)
- `CELERY_RESULT_BACKEND`: Redis 结果后端 URL (默认: redis://localhost:6379/0)

## 📚 API 文档

### 文本转语音
```http
POST /v1/audio/speech
```

请求体:
```json
{
  "input": "你好，世界！",
  "voice": "alloy",
  "response_format": "mp3",
  "instructions": "用欢快的语气说话"
}
```

#### 参数
- `input` (必需): 要转换为语音的文本
- `voice` (必需): 要使用的语音。
- `response_format` (可选): 音频输出格式。默认: mp3。支持的格式: mp3, opus, aac, flac, wav, pcm
- `instructions` (可选): 语音调制的额外指令

#### 响应
- 成功: 返回音频数据和相应的内容类型
- 错误: 返回包含错误信息和状态码的 JSON

### 队列状态
```http
GET /api/queue-size
```

响应:
```json
{
  "queue_size": 5,
  "max_queue_size": 100
}
```

### 语音样本
```http
GET /api/voice-sample/{voice}
```

#### 参数
- `voice` (必需): 要获取样本的语音。必须是以下之一: alloy, ash, ballad, coral, echo, fable, onyx, nova, sage, shimmer, verse

#### 响应
- 成功: 返回 MP3 音频样本
- 错误: 返回包含错误信息和状态码的 JSON

### 版本
```http
GET /api/version
```

响应:
```json
{
  "version": "v2.0.0-alpha1"
}
```

## 📝 许可证
本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢
- [OpenAI](https://openai.com/) 提供 TTS API 格式
- [Flask](https://flask.palletsprojects.com/) 提供 Web 框架
- [Celery](https://docs.celeryq.dev/) 提供任务队列管理
- [Waitress](https://docs.pylonsproject.org/projects/waitress/) 提供生产环境 WSGI 服务器