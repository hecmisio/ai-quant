## Why

当前仓库已经具备策略目录骨架和最小策略接口，但还没有任何可以实际产生信号、用于回测验证的正式策略实现。MACD 是仓库文档中已经沉淀过的经典趋势策略，规则清晰、参数少、容易程序化，适合作为首个正式策略能力，用来打通“行情输入 -> 指标计算 -> 买卖信号 -> 仓位输出 -> 回测验证”的最小闭环。

## What Changes

- 新增 `macd-strategy` capability，定义 MACD 趋势策略的输入、指标计算、信号规则、参数配置和输出约束。
- 在 `src/strategies/trend/` 下落地 MACD 策略实现，基于现有 `BaseStrategy` 接口生成交易信号和目标仓位。
- 为 MACD 策略补充最小可复现的测试数据与测试用例，验证金叉、死叉、零轴过滤和缺失数据处理等关键行为。
- 为策略提供可用于研究或回测的调用入口，确保后续能与回测模块或脚本顺利衔接。

## Capabilities

### New Capabilities
- `macd-strategy`: 定义基于 EMA 快慢线、信号线和可选趋势过滤条件的 MACD 趋势策略能力。

### Modified Capabilities
- None.

## Impact

- Affected code: `src/strategies/base.py`, `src/strategies/trend/`, `tests/`, 以及可能新增的 `scripts/` 或 `src/factors/` 辅助模块。
- Affected systems: 策略信号生成、参数配置、最小回测/研究调用链路。
- Dependencies: 可能需要依赖 `pandas` 或现有数据表结构来完成时间序列指标计算。
