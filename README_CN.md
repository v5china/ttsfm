# TTSFM

[![Docker Image](https://img.shields.io/docker/pulls/dbcccc/ttsfm?style=flat-square)](https://hub.docker.com/r/dbcccc/ttsfm)
[![License](https://img.shields.io/github/license/dbccccccc/ttsfm?style=flat-square)](LICENSE)

> **免责声明**: 此项目仅用于学习测试，请使用 https://platform.openai.com/docs/guides/audio OpenAI的官方服务进行生产环境使用。

[English](../README.md) | 中文

TTSFM 是一个逆向工程的 API 服务器，镜像了 OpenAI 的 TTS 服务，提供了兼容的文本转语音接口，支持多种语音选项。

### 系统要求
- Python 3.8 或更高版本
- pip（Python 包管理器）
- 或 Docker

### 安装步骤

#### 选项一：使用 Docker（推荐）
```bash
docker pull dbcccc/ttsfm:latest
docker run -p 7000:7000 dbcccc/ttsfm:latest
```

#### 选项二：手动安装
1. 克隆仓库：
```bash
git clone https://github.com/yourusername/ttsfm.git
cd ttsfm
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

### 使用方法

#### 选项一：使用 Docker
1. 运行 docker 命令后服务器将自动启动
2. 访问网页界面：`http://localhost:7000`

#### 选项二：手动使用
1. 启动服务器：
```bash
python server.py
```

2. 访问网页界面：`http://localhost:7000`

3. 使用 API 接口

### API 接口
具体信息请至部署完成的网页查看。
- `POST /v1/audio/speech`：文本转语音
- `GET /v1/voices`：获取可用语音列表

### 压力测试
项目包含一个压力测试脚本，用于评估服务器在负载下的性能。使用方法：

```bash
# 基础测试（10个请求，2个并发连接）
python pressure_test.py

# 更多请求和更高并发测试
python pressure_test.py -n 50 -c 10

# 不同文本长度测试
python pressure_test.py -t short  # 短文本
python pressure_test.py -t medium # 中等文本（默认）
python pressure_test.py -t long   # 长文本

# 保存生成的音频文件
python pressure_test.py -s

# 自定义服务器地址
python pressure_test.py -u http://localhost:7000
```

选项说明：
- `-n, --num-requests`：发送的总请求数（默认：10）
- `-c, --concurrency`：并发连接数（默认：2）
- `-t, --text-length`：使用的文本长度（short/medium/long）
- `-s, --save-audio`：将生成的音频文件保存到 test_output 目录
- `-u, --url`：自定义服务器地址（默认：http://localhost:7000）

### 许可证
本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。 

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=dbccccccc/ttsfm&type=Date)](https://www.star-history.com/#dbccccccc/ttsfm&Date)