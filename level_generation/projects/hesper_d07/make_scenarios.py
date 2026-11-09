"""Native D7 checks; poses follow the plan, boss indices come from the semantic record."""
import json
import math
from pathlib import Path
import yaml

P=Path(__file__).resolve().parent
sem=json.loads((P/'source/hes_d07.semantic.json').read_text())
BOSS=next(i for i,a in enumerate(sem['actors']) if a['group']==8)
COUPLED=next(i for i,a in enumerate(sem['actors']) if a['group']==9)
MAP='hes_d07.blv'

def pose(x,y,z=-512,yaw=0,pitch=0):return dict(map=MAP,x=x,y=y,z=z,yaw=yaw,pitch=pitch)
def new(mastery=3):
    members=[dict(name=n,**{'class':'Knight'},level=1000,
                  skills=[dict(name='Hacking',level=12,mastery=mastery)] if mastery else [],equipment={})
             for n in ('Ada','Bram','Cyra','Dana','Eli')]
    return dict(new_game_flow=dict(start_map=MAP,party=dict(members=members)))
def var(n,v):return {'assert':{'state_dump_map_var':dict(index=n,value=v)}}
def click(x,y,z=-512,yaw=0,pitch=0):return [dict(set_pose=pose(x,y,z,yaw,pitch)),dict(press_interact={})]
def close():return dict(press_action=dict(action='cancel_dialog'))
def waitdoor(n):return dict(wait_until=dict(timeout_runtime_seconds=2,**{'assert':{'mechanism':dict(id=n,state='open')}}))
def walk(x,y,ex,ey,z=-512,ez=None,seconds=None):
    angle=math.atan2(ey-y,ex-x);duration=seconds or math.hypot(ex-x,ey-y)/768
    return dict(movement_segment=dict(input='forward',seconds=round(duration,4),start=pose(x,y,z,angle),
        expect_stop=pose(ex,ey,z if ez is None else ez,angle),delta_game_minutes=0,
        tolerance_xy=80,tolerance_z=35,loose_tolerance=True,actor_collision=False,actor_ai=False))
def idle(seconds,x=4800,y=300,z=0):
    return dict(movement_segment=dict(input='none',seconds=seconds,start=pose(x,y,z),expect_stop=pose(x,y,z),
        tolerance_xy=2,tolerance_z=2,actor_collision=False,actor_ai=False))
def save(name):return dict(save_game='d07_'+name)
def load(name):return dict(load_game='d07_'+name)
def kill():return [dict(set_pose=pose(4800,300,0)),dict(damage_actor=dict(actor_index=BOSS,amount=100000,tier='kreegan_energy')),
    dict(damage_actor=dict(actor_index=BOSS,amount=100000,tier='kreegan_energy')),dict(advance_runtime=dict(seconds=3.2)),
    {'assert':{'actor_visible':dict(actor_index=BOSS,dead=True,hp=0)}},var(6,1),var(7,1),
    {'assert':{'qbit_set':[100009],'qbit_clear':[100209]}},
    {'assert':{'world_item_state':dict(item_id=11332,present=True)}}]
def collar(k):
    x,y=sem['couplings'][k]
    return click(x,y-350,yaw=math.pi/2)
def write(name,steps):
    (P/(name+'.yml')).write_text(yaml.safe_dump(dict(id='hesper.'+name,world='hesper',mode='faithful',steps=steps),sort_keys=False))
def crown_return(event):
    x,y,z,yaw=json.loads((P.parent/'hesper_out4/out4_build.json').read_text())['door_poses'][str(event)]
    return [dict(set_pose=dict(map='hes_out4.odm',x=x,y=y,z=z,yaw=yaw,pitch=0)),
            dict(press_interact={}),{'assert':{'map':MAP}}]

base=yaml.safe_load((P.parent/'hesper_d06/d06_main_path.yml').read_text())['steps']
def convert(steps):
    return yaml.safe_load(yaml.safe_dump(steps).replace('hes_d06','hes_d07').replace('d06_','d07_').replace('100210','100209').replace('100010','100009').replace('11215','11004'))
main=convert(base[:20])
# Entry stays west of the conveyor, then traverses the clear aisle to the lever.
main += [var(13,1),walk(8300,5472,8300,6000),walk(8300,6000,10550,6000)]
main += click(10650,6100,yaw=0)+[var(13,2),save('line_stopped'),idle(41),var(14,4),save('line_stopped_after_41')]
main += click(10600,7010,yaw=math.pi/2)+[waitdoor(7)]
main += [walk(10600,7010,10600,7700),walk(10600,7700,10100,7700),walk(10100,7700,10100,8316),walk(10100,8316,9800,8316)]
main += click(9780,8316,yaw=math.pi)+[waitdoor(8),walk(9780,8316,9200,8316)]
main += convert(base[28:45])
main += [var(10,1),var(36,1),save('quiet_free'),load('quiet_free'),var(10,1)]
main += kill()+[{'assert':{'gold':30000}},waitdoor(5),waitdoor(6)]
main += convert(base[69:83])
main += click(3424,12280,yaw=math.pi/2)+[{'select_topic':{'kind':'map_transition_confirm','source_id':0,'action_id':0,'selection_index':0,'label':'OK'}},{'assert':{'map':'hes_out4.odm'}}]
main += crown_return(56)+[var(7,1)]
write('d07_main_path',main)

loud=[new(0),dict(setup_shortcut=dict(kind='set_qbit',id=100209))]
# A real cache pickup plus two carried charges; save/load installs shortcut inventory in the native party.
loud += [dict(press_interact=dict(kind='world_item',world_item_index=0,pose=pose(2950,5870,yaw=math.pi/2,pitch=-.15)))]
loud += [dict(setup_shortcut=dict(kind='grant_item',item_id=11304)),dict(setup_shortcut=dict(kind='grant_item',item_id=11304)),save('charges'),load('charges')]
loud += [walk(6170,8316,6330,8316),var(36,1),var(10,0),save('coupled')]
loud += [idle(6.2,4800,6200,-512),var(30,1),save('core_mine_armed')]
for k in range(3):loud+=collar(k)+[var(k+1,2)]
loud += [var(5,1),var(10,1),var(30,2),var(35,2),save('loud_free'),idle(31),var(9,31),save('alarm_waves')]
loud += kill()+[{'assert':{'mechanism':dict(id=5,state='closed')}},waitdoor(6),save('loud_dead'),load('loud_dead'),var(3,2),var(10,1)]
write('d07_loud_path',loud)

special=[new(4),dict(setup_shortcut=dict(kind='grant_item',item_id=11304)),save('gm_charge'),load('gm_charge')]
for k in range(3):special+=collar(k)+[var(k+1,1),close()]
special += [var(5,0),var(10,1),{'assert':{'inventory_any_member':[{'item_id':11304}]}},save('gm_free')]
special += [new(),walk(7850,5472,8400,5472),var(13,1),idle(20.1),var(14,20),save('line_first'),
            idle(20),var(14,40),var(13,2),save('line_second'),load('line_second'),var(14,40)]
# One actual mine: damage once, survive save/load and cross the spent plate unharmed.
special += [new(),{'assert':{'party_health':{'full':True}}},walk(11000,7370,11000,7550),var(20,2),
            {'assert':{'party_health':{'full':False}}},save('mine_spent'),load('mine_spent'),
            walk(11000,7370,11000,7550),var(20,2),{'assert':{'party_health':{'full':False}}},save('mine_crossed_again')]
write('d07_factory_and_mines',special)
# The common arc checks use the same real movement tests as D6 (exclude D6-specific vents and panels).
arc=yaml.safe_load((P.parent/'hesper_d06/d06_hazards.yml').read_text())['steps'][:12]
write('d07_arcs',convert([step for step in arc if step.get('assert',{}).get('state_dump_map_var',{}).get('index')!=10]))

shots=[]
for s in yaml.safe_load((P.parent/'hesper_d06/review_tour_01.yml').read_text())['shots']:
    if s['name'] not in ('pumps','loop'):shots.append(s)
for name,pos,yaw in [('assembly',[8300,6000,-512],0),('capgallery',[9800,7850,-512],0),('bulwark',[4800,6200,-512],math.pi/2)]:
    shots.append(dict(name=name,position=pos,yaw=yaw,pitch=0))
(P/'review_tour_01.yml').write_text(yaml.safe_dump(dict(output_dir=str(P/'review/build01'),settle_seconds=1.5,exit=True,shots=shots),sort_keys=False))
print('D7 scenarios and tour generated; free/coupled actor ids',BOSS,COUPLED)

# Front exit independently, plus one native charge by the stand-in Harrower.
exits=[new(),dict(set_pose=pose(4350,2000,0,math.pi/2)),
       dict(charge_actor=dict(actor_index=0)),dict(advance_runtime=dict(seconds=2)),
       {'assert':{'charges':{'min_started':1}}}]
exits+=click(4800,180,0,yaw=-math.pi/2)+[
    {'select_topic':{'kind':'map_transition_confirm','source_id':0,'action_id':0,'selection_index':0,'label':'OK'}},
    {'assert':{'map':'hes_out4.odm'}}]
exits+=crown_return(51)
write('d07_front_and_charge',exits)
