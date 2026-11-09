-- Authored node state; build_d06.py supplies only indices and external arrivals.
local handlers = {}
local BOSS = select(1, BOSS_INDEX, nil)
local CROWN_DOOR = select(1, CROWN_DOOR_BINDING, nil)
local CROWN_HATCH = select(1, CROWN_HATCH_BINDING, nil)
local ARC_LIGHTS = {ARC_LIGHT_BINDINGS, }
local COUPLINGS = {COUPLING_BINDINGS, }
local VENTS = {VENT_BINDINGS, }
local FIXTURE_COG = select(1, FIXTURE_BINDING, nil)
local function value(n, limit)
    for i=limit or 3,1,-1 do if IsAtLeast(MapVar(n),i) then return i end end
    return 0
end
local function dead() return IsAtLeast(MapVar(7),1) or IsQBitSet(QBit(100010)) end
local function blown() return value(1)==2 or value(2)==2 or value(3)==2 end
local function allOff() return value(1)>0 and value(2)>0 and value(3)>0 end
local function sound(name,x,y,z) evt.PlaySoundName(name,x,y,z) end
local function panels()
    for k=0,7 do
        local down = IsAtLeast(MapVar(6),1) or k%2==value(13)
        evt.SetDoorState(8+k,down and DoorAction.Open or DoorAction.Close)
    end
end
local function arcs()
    for k=0,2 do
        local live=not dead() and (value(8,4)-k)%5<2
        evt.SetTexture(71+k,live and 'hnstrip' or 'hnfloor')
        evt.SetLight(ARC_LIGHTS[k+1],live and 1 or 0)
    end
end
local function vents()
    for k=0,3 do evt.SetLight(5+k,not dead() and math.floor(value(10,7)/2)==k and 1 or 0) end
end
local function restore()
    local cold=dead()
    evt.SetLight(1,cold and 0 or 1); evt.SetLight(3,cold and 0 or 1); evt.SetLight(2,cold and 1 or 0)
    evt.SetSprite(FIXTURE_COG+1,1,cold and 'hes_lattice_coil_off' or 'hes_lattice_coil')
    evt.SetSprite(FIXTURE_COG+2,1,cold and 'hes_tunnel_lamp' or 'hes_tunnel_lamp_off')
    evt.SetTexture(90,cold and 'hncapacx' or 'hncapac')
    for k=1,3 do
        local state=value(k)
        evt.SetTexture(84+k,state==2 and 'hncouplx' or state==1 and 'hncouplo' or 'hncoupl')
        evt.SetTexture(79+k,state>0 and 'hntermx' or 'hnterm')
    end
    local silenced=IsAtLeast(MapVar(4),1)
    evt.SetSprite(70,1,silenced and 'hes_alarm_pylon_off' or 'hes_alarm_pylon')
    evt.SetTexture(70,silenced and 'hkpylonx' or 'hkpylon')
    if cold then
        evt.SetDoorState(6,DoorAction.Open)
        if not blown() then evt.SetDoorState(5,DoorAction.Open) end
    end
    -- The vault mover has its own cog, so a fused door stays visibly scorched on reload.
    if blown() then evt.SetTexture(55,'hncapacx') end
    if IsAtLeast(MapVar(15),1) then evt.SetDoorState(2,DoorAction.Open) end
    evt.SetMonGroupBit(5,MonsterBits.Invisible,not IsAtLeast(MapVar(5),1))
    evt.SetMonGroupBit(6,MonsterBits.Invisible,not IsAtLeast(MapVar(9),31))
    arcs(); vents(); panels()
end
local function heartCheck()
    if dead() or not allOff() or not IsAtLeast(MapVar(6),1) then return end
    SetValue(MapVar(7),1); SetQBit(QBit(100010)); ClearQBit(QBit(100210))
    evt.ForPlayer(Players.All); AddValue(Experience,40000)
    restore()
    sound('shield_break_noble',4800,7616,-512)
    evt.StatusText('The heart gutters and goes dark. Through the walls the whole grid lurches, and the Hum drops a note.')
end
local function alarm()
    if IsAtLeast(MapVar(5),1) then return end
    SetValue(MapVar(5),1); SetValue(MapVar(9),1)
    evt.SetMonGroupBit(5,MonsterBits.Invisible,false)
    sound('turret_windup',3330,1500,0)
    evt.StatusText('A shriek from the pylon: the alarm is up!')
end
handlers[1]=function()
    if IsQBitSet(QBit(100010)) then SetValue(MapVar(7),1); SetValue(MapVar(6),1) end
    restore()
    if not IsAtLeast(MapVar(6),1) then evt.SetActorBehavior(BOSS,'hesper/coil_keeper') end
    if not IsAtLeast(MapVar(14),1) then
        SetValue(MapVar(14),1); handlers[2]()
    end
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
    if not IsAtLeast(MapVar(6),1) and evt.CheckMonstersKilled(ActorKillCheck.Group,9,0,false) then handlers[151]() end
end
handlers[5]=function()
    if not IsAtLeast(MapVar(4),1) and not dead() and evt.CheckMonstersKilled(ActorKillCheck.Group,1,1,false) then alarm() end
end
handlers[6]=function()
    if dead() then return end
    SetValue(MapVar(10),(value(10,7)+1)%8); vents()
    for k,p in ipairs(VENTS) do
        local phase=(value(10,7)-2*(k-1))%8
        if phase==0 then
            evt.SpawnWorldEffect('hesper:fx/d06_steam',p[1],p[2],-512,1,0)
            sound('crawler_acid_hit',p[1],p[2],-512)
        elseif phase==7 then sound('drone_hover_loop',p[1],p[2],-512) end
    end
end
handlers[7]=function()
    if not IsAtLeast(MapVar(11),1) or IsAtLeast(MapVar(6),1) then return end
    AddValue(MapVar(12),1)
    if value(12)==2 then sound('kr_lance_charge',4800,7616,-512) end
    if value(12)>=3 then
        SetValue(MapVar(12),0); SetValue(MapVar(13),1-value(13)); panels()
    end
end
handlers[10]=function()
    evt.SimpleMessage("A ward sigil: the west Lattice; let nothing soft pass the pylon unseen.\n\nAster: A guard post's charge. They expect you to be seen.")
end
handlers[11]=function()
    evt.SimpleMessage("Conduit crossings.\nTranslated by the colony's engineers: Live crossings ahead. They discharge in turn; cross only while the floor strip is dark.")
end
handlers[12]=function()
    evt.SimpleMessage("Grid node.\nTranslated by the colony's engineers: Grid node west. Three feeds. Never open a feed under load.\n\nA claiming sigil: the Crown's.")
end
handlers[13]=function()
    evt.SimpleMessage("Coolant loop.\nTranslated by the colony's engineers: The purge runs round the loop, vent one to vent four, a breath at each. Follow the purge; never lead it.")
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
    evt.MoveToMap(table.unpack(destination))
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
        if value(k+1)==2 then evt.StatusText('COUPLING '..({'ONE','TWO','THREE'})[k+1]..': NO SIGNAL.'); return end
        if value(k+1)==1 then evt.StatusText('COUPLING '..({'ONE','TWO','THREE'})[k+1]..': CLOSED.'); return end
        if not master() then evt.StatusText("The terminal's lattice locks are beyond you."); return end
        SetValue(MapVar(k+1),1); evt.SetTexture(80+k,'hntermx'); evt.SetTexture(85+k,'hncouplo')
        sound('cell_charger',COUPLINGS[k+1][1],COUPLINGS[k+1][2],-512)
        evt.SimpleMessage('COUPLING '..({'ONE','TWO','THREE'})[k+1]..": FEED CLOSED.\nThe terminal's locks give. Across the core a coupling's light dies.")
        heartCheck()
    end
    handlers[85+k]=function()
        if value(k+1)>0 then
            evt.StatusText(value(k+1)==2 and 'A scorched hole where the coupling was.' or 'The coupling is closed. Its collar is dark.'); return
        end
        if not HasItem(11304) then evt.StatusText('A Breach Charge would sever it; or its terminal could shut it.'); return end
        RemoveItem(11304); SetValue(MapVar(k+1),2); evt.SetTexture(85+k,'hncouplx')
        local p=COUPLINGS[k+1]
        evt.SpawnWorldEffect('openyamm:fx/ember_impact',p[1],p[2],-300,1,0)
        sound('emp_grenade',p[1],p[2],-512); alarm(); evt.SetTexture(55,'hncapacx')
        evt.StatusText('The charge tears the coupling out of its collar. Somewhere a pylon shrieks.')
        heartCheck()
    end
end
handlers[90]=function()
    heartCheck()
    evt.StatusText(dead() and 'The heart is cold and dark.' or allOff() and 'The heart gutters, unfed. Its keeper still stands.'
        or value(1)+value(2)+value(3)==0 and 'The Lattice heart burns violet-white, fed by all three couplings.'
        or 'The heart flickers. Some of its couplings are cut.')
end
for k=0,3 do handlers[100+k]=function()
    if not dead() and math.floor(value(10,7)/2)==k then
        evt.DamagePlayer(Players.All,const.Damage.Fire,55); evt.StatusText('Scalding vapor!')
    end
end end
handlers[151]=function()
    if IsAtLeast(MapVar(6),1) then return end
    SetValue(MapVar(6),1); SetValue(MapVar(11),0); panels()
    evt.SummonItem(11422,4800,7100,-512,0,1,false)
    evt.SummonItem(11332,4800,7100,-512,0,1,false)
    -- shortcut: SummonItem cannot set a gold payload; credit the exact reward until that data API exists.
    evt.ForPlayer(Players.Current); AddValue(Gold,30000)
    heartCheck()
end
handlers[152]=function() if not IsAtLeast(MapVar(6),1) then SetValue(MapVar(11),1) end end
SetMapMetadata({onLoad={},onLeave={},timers={}})
for id=3,7 do RegisterMapTimerEvent(id,30,handlers[id],'Node clock '..id) end

-- Shared stat containers and supply satchels; placements are in pickups.json.
-- H3 is level 6; GetCurrentMapName returns the display name, not the shared lookup's filename.
HesperPickups.setup({
    treasure = 6,
    canisters = {},
    vats = {},
    satchels = {750, 751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761, 762, 763, 764, 765, 766, 767, 768, 769},
    bundles = {}
})
