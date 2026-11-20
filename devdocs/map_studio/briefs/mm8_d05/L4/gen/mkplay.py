import yaml
steps=[{'new_game_flow':{'start_map':'calib_mm8_d05.blv'}},{'assert':{'map':'calib_mm8_d05.blv'}},{'setup_shortcut':{'kind':'immortal','value':True}}]
def W(x,y,z,r=48,t=90): steps.append({'walk_to':{'x':x,'y':y,'z':z,'radius':r,'timeout_seconds':t,'clear_hostiles':1500}})
def LUA(src): steps.append({'play_lua':{'source':src}})
def A(x,y,r,z0,z1):
    LUA('wait(1.5)\n'); steps.append({'assert':{'party_position':{'x':x,'y':y,'radius':r,'z_min':z0,'z_max':z1}}})
def opendoor(evt,door): LUA('click(%d); wait(6)\nif door_state(%d) ~= "open" then error("event %d did not open door %d: " .. door_state(%d)) end\n'%(evt,door,evt,door,door))
# the tower, down three flights
A(-3008,-1536,200,1900,1940)
W(-2800,-1480,1920); W(-2800,-420,1650,r=48); A(-2800,-420,120,1600,1700)
W(-2800,-224,1616); W(-3900,-224,1340); W(-4080,-224,1328); A(-4080,-224,120,1320,1336)
W(-4080,-1700,960); W(-4080,-2000,944); A(-4080,-2000,140,940,950)
# the stairwell and the tunnel
W(-2760,-1344,944,t=120); W(-1830,-1344,560); A(-1830,-1344,120,540,640)
for x,y,z in ((-1560,-1380,528),(-1340,-1600,480),(-1100,-1740,440),(-832,-1728,384),(-560,-1690,345),(-380,-1470,345),(-200,-1220,280),(0,-1060,225),(64,-860,180),(64,-700,160)): W(x,y,z,r=48)
W(64,-512,160); A(64,-512,120,152,168)
# the trap hall: stones are up; one sinks when used
LUA('if door_state(9) ~= "open" then error("stone 94 does not start up: " .. door_state(9)) end\nclick(76); wait(7)\nif door_state(9) ~= "closed" then error("stone 94 did not sink: " .. door_state(9)) end\n')
W(64,-250,0); A(64,-250,140,-4,8)
# the buttons work only in order
LUA('click(73); wait(2)\nif door_state(3) ~= "closed" then error("step button 2 worked before button 1") end\nlog("button 2 first: " .. status())\n')
opendoor(55,20); W(-660,896,0); LUA('click(72); wait(4)\nif door_state(1) ~= "open" or door_state(2) ~= "open" then error("button 1 did not raise the first steps") end\n')
W(0,896,0); opendoor(54,19); W(790,896,0); LUA('click(73); wait(4)\nif door_state(3) ~= "open" then error("button 2 did not raise its steps") end\n')
W(300,300,0); W(-300,0,0); opendoor(57,22); W(-660,0,0); LUA('click(74); wait(4)\nif door_state(5) ~= "open" then error("button 3 did not raise its steps") end\n')
W(0,-250,0); opendoor(56,21); W(790,0,0); LUA('click(75); wait(4)\nif door_state(7) ~= "open" then error("button 4 did not raise its steps") end\n')
# up the raised steps to the north landing
W(560,600,0); W(580,1200,0); W(560,1344,0,r=60); W(64,1344,160,r=48); A(64,1344,120,150,170)
W(64,1500,160); W(64,1792,160)
opendoor(58,23); W(-200,1792,160,r=70); LUA('loot_chest(43)\n'); W(64,1792,160)
opendoor(59,24); W(330,1792,160,r=70); LUA('loot_chest(44)\n'); W(64,1792,160)
W(64,2304,160); W(700,2304,-64,r=48); W(1640,2304,-352); A(1640,2304,120,-360,-340)
# door 5, then fall off the walkway and come back by the return stair and door 6
opendoor(60,25); W(2300,2304,-352)
W(2500,2700,-1056,r=140); LUA('wait(2)\n'); A(2500,2700,200,-1060,-1050)
W(2330,2576,-1056); W(2112,2576,-1056); W(2112,2304,-1056); W(900,2304,-1056,t=120); W(500,2304,-880); W(250,2304,-864); W(250,2688,-864)
W(1000,2688,-600,r=48); W(1536,2688,-352); W(1728,2688,-352); A(1728,2688,120,-360,-344)
LUA('if door_state(34) ~= "closed" then error("door 6 does not start shut") end\n'); opendoor(61,34); W(1728,2304,-352)
W(2300,2304,-352)
for x,y in ((2520,2240),(2700,2000),(2900,1750),(3100,1690),(3330,1800),(3360,1960),(3220,2240),(3120,2560),(3140,2800),(3300,2900),(3520,2900),(3700,2720),(3800,2500),(3860,2300),(3960,2160),(4100,2200),(4230,2300)): W(x,y,-352,r=50,t=60)
A(4230,2300,90,-360,-344)
W(4380,2380,-352,r=60); W(4800,1920,-640,r=48); W(5100,1900,-640); W(5860,2432,-640)
opendoor(51,16); W(6200,2432,-656)
LUA('click(52); wait(3)\nif door_state(17) ~= "closed" then error("the far door opened with the panels lit") end\nfor e = 64, 71 do click(e); wait(1) end\n')
opendoor(52,17); W(7450,2432,-640); W(7900,2850,-640); W(8512,2900,-640); W(9300,2620,-640); W(9900,2432,-640)
# the great hall, its chest, the back stair and the back door chamber
W(10368,3400,-640,t=120); LUA('loot_chest(45)\n')
W(13600,2432,-640,t=180); W(14080,2432,-640); W(14080,2100,-600,r=48); W(14080,1100,-128); W(13700,1000,-128); W(13700,1300,-64,r=48); W(13700,2240,384); A(13700,2240,120,376,392)
W(13120,2432,384)
W(13700,2240,384); W(13700,1100,-128,t=120); W(14080,1000,-128); W(14080,2300,-640,t=120); W(13700,2432,-640)
# the maze: entry door, then the right buttons
W(9300,2620,-640,t=240); W(8512,2900,-640); W(8512,2700,-640); opendoor(50,15); W(8512,1800,-640)
def hop(evt,door,bx,by,through):
    W(bx,by,-640,r=48); LUA('if door_state(%d) ~= "closed" then error("maze door %d does not start shut") end\n'%(door,door)); opendoor(evt,door)
    for p in through: W(p[0],p[1],-640,r=48)
hop(2,27,8512,1640,[(9408,1640),(9408,1000)])            # hall 22 -> 27a by door 53
hop(5,30,9408,800,[(9024,800),(9024,-500)])               # 27a -> long passage -> 27b by door 56
hop(16,42,9024,-730,[(9216,-730),(9216,-1300)])           # 27b -> 29a by door 67
hop(23,49,8832,-1500,[(8640,-1500),(8640,-2100)])         # 29a -> 29b by door 74
hop(29,55,8640,-2260,[(8448,-2260),(8448,-2880)])         # 29b -> 30 by door 80
hop(38,64,9216,-3030,[(9408,-3030),(9408,-4288),(9800,-4288)])  # 30 -> the cave by door 89
# a wrong button: the closet opens and something is summoned
LUA('click(37); wait(6)\nif door_state(63) ~= "open" then error("button 46 did not open closet door 88") end\nif door_state(64) ~= "closed" then error("button 46 did not shut door 89") end\nclick(38); wait(6)\n')
# across the causeway, the niche door
W(11000,-4288,-640,t=120); W(12000,-4288,-640); W(10944,-3700,-640,r=120,t=120) 
steps.append({'clear_hostiles':{'radius':1500}})
opendoor(53,18); W(10944,-3330,-640,r=48)
A(10944,-3330,140,-650,-630)
doc={'id':'studio.calib_mm8_d05.walk','title':'Abandoned Temple rebuild: the critical path and every mechanism','world':'mm8','mode':'faithful','steps':steps}
open('/home/pjasicek/github/OpenYAMM/devdocs/map_studio/briefs/mm8_d05/L4/playtest.yml','w').write("# Written by output/studio_cal/mm8_d05/mkplay.py. Event and door numbers are those of ids.lock.yml.\n"+yaml.safe_dump(doc,sort_keys=False,width=1000,default_flow_style=None))
print(len(steps),'steps')
