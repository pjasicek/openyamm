"""Native interaction and movement coverage for Deepwell; no recorded-hit fallbacks."""
import json
import math
from pathlib import Path
import yaml
from layout import ARRIVALS, PROJECT as P, zone
R=json.loads((P/'d13_build.json').read_text()); groups=R['actor_groups']
MAP='hes_d13.blv'
def step(step_kind,**v):return {step_kind:v}
def check(**v):return step('assert',**v)
def pose(x,y,z=0,yaw=0,pitch=0):return dict(map=MAP,x=x,y=y,z=z,yaw=math.radians(yaw),pitch=pitch)
def at(*a,**kw):return step('set_pose',**pose(*a,**kw))
def click(x,y,z=0,yaw=0,event=None,pitch=0):
    return [at(x,y,z,yaw,pitch),step('press_interact',**({'expect':dict(kind='event_target',triggered_event=event)} if event else {}))]
def wait(seconds=1):return step('advance_runtime',seconds=seconds)
def var(n,v):return check(map_var_changed=dict(index=n,value=v))
def door(n,state='open'):return check(mechanism=dict(id=n,state=state))
def answer(event,value='Yes'):return step('answer_input',text=value)
def bit(n):return step('setup_shortcut',kind='set_qbit',id=n)
def new(hack=True):return step('new_game_flow',start_map=MAP,party=dict(food=200,members=[
    dict(name='Deepwell tester '+str(i+1),**{'class':'Knight'},level=1000,endurance=100,equipment={},
         skills=[dict(name='Hacking',level=12,mastery=2)] if hack else []) for i in range(5)]))
def kill(g):return [step('damage_actor',actor_index=i,amount=1000000,tier='kreegan_energy') for i in groups[str(g)] for _ in range(1 if g in (1,3,7) else 2)]
def write(name,s):
    (P/(name+'.yml')).write_text(yaml.safe_dump(dict(id='hesper.d13.'+name,world='hesper',mode='faithful',steps=s),sort_keys=False))
def move(x,y,z,yaw,seconds,end,endz=None,ai=False):
    return step('movement_segment',input='forward',duration_ms=round(seconds*1000),delta_game_minutes=0,
                start=pose(x,y,z,yaw),expect_stop=pose(*end,z if endz is None else endz,yaw),
                tolerance_xy=60,tolerance_z=40,actor_collision=False,actor_ai=ai)
def vent(x,y,z,seconds):
    # advance_runtime does not drain timer-issued map moves; a neutral movement frame does.
    return step('movement_segment',input='none',duration_ms=round(seconds*1000),
                start=pose(x,y,z),expect_stop=pose(*ARRIVALS['tap_ring']['position']),
                tolerance_xy=4,tolerance_z=4,actor_collision=False,actor_ai=True)
def locks(hack=True):
    s=[new(hack),check(map=MAP),check(qbit_clear=[100607])]
    s+=kill(1)+kill(2)
    s+=[move(1100,1000,0,0,1,(1868,1000)),move(4100,1000,0,0,1.5,(5252,1000))]
    s+=[at(5300,1650,0,90,-.3),step('press_interact',expect={'kind':'world_item'}),
         check(inventory_any_member=[{'item_id':11304}])]
    x,y=zone.TAP_LOCKS[0];s+=click(x-220,y,event=80)
    if hack:s+=[var(11,1)]
    return s
s=locks()+click(6328,-300,yaw=90,event=81)+[var(12,1)]+click(7460,1525,yaw=180,event=82)+[
    answer(83),wait(2.1),var(1,1),check(qbit_clear=[100607]),door(3,'closed'),door(4)]
s += [move(5728,2200,0,90,.65,(5728,2699)),move(5728,2700,0,180,.297,(5500,2700)),
      move(5500,2700,0,90,1.5625,(5500,3900)),var(16,1),wait(2.1),door(5,'closed'),
      check(actor_visible={'actor_index':groups['7'][0],'dead':False})]
s += kill(7)+kill(3)
s += [move(5500,3900,0,0,1.078,(6328,3900)),move(6328,3900,0,90,2.474,(6328,5750),512),
      var(17,1),wait(2.1),door(6,'closed'),check(actor_visible={'actor_index':groups['8'][0],'dead':False})]
s += kill(8)
s += [move(6328,5750,512,90,.576,(6328,6192)),move(6328,6192,512,180,1.599,(5100,6192)),
      move(5100,6192,512,90,1.385,(5100,7256)),move(5100,7256,512,180,1.042,(4300,7256)),
      move(4300,7256,512,270,1.385,(4300,6192))]
s += click(4180,6192,512,180,72)+[wait(1),door(2),move(4180,6192,512,180,1.193,(3264,6192))]
s += click(3264,5800,512,270,51)+[
      step('select_topic',kind='map_transition_cancel',source_id=0,action_id=0,match_label='Close'),check(map=MAP),
      step('press_interact',expect={'kind':'event_target','triggered_event':51}),
      step('select_topic',kind='map_transition_confirm',source_id=0,action_id=0,selection_index=0,label='OK'),
      check(map='hes_out4.odm'),check(qbit_set=[100607])]
write('d13_main_path',s)
write('d13_smoke',[new(),wait(),check(map=MAP),check(actor_visible={'actor_index':groups['5'][0],'combat_targeting_party':False}),door(3),door(4,'closed')])

armed=s[:next(i for i,v in enumerate(s) if v.get('movement_segment',{}).get('start',{}).get('x')==5728)]
s=locks(False)+[answer(80),var(14,1),check(actor_visible={'actor_index':groups['5'][0],'dead':False}),
    step('save_game',name='d13_override_first'),wait(60),var(15,60),step('save_game',name='d13_override_second'),check(actor_visible={'actor_index':groups['6'][0],'dead':False})]
s+=kill(5)+kill(6)+[wait(60),var(11,1),var(14,0),var(15,120),check(qbit_clear=[100607])]
write('d13_override',s)
# Let the native clock reach one second, then save/reload that state and watch it vent.
s=armed+[var(2,118),step('save_game',name='d13_running'),step('load_game',name='d13_running'),var(2,118),
    wait(117),var(2,1),step('save_game',name='d13_one_second'),step('load_game',name='d13_one_second'),var(2,1),
    vent(7460,1525,0,2.1),var(1,0),var(2,120),var(11,1),var(12,1),var(13,0),var(16,0),var(17,0),
    check(qbit_clear=[100607]),check(input_prompt={'active':True,'event_id':83}),answer(83,'No'),wait(2.1),
    door(3),door(4,'closed'),door(5),door(6)]
write('d13_vent',s)
s=[new(),bit(100015),bit(100013),bit(100052)]+[bit(q) for q in range(100040,100044)]
s+=click(200,1000,yaw=180,event=50)+[check(map='hes_d12.blv'),
    step('set_pose',map='hes_d12.blv',x=1600,y=19300,z=2304,yaw=math.pi/2,pitch=0),
    step('press_interact',expect={'kind':'event_target','triggered_event':53}),answer(53),check(map=MAP)]
write('d13_round_trips',s)
s=[new()]+kill(1)+kill(2)+[at(5500,1660,yaw=210),step('spawn_actor',monster_id=10242,count=1,x=5000,y=1660,z=0,group=9),
    check(actor_visible={'actor_index':28,'report_state':True}),step('charge_actor',actor_index=28),wait(2),check(actor_visible={'actor_index':28,'report_state':True}),check(charges={'min_started':1,'min_hits':1}),
    step('press_interact',expect={'kind':'event_target','triggered_event':80})]
write('d13_charge',s)

# Timed route rehearsal: native firing/recovery and moving enemies, with actor-body collisions disabled.
# Difficulty balance still needs the integrator's human tour; this measures the escape's clock allowance.
import copy
main=yaml.safe_load((P/'d13_main_path.yml').read_text())['steps']
start=next(i for i,v in enumerate(main) if v.get('movement_segment',{}).get('start',{}).get('x')==5728)
finish=next(i for i,v in enumerate(main) if v.get('press_interact',{}).get('expect',{}).get('triggered_event')==51)
for mode in ('bare','fighting'):
    timed=copy.deepcopy(main)
    if mode=='fighting':
        for member in timed[0]['new_game_flow']['party']['members']:
            member.update(level=135,might=150,accuracy=200,speed=150,endurance=150,equipment={'main_hand':11002})
            member['skills'].append(dict(name='Energy Guns',level=20,mastery=3))
    result=[];elapsed=0
    for i,v in enumerate(timed):
        movement=v.get('movement_segment')
        if movement:
            movement.pop('delta_game_minutes',None)
            if i>=start:movement['actor_ai']=mode=='fighting'
        if mode=='fighting' and i>=start and 'damage_actor' in v:continue
        if i==finish:result.append(check(runtime_event_variable={'id':125,'min':1,'max':119}))
        result.append(v)
        if start<=i<=finish:
            elapsed+=(movement or {}).get('duration_ms',0)/1000+v.get('advance_runtime',{}).get('seconds',0)
        if mode=='fighting' and i>=start and v.get('assert',{}).get('actor_visible',{}).get('actor_index')==groups['7'][0]:
            result += [move(5500,3900,0,0,2.409,(7350,3900),ai=True),at(7350,3900,0,180),
                       step('press_action',action='attack',seconds=15),at(7350,3900,0,160),
                       step('press_action',action='attack',seconds=15)]
            result += [check(actor_visible={'actor_index':a,'report_state':True}) for a in groups['7']+groups['3']]
            result += [move(7350,3900,0,180,2.409,(5500,3900),ai=True)]
            elapsed+=34.818
        if mode=='fighting' and movement and movement['expect_stop']['x']==5100 and movement['expect_stop']['y']==7256:
            result += [at(5100,7256,512,0),step('press_action',action='attack',seconds=20),check(charges={'min_started':1})]
            result += [check(actor_visible={'actor_index':a,'report_state':True}) for a in groups['8']]
            elapsed+=20
    write('d13_timing_'+mode,result)
    print(mode,'rehearsal seconds',round(elapsed,3))

# Reset after both cave-ins, retaining one living enemy in each hidden group and their dead companions.
prefix=main[:next(i for i,v in enumerate(main) if v.get('movement_segment',{}).get('start',{}).get('y')==5750)]
prefix=[v for v in prefix if v.get('damage_actor',{}).get('actor_index') not in (groups['7'][-1],groups['8'][-1])]
s=prefix+[step('save_game',name='d13_collapse_shown'),vent(6328,5750,512,121),var(1,0),var(2,120),var(11,1),var(12,1),var(13,0),var(16,0),var(17,0),
    check(qbit_clear=[100607]),check(input_prompt={'active':True,'event_id':83}),
    answer(83,'No'),wait(2.1),door(3),door(4,'closed'),door(5),door(6),
    check(actor_visible={'actor_index':groups['7'][0],'current_hp':0}),
    check(actor_visible={'actor_index':groups['8'][0],'current_hp':0})]
s += [step('save_game',name='d13_after_vent')]
write('d13_collapse_reset',s)
