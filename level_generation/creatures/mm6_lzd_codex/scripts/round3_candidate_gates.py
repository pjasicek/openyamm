"""Replay existing all-clip gates for a saved reduction candidate."""
import sys,json,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def check(path):
 clips=['Standing','Fidget','Walking','Running','Attack','Cast','Hit','Death','Dead']
 for name,args in [('scan_deformation.py',[path]),('g6_contacts.py',[path,*clips]),('g6_head_clearance.py',[path,*clips]),('equipment_gate.py',[]),('round3_gates.py',[path])]:
  sys.argv=[name,'--',*map(str,args)]
  runpy.run_path(str(P/'scripts'/name),run_name='__main__',init_globals={'GATE_BLEND':path})
 scan=json.loads((P/'review/deformation_scan.json').read_text());contacts=json.loads((P/'work/g6_contacts.json').read_text());head=json.loads((P/'review/head_clearance.json').read_text());eq=json.loads((P/'review/equipment_gate.json').read_text());motion=json.loads((P/'review/round3_motion_gate.json').read_text())
 arm=max(r['p99']for x in scan.values()for n,r in x['stretch'].items()if n.endswith('_arm'));hand=max(r['max']for x in scan.values()for n,r in x['stretch'].items()if n.endswith('_hand'));contact=max([0]+[r[0]*.01 for x in contacts.values()for r in x.values()]);heads=max(x['depth_m']for x in head.values());weapon=max(r['depth_m']for x in eq.values()for r in x['contacts'].values())
 report={'arm_p99':arm,'hand_max':hand,'body_contact_m':contact,'head_contact_m':heads,'equipment_contact_m':weapon,'motion':motion,'passed':arm<=2 and hand<=4.5 and contact<=.002 and heads<=.010 and weapon<=.002 and motion['passed']}
 return report
