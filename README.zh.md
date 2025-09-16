# TTSFM - 文本转语音API客户端

> **Language / 语言**: [English](README.md) | [中文](README.zh.md)

[![Docker Pulls](https://img.shields.io/docker/pulls/dbcccc/ttsfm?style=flat-square&logo=docker)](https://hub.docker.com/r/dbcccc/ttsfm)
[![GitHub Stars](https://img.shields.io/github/stars/dbccccccc/ttsfm?style=social)](https://github.com/dbccccccc/ttsfm)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

## Star历史

[![Star History Chart](https://api.star-history.com/svg?repos=dbccccccc/ttsfm&type=Date)](https://www.star-history.com/#dbccccccc/ttsfm&Date)

🎤 **现代化、免费的文本转语音API客户端，兼容OpenAI**

TTSFM为文本转语音生成提供同步和异步Python客户端，使用逆向工程的openai.fm服务。无需API密钥 - 完全免费使用！

## ✨ 主要特性

- 🆓 **完全免费** - 使用逆向工程的openai.fm服务（无需API密钥）
- 🎯 **OpenAI兼容** - OpenAI TTS API的直接替代品（`/v1/audio/speech`）
- ⚡ **异步和同步** - 提供`asyncio`和同步客户端
- 🗣️ **11种声音** - 所有OpenAI兼容的声音（alloy、echo、fable、onyx、nova、shimmer等）
- 🎵 **6种音频格式** - 支持MP3、WAV、OPUS、AAC、FLAC、PCM
- 🐳 **Docker就绪** - 一键部署，包含Web界面
- 🌐 **Web界面** - 用于测试声音和格式的交互式试用平台
- 🔧 **CLI工具** - 用于快速TTS生成的命令行界面
- 📦 **类型提示** - 完整的类型注解支持，提供更好的IDE体验
- 🛡️ **错误处理** - 全面的异常层次结构和重试逻辑
- ✨ **自动合并** - 自动处理长文本，无缝音频合并
- 📊 **文本验证** - 自动文本长度验证和分割
- 🔐 **API密钥保护** - 可选的OpenAI兼容身份验证，用于安全部署

## 📦 安装

### 快速安装

```bash
pip install ttsfm
```

### 安装选项

```bash
# 基础安装（仅同步客户端）
pip install ttsfm

# 包含Web应用支持
pip install ttsfm[web]

# 包含开发工具
pip install ttsfm[dev]

# 包含文档工具
pip install ttsfm[docs]

# 安装所有可选依赖
pip install ttsfm[web,dev,docs]
```

### 系统要求

- **Python**: 3.8+（在3.8、3.9、3.10、3.11、3.12上测试）
- **操作系统**: Windows、macOS、Linux
- **依赖**: `requests`、`aiohttp`、`fake-useragent`

## 🚀 快速开始

### 🐳 Docker（推荐）

运行带有Web界面和OpenAI兼容API的TTSFM：

```bash
# 使用GitHub Container Registry
docker run -p 8000:8000 ghcr.io/dbccccccc/ttsfm:latest

# 使用Docker Hub
docker run -p 8000:8000 dbcccc/ttsfm:latest
```

容器现在默认监听 `0.0.0.0`，因此端口映射会立即对宿主机开放。如需限制
监听地址，可以通过设置 `HOST` 环境变量进行覆盖。

**可用端点：**
- 🌐 **Web界面**: http://localhost:8000
- 🔗 **OpenAI API**: http://localhost:8000/v1/audio/speech
- 📊 **健康检查**: http://localhost:8000/api/health

**测试API：**

```bash
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini-tts","input":"你好世界！","voice":"alloy"}' \
  --output speech.mp3
```

### 📦 Python包

#### 同步客户端

```python
from ttsfm import TTSClient, Voice, AudioFormat

# 创建客户端（使用免费的openai.fm服务）
client = TTSClient()

# 生成语音
response = client.generate_speech(
    text="你好！这是TTSFM - 一个免费的TTS服务。",
    voice=Voice.CORAL,
    response_format=AudioFormat.MP3
)

# 保存音频文件
response.save_to_file("output")  # 保存为output.mp3

# 或获取原始音频数据
audio_bytes = response.audio_data
print(f"生成了 {len(audio_bytes)} 字节的音频")
```

#### 异步客户端

```python
import asyncio
from ttsfm import AsyncTTSClient, Voice

async def generate_speech():
    async with AsyncTTSClient() as client:
        response = await client.generate_speech(
            text="异步TTS生成！",
            voice=Voice.NOVA
        )
        response.save_to_file("async_output")

# 运行异步函数
asyncio.run(generate_speech())
```

#### 长文本处理（Python包）

对于需要精细控制文本分割的开发者：

```python
from ttsfm import TTSClient, Voice, AudioFormat

# 创建客户端
client = TTSClient()

# 从长文本生成语音（为每个片段创建单独的文件）
responses = client.generate_speech_long_text(
    text="超过4096字符的很长文本...",
    voice=Voice.ALLOY,
    response_format=AudioFormat.MP3,
    max_length=2000,
    preserve_words=True
)

# 将每个片段保存为单独的文件
for i, response in enumerate(responses, 1):
    response.save_to_file(f"part_{i:03d}")  # 保存为part_001.mp3、part_002.mp3等

print(f"从长文本生成了 {len(responses)} 个音频文件")
```

#### OpenAI Python客户端兼容性

```python
from openai import OpenAI

# 指向TTSFM Docker容器（默认不需要API密钥）
client = OpenAI(
    api_key="not-needed",  # TTSFM默认免费
    base_url="http://localhost:8000/v1"
)

# 启用API密钥保护时
client_with_auth = OpenAI(
    api_key="your-secret-api-key",  # 您的TTSFM API密钥
    base_url="http://localhost:8000/v1"
)

# 生成语音（与OpenAI完全相同）
response = client.audio.speech.create(
    model="gpt-4o-mini-tts",
    voice="alloy",
    input="来自TTSFM的问候！"
)

response.stream_to_file("output.mp3")
```

#### 长文本自动合并功能

TTSFM通过新的自动合并功能自动处理长文本（>4096字符）：

```python
from openai import OpenAI

client = OpenAI(
    api_key="not-needed",
    base_url="http://localhost:8000/v1"
)

# 长文本自动分割并合并为单个音频文件
long_article = """
您的很长的文章或文档内容在这里...
这可以是数千字符长，TTSFM将
自动将其分割成片段，为每个片段生成音频，
并将它们合并成一个无缝的音频文件。
""" * 100  # 使其真的很长

# 这可以无缝工作 - 无需手动分割！
response = client.audio.speech.create(
    model="gpt-4o-mini-tts",
    voice="nova",
    input=long_article,
    # auto_combine=True 是默认值
)

response.stream_to_file("long_article.mp3")  # 单个合并文件！

# 禁用自动合并以严格兼容OpenAI
response = client.audio.speech.create(
    model="gpt-4o-mini-tts",
    voice="nova",
    input="仅短文本",
    auto_combine=False  # 如果文本>4096字符将出错
)
```

### 🖥️ 命令行界面

```bash
# 基本用法
ttsfm "你好，世界！" --output hello.mp3

# 指定声音和格式
ttsfm "你好，世界！" --voice nova --format wav --output hello.wav

# 从文件读取
ttsfm --text-file input.txt --output speech.mp3

# 自定义服务URL
ttsfm "你好，世界！" --url http://localhost:7000 --output hello.mp3

# 列出可用声音
ttsfm --list-voices

# 获取帮助
ttsfm --help
```

## ⚙️ 配置

TTSFM自动使用免费的openai.fm服务 - **默认情况下无需配置或API密钥！**

### 环境变量

| 变量 | 默认值 | 描述 |
|----------|---------|-------------|
| `REQUIRE_API_KEY` | `false` | 启用API密钥保护 |
| `TTSFM_API_KEY` | `None` | 您的秘密API密钥 |
| `HOST` | `localhost` | 服务器主机 |
| `PORT` | `8000` | 服务器端口 |
| `DEBUG` | `false` | 调试模式 |

### Python客户端配置

```python
from ttsfm import TTSClient

# 默认客户端（使用openai.fm，无需API密钥）
client = TTSClient()

# 自定义配置
client = TTSClient(
    base_url="https://www.openai.fm",  # 默认
    timeout=30.0,                     # 请求超时
    max_retries=3,                    # 重试次数
    verify_ssl=True                   # SSL验证
)

# 用于带有API密钥保护的TTSFM服务器
protected_client = TTSClient(
    base_url="http://localhost:8000",
    api_key="your-ttsfm-api-key"
)

# 用于其他自定义TTS服务
custom_client = TTSClient(
    base_url="http://your-tts-service.com",
    api_key="your-api-key-if-needed"
)
```

## 🗣️ 可用声音

TTSFM支持所有**11种OpenAI兼容声音**：

| 声音 | 描述 | 最适合 |
|-------|-------------|----------|
| `alloy` | 平衡且多功能 | 通用目的，中性语调 |
| `ash` | 清晰且清楚 | 专业，商务内容 |
| `ballad` | 流畅且优美 | 讲故事，有声读物 |
| `coral` | 温暖且友好 | 客户服务，教程 |
| `echo` | 共鸣且清晰 | 公告，演示 |
| `fable` | 富有表现力且动态 | 创意内容，娱乐 |
| `nova` | 明亮且充满活力 | 营销，积极内容 |
| `onyx` | 深沉且权威 | 新闻，严肃内容 |
| `sage` | 智慧且稳重 | 教育，信息性 |
| `shimmer` | 轻盈且飘逸 | 休闲，对话式 |
| `verse` | 有节奏且流畅 | 诗歌，艺术内容 |

```python
from ttsfm import Voice

# 使用枚举值
response = client.generate_speech("你好！", voice=Voice.CORAL)

# 或使用字符串值
response = client.generate_speech("你好！", voice="coral")

# 测试不同声音
for voice in Voice:
    response = client.generate_speech(f"这是{voice.value}声音", voice=voice)
    response.save_to_file(f"test_{voice.value}")
```

## 🎵 音频格式

TTSFM支持**6种音频格式**，具有不同的质量和压缩选项：

| 格式 | 扩展名 | 质量 | 文件大小 | 使用场景 |
|--------|-----------|---------|-----------|----------|
| `mp3` | `.mp3` | 良好 | 小 | Web、移动应用、通用使用 |
| `opus` | `.opus` | 优秀 | 小 | Web流媒体、VoIP |
| `aac` | `.aac` | 良好 | 中等 | Apple设备、流媒体 |
| `flac` | `.flac` | 无损 | 大 | 高质量存档 |
| `wav` | `.wav` | 无损 | 大 | 专业音频 |
| `pcm` | `.pcm` | 原始 | 大 | 音频处理 |

### **使用示例**

```python
from ttsfm import TTSClient, AudioFormat

client = TTSClient()

# 生成不同格式
formats = [
    AudioFormat.MP3,   # 最常见
    AudioFormat.OPUS,  # 最佳压缩
    AudioFormat.AAC,   # Apple兼容
    AudioFormat.FLAC,  # 无损
    AudioFormat.WAV,   # 未压缩
    AudioFormat.PCM    # 原始音频
]

for fmt in formats:
    response = client.generate_speech(
        text="测试音频格式",
        response_format=fmt
    )
    response.save_to_file(f"test.{fmt.value}")
```

### **格式选择指南**

- **选择MP3**用于：
  - Web应用
  - 移动应用
  - 较小的文件大小
  - 通用音频

- **选择OPUS**用于：
  - Web流媒体
  - VoIP应用
  - 最佳压缩比
  - 实时音频

- **选择AAC**用于：
  - Apple设备
  - 流媒体服务
  - 良好的质量/大小平衡

- **选择FLAC**用于：
  - 存档目的
  - 无损压缩
  - 专业工作流程

- **选择WAV**用于：
  - 专业音频制作
  - 最大兼容性
  - 当文件大小不是问题时

- **选择PCM**用于：
  - 音频处理
  - 原始音频数据
  - 自定义应用

> **注意**：库会自动优化请求，为您选择的格式提供最佳质量。文件总是根据音频格式以正确的扩展名保存。

## 🌐 Web界面

TTSFM包含一个**美观的Web界面**用于测试和实验：

![Web Interface](https://img.shields.io/badge/Web%20Interface-Available-brightgreen?style=flat-square)

**功能：**
- 🎮 **交互式试用平台** - 实时测试声音和格式
- 📝 **文本验证** - 字符计数和长度验证
- 🎛️ **高级选项** - 声音指令，自动分割长文本
- 📊 **音频播放器** - 内置播放器，显示时长和文件大小信息
- 📥 **下载支持** - 下载单个或批量音频文件
- 🎲 **随机文本** - 生成随机示例文本进行测试
- 📱 **响应式设计** - 在桌面、平板和移动设备上工作

访问地址：http://localhost:8000（运行Docker容器时）

## 🔗 API端点

运行Docker容器时，这些端点可用：

| 端点 | 方法 | 描述 |
|----------|--------|-------------|
| `/` | GET | Web界面 |
| `/playground` | GET | 交互式TTS试用平台 |
| `/v1/audio/speech` | POST | OpenAI兼容的TTS API |
| `/v1/models` | GET | 列出可用模型 |
| `/api/health` | GET | 健康检查端点 |
| `/api/voices` | GET | 列出可用声音 |
| `/api/formats` | GET | 列出支持的音频格式 |
| `/api/validate-text` | POST | 验证文本长度 |

### OpenAI兼容API

```bash
# 生成语音（短文本） - 默认不需要API密钥
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini-tts",
    "input": "你好，这是一个测试！",
    "voice": "alloy",
    "response_format": "mp3"
  }' \
  --output speech.mp3

# 使用API密钥生成语音（启用保护时）
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secret-api-key" \
  -d '{
    "model": "gpt-4o-mini-tts",
    "input": "你好，这是一个测试！",
    "voice": "alloy",
    "response_format": "mp3"
  }' \
  --output speech.mp3

# 使用自动合并从长文本生成语音（默认行为）
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini-tts",
    "input": "这是一个超过4096字符限制的很长文本...",
    "voice": "alloy",
    "response_format": "mp3",
    "auto_combine": true
  }' \
  --output long_speech.mp3

# 不使用自动合并从长文本生成语音（如果文本>4096字符将返回错误）
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini-tts",
    "input": "您的文本在这里...",
    "voice": "alloy",
    "response_format": "mp3",
    "auto_combine": false
  }' \
  --output speech.mp3

# 列出模型
curl http://localhost:8000/v1/models

# 健康检查
curl http://localhost:8000/api/health
```

#### **新参数：`auto_combine`**

TTSFM通过可选的`auto_combine`参数扩展了OpenAI API：

- **`auto_combine`**（布尔值，可选，默认：`true`）
  - 当为`true`时：自动将长文本（>4096字符）分割成片段，为每个片段生成音频，并将它们合并成一个无缝的音频文件
  - 当为`false`时：如果文本超过4096字符限制则返回错误（标准OpenAI行为）
  - **好处**：无需手动管理长内容的文本分割或音频文件合并

## 🐳 Docker部署

### 快速开始

```bash
# 使用默认设置运行（无需API密钥）
docker run -p 8000:8000 ghcr.io/dbccccccc/ttsfm:latest

# 启用API密钥保护运行
docker run -p 8000:8000 \
  -e REQUIRE_API_KEY=true \
  -e TTSFM_API_KEY=your-secret-api-key \
  ghcr.io/dbccccccc/ttsfm:latest

# 使用自定义端口运行
docker run -p 3000:8000 ghcr.io/dbccccccc/ttsfm:latest

# 后台运行
docker run -d -p 8000:8000 --name ttsfm ghcr.io/dbccccccc/ttsfm:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  ttsfm:
    image: ghcr.io/dbccccccc/ttsfm:latest
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
      # 可选：启用API密钥保护
      - REQUIRE_API_KEY=false
      - TTSFM_API_KEY=your-secret-api-key-here
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 可用镜像

| 注册表 | 镜像 | 描述 |
|----------|-------|-------------|
| GitHub Container Registry | `ghcr.io/dbccccccc/ttsfm:latest` | 最新稳定版本 |
| Docker Hub | `dbcccc/ttsfm:latest` | Docker Hub镜像 |
| GitHub Container Registry | `ghcr.io/dbccccccc/ttsfm:v3.2.8` | 特定版本 |

## 🛠️ 高级用法

### 错误处理

```python
from ttsfm import TTSClient, TTSException, APIException, NetworkException

client = TTSClient()

try:
    response = client.generate_speech("你好，世界！")
    response.save_to_file("output")
except NetworkException as e:
    print(f"网络错误：{e}")
except APIException as e:
    print(f"API错误：{e}")
except TTSException as e:
    print(f"TTS错误：{e}")
```

### 文本验证和分割

```python
from ttsfm.utils import validate_text_length, split_text_by_length

# 验证文本长度
text = "您的长文本在这里..."
is_valid, length = validate_text_length(text, max_length=4096)

if not is_valid:
    # 将长文本分割成片段
    chunks = split_text_by_length(text, max_length=4000)

    # 为每个片段生成语音
    for i, chunk in enumerate(chunks):
        response = client.generate_speech(chunk)
        response.save_to_file(f"output_part_{i}")
```

### 自定义请求头和用户代理

```python
from ttsfm import TTSClient

# 客户端自动使用真实的请求头
client = TTSClient()

# 请求头包括：
# - 真实的User-Agent字符串
# - 音频内容的Accept头
# - 连接保持活跃
# - 压缩的Accept-Encoding
```

## 🔧 开发

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/dbccccccc/ttsfm.git
cd ttsfm

# 以开发模式安装
pip install -e .[dev]

# 运行测试
pytest

# 运行Web应用
cd ttsfm-web
python app.py
```

### 构建Docker镜像

```bash
# 构建镜像
docker build -t ttsfm:local .

# 运行本地镜像
docker run -p 8000:8000 ttsfm:local
```

### 贡献

1. Fork仓库
2. 创建功能分支（`git checkout -b feature/amazing-feature`）
3. 提交更改（`git commit -m 'Add amazing feature'`）
4. 推送到分支（`git push origin feature/amazing-feature`）
5. 打开Pull Request

## 📊 性能

### 基准测试

- **延迟**：典型文本约1-3秒（取决于openai.fm服务）
- **吞吐量**：异步客户端支持并发请求
- **文本限制**：使用自动合并无限制！自动处理任何长度的文本
- **音频质量**：与OpenAI相当的高质量合成

### 优化技巧

```python
# 使用异步客户端获得更好的性能
async with AsyncTTSClient() as client:
    # 并发处理多个请求
    tasks = [
        client.generate_speech(f"文本 {i}")
        for i in range(10)
    ]
    responses = await asyncio.gather(*tasks)

# 重用客户端实例
client = TTSClient()
for text in texts:
    response = client.generate_speech(text)  # 重用连接
```

## 🔐 API密钥保护（可选）

TTSFM支持**OpenAI兼容的API密钥身份验证**用于安全部署：

### 快速设置

```bash
# 启用API密钥保护
export REQUIRE_API_KEY=true
export TTSFM_API_KEY=your-secret-api-key

# 启用保护运行
docker run -p 8000:8000 \
  -e REQUIRE_API_KEY=true \
  -e TTSFM_API_KEY=your-secret-api-key \
  ghcr.io/dbccccccc/ttsfm:latest
```

### 身份验证方法

API密钥以**OpenAI兼容格式**接受：

```python
from openai import OpenAI

# 标准OpenAI格式
client = OpenAI(
    api_key="your-secret-api-key",
    base_url="http://localhost:8000/v1"
)

# 或使用curl
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Authorization: Bearer your-secret-api-key" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini-tts","input":"你好！","voice":"alloy"}'
```

### 功能

- 🔑 **OpenAI兼容**：使用标准`Authorization: Bearer`头
- 🛡️ **多种认证方法**：头部、查询参数或JSON正文
- 🎛️ **可配置**：通过环境变量轻松启用/禁用
- 📊 **安全日志**：跟踪无效访问尝试
- 🌐 **Web界面**：自动API密钥字段检测

### 受保护的端点

启用时，这些端点需要身份验证：
- `POST /v1/audio/speech` - 语音生成
- `POST /api/generate` - 传统语音生成
- `POST /api/generate-combined` - 合并语音生成

### 公共端点

这些端点无需身份验证即可访问：
- `GET /` - Web界面
- `GET /playground` - 交互式试用平台
- `GET /api/health` - 健康检查
- `GET /api/voices` - 可用声音
- `GET /api/formats` - 支持的格式

## 🔒 安全和隐私

- **可选API密钥**：默认免费，需要时安全
- **无数据存储**：音频按需生成，不存储
- **HTTPS支持**：到TTS服务的安全连接
- **无跟踪**：TTSFM不收集或存储用户数据
- **开源**：完整源代码可供审计

## 📋 更新日志

查看[CHANGELOG.md](CHANGELOG.md)了解详细版本历史。

### 最新更改（v3.2.8）

- 🐳 **Docker 默认监听升级**：容器自动绑定 `0.0.0.0`，解决端口映射后 WebSocket 长时间“Starting”及 HTTP 502 的问题。
- 📘 **文档同步更新**：README 新增说明，展示如何通过 `HOST` 环境变量重写绑定地址。
- 🌐 **界面版本同步**：Web 徽章、健康检查和多语言文案均更新为 v3.2.8，方便快速确认运行版本。
- 🧪 **发布就绪**：包元数据与分发清单已对齐，为 v3.2.8 的 PyPI 与镜像发布做好准备。

## 🤝 支持和社区

- 🐛 **错误报告**：[GitHub Issues](https://github.com/dbccccccc/ttsfm/issues)
- 💬 **讨论**：[GitHub Discussions](https://github.com/dbccccccc/ttsfm/discussions)
- 👤 **作者**：[@dbcccc](https://github.com/dbccccccc)
- ⭐ **为项目加星**：如果您觉得TTSFM有用，请在GitHub上为其加星！

## 📄 许可证

MIT许可证 - 详见[LICENSE](LICENSE)文件。

## 🙏 致谢

- **OpenAI**：原始TTS API设计
- **openai.fm**：提供免费TTS服务
- **社区**：感谢所有帮助改进TTSFM的用户和贡献者

---

<div align="center">

**TTSFM** - 免费文本转语音API，兼容OpenAI

[![GitHub](https://img.shields.io/badge/GitHub-dbccccccc/ttsfm-blue?style=flat-square&logo=github)](https://github.com/dbccccccc/ttsfm)
[![PyPI](https://img.shields.io/badge/PyPI-ttsfm-blue?style=flat-square&logo=pypi)](https://pypi.org/project/ttsfm/)
[![Docker](https://img.shields.io/badge/Docker-dbcccc/ttsfm-blue?style=flat-square&logo=docker)](https://hub.docker.com/r/dbcccc/ttsfm)

---

## 📖 文档

- 🇺🇸 **English**: [README.md](README.md)
- 🇨🇳 **中文**: [README.zh.md](README.zh.md)

由[@dbcccc](https://github.com/dbccccccc)用❤️制作

</div>
