## ADDED Requirements

### Requirement: 项目必须定义交易系统边界
项目 MUST 将市场数据接入、信号生成、风险控制和交易执行划分为不同职责，以保证后续变更能够维持清晰的系统边界。

#### Scenario: 提出新的交易相关能力
- **WHEN** 贡献者提出一个处理市场数据或生成订单的能力
- **THEN** 该变更 MUST 明确说明自己属于哪一层职责
- **AND** 它 MUST NOT 将数据接入、信号生成、风控审批和交易执行混成一个无法审查的单步骤流程

### Requirement: 执行前必须经过风控闸门
任何可能产生可执行订单的行为 MUST 在到达券商或交易接口之前经过显式风险控制审批。

#### Scenario: 策略生成候选订单
- **WHEN** 策略模块或信号模块给出买卖建议
- **THEN** 该建议 MUST 先经过风险约束检查，才能转换为可执行订单
- **AND** 执行相关组件 MUST 只接收已经通过审批的指令

### Requirement: 重要变更必须遵循 OpenSpec 流程
所有涉及系统行为、架构边界、交易流程或治理规则的重要变更 MUST 在实现前通过 OpenSpec 进行定义。

#### Scenario: 贡献者要增加跨模块功能
- **WHEN** 一个功能会改变用户可见行为、交易流程、安全边界或跨模块架构
- **THEN** 贡献者 MUST 先创建或更新对应的 OpenSpec change 与 spec，再进入实现阶段

### Requirement: 策略相关变更必须说明证据与限制
未来任何策略、信号或执行能力 MUST 说明其证据基础、适用假设和安全限制。

#### Scenario: 新增策略能力
- **WHEN** 一个 change 引入新的策略、因子模型、信号规则或执行逻辑
- **THEN** 该 change MUST 说明其数据依据或评估证据
- **AND** 它 MUST 定义关键的适用范围、假设条件或安全限制

### Requirement: 项目文档必须与现行 capability 保持一致
项目级文档 MUST 与当前生效的 OpenSpec capability 保持一致，不得与架构规则和交付要求相互冲突。

项目中涉及 QMT 的表述 MUST 采用以下统一标准：
- QMT 默认指国信 iQuant
- 项目内参考 API 文档路径为 `third/docs/iquant-api.pdf`
- 项目中引用该接口文档时，标准名称为 `iquant-api`

#### Scenario: 治理规范发生变更
- **WHEN** 与治理相关的 capability 被新增或修改
- **THEN** 所有受影响的项目文档 MUST 一并更新，确保其内容不与现行规范相矛盾

#### Scenario: 文档引用 QMT
- **WHEN** 项目文档、设计说明或实现说明引用 QMT
- **THEN** 它们 MUST 将 QMT 视为国信 iQuant
- **AND** 它们 MUST 使用 `third/docs/iquant-api.pdf` 作为项目内参考 API 文档路径，除非后续规范另有更新

#### Scenario: 文档引用 iquant-api
- **WHEN** 项目文档、设计说明或实现说明引用该 API 文档或其标准名称
- **THEN** 它们 MUST 使用 `iquant-api` 这一命名
- **AND** 它们 MUST NOT 再使用 `iquant API` 作为项目当前标准名称

### Requirement: QMT 相关变更必须声明是否遵循项目标准
任何新增的 QMT 相关 change 或实现说明 MUST 明确说明自己是否遵循项目当前定义的 QMT 标准。

#### Scenario: 提出新的 QMT 相关功能
- **WHEN** 一个 change 涉及 QMT 数据接入、信号联动、交易执行或 API 封装
- **THEN** 该 change MUST 明确说明其基于国信 iQuant 标准
- **AND** 如果它不遵循 `third/docs/iquant-api.pdf` 所代表的项目参考基线，就 MUST 在变更中显式说明偏离原因
