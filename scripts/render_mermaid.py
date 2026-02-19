import base64
import requests
import os

def render_mermaid(mmd_code, output_path):
    print(f"Rendering to {output_path}...")
    # mermaid.ink uses base64 encoding of the code
    b64_code = base64.b64encode(mmd_code.encode('utf-8')).decode('utf-8')
    url = f"https://mermaid.ink/img/{b64_code}"
    
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print("Success!")
    else:
        print(f"Failed with status code: {response.status_code}")

mmd1 = """
graph TD
    P1["P1: Primary Extremum (High)"] --> P2["P2: Base Low"]
    P2 --> P3["P3: Internal Lower High"]
    P5["P5: Historical Anchor (Low)"] -. "Precedes P1" .-> P1
    P3 --> P4["P4: Fracture (Close below P5)"]
    subgraph BSA_Detection [BSA Detection Engine]
    P1
    P2
    P3
    P5
    P4
    end
    P4 --> L1["Level 1 (Execution): P2.Price"]
    P4 --> L2["Level 2 (Terminal): Max(P1, P3)"]
"""

mmd2 = """
graph TD
    T1["Tier 1: Macro Hierarchy (MN1, W1, D1)"] -- "Storyline Latch" --> T2["Tier 2: Tactical Handover (H4, H1, M30)"]
    T2 -- "Execution Handover" --> T3["Tier 3: Micro Structural Triggers (M15, M5, M1)"]
    subgraph Hierarchy [Recursive Gating Hierarchy]
    T1
    T2
    T3
    end
    T3 --> Trigger["Execution Trigger (T1/T2/T3)"]
"""

output_dir = r"C:\Users\User\.gemini\antigravity\brain\6ca37f70-a9f2-4ef8-82ae-d04457d3dae3"
render_mermaid(mmd1, os.path.join(output_dir, "bsa_detection_logic.png"))
render_mermaid(mmd2, os.path.join(output_dir, "recursive_gating_hierarchy.png"))
