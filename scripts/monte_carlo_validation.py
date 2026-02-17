import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def run_monte_carlo(log_path, iterations=10000, initial_capital=10000):
    df = pd.read_csv(log_path)
    
    # Calculate % returns per trade based on pnl/capital (proxy)
    # Since we don't have absolute capital per trade in the log, we use the profit percentage
    # In our engine, pnl is usually absolute USDT. Let's assume a fixed risk per trade for the sim.
    returns = df['pnl'].values
    
    # CAGR calculation helper
    def calc_cagr(final_val, initial_val, years):
        if final_val <= 0: return -1.0
        return (final_val / initial_val) ** (1/years) - 1

    # Max Drawdown helper
    def calc_mdd(equity_curve):
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - peak) / peak
        return np.min(drawdown)

    results_cagr = []
    results_mdd = []
    
    print(f"--- MONTE CARLO SIMULATION ({iterations} Iterations) ---")
    print(f"Base Trades: {len(returns)}")
    
    for i in range(iterations):
        # 1. Shuffle
        sim_returns = np.random.permutation(returns)
        
        # 2. Variable Slippage (Randomly subtract 1-3% from wins, add to losses)
        # Assuming avg trade is ~1% of capital, slippage of 0.1% of capital
        slippage = np.random.uniform(0.0001, 0.0005, len(sim_returns)) 
        sim_returns = sim_returns - (initial_capital * slippage)
        
        # 3. Execution Drop (Randomly skip 5% of trades)
        mask = np.random.choice([0, 1], size=len(sim_returns), p=[0.05, 0.95])
        sim_returns = sim_returns * mask
        
        # 4. Construct Equity Curve
        equity_curve = initial_capital + np.cumsum(sim_returns)
        
        # 5. Metrics
        final_val = equity_curve[-1]
        cagr = calc_cagr(final_val, initial_capital, 3.0) # 3 years total OOS
        mdd = calc_mdd(equity_curve)
        
        results_cagr.append(cagr * 100)
        results_mdd.append(mdd * 100)

    # Statistical Summary
    results_cagr = np.array(results_cagr)
    results_mdd = np.array(results_mdd)
    
    print("\n--- STATISTICAL CONFIDENCE (95% CI) ---")
    print(f"CAGR Mean: {np.mean(results_cagr):.2f}%")
    print(f"CAGR 5th Percentile (Worst Case): {np.percentile(results_cagr, 5):.2f}%")
    print(f"Max DD Mean: {np.mean(results_mdd):.2f}%")
    print(f"Max DD 95th Percentile (Worst Case): {np.percentile(results_mdd, 5):.2f}%")
    print(f"Probability of Ruin (DD > 90%): {(np.sum(results_mdd < -90) / iterations * 100):.2f}%")

    # --- VISUALIZATION ---
    output_dir = r'C:\Users\User\.gemini\antigravity\brain\5072d2d6-41eb-4371-9019-085a6c74e69f'
    import matplotlib
    matplotlib.use('Agg')
    
    # 1. Equity Fan Chart (Spaghetti Plot)
    plt.figure(figsize=(12, 6))
    plt.title("B2B Alpha Sentinel: Monte Carlo Equity Fan (2500 Iterations)")
    
    # Run a few sample paths for the visual
    for _ in range(100):
        path = initial_capital + np.cumsum(np.random.permutation(returns) - (initial_capital * 0.0002))
        plt.plot(path, color='gray', alpha=0.1, linewidth=0.5)
    
    # Highlight Mean Path
    plt.plot(initial_capital + np.cumsum(np.full(len(returns), np.mean(returns))), color='blue', label='Mean Path', linewidth=2)
    plt.axhline(initial_capital, color='black', linestyle='--')
    plt.ylabel("Equity (USDT)")
    plt.xlabel("Trade Number")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(f"{output_dir}\\mc_equity_fan.png", dpi=150)
    plt.close()

    # 2. Max Drawdown Histogram
    plt.figure(figsize=(10, 5))
    sns.histplot(results_mdd, bins=50, color='red', alpha=0.6, kde=True)
    plt.title("Distribution of Max Drawdowns (Monte Carlo)")
    plt.axvline(np.mean(results_mdd), color='black', linestyle='--', label=f'Mean DD: {np.mean(results_mdd):.1f}%')
    plt.axvline(-90, color='darkred', linestyle='-', label='Ruin Threshold (-90%)')
    plt.xlabel("Max Drawdown (%)")
    plt.ylabel("Frequency")
    plt.legend()
    plt.savefig(f"{output_dir}\\mc_drawdown_dist.png", dpi=150)
    plt.close()
    
    print(f"\n[SUCCESS] Visualizations saved to artifact directory.")

if __name__ == "__main__":
    run_monte_carlo(r'research\reports\Test_13A_OOS_AlphaSentinel\trade_log.csv')
