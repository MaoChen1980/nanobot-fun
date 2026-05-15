# 🐈 nanobot

<div align="center">

![Python](https://img.shields.io/badge/python-≥3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**轻量 · 可读 · 可扩展的 AI 代理框架**

🌏 [English README](./README_en.md)

</div>

---

## 致谢

本项目基于 [HKUDS/nanobot](https://github.com/HKUDS/nanobot) 构建，向原项目及维护者致敬。

---

## 快速上手

### 前置条件

- **手机** — 注册 Bot 时需要扫码，请确保已安装并登录 **飞书** 或 **钉钉**
- **Git** — 克隆代码仓库

### 1. 安装 Python

如果电脑还没有 Python，按系统选择：

**Windows**：从 [python.org](https://www.python.org/downloads/) 下载 Python 3.11+ 安装包，安装时**勾选"Add Python to PATH"**。

安装完成后打开命令提示符（按 `Win + R` → 输入 `cmd` → 回车），验证：

```bash
python --version
```

**macOS**：打开终端（`Cmd + 空格` → 搜索"终端" → 回车），然后：

```bash
# Homebrew 安装
brew install python@3.12

# 或者使用官方安装包
# https://www.python.org/downloads/
python3 --version
```

**Linux (Debian/Ubuntu)**：打开终端（按 `Ctrl + Alt + T`），然后：

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 --version
```

### 2. 安装 nanobot

```bash
git clone https://github.com/MaoChen1980/nanobot-mg.git
cd nanobot-mg
pip install -e .
```

> **Windows 用户须知**：如果提示权限错误，请以管理员身份运行命令提示符（右键 → 以管理员身份运行）。建议在虚拟环境中安装（`python -m venv venv` → `venv\Scripts\activate` → `pip install -e .`）。

完成后终端里就有了 `nanobot` 命令。

### 3. 初始化

```bash
nanobot onboard
```

创建 `~/.nanobot/config.json` 和默认工作区。（`~` 即用户主目录：Windows 上为 `C:\Users\你的用户名`，macOS/Linux 上为 `/home/你的用户名`）

### 4. 配置模型

先启动网关，打开 WebUI 填入 API Key（初次启动只用来配置，稍后关掉再正式运行）：

```bash
nanobot gateway
# 浏览器打开 http://localhost:18790/
```

在 WebUI 中设置模型提供商（OpenAI、Anthropic、DeepSeek 等）和 API Key。配置完成后按 `Ctrl+C` 关闭网关——等 Bot 接入完毕再正式启动。

### 5. 接入聊天平台

nanobot 支持扫码自动创建 Bot（飞书/钉钉）和手动配置（其他平台）。

#### 飞书

**前提：手机已安装并登录飞书 App**

**方式一：扫码自动创建（推荐）**

```bash
nanobot onboard feishu
```

1. 终端显示二维码，用飞书扫码确认
2. 自动完成：创建应用 → 启用 Bot → 写入配置
3. 之后在 [飞书开发者控制台](https://open.feishu.cn/app) 添加权限并发布（终端有指引）

**方式二：手动配置**

如果已有名为「凭证与基础信息」的 App ID + App Secret：

```bash
nanobot channels
# 按提示选择 feishu，输入 App ID 和 App Secret
```

手动添加配置到 `~/.nanobot/config.json`：

```json
{
  "channels": {
    "feishu": {
      "enabled": true,
      "appId": "cli_xxx",
      "appSecret": "你的AppSecret",
      "allowFrom": ["*"],
      "streaming": true
    }
  }
}
```

> `allowFrom` 中 `*` 表示允许所有用户。上线后改为你的 `open_id`（在 nanobot 日志中找到）。

#### 钉钉

**前提：手机已安装并登录钉钉 App**

**方式一：扫码自动创建（推荐）**

```bash
nanobot onboard dingtalk
```

1. 终端显示二维码，用钉钉扫码确认
2. 自动完成：创建应用 → 写入配置

**方式二：手动配置**

如果已有 App Key + App Secret：

```bash
nanobot channels
# 按提示选择 dingtalk，输入 App Key 和 App Secret
```

手动添加配置到 `~/.nanobot/config.json`：

```json
{
  "channels": {
    "dingtalk": {
      "enabled": true,
      "clientId": "YOUR_APP_KEY",
      "clientSecret": "YOUR_APP_SECRET",
      "allowFrom": ["*"]
    }
  }
}
```

#### Telegram / Discord / Slack 等

```bash
nanobot channels
```

按提示输入 Bot Token 等凭据。

#### 微信

```bash
pip install "nanobot-ai[weixin]"
nanobot channels login weixin   # 扫码登录
nanobot channels               # 配置 allowFrom
```

### 6. 启动网关

```bash
nanobot gateway
```

Bot 自动上线开始响应消息。WebUI 在 `http://localhost:18790/` 可查看状态。

### 7. CLI 对话（可选）

```bash
nanobot agent
```

单轮模式：

```bash
nanobot agent -m "你好"
```

---

## 工作原理

```
你的手机        聊天平台          nanobot               LLM
 ┌────┐        ┌────────┐      ┌──────────┐         ┌─────┐
 │飞书│   ←→   │ Feishu │  ←→  │  Proxy   │  ←→    │模型 │
 │钉钉│        │ DingTalk│      │  消息代理 │        │     │
 │微信│        │ WeChat │      └────┬─────┘         └─────┘
 └────┘        └────────┘           │                    │
                                    │ Agent Loop         │
                              ┌─────┴──────┐             │
                              │  工具调用   │  ←←←←←←←←←  │
                              │  exec/grep │             │
                              │  文件读写   │             │
                              │  Web 搜索   │             │
                              └────────────┘             │
```

**消息流：**

1. 你在飞书/钉钉发一条消息
2. 聊天平台通过 WebSocket 把消息推给 nanobot
3. AgentLoop 构建上下文（历史对话 + 记忆 + 工具说明）
4. LLM 推理，决定调用哪个工具
5. nanobot 执行工具（读文件、搜索、执行命令、Web 查询等）
6. 工具结果回传给 LLM，继续推理
7. 最终回复通过 nanobot → 聊天平台 → 你的手机

**并发模型：**
- 不同用户独立 Session，互不阻塞，可并行处理
- 同 Session 内消息按顺序串行

---

## CLI 命令

| 命令 | 作用 |
|------|------|
| `nanobot onboard` | 初始化配置和工作区 |
| `nanobot onboard feishu` | 扫码创建飞书 Bot |
| `nanobot onboard dingtalk` | 扫码创建钉钉 Bot |
| `nanobot gateway` | 启动网关（WebUI + Bot 连接） |
| `nanobot agent` | CLI 对话 |
| `nanobot status` | 查看配置和状态 |
| `nanobot channels` | 配置聊天渠道 |
| `nanobot plugins` | 管理插件 |
| `nanobot provider` | OAuth 提供商登录 |

---

## 会话模型

- 每个用户独立 Session（`channel:bot:sender_id`）
- Session 持久化在 SQLite，消息历史自动管理
- 不同用户互不阻塞，可并行处理
- 同 Session 内消息按顺序串行

---

## 内置工具

**文件与搜索：** `read_file` · `read_files` · `write_file` · `edit_file` · `delete_file` · `move_file` · `list_dir` · `glob` · `grep` · `explore_module` · `inspect_text` · `git_inspect`

**执行与计算：** `exec` · `analyze_tool` · `diagnose_tool`

**记忆与检索：** `recall` · `search_memory` · `search_text`

**目标与事件：** `write_goal` · `list_goals` · `write_event` · `list_events`

**通信与调度：** `message` · `ask_user` · `cron` · `spawn`

**会话管理：** `session_manage` · `tool_call_log`

**网络：** `web_search` · `web_fetch`

---

## 配置

`~/.nanobot/config.json`，通过 WebUI 可视化编辑或直接修改：

| 字段 | 说明 |
|------|------|
| `model` | 模型标识，如 `anthropic/claude-opus-4-5` |
| `provider` | 提供商（`auto`/`anthropic`/`openai`/`deepseek`） |
| `workspace` | 工作区路径，默认 `~/.nanobot/workspace` |
| `tools.exec` | 命令执行配置（超时、沙箱） |
| `tools.web` | Web 搜索/抓取配置 |

---

## 支持的消息渠道

Telegram · Discord · Slack · 飞书 · 微信 · QQ · 钉钉 · WhatsApp · Email · Matrix 等 16+ 后端。

---

## 常见问题

**Q: 启动 `nanobot gateway` 报错？**
- 确认 Python ≥ 3.11：`python --version`
- 确认配置文件存在：`~/.nanobot/config.json`
- 检查 API Key 是否在 WebUI 中正确配置

**Q: 飞书/钉钉收不到消息？**
- 确认应用已发布（在开发者后台发布新版本）
- 确认 `allowFrom` 包含你的 ID（或设为 `["*"]`）
- 查看 nanobot 日志中的 `open_id` / `staff_id`，填入 `allowFrom`

**Q: 微信扫码失败？**
- 确认已安装：`pip install "nanobot-ai[weixin]"`
- 尝试强制重新登录：`nanobot channels login weixin --force`
- 确认手机微信已登录同一账号

**Q: 想用其他 LLM 模型？**
```bash
nanobot gateway
# 浏览器打开 http://localhost:18790/  配置
```
支持 OpenAI、Anthropic、DeepSeek、OpenRouter、Google Gemini、Kimi、Qwen、Ollama 等。

---

## 开发

### 目录结构

```
nanobot/
├── agent/              # 核心代理引擎
│   ├── loop.py         # 主循环入口
│   ├── runner.py       # 执行引擎
│   ├── context.py      # Prompt 构建
│   ├── tools/          # 30+ 工具实现
│   └── memory*.py      # 记忆系统
├── providers/          # LLM 提供商
├── proxy/              # 消息渠道代理
├── onboard/            # Bot 扫码注册
├── session/            # 会话管理
├── skills/             # 内置 skills
├── config/             # 配置 schema
└── utils/              # 工具函数
```

### 添加自定义工具

```python
from nanobot.agent.tools.base import Tool

class MyTool(Tool):
    name = "my_tool"
    description = "做什么的"
    read_only = False

    async def execute(self, param1: str) -> str:
        return f"Result: {param1}"
```

在 `loop.py` 的 `_register_default_tools()` 中注册即可。

---

## 文档

完整文档请访问 [nanobot.wiki](https://nanobot.wiki/docs/latest/getting-started/nanobot-overview)。

---

<div align="center">

由 [Xubin Ren](https://github.com/re-bin) 发起，社区贡献者共同维护。

</div>
