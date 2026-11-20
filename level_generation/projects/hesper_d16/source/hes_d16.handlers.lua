-- Authored D16 state; the build supplies only actor/light indices and destination records.
local handlers = {}
local BOSS = select(1, BOSS_INDEX, nil)
local CROWN_DOOR = select(1, CROWN_DOOR_BINDING, nil)
local CROWN_HATCH = select(1, CROWN_HATCH_BINDING, nil)
local ARC_LIGHTS = {ARC_LIGHT_BINDINGS, }
local COUPLINGS = {COUPLING_BINDINGS, }
local function value(n, limit)
    for i=limit or 3,1,-1 do if IsAtLeast(MapVar(n),i) then return i end end
    return 0
end
local function dead() return IsAtLeast(MapVar(7),1) or IsQBitSet(QBit(100014)) end
local function blown() return value(1)==2 or value(2)==2 or value(3)==2 end
local function liveCount()
    local count=0
    for k=1,3 do if value(k)==0 then count=count+1 end end
    return count
end
local function sound(name,x,y,z) evt.PlaySoundName(name,x,y,z) end
local function bossStage()
    if not IsAtLeast(MapVar(6),1) then evt.SetActorBehavior(BOSS,'hesper/conductor_'..liveCount()) end
end
local function arcs()
    for k=0,2 do
        local live=not dead() and (value(8,4)-k)%5<2
        evt.SetTexture(71+k,live and 'hnstrip' or 'hnfloor')
        evt.SetLight(ARC_LIGHTS[k+1],live and 1 or 0)
    end
end
local function column(k)
    local off=value(k)>0
    evt.SetTexture(84+k,off and 'hncapacx' or 'hncapac')
    evt.SetTexture(79+k,off and 'hntermx' or 'hnterm')
    evt.SetLight(20+k,off and 0 or 1)
    evt.SetMonGroupBit(20+k,MonsterBits.Invisible,off)
end
local function restore()
    local cold=dead()
    evt.SetLight(1,cold and 0 or 1); evt.SetLight(3,cold and 0 or 1); evt.SetLight(2,cold and 1 or 0)
    if cold then
        evt.SetSprite(121,1,'hes_lattice_coil_off'); evt.SetSprite(122,1,'hes_tunnel_lamp')
    else
        evt.SetSprite(121,1,'hes_lattice_coil'); evt.SetSprite(122,1,'hes_tunnel_lamp_off')
    end
    evt.SetTexture(90,cold and 'hncapacx' or 'hncapac')
    for k=1,3 do column(k) end
    if IsAtLeast(MapVar(4),1) then
        evt.SetSprite(70,1,'hes_alarm_pylon_off'); evt.SetTexture(70,'hkpylonx')
    else evt.SetSprite(70,1,'hes_alarm_pylon'); evt.SetTexture(70,'hkpylon') end
    if cold then
        evt.SetDoorState(6,DoorAction.Open)
        if not blown() then evt.SetDoorState(5,DoorAction.Open) end
    end
    if blown() then evt.SetTexture(55,'hncapacx') end
    if IsAtLeast(MapVar(15),1) then evt.SetDoorState(2,DoorAction.Open) end
    evt.SetMonGroupBit(5,MonsterBits.Invisible,not IsAtLeast(MapVar(5),1))
    evt.SetMonGroupBit(6,MonsterBits.Invisible,not IsAtLeast(MapVar(9),31))
    arcs()
end
local function heartCheck()
    if dead() or liveCount()>0 or not IsAtLeast(MapVar(6),1) then return end
    SetValue(MapVar(7),1); SetQBit(QBit(100014)); ClearQBit(QBit(100214))
    evt.ForPlayer(Players.All); AddValue(Experience,40000)
    restore(); sound('shield_break_noble',4800,7616,-512)
    evt.StatusText('The heart gutters and goes dark. Through the walls the whole grid lurches, and the Hum drops a note.')
end
local function alarm()
    if IsAtLeast(MapVar(5),1) then return end
    SetValue(MapVar(5),1); SetValue(MapVar(9),1)
    evt.SetMonGroupBit(5,MonsterBits.Invisible,false)
    sound('turret_windup',3330,1500,0)
    evt.StatusText('A shriek from the pylon: the alarm is up!')
end
local function shortColumn(k,state)
    if value(k)>0 then return end
    SetValue(MapVar(k),state); column(k)
    if state==2 then alarm(); evt.SetTexture(55,'hncapacx') end
    bossStage()
    local p=COUPLINGS[k]
    sound('cell_charger',p[1],p[2],-512)
    evt.StatusText("The column's light gutters out.")
    heartCheck()
end
handlers[1]=function()
    if IsQBitSet(QBit(100014)) then SetValue(MapVar(7),1); SetValue(MapVar(6),1) end
    for _,group in ipairs({1,2,3,5,6,9,10,11,12,21,22,23}) do evt.SetMonGroupBit(group,MonsterBits.Hostile,true) end
    restore(); bossStage()
    if not IsAtLeast(MapVar(14),1) then SetValue(MapVar(14),1); handlers[2]() end
end
handlers[2]=function() evt.StatusText("The Lattice's hum is a pressure behind the eyes here.") end
handlers[3]=function()
    if dead() then return end
    SetValue(MapVar(8),(value(8,4)+1)%5); arcs()
    for k,x in ipairs({3000,5900,7300}) do
        if (value(8,4)-(k-1))%5==4 then sound('kr_lance_charge',x,5472,-420) end
    end
end
handlers[4]=function()
    if IsAtLeast(MapVar(5),1) and not IsAtLeast(MapVar(9),31) then
        AddValue(MapVar(9),1)
        if IsAtLeast(MapVar(9),31) then evt.SetMonGroupBit(6,MonsterBits.Invisible,false) end
    end
    handlers[153]()
    if not IsAtLeast(MapVar(6),1) and evt.CheckMonstersKilled(ActorKillCheck.Group,9,0,false) then handlers[151]() end
end
handlers[5]=function()
    if not IsAtLeast(MapVar(4),1) and not dead() and evt.CheckMonstersKilled(ActorKillCheck.Group,1,1,false) then alarm() end
end
handlers[10]=function()
    evt.SimpleMessage("A ward sigil: the north Lattice; let nothing soft pass the pylon unseen.\n\nAster: A guard post's charge. They expect you to be seen.")
end
handlers[11]=function()
    evt.SimpleMessage("Conduit crossings.\nTranslated by the colony's engineers: Live crossings ahead. They discharge in turn; cross only while the floor strip is dark.")
end
handlers[12]=function()
    evt.SimpleMessage("Grid node.\nTranslated by the colony's engineers: Grid node north. Three feeds. Never open a feed under load.\n\nA claiming sigil: the Crown's.")
end
handlers[15]=function()
    evt.SimpleMessage("A grafter's sigil: here the north is made flesh.\n\nAster: They meant to finish this node before their brood season.")
end
local function master()
    evt.ForPlayer(Players.Current)
    return evt.CheckSkill(const.Skills.Hacking,const.SkillCheck.Master,1)
end
handlers[30]=function()
    if master() then evt.OpenChest(0) else evt.StatusText("The terminal's lattice locks are beyond you.") end
end
handlers[31]=function() evt.OpenChest(1) end
handlers[32]=function() evt.OpenChest(2) end
handlers[33]=function() if dead() and not blown() then evt.OpenChest(3) end end
local function leave(destination)
    if not destination then evt.StatusText('The passage to the Crown is blocked.'); return end
    evt.MoveToMap(destination[1],destination[2],destination[3],destination[4],0,0,0,0,destination[9])
end
handlers[50]=function() leave(CROWN_DOOR) end
handlers[51]=function() evt.SetDoorState(1,DoorAction.Open) end
handlers[52]=function()
    local x,y=evt.GetPartyPosition()
    if x<3200 and not IsAtLeast(MapVar(15),1) then evt.StatusText('Latched from the other side.'); return end
    SetValue(MapVar(15),1); evt.SetDoorState(2,DoorAction.Open)
end
handlers[53]=function() evt.SetDoorState(3,DoorAction.Open) end
handlers[54]=function() evt.SetDoorState(4,DoorAction.Open) end
handlers[55]=function()
    if blown() then evt.StatusText("The vault door is fused shut: the blown coupling's surge welded it.")
    elseif not dead() then evt.StatusText('A vault door, sealed while the heart lives.')
    else evt.SetDoorState(5,DoorAction.Open) end
end
handlers[56]=function()
    if dead() then evt.SetDoorState(6,DoorAction.Open)
    else evt.StatusText('Sealed. It opens when the heart is dead.') end
end
handlers[57]=function() if dead() then leave(CROWN_HATCH) end end
handlers[58]=function() evt.SetDoorState(7,DoorAction.Open) end
handlers[70]=function()
    evt.ForPlayer(Players.Current)
    if not evt.CheckSkill(const.Skills.Hacking,const.SkillCheck.Novice,1) then
        evt.StatusText('It is beyond you: kill the guards before it screams, or not at all.'); return
    end
    SetValue(MapVar(4),1); evt.SetSprite(70,1,'hes_alarm_pylon_off'); evt.SetTexture(70,'hkpylonx')
    evt.StatusText('The pylon falls silent.')
end
for k=0,2 do
    handlers[71+k]=function()
        if not dead() and (value(8,4)-k)%5<2 then
            evt.DamagePlayer(Players.All,const.Damage.Air,60); evt.StatusText('The arc catches you!')
        end
    end
    handlers[80+k]=function()
        local label=({'ONE','TWO','THREE'})[k+1]
        if value(k+1)==2 then evt.StatusText('COUPLING '..label..': NO SIGNAL.'); return end
        if value(k+1)==1 then evt.StatusText('COUPLING '..label..': CLOSED.'); return end
        if not master() then evt.StatusText("The terminal's lattice locks are beyond you."); return end
        shortColumn(k+1,1)
        evt.SimpleMessage('COUPLING '..label..": FEED CLOSED.\nThe terminal's locks give. Across the core a coupling's light dies.")
    end
    handlers[85+k]=function()
        if value(k+1)>0 then
            evt.StatusText(value(k+1)==2 and 'A scorched hole where the coupling was.' or 'The coupling is closed. Its collar is dark.'); return
        end
        if not HasItem(11304) then
            evt.StatusText('A Breach Charge would blow it, or its terminal could shut it; or break the cell.'); return
        end
        RemoveItem(11304); shortColumn(k+1,2)
        local p=COUPLINGS[k+1]
        evt.SpawnWorldEffect('openyamm:fx/ember_impact',p[1],p[2],-300,1,0)
        sound('emp_grenade',p[1],p[2],-512)
        evt.StatusText('The charge tears the coupling out of its collar. Somewhere a pylon shrieks.')
    end
end
handlers[90]=function()
    heartCheck()
    evt.StatusText(dead() and 'The heart is cold and dark.' or liveCount()==0 and 'The heart gutters, unfed. Its keeper still stands.'
        or liveCount()==3 and 'The Lattice heart burns violet-white, fed by all three couplings.'
        or 'The heart flickers. Some of its couplings are cut.')
end
handlers[151]=function()
    if IsAtLeast(MapVar(6),1) then return end
    SetValue(MapVar(6),1)
    evt.SummonItem(11424,4800,7100,-512,0,1,false)
    evt.SummonItem(11332,4800,7100,-512,0,1,false)
    heartCheck()
end
handlers[153]=function()
    for k=1,3 do
        if value(k)==0 and evt.CheckMonstersKilled(ActorKillCheck.Group,20+k,0,false) then shortColumn(k,2) end
    end
end
SetMapMetadata({onLoad={},onLeave={},timers={}})
for id=3,5 do RegisterMapTimerEvent(id,30,handlers[id],'Node clock '..id) end

-- Shared stat containers and supply satchels; placements are in pickups.json.
-- H3 is level 6; GetCurrentMapName returns the display name, not the shared lookup's filename.
HesperPickups.setup({
    treasure = 6,
    canisters = {},
    vats = {},
    satchels = {750, 751, 752, 753, 756, 757, 758, 760, 761, 762, 763, 764, 765},
    bundles = {754, 755, 759, 766, 767, 768, 769}
})
