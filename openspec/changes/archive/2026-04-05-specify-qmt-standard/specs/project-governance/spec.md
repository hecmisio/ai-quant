## MODIFIED Requirements

### Requirement: 项目文档必须与现行 capability 保持一致
项目级文档 MUST 与当前生效的 OpenSpec capability 保持一致，不得与架构规则和交付要求相互冲突。

项目中涉及 QMT 的表述 MUST 采用以下统一标准：
- QMT 默认指国信 iQuant
- 项目内参考 API 文档路径为 `third/docs/iquant API.pdf`

#### Scenario: 治理规范发生变更
- **WHEN** 与治理相关的 capability 被新增或修改
- **THEN** 所有受影响的项目文档 MUST 一并更新，确保其内容不与现行规范相矛盾

#### Scenario: 文档引用 QMT
- **WHEN** 项目文档、设计说明或实现说明引用 QMT
- **THEN** 它们 MUST 将 QMT 视为国信 iQuant
- **AND** 它们 MUST 使用 `third/docs/iquant API.pdf` 作为项目内参考 API 文档路径，除非后续规范另有更新

## ADDED Requirements

### Requirement: QMT 相关变更必须声明是否遵循项目标准
任何新增的 QMT 相关 change 或实现说明 MUST 明确说明自己是否遵循项目当前定义的 QMT 标准。

#### Scenario: 提出新的 QMT 相关功能
- **WHEN** 一个 change 涉及 QMT 数据接入、信号联动、交易执行或 API 封装
- **THEN** 该 change MUST 明确说明其基于国信 iQuant 标准
- **AND** 如果它不遵循 `third/docs/iquant API.pdf` 所代表的项目参考基线，就 MUST 在变更中显式说明偏离原因
