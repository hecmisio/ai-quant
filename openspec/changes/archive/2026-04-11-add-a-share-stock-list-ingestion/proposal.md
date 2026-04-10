## Why

当前仓库已经具备基于 AkShare 获取并标准化 A 股股票列表的能力，但这份主数据还停留在内存或 CSV 输出层，无法进入 Anne 主库供后续行情、财报和事件数据统一复用。现在需要补上从股票列表到数据库 `instruments` 维表的标准入库链路，让 A 股标的主数据具备可追溯、可重复执行、可增量维护的落库能力。

## What Changes

- 新增一个 A 股股票列表入库流程，将已有标准化股票列表写入 Anne 主库的 `instruments` 表。
- 在入库流程中补充 `data_sources`、`ingestion_batches` 与必要的质量检查记录，保证来源与批次可追踪。
- 定义 A 股股票列表到 `instruments` 字段的映射、去重和幂等更新规则。
- 提供脚本级入口，支持手动触发股票列表入库并输出入库摘要。
- 为核心入库行为补充测试，覆盖字段映射、幂等写入和治理记录创建。

## Capabilities

### New Capabilities
- `a-share-stock-list-ingestion`: 定义将标准化 A 股股票列表写入 Anne 主库并记录来源、批次和质量检查的能力。

### Modified Capabilities

## Impact

- 受影响代码与目录：`src/data`、`scripts`、数据库访问或入库模块、相关测试用例。
- 受影响系统：Anne PostgreSQL 主库中的 `data_sources`、`ingestion_batches`、`quality_checks`、`instruments` 表。
- 依赖已有能力：AkShare A 股股票列表抓取与标准化逻辑、Anne 核心表 schema。
