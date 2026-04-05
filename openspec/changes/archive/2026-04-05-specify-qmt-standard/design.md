## 背景

当前 `project-governance` 规范约束了项目级流程、边界和文档一致性，但尚未定义外部交易终端和 API 文档的统一参考来源。由于 QMT 在量化交易系统中往往同时影响数据、执行、集成和文档表达，因此应先在治理层统一术语和参考资料。

本次设计只做项目级标准化声明，不引入任何运行时接入逻辑。

## 目标 / 非目标

**目标：**
- 将项目中的 QMT 标准明确为国信 iQuant。
- 将 `third/docs/iquant API.pdf` 明确为项目内参考 API 文档路径。
- 保证未来涉及 QMT 的文档和设计使用同一套外部依赖假设。

**非目标：**
- 不实现 iQuant API 的代码封装。
- 不定义具体 API 调用方式、鉴权流程或订单流程。
- 不排除未来新增其他终端或券商接口，只定义当前默认标准。

## 关键决策

### Decision: 在项目治理层声明 QMT 标准
将 QMT 的具体产品标准和文档路径放入 `project-governance`，而不是只写在普通文档里。

Rationale:
- 这是项目范围内的统一约定，适合放在治理层。
- 后续任何涉及 QMT 的功能 change 都可以直接引用该标准。
- 可以减少对“当前用的是哪一种 QMT”的歧义。

Alternatives considered:
- 仅在 README 或接入文档中说明：可见性不足，也不属于正式规范。

### Decision: 文档路径作为项目内参考基线
将 `third/docs/iquant API.pdf` 视为当前项目内的参考文档基线。

Rationale:
- 便于后续实现和文档统一引用。
- 可减少外部链接变动带来的不稳定性。

Alternatives considered:
- 只引用外部官网文档：可能受版本变化和访问条件影响。

## 风险 / 权衡

- [Risk] 后续若切换到其他 QMT 或 API 文档版本，需要再次修改规范。 → Mitigation: 通过后续 OpenSpec delta 明确更新。
- [Risk] 项目成员可能误以为此规范已经等于实现完成。 → Mitigation: 在规范中仅声明标准与文档来源，不涉及接入完成状态。

## 迁移计划

1. 修改 `project-governance` capability，加入 QMT 标准约定。
2. 归档该 change，使 QMT 标准成为项目现行规范的一部分。
3. 后续所有涉及 QMT 的文档和设计，默认引用该标准与文档路径。

## 开放问题

- 后续是否需要在规范中补充 API 版本号或文档发布日期。
- 是否需要为 QMT 相关实现再单独创建 capability，约束接入层设计。
