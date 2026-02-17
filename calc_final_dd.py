import pandas as pd
import numpy as np

def calculate_drawdown(path):
    df = pd.read_csv(path)
    df['equity'] = df['equity'] # Correct column name: equity
    rolling_max = df['equity'].cummax()
    drawdown = (df['equity'] - rolling_max) / rolling_max
    max_dd = drawdown.min()
    return max_dd


if __name__ == "__main__":
    tests = {
        "Test 10C (Pillar 3)": r'research\reports\Test_10C_Phase12C_StructuralGasket\equity_curve.csv',
        "Test 10B (12A+12B)": r'research\reports\Test_10B_Phase12B_TierGating\equity_curve.csv',
        "Test 10A": r'research\reports\Test_10A_Phase12A_TierGating\equity_curve.csv',
        "Test 9G": r'research\reports\Test_9G_Surgical_Flow\equity_curve.csv',
        "Test 10D (Combined)": r'research\reports\Test_10D_Phase12D_StructuralIntegrity\equity_curve.csv',
        "Test 10E (Memory Only)": r'research\reports\Test_10E_Phase12D_StructuralMemoryOnly\equity_curve.csv'
    }

    for label, path in tests.items():
        print(f"Max DD ({label}): {calculate_drawdown(path):.2%}")
