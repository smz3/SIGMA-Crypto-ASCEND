---
name: SIGMA B2B MQL5→Python Port
description: End-to-end porting guide for the SIGMA V5.0 MT5 trading system to Python-native crypto. Interview project for Crypto Quant Researcher role at ASCEND.
---

# SIGMA B2B: MQL5 V5.0 → Python Native Port

## Project Context

This is an **end-to-end Crypto Quant Researcher interview project** for ASCEND. We are porting our production MT5 algorithmic trading system (SIGMA V5.0) from MQL5 to Python-native, targeting **BTCUSDT Perpetual Futures**. The goal is to demonstrate:

1. Full quantitative pipeline mastery (data → detection → backtest → statistics → **execution** → visualization)
2. Institutional-grade code structure and documentation
3. Domain transfer capability (Gold/FX → Crypto)
4. Live execution capability (paper trading / signal generation demo)

## Source Architecture (MQL5 V5.0)

All MQL5 source files live in: `MQL5/Include/V5.0/`

```
MQL5/Include/V5.0/
├── Data/
│   ├── Structures.mqh          ← ALL data structures (SwingPointInfo, B2BZoneInfo, etc.)
│   ├── QuantLogger.mqh         ← Trade logging for quant analysis
│   ├── QuantTypes.mqh          ← Quant-specific type definitions
│   ├── DataExporter.mqh        ← CSV/data export for analysis
│   ├── ZonePersistence.mqh     ← Zone save/load across sessions
│   └── Quant_4.0/              ← STRATEGY DOCTRINE LIBRARY (18 docs)
│       ├── strategy_v5.0.md        ← Conscious Hierarchy + Storyline Memory
│       ├── origin_magnet_v2.md     ← Fixed-Role Origin-Magnet Model
│       ├── README_FFT_Logic.md     ← 3 Levels of Trap Selection
│       ├── strategy_V5.6_trap_liberation.md ← Strict→Free Flow→Discovery
│       ├── README_StrategyOrchestrator_V5.8_Audit.md ← Block-by-block audit
│       ├── README_V5.9_Fractal_Hierarchy.md ← 3-Tier Recursive Engine
│       ├── strategy_V5.8_D1_Magnet_Fade_Optimizations.md
│       ├── strategy_V5.7_FFT_Optimizations.md
│       ├── fractal_flow_analysis.md
│       ├── fractal_flow_design.md
│       └── ... (18 total strategy docs)
│
├── Detection/                  ← CORE DETECTION PIPELINE
│   ├── SwingPointDetector.mqh  ← Swing high/low detection (close-based)
│   ├── RawBreakoutDetector.mqh ← Breakout detection + L2 impulse swing
│   ├── B2BDetector.mqh         ← 5-Pointer B2B zone detection engine
│   ├── B2BZoneStatus.mqh       ← Zone touch tracking (T1/T2/T3) + invalidation
│   ├── B2BZoneManager.mqh      ← Zone CRUD, dedup, pruning, consolidation
│   ├── B2BConfluence.mqh       ← Parent-child zone hierarchy (Russian Doll)
│   └── B2BTradeTracker.mqh     ← Per-zone trade lifecycle tracking
│
├── Configuration/
│   └── TradingParameters.mqh   ← ALL input parameters (centralized)
│
├── Common/
│   ├── Defines.mqh             ← Enums (SwingType, SignalDirection, etc.)
│   ├── CircularBuffer.mqh      ← Generic circular buffer template
│   ├── Utils.mqh               ← Utility functions (FindBarIndexByTime, etc.)
│   ├── PerformanceUtils.mqh    ← Performance monitoring
│   └── UniversalSymbolManager.mqh ← Symbol handling
│
├── Trading/
│   ├── StrategyOrchestrator.mqh ← Master orchestrator (flow/narrative logic)
│   ├── RiskManager.mqh          ← Position sizing, Kelly, risk gates
│   ├── OrderManager.mqh         ← Order execution, modification, closing
│   ├── TradeSignalGenerator.mqh ← Signal validation and filtering
│   └── TrailingStopManager.mqh  ← Trailing stop management
│
├── System/
│   └── TimeFrameManager.mqh    ← Multi-timeframe data management
│
├── Analysis/
│   └── MetricCalculator.mqh    ← Performance metrics (Sharpe, Sortino, etc.)
│
├── Communication/
│   └── TelegramBot.mqh         ← Alert notifications
│
├── UI/
│   └── FeedbackPanel.mqh       ← On-chart visual panel
│
└── Visualization/
    └── Visualizer.mqh          ← Zone drawing on chart
```

## Strategy Doctrine Library (Quant_4.0)

The `Data/Quant_4.0/` directory contains **18 strategy documents** that define the complete trading philosophy. These are the "brain" of the system.

### Core Strategy: Conscious Hierarchy + Storyline Memory (V5.0)

The market is modeled as a **battlefield** with 3 authority tiers:
- **MN1 (The Tide):** Invincible momentum. Bulldozes minor obstacles.
- **W1 (The Wave):** Structural swing. Rides the tide but respects local resistance.
- **D1 (The Path):** Execution route. Must be clear of roadblocks.

**Storyline Memory (Siege Persistence):** Once an Origin/Magnet pair is locked, the narrative persists until:
1. **VICTORY** — Magnet T3 (L2) touched → Promote latest Outpost to new Origin
2. **DEFEAT** — Origin L2 broken → Reset to vacuum

### Origin-Magnet Model (V2.0)

| Concept | Definition |
|---|---|
| **Origin** | Zone where price most recently bounced FROM (Point A, WITH-TREND) |
| **Magnet** | First opposing zone ahead of price (Point B, the target) |
| **Outpost** | New same-direction zone formed during trend (forward base) |
| **Roadblock** | Opposing zone that may block the path |

Roles are **FIXED** — they only change on new structure formation, zone invalidation, or full retracement completion. Touching a zone does NOT swap roles.

The **Fractal Cascade** nests each timeframe's Origin-Magnet within the higher:
```
MN1: Origin @ 1500 (BUY) ──────────► Magnet @ 1700 (SELL)
     │
     │  W1: Origin @ 1520 ──────► Magnet @ 1650
     │       │
     │       │  D1: Origin @ 1530 ──► Magnet @ 1620
     │       │       │
     │       │       │  H4/H1/M30: Traps (execution)
```

### 3 Levels of Trap Selection (FFT Logic)

| Level | Mode | Requirement | Targeting | Goal |
|---|---|---|---|---|
| **1** | **Strict** | Nested inside Origin L1-L2 | Magnet L1/L2 | Defensive Entry |
| **2** | **Free Flow** | Post-Outpost Touch only | Magnet L1/L2 | Momentum Chase |
| **3** | **Discovery** | Post-Outpost + No Magnet | Trailing Stop (TP=0) | Blue Sky Extraction |

**Freshness Rule:** Trap must be created AFTER the narrative zone was TOUCHED. `Trap.CreatedTime > NarrativeZone.L1_TouchTime`. Prevents "catching falling knives."

### Trap Liberation (V5.6)

**Phase 1 (Strict):** `outpost_id == 0` → Trap MUST be spatially nested inside Origin.
**Phase 2 (Liberation):** `outpost_id > 0` → Spatial check skipped, only freshness required.
**Constraint:** Free Flow is BLOCKED if Magnet is fading (50%/L2 touched) and Siege is OFF.
**Override:** Siege Mode ignores the runway check ("Bulldozer").

**Global Fade Awareness (V5.6.3):** Before ANY free trap, scan ALL higher timeframes for active fades. If a superior TF has its "Shield Up" (Magnet fading), ALL inferior TF free traps are GROUNDED.

### V5.8 Audit — The Validation Gauntlet

A trade only fires when 3 gates pass simultaneously:
1. **State Engine** → Clear Origin-Target path identified
2. **Location Filter** → `IsInsideOpposingZone()` confirms no roadblock (with Bulldozer override)
3. **Validation Gauntlet** → Freshness (Relative Baseline) + Spatial Integrity (Nesting/Liberation)

Key blocks in `StrategyOrchestrator.mqh`:
- **`UpdateTimeframeFlow()`** — Core narrative engine managing Origin→Magnet lifecycle
- **`GetLatestOutpost()`** — Linear successor selection (V5.6.4 zombie prevention)
- **`IsInsideOpposingZone()`** — Defensive location filter with Bulldozer bypass
- **`ValidateTrap()`** — Freshness Guard + Global Shield + Liberation Check
- **`IsTradeAllowed()`** — Hierarchy loop: Global Siege → Handover → Authority Tiers → Magnet Fades

### V5.9 Fractal Hierarchy — 3-Tier Recursive Engine

| Tier | Category | Timeframes | Role |
|---|---|---|---|
| **Tier 1** | Macro Generals | MN1, W1, D1 | Strategy: Global bias + hunting grounds |
| **Tier 2** | Micro Officers | H4, H1, M30 | Timing: Session cycles + discovery map |
| **Tier 3** | Precision Snipers | M15, M5, M1 | Execution: Structural wick triggers |

**Chain of Trust:** A Sniper doesn't check the General; it only trusts its immediate Officer. Symmetric recursive handshake at each level.

### Execution Matrix

| Flow | Authority | Roadblocks Checked | Trap Requirement | TP Target |
|---|---|---|---|---|
| **MN1** | High | W1, MN1 | Fresh H4/H1/M30 inside W1/MN1 Origin | MN1 Magnet L1 |
| **W1** | Medium | D1, W1, MN1 | Fresh H4/H1/M30 inside W1 Origin | W1 Magnet L1 |
| **D1** | Low | D1, W1, MN1 | Fresh H4/H1/M30 inside D1 Origin | D1 Magnet L1 |

---

## Trading Engine Reference (MQL5)

The `Trading/` folder contains 5 modules that handle everything from narrative interpretation to order execution.

### StrategyOrchestrator.mqh (39KB, 789+ lines)
**The Brain.** Master orchestrator that manages market narrative across MN1/W1/D1.

**Key Data Structures:**
- `FlowState` — Origin/Magnet/Outpost IDs, touch tracking, siege flags, safety triggers per TF
- `TrapState` — Signal-specific data (price, SL, TP, authorization status)

**Core Functions:**
| Function | Lines | Purpose |
|---|---|---|
| `Orchestrate()` | L137-141 | Entry point, triggers state update every tick |
| `UpdateFlowState()` | L143-163 | Heartbeat — loops MN1→W1→D1, generates storyline log |
| `UpdateTimeframeFlow()` | L165-350 | **Most critical block.** Manages Origin→Magnet lifecycle: persistence/defeat, successor logic, outpost tracking, siege trigger, vacuum/origin search |
| `GetLatestOutpost()` | L351-397 | Strict linear successor search (V5.6.4 zombie prevention) |
| `IsInsideOpposingZone()` | L400-444 | Location filter + Bulldozer Mode bypass |
| `ValidateTrap()` | L454-529 | Freshness Guard → Global Shield → Liberation Check |
| `IsTradeAllowed()` | L532-789 | **Decision engine.** Hierarchy loop → authority tiers → magnet fades |

### TradeSignalGenerator.mqh (17KB, 398 lines)
**The Scanner.** Single-pass trigger scanner across all execution timeframes.

**Architecture:**
1. Scans zones backwards to find best Buy/Sell candidates per TF (H4/H1/M30/M15/M5/M1)
2. Asks `StrategyOrchestrator.IsTradeAllowed()` for authorization
3. Evaluates metrics (SL distance, anchor distance) for filtering
4. Fires the winner through `OrderManager.ExecuteSignal()`

**Key Flow:** Zone Discovery → `IsTradeAllowed()` gate → `CalculateRiskBasedLot()` → `ExecuteSignal()`

### OrderManager.mqh (21KB, 565 lines)
**The Executor.** Handles all order placement with strict deduplication.

**Key Functions:**
| Function | Purpose |
|---|---|
| `ExecuteSignal()` | Places BUY/SELL with formatted comment: `{TF}#{ZoneID}_T{Tier}_{ParentTF}#{OriginID}` |
| `TradeExistsForZone()` | Scans open positions for `#{ZoneID}_` marker + tier code (T1/T2/T3) to prevent duplicate entries |
| `IsWithinChaosWindow()` | Time-based filter (Beta 1) |

**Comment Format:** `M30#3352_T1_D1#2862` → M30 zone 3352, T1 entry, authorized by D1 origin 2862

### RiskManager.mqh (15KB, 414 lines)
**The Gatekeeper.** Position sizing and risk gates.

**Core Formula:** `Lot Size = (Balance × Risk% × Position%) / (SL_Pips × Pip_Value)`

**Safety Gates:**
- Max open positions cap (`InpMaxOpenPositions = 200`)
- Min margin level check (`InpMinMarginLevel = 150%`)
- Max lot cap (`InpMaxLotsPerTrade = 100.0`)
- Min SL distance clamp (5 pips safety floor)
- Daily drawdown limit tracking

**Key Parameters:**
| Input | Default | Description |
|---|---|---|
| `InpBaseRisk` | 1.0% | Risk per trade |
| `InpMaxLotsPerTrade` | 100.0 | Absolute lot ceiling |
| `InpMaxOpenPositions` | 200 | Position count limit |
| `InpMinMarginLevel` | 150% | Margin safety threshold |

### TrailingStopManager.mqh (15KB, 395 lines)
**The Protector.** Break-even + milestone-based trailing stops.

**Two-Phase Protection:**
1. **Break-Even (BE):** When profit reaches `InpBEActivationPoints`, SL moves to entry + `InpBELockInPoints`
2. **Trailing Stop:** After BE, SL trails behind price by `InpTrailStepPoints` with milestone checkpoints

**Physics Gate:** Position must breach next milestone price before any SL modification. Prevents tick-spamming.

**Key Parameters:**
| Input | Description |
|---|---|
| `InpBEActivationPoints` | Points in profit to trigger break-even |
| `InpBELockInPoints` | Points locked in above entry |
| `InpTrailStartPoints` | Points before trailing begins |
| `InpTrailStepPoints` | Step distance for trailing SL |

---

## Target Architecture (Python)

All Python code lives in: `SIGMA-Crypto-ASCEND/`

```
SIGMA-Crypto-ASCEND/
├── core/
│   ├── models/
│   │   ├── __init__.py
│   │   └── structures.py       ← Port of Structures.mqh + Defines.mqh
│   └── detectors/
│       ├── __init__.py
│       ├── swing_points.py     ← Port of SwingPointDetector.mqh
│       ├── breakouts.py        ← Port of RawBreakoutDetector.mqh
│       ├── b2b_engine.py       ← Port of B2BDetector.mqh (5-Pointer)
│       └── zone_status.py      ← Port of B2BZoneStatus.mqh
│
├── simulation/
│   ├── engine/
│   │   └── vectorized_backtester.py ← Replaces StrategyTester + OrderManager
│   └── backtest/
│       └── result_analyzer.py   ← Port of MetricCalculator.mqh
│
├── scripts/
│   ├── data_fetcher.py         ← Multi-exchange OHLCV fetcher (MEXC/Kraken)
│   └── supabase_push.py        ← Push results to Supabase for dashboard
│
├── config/
│   ├── defaults.yaml           ← Port of TradingParameters.mqh
│   └── exchange_config.yaml    ← Exchange connection settings
│
├── tests/
│   └── test_detector.py        ← Unit tests for detection pipeline
│
└── data/
    └── raw/                    ← OHLCV parquet files
```

## Module-by-Module Mapping

### MUST PORT (Core Pipeline)

| MQL5 Source               | Python Target                     | Status    | Notes |
|---                        |---                                |---        |---    |
| `Structures.mqh`          | `core/models/structures.py`       | ✅ Done    | SwingPointInfo, B2BZoneInfo, DetectionConfig, DetectionContext |
| `Defines.mqh`             | `core/models/structures.py`       | ✅ Done    | SwingType, SignalDirection enums |
| `SwingPointDetector.mqh`  | `core/detectors/swing_points.py`  | ✅ Done    | Close-based swing detection |
| `RawBreakoutDetector.mqh` | `core/detectors/breakouts.py`     | ✅ Done    | Breakout + L2 impulse swing |
| `B2BDetector.mqh`         | `core/detectors/b2b_engine.py`    | ✅ Done    | 3-pass 5-pointer detection |
| `B2BZoneStatus.mqh`       | `core/detectors/zone_status.py`   | ✅ Done    | T1/T2/T3 touch + invalidation |
| `TradingParameters.mqh`   | `config/defaults.yaml`            | ✅ Done    | Detection + backtest params |
| `MetricCalculator.mqh`    | `simulation/backtest/result_analyzer.py` | ✅ Done    | Sharpe/Sortino/Kelly/PF |

### SHOULD PORT (Day 3 — Confluence + Multi-TF)

| MQL5 Source           | Python Target                     | Status     | Notes |
|---                    |---                                |---          |---    |
| `B2BConfluence.mqh`   | `core/detectors/confluence.py`    | ✅ Done    | Parent-child zone hierarchy   |
| `B2BZoneManager.mqh`  | `core/detectors/zone_manager.py`  | ✅ Done    | Dedup, pruning, consolidation |
| `TimeFrameManager.mqh`| `core/system/timeframe_mgr.py`    | ✅ Done    | Multi-TF data orchestration   |

### NOT PORTING (MT5-Specific / Simplified in Python)

| MQL5 Source           | Reason | How It's Handled in Python |
|---|---|---|
| `StrategyOrchestrator.mqh` | Complex narrative logic (789+ lines) | Simplified: `vectorized_backtester.py` uses zone touches directly. Full port is a future iteration. |
| `TradeSignalGenerator.mqh` | Single-pass zone scanner | Simplified: backtester scans zones sequentially, no tick-by-tick evaluation |
| `OrderManager.mqh` | Live MT5 order execution | Replaced by simulated fills in `vectorized_backtester.py` |
| `RiskManager.mqh` | Position sizing + margin checks | Simplified: fixed R-multiple sizing in backtester |
| `TrailingStopManager.mqh` | Break-even + milestone trailing | Not needed for fixed-TP backtest; future R-multiple trailing |
| `CircularBuffer.mqh` | MQL5 template container | Python lists suffice |
| `Utils.mqh` | `FindBarIndexByTime`, helpers | Integrated inline in Python modules |
| `TelegramBot.mqh` | Alert notifications | Not needed for interview |
| `FeedbackPanel.mqh` | MT5 on-chart UI | Replaced by SIGMA Quant dashboard |
| `Visualizer.mqh` | Chart zone drawing | Replaced by SIGMA Quant dashboard |
| `ZonePersistence.mqh` | Zone save/load across sessions | Not needed for single-run backtest |
| `QuantLogger.mqh` | Trade logging | Python logging suffices |
| `DataExporter.mqh` | CSV export | Built into backtester + Parquet |
| `PerformanceUtils.mqh` | Performance monitoring | Python profiling (cProfile) |
| `UniversalSymbolManager.mqh` | Multi-symbol handling | Single-symbol (BTCUSDT) |
| `B2BTradeTracker.mqh` | Per-zone trade lifecycle | Built into backtester |

## Doctrinal Rules (NEVER VIOLATE)

### 1. Close-Based Swing Detection
```
MQL5: IsSwingHigh uses candidate_bar.close comparison
Python: detect_swings() uses df['close'] — NOT high/low prices
```
Swings are detected by comparing the **close price** of the center bar against surrounding bars. This is the MT5 production logic. A previous SciPy implementation incorrectly used high/low — that was wrong.

### 2. The 5-Pointer B2B Pattern

**SELL Zone Pattern:**
```
P1 (Swing High) → P2 (Swing Low) → P3 (Swing High, LOWER than P1)
P5 (older Swing Low, price < P2) → P4 (bar that closes below P5)
Zone: L1 = P2.price (entry level), L2 = max(P1, P3).price (stop level)
```

**BUY Zone Pattern:**
```
P1 (Swing Low) → P2 (Swing High) → P3 (Swing Low, HIGHER than P1)
P5 (older Swing High, price > P2) → P4 (bar that closes above P5)
Zone: L1 = P2.price (entry level), L2 = min(P1, P3).price (stop level)
```

### 3. Zone Touch Hierarchy
- **T1 (L1 Touch):** Wick touches L1 → zone becomes tradeable
- **T2 (50% Touch):** Wick reaches midpoint → deeper engagement
- **T3 (L2 Touch):** Wick hits L2 → deepest touch before invalidation
- **Invalidation:** Close THROUGH L2 → zone is dead (bulldozed)

Key distinction: **Touch detection uses High/Low (wicks)**. **Invalidation uses Close price only.**

### 4. Swing Usage Deduplication
A swing can only participate in ONE zone per direction. The `IsSwingUsedInZones()` check prevents the same structural point from being reused, maintaining zone integrity.

### 5. P5 Deduplication
When multiple candidates share the same P5 anchor, keep only the **freshest** (highest `p1_idx`). This mirrors the MT5 logic of preferring the most recent structural pattern.

### 6. Zone ID Generation
Zone IDs are deterministic hashes of `(L1, L2, timeframe, direction, creation_time)`. Same zone always gets same ID regardless of session.

## Detection Config Parameters

Mapped from `TradingParameters.mqh`:

| MQL5 Input | Python Config | Default | Description |
|---|---|---|---|
| `InpHistoricalBars` | `historical_bars` | 5000 | Initial bar load per TF |
| `InpQuantMinAgeBars` | `min_age_bars` | 8 | Min bars for zone validation |
| `InpMaxZoneAgeBars` | `max_zone_age_bars` | 5000 | Max zone lifetime |
| `InpBaseRisk` | `base_risk_pct` | 1.0 | Risk % per trade |
| (Swing window) | `swing_window` | 3 | Odd integer, bars each side |
| (Swing lookback) | `swing_lookback` | 20 | Historical scan depth |
| `InpMaxBreakoutAge` | `max_breakout_age` | 0 | Max breakout age (0=unlimited) |

## Timeframe Hierarchy

```python
TF_HIERARCHY = ['MN1', 'W1', 'D1', 'H4', 'H1', 'M30', 'M15', 'M5', 'M1']
TF_RANK = {'MN1': 0, 'W1': 1, 'D1': 2, 'H4': 3, 'H1': 4, 'M30': 5, 'M15': 6, 'M5': 7, 'M1': 8}
```

- **Narrative TFs:** MN1, W1, D1 (determine trade direction)
- **Control TFs:** H4, H1 (zone confluence)
- **Entry TFs:** M15, M5, M1 (execution timing)

A zone at D1 is a **parent** to overlapping zones at H4/H1. Parent must be a HIGHER timeframe (lower rank number).

## Supabase Integration

### Schema (Production — DO NOT MODIFY)

The SIGMA Quant dashboard (Next.js + Supabase) uses these tables:

| Table | Purpose |
|---|---|
| `trades` | All trade records (MT5 + Crypto) |
| `b2b_zones` | Zone snapshots for visualization |
| `strategy_registry` | Strategy config per environment |
| `gps_snapshots` | GPS flow snapshots per trade |
| `gps_flows` | GPS flow lifecycle records |

### Data Separation Strategy

The `environment` column on the `trades` table namespaces data:

- **MT5 data:** `environment = 'LIVE'`, `'BACKTEST'`, etc.
- **Crypto data:** `environment = 'CRYPTO_ASCEND_V1'`

This is a **zero-migration** approach: no schema changes, no interference with existing MT5 data. The SIGMA Quant dashboard auto-discovers environments from the dropdown.

### Safety Rules for Supabase
1. **NEVER run DDL migrations** — schema is production
2. **ONLY INSERT** with `environment = 'CRYPTO_ASCEND_V1'`
3. **NEVER DELETE or UPDATE** rows where `environment != 'CRYPTO_ASCEND_V1'`
4. **Always dry-run first** before pushing to production
5. **Batch inserts** (50 per batch) with dedup by ticket number

### Connection
```python
# Via environment variables (never hardcode)
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']
```

Dashboard: Deployed on Cloudflare Pages. Project: `SIGMA Quant`
Supabase project ID available via MCP server (requires `SUPABASE_ACCESS_TOKEN`).

## Data Pipeline

### Exchange Configuration
- **Primary:** MEXC (accessible from Malaysia)
- **Fallback:** Kraken
- **Symbol:** `BTC/USDT:USDT` (perpetual futures)
- **Timeframes:** 1M, 1w, 1d, 4h, 1h, 30m, 15m, 5m
- **Storage:** Parquet files in `data/raw/`

### Full Pipeline Flow (End-to-End)
```
 1. Fetch OHLCV     → data_fetcher.py
 2. Detect Swings   → swing_points.py
 3. Detect Breaks   → breakouts.py
 4. Detect Zones    → b2b_engine.py
 5. Update Status   → zone_status.py
 6. Backtest        → vectorized_backtester.py
 7. Statistics      → result_analyzer.py
 8. Push Results    → supabase_push.py
 9. Visualize       → SIGMA Quant Dashboard
10. Live Execution  → live_signal_engine.py (paper trading / signal gen)
```

### Execution Demo Architecture
The live execution component demonstrates the complete loop:
- **Signal Engine:** Real-time zone monitoring against live OHLCV feed
- **Paper Trading:** Simulated order fills with position tracking (no real capital)
- **Signal Logging:** Every signal decision logged with full context (zone ID, TF, freshness, authorization chain)
- **Dashboard Sync:** Live signals pushed to Supabase for real-time dashboard visualization

This mirrors the MT5 production flow (`TradeSignalGenerator → StrategyOrchestrator.IsTradeAllowed() → OrderManager.ExecuteSignal()`) but in Python with exchange WebSocket feeds.

## Performance Notes

### Known Bottleneck: Timestamp Conversion
`pd.Timestamp(times[b]).to_pydatetime()` is extremely expensive inside tight loops. Always pre-convert timestamps:

```python
# At entry point of detect_b2b_zones():
py_times = [pd.Timestamp(t).to_pydatetime() for t in df['time'].values]
# Then use py_times[b] in all inner functions
```

This applies to: `b2b_engine.py`, `swing_points.py`, `breakouts.py`

## Testing

All tests are in `tests/test_detector.py`. Run with:
```bash
python -m pytest tests/test_detector.py -v
```

Current status: **16/16 tests passing in 0.59s**

Test categories:
- Swing detection (close-based, window validation)
- Breakout detection (bullish/bearish, swing marking)
- B2B zone detection (sell zones, sessions)
- Zone status (touch tracking, invalidation)
- Full pipeline end-to-end

## Schedule

| Day | Focus | Status |
|---|---|---|
| Day 1 | Core Detection Pipeline | ✅ Complete |
| Day 2 | Data Fetcher + Backtester + Supabase Push | 🔄 In Progress |
| Day 3 | Confluence + Multi-TF + Verification Notebook | ✅ Complete |
| Day 4 | Live Signal Engine + Paper Trading Demo | ⬜ TODO |
| Day 5 | Research Documentation + Failure Modes + Regime Analysis | ⬜ TODO |
