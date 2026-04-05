## 背景

项目后续很可能围绕 QMT 进行研究、接入与执行开发。如果不在项目规范中统一 QMT 的具体产品与参考资料来源，后续文档和实现中可能会出现不同供应商、不同接口文档和不同接入假设并存的情况，增加沟通和维护成本。

本次变更用于明确项目当前采用的 QMT 标准为国信 iQuant，并将仓库中的 API 文档路径写入正式规范。

## 变更内容

- 在 `project-governance` capability 中补充 QMT 标准约定。
- 明确项目中提到的 QMT 默认指国信 iQuant。
- 明确项目内参考 API 文档路径为 `third/docs/iquant API.pdf`。

## 能力范围

### 新增 Capabilities

None.

### 修改的 Capabilities
- `project-governance`：补充 QMT 产品标准和参考文档路径要求。

## 影响范围

- 影响所有后续引用 QMT 的项目文档、设计说明和实现假设。
- 不改变现有系统职责边界，不直接引入代码实现变更。
- 为后续与 QMT 相关的功能 change 提供统一约定。
