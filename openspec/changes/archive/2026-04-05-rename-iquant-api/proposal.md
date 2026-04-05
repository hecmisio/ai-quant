## 背景

项目规范中当前仍使用 `iquant API` 与 `third/docs/iquant API.pdf` 的写法，但仓库中的实际文档文件名已经调整为 `iquant-api.pdf`。如果不及时同步，后续文档引用和实现说明会出现命名与路径不一致的问题。

本次变更用于统一项目中关于 iquant API 的命名和文档路径表述。

## 变更内容

- 将项目规范中的 `iquant API` 更名为 `iquant-api`。
- 将参考文档路径从 `third/docs/iquant API.pdf` 更新为 `third/docs/iquant-api.pdf`。
- 保持 QMT 默认指国信 iQuant 的规则不变。

## 能力范围

### 新增 Capabilities

None.

### 修改的 Capabilities
- `project-governance`：更新 iquant API 的标准命名与文档路径。

## 影响范围

- 影响所有引用 iquant API 的项目文档、设计说明和实现假设。
- 不改变 QMT 标准本身，也不引入新的实现逻辑。
- 用于修正规范与仓库实际文件命名之间的差异。
