## Context

Anne 主库的 PostgreSQL 18.3 启动基线已经具备，但库内还没有承接统一事实源职责的表结构。根据数据库选型决策，Anne 需要同时管理时间序列、事件、文档元数据、实体关系和可审计的数据治理信息，因此第一版 schema 不能只建单一行情表，而要覆盖治理层与几类核心事实层。

本次设计的目标是建立 `anne` 库的第一批关系型表基线，为后续数据采集、清洗、标准化和交付提供稳定落点。这个阶段要优先解决“有统一 schema 可落库”，而不是一次性穷尽所有分析优化。

约束包括：

- 必须与现有 `PostgreSQL 18.3 + TimescaleDB + pgvector` 基线兼容。
- 表结构要服务于混合型金融数据，而不是只针对一种数据源。
- 所有核心表都要包含统一治理字段，满足追溯、版本与原始文件定位需求。
- 本次实现应以基础 SQL schema 为主，不引入过早复杂化的物化视图、分区策略或外部检索系统。

## Goals / Non-Goals

**Goals:**

- 为 Anne 主库建立第一批核心治理表与事实表。
- 为行情、财报、宏观、文档、事件和日历数据定义稳定的第一版落库结构。
- 为所有核心表统一主键策略、唯一约束思路和治理字段规范。
- 为后续 Timescale hypertable、向量索引和更细粒度实体关系建模预留扩展路径。

**Non-Goals:**

- 不在本次设计中覆盖 tick、orderbook 或超大规模分钟级数据建模细节。
- 不在本次设计中实现完整的 RAG 切片表、embedding 列或向量索引策略。
- 不定义 Sophie 的查询视图、报表接口或下游 API。
- 不试图一次性覆盖所有金融资产类别和全部供应商字段口径。

## Decisions

### 1. 第一版 schema 采用“治理表 + 核心事实表 + 文档/事件表”分层

选择先建立三类表：

- 治理表：`data_sources`、`ingestion_batches`、`quality_checks`
- 核心事实表：`instruments`、`market_bars`、`financial_reports`、`macro_series`、`macro_observations`
- 文档与事件表：`documents`、`calendar_events`、`catalyst_events`

原因：

- 这几类表覆盖了选型文档中明确指出的第一批关键数据域。
- 治理表先行可以让所有事实表共享来源、批次、质量和回溯语义。
- 把宏观序列拆成定义表和观测表，有利于后续扩展和唯一约束表达。

备选方案：

- 只先建行情相关表：范围过窄，不符合 Anne 作为统一事实源的职责。
- 一次性把所有关系拆得非常细：早期复杂度过高，拖慢首版落地。

### 2. 所有核心表统一保留治理字段

选择把 `source`、`ingested_at`、`as_of`、`version`、`raw_uri` 作为跨表统一治理字段基线；必要时再增加 `batch_id` 或 `source_id` 外键。

原因：

- 这些字段已经在数据库选型文档中被明确点名。
- 统一字段可以降低后续 ETL 与审计逻辑的分叉。
- 即使不同表业务列差异很大，治理语义仍可以保持一致。

备选方案：

- 仅在治理表中记录这些信息，再由事实表间接关联：查询成本和建模复杂度更高。
- 每张表自由定义治理字段：会导致口径漂移。

### 3. 使用自然业务键 + 代理键的混合策略

选择对大多数表使用 `BIGSERIAL`/`IDENTITY` 主键，同时针对业务唯一性建立显式唯一约束，例如：

- `instruments(exchange, symbol)`
- `market_bars(instrument_id, bar_time, timeframe, adjustment_type)`
- `financial_reports(instrument_id, report_period_end, statement_type, version)`
- `macro_observations(series_id, observation_time, version)`

原因：

- 代理键简化关系连接与后续引用。
- 业务唯一约束可以防止重复摄入，同时保留版本化空间。

备选方案：

- 全部使用复合主键：联表和外键维护成本偏高。
- 全部仅用代理键无唯一业务约束：容易引入重复事实记录。

### 4. 时序表先建普通表，保留后续 Timescale 升级路径

选择在第一版 schema 中先定义普通 PostgreSQL 表和必要索引，不强制立即对所有时序表执行 hypertable 转换。

原因：

- 先完成事实模型比先完成存储优化更关键。
- 哪些表最值得 hypertable 化，需要结合真实数据量和写入模式判断。

备选方案：

- 第一版全部变成 hypertable：增加实现复杂度，也容易在数据量尚小阶段过度设计。

## Risks / Trade-offs

- [第一版表结构覆盖范围不足] -> 先优先支持明确的数据域，保留后续增量变更继续扩展。
- [治理字段统一但部分数据源语义不完全匹配] -> 允许部分字段为空，但保留统一列名和约束风格。
- [文档与事件建模仍偏粗粒度] -> 第一版先满足权威落库和关联追溯，后续再继续拆分实体关系表。
- [过早固定字段命名可能与未来供应商口径冲突] -> 采用标准化后的内部命名，不直接复刻单一供应商字段。

## Migration Plan

1. 在仓库中新增 Anne 主库 schema SQL 文件，按依赖顺序创建治理表、维表和事实表。
2. 通过当前数据库容器连接 `anne` 库，执行建表脚本并验证约束和索引可以成功创建。
3. 用最小样例插入验证外键关系、唯一约束和空值策略。
4. 如后续需要调整字段或拆表，新增后续 schema 变更，而不是重写 bootstrap。

## Open Questions

- `documents` 是否需要在第一版就区分 `news` 与 `research_reports` 两张表，还是先用单表加 `document_type`。
- `catalyst_events` 与文档/标的的多对多关联是否需要第一版就落关联表。
- `financial_reports` 是先采用宽表按 statement_type 区分，还是进一步拆成利润表、资产负债表、现金流表三张表。
