"""Check only the revised attack on the retained UV/weight master."""
from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=(P/'scripts/check_pilots.py').read_text().replace("P/'work/pilots_fitted.blend'","P/'work/attack_revision_03.blend'").replace("('Standing','Walking','Running','Attack')","('Attack',)").replace("a.frame_range[1]+.01,.5","a.frame_range[1]+.01,.25").replace("P/'review/pilot_gates.json'","P/'review/attack_revision_03/master_gates.json'")
# UV transfer/reduction changed vertex indices; rigid-claw edges follow actual current weights.
a=s.index('F=json.loads');b=s.index('report=',a)
s=s[:a]+"""hard=[]
for j,n in enumerate(gn):
 if 'Finger' in n:
  mask_hard=W[:,j]>.9999;hard.extend(np.flatnonzero(valid&mask_hard[E].all(1)).tolist())
assert len(hard)>100
"""+s[b:]
exec(compile(s,str(P/'scripts/check_pilots.py'),'exec'))
print('ATTACK_CONTACTS',report['clips']['Attack']['contacts'])
