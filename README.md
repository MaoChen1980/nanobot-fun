# 🐈 nanobot

<div align="center">
  <p>
    <strong>轻量 · 可读 · 可扩展的 AI 代理框架</strong>
  </p>
  <p>
    <img src="https://img.shields.io/badge/python-≥3.11-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <a href="https://nanobot.wiki/docs/latest/getting-started/nanobot-overview"><img src="https://img.shields.io/badge/Docs-nanobot.wiki-blue" alt="Docs"></a>
  </p>
  <p>
    🌏 <a href="./README_en.md">English README</a>
  </p>
</div>

<p align="center">
  Forked from <a href="https://github.com/HKUDS/nanobot">HKUDS/nanobot</a> — 向原项目及维护者 <a href="https://github.com/re-bin">Xubin Ren</a> 致敬。
</p>

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

支持 20+ 模型提供商：OpenAI、Anthropic、DeepSeek、OpenRouter、Google Gemini、Azure、Kimi、Qwen、Ollama、vLLM、MiniMax、StepFun、GitHub Copilot 等。配置格式为 `提供商/模型名`。

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

## 架构概览

```
┌─────────────────────────────────────────────────────┐
│                    Agent Loop                       │
│         (nanobot/agent/loop.py — 1078 行)           │
│                                                     │
│  接收消息 → 构建 Prompt → LLM 推理 → 执行工具 → 响应│
└──────────┬───────────────────────┬──────────────────┘
           │                       │
           ▼                       ▼
┌──────────────────┐    ┌───────────────────────────┐
│  ContextBuilder  │    │      ToolRegistry         │
│  (上下文构建)     │    │  (30+ 内置工具 + MCP)      │
│                  │    │                           │
│  - Bootstrap    │    │  - 文件: read/write/edit  │
│  - Memory       │    │  - 搜索: grep/glob/search │
│  - Skills       │    │  - 执行: exec/shell       │
│  - Goals/Events  │    │  - 消息: message/cron     │
│  - History      │    │  - 记忆: recall/vector    │
│  - Tools        │    │  - 子代理: spawn          │
└──────────────────┘    └───────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│                  Session Manager                    │
│         (状态持久化 · 断点恢复 · 历史截断)            │
└─────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│                  Memory System                       │
│                                                     │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │  MEMORY.md   │  │ FAISS 向量  │  │ Goals/     │ │
│  │  (长期记忆)   │  │ 索引搜索    │  │ Events DB  │ │
│  └──────────────┘  └─────────────┘  └────────────┘ │
│                                                     │
│  Dream: 自动从对话历史中提取长期记忆                │
│  Consolidator: 定期压缩历史会话为摘要               │
└─────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│                  Channels (Proxy)                   │
│                                                     │
│  Telegram · Discord · Slack · 飞书 · 微信 ·         │
│  QQ · 钉钉 · WhatsApp · Email · Matrix · ...        │
└─────────────────────────────────────────────────────┘
```

**核心设计原则**：LLM 每次请求构建完整 prompt，框架保持状态持久化。工具执行结果自动保存、断点可恢复、用户消息可在推理过程中注入。

---

## 功能一览

| 功能 | 说明 |
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

## 内置工具

nanobot 内置 30+ 工具，分为以下类别：

### 文件与搜索

| 工具 | 作用 |
|------|------|
| `read_file` | 读取文件，支持行范围和正则过滤 |
| `read_files` | 批量读取多个文件（glob 模式） |
| `write_file` | 创建或覆写文件 |
| `edit_file` | 文本匹配修改文件 |
| `delete_file` | 删除单个文件 |
| `move_file` | 移动或重命名文件 |
| `list_dir` | 列出目录内容，支持递归 |
| `glob` | 按模式搜索文件 |
| `grep` | 正则搜索文件内容 |
| `explore_module` | 获取代码结构概览（类和函数定义） |
| `inspect_text` | 预览文档结构 |
| `git_inspect` | 查看 git 历史 |

### 执行与计算

| 工具 | 作用 |
|------|------|
| `exec` | 执行 Shell 命令，支持超时、沙箱、输出捕获 |
| `analyze_tool` | Python/JS AST 分析（导入/导出/调用者） |
| `diagnose_tool` | 结合代码搜索和 git 历史调查错误根因 |

### 记忆与检索

| 工具 | 作用 |
|------|------|
| `recall` | 搜索历史会话记录 + MEMORY.md |
| `search_memory` | 在 memory/ 目录做语义搜索 |
| `search_text` | 在给定文本/文件内做语义搜索 |

### 目标与事件

| 工具 | 作用 |
|------|------|
| `write_goal` | 创建或更新目标（跨会话跟踪） |
| `list_goals` | 查询目标，支持 status/project/scope 过滤 |
| `write_event` | 记录里程碑、决策、阻塞事件 |
| `list_events` | 查询事件历史 |

### 通信与调度

| 工具 | 作用 |
|------|------|
| `message` | 向用户发送消息和文件附件 |
| `ask_user` | 阻塞式提问，暂停执行等待用户回答 |
| `cron` | 安排定时/周期性任务，支持 test 调试 |
| `spawn` | 派生子代理后台执行独立任务 |

### 会话管理

| 工具 | 作用 |
|------|------|
| `session_manage` | 管理会话消息，压缩或排除历史 |
| `tool_call_log` | 查询工具调用记录（调试/审计） |

### 网络

| 工具 | 作用 |
|------|------|
| `web_search` | 网络搜索 |
| `web_fetch` | 获取 URL 内容并提取可读文本 |

---

## Skills 系统

Skills 是可插拔的能力扩展。内置 skills 位于 `nanobot/nanobot/skills/`，用户自定义 skills 放在 `~/.nanobot/workspace/skills/`。

常用内置 skills：

| Skill | 作用 |
|-------|------|
| `github` | 与 GitHub 交互（issues、PRs、CI runs） |
| `cron` | 定时任务调度 |
| `weather` | 获取天气信息（无需 API key） |
| `memory` | 双层记忆系统管理 |
| `my` | 查看和修改运行时状态 |

---

## 配置要点

配置文件位于 `~/.nanobot/config.json`，核心字段：

| 字段 | 说明 |
|------|------|
| `model` | 模型标识，如 `anthropic/claude-opus-4-5` |
| `provider` | 提供商（`auto`/`anthropic`/`openai`/`deepseek` 等） |
| `workspace` | 工作区路径，默认 `~/.nanobot/workspace` |
| `tools.exec` | 命令执行配置（超时、沙箱、允许的命令） |
| `tools.web` | Web 搜索/抓取配置 |
| `tools.my` | 运行时状态修改权限 |
| `channels` | 渠道配置（Telegram / 飞书 / Discord 等） |

详细配置参考 [nanobot.wiki](https://nanobot.wiki/)。

---

## 渠道配置

nanobot 支持 16+ 聊天后端共享一个代理实例。渠道通过 `~/.nanobot/config.json` 配置，每种渠道的配置项各不相同，具体参考[文档](https://nanobot.wiki/)。

---

## 开发指南

### 目录结构

```
nanobot/
├── agent/              # 核心代理引擎
│   ├── loop.py         # AgentLoop — 主循环入口
│   ├── runner.py       # AgentRunner — 执行引擎
│   ├── context.py      # ContextBuilder — Prompt 构建
│   ├── tools/          # 工具实现（30+ 个工具）
│   ├── memory*.py      # 记忆系统（向量索引、Dream、 Consolidator）
│   ├── skills.py       # Skills 加载器
│   └── subagent*.py    # 子代理管理
├── bridge/             # 前端（TypeScript + React）
├── config/             # 配置 schema
├── providers/          # LLM 提供商（OpenAI / Anthropic / DeepSeek 等）
├── proxy/              # 消息渠道代理（Telegram / 飞书 / Discord 等）
├── session/            # 会话管理
├── skills/             # 内置 skills
├── templates/          # Prompt 模板
├── utils/              # 工具函数
└── web/                # Web 服务
```

### 添加自定义工具

```python
# nanobot/agent/tools/my_tool.py
from nanobot.agent.tools.base import Tool

class MyTool(Tool):
    name = "my_tool"
    description = "做什么的"
    read_only = False  # True = 结果可缓存

    async def execute(self, param1: str) -> str:
        return f"Result: {param1}"
```

在 `loop.py` 的 `_register_default_tools()` 中注册即可。

### 自定义 Hook

```python
# workspace/hooks/my_hook.py
from nanobot.agent.hook import AgentHook, AgentHookContext

class MyHook(AgentHook):
    async def before_iteration(self, ctx: AgentHookContext) -> None:
        pass  # 在每次 LLM 调用前执行
```

---

## 文档

完整文档请访问 [nanobot.wiki](https://nanobot.wiki/docs/latest/getting-started/nanobot-overview)。

---

<p align="center">
  由 <a href="https://github.com/re-bin">Xubin Ren</a> 发起，社区贡献者共同维护。
</p>

<div align="center">
  <img src="https://visitor-badge.laobi.icu/badge?page_id=HKUDS.nanobot&style=for-the-badge&color=00d4ff" alt="visitors">
</div>