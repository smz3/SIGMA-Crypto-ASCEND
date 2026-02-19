import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Optional, Any
from core.models.structures import B2BZoneInfo, SignalDirection, SwingType

class ChartVisualizer:
    """
    The DEFINITIVE VERIFIER engine.
    Plots Candlesticks + Zones + Trades.
    Handles coordinate mapping between Bar Index and Datetime.
    """
    
    def __init__(self, data: Optional[pd.DataFrame] = None):
        """Initialize with optional dataframe."""
        self.df = data
        self.fig = None
        print("SIGMA Visualizer: Definitive V5.3 Build Loaded.")
        if data is not None:
            self._init_subplots()

    def _init_subplots(self):
        """Standard 2-row subplot layout."""
        self.fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                 vertical_spacing=0.03, 
                                 row_heights=[0.7, 0.3])

    def _get_x(self, item: Any, default_time: Any = None) -> Any:
        """
        Calculates the correct X coordinate.
        If the dataframe index is integers (reset_index), it MUST use bar_index.
        """
        if self.df is None:
            return getattr(item, 'time', getattr(item, 'breakout_bar_time', getattr(item, 'zone_created_time', default_time)))
        
        # Determine if we are on a numeric (integer) timeline
        is_numeric = pd.api.types.is_integer_dtype(self.df.index)
        
        if is_numeric:
            # Priority Ladder for structural anchoring:
            # 1. First Barrier (P2 - The Origin Breakout) - Highest priority for zones
            idx = getattr(item, 'first_barrier_bar_index', -1)
            # 2. Breakout Bar (For raw breakouts)
            if idx == -1: idx = getattr(item, 'breakout_bar_index', -1)
            # 3. Pivot Point Bar (For swings)
            if idx == -1: idx = getattr(item, 'bar_index', -1)
            # 4. Confirmation Bar (P4 - The creation signal) - Lowest priority
            if idx == -1: idx = getattr(item, 'created_bar_index', -1)
            # 5. Fallback side-car
            if idx == -1: idx = getattr(item, 'second_barrier_bar_index', -1)
            
            if idx != -1 and idx < len(self.df):
                return self.df.index[idx]
            
            # Smart fallback: if we have a time but no index, try mapping it
            # We also prioritize first_barrier_time here
            item_time = getattr(item, 'first_barrier_time', 
                        getattr(item, 'breakout_bar_time', 
                        getattr(item, 'time', 
                        getattr(item, 'zone_created_time', default_time))))
            
            if item_time is not None:
                try: 
                    loc = self.df.index.get_loc(item_time)
                    return self.df.index[loc]
                except: pass
        
        # Fallback to time-based attributes
        return getattr(item, 'first_barrier_time', 
               getattr(item, 'breakout_bar_time', 
               getattr(item, 'time', 
               getattr(item, 'zone_created_time', default_time))))

    def plot_candles(self):
        if self.fig is None: self._init_subplots()
        self.fig.add_trace(go.Candlestick(
            x=self.df.index, open=self.df['open'], high=self.df['high'],
            low=self.df['low'], close=self.df['close'], name='Price'
        ), row=1, col=1)
        
    def plot_zones(self, zones: List[B2BZoneInfo]):
        if self.fig is None: self._init_subplots()
        for z in zones:
            is_bullish = getattr(z, 'direction', SignalDirection.NONE) == SignalDirection.BULLISH
            color = 'rgba(0, 255, 0, 0.2)' if is_bullish else 'rgba(255, 0, 0, 0.2)'
            x_start = self._get_x(z)
            if x_start is None: continue
            
            self.fig.add_shape(
                type="rect", x0=x_start, y0=getattr(z, 'L1_price', 0),
                x1=self.df.index[-1], y1=getattr(z, 'L2_price', 0),
                line=dict(width=0), fillcolor=color, row=1, col=1
            )
            
    def plot_trades(self, trade_log_path: str):
        if self.fig is None: self._init_subplots()
        try:
            trades = pd.read_csv(trade_log_path)
            trades['open_time'] = pd.to_datetime(trades['open_time'])
            # Trade plotting stays time-based if CSV has timestamps
            buys = trades[trades['direction'] == 'BULLISH']
            self.fig.add_trace(go.Scatter(
                x=buys['open_time'], y=buys['entry_price'], mode='markers',
                marker=dict(symbol='triangle-up', size=7, color='green'), name='Buy'
            ), row=1, col=1)
            sells = trades[trades['direction'] == 'BEARISH']
            self.fig.add_trace(go.Scatter(
                x=sells['open_time'], y=sells['entry_price'], mode='markers',
                marker=dict(symbol='triangle-down', size=7, color='red'), name='Sell'
            ), row=1, col=1)
        except Exception: pass

    # --- HIGH-FIDELITY RESEARCH AUDIT METHODS ---
    
    def create_structural_audit(self, df: pd.DataFrame, swings: List, title: str = "Chart 1: Structural Swings (The DNA Audit)"):
        """Structural Audit Def: No Price Dots + Filled Swing Dots + Right Labels."""
        self.df = df
        self.fig = make_subplots(rows=1, cols=1)
        
        # 1. Price Path (Bold Solid Black - NO DOTS)
        self.fig.add_trace(go.Scatter(
            x=df.index, y=df['close'],
            mode='lines', name='Price Path',
            line=dict(color='black', width=2.0),
            opacity=1.0
        ))
        
        # 2. Structural Labels (H/L) with FILLED Dots and Right-aligned text
        highs = [s for s in swings if "HIGH" in str(getattr(s, 'type', "")).upper()]
        lows = [s for s in swings if "LOW" in str(getattr(s, 'type', "")).upper()]
        
        if highs:
            self.fig.add_trace(go.Scatter(
                x=[self._get_x(s) for s in highs], y=[getattr(s, 'price', 0) for s in highs],
                mode='markers+text', name='High',
                text=[f"H: {getattr(s, 'price', 0):,.2f}" for s in highs],
                textposition="middle right", 
                textfont=dict(color='red', size=11, family="Arial Black"),
                marker=dict(color='red', symbol='circle', size=10, line=dict(width=1, color='white'))
            ))
        if lows:
            self.fig.add_trace(go.Scatter(
                x=[self._get_x(s) for s in lows], y=[getattr(s, 'price', 0) for s in lows],
                mode='markers+text', name='Low',
                text=[f"L: {getattr(s, 'price', 0):,.2f}" for s in lows],
                textposition="middle right", 
                textfont=dict(color='green', size=11, family="Arial Black"),
                marker=dict(color='green', symbol='circle', size=10, line=dict(width=1, color='white'))
            ))
        
        self._apply_paper_layout(title)
        return self.fig

    def create_breakout_audit(self, df: pd.DataFrame, breakouts: List, title: str = "Chart 2: Raw Breakout Events (Bob/Bos Audit)"):
        """Breakout Audit: Anchored to Broken Swing + Filled Dots + Format ( Bos Price (Close) )."""
        self.df = df
        self.fig = make_subplots(rows=1, cols=1)
        
        # 1. Price Path (Bold Solid Black - NO DOTS)
        self.fig.add_trace(go.Scatter(
            x=df.index, y=df['close'], mode='lines', name='Price Path',
            line=dict(color='black', width=2.0)
        ))
        
        # 2. Breakout Markers and Labels (Anchored at Broken Swing)
        for b in breakouts:
            is_bullish = getattr(b, 'direction', SignalDirection.NONE) == SignalDirection.BULLISH
            label_prefix = "Bob" if is_bullish else "Bos"
            color = 'green' if is_bullish else 'red'
            
            # Anchor coordinate: Broken Swing Time/Index
            # We use a custom object-like access to Get X for the broken swing
            class BrokenSwingAnchor:
                def __init__(self, time, bar_index):
                    self.time = time
                    self.bar_index = bar_index
            
            anchor = BrokenSwingAnchor(
                getattr(b, 'broken_swing_time', None),
                getattr(b, 'broken_swing_bar_index', -1) # Need to ensure this exists or fallback
            )
            
            # Fallback if bar_index is missing: use time to find index
            if getattr(anchor, 'bar_index', -1) == -1 and anchor.time is not None:
                try: anchor.bar_index = df.index.get_loc(anchor.time)
                except: pass

            x_val = self._get_x(anchor)
            if x_val is not None:
                broken_price = getattr(b, 'broken_swing_price', 0.0)
                close_price = getattr(b, 'breakout_bar_close_price', 0.0)
                
                label_text = f"{label_prefix} {broken_price:,.2f} ({close_price:,.2f})"
                
                self.fig.add_trace(go.Scatter(
                    x=[x_val], y=[broken_price],
                    mode='markers+text', 
                    text=[label_text],
                    textposition="middle right", 
                    textfont=dict(color=color, size=11, family="Arial Black"),
                    marker=dict(color=color, symbol='circle', size=10, line=dict(width=1, color='white')),
                    showlegend=False
                ))
        
        self._apply_paper_layout(title)
        return self.fig

    def create_b2b_audit(self, df: pd.DataFrame, zones: List[B2BZoneInfo], title: str = "Chart 3: B2B Zone Lifecycle Audit"):
        """Siege Audit: L1/L2 (Dash), 50% (Dot), Vertical (Solid), T0-T3 Labels."""
        self.df = df
        self.fig = make_subplots(rows=1, cols=1)
        
        # 1. Price Path (Bold Solid Black - NO DOTS)
        self.fig.add_trace(go.Scatter(
            x=df.index, y=df['close'], mode='lines', name='Price Path',
            line=dict(color='black', width=2.0)
        ))
        
        # TF Color Specs (Narrative, Control, Sniper)
        tf_palette = {
            'MN1': 'gold', 'W1': 'darkgoldenrod', 'D1': 'orange',
            'H4': 'royalblue', 'H1': 'dodgerblue',
            'M30': 'deepskyblue', 'M15': 'cadetblue',
            'M5': 'cyan', 'M1': 'aquamarine'
        }
        
        for z in zones:
            if not z.is_valid and not z.is_invalidated: continue
            
            # TF mapping for TEXT hierarchy (Strictly for the label string)
            tf_val = getattr(z, 'timeframe', "D1")
            if hasattr(tf_val, 'name'): 
                tf_key = tf_val.name.upper().replace("PERIOD_", "")
            else:
                tf_key = str(tf_val).upper().replace("PERIOD_", "")
            
            # Absolute Guard: prevent DetectionConfig leakage
            if len(tf_key) > 4 or tf_key not in ['MN1', 'W1', 'D1', 'H4', 'H1', 'M30', 'M15', 'M5', 'M1']:
                tf_key = "D1"
            
            # Directional colors strictly Red/Green for BOTH lines and text labels
            is_sell = z.direction == SignalDirection.BEARISH
            color = 'red' if is_sell else 'green'
            label_color = color # Locked to directional bias
            
            # Start coordinate: Anchored to first_barrier
            # x_start will now resolve correctly via _get_x checking first_barrier_bar_index
            x_start = self._get_x(z, z.first_barrier_time)
            
            x_end = df.index[-1]
            if z.is_invalidated and z.invalidation_time:
                x_end_val = z.invalidation_time
                if pd.api.types.is_integer_dtype(df.index):
                    try: 
                        loc = df.index.get_loc(z.invalidation_time)
                        x_end_val = df.index[loc]
                    except: pass
                x_end = x_end_val

            # --- L1 & L2 Lines (Dashed) ---
            for price in [z.L1_price, z.L2_price]:
                self.fig.add_trace(go.Scatter(
                    x=[x_start, x_end], y=[price, price],
                    mode='lines', line=dict(color=color, dash='dash', width=1.5),
                    showlegend=False, opacity=0.8
                ))
            
            # --- 50% Line (Dotted) ---
            self.fig.add_trace(go.Scatter(
                x=[x_start, x_end], y=[z.fifty_percent, z.fifty_percent],
                mode='lines', line=dict(color='rgba(0,0,0,0.3)', dash='dot', width=1),
                showlegend=False
            ))
            
            # --- Left Vertical Connector (Solid) ---
            self.fig.add_trace(go.Scatter(
                x=[x_start, x_start], y=[z.L1_price, z.L2_price],
                mode='lines', line=dict(color=color, width=2.0),
                showlegend=False
            ))
            
            # --- Label ---
            touch_state = "T0"
            if z.L2_touched: touch_state = "T3"
            elif z.fifty_touched: touch_state = "T2"
            elif z.L1_touched: touch_state = "T1"
            
            lane_id = str(getattr(z, 'zone_id', ""))[:4]
            dir_str = "Buy" if z.direction == SignalDirection.BULLISH else "Sell"
            # Explicitly format the label to avoid grabbing unwanted object attributes
            label_text = f"L2 B2B {tf_key} {dir_str} [{touch_state}] {float(z.L2_price):,.2f} #{lane_id}"
            
            pos = "bottom right" if z.direction == SignalDirection.BULLISH else "top right"
            
            self.fig.add_trace(go.Scatter(
                x=[x_start], y=[z.L2_price],
                mode='text', text=[label_text],
                textposition=pos,
                textfont=dict(color=label_color, size=11, family="Arial Black"),
                showlegend=False
            ))
            
        self._apply_paper_layout(title)
        return self.fig

    def _apply_paper_layout(self, title: str):
        self.fig.update_layout(
            template='plotly_white', paper_bgcolor='white', plot_bgcolor='white',
            title=dict(text=title, x=0.05, y=0.95, font=dict(size=22, color='black', family="Arial Black")),
            xaxis=dict(title="Historical Timeline", showgrid=True, gridcolor='rgba(0,0,0,0.1)', linecolor='black', linewidth=2.0, mirror=True),
            yaxis=dict(title="Price Efficiency ($)", showgrid=True, gridcolor='rgba(0,0,0,0.1)', linecolor='black', linewidth=2.0, mirror=True),
            height=700, margin=dict(l=80, r=150, t=120, b=80), showlegend=True # Precise right margin for siege labels
        )

    def show(self):
        if self.fig: self.fig.show()

PlotlyVisualizer = ChartVisualizer