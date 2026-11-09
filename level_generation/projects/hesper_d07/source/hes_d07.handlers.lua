-- Authored D7 state; the builder supplies actor/light ids, mine positions and Crown arrivals.
local handlers = {}
local BOSS = select(1, BOSS_INDEX, nil)
local CROWN_DOOR = select(1, CROWN_DOOR_BINDING, nil)
local CROWN_HATCH = select(1, CROWN_HATCH_BINDING, nil)
local ARC_LIGHTS = {ARC_LIGHT_BINDINGS, }
local LINE_LIGHTS = {LINE_LIGHT_BINDINGS, }
local COUPLINGS = {COUPLING_BINDINGS, }
local MINE_POSITIONS = {MINE_POSITION_BINDINGS, }
local function value(n,limit)
    for i=limit or 3,1,-1 do if IsAtLeast(MapVar(n),i) then return i end end
    return 0
end
local function dead() return IsAtLeast(MapVar(7),1) or IsQBitSet(QBit(100009)) end
local function free() return IsAtLeast(MapVar(10),1) or dead() end
local function blown() return value(1)==2 or value(2)==2 or value(3)==2 end
local function allOff() return value(1)>0 and value(2)>0 and value(3)>0 end
local function sound(name,x,y,z) evt.PlaySoundName(name,x,y,z) end
local mineSprites = {MINE_SPRITE_BINDINGS, }
local function arcs()
    for k=0,2 do
        local live=not dead() and (value(8,4)-k)%5<2
        evt.SetTexture(71+k,live and 'hnstrip' or 'hnfloor')
        evt.SetLight(ARC_LIGHTS[k+1],live and 1 or 0)
    end
end
local function lineLights()
    local running=not dead() and value(13)==1
    for _,id in ipairs(LINE_LIGHTS) do evt.SetLight(id,running and 1 or 0) end
end
local function restore()
    local cold=dead()
    evt.SetLight(1,cold and 0 or 1);evt.SetLight(3,cold and 0 or 1);evt.SetLight(2,cold and 1 or 0)
    if cold then
        evt.SetSprite(121,1,'hes_lattice_coil_off');evt.SetSprite(122,1,'hes_tunnel_lamp')
    else
        evt.SetSprite(121,1,'hes_lattice_coil');evt.SetSprite(122,1,'hes_tunnel_lamp_off')
    end
    evt.SetTexture(90,cold and 'hncapacx' or 'hncapac')
    for k=1,3 do
        local state=value(k)
        evt.SetTexture(84+k,state==2 and 'hncouplx' or state==1 and 'hncouplo' or 'hncoupl')
        evt.SetTexture(79+k,state>0 and 'hntermx' or 'hnterm')
    end
    if IsAtLeast(MapVar(4),1) then evt.SetSprite(70,1,'hes_alarm_pylon_off');evt.SetTexture(70,'hkpylonx')
    else evt.SetSprite(70,1,'hes_alarm_pylon');evt.SetTexture(70,'hkpylon') end
    if value(13)==2 then evt.SetSprite(110,1,'hes_line_lever_thrown')
    else evt.SetSprite(110,1,'hes_line_lever') end
    if cold then
        evt.SetDoorState(6,DoorAction.Open)
        if not blown() then evt.SetDoorState(5,DoorAction.Open) end
    end
    if blown() then evt.SetTexture(55,'hncapacx') end
    if IsAtLeast(MapVar(12),1) then evt.SetDoorState(2,DoorAction.Open) end
    evt.SetMonGroupBit(5,MonsterBits.Invisible,not IsAtLeast(MapVar(5),1))
    evt.SetMonGroupBit(6,MonsterBits.Invisible,not IsAtLeast(MapVar(9),31))
    evt.SetMonGroupBit(12,MonsterBits.Invisible,not IsAtLeast(MapVar(14),20))
    evt.SetMonGroupBit(13,MonsterBits.Invisible,not IsAtLeast(MapVar(14),40))
    evt.SetSprite(260,free() and 0 or 1,'d07_bulwark_cable_1')
    evt.SetSprite(261,free() and 0 or 1,'d07_bulwark_cable_2')
    evt.SetSprite(262,free() and 0 or 1,'d07_bulwark_cable_3')
    evt.SetMonGroupBit(9,MonsterBits.Invisible,free())
    evt.SetMonGroupBit(8,MonsterBits.Invisible,not free())
    evt.SetSprite(270,IsAtLeast(MapVar(6),1) and 1 or 0,'hes_bulwark_wreck')
    for k,fn in ipairs(mineSprites) do fn(value(k<=8 and 19+k or 21+k)) end
    lineLights();arcs()
end
local function heartCheck()
    if dead() or not allOff() or not IsAtLeast(MapVar(6),1) then return end
    SetValue(MapVar(7),1);SetValue(MapVar(13),2)
    SetQBit(QBit(100009));ClearQBit(QBit(100209))
    evt.ForPlayer(Players.All);AddValue(Experience,40000)
    restore();sound('shield_break_noble',4800,7616,-512)
    evt.StatusText('The heart gutters and goes dark. Through the walls the whole grid lurches, and the Hum drops a note.')
end
local function alarm()
    if IsAtLeast(MapVar(5),1) then return end
    SetValue(MapVar(5),1);SetValue(MapVar(9),1)
    evt.SetMonGroupBit(5,MonsterBits.Invisible,false)
    sound('turret_windup',3330,1500,0);evt.StatusText('A shriek from the pylon: the alarm is up!')
end
handlers[1]=function()
    if not IsAtLeast(MapVar(11),1) then
        SetValue(MapVar(11),1)
        for k=20,27 do SetValue(MapVar(k),1) end
        handlers[2]()
    end
    if IsQBitSet(QBit(100009)) then SetValue(MapVar(7),1);SetValue(MapVar(6),1);SetValue(MapVar(10),1) end
    handlers[152]();restore()
    if free() and not IsAtLeast(MapVar(6),1) then evt.SetActorBehavior(BOSS,'hesper/bulwark') end
end
handlers[2]=function() evt.StatusText("The Lattice's hum is a pressure behind the eyes here.") end
handlers[3]=function()
    if dead() then return end
    SetValue(MapVar(8),(value(8,4)+1)%5);arcs()
    for k,x in ipairs({3000,5900,7300}) do
        if (value(8,4)-(k-1))%5==4 then sound('kr_lance_charge',x,5472,-420) end
    end
end
handlers[4]=function()
    if IsAtLeast(MapVar(5),1) and not IsAtLeast(MapVar(9),31) then
        AddValue(MapVar(9),1)
        if IsAtLeast(MapVar(9),31) then evt.SetMonGroupBit(6,MonsterBits.Invisible,false) end
    end
    if free() and not IsAtLeast(MapVar(6),1) and evt.CheckMonstersKilled(ActorKillCheck.Group,8,0,false) then handlers[151]() end
end
handlers[5]=function()
    if not IsAtLeast(MapVar(4),1) and not dead() and evt.CheckMonstersKilled(ActorKillCheck.Group,1,1,false) then alarm() end
end
handlers[6]=function()
    if dead() or value(13)~=1 then return end
    AddValue(MapVar(14),1)
    if IsAtLeast(MapVar(14),20) then evt.SetMonGroupBit(12,MonsterBits.Invisible,false) end
    if IsAtLeast(MapVar(14),40) then
        evt.SetMonGroupBit(13,MonsterBits.Invisible,false);SetValue(MapVar(13),2)
        evt.SetSprite(110,1,'hes_line_lever_thrown');lineLights()
    end
end
handlers[7]=function()
    if free() or not IsAtLeast(MapVar(36),1) then return end
    local x,y=evt.GetPartyPosition()
    if x<3200 or x>6400 or y<6016 or y>9216 then return end
    for k=30,35 do
        if value(k)==0 then
            SetValue(MapVar(k),1);mineSprites[k-21](1)
            local p=MINE_POSITIONS[k-21];sound('turret_windup',p[1],p[2],-512);return
        end
    end
end
handlers[10]=function() evt.SimpleMessage("A ward sigil: the east Lattice; let nothing soft pass the pylon unseen.\n\nAster: A guard post's charge. They expect you to be seen.") end
handlers[11]=function() evt.SimpleMessage("Conduit crossings.\nTranslated by the colony's engineers: Live crossings ahead. They discharge in turn; cross only while the floor strip is dark.") end
handlers[12]=function() evt.SimpleMessage("Grid node.\nTranslated by the colony's engineers: Grid node east. Three feeds. Never open a feed under load.\n\nA claiming sigil: the Crown's.") end
handlers[14]=function() evt.SimpleMessage('Drone line.\nTranslated by the colony\'s engineers: Maintenance drone line two. Emergency stop at the far station. Never stand under a cradle in its cycle.') end
local function master()
    evt.ForPlayer(Players.Current);return evt.CheckSkill(const.Skills.Hacking,const.SkillCheck.Master,1)
end
handlers[30]=function() if master() then evt.OpenChest(0) else evt.StatusText("The terminal's lattice locks are beyond you.") end end
handlers[31]=function() evt.OpenChest(1) end
handlers[32]=function() evt.OpenChest(2) end
handlers[33]=function() if dead() and not blown() then evt.OpenChest(3) end end
handlers[50]=function() evt.MoveToMap(table.unpack(CROWN_DOOR)) end
handlers[51]=function() evt.SetDoorState(1,DoorAction.Open) end
handlers[52]=function()
    local x=evt.GetPartyPosition()
    if x<3200 and not IsAtLeast(MapVar(12),1) then evt.StatusText('Latched from the other side.');return end
    SetValue(MapVar(12),1);evt.SetDoorState(2,DoorAction.Open)
end
handlers[53]=function() evt.SetDoorState(3,DoorAction.Open) end
handlers[54]=function() evt.SetDoorState(4,DoorAction.Open) end
handlers[55]=function()
    if blown() then evt.StatusText("The vault door is fused shut: the blown coupling's surge welded it.")
    elseif not dead() then evt.StatusText('A vault door, sealed while the heart lives.')
    else evt.SetDoorState(5,DoorAction.Open) end
end
handlers[56]=function()
    if dead() then evt.SetDoorState(6,DoorAction.Open) else evt.StatusText('Sealed. It opens when the heart is dead.') end
end
handlers[57]=function() if dead() then evt.MoveToMap(table.unpack(CROWN_HATCH)) end end
handlers[58]=function() evt.SetDoorState(7,DoorAction.Open) end
handlers[59]=function() evt.SetDoorState(8,DoorAction.Open) end
handlers[70]=function()
    evt.ForPlayer(Players.Current)
    if not evt.CheckSkill(const.Skills.Hacking,const.SkillCheck.Novice,1) then
        evt.StatusText('It is beyond you: kill the guards before it screams, or not at all.');return
    end
    SetValue(MapVar(4),1);evt.SetSprite(70,1,'hes_alarm_pylon_off');evt.SetTexture(70,'hkpylonx')
    evt.StatusText('The pylon falls silent.')
end
for k=0,2 do
    handlers[71+k]=function()
        if not dead() and (value(8,4)-k)%5<2 then evt.DamagePlayer(Players.All,const.Damage.Air,60);evt.StatusText('The arc catches you!') end
    end
    local function shut()
        SetValue(MapVar(k+1),1);evt.SetTexture(80+k,'hntermx');evt.SetTexture(85+k,'hncouplo')
        sound('cell_charger',COUPLINGS[k+1][1],COUPLINGS[k+1][2],-512)
        evt.SimpleMessage('COUPLING '..({'ONE','TWO','THREE'})[k+1]..": FEED CLOSED.\nThe terminal's locks give. Across the core a coupling's light dies.")
        handlers[152]();heartCheck()
    end
    handlers[80+k]=function()
        if value(k+1)==2 then evt.StatusText('COUPLING '..({'ONE','TWO','THREE'})[k+1]..': NO SIGNAL.');return end
        if value(k+1)==1 then evt.StatusText('COUPLING '..({'ONE','TWO','THREE'})[k+1]..': CLOSED.');return end
        if not master() then evt.StatusText("The terminal's lattice locks are beyond you.");return end
        shut()
    end
    handlers[85+k]=function()
        if value(k+1)>0 then evt.StatusText(value(k+1)==2 and 'A scorched hole where the coupling was.' or 'The coupling is closed. Its collar is dark.');return end
        evt.ForPlayer(Players.Current)
        if evt.CheckSkill(const.Skills.Hacking,const.SkillCheck.Grandmaster,1) then shut();return end
        if not HasItem(11304) then evt.StatusText('A Breach Charge would sever it; or its terminal could shut it.');return end
        RemoveItem(11304);SetValue(MapVar(k+1),2);evt.SetTexture(85+k,'hncouplx')
        local p=COUPLINGS[k+1];evt.SpawnWorldEffect('openyamm:fx/ember_impact',p[1],p[2],-300,1,0)
        sound('emp_grenade',p[1],p[2],-512);alarm();evt.SetTexture(55,'hncapacx')
        evt.StatusText('The charge tears the coupling out of its collar. Somewhere a pylon shrieks.')
        handlers[152]();heartCheck()
    end
end
handlers[90]=function()
    heartCheck();evt.StatusText(dead() and 'The heart is cold and dark.' or allOff() and 'The heart gutters, unfed. Its keeper still stands.'
        or value(1)+value(2)+value(3)==0 and 'The Lattice heart burns violet-white, fed by all three couplings.' or 'The heart flickers. Some of its couplings are cut.')
end
handlers[110]=function()
    if value(13)==2 then evt.StatusText('The line is still.');return end
    SetValue(MapVar(13),2);evt.SetSprite(110,1,'hes_line_lever_thrown');lineLights()
    evt.StatusText('The line grinds to a halt. Half-built drones hang dead in their cradles.')
end
handlers[111]=function()
    if value(13)~=0 or dead() then return end
    SetValue(MapVar(13),1);lineLights();sound('drone_hover_loop',9000,6100,-380)
end
for k=1,14 do
    local variable=k<=8 and 19+k or 21+k
    local event=k<=8 and 119+k or 121+k
    handlers[event]=function()
        if value(variable)~=1 then return end
        SetValue(MapVar(variable),2);mineSprites[k](2)
        evt.DamagePlayer(Players.All,const.Damage.Energy,75)
        local p=MINE_POSITIONS[k];evt.SpawnWorldEffect('openyamm:fx/ember_impact',p[1],p[2],-480,1,0)
        sound('emp_grenade',p[1],p[2],-512);evt.StatusText('A mine! The blast throws you back.')
    end
end
handlers[151]=function()
    if IsAtLeast(MapVar(6),1) then return end
    SetValue(MapVar(6),1);evt.SummonItem(11332,4800,7100,-512,0,1,false)
    -- shortcut: SummonItem cannot encode a gold amount; credit exactly until a payload API exists.
    evt.ForPlayer(Players.Current);AddValue(Gold,30000)
    evt.SetSprite(270,1,'hes_bulwark_wreck');heartCheck()
end
handlers[152]=function()
    if free() or not allOff() then return end
    SetValue(MapVar(10),1)
    evt.SetSprite(260,0,'d07_bulwark_cable_1');evt.SetSprite(261,0,'d07_bulwark_cable_2');evt.SetSprite(262,0,'d07_bulwark_cable_3')
    evt.SpawnWorldEffect('hesper:fx/d07_steam',4800,6716,-300,1,0);sound('crawler_acid_hit',4800,6716,-300)
    evt.SetMonGroupBit(9,MonsterBits.Invisible,true);evt.SetMonGroupBit(8,MonsterBits.Invisible,false)
    for k=30,35 do SetValue(MapVar(k),2);mineSprites[k-21](2) end
    evt.SetActorBehavior(BOSS,'hesper/bulwark')
end
handlers[153]=function()
    if not IsAtLeast(MapVar(36),1) and not free() then
        evt.StatusText('INTRUDERS AT GRID NODE EAST. DEFENCE COUPLED. DEPLOYING.')
    end
    SetValue(MapVar(36),1);handlers[152]()
end
SetMapMetadata({onLoad={},onLeave={},timers={}})
for id=3,6 do RegisterMapTimerEvent(id,30,handlers[id],'Node clock '..id) end
RegisterMapTimerEvent(7,180,handlers[7],'Bulwark mine rack')

-- Shared stat containers and supply satchels; placements are in pickups.json.
-- H3 is level 6; GetCurrentMapName returns the display name, not the shared lookup's filename.
HesperPickups.setup({
    treasure = 6,
    canisters = {},
    vats = {},
    satchels = {750, 751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761, 762, 763, 764, 765, 766, 767, 768, 769},
    bundles = {}
})
