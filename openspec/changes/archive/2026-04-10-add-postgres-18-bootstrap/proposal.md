## Why

Anne 需要一个可持续扩展、可治理的主数据库底座，来承接行情、财报、宏观、新闻、研报和事件等混合数据。当前仓库尚未提供可直接启动的 PostgreSQL 18.3 本地开发环境和扩展初始化机制，这会阻塞后续表结构设计、数据入库与研发协作。

## What Changes

- 新增基于 `PostgreSQL 18.3` 的本地数据库启动方案，提供仓库级 `docker-compose.yml`。
- 新增数据库初始化扩展脚本，用于自动启用 `TimescaleDB` 与 `pgvector`。
- 约定数据库容器的基础环境变量、端口、卷挂载与初始化目录结构，作为 Anne 主库的统一开发基线。
- 明确该数据库基线服务于 Anne 作为统一事实源的主库职责，而不是用于替代原始文件存储或研究缓存层。

## Capabilities

### New Capabilities
- `anne-database-bootstrap`: 定义 Anne 主库的 PostgreSQL 18.3 本地启动、扩展初始化和基础运行约定。

### Modified Capabilities

## Impact

- 受影响系统：本地开发环境、数据库基础设施、后续 Anne 数据建模与入库流程。
- 新增依赖：`PostgreSQL 18.3`、`TimescaleDB`、`pgvector`、Docker Compose。
- 受影响代码与目录：仓库根目录基础设施文件、数据库初始化脚本目录、后续依赖数据库的实现模块。
