# Failure Modes: SIGMA-Crypto-ASCEND

To establish institutional-grade rigor, we must document where the strategy breaks.

### 1. Systemic Infinite-Expansion (The "Black Hole")
In events like the FTX collapse, delta-neutrality breaks. Liquidation flushes do not mean-revert; they lead to logarithmic expansion.
**Mitigation**: Hard Circuit-Breaker based on Volatility-Z-Score limits.

### 2. Low-Volatility Funding Bleed
If funding remains high but the market enters a low-volatility "drift" phase, the cost of carry (funding payments) will eventually erode the alpha of any subsequent mean-reversion.
**Mitigation**: Time-based exit or dynamic funding-adjustment threshold.

### 3. Stop-Hunt "Deep Wicks" (Microstructure Noise)
In lower-liquidity pairs, "wicks" can extend beyond the predicted liquidation cluster, hitting our hard Stop-Loss before the reversal occurs.
**Mitigation**: ATR-based SL buffers rather than fixed-price levels.
