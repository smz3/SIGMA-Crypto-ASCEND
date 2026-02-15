"""
SIGMA Supabase Push Script
Pushes backtest results to Supabase for visualization in the SIGMA Quant dashboard.

Safety:
  - Only INSERTS into 'trades' with environment='CRYPTO_ASCEND_V1'
  - Never touches existing MT5 data
  - Deduplicates by checking existing records first
"""
import os
import pandas as pd
from pathlib import Path

try:
    from supabase import create_client, Client
except ImportError:
    print("Install supabase-py: pip install supabase")
    raise


ENVIRONMENT = "CRYPTO_ASCEND_V1"

TRADES_COLUMNS = [
    'ticket', 'symbol', 'direction', 'entry_time', 'exit_time',
    'entry_price', 'exit_price', 'sl_price', 'tp_price',
    'pnl_money', 'pnl_points', 'r_multiple',
    'mae_points', 'mfe_points', 'duration_seconds',
    'result', 'exit_reason', 'session', 'hour_of_day',
    'zone_tf', 'zone_id', 'zone_age_bars', 'zone_touch_num',
    'zone_size_points', 'atr_at_entry', 'sl_distance_points',
    'base_risk_pct', 'capital_at_entry', 'environment',
]


def get_supabase_client() -> Client:
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_KEY')

    if not url or not key:
        raise ValueError(
            "Set SUPABASE_URL and SUPABASE_KEY environment variables.\n"
            "Example:\n"
            "  $env:SUPABASE_URL = 'https://your-project.supabase.co'\n"
            "  $env:SUPABASE_KEY = 'your-anon-key'"
        )

    return create_client(url, key)


def push_trades(
    trades_df: pd.DataFrame,
    environment: str = ENVIRONMENT,
    dry_run: bool = False,
) -> int:
    if trades_df.empty:
        print("No trades to push.")
        return 0

    trades_df = trades_df.copy()
    trades_df['environment'] = environment

    available = [c for c in TRADES_COLUMNS if c in trades_df.columns]
    push_df = trades_df[available].copy()

    push_df = push_df.where(pd.notnull(push_df), None)

    records = push_df.to_dict(orient='records')

    for record in records:
        for key, val in record.items():
            if isinstance(val, float) and (pd.isna(val) or val != val):
                record[key] = None

    if dry_run:
        print(f"[DRY RUN] Would push {len(records)} trades with environment='{environment}'")
        for i, r in enumerate(records[:3]):
            print(f"  Trade {i+1}: {r['symbol']} {r['direction']} PnL=${r.get('pnl_money', 0)}")
        if len(records) > 3:
            print(f"  ... and {len(records) - 3} more")
        return len(records)

    client = get_supabase_client()

    print(f"Checking existing {environment} trades...")
    existing = client.table('trades').select('ticket').eq('environment', environment).execute()
    existing_tickets = {r['ticket'] for r in existing.data} if existing.data else set()

    new_records = [r for r in records if r.get('ticket') not in existing_tickets]

    if not new_records:
        print(f"All {len(records)} trades already exist in Supabase. Skipping.")
        return 0

    print(f"Pushing {len(new_records)} new trades (skipping {len(records) - len(new_records)} existing)...")

    batch_size = 50
    pushed = 0
    for i in range(0, len(new_records), batch_size):
        batch = new_records[i:i + batch_size]
        try:
            client.table('trades').insert(batch).execute()
            pushed += len(batch)
            print(f"  Pushed batch {i // batch_size + 1}: {len(batch)} trades")
        except Exception as e:
            print(f"  Batch {i // batch_size + 1} failed: {e}")
            for record in batch:
                try:
                    client.table('trades').insert(record).execute()
                    pushed += 1
                except Exception as inner_e:
                    print(f"    Failed single insert (ticket={record.get('ticket')}): {inner_e}")

    print(f"Successfully pushed {pushed}/{len(new_records)} trades to Supabase")
    return pushed


def register_strategy(config: dict, environment: str = ENVIRONMENT) -> None:
    client = get_supabase_client()

    record = {
        'environment': environment,
        'config': config,
        'description': f'SIGMA B2B Crypto - {environment}',
    }

    try:
        client.table('strategy_registry').upsert(record).execute()
        print(f"Registered strategy for {environment}")
    except Exception as e:
        print(f"Strategy registration failed (non-critical): {e}")


def main():
    csv_path = "data/backtest_results.csv"

    if not Path(csv_path).exists():
        print(f"No results file found at {csv_path}")
        print("Run the backtester first: python -m simulation.engine.vectorized_backtester")
        return

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} trades from {csv_path}")

    push_trades(df, dry_run=True)

    confirm = input("\nPush to Supabase? (yes/no): ").strip().lower()
    if confirm == 'yes':
        pushed = push_trades(df)
        if pushed > 0:
            register_strategy({
                'swing_window': 3,
                'swing_lookback': 20,
                'max_breakout_age': 0,
                'target_r': 1.5,
                'asset': 'BTCUSDT',
                'market': 'futures',
            })
    else:
        print("Aborted.")


if __name__ == "__main__":
    main()
