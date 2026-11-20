-- Bathhouse, MM9 rework (level_generation/projects/mm9r_bathhouse/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {Door0 = 1, Door1 = 2, Door2 = 3, Door3 = 4, Door4 = 5, Door5 = 6, Door6 = 7, Door7 = 8, Door8 = 9, Door9 = 10, FloodWater = 19, FloodWaterStairs = 20, GasRelease0 = 11, PistonDown0 = 12, PistonDown1 = 15, PistonUp0 = 13, PistonUp1 = 14, RotatingDoor0 = 16, Switch0 = 17, WaterProp = 18}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 900}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}, [44] = {3}}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(1, DoorAction.Trigger) end   -- Door0
handlers[102] = function() evt.SetDoorState(2, DoorAction.Trigger) end   -- Door1
handlers[103] = function() evt.SetDoorState(3, DoorAction.Trigger) end   -- Door2
handlers[104] = function() evt.SetDoorState(4, DoorAction.Trigger) end   -- Door3
handlers[105] = function() evt.SetDoorState(5, DoorAction.Trigger) end   -- Door4
handlers[106] = function() evt.SetDoorState(6, DoorAction.Trigger) end   -- Door5
handlers[107] = function() evt.SetDoorState(9, DoorAction.Trigger) evt.SetDoorState(10, DoorAction.Trigger) end   -- Door89

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- BlackBox
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest0
handlers[43] = function() evt.OpenChest(2) end   -- TreasureChest1
handlers[44] = function() evt.OpenChest(3) end   -- TreasureChest2

-- Bits every handler below shares. One-shot timers: the map's timers run from load (RegisterMapTimerEvent
-- repeats), so each is armed by a variable when started and acts only when armed.
local function arm(timer, delay) set("Armed" .. timer, 1); evt.StartTimer(timer, seconds(delay)) end
local function fired(timer)
    evt.StopTimer(timer)
    if var("Armed" .. timer) ~= 1 then return false end
    set("Armed" .. timer, 0)
    return true
end
local function near(p, range)
    local x, y, z = evt.GetPartyPosition()
    return math.abs(x - p[1]) < range and math.abs(y - p[2]) < range and math.abs(z - p[3]) < range
end
local rumble = {left = 0, ticks = 0}   -- EffectsMgr.scr's rumble loops still to play (transient)

-- The furnace (BathFurnace.scr on the gas valve GasRelease0, a RotatingDoor: 180 degrees, sticky). Opening it lights
-- the big fires (Fire1/4, DP2steam.scr), starts the steam over both pools and the pistons (PistonDown/Up 0/1
-- toggle each other while the valve is open), quakes the first time (TriggerEffects -> EffectsMgr.scr) and 2 s
-- later boils Ebora's fat friend in pool A to death (KillFatc -> Fatc.scr `Die`). Closing it puts all out.
handlers[90] = function()   -- GasRelease0
    if var("Furnace") == 0 then
        set("Furnace", 1)
        open("GasRelease0")
        evt.SetSprite(400, true)   -- Fire1
        evt.SetSprite(401, true)   -- Fire4
        if var("Quaked") == 0 then   -- TriggerEffects (once) -> EffectsMgr.scr: the weak long quake
            set("Quaked", 1)
            evt.CameraShake(0.5, 18.0)
            evt.PlaySoundName("sounds/weapons/eqhammerpostimpactloop.wav", 0, 0, 0)
            rumble.left, rumble.ticks = 3, 0
        end
        if var("FatcBoiled") == 0 then arm(301, 2) end
    else
        set("Furnace", 0)
        close("GasRelease0")
        evt.SetSprite(400, false)   -- Fire1
        evt.SetSprite(401, false)   -- Fire4
    end
    evt.PlaySoundName("sounds/door/metaldoorslide01.wav", 0, 0, 0)
end
handlers[301] = function()   -- KillFatc
    if not fired(301) or var("FatcBoiled") == 1 then return end
    -- Fatc.scr's Die: a Fatc the party has killed takes none (its corpse stays; each turnon tries again)
    if not MM9.receives("bathhouse", "BigColWinPool2", "Die", 0) then return end
    set("FatcBoiled", 1)
    MM9.removeActor(0)   -- BigColWinPool2
    evt.PlaySoundName("sounds/ambient/water/liquidboiling.wav", 0, 0, 0)
end
handlers[93] = function() evt.StatusText("Warning: Heat Valve") end   -- FurnaceWarning

-- The drain (Switch0, a Switch authored thrown open: one click throws it). Its targets: the propeller WaterProp
-- spins (9000 degrees at 300/s), BlueWater2 drains (DrainWater.scr: the surface sinks to FloodRoomMarker at
-- 10 LT/s) and Door6/Door7 unlock.
handlers[91] = function()   -- Switch0
    if var("Drained") == 1 then return end
    set("Drained", 1)
    close("Switch0"); open("WaterProp"); set("PropellerTurns", 0)
    open("FloodWater"); open("FloodWaterStairs")   -- the drained room's water
    evt.PlaySoundName("sounds/ambient/fountain_20.wav", 0, 0, 0)   -- DrainWater.scr :DrainWater
    evt.PlaySoundName("sounds/ambient/machinery03.wav", 0, 0, 0)
end
handlers[92] = function()   -- Door6/Door7: Locked until Switch0 unlocks them
    if var("Drained") == 0 then evt.StatusText("The door is locked.") return end
    evt.SetDoorState(DOORS.Door6, DoorAction.Trigger); evt.SetDoorState(DOORS.Door7, DoorAction.Trigger)
end
handlers[99] = function() evt.SetDoorState(DOORS.RotatingDoor0, DoorAction.Trigger) end   -- RotatingDoor0, the flap over SteamVent0 (swings 90 on a push, back after 10 s)


-- The letters (BookLetter.scr DoLetter): MM9's book and scroll texts.
handlers[95] = function() set("ReadProp8", 1); evt.SimpleMessage("Invoice\n\n2000 gallons clean water          1000 Gold\n16 hours cleaning pools            1000 Gold\nVarious Cleaning supplies            50 Gold\nTotal                                       2985 Gold\n\nPayment due upon completion") end   -- Prop8
handlers[96] = function() set("ReadProp7", 1); evt.SimpleMessage("Scrap of Paper\n\n..And then I told that Krohn fellow no!  He told me like he was in charge of the world!  Well I just could not tolerate that kind of behavior.  I probably would have helped him if he had only asked me nicely.  I can assure you though he did not!  Maybe being a few days without a bath will lighten him up.  And then you know what happened..") end   -- Prop7

-- The spores (StepTrigger0-2 -> SpawnLoc0/1 `spawn` twice, SpawnMgr.scr '1 1 JellySpore', then all three
-- triggers and the manager off): the first trigger stepped on shows its location's two hidden Jellyspores.
local SPAWNED = {SpawnLoc0 = {16, 17}, SpawnLoc1 = {18, 19}}
local function spores(loc)
    if var("Spores") == 1 then return end
    set("Spores", 1)
    for _, index in ipairs(SPAWNED[loc]) do
        evt.SetMonsterBit(index, MonsterBits.Invisible, false)
        evt.SetMonsterBit(index, MonsterBits.Hostile, true)
    end
end
handlers[150] = function() spores("SpawnLoc0") end   -- StepTrigger0
handlers[151] = function() spores("SpawnLoc0") end   -- StepTrigger1
handlers[152] = function() spores("SpawnLoc1") end   -- StepTrigger2

-- Ebora (EboraBath.scr): she cannot be hurt (CanDamage FALSE) and stays in her tub; the gossip trigger by
-- Door5 has her taunt the party (OnGossip, up to four lines); each dead concubine (EboraConcubine.scr OnDeath
-- -> DeadConcubine) a taunt; the third sends her off in a column of fire (DitchTheJoint): key 349 and 80 000
-- experience for a party on Gostaf's errand (key 348), else key 350 (NPC339.rude reads both): the cinematic
-- ebora_escape (bathhouse.cinematics.yml; its steps at the end of this file, bath_cinematics.py).
local GOSSIP = {"Ebora: Gosh this bathhouse is soooo lovely... aaahhhh...", "Ebora: Concubine!!  Get my towel!!", "Ebora: What's that?  Did you three concubines hear something?", "Ebora: Thank you my large friend for inviting me to this cozy bathhouse!"}
local TAUNTS = {"Ebora: Do not defy me! My concubines will slay you!", "Ebora: Bah! Luck is with you! But you shall not prevail!"}
local EBORA = 7
local CONCUBINES = {[10] = true, [8] = true, [9] = true}
local GREATER_ON_DEATH = {[15] = true}
handlers[94] = function()   -- EboraGossip
    local n = var("Gossip")
    if var("EboraGone") == 1 or n >= #GOSSIP then return end
    set("Gossip", n + 1)
    evt.StatusText(GOSSIP[n + 1])
end
handlers[97] = function(context)
    if context.actorIndex == EBORA then evt.SetHookDamage(0) end
end
handlers[98] = function(context)
    if GREATER_ON_DEATH[context.actorIndex] then   -- LesserDemon.scr :OnDeathDone (p0 1)
        local x, y, z = evt.GetMapActorPosition(context.actorIndex)
        if x ~= nil then evt.SummonMonstersById({monster = 9242, x = x, y = y, z = z, radius = 32, count = 1, effect = "mm9:GreaterDemon"}) end   -- GreaterDemon.scr :SpawnIn's DoClientFX
        return
    end
    if not CONCUBINES[context.actorIndex] or var("EboraGone") == 1 then return end
    local dead = var("DeadConcubines") + 1
    set("DeadConcubines", dead)
    if dead >= 3 then MM9Cinematic.start("ebora_escape") else evt.StatusText(TAUNTS[dead]) end
end

-- The steam vents (SteamVent.scr: on 3 s, off 3 s; SteamVentDB.scr moves the DamageBrush onto the vent while
-- it blows) and the steam over the hot water: one poll four times a second. A party in a blowing vent's box
-- takes 20 fire damage a second; steam puffs (mm9:smokestack) rise near the party.
local VENTS = {{7721, -4823, -241, 8028, -4741, -61}, {7188, -5499, -241, 7270, -5192, -61}, {6922, -5499, -241, 7004, -5192, -61}, {6595, -5499, -241, 6676, -5192, -61}}
local VENT_POINTS = {{7875, -4782, -64}, {7229, -5468, -169}, {6963, -5468, -169}, {6636, -5468, -169}}
local STEAM = {{6038, -4095, -119}, {6202, -4750, -119}, {7455, -532, -205}, {7496, 573, -205}, {8069, -246, -205}, {8069, -819, -205}, {8110, 860, -205}, {8110, 287, -205}}
local STEAM_FURNACE = {{4809, -4357, -133}, {2417, -4014, -133}}
local polls = 0
local DRAIN_TURNS = 24
handlers[300] = function()
    evt.StartTimer(300, seconds(0.25))
    polls = polls + 1
    local cycle = math.floor(polls / 4) % 6
    local blowing = cycle < 3
    local x, y, z = evt.GetPartyPosition()
    for k, b in ipairs(VENTS) do
        if blowing and x > b[1] - 40 and x < b[4] + 40 and y > b[2] - 40 and y < b[5] + 40 and z > b[3] - 200
                and z < b[6] then
            if polls % 4 == 0 then
                evt.DamagePlayer(Players.All, const.Damage.Fire, 20)
                set("VentHits", var("VentHits") + 1); set("VentHit", 1)
            end
        end
        if blowing and polls % 4 == 0 and cycle == 0 and near(VENT_POINTS[k], 2500) then
            local p = VENT_POINTS[k]; evt.SpawnWorldEffect("mm9:smokestack", p[1], p[2], p[3], 0.35)
        end
    end
    if polls % 12 == 0 then
        for _, p in ipairs(STEAM) do
            if near(p, 2500) then evt.SpawnWorldEffect("mm9:smokestack", p[1], p[2], p[3], 0.35) end
        end
        if var("Furnace") == 1 then
            for _, p in ipairs(STEAM_FURNACE) do
                if near(p, 2500) then evt.SpawnWorldEffect("mm9:smokestack", p[1], p[2], p[3], 0.35) end
            end
        end
    end
    -- the propeller turns while the room drains (a turn each 1.25 s at MM9's 300 degrees a second)
    if var("Drained") == 1 and var("PropellerTurns") < DRAIN_TURNS and polls % 5 == 0 then
        local turns = var("PropellerTurns") + 1
        set("PropellerTurns", turns)
        if turns % 2 == 1 then close("WaterProp") else open("WaterProp") end
    end
    -- the quake's rumble loops (EffectsMgr.scr PlaySoundLoop: the next when one ends)
    if rumble.left > 0 then
        rumble.ticks = rumble.ticks + 1
        if rumble.ticks >= 14 then
            rumble.left, rumble.ticks = rumble.left - 1, 0
            evt.PlaySoundName("sounds/weapons/eqhammerpostimpactloop.wav", 0, 0, 0)
        end
    end
    -- the pistons pump while the valve is open (PistonUp0's close trigger `repeat0` toggles it again)
    if var("Furnace") == 1 and polls % 4 == 0 then
        local p = (polls / 4) % 2 == 0
        evt.SetDoorState(DOORS.PistonDown0, p and DoorAction.Open or DoorAction.Close)
        evt.SetDoorState(DOORS.PistonUp0, p and DoorAction.Open or DoorAction.Close)
        evt.SetDoorState(DOORS.PistonDown1, p and DoorAction.Close or DoorAction.Open)
        evt.SetDoorState(DOORS.PistonUp1, p and DoorAction.Close or DoorAction.Open)
    end
end

handlers[1] = function()   -- map load: the saved states, the poll
    local furnace = var("Furnace") == 1
    evt.SetSprite(400, furnace)   -- Fire1
    evt.SetSprite(401, furnace)   -- Fire4
    if var("FatcBoiled") == 1 then MM9.removeActor(0) end
    if var("EboraGone") == 1 then MM9.removeActor(EBORA) end
    if var("Drained") == 1 then open("FloodWater"); open("FloodWaterStairs") end
    evt.StartTimer(300, seconds(0.25))
end

-- MM9's TouchToOpen doors: walking into one opens it (a 4 Hz poll of the party's position).
local TOUCH_DOORS = {
    {door = 4, box = {{4087, 1458, -319}, {4202, 1911, 356}}},   -- Door3
    {door = 5, box = {{2090, 1458, -319}, {2205, 1911, 356}}},   -- Door4
}
handlers[900] = function()
    local x, y, z = evt.GetPartyPosition()
    for _, t in ipairs(TOUCH_DOORS) do
        local b = t.box
        if x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2]
                and z >= b[1][3] and z <= b[2][3] then
            evt.SetDoorState(t.door, DoorAction.Open)   -- an open door ignores it; a closing one reopens
        end
    end
    evt.StartTimer(900, seconds(0.25))
end

-- MM9's breaking destructibles: an urn's SpawnObject TreasureBag drops (evt.SpawnLootContainer).
handlers[30224] = function() evt.SpawnLootContainer("mm9:bathhouse:object:224") end   -- Urn0
handlers[30225] = function() evt.SpawnLootContainer("mm9:bathhouse:object:225") end   -- Urn1
handlers[30226] = function() evt.SpawnLootContainer("mm9:bathhouse:object:226") end   -- Urn2
handlers[30227] = function() evt.SpawnLootContainer("mm9:bathhouse:object:227") end   -- Urn3
handlers[30228] = function() evt.SpawnLootContainer("mm9:bathhouse:object:228") end   -- Urn4
handlers[30229] = function() evt.SpawnLootContainer("mm9:bathhouse:object:229") end   -- Urn5
handlers[30230] = function() evt.SpawnLootContainer("mm9:bathhouse:object:230") end   -- Urn6
handlers[30231] = function() evt.SpawnLootContainer("mm9:bathhouse:object:231") end   -- Urn7
handlers[30232] = function() evt.SpawnLootContainer("mm9:bathhouse:object:232") end   -- Urn8
handlers[30233] = function() evt.SpawnLootContainer("mm9:bathhouse:object:233") end   -- Urn9
handlers[30234] = function() evt.SpawnLootContainer("mm9:bathhouse:object:234") end   -- Urn10
handlers[30235] = function() evt.SpawnLootContainer("mm9:bathhouse:object:235") end   -- Urn11
handlers[30236] = function() evt.SpawnLootContainer("mm9:bathhouse:object:236") end   -- Urn12
handlers[30237] = function() evt.SpawnLootContainer("mm9:bathhouse:object:237") end   -- Urn13
handlers[30238] = function() evt.SpawnLootContainer("mm9:bathhouse:object:238") end   -- Urn14
handlers[30239] = function() evt.SpawnLootContainer("mm9:bathhouse:object:239") end   -- Urn15
handlers[30240] = function() evt.SpawnLootContainer("mm9:bathhouse:object:240") end   -- Urn16
handlers[30241] = function() evt.SpawnLootContainer("mm9:bathhouse:object:241") end   -- Urn17
handlers[30242] = function() evt.SpawnLootContainer("mm9:bathhouse:object:242") end   -- Urn18
handlers[30243] = function() evt.SpawnLootContainer("mm9:bathhouse:object:243") end   -- Urn19
handlers[30244] = function() evt.SpawnLootContainer("mm9:bathhouse:object:244") end   -- Urn20


RegisterEvent(101, "Door", handlers[101], "Door")
RegisterEvent(102, "Door", handlers[102], "Door")
RegisterEvent(103, "Door", handlers[103], "Door")
RegisterEvent(104, "Door", handlers[104], "Door")
RegisterEvent(105, "Door", handlers[105], "Door")
RegisterEvent(106, "Door", handlers[106], "Door")
RegisterEvent(107, "Door", handlers[107], "Door")
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(43, "Chest", handlers[43], "Chest")
RegisterEvent(44, "Chest", handlers[44], "Chest")
RegisterEvent(90, "Gas valve", handlers[90], "Valve")
RegisterMapTimerEvent(301, seconds(3), handlers[301], "KillFatc", "", seconds(3))
RegisterEvent(93, "Warning", handlers[93], "Warning")
RegisterEvent(91, "Switch", handlers[91], "Switch")
RegisterEvent(92, "Door", handlers[92], "Door")
RegisterEvent(99, "Flap", handlers[99], "Flap")
RegisterEvent(95, "Scroll", handlers[95], "Scroll")
RegisterEvent(96, "Scroll", handlers[96], "Scroll")
RegisterEvent(150, "StepTrigger0", handlers[150])
RegisterEvent(151, "StepTrigger1", handlers[151])
RegisterEvent(152, "StepTrigger2", handlers[152])
RegisterEvent(94, "EboraGossip", handlers[94])
RegisterMapTimerEvent(300, seconds(3), handlers[300], "Steam and vents", "", seconds(3))
RegisterEvent(1, "Map load", handlers[1])
RegisterMapTimerEvent(900, seconds(3), handlers[900], "Touch doors", "", seconds(3))
RegisterEvent(30224, "Urn0", handlers[30224])
RegisterEvent(30225, "Urn1", handlers[30225])
RegisterEvent(30226, "Urn2", handlers[30226])
RegisterEvent(30227, "Urn3", handlers[30227])
RegisterEvent(30228, "Urn4", handlers[30228])
RegisterEvent(30229, "Urn5", handlers[30229])
RegisterEvent(30230, "Urn6", handlers[30230])
RegisterEvent(30231, "Urn7", handlers[30231])
RegisterEvent(30232, "Urn8", handlers[30232])
RegisterEvent(30233, "Urn9", handlers[30233])
RegisterEvent(30234, "Urn10", handlers[30234])
RegisterEvent(30235, "Urn11", handlers[30235])
RegisterEvent(30236, "Urn12", handlers[30236])
RegisterEvent(30237, "Urn13", handlers[30237])
RegisterEvent(30238, "Urn14", handlers[30238])
RegisterEvent(30239, "Urn15", handlers[30239])
RegisterEvent(30240, "Urn16", handlers[30240])
RegisterEvent(30241, "Urn17", handlers[30241])
RegisterEvent(30242, "Urn18", handlers[30242])
RegisterEvent(30243, "Urn19", handlers[30243])
RegisterEvent(30244, "Urn20", handlers[30244])
RegisterMonsterDamageHook(97, "Ebora cannot be hurt", handlers[97])
RegisterMonsterKilledHook(98, "Ebora concubines", handlers[98])


-- MM9 cutscenes as in-engine cinematics (devdocs/mm9_rework/MM9_CUTSCENES.md; mm9r_common/cutscenes.py).
MM9Cinematic = MM9Cinematic or { steps = {}, play = {} }

function MM9Cinematic.runStep(id, index)
    local step = MM9Cinematic.steps[id][index]
    local name = "Cinema." .. id .. ".step." .. step[1]
    if evt.GetMapVar(name, 0) == 0 then
        evt.SetMapVar(name, 1)
        step[2]()
    end
end

function MM9Cinematic.finish(id)
    for index = 1, #MM9Cinematic.steps[id] do
        MM9Cinematic.runStep(id, index)
    end
end

-- Starts a cinematic once per map state (its started map var); a second start while or after it played does nothing.
function MM9Cinematic.start(id)
    local play = MM9Cinematic.play[id]
    if play ~= nil then
        play()
    end
end

-- Cinematic ebora_escape (EboraBath.scr :EscapeTheTub..:TurnCameraOff, EboraCam1.scr): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["ebora_escape"] = {
    { "column", function()
        local x, y, z = evt.GetMapActorPosition(EBORA)
        if x ~= nil then evt.SpawnWorldEffect("mm9:column_of_fire", x, y, z, 1) end
        set("EboraGone", 1)
        if MM9.hasKey(348) == 1 then
            if MM9.hasKey(349) == 0 then
                MM9.giveKey(349)
                MM9.giveExperience(18500) -- MM9 GiveExp 80000, mm9_quest_xp_profile.yml
                MM9.playSound("sounds/events/quest.wav")
            end
        else
            MM9.giveKey(350)
        end
    end },
    { "clear", function()
        MM9.removeActor(EBORA)
    end },
}
RegisterEvent(36001, "Cinema ebora_escape: column", function() MM9Cinematic.runStep("ebora_escape", 1) end)
RegisterEvent(36002, "Cinema ebora_escape: clear", function() MM9Cinematic.runStep("ebora_escape", 2) end)
RegisterEvent(36000, "Cinema ebora_escape: done", function() MM9Cinematic.finish("ebora_escape") end)
MM9Cinematic.play["ebora_escape"] = function()
    if evt.GetMapVar("Cinema.ebora_escape.started", 0) == 0 then
        evt.SetMapVar("Cinema.ebora_escape.started", 1)
        evt.PlayCinematic("ebora_escape", 36000)
    end
end
