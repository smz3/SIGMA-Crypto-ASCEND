import pandas as pd
import numpy as np
import quantstats as qs
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Patching QuantStats to avoid display issues in some environments
qs.extend_pandas()

def calculate_fractal_metrics(ledger: list) -> pd.DataFrame:
    """
    Parses trade reasons to generate B2B specific alpha metrics.
    "Fractal Edge" Analysis.
    """
    if not ledger: return pd.DataFrame()
    
    metrics = {
        'Total Trades': len(ledger),
        'Win Rate': 0.0,
        'Siege (Bulldozer) WR': 0.0,
        'Magnet Fade WR': 0.0,
        'Handover WR': 0.0,
        'Fractal Consensus WR': 0.0, # MN1=W1=D1
        'MN1 Authority WR': 0.0,
        'D1 Authority WR': 0.0
    }
    
    df = pd.DataFrame([vars(t) for t in ledger])
    
    # Win Rate Helper
    def get_wr(sub_df):
        if sub_df.empty: return 0.0
        wins = sub_df[sub_df['pnl'] > 0]
        return (len(wins) / len(sub_df)) * 100.0

    metrics['Win Rate'] = get_wr(df)
    
    # logic tags are in 'entry_reason' (which maps to 'lifecycle_phase' in signal)
    # Note: Trade object might have 'entry_reason' populated from signal.lifecycle_phase
    
    # 1. Siege / Bulldozer
    siege_trades = df[df['entry_reason'].astype(str).str.contains("Bulldozer", case=False, na=False)]
    metrics['Siege (Bulldozer) WR'] = get_wr(siege_trades)
    
    # 2. Fade
    fade_trades = df[df['entry_reason'].astype(str).str.contains("Fade", case=False, na=False)]
    metrics['Magnet Fade WR'] = get_wr(fade_trades)
    
    # 3. Handover
    handover_trades = df[df['entry_reason'].astype(str).str.contains("Handover", case=False, na=False)]
    metrics['Handover WR'] = get_wr(handover_trades)
    
    # 4. Fractal Authority
    # Based on parent_tf field in logic logs (we need to capture this in Trade object if not already)
    # Assuming 'entry_reason' contains "MN1 Flow", "D1 Flow" etc.
    mn1_trades = df[df['entry_reason'].astype(str).str.contains("MN1", case=False, na=False)]
    d1_trades = df[df['entry_reason'].astype(str).str.contains("D1", case=False, na=False)]
    
    metrics['MN1 Authority WR'] = get_wr(mn1_trades)
    metrics['D1 Authority WR'] = get_wr(d1_trades)

    return pd.DataFrame([metrics])

def plot_trade_overlay(price_data: pd.DataFrame, ledger: list, output_path: str):
    """
    Generates a professional Interactive HTML chart with Trade Markers.
    Style: Small Markers (5px), Dotted Lines for Trade Path.
    """
    print(f"Generating Visual Verification Chart: {output_path}")
    
    if price_data.empty: return
    
    # Resample for visual clarity if data is huge (e.g. 1m data over 3 years is too heavy)
    # We'll stick to H4 for the chart to keep it lightweight but granular enough
    df_plot = price_data.resample('4h').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}).dropna()
    
    fig = go.Figure()
    
    # 1. Price Line (Simple Line is cleaner than Candles for long periods)
    fig.add_trace(go.Scatter(
        x=df_plot.index, y=df_plot['close'],
        mode='lines', name='BTCUSDT Price',
        line=dict(color='#1f77b4', width=1)
    ))
    
    # 2. Trade Markers
    # We process trades one by one to draw the dotted lines
    
    for t in ledger:
        # User Request: 
        # 1. Buy = Green Triangle, Sell = Red Triangle (Regardless of PnL)
        # 2. Only show Trade Path for Winners
        
        is_buy = (str(t.direction) == "BULLISH") or (t.direction == 1)
        
        # Color & Symbol based on DIRECTION
        entry_color = 'green' if is_buy else 'red'
        marker_symbol = 'triangle-up' if is_buy else 'triangle-down'
        
        # Entry Marker
        fig.add_trace(go.Scatter(
            x=[t.open_time], y=[t.entry_price],
            mode='markers', name='Entry',
            marker=dict(symbol=marker_symbol, color=entry_color, size=8), # Size 8 for visibility
            showlegend=False,
            hovertext=f"Entry: {t.entry_reason} | Dir: {t.direction}"
        ))
        
        # Exit Marker (Keep PnL based coloring for Exit to show result?)
        # User didn't specify, but usually Green/Red or Star/X for exit is good.
        # Let's keep Star/X but maybe color matches direction or result?
        # Let's stick to Gold/Red for result differentiation on the Exit itself.
        exit_symbol = 'star' if t.pnl > 0 else 'x'
        exit_color = 'gold' if t.pnl > 0 else 'red' # Exit is Result-based
        
        fig.add_trace(go.Scatter(
            x=[t.close_time], y=[t.exit_price],
            mode='markers', name='Exit',
            marker=dict(symbol=exit_symbol, color=exit_color, size=8),
            showlegend=False,
            hovertext=f"Exit: {t.reason} | PnL: {t.pnl:.2f}"
        ))
        
        # Dotted Line (Path) - ONLY FOR WINNERS
        if t.pnl > 0:
            fig.add_trace(go.Scatter(
                x=[t.open_time, t.close_time],
                y=[t.entry_price, t.exit_price],
                mode='lines',
                line=dict(color=entry_color, width=1, dash='dot'), # Path color matches Entry Direction
                showlegend=False
            ))

    # Add Legend Traces (Invisible traces just for the legend)
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', 
                             marker=dict(symbol='triangle-up', color='green', size=8), name='Buy Entry'))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', 
                             marker=dict(symbol='triangle-down', color='red', size=8), name='Sell Entry'))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', 
                             marker=dict(symbol='star', color='gold', size=8), name='Win Exit'))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', 
                             marker=dict(symbol='x', color='red', size=8), name='Loss Exit'))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', 
                             line=dict(color='gray', width=1, dash='dot'), name='Trade Path'))

    fig.update_layout(
        title="SIGMA V5.9 Strategy - Visual Verification (Trade Path)",
        xaxis_title="Date",
        yaxis_title="Price (USDT)",
        template='plotly_white', # User Request: White Background
        height=800,
        showlegend=True
    )
    
    # Save
    fig.write_html(output_path)
    print(f"Visual Chart saved to {output_path}")

def generate_tearsheet(equity_path: str, output_path: str):
    """
    Generates a professional QuantStats tearsheet from an equity curve.
    """
    print(f"Generating Tearsheet from {equity_path}...")
    
    if not os.path.exists(equity_path):
        print(f"Error: Equity history not found at {equity_path}")
        return

    # 1. Load Equity
    df = pd.read_csv(equity_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    # 2. Resample to Daily to avoid "High Frequency Noise" in some metrics
    df_daily = df['equity'].resample('D').last().dropna()
    
    # 3. Calculate Returns
    returns = df_daily.pct_change().dropna()
    
    # 4. Generate Report
    try:
        qs.reports.html(returns, output=output_path, title="SIGMA B2B Strategy (2020-2022)")
        print(f"QuantStats Report saved to {output_path}")
    except Exception as e:
        print(f"QuantStats Error: {e}")

if __name__ == "__main__":
    generate_tearsheet("research/reports/equity_curve.csv", "research/reports/tearsheet.html")
