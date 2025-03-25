# TTSFM (文本转语音转发镜像)

[English](../README.md) | 中文

TTSFM 是一个逆向工程的 API 服务器，镜像了 OpenAI 的 TTS 服务，提供了兼容的文本转语音接口，支持多种语音选项。

### 系统要求
- Python 3.8 或更高版本
- pip（Python 包管理器）

### 安装步骤
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

### 许可证
本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。 