"""Penetration-only probe of a gait2 experiment blend on LOD0 (G2_SRC), Walk2/Run2 only."""
import os,runpy,subprocess
from pathlib import Path
p=Path(__file__).resolve().parents[1]
os.environ.update(G2_LEVELS='0',G2_ONLY_GAITS='1',G2_GATE_OUT='work/gait2/probe.blend')
runpy.run_path(str(p/'scripts/gait2_gate_blends.py'),run_name='__main__')
os.environ.update(GATE_BLEND='work/gait2/probe.blend',PENETRATION_PROBE='1',PENETRATION_REPORT='work/gait2/probe_penetration.json')
runpy.run_path(str(p/'scripts/review4_penetration.py'),run_name='__main__')
