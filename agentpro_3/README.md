# 🎫 智能演出购票助手 (Agent Harness)

> 基于 **Agent Harness (ETCSLV)** 六元治理模型的智能票务平台 | Python + FastAPI + DeepSeek

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-teal)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.3+-green)](https://langchain.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📋 项目概述

一个面向 C 端用户的**智能演出票务平台**，覆盖「搜索 → 选座 → 锁座 → 下单 → 支付 → 退票」全流程。核心创新在于自研了一套 **Agent Harness 执行引擎**替代 LangChain 的 `AgentExecutor`，用 **ETCSLV 六元治理模型**解决 AI Agent 在生产环境中的**稳定性、可观测性、韧性**三大核心问题。

| 演示地址 | API 文档 | 前端界面 |
|----------|----------|----------|
| `http://localhost:8000` | `http://localhost:8000/docs` | 暗色主题 SPA |

---

## 🧠 解决了什么问题

### 原生 LangChain Agent 的痛点

| 痛点 | 表现 | Harness 方案 |
|------|------|-------------|
| **死循环/卡死** | LLM 反复调用同一工具不退出 | **V: 中途停检** — 3 次连续失败自动终止 |
| **上下文爆炸** | 多轮对话 token 超限 | **C: 窗口压缩** — 自动摘要+截断策略 |
| **崩溃无恢复** | 进程重启后状态丢失 | **S: 状态快照** — JSON 持久化+断点续跑 |
| **黑盒执行** | 无法观测每步做了什么 | **L: 审计钩子** — 6 阶段 HookStage 全记录 |
| **工具调用混乱** | 参数格式错误导致 400 | **T: Schema 校验** — JSON Schema 约束工具参数 |
| **目标模糊** | 不知道任务是否完成 | **V: 目标验证** — `evaluate_success()` 独立判定 |

### 技术挑战与解决

| 挑战 | 解决方案 |
|------|----------|
| DeepSeek API 对 tool message 顺序敏感 | 修复 assistant→tool 消息排序 |
| LangChain `tool_calls.arguments` 单引号序列化 | 改用 `json.dumps()` 确保合法 JSON |
| 多轮对话记忆跨请求丢失 | 会话级 context 缓存 + 历史注入 prompt |
| LLM 拒绝对话式执行购票操作 | 强化 system prompt 操作员角色设定 |

---

## 🏗 技术架构

```
┌─────────────────────────────────────────────────┐
│              🖥  Frontend (SPA)                   │
│     HTML5 + CSS3 + Vanilla JS (零依赖)            │
│     暗色主题 · 卡片网格 · 响应式 · 三面板          │
└──────────────────────┬──────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────┐
│           ⚡ FastAPI + Uvicorn                    │
│     /chat  /agent/run  /shows/*  /orders/*       │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│         🔧 Agent Harness 内核 (ETCSLV)           │
│                                                  │
│  E ─ NanoEngine        Think→Act→Observe 循环    │
│  T ─ DictToolRegistry  工具注册 + Schema 校验     │
│  C ─ ContextManager    窗口管理 + 自动压缩        │
│  S ─ JsonStateStore    快照持久化 + 崩溃恢复      │
│  L ─ HookManager       6 阶段审计钩子             │
│  V ─ TicketingEvaluator 中途停检 + 目标验证       │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│         🛠 业务工具 (10 Tools)                    │
│  search_shows · check_seats · lock_seats         │
│  create_order · pay_order · query_order · refund │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│     🎭 业务 Agent · 🤖 LLM · 💾 Data             │
│  ShowSearcher · TicketAgent · CustomerService    │
│  Orchestrator · DeepSeek · 50+ 演出 · 6 场馆     │
└─────────────────────────────────────────────────┘
```

### ETCSLV 六元模型详解

| 组件 | 实现 | 关键能力 |
|------|------|----------|
| **E**xecution | `NanoEngine` | ReAct 循环、`max_steps` 限制、异常捕获与恢复 |
| **T**ools | `DictToolRegistry` | `@tool` 装饰器注册、JSON Schema 推断、`merge()` 合并 |
| **C**ontext | `SimpleContextManager` | 消息去重、token 估算、超限自动 compact |
| **S**tate | `JsonStateStore` | 每步 checkpoint 写入、崩溃后 `load_state()` 恢复 |
| **L**ifecycle | `SimpleHookManager` | `ON_TASK_START/BEFORE_ACTION/AFTER_ACTION/TASK_END` |
| **V**erification | `TicketingEvaluator` | 死循环检测、连续失败检测、支付成功判定 |

---

## 📊 项目指标

| 指标 | 数值 |
|------|------|
| 预置演出 | **50+** 场 (7 种类型) |
| 覆盖城市 | **6** 个 (北京/上海/广州/深圳/成都/杭州) |
| 业务工具 | **10** 个 (搜索/座位/订单/支付/退票) |
| API 端点 | **12** 个 |
| 测试覆盖 | 端到端多轮购票 ✅ |
| 前端依赖 | **0** (纯 HTML/CSS/JS) |

---

## 🚀 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY

# 3. 启动
python main.py

# 4. 访问
# 前端: http://localhost:8000
# API文档: http://localhost:8000/docs
```

---

## 📁 项目结构

```
agentpro_3/
├── harness/                    # ⭐ Agent Harness 内核
│   ├── schema.py               #   ToolCall, StepResult, EngineResult
│   ├── base.py                 #   ETCSLV 六组件抽象接口
│   ├── engine.py               #   NanoEngine 执行引擎
│   ├── prompt.py               #   PromptManager 模板管理
│   └── components/
│       ├── tools.py            #   T: DictToolRegistry
│       ├── context.py          #   C: SimpleContextManager
│       ├── state.py            #   S: JsonStateStore
│       ├── hooks.py            #   L: SimpleHookManager
│       └── evaluator.py        #   V: TicketingEvaluator
├── agents/                     # 业务 Agent
│   ├── base.py                 #   HarnessAgent 基类
│   ├── show_searcher.py        #   演出搜索
│   ├── ticket_agent.py         #   购票执行
│   ├── customer_service.py     #   售后客服
│   └── orchestrator.py         #   智能编排
├── tools/                      # 10 个业务工具
├── data/                       # 50+ 演出 / 6 场馆 / 订单存储
├── routers/                    # FastAPI 路由
├── core/                       # LLM 适配器 / 数据库
├── models/                     # Pydantic / SQLAlchemy
├── workflows/                  # LangGraph 工作流
├── static/                     # 前端 SPA
└── main.py                     # 入口
```

---

## 🔧 技术栈

| 层级 | 技术 |
|------|------|
| **Web 框架** | FastAPI + Uvicorn |
| **LLM** | DeepSeek (Chat API, OpenAI 兼容) |
| **Agent 框架** | 自研 Agent Harness (ETCSLV) + LangChain 适配 |
| **工具定义** | JSON Schema + `@tool` 装饰器 |
| **状态持久化** | JSON 文件 + SQLAlchemy + SQLite |
| **前端** | HTML5 + CSS3 + Vanilla JS (零框架) |
| **工作流** | LangGraph (意图路由) |

---

## 📝 简历项目描述

**智能演出购票助手** | 全栈开发 | 2026.06

- 设计并实现了基于 **Agent Harness (ETCSLV)** 六元治理模型的 AI Agent 执行引擎，替代 LangChain `AgentExecutor`，解决死循环检测、上下文爆炸、状态丢失、黑盒执行等生产级 Agent 稳定性问题
- 搭建完整票务业务闭环：搜索 → 选座 → 锁座 → 下单 → 支付 → 退票，覆盖 50+ 场演出、6 城市、10 个业务工具
- 实现 **NanoEngine** 执行循环，支持 Think→Act→Observe 多步推理、异常恢复、中途停检 (`should_stop`) 与独立目标验证 (`evaluate_success`)
- 构建 **DictToolRegistry** 工具注册表，支持 JSON Schema 参数校验、`@tool` 装饰器自动注册、多注册表 `merge()` 组合
- 修复 DeepSeek API 兼容性问题：tool message 消息排序、`arguments` JSON 序列化格式、多轮上下文截断
- 独立完成前后端：FastAPI 12 端点 + 暗色主题 SPA 前端 (零 JS 框架依赖)
