# TTSFM

[![Docker Pulls](https://img.shields.io/docker/pulls/dbcccc/ttsfm?style=flat-square&logo=docker)](https://hub.docker.com/r/dbcccc/ttsfm)
[![License](https://img.shields.io/github/license/dbccccccc/ttsfm?style=flat-square)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/dbccccccc/ttsfm?style=social)](https://github.com/dbccccccc/ttsfm)

> ⚠️ **免责声明**  
> 此项目仅用于学习测试，生产环境请使用 [OpenAI 官方 TTS 服务](https://platform.openai.com/docs/guides/audio)。

[English](README.md) | 中文文档

## 🌟 项目简介

TTSFM 是一个逆向工程实现的 API 服务器，完全兼容 OpenAI 的文本转语音(TTS)接口。

> 🎮 立即体验：[官方演示站](https://ttsapi.fm) 


## 🏗️ 项目结构

```text
ttsfm/
├── main.py              # 应用入口
├── server/              # 服务核心
│   ├── api.py           # OpenAI 兼容API
│   └── handlers.py      # 请求处理器
├── proxy/               # 代理系统
│   └── manager.py
├── utils/               # 工具模块
│   └── config.py
├── static/              # 前端资源
│   ├── index.html       # 英文界面
│   ├── index_zh.html    # 中文界面
│   └── ...              # JS/CSS 资源
└── requirements.txt     # Python依赖
```

## 🚀 快速开始

### 系统要求
- Python ≥ 3.8
- 或 Docker 环境

### 🐳 Docker 运行（推荐）
```bash
docker run -p 7000:7000 dbcccc/ttsfm:latest
```

> 💡 **提示**  
> MacOS 用户若遇到端口冲突，可替换端口号：  
> `docker run -p 5051:7000 dbcccc/ttsfm:latest`

以下是精简后的手动安装部分，仅保留发行版下载方式：

### 📦 手动安装

1. 从 [GitHub Releases](https://github.com/dbccccccc/ttsfm/releases) 下载最新版本压缩包
2. 解压并进入目录：
```bash
tar -zxvf ttsfm-vX.X.X.tar.gz
cd ttsfm-vX.X.X
```
3. 安装依赖并启动：
```bash
pip install -r requirements.txt
cp .env.example .env  # 按需编辑配置
python main.py
```

## 📚 使用指南

### Web 界面
访问 `http://localhost:7000` 体验交互式演示

### API 端点
| 端点 | 方法 | 描述 |
|------|------|-------------|
| `/v1/audio/speech` | POST | 文本转语音 |
| `/api/queue-size` | GET | 查询任务队列 |

> 🔍 完整 API 文档可在本地部署后通过 Web 界面查看

### 🧪 压力测试
```bash
# 基础测试
python pressure_test.py

# 自定义测试示例
python pressure_test.py -n 50 -c 10 -t long -s
```

**参数说明**：
- `-n` 总请求数
- `-c` 并发数
- `-t` 文本长度 (short/medium/long)  
- `-s` 保存生成音频

## 🤝 参与贡献

我们欢迎所有形式的贡献！您可以通过以下方式参与：

- 提交 [Issue](https://github.com/dbccccccc/ttsfm/issues) 报告问题
- 发起 [Pull Request](https://github.com/dbccccccc/ttsfm/pulls) 改进代码
- 分享使用体验和建议

📜 项目采用 [MIT 许可证](LICENSE)

## 📈 项目动态

[![Star History Chart](https://api.star-history.com/svg?repos=dbccccccc/ttsfm&type=Date)](https://star-history.com/#dbccccccc/ttsfm&Date)