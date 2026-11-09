from pathlib import Path
import runpy
P=Path(__file__).resolve().parents[1]
for n in ['round2_bind.py','round2_fingers_fit.py','round2_hands.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
