## ADDED Requirements

### Requirement: 项目必须定义标准目录结构
项目 MUST 定义一套稳定的目录职责划分，用于区分研究文档、正式代码、数据资产、配置、测试、脚本和运行输出，以保证策略开发能够在统一工程结构下持续演进。

推荐的完整项目目录结构如下：

```text
ai-quant/
├─ docs/                      # 你的策略思考、市场认知、专题笔记
├─ data/
│  ├─ raw/                    # 原始行情、财务、新闻等，不做修改
│  ├─ interim/                # 清洗中间结果
│  ├─ processed/              # 回测/训练直接使用的数据
│  └─ snapshots/              # 关键时点快照，便于复现
├─ notebooks/                 # 临时研究、指标验证、想法试验
├─ config/
│  ├─ env/                    # dev/test/prod 配置
│  ├─ data/                   # 数据源配置
│  └─ strategies/             # 各策略参数配置
├─ src/
│  ├─ common/                 # 通用工具：时间、日志、文件、配置加载
│  ├─ data/                   # 数据接入、清洗、特征加工
│  ├─ factors/                # 因子计算、技术指标、信号组件
│  ├─ strategies/             # 策略实现
│  │  ├─ trend/               # 趋势类
│  │  ├─ mean_reversion/      # 均值回归/震荡类
│  │  ├─ rotation/            # 轮动类
│  │  └─ base.py              # 策略基类/统一接口
│  ├─ portfolio/              # 仓位管理、组合构建、资金分配
│  ├─ risk/                   # 止损、限仓、风控规则
│  ├─ backtest/               # 回测引擎、撮合、绩效分析
│  ├─ execution/              # 实盘下单、券商/交易接口适配
│  └─ pipelines/              # 把“取数→算信号→回测/执行”串起来
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  └─ fixtures/
├─ scripts/                   # 命令行脚本，如批量回测、数据更新
├─ outputs/
│  ├─ reports/                # 回测报告
│  ├─ signals/                # 每日信号输出
│  └─ logs/                   # 运行日志
├─ third/
│  ├─ docs/                   # 第三方官方文档、接口手册、供应商资料
│  ├─ sdk/                    # 第三方 SDK、安装包或无法通过包管理器获取的依赖
│  └─ examples/               # 第三方官方示例
└─ README.md
```

#### Scenario: 新增项目级目录或模块
- **WHEN** 贡献者准备新增一个目录、模块或存放规则
- **THEN** 它 MUST 对应明确的工程职责
- **AND** 它 MUST NOT 与已有目录在职责上形成明显重叠或混淆

### Requirement: 项目必须区分研究区与实现区
项目 MUST 将研究与说明内容放在 `docs`，并将正式可执行实现放在 `src`，从而避免研究材料与工程代码混杂。

#### Scenario: 新增策略说明文档
- **WHEN** 贡献者新增策略说明、市场分析、方法论总结或设计解读
- **THEN** 这些内容 MUST 放在 `docs` 或其子目录中
- **AND** 它们 MUST NOT 作为正式实现文件放入 `src`

#### Scenario: 新增正式代码
- **WHEN** 贡献者新增可执行代码、基础模块、策略实现、回测逻辑或执行逻辑
- **THEN** 这些内容 MUST 放在 `src` 或其规范化子目录中
- **AND** 它们 MUST NOT 以“文档草稿”方式长期停留在研究目录中替代正式实现

### Requirement: Notebook 必须作为临时研究区使用
项目 MUST 将 `notebooks/` 视为临时研究、指标验证和想法试验目录，而不是正式实现或长期归档的主存放区。

#### Scenario: 进行交互式策略试验
- **WHEN** 贡献者为了快速验证指标、因子、信号或可视化结果而创建 Notebook
- **THEN** 这些内容 MAY 放在 `notebooks/`
- **AND** 一旦结论稳定，相关说明 SHOULD 回流到 `docs/`，正式实现 SHOULD 回流到 `src/`

### Requirement: 第三方资产必须与项目自有内容分离
项目 MUST 将 `third/` 作为第三方官方文档、SDK、官方示例和供应商原始资料的目录，并与项目自己的研究、实现和运行产物保持边界分离。

#### Scenario: 保存第三方接口文档或 SDK
- **WHEN** 贡献者需要保存第三方接口手册、官方 PDF、SDK 安装包或供应商示例
- **THEN** 这些内容 MUST 放在 `third/` 或其规范化子目录中
- **AND** 它们 MUST NOT 混放到 `docs/`、`src/` 或 `outputs/`

#### Scenario: 保存项目内部研究结论
- **WHEN** 贡献者整理自己对第三方系统的分析、对接说明或使用总结
- **THEN** 这些内容 SHOULD 放在 `docs/`
- **AND** 它们 SHOULD NOT 以项目自有文档的形式长期混放在 `third/`

### Requirement: 项目必须为量化开发闭环预留标准目录
项目 MUST 为数据、配置、测试、脚本和运行输出预留标准落位，以支持从研究到验证再到执行的完整工程闭环。

推荐目录包括：
- `data/`：数据资产目录，可进一步包含 `raw/`、`interim/`、`processed/` 和 `snapshots/`
- `config/`：配置目录，可进一步包含 `env/`、`data/` 和 `strategies/`
- `tests/`：测试目录，可进一步包含 `unit/`、`integration/` 和 `fixtures/`
- `scripts/`：命令行脚本或批处理入口目录
- `outputs/`：运行产物目录，可进一步包含 `reports/`、`signals/` 和 `logs/`

#### Scenario: 新增数据处理或运行产物
- **WHEN** 贡献者需要保存原始数据、中间加工数据、测试样本、回测报告、日志或每日信号输出
- **THEN** 这些内容 MUST 放在与其职责对应的标准目录中
- **AND** 它们 MUST NOT 随意散落在 `src`、`docs` 或其他无明确约定的位置

### Requirement: 数据资产与运行产物默认不得提交到 Git
项目 MUST 将 `data/` 和 `outputs/` 视为默认不纳入版本库的目录，以避免大体积、可再生成或环境耦合资产污染代码仓库历史。

允许的例外包括：
- 用于保留目录结构的占位文件
- 放在 `tests/fixtures/` 的小型测试样本
- 为关键复现实验保留、且在变更中明确说明用途的小型快照

#### Scenario: 保存原始行情或中间处理结果
- **WHEN** 贡献者生成或导入原始行情数据、中间加工结果或常规回测输出
- **THEN** 这些文件 MUST NOT 提交到 Git
- **AND** 项目 SHOULD 通过 `.gitignore` 或等效机制默认忽略这些目录

#### Scenario: 提交测试或复现样本
- **WHEN** 贡献者需要提交一个用于测试或关键复现的小型样本
- **THEN** 该样本 MUST 保持最小规模并具备明确用途
- **AND** 它 SHOULD 优先放在 `tests/fixtures/`，或在确有必要时作为经过说明的小型快照保留

### Requirement: 项目必须为核心量化模块提供标准代码落位
项目 MUST 在 `src` 下为通用能力、数据处理、因子计算、策略实现、组合管理、风控、回测、执行和流程编排提供清晰的模块边界。

推荐子目录包括：
- `src/common/`
- `src/data/`
- `src/factors/`
- `src/strategies/`
- `src/portfolio/`
- `src/risk/`
- `src/backtest/`
- `src/execution/`
- `src/pipelines/`

#### Scenario: 新增策略实现
- **WHEN** 贡献者开始开发一个新的趋势、轮动、网格或均值回归策略
- **THEN** 该实现 MUST 放在 `src/strategies/` 或其下的规范化子目录中
- **AND** 如需依赖回测、风控或执行能力，这些依赖 MUST 分别落在对应模块边界中

#### Scenario: 新增跨模块流程
- **WHEN** 贡献者需要实现“取数 -> 特征/因子 -> 信号 -> 风控 -> 回测/执行”的流程
- **THEN** 其流程编排逻辑 SHOULD 放在 `src/pipelines/`
- **AND** 它 SHOULD 复用各职责模块，而不是将全部逻辑挤在单一文件中
