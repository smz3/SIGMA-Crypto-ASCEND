import os

def create_skeleton():
    base_dir = r"c:\Users\User\Desktop\SIGMA System Anti Gravity\SIGMA-Crypto-ASCEND"
    
    structure = {
        "config": ["defaults.yaml", "binance_config.yaml"],
        "core": ["__init__.py"],
        "core/detectors": ["__init__.py", "swing_points.py", "breakouts.py", "b2b_engine.py", "zone_manager.py", "zone_status.py"],
        "core/filters": ["__init__.py", "confluence.py", "fractal_geometry.py"],
        "core/models": ["__init__.py", "structures.py"],
        "data": ["__init__.py"],
        "data/raw": [],
        "data/processed": [],
        "simulation": ["__init__.py"],
        "simulation/engine": ["__init__.py", "vectorized_backtester.py", "execution_engine.py"],
        "simulation/backtest": ["__init__.py", "result_analyzer.py"],
        "dashboard": ["__init__.py"],
        "dashboard/components": ["__init__.py"],
        "scripts": ["binance_fetcher.py", "audit_mt5_parity.py"],
        "logs": [],
        "tests": ["__init__.py", "test_detectors.py", "test_engine.py"]
    }
    
    for folder, files in structure.items():
        folder_path = os.path.join(base_dir, folder)
        os.makedirs(folder_path, exist_ok=True)
        for file in files:
            file_path = os.path.join(folder_path, file)
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    if file.endswith('.py'):
                        f.write(f'# {file}\n# Placeholder for SIGMA-Crypto-ASCEND\n')
                    else:
                        f.write(f'# {file} configuration\n')
    
    print("Skeleton created successfully.")

if __name__ == "__main__":
    create_skeleton()
