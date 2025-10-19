# TTSFM - 文本转语音 API 客户端

> **Language / 语言**: [English](README.md) | [中文](README.zh.md)

[![Docker Pulls](https://img.shields.io/docker/pulls/dbcccc/ttsfm?style=flat-square&logo=docker)](https://hub.docker.com/r/dbcccc/ttsfm)
[![GitHub Stars](https://img.shields.io/github/stars/dbccccccc/ttsfm?style=social)](https://github.com/dbccccccc/ttsfm)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
![ghcr pulls](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fghcr-badge.elias.eu.org%2Fapi%2Fdbccccccc%2Fttsfm%2Fttsfm&query=downloadCount&label=ghcr+pulls&logo=github)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=dbccccccc/ttsfm&type=Date)](https://www.star-history.com/#dbccccccc/ttsfm&Date)

## 概述

TTSFM 是一个免费的 OpenAI 兼容文本转语音解决方案，基于 openai.fm 后端，同时提供 Python 客户端、REST API 与网页端 Playground。

## 安装

### Python 包

```bash
pip install ttsfm        # 核心客户端
pip install ttsfm[web]   # 客户端 + Flask Web 应用
```

### Docker 镜像

```bash
docker run -p 8000:8000 dbcccc/ttsfm:latest
```

容器默认开放网页 Playground（`http://localhost:8000`）以及兼容 OpenAI 的 `/v1/audio/speech` 接口。

## 快速开始

### Python 客户端

```python
from ttsfm import TTSClient, AudioFormat, Voice

client = TTSClient()
response = client.generate_speech(
    text="来自 TTSFM 的问候！",
    voice=Voice.ALLOY,
    response_format=AudioFormat.MP3,
)
response.save_to_file("hello")  # -> hello.mp3
```

### 命令行

```bash
ttsfm "你好，世界" --voice nova --format mp3 --output hello.mp3
```

### REST API

```bash
curl -X POST http://localhost:8000/v1/audio/speech   -H "Content-Type: application/json"   -d '{"model":"gpt-4o-mini-tts","input":"你好，世界","voice":"alloy"}'   --output speech.mp3
```

## 了解更多

- 在 [Web 文档](http://localhost:8000/docs)（或 `ttsfm-web/templates/docs.html`）查看完整接口说明与运行注意事项。
- 查看 [架构概览](docs/architecture.md) 了解组件间的关系。
- 欢迎参与贡献，流程说明请见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

TTSFM 采用 [MIT 许可证](LICENSE) 发布。
