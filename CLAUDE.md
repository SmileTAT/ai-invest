# CLAUDE.md — ai-invest 工程指南

本文件为 Claude Code（及所有协作者）提供本仓库的项目背景、架构约定与工程规范。
项目当前处于 **0 → 1 阶段**：仓库刚初始化，尚无代码。产品定义见 `docs/PRD.md`。

## 项目是什么

**ai-invest** 是一个 AI 驱动的个人投资研究助手：聚合行情与财报数据，
用 LLM 做多智能体研究分析（基本面 / 技术面 / 情绪面 / 风控），
产出结构化的研究报告与组合建议，而**不是**自动交易系统。

核心原则：

1. **研究辅助，不代客交易** — 产品输出是"研究结论 + 依据"，不直接下单。所有输出必须附带免责声明与数据来源。
2. **可解释性优先** — 每个结论必须能追溯到数据源与推理链，禁止输出无依据的"黑盒"结论。
3. **数据与推理分离** — 数据采集层、分析引擎层、呈现层严格解耦，任何一层可独立替换。

## 推荐技术栈（未确定前的默认选择）

| 层 | 选型 | 理由 |
|---|---|---|
| 后端 | Python 3.12 + FastAPI | 金融数据生态（pandas/akshare/yfinance）最成熟 |
| LLM 编排 | Anthropic SDK（直接调用，`claude-sonnet-5` 为默认模型；重分析任务用更强模型） | 多智能体研究流水线；避免过早引入重框架 |
| 数据存储 | PostgreSQL + TimescaleDB 扩展 | 行情时序数据 + 关系数据一体化 |
| 缓存/队列 | Redis | 行情缓存、分析任务队列 |
| 前端 | Next.js + TypeScript + Tailwind | 报告呈现、图表（ECharts/lightweight-charts） |
| 部署 | Docker Compose（MVP）→ K8s（规模化后） | 先简单 |

> 若实际开发中选型变化，**必须同步更新本文件**。

## 目录结构约定（代码落地时遵循）

```
ai-invest/
├── CLAUDE.md
├── docs/
│   ├── PRD.md              # 产品需求文档（含变现路径）
│   └── adr/                # 架构决策记录，一事一文件
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI 路由，只做参数校验与编排
│   │   ├── datasources/    # 数据源适配器，每个数据源一个模块，统一接口
│   │   ├── agents/         # 分析智能体（fundamental / technical / sentiment / risk）
│   │   ├── pipeline/       # 研究流水线编排（智能体调度、结果聚合）
│   │   ├── models/         # SQLAlchemy 模型 + Pydantic schema
│   │   └── core/           # 配置、日志、LLM 客户端封装
│   └── tests/
├── frontend/
└── docker-compose.yml
```

## 工程规范

### 通用

- 所有金额/价格用 `Decimal`，禁止 `float` 参与货币计算。
- 所有时间统一存 UTC，展示层再做时区转换；行情数据必须带交易所时区元信息。
- 数据源适配器必须实现统一接口（`fetch_quote` / `fetch_fundamentals` / `fetch_news`），并声明数据延迟等级（实时/延迟15min/日更）。
- LLM 调用统一走 `core/llm.py` 封装：集中管理重试、超时、token 计量、成本记录。**禁止在业务代码中直接 import anthropic**。
- 每次 LLM 分析输出必须是结构化 JSON（用 tool_use 强制 schema），禁止解析自由文本。

### 合规红线（写代码前必读）

- 任何面向用户的分析输出，必须包含免责声明字段 `disclaimer`，前端强制展示。
- 禁止输出"保证收益""必涨"类表述——在 prompt 与输出后处理中双重过滤。
- 不接入任何实盘交易 API（券商下单接口）。回测与模拟盘可以。
- 用户数据（持仓、自选股）属敏感数据：不进日志、不进 LLM prompt 缓存日志、导出需脱敏。

### 测试与提交

- 后端：`pytest`，数据源适配器必须有基于录制夹具（fixture）的离线测试，CI 不打真实外部 API。
- 提交信息用英文祈使句（`Add fundamental agent pipeline`），一次提交一个逻辑变更。
- 主分支 `main` 受保护，所有变更走 PR。

## 常用命令（代码落地后补全实际命令）

```bash
# 预期形态，落地时更新为真实命令
docker compose up -d          # 启动 postgres/redis
cd backend && uvicorn app.main:app --reload
cd backend && pytest
cd frontend && npm run dev
```

## 关键文档

- 产品定义、路线图、变现路径：`docs/PRD.md`
- 架构决策：`docs/adr/`（重大技术选型变更必须先写 ADR）
