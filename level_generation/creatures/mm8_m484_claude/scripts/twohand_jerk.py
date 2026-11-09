import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for source,role in [("work/gated_master.blend","Attack"),("work/twohand_source.blend","AttackTwoHandSource")]:
 sys.argv=["jerk_probe.py","--",str(P/source),role];runpy.run_path(str(P/"scripts/jerk_probe.py"),run_name="__main__")
