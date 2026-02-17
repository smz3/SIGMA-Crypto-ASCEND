import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from pathlib import Path

def generate_multi_tf_overlay(test_id: str):
    reports_dir = Path(f"research/reports/{test_id}")
    trade_log_path = reports_dir / "trade_log.csv"
    
    if not trade_log_path.exists():
        print(f"Error: Trade log not found at {trade_log_path}")
        return

    # 1. Load Trades
    trades = pd.read_csv(trade_log_path)
    trades['open_time'] = pd.to_datetime(trades['open_time'])
    trades['close_time'] = pd.to_datetime(trades['close_time'])

    # 2. Load Price Data
    tfs = ["MN1", "W1", "D1", "H4"]
    data = {}
    for tf in tfs:
        path = Path(f"data/raw/BTCUSDT_{tf}.parquet")
        if path.exists():
            df = pd.read_parquet(path)
            if 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'])
                df.set_index('time', inplace=True)
            elif 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            
            # Filter for report period
            data[tf] = df[df.index >= "2020-01-01"]
        else:
            print(f"Warning: Data for {tf} not found at {path}")

    # 3. Create Subplots
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=[f"BTCUSDT {tf} Strategy Overlay" for tf in tfs]
    )

    for i, tf in enumerate(tfs):
        if tf not in data: continue
        df = data[tf]
        
        # Add Price Line
        fig.add_trace(
            go.Scatter(x=df.index, y=df['close'], mode='lines', name=f'{tf} Price', line=dict(width=1)),
            row=i+1, col=1
        )

        # Add Trades
        for _, t in trades.iterrows():
            is_buy = "BULLISH" in str(t['direction'])
            color = 'green' if is_buy else 'red'
            symbol = 'triangle-up' if is_buy else 'triangle-down'
            
            # Entry
            fig.add_trace(
                go.Scatter(
                    x=[t['open_time']], y=[t['entry_price']],
                    mode='markers',
                    marker=dict(symbol=symbol, color=color, size=6),
                    showlegend=False,
                    hovertext=f"{tf} Entry | {t['entry_reason']}"
                ),
                row=i+1, col=1
            )
            
            # Exit
            exit_symbol = 'star' if t['pnl'] > 0 else 'x'
            exit_color = 'gold' if t['pnl'] > 0 else 'red'
            fig.add_trace(
                go.Scatter(
                    x=[t['close_time']], y=[t['exit_price']],
                    mode='markers',
                    marker=dict(symbol=exit_symbol, color=exit_color, size=6),
                    showlegend=False,
                    hovertext=f"{tf} Exit | {t['reason']} | PnL: {t['pnl']:.2f}"
                ), row=i+1, col=1
            )
            
            # Path for winners
            if t['pnl'] > 0:
                fig.add_trace(
                    go.Scatter(
                        x=[t['open_time'], t['close_time']],
                        y=[t['entry_price'], t['exit_price']],
                        mode='lines',
                        line=dict(color=color, width=1, dash='dot'),
                        showlegend=False
                    ), row=i+1, col=1
                )

    fig.update_layout(
        height=1600,
        title_text=f"SIGMA {test_id} Multi-Timeframe Structural Audit",
        template='plotly_white',
        showlegend=False
    )

    output_path = reports_dir / "multi_tf_overlay.html"
    fig.write_html(output_path)
    print(f"✅ Multi-TF Overlay saved to: {output_path}")

if __name__ == "__main__":
    generate_multi_tf_overlay("8th_IS_test")
