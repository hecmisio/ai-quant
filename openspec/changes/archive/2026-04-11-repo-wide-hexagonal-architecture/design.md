## Context

仓库已经在 A 股股票列表获取、入库与 K 线标准化链路上落地了第一批 `domain`、`application`、`adapters` 与 `db` 分层，但这仍然是局部改造而非全仓库工程规则。当前仍存在三个问题：

- 部分能力已经迁入新结构，但旧的 `src/data` 兼容层和旧 spec 描述仍然保留，容易让后续开发继续把新逻辑写回旧路径。
- 脚本、AkShare、文件系统、数据库访问虽然已经开始分离，但 port/adaptor 命名和职责边界还没有被正式规范化。
- 现有多个 capability 的 spec 仍按“脚本直接调用实现”或“模块位于 `src/data`”的旧口径描述，导致规范与代码现状开始偏离。

这次 change 的目标不是一次性重写全仓库所有模块，而是把“全仓库六边形化”的演进路径定义清楚，并优先覆盖当前最常用、最具代表性的市场数据、入库和 CLI 流程。这样后续回测、策略、执行和 pipeline 模块可以沿同一模式继续迁移。

约束包括：

- 必须保留一段兼容期，不能为了纯粹架构而立即打断现有 `src/data` 调用。
- 新增规范必须足够具体，能约束后续新代码不再把业务逻辑直接写进脚本或 ORM 层。
- 需要同步更新已有 capability 的 spec，使正式规范与现有代码方向一致。
- 第一版仓库级架构治理应聚焦目录职责、端口边界和迁移约束，不展开到完整 DDD 建模或事件驱动架构。

## Goals / Non-Goals

**Goals:**

- 为仓库建立正式的六边形架构 capability，定义 `domain`、`application`、`adapters`、`db` 与兼容层职责。
- 为 AkShare、数据库、文件系统和 CLI 建立一致的 port/adaptor 约定。
- 更新已有 A 股股票列表获取、A 股股票列表入库和 K 线 CLI 相关 capability 的规范描述，使其与新架构一致。
- 明确 `src/data` 的过渡定位，阻止新核心逻辑继续进入兼容层。
- 要求 README 与项目级架构文档在能力变更时保持同步。

**Non-Goals:**

- 不在本次 change 中完成全仓库每一个模块的彻底迁移。
- 不强制本次就重写 `backtest`、`strategies`、`execution` 的全部内部实现。
- 不把架构治理扩展到消息总线、事件溯源或复杂服务拆分。
- 不替换当前已有的 Anne 数据库 schema 或交易策略行为定义。

## Decisions

### 1. 采用“先定义治理能力，再逐步迁移模块”的两阶段策略

选择先把仓库级架构规则和已有 capability 的规范描述固定下来，再按优先级逐步迁移更多模块，而不是一次性大规模移动整个代码库。

原因：

- 六边形架构本质上是边界治理问题，先固定规范能减少后续反复返工。
- 当前仓库还在快速演进，一次性全量迁移会把风险集中到单次变更。
- 现有 A 股与 K 线链路已经提供了可复用样板，适合作为仓库级模式模板。

备选方案：

- 先做大规模文件迁移再补规范：容易让新的代码位置改变但职责边界仍不清晰。
- 只写文档不改 spec：无法形成正式 capability 约束，后续容易失效。

### 2. 以 port/adaptor 契约约束外部依赖，而不是以目录名替代架构

选择把 AkShare、数据库、文件系统和 CLI 的边界明确定义为 provider、gateway 或 inbound adapter 这类端口契约，而不是仅要求把文件放到某个目录。

原因：

- 六边形架构的关键是依赖方向，不只是目录名字。
- 仅做目录迁移无法阻止 application 层继续直接 import ORM model 或第三方 SDK。
- port/adaptor 约束更便于测试和替换实现。

备选方案：

- 只规定目录：执行成本低，但无法防止架构回退。
- 直接引入更复杂的 repository/service 基础框架：当前仓库规模下会增加过早抽象。

### 3. 保留 `src/data` 作为显式兼容层，但禁止其继续承载新核心逻辑

选择让 `src/data` 在过渡期保留 facade/re-export 职责，用于稳定旧导入路径，同时通过规范明确禁止向该目录继续添加新的核心实现。

原因：

- 可以降低渐进迁移的破坏性。
- 允许脚本、测试和外部引用按优先级逐步切换。
- 与“仓库级治理 change + 后续增量迁移”策略一致。

备选方案：

- 立即删除 `src/data`：短期更干净，但会打断现有调用。
- 无限期保留 `src/data` 作为正常开发目录：会让新旧结构长期并存，削弱迁移效果。

### 4. 通过修改现有 capability，显式把旧描述升级成新边界

选择修改 `a-share-stock-universe`、`a-share-stock-list-ingestion`、`kline-volume-chart` 与 `project-governance`，让正式 spec 从“旧实现位置”升级为“新边界职责”。

原因：

- 这些能力已经在代码中受到了六边形改造影响。
- 如果不更新 spec，后续 archive 或 review 时会持续出现规范与代码不一致。
- 这几个 capability 分别覆盖 provider adapter、gateway adapter、CLI adapter 和项目治理，具有代表性。

备选方案：

- 只新增一个总架构 capability：不足以修复旧 capability 的描述漂移。
- 为每个模块都新增独立 capability：会让 change 过于分散。

## Risks / Trade-offs

- [迁移周期较长导致新旧结构并存时间较久] -> 通过 capability 明确 `src/data` 只能作为兼容层，限制继续堆积新逻辑。
- [规范更新过快而部分历史模块尚未迁移] -> 在 spec 中区分“新开发必须遵循”与“历史模块逐步迁移”的过渡语义。
- [过度抽象导致仓库复杂度上升] -> 第一版只定义最小 port/adaptor 约定，不引入过多抽象基类。
- [贡献者仍沿旧路径开发] -> 同步更新 README、架构约束文档和项目治理 capability，把 review 检查项正式化。

## Migration Plan

1. 新增仓库级六边形架构 capability，并定义目录职责、端口约定、兼容层策略与文档同步要求。
2. 更新现有 A 股股票列表获取、A 股股票列表入库、K 线 CLI 与项目治理相关 spec，使其与现有架构方向一致。
3. 在后续 change 中按优先级继续迁移 `backtest`、`strategies`、`pipelines`、`execution` 等模块。
4. 逐步减少 `src/data` 的直接使用面，待兼容期结束后再考虑收缩或移除旧 facade。

回滚策略：

- 如规范方向不合适，可在后续 change 中修改 capability，而不需要回滚已完成的实现文件迁移。
- 对于具体模块迁移，优先使用兼容 facade 作为回退缓冲层。

## Open Questions

- `backtest` 与 `strategies` 是否应继续保留当前目录名，还是未来也按 `domain/application/adapters` 方式进一步展开子层次。
- 是否需要为全仓库定义统一的 provider/gateway/repository 命名规范，而不只是在文档中给出示例。
