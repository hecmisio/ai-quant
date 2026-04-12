# AI量化-六边形架构约束

## 目标

本仓库在新增功能和重构时，默认遵循六边形架构：

- `domain/` 负责纯业务规则与转换逻辑
- `application/` 负责用例编排、命令对象、返回结果和端口定义
- `adapters/` 负责把外部世界接入端口，例如数据库、AkShare、文件系统、CLI
- `db/` 负责数据库基础设施细节，例如 ORM model、session、schema 对应关系

目标不是追求形式化分层，而是降低以下耦合：

- 业务规则直接耦合 SQLAlchemy 或 pandas I/O
- 脚本入口直接写业务逻辑
- 外部数据源口径变化直接污染应用层
- 数据库模型散落在服务代码里

## 目录约定

### Domain

放纯规则、纯转换、纯校验：

- `src/domain/market_data/a_share.py`
- `src/domain/market_data/kline.py`

约束：

- 不直接访问数据库
- 不直接读写文件
- 不直接请求 AkShare 或其他外部 API
- 尽量保持函数输入输出明确、可单元测试

### Application

放用例和端口：

- `src/application/ports/`
- `src/application/services/`

约束：

- 可以定义 `Protocol` 端口
- 可以编排 domain 逻辑
- 不直接依赖 ORM model 或第三方数据源 SDK
- 所有外部能力都通过 port 注入

### Adapters

放端口实现：

- `src/adapters/outbound/market_data/`
- `src/adapters/outbound/persistence/`
- `src/adapters/outbound/filesystem/`
- `src/adapters/inbound/cli/`

约束：

- outbound adapter 实现 application port
- inbound adapter 负责把 CLI / HTTP / job 参数转换成 application command
- adapter 可以依赖第三方库、数据库、文件系统、AkShare
- adapter 不应承载核心业务规则

### DB

放数据库基础设施：

- `db/models.py`
- `db/session.py`
- `db/schema/`

约束：

- ORM model 不放进 application service
- schema SQL 和 ORM model 保持明确对应
- repository/gateway 可以依赖这里，但 application 不直接依赖这里

## 端口与适配器约定

### AkShare

- port：`src/application/ports/*.py`
- adapter：`src/adapters/outbound/market_data/*.py`
- 命名：优先使用 `*Provider`

规则：

- 上游字段兼容和 SDK 调用放在 adapter
- 标准化、过滤、业务口径放在 domain

### 数据库

- port：`src/application/ports/*.py`
- adapter：`src/adapters/outbound/persistence/*.py`
- infra：`db/models.py`、`db/session.py`
- 命名：
  - 以持久化写入和查询为主的 adapter 优先使用 `*Gateway`
  - 需要表达聚合级持久化抽象时可使用 `*Repository`

规则：

- application service 只依赖 gateway port
- SQLAlchemy session 和 ORM model 只应出现在 adapter / db 层

### 脚本入口

- adapter：`src/adapters/inbound/cli/*.py`
- `scripts/*.py` 只保留极薄的启动包装
- 命名：CLI 适配器优先使用 `*_cli.py`，并暴露 `run_*_command`

规则：

- 参数解析和输出展示属于 inbound adapter
- `scripts/*.py` 不承载业务逻辑或 SQL

## 命名约定

- 从外部系统读取或拉取数据的端口或适配器，优先命名为 `Provider`
- 向数据库、文件系统、下游系统写入或协调持久化的端口或适配器，优先命名为 `Gateway`
- 当某个持久化抽象需要围绕领域聚合组织时，再使用 `Repository`
- 应用层编排入口放在 `src/application/services/`，优先使用 `run_*_workflow`、`build_*`、`export_*` 这类清晰动作命名
- CLI 入口放在 `src/adapters/inbound/cli/`，优先使用 `run_*_command`

## 迁移策略

本仓库当前仍保留 `src/data/` 兼容层，供旧代码平滑过渡。后续新增代码应优先写入：

- `src/domain/`
- `src/application/`
- `src/adapters/`
- `db/`

`src/data/` 的定位：

- 仅作为兼容 facade 或过渡 re-export
- 不再新增新的核心逻辑

类似约束同样适用于其他历史兼容路径：

- `src/strategies/` 可以在迁移期保留 facade，但新的核心策略规则优先进入 `src/domain/strategies/`
- `scripts/` 可以保留启动包装，但新的参数解析和命令编排优先进入 `src/adapters/inbound/cli/`

## Code Review 检查项

提交新代码时，至少检查以下问题：

- 是否把业务规则直接写进了脚本、SQLAlchemy adapter 或 notebook
- 是否在 application 层直接 import 了 ORM model、`Session`、AkShare SDK
- 是否把第三方接口字段名直接传播到 domain 或 strategy 层
- 是否为新增外部依赖定义了明确 port
- 是否存在可以下沉到 domain 的纯转换逻辑，却被写在 adapter 中

## 当前落地示例

### A股股票列表入库

- domain：A 股股票列表标准化与过滤
- application：A 股入库用例与 gateway/provider 端口
- adapters：
  - AkShare provider
  - SQLAlchemy persistence gateway
  - CLI entrypoint
- db：
  - ORM model
  - session 工厂

### K线 CSV 标准化

- domain：K 线 dataframe 字段标准化
- adapter：
  - CSV 读取与 UTF-8 写出
  - CLI entrypoint

### 通用策略与回测工作流

- domain：策略规则与信号生成逻辑
- application：策略运行与工作流编排
- adapters：
  - CLI entrypoint
  - 复用现有回测与输出能力的适配层
- compatibility：
  - `src/strategies/` 在迁移期继续保留兼容边界

## 下一批迁移优先级

建议按以下顺序继续迁移：

1. `backtest/engine.py` 周边的编排与输出入口
2. `pipelines/` 中未来的跨模块流程
3. `execution/` 与 `risk/` 的真实端口边界
4. `portfolio/` 与 `factors/` 的应用层编排

## 后续建议

- 对 `backtest/`、`strategies/`、`pipelines/` 继续按同一命名和边界规则推进
- 优先迁移那些已经拥有稳定 CLI 和测试的工作流，再处理更深层的共享引擎
