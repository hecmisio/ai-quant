## Why

当前仓库已经有 MACD 趋势策略与基础回测能力，但还缺少适合震荡行情、能够围绕价格区间进行分层交易的策略类型。网格策略规则直观、参数清晰，适合作为第二个正式策略能力，用来补齐“趋势策略之外的区间策略”研究路径，并验证现有策略接口是否能承载不同信号生成机制。

## What Changes

- 新增 `grid-strategy` capability，定义网格策略的输入数据、参数约束、网格价格层级生成、买卖信号与目标仓位输出。
- 在现有 `BaseStrategy` 风格下实现一个首版长仓网格策略，支持围绕基准价和价格区间生成固定数量网格。
- 为网格策略补充可复现的测试用例，验证价格穿越网格时的逐级加仓、减仓、边界处理与异常输入校验。
- 为研究脚本或后续回测接入暴露可调用入口，使网格策略可以像现有 MACD 策略一样被执行与验证。

## Capabilities

### New Capabilities
- `grid-strategy`: 定义面向区间行情的参数化长仓网格策略，包括网格生成、穿越触发、分层仓位调整和安全边界行为。

### Modified Capabilities

None.

## Impact

- Affected code: `src/strategies/`, `tests/unit/`, 以及可能新增的 `scripts/` 调用入口。
- Affected systems: 现有策略接口、策略测试夹具、未来复用该策略输出的回测流程。
- Dependencies: 继续基于当前 Pandas 数据处理栈，不预期新增外部依赖。
