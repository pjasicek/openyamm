"""Concept coverage: articulated cuirass, layered shoulders and full limb plates on the shared skinned shell."""
import copy
import json
import math
from pathlib import Path
import armour_spec_v4 as base
P=Path(__file__).resolve().parents[1]
spec=copy.deepcopy(base.spec)
spec['plates']=[p for p in spec['plates'] if not p['name'].startswith(('carapace','upperarm'))]
spec['props']=[p for p in spec['props'] if p['name']=='crest']
D=math.radians

def shape(p, v, widths):
    p['v']=v
    p['lo']=[[z,-w] for z,w in widths]
    p['hi']=[[z,w] for z,w in widths]

def cylinder(p, v, lo, hi):
    p['v']=v
    sign=1 if p['name'].endswith('_L') else -1
    p['lo']=[[z,D(lo if sign==1 else -hi)] for z in v]
    p['hi']=[[z,D(hi if sign==1 else -lo)] for z in v]

for p in spec['plates']:
    p['nu']=max(4,round(p['nu']*.85));p['nv']=max(3,round(p['nv']*.85))
    p['t']*=1.2;p['off']+=.008
    p['paint_studs']=p.get('paint_studs',[])+p.pop('studs',[])
    n=p['name']
    if n=='chest':
        shape(p,[1.15,1.445],[[1.15,.10],[1.19,.16],[1.27,.19],[1.36,.18],[1.41,.13],[1.445,.08]])
        p['off']=.018; p['t']=.014
        p['exclude_pieces']=[1]
        p['v'][0]=1.18
        p['lo']=[(max(1.18,z),w) for z,w in p['lo']]
        p['hi']=[(max(1.18,z),min(w,.15)) for z,w in p['hi']]
        p['lo']=[[z,max(-.125,w)] for z,w in p['lo']]
    elif n=='abdomen_u':
        shape(p,[1.035,1.10],[[1.035,.06],[1.06,.09],[1.10,.12]])
        p['nv']=5; p['off']=.020; p['t']=.010
        p['shell']['bones']=['B_Pelvis','B_Spine']
    elif n=='belt':
        shape(p,[.985,1.006],[[.985,.025],[1.006,.030]])
        p['off']=.005;p['t']=.008;p['crown']=.006
    elif n=='back':p['v'][1]=1.48
    elif n=='back_low':
        shape(p,[1.015,1.085],[[1.015,.12],[1.085,.14]])
    elif n.startswith('pauldron'):
        p['shell']={'rigid':1.0,'bones':[p['bone']]}
        p['off']+=.012
        p['v']=[-.40,.38]
        p['lo']=[[-.40,-.85],[.15,-1.0],[.38,-.68]]
        p['hi']=[[-.40,.85],[.15,1.0],[.38,.68]]
        p['lo' if n.endswith('_L') else 'hi']=[[-.40,-.70 if n.endswith('_L') else .70],[.10,-.35 if n.endswith('_L') else .35],[.38,-.05 if n.endswith('_L') else .05]]
    elif n.startswith('forearm'):
        cylinder(p,[.38,.90],-140,10)
        if n.endswith('_L'):p['hi']=[[.38,D(-55)],[.62,D(10)],[.90,D(10)]]
        if n.endswith('_R'):
            p['lo']=[[.38,D(45)],[.60,D(70)],[.90,D(70)]]
        p['nu']=8;p['nv']=6
    elif n.startswith('thigh'):
        cylinder(p,[.10,.75],-80,15)
        p['lo']=[[.10,D(-80 if n.endswith('_L') else -15)],[.75,D(-55 if n.endswith('_L') else -10)]]
        p['hi']=[[.10,D(15 if n.endswith('_L') else 80)],[.75,D(10 if n.endswith('_L') else 55)]]
        p['nu']=9;p['nv']=6;p['off']=.005;p['t']=.010
        p['off_v']=[[.10,.005],[.55,.005],[.75,.035]]
        inner=[[.10,D(10)],[.35,D(30)],[.55,D(25)],[.75,D(10)]]
        if n.endswith('_L'):p['hi']=inner
        else:p['lo']=[[v,-u] for v,u in inner]
    elif n.startswith('shin'):
        cylinder(p,[.12,.80],-65,40)
        p['nu']=8;p['nv']=6
    elif n.startswith('tasset'):
        cylinder(p,[.14,.29],-105,-10)
        p['nu']=7;p['nv']=5
for side in 'LR':
    upper=next(p for p in spec['plates'] if p['name']==f'pauldron_{side}')
    lower=copy.deepcopy(upper)
    lower.update(name=f'pauldron_lower_{side}',v=[-.58,-.40],nv=3,off=upper['off']+.025,
                 lo=[[-.58,-.55],[-.40,-.70]],hi=[[-.58,.55],[-.40,.70]],glow=[],paint_studs=[])
    lower['lo' if side=='L' else 'hi']=[[-.58,-.15 if side=='L' else .15],[-.40,-.15 if side=='L' else .15]]
    spec['plates'].append(lower)

# One complete breastplate, with the shoulder clearance built into its upper outline.
core=next(p for p in spec['plates'] if p['name']=='chest')
shape(core,[1.19,1.445],[[1.19,.11],[1.24,.14],[1.34,.145],[1.40,.11],[1.445,.085]])
core.update(nu=9,nv=8,off=.012,t=.010,crown=.012)
upper=copy.deepcopy(next(p for p in spec['plates'] if p['name']=='abdomen_u'))
upper.update(name='abdomen_upper',bone='B_Spine1',off=.045,t=.010)
shape(upper,[1.115,1.145],[[1.115,.11],[1.145,.075]])
upper['glow']=[[[.12,.15],[.88,.15]]]
spec['plates'].append(upper)

for side in 'LR':
    angles=[[.52,D(-150),D(-70)],[.76,D(-120),D(-60)]]
    if side=='R':angles=base.mirror_angles(angles)
    spec['plates'].append(base.cyl('shoulder_lame_'+side,f'B_{side}_UpperArm',[.52,.76],angles,8,5,.025,.014,
        [f'B_{side}_Clavicle',f'B_{side}_UpperArm',f'B_{side}_UpperArmTwist'],
        shell={'rigid':1.0,'bones':[f'B_{side}_UpperArm',f'B_{side}_UpperArmTwist']},
        glow=[[[.15,.12],[.5,.08],[.85,.12]]]))

for side,sign in [('L',1),('R',-1)]:
    p=copy.deepcopy(core)
    p.update(name='breast_'+side,v=[1.34,1.49],nu=7,nv=6,off=(.065 if side=='L' else .070),crown=.012)
    bounds=[[1.34,.155,.19],[1.37,.125,.215],[1.40,.11,.205],[1.45,.105,.175],[1.49,.115,.145]]
    p['lo']=[[z,lo if sign==1 else -hi] for z,lo,hi in bounds]
    p['hi']=[[z,hi if sign==1 else -lo] for z,lo,hi in bounds]
    p['glow']=[[[.08,.10],[.85,.28],[.90,.80]]]
    spec['plates'].append(p)

spec['texels_per_m']=900
assert all(p.get('shell') for p in spec['plates'])
(P/'scripts/armour_lancer.json').write_text(json.dumps(spec,indent=2)+'\n')
print('LANCER_SPEC',len(spec['plates']),'shell pieces')
