
import pandas as pd
import plotly.graph_objects as go
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath('c:/Users/User/Desktop/SIGMA System Anti Gravity/SIGMA-Crypto-ASCEND'))

from core.detectors.swing_points import detect_swings
from core.detectors.breakouts import detect_breakouts
from core.detectors.b2b_engine import detect_b2b_zones
from core.models.structures import DetectionConfig

from core.visualization.plotly_visualizer import PlotlyVisualizer

def generate_visuals():
    data_path = "c:/Users/User/Desktop/SIGMA System Anti Gravity/SIGMA-Crypto-ASCEND/data/raw/BTCUSDT_1d.parquet"
    artifact_dir = "C:/Users/User/.gemini/antigravity/brain/6ca37f70-a9f2-4ef8-82ae-d04457d3dae3"
    
    df_raw = pd.read_parquet(data_path)
    # Use a small recent window for clear visualization
    df = df_raw.tail(300).reset_index(drop=True)
    df.index = pd.to_datetime(df.index)
    
    config = DetectionConfig(swing_window=3)
    swings = detect_swings(df, config)
    breakouts = detect_breakouts(df, swings, config)
    zones = detect_b2b_zones(df, swings, config)
    
    visualizer = PlotlyVisualizer(df)
    
    # 1. Structural Audit (DNA)
    fig1 = visualizer.create_structural_audit(df, swings, title="Figure 1: Vectorized Structural Anchors (DNA)")
    fig1.write_image(os.path.join(artifact_dir, "visual_swings.png"))
    
    # 2. Breakout Audit (Events)
    fig2 = visualizer.create_breakout_audit(df, breakouts, title="Figure 2: Multi-Temporal Breakout Events")
    fig2.write_image(os.path.join(artifact_dir, "visual_breakouts.png"))
    
    # 3. B2B Audit (Siege)
    fig3 = visualizer.create_b2b_audit(df, zones, title="Figure 3: Bilateral Structural Anchors (BSA) Mapping")
    fig3.write_image(os.path.join(artifact_dir, "visual_b2b_zones.png"))
    
    print(f"Paper-ready visuals generated in: {artifact_dir}")

if __name__ == "__main__":
    generate_visuals()
