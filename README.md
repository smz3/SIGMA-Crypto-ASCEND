# SIGMA-Crypto-ASCEND 🚀

A professional-grade quantitative strategy engine for Crypto Perpetuals, porting the proprietary **Sigma B2B** fractal logic from MQL5 to a vectorized Python environment.

## 🏛 Architecture
- **`core/`**: Alpha Engine (B2B Detectors, Russian Doll Filters).
- **`data/`**: CCXT-based ingestion for Binance Futures (Price, Funding, Liquidations).
- **`simulation/`**: Custom Vectorized Backtester with walk-forward analysis.
- **`dashboard/`**: Live monitoring via [SIGMA Quant](https://sigma-quant.pages.dev) (Next.js).

## 🧪 Methodology: "First Principles Quant"
This strategy exploits **Microstructure Inefficiency** and **Liquidity Stress**. We focus on:
1. **Extreme Funding Z-Scores** (Crowded Trade detection).
2. **Liquidation Cluster Sweeps** (Forced counter-party liquidity).
3. **Multi-Timeframe Fractal Alignment** (Macro-to-Micro shielding).

---
*Created for the ASCEND Quant Researcher Strategy Builder interview.*
