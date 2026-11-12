-- Bootcamp, MM9 rework (level_generation/projects/mm9r_bootcamp/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {Door0 = 1, Door1 = 2, Door2 = 3, Door3 = 4, MonsterDoor1 = 5, MonsterDoor2 = 6, MuseumDoor0 = 7, MuseumDoor1 = 8, MuseumDoor2 = 9, MuseumDoor3 = 10, NewHouseDoor0 = 12, NewHouseDoor1 = 11, RotatingDoor0 = 13, RotatingDoor1 = 14, RotatingDoor2 = 15, StoreDoorLeft = 16, StoreDoorRight = 17, Switch0 = 18, Switch1 = 19, TrainingDoor0 = 21, TrainingDoor1 = 20, barflap1 = 22, barflap2 = 23}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 902}, onLeave = {}, timers = {}, openedChestIds = {}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(1, DoorAction.Trigger) evt.SetDoorState(2, DoorAction.Trigger) end   -- Door0
handlers[102] = function() evt.SetDoorState(3, DoorAction.Trigger) evt.SetDoorState(4, DoorAction.Trigger) end   -- Door2
handlers[103] = function() evt.SetDoorState(5, DoorAction.Trigger) evt.SetDoorState(6, DoorAction.Trigger) end   -- MonsterDoor1
handlers[104] = function() evt.SetDoorState(7, DoorAction.Trigger) evt.SetDoorState(8, DoorAction.Trigger) end   -- MuseumDoor0
handlers[105] = function() evt.SetDoorState(9, DoorAction.Trigger) evt.SetDoorState(10, DoorAction.Trigger) end   -- MuseumDoor2
handlers[106] = function() evt.SetDoorState(11, DoorAction.Trigger) evt.SetDoorState(12, DoorAction.Trigger) end   -- NewHouseDoor1
handlers[107] = function() evt.SetDoorState(13, DoorAction.Trigger) evt.SetDoorState(14, DoorAction.Trigger) end   -- RotatingDoor0
handlers[108] = function() evt.SetDoorState(15, DoorAction.Trigger) end   -- RotatingDoor2
handlers[109] = function() evt.SetDoorState(16, DoorAction.Trigger) evt.SetDoorState(17, DoorAction.Trigger) end   -- StoreDoorLeft
handlers[110] = function() evt.SetDoorState(18, DoorAction.Trigger) end   -- Switch0
handlers[111] = function() evt.SetDoorState(19, DoorAction.Trigger) end   -- Switch1
handlers[112] = function() evt.SetDoorState(20, DoorAction.Trigger) evt.SetDoorState(21, DoorAction.Trigger) end   -- TrainingDoor1
handlers[113] = function() evt.SetDoorState(22, DoorAction.Trigger) evt.SetDoorState(23, DoorAction.Trigger) end   -- barflap1

-- Chests (MM9 TreasureChest objects; loot records in the scene).

local function has(k) return MM9.hasKey(k) == 1 end
local function quest() MM9.playSound("sounds/events/quest.wav") end
local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; if gold > 0 then MM9.giveGold(gold) end; quest() end

handlers.regionLoad = function()
    if handlers.museumLoad then handlers.museumLoad() end
    -- MM9's opening movie (movies\intro.bik, which cshell.dll menus.cpp plays at start-up after the logos):
    -- OpenYAMM plays a world's intro on the party's first arrival at its start map, as for MM6 and MM8.
    if evt.GetGlobalVar("OpenYAMM.WorldIntro.MM9", 0) == 0 then
        evt.SetGlobalVar("OpenYAMM.WorldIntro.MM9", 1)
        evt.ShowMovie("MM9Intro", true)
    end
end


-- NPC436.scr :OnRude (Grandpa, RUDE 436): with the training done (key 475) Strategy Tips, Disarm Trap Skill and
-- Identify Item Skill once (key 496); otherwise Interface I and II while the party has no Interface I.
handlers[50207] = function()   -- CommonerHuman2MaleA0
    if has(475) and not has(496) then
        MM9.giveItem(589, "bootcamp:NPC436"); MM9.giveItem(298, "bootcamp:NPC436"); MM9.giveItem(302, "bootcamp:NPC436")
        MM9.giveKey(496)
        return
    end
    if MM9.hasItem(579, "bootcamp:NPC436") == 1 then return end
    MM9.giveItem(579, "bootcamp:NPC436"); MM9.giveItem(580, "bootcamp:NPC436")
end
-- NPC436.scr :Init -> OnFoundPlayer :DoRude: the first time he sees the party (bSpokeTo) his dialogue and voice.
handlers[56207] = function()   -- CommonerHuman2MaleA0
    if not MM9.foundPlayerEnabled(207) then return end
    MM9.disableFoundPlayer(207)
    MM9.openRude(436)
    MM9.playSound("voices/npc/npc_249.wav")
end
-- NPC436.scr :OnLeave (Trigger0 at the dock sends "Leave" as the party boards): key 473, training completed.
-- A slain Grandpa takes no Leave (MM9.receives, scr_audit README "Implicit engine semantics"): no key.
handlers[600] = function()
    if not MM9.receives("bootcamp", "CommonerHuman2MaleA0", "Leave", 20) then return end
    if not has(473) then MM9.giveKey(473) end
end

-- BC_Manager.scr (ScriptObject BC_Manager, "SpawnLoc0 SpawnLoc1 SpawnLoc2"): the museum's shows. Switch0's
-- OpenTrigger sends it "fight", Switch1's "open" (each switch then springs back: its OpenTrigger1 "close").
local BC = {sorcerer = 9158, oculus = 9230, monk = 9125, spawns = {{1961, -10542, 1388}, {3272, -10542, 1388}, {-1480, -10051, 1388}},
    stops = {{-1472, -10230, 1388}, {-1622, -10499, 1388}, {-1841, -10763, 1388}}, chests = {{-1464, -10409, 1388}, {-1710, -10655, 1388}, {-1956, -10901, 1388}},
    sounds = {"ambient/people/crowdnoise-cheer01.wav", "ambient/people/crowdnoise-cheer02.wav", "ambient/people/crowdnoise-ohhh 02.wav"}, waits = {19, 25, 17}}
local function bcIndex(name) local v = var(name) return v > 0 and v - 1 or nil end
local function bcMist(index)
    local x, y, z = evt.GetMapActorPosition(index)
    if x ~= nil then evt.SpawnWorldEffect("mm9:mist", x, y, z + 64, 1) end
end
local function bcSpawn(monster, at, yaw)
    local _, made = evt.SummonMonstersById({monster = monster, x = at[1], y = at[2], z = at[3], radius = 0, count = 1, hostile = false, loot = false, yawDegrees = yaw})
    local index = made ~= nil and made[1] or nil
    if index ~= nil then bcMist(index) end   -- DoClientFX hSpawn, SPELL_MIST
    return index
end
local function bcRemove(name)
    local index = bcIndex(name)
    if index ~= nil then evt.StopActorMove(index); MM9.removeActor(index) end
    set(name, 0)
end
local function bcClock() evt.StartTimer(610, seconds(0.25)) end
-- The party's friends (AddFriend Player; BC_MonsterOpen.scr: AddFriend AIBase), and the fighters each other's
-- enemies (AddEnemy AIBase): MM9's rows are the party's enemies by the table, so the map sets these.
local function bcRelations()
    evt.SetMonsterRelation(BC.sorcerer, 0, 0); evt.SetMonsterRelation(BC.oculus, 0, 0); evt.SetMonsterRelation(BC.monk, 0, 0)
    evt.SetMonsterRelation(BC.sorcerer, BC.oculus, 4); evt.SetMonsterRelation(BC.oculus, BC.sorcerer, 4)
end
local function bcFight()   -- :StartFight
    if var("BCFight") ~= 0 then return end
    bcRelations()
    -- :SetupFighting: the sorcerer faces +x (FaceDir 1, 0, 0), the Oculus -x: each other
    local a, b = bcSpawn(BC.sorcerer, BC.spawns[1], 0), bcSpawn(BC.oculus, BC.spawns[2], 180)
    set("BCSorcerer", a ~= nil and a + 1 or 0); set("BCOculus", b ~= nil and b + 1 or 0)
    set("BCFight", 1); set("BCFightLeft", 480); set("BCSurvivorLeft", 0)
    bcClock()
end
local function bcFightOver()   -- :ForceEndFight, :RemoveCreature
    bcRemove("BCSorcerer"); bcRemove("BCOculus")
    set("BCFight", 0); set("BCSurvivorLeft", 0)
end
local function bcOpen()   -- :StartOpen; BC_MonsterOpen.scr waits 0.1 s, then 1 s, then walks
    if var("BCMonkStage") ~= 0 then return end
    bcRelations()
    local m = bcSpawn(BC.monk, BC.spawns[3])
    if m == nil then return end
    set("BCMonk", m + 1); set("BCMonkStage", 1); set("BCMonkChest", 0); set("BCMonkLeft", 4)
    bcClock()
end
local function bcMonkWalk()   -- :WalkToFirst, :WalkToSecond, :WalkToThird
    local m, k = bcIndex("BCMonk"), var("BCMonkChest") + 1
    local stop = BC.stops[k]
    set("BCMonkChest", k); set("BCMonkStage", 2)
    if m == nil or not evt.MoveActorTo(m, stop[1], stop[2], stop[3], 611) then set("BCMonkStage", 0) end
end
local function bcMonkGone()   -- the link broken: "open" works again
    bcRemove("BCMonk"); set("BCMonkStage", 0)
end
handlers[611] = function()   -- :OpenFirst, :OpenSecond, :OpenThird
    if var("BCMonkStage") ~= 2 then return end
    local k, c = var("BCMonkChest"), BC.chests[var("BCMonkChest")]
    evt.PlaySoundName(BC.sounds[k], c[1], c[2], c[3])
    if k < #BC.stops then
        set("BCMonkStage", 1); set("BCMonkLeft", BC.waits[k])
    else
        -- BC_TreasureChest.scr "1" :SpringTrap: a column of fire on the opener and the latch; :KillTheGuy 1 s
        -- later, :RemoveTheGuy 2 s after that
        local m = bcIndex("BCMonk")
        local x, y, z = nil, nil, nil
        if m ~= nil then x, y, z = evt.GetMapActorPosition(m) end
        if x ~= nil then evt.SpawnWorldEffect("mm9:column_of_fire", x, y, z, 1) end
        evt.PlaySoundName("door/doorlatch01.wav", c[1], c[2], c[3])
        set("BCMonkStage", 3); set("BCMonkLeft", 4)
    end
    bcClock()
end
handlers[610] = function()
    local running = false
    if var("BCSpring") > 0 then   -- the pushed switches spring back
        running = true
        set("BCSpring", var("BCSpring") - 1)
        if var("BCSpring") == 0 then evt.SetDoorState(18, DoorAction.Close) evt.SetDoorState(19, DoorAction.Close) end
    end
    if var("BCFight") == 1 then
        running = true
        set("BCFightLeft", var("BCFightLeft") - 1)
        local survivor = var("BCSurvivorLeft")
        if survivor > 0 then set("BCSurvivorLeft", survivor - 1) end
        if var("BCFightLeft") <= 0 or survivor == 1 then bcFightOver(); running = false end
    end
    local stage = var("BCMonkStage")
    if stage == 1 or stage == 3 or stage == 4 then
        running = true
        set("BCMonkLeft", var("BCMonkLeft") - 1)
        if var("BCMonkLeft") <= 0 then
            if stage == 1 then bcMonkWalk()
            elseif stage == 3 then   -- :KillTheGuy
                local m = bcIndex("BCMonk")
                if m ~= nil then evt.KillMapActor(m) end
                set("BCMonkStage", 4); set("BCMonkLeft", 8)
            else bcMonkGone() end
        end
    elseif stage == 2 then
        running = true
    end
    if running then bcClock() end
end
-- :OnObjectLinkBroken: one fighter dead, the other vanishes in a mist 2 s later; the monk dead (by the trap or
-- the party), "open" works again once his body is gone.
handlers[612] = function(context)
    local i = context.actorIndex
    if i == nil then return end
    if var("BCFight") == 1 and var("BCSurvivorLeft") == 0 and (i == bcIndex("BCSorcerer") or i == bcIndex("BCOculus")) then
        local other = i == bcIndex("BCSorcerer") and bcIndex("BCOculus") or bcIndex("BCSorcerer")
        if other ~= nil then bcMist(other) end
        set("BCSurvivorLeft", 9)
    elseif i == bcIndex("BCMonk") and var("BCMonkStage") ~= 4 then
        evt.StopActorMove(i)
        set("BCMonkStage", 4); set("BCMonkLeft", 8)
        bcClock()
    end
end
-- Switch0: pushed in, it springs back (OpenTrigger1 "close") and starts its show.
handlers[110] = function()
    evt.SetDoorState(18, DoorAction.Open)
    set("BCSpring", 4); bcClock()
    bcFight()
end
-- Switch1: pushed in, it springs back (OpenTrigger1 "close") and starts its show.
handlers[111] = function()
    evt.SetDoorState(19, DoorAction.Open)
    set("BCSpring", 4); bcClock()
    bcOpen()
end

handlers.museumLoad = function()
    -- BC_Manager.scr: a show under way when the map was left or saved ends; both switches work again
    bcRelations()
    bcFightOver(); bcMonkGone(); set("BCSpring", 0)
    evt.SetDoorState(18, DoorAction.Close)
    evt.SetDoorState(19, DoorAction.Close)
end

handlers[1] = function()
    if handlers.regionLoad then handlers.regionLoad() end
end

-- MM9's greeting voices (dungeon/voices.py): a click on these people plays their GreetingSound or the
-- voice their script's :OnUse plays, then opens their dialogue (or runs the map's own click).
handlers[53207] = function() MM9.playSound("voices/npc/npc_249.wav"); MM9.openRude(436) end   -- CommonerHuman2MaleA0
handlers[53209] = function() MM9.playSound("voices/npc/npc_101.wav"); MM9.openRude(101) end   -- ShopkeeperElfFemaleA2
handlers[53210] = function() MM9.playSound("voices/npc/npc_204.wav"); MM9.openRude(204) end   -- ShopkeeperElfFemaleA0
handlers[53211] = function() MM9.playSound("voices/npc/npc_206.wav"); MM9.openRude(206) end   -- ShopkeeperElfFemaleA1

-- MM9's BonePile objects (dungeon/objects.py): a click searches the pile (evt.SearchLootProp: its
-- TreasureLevel loot once, DiseaseChance; the pile stays).
handlers[30362] = function() evt.SearchLootProp("mm9:bootcamp:object:362") end   -- BonePile0

-- MM9's bonus props (dungeon/objects.py bonus_lines; the use of each class, object.lto): wells, cauldrons,
-- cook pots and clovers.
handlers[30361] = function() MM9.useCauldron(361, 0, 0) end   -- obj_Cauldron1 (Cauldron)
handlers[30373] = function() MM9.useCauldron(373, 0, 0) end   -- obj_Cauldron0 (Cauldron)
handlers[30374] = function() MM9.useCookpot(374, 0, 0, 0, 0) end   -- obj_Cookpot0 (Cookpot)

-- MM9's PerceptionBrushes (dungeon/perception.py): the red glow shows to a party whose Perception reaches the
-- brush's PerceptionValue, checked on load and every 3 s; map Lua turns one off for good with
-- set("HintOff<cog>", 1) (MM9's Off message to the brush).
local HINTS = {[23007] = 1, [23064] = 1, [23065] = 1, [23580] = 1, [23581] = 1, [23586] = 1}
handlers[901] = function()
    for cog, value in pairs(HINTS) do
        local want = (var("HintOff" .. cog) == 0 and evt.CheckSkill(29, 0, value)) and 2 or 1
        if var("Hint" .. cog) ~= want then
            set("Hint" .. cog, want)
            evt.SetFacetBit(cog, FacetBits.Invisible, want == 1)
        end
    end
end
handlers[902] = function()   -- map load: the shared objects
    for cog, _ in pairs(HINTS) do set("Hint" .. cog, 0) end
    handlers[901]()
end

RegisterEvent(101, "Door", handlers[101], "Door")
RegisterEvent(102, "Door", handlers[102], "Door")
RegisterEvent(103, "Door", handlers[103], "Door")
RegisterEvent(104, "Door", handlers[104], "Door")
RegisterEvent(105, "Door", handlers[105], "Door")
RegisterEvent(106, "Door", handlers[106], "Door")
RegisterEvent(107, "Door", handlers[107], "Door")
RegisterEvent(108, "Door", handlers[108], "Door")
RegisterEvent(109, "Door", handlers[109], "Door")
RegisterEvent(110, "Door", handlers[110], "Door")
RegisterEvent(111, "Door", handlers[111], "Door")
RegisterEvent(112, "Door", handlers[112], "Door")
RegisterEvent(113, "Door", handlers[113], "Door")
RegisterEvent(50207, "Grandpa", handlers[50207])
RegisterEvent(56207, "Grandpa", handlers[56207])
RegisterEvent(611, "Museum monk", handlers[611])
RegisterMapTimerEvent(610, seconds(3), handlers[610], "Museum shows", "", seconds(3))
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(53207, "Old Man", handlers[53207])
RegisterEvent(53209, "Thorkatla the Indiscreet", handlers[53209])
RegisterEvent(53210, "Dearbhorgaill A'Washadi", handlers[53210])
RegisterEvent(53211, "Fiachna A'Lanth", handlers[53211])
RegisterEvent(30362, "Bone Pile", handlers[30362], "Bone Pile")
RegisterEvent(30361, "Cauldron", handlers[30361], "Drink")
RegisterEvent(30373, "Cauldron", handlers[30373], "Drink")
RegisterEvent(30374, "Cook pot", handlers[30374], "Eat")
RegisterMapTimerEvent(901, seconds(3), handlers[901], "Perception hints", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
RegisterMapOnLeaveEvent(600, "Leaving Boot Camp", handlers[600])
RegisterMonsterKilledHook(612, "Museum shows", handlers[612])
