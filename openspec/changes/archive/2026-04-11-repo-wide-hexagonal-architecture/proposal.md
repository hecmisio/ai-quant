## Why

当前仓库已经开始局部引入 `domain`、`application`、`adapters` 与 `db` 分层，但整体代码和规范仍存在旧的 `src/data` 兼容层、脚本直接耦合实现、以及部分 spec 仍按旧目录和旧职责描述能力的问题。现在需要把“全仓库六边形化”正式定义为一个跨模块 change，让后续新增功能和历史能力都遵循一致的 port/adaptor 边界，而不是停留在局部重构。

## What Changes

- 新增一个仓库级六边形架构治理 capability，定义 `domain`、`application`、`adapters`、`db` 和兼容层的职责边界。
- 将现有市场数据、入库和 CLI 能力的规范描述更新为基于 port/adaptor 的口径，而不再默认使用旧的 `src/data` 直连实现。
- 逐步把现有核心模块迁移到新结构，并将 `src/data` 收敛为过渡兼容 facade。
- 明确数据库、AkShare、文件系统和脚本入口各自的 port/adaptor 约定。
- 更新 README 与架构文档，使项目文档与现行 capability 保持一致。

## Capabilities

### New Capabilities
- `hexagonal-architecture-governance`: 定义仓库级六边形架构分层、端口适配器约定、兼容层策略和文档一致性要求。

### Modified Capabilities
- `a-share-stock-universe`: 将股票列表抓取能力的规范描述更新为 provider adapter + domain normalization 的架构口径。
- `a-share-stock-list-ingestion`: 将股票列表入库能力的规范描述更新为 application service + gateway adapter 的架构口径。
- `kline-volume-chart`: 将 K 线图表与 CLI 工作流的规范描述更新为 inbound/outbound adapter 分层口径。
- `project-governance`: 将项目治理要求扩展为必须维护架构分层约束和文档同步。

## Impact

- 受影响代码与目录：`src/` 下多个模块、`scripts/`、`db/`、兼容层 `src/data/`、相关测试。
- 受影响文档：`README.md`、架构约束文档，以及后续任何涉及模块职责描述的项目文档。
- 受影响规范：A 股股票列表获取、A 股股票列表入库、K 线图表 CLI、项目治理。
