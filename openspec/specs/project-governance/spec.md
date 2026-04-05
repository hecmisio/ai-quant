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

#### Scenario: 治理规范发生变更
- **WHEN** 与治理相关的 capability 被新增或修改
- **THEN** 所有受影响的项目文档 MUST 一并更新，确保其内容不与现行规范相矛盾
