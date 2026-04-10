## Why

Anne 的数据库基础设施已经就位，但 `anne` 库中仍缺少可承载统一事实源职责的关系型表结构。现在需要建立第一批核心表，给后续行情、财报、宏观、新闻、研报、日历和催化剂事件的数据摄入提供稳定落点。

## What Changes

- 在 `anne` 库中新增一组基础治理表，用于记录数据源、入库批次和质量检查结果。
- 在 `anne` 库中新增第一批核心事实表与元数据表，覆盖行情、财报、宏观序列、新闻/研报文档、财经日历和催化剂事件。
- 为核心表统一定义主键、唯一约束、时间字段和治理字段，如 `source`、`ingested_at`、`as_of`、`version`、`raw_uri`。
- 为适合时序化管理的表预留 TimescaleDB 使用路径，但本次不强制把所有表立即升级为 hypertable。
- 提供可重复执行的数据库建表脚本，作为 Anne 主库 schema 的第一版基线。

## Capabilities

### New Capabilities
- `anne-core-tables`: 定义 Anne 主库第一批基础治理表、核心事实表和统一治理字段的关系型 schema 基线。

### Modified Capabilities

## Impact

- 受影响系统：`anne` PostgreSQL 主库、数据库初始化/迁移脚本目录、后续数据接入实现。
- 新增能力：统一事实源的第一版落库结构，可支撑多源标准化数据入库。
- 受影响代码与目录：数据库 schema SQL、后续依赖这些表的 ETL/数据接入模块、面向 Sophie 的查询视图设计。
