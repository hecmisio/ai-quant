## 背景

当前项目已经规定 QMT 默认指国信 iQuant，并指定项目内参考 API 文档路径，但规范中的 API 名称与实际文件名存在大小写和连接符形式不一致的问题。由于这些内容会被后续 change、设计文档和实现说明重复引用，应尽快统一成单一标准。

本次设计只修正命名与路径，不调整已有治理规则的含义。

## 目标 / 非目标

**目标：**
- 将规范中的 `iquant API` 统一更名为 `iquant-api`。
- 将参考文档路径统一为 `third/docs/iquant-api.pdf`。
- 保证主规范与仓库中的实际文件名保持一致。

**非目标：**
- 不改变 QMT 默认指向国信 iQuant 的规则。
- 不引入新的 API 接入要求。
- 不修改非规范文件中的实现逻辑。

## 关键决策

### Decision: 以仓库中的实际文件名为准
项目规范中的 API 名称与路径统一以当前仓库中的文件名 `iquant-api.pdf` 为准。

Rationale:
- 这是项目内最直接、最稳定的参考来源。
- 可以消除规范文本与实际文件路径不一致的问题。

Alternatives considered:
- 保留旧写法并在文档中解释：会持续制造歧义，没有必要。

## 风险 / 权衡

- [Risk] 其他文档中可能仍残留旧写法。 → Mitigation: 后续引用统一按新规范逐步修正。
- [Risk] 若文件再次改名，需要再次更新规范。 → Mitigation: 继续通过 OpenSpec delta 维护一致性。

## 迁移计划

1. 修改 `project-governance` capability 中的 API 名称和参考路径。
2. 将该 change 归档，使新命名正式生效。
3. 后续所有项目文档均采用 `iquant-api` 和 `third/docs/iquant-api.pdf`。

## 开放问题

- 是否需要在后续统一补一遍历史文档中的旧命名引用。
