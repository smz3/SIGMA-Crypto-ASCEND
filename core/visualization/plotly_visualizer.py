import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Optional
from core.models.structures import B2BZoneInfo, SignalDirection

class ChartVisualizer:
    """
    The VERIFIER.
    Plots Candlesticks + Zones + Trades.
    """
    
    def __init__(self, data: pd.DataFrame):
        self.df = data
        self.fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                 vertical_spacing=0.03, 
                                 row_heights=[0.7, 0.3])
                                 
    def plot_candles(self):
        self.fig.add_trace(go.Candlestick(
            x=self.df.index,
            open=self.df['open'],
            high=self.df['high'],
            low=self.df['low'],
            close=self.df['close'],
            name='Price'
        ), row=1, col=1)
        
    def plot_zones(self, zones: List[B2BZoneInfo]):
        for z in zones:
            color = 'rgba(0, 255, 0, 0.2)' if z.direction == SignalDirection.BULLISH else 'rgba(255, 0, 0, 0.2)'
            
            # Draw Rectangle
            self.fig.add_shape(
                type="rect",
                x0=z.zone_created_time,
                y0=z.L1_price,
                x1=self.df.index[-1], # Extend to end (or invalidation time)
                y1=z.L2_price,
                line=dict(width=0),
                fillcolor=color,
                row=1, col=1
            )
            
    def plot_trades(self, trade_log_path: str):
        try:
            trades = pd.read_csv(trade_log_path)
            trades['open_time'] = pd.to_datetime(trades['open_time'])
            
            # Buy Trades (Entries)
            buys = trades[trades['direction'] == 'BULLISH']
            self.fig.add_trace(go.Scatter(
                x=buys['open_time'], 
                y=buys['entry_price'],
                mode='markers',
                marker=dict(symbol='triangle-up', size=5, color='green'),
                name='Buy Entry'
            ), row=1, col=1)
            
            # Sell Trades (Entries)
            sells = trades[trades['direction'] == 'BEARISH']
            self.fig.add_trace(go.Scatter(
                x=sells['open_time'], 
                y=sells['entry_price'],
                mode='markers',
                marker=dict(symbol='triangle-down', size=5, color='red'),
                name='Sell Entry'
            ), row=1, col=1)

            # 3. Plot Exits
            trades['close_time'] = pd.to_datetime(trades['close_time'])
            
            # --- NEW: Plot Connecting Lines ---
            # For performance, we add separate traces for each category
            for direction, color in [('BULLISH', 'rgba(0,255,0,0.2)'), ('BEARISH', 'rgba(255,0,0,0.2)')]:
                df_dir = trades[trades['direction'] == direction]
                x_lines = []
                y_lines = []
                for _, t in df_dir.iterrows():
                    x_lines.extend([t['open_time'], t['close_time'], None])
                    y_lines.extend([t['entry_price'], t['exit_price'], None])
                
                self.fig.add_trace(go.Scatter(
                    x=x_lines, y=y_lines,
                    mode='lines',
                    line=dict(color=color, width=0.5), # Thinner lines
                    hoverinfo='none',
                    showlegend=False,
                    name=f'{direction} Paths'
                ), row=1, col=1)

            # Take Profits
            tps = trades[trades['reason'] == 'Take Profit']
            self.fig.add_trace(go.Scatter(
                x=tps['close_time'],
                y=tps['exit_price'],
                mode='markers',
                marker=dict(symbol='circle', size=4, color='blue', line=dict(width=0.5, color='white')),
                name='Take Profit'
            ), row=1, col=1)

            # Stop Losses
            sls = trades[trades['reason'] == 'Stop Loss']
            self.fig.add_trace(go.Scatter(
                x=sls['close_time'],
                y=sls['exit_price'],
                mode='markers',
                marker=dict(symbol='x', size=5, color='orange'),
                name='Stop Loss'
            ), row=1, col=1)
            
        except Exception as e:
            print(f"No trades to plot or error: {e}")
            
    def show(self):
        self.fig.update_layout(height=800, title_text="SIGMA Strategy Audit")
        self.fig.show()

    def save_html(self, filename="strategy_audit.html"):
        self.fig.write_html(filename)
        print(f"Chart saved to {filename}")
