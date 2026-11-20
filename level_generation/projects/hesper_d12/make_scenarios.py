"""Generate native interaction scenarios from D12's built actor indices."""
import json
import math
import sys
from pathlib import Path
import yaml

P = Path(__file__).resolve().parent
report = json.loads((P / 'd12_build.json').read_text())
groups = report['actor_groups']
# Ssekh's Fang, Mraal's Cleaver and Xith's Sight spawn before the Court Seal.
court_seal_index = len(json.loads((P / 'runtime/hes_d12.scene.yml').read_text())['initial_state']['sprite_objects']) + 3
sys.path.insert(0,str(P.parents[2]/'util'))
from map_export import parse_blv_file
native=parse_blv_file(P/'runtime/hes_d12.blv')['payload']


def control_face(x,y,z,event):
    # The same ray after a ride must hit the other landing's control, without resetting the party's pose.
    found=[]
    for face in native['faces']:
        if face['face_param']['cog_triggered']!=event: continue
        vertices=[native['vertices'][i] for i in face['vertex_indices']]
        if any(abs(v['x']-x)>.1 for v in vertices): continue
        cross=[(b['y']-a['y'])*(z-a['z'])-(b['z']-a['z'])*(y-a['y'])
               for a,b in zip(vertices,vertices[1:]+vertices[:1])]
        if min(cross)>=0 or max(cross)<=0: found.append(face['index'])
    assert len(found)==1,(x,y,z,event,found)
    return found[0]


def landed(x,y,z,event):
    return {'press_interact':{'expect':{'kind':'event_target','triggered_event':event,
                                      'face_index':control_face(x,y+.1,z-.01,event)}}}



def pose(x, y, z=0, yaw=90, pitch=0):
    return dict(map='hes_d12.blv', x=x, y=y, z=z, yaw=math.radians(yaw), pitch=pitch)


def step(step_kind, **args): return {step_kind: args}
def check(**args): return step('assert', **args)
def at(x, y, z=0, yaw=90, pitch=0): return step('set_pose', **pose(x,y,z,yaw,pitch))
def click(x,y,z=0,yaw=90,pitch=0): return [at(x,y,z,yaw,pitch),step('press_interact')]
def wait(seconds=2): return step('advance_runtime',seconds=seconds)
def door(n,state='open'):
    return {'wait_until':{'timeout_runtime_seconds':6.1 if n in (21,22) else 3.1 if n in (5,17) else 2.1 if n in (1,2,3) else 1.6,'assert':{'mechanism':{'id':n,'state':state}}}}
def bit(n): return step('setup_shortcut',kind='set_qbit',id=n)
def kill(group):
    return [step('damage_actor',actor_index=i,amount=1000000,tier='kreegan_energy')
            for i in groups[str(group)] for _ in range(1 if group==19 else 2)]


def move(x,y,z,yaw,seconds,end,zend=None):
    return step('movement_segment',input='forward',duration_ms=round(seconds*1000),delta_game_minutes=0,
                start=pose(x,y,z,yaw),expect_stop=pose(end[0],end[1],z if zend is None else zend,yaw),
                loose_tolerance=True,tolerance_xy=100,tolerance_z=40,actor_collision=False,actor_ai=False)


def new(hack=3,mapfile="hes_d12.blv"):
    skills=[dict(name='Hacking',level=12,mastery=hack)] if hack else []
    return step('new_game_flow',start_map=mapfile,party={'food':200,'members':[
        dict(name='Crown tester '+str(i+1),**{'class':'Knight'},level=1000,endurance=100,skills=skills,equipment={})
        for i in range(5)]})


def write(name,steps):
    (P/(name+'.yml')).write_text(yaml.safe_dump(
        dict(id='hesper.d12.'+name,world='hesper',mode='faithful',steps=steps),sort_keys=False))


s=[new(),check(map='hes_d12.blv')]
s+=click(0,400,yaw=270)+[check(mechanism={'id':1,'state':'closed'}),bit(100603)]
s+=click(-900,1450,yaw=90)+[door(1)]
s+=click(0,1000)+[door(2),move(0,1050,0,90,.8,(0,1660)),check(map_var_changed={'index':4,'value':1})]
for group in range(1,7): s+=kill(group)
# Stand on the trophy plinth and try to walk through the founder-head decoration.
s+=[step('movement_segment',input='forward',duration_ms=500,delta_game_minutes=0,
         start=pose(-3064,6780,112),expect_stop=pose(-3064,6811,112),
         tolerance_xy=4,tolerance_z=4,actor_collision=False,actor_ai=False)]
s+=[wait()]+click(0,3450)+[door(3),move(0,3500,0,90,.7,(0,4030)),
    move(800,4000,0,90,2.5,(800,5910)),move(0,6000,0,90,2.5,(0,7910),720)]
s+=click(0,8000,z=768)+[door(5),move(0,8040,768,90,.7,(0,8570),768),
    check(state_dump_named_map_var={'name':'herald','value':1}),move(100,8600,768,90,.5,(100,8980),704),
    check(map_var_changed={'index':1,'value':0})]
s+=kill(7)+[wait()]
for lord,group,item in ((1,16,11425),(2,17,11426),(3,18,11510)):
    s+=[move(100,8600,768,90,.5,(100,8980),704),wait(),check(map_var_changed={'index':1,'value':lord}),door(5+lord)]
    s+=kill(group)+[wait(6),check(world_item_state={'item_id':item,'present':True})]
    if lord==3: s+=[check(world_item_state={'item_id':11436,'present':True})]
s+=[check(map_var_changed={'index':1,'value':4}),check(map_var_changed={'index':5,'value':1})]
s+=[at(340,10056,704,180,-.75),{'press_interact':{'kind':'world_item','world_item_index':court_seal_index,'item_id':11510,
    'pose':pose(340,10056,704,180,-.75),'expect':{'kind':'world_item','item_id':11510}}},
    check(inventory_any_member=[{'item_id':11510}])]
s+=kill(8)+[wait()]+click(0,11600,z=768)+[door(20),move(0,11700,768,90,.8,(0,12310))]
s+=click(350,12520,z=768,yaw=0)+[door(21),landed(588,12520,2464,121),door(21,'closed'),
    landed(588,12520,928,121),door(21)]
s+=[move(0,12900,2304,90,.8,(0,13510)),check(map_var_changed={'index':6,'value':1})]
s+=kill(15)+[wait()]+click(0,15400,z=2304)+[door(17),move(0,15450,2304,90,.7,(0,15980)),
    bit(100023),bit(100215),wait(11),check(state_dump_named_map_var={'name':'phase1_spoken','value':1})]
s+=kill(13)+[wait(),check(qbit_set=[100608]),check(map_var_changed={'index':2,'value':2}),
    check(actor_visible={'actor_index':121,'monster_id':10120,'max_hp':30000,'report_state':True})]+kill(12)+[wait(6),
    check(actor_visible={'actor_index':4,'hostile_to_party':False,'combat_targeting_party':False,'report_state':True}),
    check(actor_visible={'actor_index':121,'shield_fraction':[0,0.999],'report_state':True})]
s+=kill(11)+[wait(),check(map_var_changed={'index':2,'value':3}),
    check(actor_visible={'actor_index':122,'monster_id':10146,'max_hp':30000,'report_state':True})]
s+=kill(19)+[wait(),check(qbit_set=[100032]),step('save_game',name='d12_before_choice')]
for answer,q,items in [('Free her',100033,[11432]),('Tear it out',100034,[11433]),
                        ('Both survive',100035,[11432,11433])]:
    s+=[step('load_game',name='d12_before_choice')]+click(0,13880,z=2304,pitch=.5)
    s+=[step('answer_input',text=answer),check(qbit_set=[q,100015,100216,100052],qbit_clear=[100215]),
        step('press_action',action='cancel_dialog'),
        check(held_item={'active':True,'item_id':items[-1]}),check(held_item={'active':False}),
        check(inventory_any_member=[{'item_id':i} for i in items])]
    for member in range(5):
        for tag,value in ((32,15),(33,15),(34,15),(35,100),(36,15),(37,15),(38,15)):
            s += [check(runtime_event_variable={'id':tag,'member_index':member,'value':value+(10 if q==100034 else 0)})]
    s+=click(1600,18700,z=2304)+[check(mechanism={'id':19,'state':'closed'})]
s += [bit(100013)]+[bit(q) for q in range(100040,100044)]
s += click(1600,18700,z=2304)+[step('answer_input',text='No'),door(19),
    move(1600,18700,2304,90,.8,(1600,19310)),check(map='hes_d12.blv'),
    step('save_game',name='d12_complete'),step('load_game',name='d12_complete'),
    check(qbit_set=[100015,100035,100032,100608]),check(map_var_changed={'index':2,'value':4})]
write('d12_main_path',s)

s=[new(2,'hes_d15.blv'),step('set_pose',map='hes_d15.blv',x=14292,y=14930,z=0,yaw=math.pi/2,pitch=0),
    step('press_interact'),check(map='hes_d12.blv'),check(runtime_event_variable={'id':3,'member_index':0,'min':1}),check(qbit_clear=[100603]),bit(100217),wait(1),check(party_health={'full':True})]
s+=click(8660,2200,-1536,180)+[door(23),move(8620,2200,-1536,180,.8,(8010,2200)),
    check(map_var_changed={'index':4,'value':1})]
s+=kill(9)+[wait(),check(world_item_state={'item_id':11437,'present':True})]+click(6400,4860,-1536,90,.4)+[
    check(qbit_set=[100602,100017,100603],qbit_clear=[100217]),step('press_action',action='cancel_dialog'),door(1),
    step('save_game',name='d12_grid'),step('load_game',name='d12_grid'),
    check(qbit_set=[100602,100017,100603])]
s+=click(6400,4860,-1536,90,.4)+[check(qbit_set=[100017]),step('press_action',action='cancel_dialog')]
s+=click(2400,2364,-1536,0)+[door(22),at(2164,2364,-1536,0)]
s+=click(2400,2364,-1536,0)+[door(22,'closed')]
s+=[landed(2652,2364,160,122),door(22),check(map='hes_d12.blv')]
write('d12_backdoor',s)
write('d12_smoke',[new(),wait(),check(map='hes_d12.blv'),check(qbit_clear=[100032]),
                  check(actor_visible={'actor_index':78,'monster_id':10145,'max_hp':30000})])

# Actual cross-map clicks use the outdoor builder's published ray poses.
out4=json.loads((P.parent/'hesper_out4/out4_build.json').read_text())
def outside(event):
    x,y,z,yaw=out4['door_poses'][str(event)]
    return [step('set_pose',map='hes_out4.odm',x=x,y=y,z=z,yaw=yaw,pitch=0),step('press_interact')]
s=[new(),bit(100603)]+click(-900,1450,yaw=90)+[door(1)]
s+=[at(0,400,yaw=270),step('press_interact',expect={'kind':'event_target','triggered_event':50})]+[step('select_topic',kind='map_transition_confirm',source_id=0,action_id=0,selection_index=0,label='OK'),
    check(map='hes_out4.odm')]+outside(53)+[check(map='hes_d12.blv')]
s+=click(8164,4180,-1536,90)+[step('select_topic',kind='map_transition_confirm',source_id=0,action_id=0,selection_index=0,label='OK'),
    check(map='hes_out4.odm')]+outside(57)+[check(map='hes_d12.blv')]
s+=click(9064,2560,-1536,90)+[check(map='hes_d15.blv'),
    step('set_pose',map='hes_d15.blv',x=14292,y=14930,z=0,yaw=math.pi/2,pitch=0),
    step('press_interact'),check(map='hes_d12.blv'),check(qbit_set=[100603])]
write('d12_round_trips',s)
