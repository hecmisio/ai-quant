## MODIFIED Requirements

### Requirement: AI 协作角色必须职责分离
项目 MUST 将情报官、分析师、风控师、交易员定义为职责清晰、边界明确的独立协作角色。

项目 MUST 使用以下标准角色名称映射作为正式命名规范：
- 情报官：Anne Hathaway
- 分析师：Sophie Marceau
- 风控师：Lily Collins
- 交易员：Monica Bellucci

#### Scenario: 工作流中的任务分配
- **WHEN** 某个流程步骤涉及数据准备、信号生成、风控审批或交易执行
- **THEN** 该步骤 MUST 能明确归属到一个责任角色
- **AND** 相邻角色之间 MUST 通过显式交接协作，而不是隐式职责重叠

#### Scenario: 文档引用标准角色名称
- **WHEN** 项目文档、设计说明或协作描述引用四个标准角色
- **THEN** 它们 MUST 使用已定义的标准角色名称映射
- **AND** 它们 MUST NOT 为同一角色引入未记录在规范中的替代人设名称

## ADDED Requirements

### Requirement: 标准角色名不直接约束实现命名
项目 MUST 将标准角色名称视为协作与文档层的命名规则，而不是对代码实现命名的强制要求。

#### Scenario: 实现模块命名
- **WHEN** 开发者为模块、类、函数或服务命名
- **THEN** 实现命名 MAY 使用技术化或职责化名称
- **AND** 只要文档和协作语义保持与标准角色映射一致，就 MUST NOT 视为违反规范
