"""
SIGMA Result Analyzer
Computes performance statistics from a trades DataFrame.
Compatible with the BacktestSummary type in the SIGMA Quant dashboard.
"""
import numpy as np
import pandas as pd
from typing import Optional


def compute_statistics(trades_df: pd.DataFrame, starting_balance: float = 100_000) -> dict:
    if trades_df.empty:
        return _empty_stats()

    pnl = trades_df['pnl_money'].values
    r_multiples = trades_df['r_multiple'].values if 'r_multiple' in trades_df.columns else np.zeros(len(pnl))

    total = len(pnl)
    wins = int(np.sum(pnl > 0))
    losses = total - wins
    win_rate = wins / total if total > 0 else 0.0

    net_profit = float(np.sum(pnl))
    final_equity = starting_balance + net_profit
    gross_profit = float(np.sum(pnl[pnl > 0])) if wins > 0 else 0.0
    gross_loss = float(np.abs(np.sum(pnl[pnl < 0]))) if losses > 0 else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

    avg_win = gross_profit / wins if wins > 0 else 0.0
    avg_loss = gross_loss / losses if losses > 0 else 0.0
    expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
    avg_r = float(np.mean(r_multiples)) if len(r_multiples) > 0 else 0.0

    equity_curve = starting_balance + np.cumsum(pnl)
    running_max = np.maximum.accumulate(equity_curve)
    drawdowns = (equity_curve - running_max) / running_max
    max_dd_pct = float(np.min(drawdowns)) if len(drawdowns) > 0 else 0.0
    max_dd_abs = float(np.min(equity_curve - running_max)) if len(drawdowns) > 0 else 0.0

    daily_returns = pnl / starting_balance
    volatility = float(np.std(daily_returns) * np.sqrt(252)) if len(daily_returns) > 1 else 0.0
    sharpe = _sharpe_ratio(daily_returns)
    sortino = _sortino_ratio(daily_returns)
    calmar = net_profit / abs(max_dd_abs) if max_dd_abs != 0 else 0.0
    recovery = net_profit / abs(max_dd_abs) if max_dd_abs != 0 else 0.0

    kelly = win_rate - ((1 - win_rate) / (avg_win / avg_loss)) if avg_loss > 0 and avg_win > 0 else 0.0

    return {
        'total_trades': total,
        'wins': wins,
        'losses': losses,
        'win_rate': round(win_rate * 100, 2),
        'net_profit': round(net_profit, 2),
        'net_profit_pct': round(net_profit / starting_balance * 100, 2),
        'final_equity': round(final_equity, 2),
        'profit_factor': round(profit_factor, 4),
        'expectancy': round(expectancy, 2),
        'average_r': round(avg_r, 4),
        'max_drawdown': round(max_dd_abs, 2),
        'max_drawdown_pct': round(max_dd_pct * 100, 2),
        'sharpe_ratio': round(sharpe, 4),
        'sortino_ratio': round(sortino, 4),
        'calmar_ratio': round(calmar, 4),
        'recovery_factor': round(recovery, 4),
        'volatility': round(volatility, 4),
        'kelly_fraction': round(kelly, 4),
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'largest_win': round(float(np.max(pnl)), 2) if total > 0 else 0.0,
        'largest_loss': round(float(np.min(pnl)), 2) if total > 0 else 0.0,
        'avg_mae': round(float(trades_df['mae_points'].mean()), 2) if 'mae_points' in trades_df.columns else 0.0,
        'avg_mfe': round(float(trades_df['mfe_points'].mean()), 2) if 'mfe_points' in trades_df.columns else 0.0,
    }


def compute_grouped_stats(trades_df: pd.DataFrame, group_col: str) -> dict:
    if trades_df.empty or group_col not in trades_df.columns:
        return {}

    result = {}
    for name, group in trades_df.groupby(group_col):
        pnl = group['pnl_money'].values
        total = len(pnl)
        wins = int(np.sum(pnl > 0))
        r_vals = group['r_multiple'].values if 'r_multiple' in group.columns else np.zeros(total)

        result[str(name)] = {
            'count': total,
            'wins': wins,
            'losses': total - wins,
            'win_rate': round(wins / total * 100, 2) if total > 0 else 0.0,
            'pnl': round(float(np.sum(pnl)), 2),
            'avg_r': round(float(np.mean(r_vals)), 4),
        }

    return result


def print_report(stats: dict, trades_df: pd.DataFrame = None) -> None:
    print("\n" + "=" * 60)
    print("  SIGMA B2B Crypto Backtest Report")
    print("=" * 60)
    print(f"  Total Trades:    {stats['total_trades']}")
    print(f"  Win Rate:        {stats['win_rate']:.1f}%")
    print(f"  Net Profit:      ${stats['net_profit']:,.2f} ({stats['net_profit_pct']:+.1f}%)")
    print(f"  Profit Factor:   {stats['profit_factor']:.2f}")
    print(f"  Avg R-Multiple:  {stats['average_r']:.2f}")
    print(f"  Max Drawdown:    ${stats['max_drawdown']:,.2f} ({stats['max_drawdown_pct']:.1f}%)")
    print(f"  Sharpe Ratio:    {stats['sharpe_ratio']:.2f}")
    print(f"  Sortino Ratio:   {stats['sortino_ratio']:.2f}")
    print(f"  Kelly Fraction:  {stats['kelly_fraction']:.2f}")
    print("=" * 60)

    if trades_df is not None and not trades_df.empty:
        if 'session' in trades_df.columns:
            print("\n  By Session:")
            for name, grp_stats in compute_grouped_stats(trades_df, 'session').items():
                print(f"    {name:10s}: {grp_stats['count']:3d} trades | WR: {grp_stats['win_rate']:5.1f}% | PnL: ${grp_stats['pnl']:>10,.2f}")

        if 'zone_tf' in trades_df.columns:
            print("\n  By Zone TF:")
            for name, grp_stats in compute_grouped_stats(trades_df, 'zone_tf').items():
                print(f"    {name:10s}: {grp_stats['count']:3d} trades | WR: {grp_stats['win_rate']:5.1f}% | PnL: ${grp_stats['pnl']:>10,.2f}")

    print()


def _sharpe_ratio(returns: np.ndarray, risk_free: float = 0.0, periods: int = 252) -> float:
    if len(returns) < 2:
        return 0.0
    excess = returns - risk_free / periods
    std = np.std(excess, ddof=1)
    if std < 1e-10:
        return 0.0
    return float(np.mean(excess) / std * np.sqrt(periods))


def _sortino_ratio(returns: np.ndarray, risk_free: float = 0.0, periods: int = 252) -> float:
    if len(returns) < 2:
        return 0.0
    excess = returns - risk_free / periods
    downside = returns[returns < 0]
    down_std = np.std(downside, ddof=1) if len(downside) > 1 else 1e-10
    if down_std < 1e-10:
        return 0.0
    return float(np.mean(excess) / down_std * np.sqrt(periods))


def _empty_stats() -> dict:
    return {k: 0 for k in [
        'total_trades', 'wins', 'losses', 'win_rate', 'net_profit', 'net_profit_pct',
        'final_equity', 'profit_factor', 'expectancy', 'average_r', 'max_drawdown',
        'max_drawdown_pct', 'sharpe_ratio', 'sortino_ratio', 'calmar_ratio',
        'recovery_factor', 'volatility', 'kelly_fraction', 'avg_win', 'avg_loss',
        'largest_win', 'largest_loss', 'avg_mae', 'avg_mfe',
    ]}
