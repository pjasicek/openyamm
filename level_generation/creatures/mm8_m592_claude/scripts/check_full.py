"""Run the same half-frame surface gates across the complete animation set."""
from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=(P/'scripts/check_pilots.py').read_text().replace('work/pilots_fitted.blend','work/full_actions.blend').replace("('Standing','Walking','Running','Attack')","('Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead','Dying')").replace("P/'review/pilot_gates.json'","P/'review/full_gates.json'")
s=s.replace("C[foot[sd],2].min()","(C[:,2].min() if name in ('Death','Dead','Dying') else C[foot[sd],2].min())")
exec(compile(s,str(P/'scripts/check_pilots.py'),'exec'))
