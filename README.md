# 🐈 nanobot

<div align="center">

![Python](https://img.shields.io/badge/python-≥3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Stars](https://img.shields.io/github/stars/HKUDS/nanobot?style=flat-square)
[![Documentation](https://img.shields.io/badge/Docs-nanobot.wiki-blue)](https://nanobot.wiki/docs/latest/getting-started/nanobot-overview)

**轻量 · 可读 · 可扩展的 AI 代理框架**

🌏 [English README](./README_en.md)

</div>

---

## 致谢

本项目基于 [HKUDS/nanobot](https://github.com/HKUDS/nanobot) 构建，向原项目及维护者 [Xubin Ren](https://github.com/re-bin) 致敬。

---

## 特性

| 分类 | 功能 |
|------|------|
| **Agent Loop** | 通用推理-执行循环，支持检查点恢复、中断续传、并发工具调用 |
| **上下文构建** | Bootstrap 文件、Memory、Skills、Goals/Events 分段注入，支持向量搜索 |
| **记忆系统** | MEMORY.md 长期记忆 + FAISS 向量索引语义搜索 + Dream 自动记忆提取 |
| **目标追踪** | SQLite 存储 Goals/Events，支持子任务、scope 过滤、阻塞标记 |
| **文件操作** | 读写编辑文件、grep/glob 搜索，支持 docx/xlsx/pptx/pdf |
| **命令执行** | Shell 命令执行，超时控制，沙箱隔离，危险命令自动拦截 |
| **Web 搜索** | DuckDuckGo、Kagi、Tavily、SearXNG、Jina 等后端，含页面内容提取 |
| **MCP 协议** | 支持 Model Context Protocol（stdio / SSE / Streamable HTTP） |
| **子代理** | 派生子代理并行执行独立任务，隔离会话 |
| **定时任务** | Cron 语法，支持一次性/周期性任务，test 模式可调试 |
| **聊天渠道** | Telegram、Discord、Slack、飞书、微信、QQ、钉钉、WhatsApp、Email、Matrix 等 |
| **Skills** | 可插拔技能系统，支持 always/conditional 技能加载 |
| **WebUI** | 浏览器配置页面，管理模型、工具、渠道 |
| **Hooks** | 自定义生命周期钩子，灵活扩展框架行为 |

---

## 安装

```bash
git clone <your-repo-url>
cd nanobot
pip install -e .
```

## 快速开始

**1. 初始化配置和工作区**

```bash
nanobot onboard
```

创建 `~/.nanobot/config.json` 和默认工作区。

**2. 配置 API Key 和模型**

启动 WebUI 配置：

```bash
nanobot gateway
# 浏览器打开 http://localhost:18790/
```

支持 20+ 模型提供商：OpenAI、Anthropic、DeepSeek、OpenRouter、Google Gemini、Azure、Kimi、Qwen、Ollama、vLLM、MiniMax、StepFun、GitHub Copilot 等。

**3. 开始对话**

```bash
nanobot agent
```

单轮模式：

```bash
nanobot agent -m "你的问题"
```

---

## CLI 命令

| 命令 | 作用 |
|------|------|
| `nanobot onboard` | 初始化配置和工作区 |
| `nanobot gateway` | 启动 WebUI + 渠道网关 + 定时任务 |
| `nanobot agent` | 启动交互式 CLI 对话 |
| `nanobot status` | 查看配置和状态 |
| `nanobot channels` | 配置聊天渠道 |
| `nanobot plugins` | 管理插件 |
| `nanobot provider` | OAuth 提供商登录 |

---

## 内置工具

nanobot 内置 30+ 工具，分为以下类别：

### 文件与搜索

`read_file` · `read_files` · `write_file` · `edit_file` · `delete_file` · `move_file` · `list_dir` · `glob` · `grep` · `explore_module` · `inspect_text` · `git_inspect`

### 执行与计算

`exec` · `analyze_tool` · `diagnose_tool`

### 记忆与检索

`recall` · `search_memory` · `search_text`

### 目标与事件

`write_goal` · `list_goals` · `write_event` · `list_events`

### 通信与调度

`message` · `ask_user` · `cron` · `spawn`

### 会话管理

`session_manage` · `tool_call_log`

### 网络

`web_search` · `web_fetch`

---

## Skills 系统

Skills 是可插拔的能力扩展。内置 skills：

| Skill | 作用 |
|-------|------|
| `github` | 与 GitHub 交互（issues、PRs、CI runs） |
| `cron` | 定时任务调度 |
| `weather` | 获取天气信息（无需 API key） |
| `memory` | 双层记忆系统管理 |
| `my` | 查看和修改运行时状态 |

用户自定义 skills 放在 `~/.nanobot/workspace/skills/`。

---

## 配置

配置文件位于 `~/.nanobot/config.json`：

| 字段 | 说明 |
|------|------|
| `model` | 模型标识，如 `anthropic/claude-opus-4-5` |
| `provider` | 提供商（`auto`/`anthropic`/`openai`/`deepseek` 等） |
| `workspace` | 工作区路径，默认 `~/.nanobot/workspace` |
| `tools.exec` | 命令执行配置（超时、沙箱、允许的命令） |
| `tools.web` | Web 搜索/抓取配置 |

---

## 渠道

支持 16+ 聊天后端：Telegram · Discord · Slack · 飞书 · 微信 · QQ · 钉钉 · WhatsApp · Email · Matrix 等。

---

## 开发

### 目录结构

```
nanobot/
├── agent/              # 核心代理引擎
│   ├── loop.py         # 主循环入口
│   ├── runner.py       # 执行引擎
│   ├── context.py      # Prompt 构建
│   ├── tools/          # 工具实现（30+ 个）
│   ├── memory*.py      # 记忆系统
│   └── skills.py       # Skills 加载器
├── providers/          # LLM 提供商
├── proxy/              # 消息渠道代理
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

![Visitors](https://visitor-badge.laobi.icu/badge?page_id=HKUDS.nanobot&style=for-the-badge&color=00d4ff)

</div>