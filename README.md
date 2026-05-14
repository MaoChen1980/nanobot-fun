# 🐈 nanobot

**轻量 · 可读 · 可扩展的 AI 代理框架**

- Python ≥3.11
- [文档](https://nanobot.wiki/docs/latest/getting-started/nanobot-overview) | [English](./README_en.md)

Forked from [HKUDS/nanobot](https://github.com/HKUDS/nanobot) — 向原项目及维护者 [Xubin Ren](https://github.com/re-bin) 致敬。

---

## 快速开始

```bash
# 1. 安装
pip install -e .

# 2. 初始化
nanobot onboard

# 3. 配置（浏览器打开 WebUI）
nanobot gateway

# 4. 开始对话
nanobot agent
```

单轮模式：`nanobot agent -m "你的问题"`

支持 20+ 模型提供商：OpenAI、Anthropic、DeepSeek、OpenRouter、Google Gemini、Azure、Kimi、Qwen、Ollama、vLLM 等。

---

## 核心能力

| 能力 | 说明 |
|------|------|
| **Agent Loop** | 推理-执行循环，支持断点恢复、中间接续、并发工具 |
| **上下文构建** | Bootstrap / Memory / Skills / Goals 分段注入，支持向量搜索 |
| **记忆系统** | MEMORY.md 长期记忆 + FAISS 向量搜索 + Dream 自动提取 |
| **目标追踪** | SQLite 存储 Goals/Events，支持子任务和 scope 过滤 |
| **文件操作** | 读写编辑 grep glob，支持 docx/xlsx/pdf |
| **命令执行** | Shell，超时控制，沙箱隔离，危险命令拦截 |
| **MCP 协议** | 支持 stdio / SSE / Streamable HTTP |
| **定时任务** | Cron 语法，test 模式可调试 |
| **渠道集成** | Telegram / Discord / 飞书 / 微信 / QQ / 钉钉 等 |
| **Skills** | 可插拔技能系统 |

---

## 内置工具

**文件与搜索**：read_file / write_file / edit_file / grep / glob / explore_module / inspect_text / git_inspect

**执行与计算**：exec / diagnose

**记忆与检索**：recall / search_memory / search_text

**目标与事件**：write_goal / list_goals / write_event / list_events

**通信与调度**：message / ask_user / cron / spawn

**会话管理**：session_manage / tool_call_log

**网络**：web_search / web_fetch

---

## 架构

```
AgentLoop → ContextBuilder → LLM → ToolRegistry
                ↓
         SessionManager（持久化）
                ↓
         Memory System（MEMORY.md + FAISS + Dream）
                ↓
         Channels（Telegram / 飞书 / Discord 等）
```

**设计原则**：LLM 每次请求构建完整 prompt，框架保持状态持久化。

---

## 配置

配置文件：`~/.nanobot/config.json`

核心字段：`model`（模型标识）、`provider`（提供商）、`workspace`（工作区）、`tools.*`（工具配置）、`channels`（渠道）

详细配置：[nanobot.wiki](https://nanobot.wiki/)

---

## 开发

**目录结构**

```
nanobot/
├── agent/           # 核心引擎（loop / runner / context）
├── tools/           # 工具实现（30+ 个）
├── providers/       # LLM 提供商
├── proxy/           # 渠道代理
├── skills/          # 内置 skills
└── web/             # Web 服务
```

**添加自定义工具**

```python
from nanobot.agent.tools.base import Tool

class MyTool(Tool):
    name = "my_tool"
    description = "做什么的"
    read_only = False

    async def execute(self, param1: str) -> str:
        return f"Result: {param1}"
```

在 `loop.py` 的 `_register_default_tools()` 中注册。

---

## CLI 命令

| 命令 | 作用 |
|------|------|
| `nanobot onboard` | 初始化配置和工作区 |
| `nanobot gateway` | 启动 WebUI + 渠道网关 + 定时任务 |
| `nanobot agent` | 启动交互式对话 |
| `nanobot status` | 查看配置和状态 |
| `nanobot channels` | 配置聊天渠道 |

---

## 文档

https://nanobot.wiki