-- Deepwell: the three locks, persistent countdown, collapse and vent retry.
local handlers = {}
local EXITS = select(1, D13_EXITS, nil)
local RESET = select(1, D13_RESET, nil)
SetMapMetadata({onLoad = {}, onLeave = {}, timers = {{eventId=3, repeating=true, intervalGameMinutes=0.5}}})
local function value(n)
    local result=0
    for power=7,0,-1 do
        local candidate=result+2^power
        if IsAtLeast(MapVar(n),candidate) then result=candidate end
    end
    return result
end
local function set(n,v) SetValue(MapVar(n),v) end
local function torn() return IsQBitSet(QBit(100034)) end
local function hide(g,v) evt.SetMonGroupBit(g,MonsterBits.Invisible,v and 1 or 0) end
local function travel(d) evt.MoveToMap(d.x,d.y,d.z,d.direction,0,0,0,0,d.map) end
local function pulse(on)
    if on then evt.SetSprite(123,1,'hes_d13_alarm_beacon') else evt.SetSprite(123,1,'hes_d13_alarm_beacon_off') end
    evt.SetLight(3,on and 1 or 0)
end
local function appearance()
    local hot=value(1)==1
    evt.SetTexture(200,hot and 'htexchot' or 'htexch')
    evt.SetTexture(201,hot and 'htcorehot' or 'htcore')
    evt.SetTexture(202,hot and 'htalarm' or 'hcstripd')
    evt.SetLight(4,hot and 1 or 0); pulse(hot)
    evt.SetDoorState(3,hot and DoorAction.Close or DoorAction.Open)
    evt.SetDoorState(4,hot and DoorAction.Open or DoorAction.Close)
end
local ASTER={
    [120]='It is done. Two minutes. Run: the collapse route, the lift, the plaza. Do not stop for anything.',
    [110]='The route is ahead of you. Keep going.',[100]='One hundred.',[90]='Ninety.',
    [80]="Eighty. Don't stop to fight.",[70]='Seventy. The heat is rising.',[60]='One minute. The lift is ahead.',
    [50]='Fifty.',[40]='Forty. Faster.',[30]='Thirty.',[20]='Twenty. The lift. Now.',[10]='Ten. Go.'}
local PILOT={
    [120]="Core's going critical. Two minutes. I'm coming for the plaza. Run.",[110]='Keep going.',
    [100]='One hundred.',[90]='Ninety.',[80]="Eighty. Don't stop.",[70]='Seventy.',
    [60]='One minute! Where are you?',[50]='Fifty.',[40]='Forty!',[30]='Thirty!',
    [20]='Twenty, get in the lift!',[10]='Ten!'}
local function readout(n)
    evt.StatusText('TAP BREACH: '..n..' - '..(torn() and 'Pilot: '..PILOT[n] or 'Aster: '..ASTER[n]))
end
handlers[1]=function()
    for g=1,8 do evt.SetMonGroupBit(g,MonsterBits.Hostile,1) end
    hide(5,value(14)==0 and value(15)==0); hide(6,value(15)<60)
    hide(7,value(16)==0); hide(8,value(17)==0)
    appearance()
    evt.SetDoorState(5,value(16)==1 and DoorAction.Close or DoorAction.Open)
    evt.SetDoorState(6,value(17)==1 and DoorAction.Close or DoorAction.Open)
end
handlers[3]=function()
    -- Same-map travel closes dialogs; ask on the next native tick after the return.
    if evt.GetMapVar('vent_question')==2 then
        evt.SetMapVar('vent_question',1);handlers[83]();return
    end
    if value(14)==1 then
        local count=value(15)+1;set(15,count)
        if count==60 then hide(6,false) end
        if count>=120 then
            set(11,1);set(14,0);evt.StatusText('The interlocks cycle open under fire.')
        end
    end
    if value(1)~=1 then return end
    for n=16,17 do
        if evt.GetMapVar('block_pending_'..n)==1 then
            evt.SetMapVar('block_pending_'..n,0);evt.SetDoorState(n-11,DoorAction.Close)
            evt.PlaySoundName('emp_grenade',n==16 and 5728 or 4700,n==16 and 2528 or 6192,n==16 and 0 or 512)
        end
    end
    local seconds=value(2)-1;set(2,math.max(seconds,0))
    pulse(seconds%2==0)
    if seconds<=0 then handlers[4]();return end
    if seconds%10==0 then readout(seconds) end
    if seconds%4==0 then evt.SpawnWorldEffect('hesper:fx/d13_steam',6328,1000,96,1,0) end
end
handlers[4]=function()
    set(1,0);set(2,120);set(13,0);set(16,0);set(17,0)
    evt.SetMapVar('block_pending_16',0);evt.SetMapVar('block_pending_17',0)
    hide(7,true);hide(8,true)
    appearance();evt.SetDoorState(5,DoorAction.Open);evt.SetDoorState(6,DoorAction.Open)
    travel(RESET)
    evt.SetMapVar('vent_question',2)
end
handlers[50]=function()
    if value(1)==0 then travel(EXITS.shaft)
    else evt.StatusText('The shaft has fallen in above you.') end
end
handlers[51]=function()
    if value(1)==0 then return end
    set(1,2);SetQBit(QBit(100607));travel(EXITS.pad)
end
handlers[72]=function() evt.SetDoorState(2,DoorAction.Trigger) end
handlers[73]=function()
    if value(1)==0 then evt.SetDoorState(3,DoorAction.Open) else evt.StatusText('The containment door is sealed.') end
end
handlers[74]=function() if value(1)==1 then evt.SetDoorState(4,DoorAction.Open) end end
handlers[80]=function(step)
    if value(11)==1 then evt.StatusText('Coolant interlocks released.');return end
    if value(14)==1 then evt.StatusText('The override is cycling. Hold them off.');return end
    if evt.CheckSkill(const.Skills.Hacking,const.SkillCheck.Expert,1) then
        set(11,1);evt.StatusText('Coolant interlocks released.');return
    end
    if step==1 then set(14,1);set(15,0);hide(5,false);return end
    if step==2 then return end
    AskChoiceWithAnswerSteps(80,0,'Hold the override? They will come for you while it cycles.',
        {{Answer='Yes',Step=1},{Answer='No',Step=2}})
end
handlers[81]=function()
    if value(12)==1 then return end
    if not HasItem(11304) then evt.StatusText('The containment ring wants a Breach Charge.');return end
    evt.ForPlayer(PartySelector.All);evt.Subtract(VarTag.Inventory,11304);evt.ForPlayer(PartySelector.Current)
    set(12,1);evt.StatusText('The charge cracks the containment ring. Red light pours through.')
end
handlers[82]=function()
    if value(1)==1 then return end
    set(13,1);evt.StatusText(torn() and 'The splinter remembers the codes.' or "Aster: My makers' last order was to open it.")
    if value(11)==1 and value(12)==1 then handlers[83]() end
end
handlers[83]=function(step)
    if value(1)~=0 or value(11)==0 or value(12)==0 then return end
    if step==1 then
        set(13,1);set(1,1);set(2,120);evt.SetMapVar('vent_question',0);appearance()
        evt.PlaySoundName('kr_lance_charge',6328,1000,0);readout(120);return
    end
    if step==2 then evt.SetMapVar('vent_question',0);return end
    local question=torn() and "The console's last line: OVERLOAD SEQUENCE ARMED. NO ABORT. BEGIN?"
        or "Aster: Once I begin, there is no stopping it, and no coming back for anything you leave. Remember what you need to remember. Begin the overload?"
    if evt.GetMapVar('vent_question')==1 then
        question=(torn() and 'The tap screams, and the safety your makers built into it vents the heat into the rock. The overload is spent. You can begin again. '
            or "White light, a roar, and then nothing. Aster: I held it. Barely. It is building again. Tell me when. ")..question
    end
    AskChoiceWithAnswerSteps(83,0,question,{{Answer='Yes',Step=1},{Answer='No',Step=2}})
end
handlers[84]=function()
    if value(1)~=1 or value(16)~=0 then return end
    set(16,1);evt.SetMapVar('block_pending_16',1);hide(7,false)
    evt.SpawnWorldEffect('hesper:fx/d13_dust',5728,2528,600,1,0)
    evt.StatusText('The ceiling gives way behind you!')
end
handlers[85]=function()
    if value(1)~=1 or value(17)~=0 then return end
    set(17,1);evt.SetMapVar('block_pending_17',1);hide(8,false)
    evt.SpawnWorldEffect('hesper:fx/d13_dust',4700,6192,1100,1,0)
    evt.StatusText('Ahead, the gallery caves in. Round by the loop, to your right! '..
        (torn() and 'Pilot: Right! Round the gantry!' or 'Aster: Right, round the fallen gantry!'))
end
RegisterEvent(3,'Deepwell timer',handlers[3])
RegisterEvent(4,'Deepwell vent',handlers[4])
RegisterEvent(83,'Begin the overload',handlers[83])

HesperPickups.setup{
    treasure=6, -- H3: explicit loot level, as in the pickup test room.
    canisters={701,702,703,704,705,706,707,708,709,710},
    satchels={751,752,753,754,755,756,757,758,759,760,761,762},
}
