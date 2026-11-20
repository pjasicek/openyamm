-- Dragon Stadium, MM9 rework (level_generation/projects/mm9r_dragonstadium/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}}})

local function sound(name) evt.PlaySoundName(name, 0, 0, 0) end
local PILLARS = {{id = 1, at = {492, -1434, 82}}, {id = 2, at = {573, -1434, 737}}, {id = 3, at = {532, -1393, 1393}}, {id = 4, at = {532, -1434, 1802}}, {id = 5, at = {492, -1475, 2130}}, {id = 6, at = {451, -1270, 2458}}, {id = 7, at = {860, -1065, 2867}}, {id = 8, at = {164, 3400, 82}}, {id = 9, at = {205, 3441, 737}}, {id = 10, at = {123, 3400, 1393}}, {id = 11, at = {41, 3441, 1802}}, {id = 12, at = {41, 3359, 2130}}, {id = 13, at = {82, 3441, 2458}}, {id = 14, at = {901, 2662, 2867}}, {id = 15, at = {4956, 1106, 82}}, {id = 16, at = {4874, 1106, 737}}, {id = 17, at = {4956, 1188, 1393}}, {id = 18, at = {5038, 1270, 1802}}, {id = 20, at = {4997, 1188, 2130}}, {id = 19, at = {5038, 1024, 2458}}, {id = 21, at = {3932, 1147, 2867}}}   -- p1 level 1..7, p2 level 1..7, p3 level 1..7
local MARKERS = {{3141, -1669, 3259}, {3456, -1155, 3272}}
local DRAGON = 0
local TRIGGER_BOX = {{1055, -4813, -125}, {2591, -4557, 366}}   -- DragonTrigger
local function inBox(b, x, y, z) return x + 37 >= b[1][1] and x - 37 <= b[2][1] and y + 37 >= b[1][2] and y - 37 <= b[2][2] and z + 170 >= b[1][3] and z <= b[2][3] end
local function give(raw, source)
    local item = MM9.ItemIds[raw]
    if item ~= nil and evt.GivePartyMemberItem(math.max(0, evt.GetCurrentPlayerIndex()), item) then return true end
    return MM9.giveItem(raw, source)
end

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest0
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest1

-- The ruined pillars (DestructableBrush 'pN level K', HitPoints 200, Stone, level 7 TriggerDestroyOnly; each
-- level's DeathTriggerTarget 'destroy's the level above): scene destructibles. Weapons (and the dragon's fire
-- in MM9) break a level; a click deals it a killing blow. Its destroyed event marks it, puffs smoke and
-- destroys the level above, so a broken level brings down everything over it (faces hidden, walk-through).
local function pillarBroken(pillar, level)     -- pillar 0..2, level 1..7
    set("Pillar" .. pillar .. "_" .. level, 1)
    local at = PILLARS[pillar * 7 + level].at
    evt.SpawnWorldEffect("mm9:smoke", at[1], at[2], at[3], 3)
    if level < 7 then evt.DestroyDestructible(PILLARS[pillar * 7 + level + 1].id) end
end
handlers[70] = function() evt.DamageDestructible(PILLARS[1].id, 1000000) end   -- p1 level 1: a click
handlers[130] = function() pillarBroken(0, 1) end   -- p1 level 1 destroyed
handlers[71] = function() evt.DamageDestructible(PILLARS[2].id, 1000000) end   -- p1 level 2: a click
handlers[131] = function() pillarBroken(0, 2) end   -- p1 level 2 destroyed
handlers[72] = function() evt.DamageDestructible(PILLARS[3].id, 1000000) end   -- p1 level 3: a click
handlers[132] = function() pillarBroken(0, 3) end   -- p1 level 3 destroyed
handlers[73] = function() evt.DamageDestructible(PILLARS[4].id, 1000000) end   -- p1 level 4: a click
handlers[133] = function() pillarBroken(0, 4) end   -- p1 level 4 destroyed
handlers[74] = function() evt.DamageDestructible(PILLARS[5].id, 1000000) end   -- p1 level 5: a click
handlers[134] = function() pillarBroken(0, 5) end   -- p1 level 5 destroyed
handlers[75] = function() evt.DamageDestructible(PILLARS[6].id, 1000000) end   -- p1 level 6: a click
handlers[135] = function() pillarBroken(0, 6) end   -- p1 level 6 destroyed
handlers[76] = function() evt.DamageDestructible(PILLARS[7].id, 1000000) end   -- p1 level 7: a click
handlers[136] = function() pillarBroken(0, 7) end   -- p1 level 7 destroyed
handlers[77] = function() evt.DamageDestructible(PILLARS[8].id, 1000000) end   -- p2 level 1: a click
handlers[137] = function() pillarBroken(1, 1) end   -- p2 level 1 destroyed
handlers[78] = function() evt.DamageDestructible(PILLARS[9].id, 1000000) end   -- p2 level 2: a click
handlers[138] = function() pillarBroken(1, 2) end   -- p2 level 2 destroyed
handlers[79] = function() evt.DamageDestructible(PILLARS[10].id, 1000000) end   -- p2 level 3: a click
handlers[139] = function() pillarBroken(1, 3) end   -- p2 level 3 destroyed
handlers[80] = function() evt.DamageDestructible(PILLARS[11].id, 1000000) end   -- p2 level 4: a click
handlers[140] = function() pillarBroken(1, 4) end   -- p2 level 4 destroyed
handlers[81] = function() evt.DamageDestructible(PILLARS[12].id, 1000000) end   -- p2 level 5: a click
handlers[141] = function() pillarBroken(1, 5) end   -- p2 level 5 destroyed
handlers[82] = function() evt.DamageDestructible(PILLARS[13].id, 1000000) end   -- p2 level 6: a click
handlers[142] = function() pillarBroken(1, 6) end   -- p2 level 6 destroyed
handlers[83] = function() evt.DamageDestructible(PILLARS[14].id, 1000000) end   -- p2 level 7: a click
handlers[143] = function() pillarBroken(1, 7) end   -- p2 level 7 destroyed
handlers[84] = function() evt.DamageDestructible(PILLARS[15].id, 1000000) end   -- p3 level 1: a click
handlers[144] = function() pillarBroken(2, 1) end   -- p3 level 1 destroyed
handlers[85] = function() evt.DamageDestructible(PILLARS[16].id, 1000000) end   -- p3 level 2: a click
handlers[145] = function() pillarBroken(2, 2) end   -- p3 level 2 destroyed
handlers[86] = function() evt.DamageDestructible(PILLARS[17].id, 1000000) end   -- p3 level 3: a click
handlers[146] = function() pillarBroken(2, 3) end   -- p3 level 3 destroyed
handlers[87] = function() evt.DamageDestructible(PILLARS[18].id, 1000000) end   -- p3 level 4: a click
handlers[147] = function() pillarBroken(2, 4) end   -- p3 level 4 destroyed
handlers[88] = function() evt.DamageDestructible(PILLARS[19].id, 1000000) end   -- p3 level 5: a click
handlers[148] = function() pillarBroken(2, 5) end   -- p3 level 5 destroyed
handlers[89] = function() evt.DamageDestructible(PILLARS[20].id, 1000000) end   -- p3 level 6: a click
handlers[149] = function() pillarBroken(2, 6) end   -- p3 level 6 destroyed
handlers[90] = function() evt.DamageDestructible(PILLARS[21].id, 1000000) end   -- p3 level 7: a click
handlers[150] = function() pillarBroken(2, 7) end   -- p3 level 7 destroyed

-- The Dragon King (Dragon.scr, ScriptParams 1 = bFlyInOnTrigger): hidden and not solid until DragonTrigger
-- sends 'Trigger' (:OnTrigger: visible, solid, Land, Taunt, then he fights). Natively he appears in place and
-- wakes; he stays where MM9 lands him (no ground walk: README, unmatched).
local function dragonUp()
    evt.SetMonGroupBit(1, MonsterBits.Invisible, false)
    evt.WakeActor(DRAGON)
end
handlers[60] = function()       -- DragonTrigger (PlayerTriggerable; :OnTrigger RemoveTrigger)
    if var("DragonAwake") == 1 then return end
    set("DragonAwake", 1)
    set("MutantInterval", 45)
    evt.StartTimer(97, seconds(45))      -- :NormalSetup Wait 22, SPAWN_INTERVAL, SpawnMutants
    dragonUp()
    sound("animsounds/dragonredhop.wav")
end

-- :SpawnMutants: SPAWN_INTERVAL doubles each time (45 s, then 90, 180, ...); a Winged Mutant at each marker
-- (MutantMarker0/1, high over the arena: 'WingedMutant MoveToFloor 0'). It is the dragon's Wait 22, which
-- a dead AI's script still runs (scr_audit README, Implicit engine semantics): the spawns go on after
-- his death.
local function spawnMutants()
    for _, m in ipairs(MARKERS) do
        evt.SummonMonstersById({monster = 9160, x = m[1], y = m[2], z = m[3], radius = 16, group = 2, count = 1})
    end
    set("MutantsSpawned", var("MutantsSpawned") + 2)
end
handlers[96] = function()                  -- four times a second, until the trigger
    evt.StartTimer(96, seconds(0.25))
    if var("DragonAwake") == 1 then return end
    local x, y, z = evt.GetPartyPosition()
    if x ~= nil and inBox(TRIGGER_BOX, x, y, z) then handlers[60]() end
end
handlers[97] = function()                 -- one-shot, armed by the trigger and by itself
    if var("DragonAwake") == 0 then
        evt.StopTimer(97)
        return
    end
    local interval = var("MutantInterval") * 2
    set("MutantInterval", interval)
    evt.StartTimer(97, seconds(interval))
    spawnMutants()
end

-- :OnDeath: killed by the party, the dragon gives key 472 and item 577 (Super Guber Award).
handlers[95] = function(context)
    if context.actorIndex ~= DRAGON or var("DragonDead") == 1 then return end
    set("DragonDead", 1)
    MM9.giveKey(472)
    give(577, "dragonstadium:DragonKing0")
end

handlers[1] = function()      -- map load: the pillars' and the dragon's state
    if var("DragonAwake") == 1 then
        if var("DragonDead") == 0 then dragonUp() end
        evt.StartTimer(97, seconds(var("MutantInterval")))   -- the current wait, from the load
    else
        evt.StopTimer(97)
    end
    evt.StartTimer(96, seconds(0.25))
end

-- MM9's BonePile objects (dungeon/objects.py): a click searches the pile (evt.SearchLootProp: its
-- TreasureLevel loot once, DiseaseChance; the pile stays).
handlers[30045] = function() evt.SearchLootProp("mm9:dragonstadium:object:45") end   -- Prop0
handlers[30046] = function() evt.SearchLootProp("mm9:dragonstadium:object:46") end   -- Prop1
handlers[30047] = function() evt.SearchLootProp("mm9:dragonstadium:object:47") end   -- Prop2


RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(70, "Pillar", handlers[70], "Pillar")
RegisterEvent(130, "Pillar destroyed", handlers[130])
RegisterEvent(71, "Pillar", handlers[71], "Pillar")
RegisterEvent(131, "Pillar destroyed", handlers[131])
RegisterEvent(72, "Pillar", handlers[72], "Pillar")
RegisterEvent(132, "Pillar destroyed", handlers[132])
RegisterEvent(73, "Pillar", handlers[73], "Pillar")
RegisterEvent(133, "Pillar destroyed", handlers[133])
RegisterEvent(74, "Pillar", handlers[74], "Pillar")
RegisterEvent(134, "Pillar destroyed", handlers[134])
RegisterEvent(75, "Pillar", handlers[75], "Pillar")
RegisterEvent(135, "Pillar destroyed", handlers[135])
RegisterEvent(76, "Pillar", handlers[76], "Pillar")
RegisterEvent(136, "Pillar destroyed", handlers[136])
RegisterEvent(77, "Pillar", handlers[77], "Pillar")
RegisterEvent(137, "Pillar destroyed", handlers[137])
RegisterEvent(78, "Pillar", handlers[78], "Pillar")
RegisterEvent(138, "Pillar destroyed", handlers[138])
RegisterEvent(79, "Pillar", handlers[79], "Pillar")
RegisterEvent(139, "Pillar destroyed", handlers[139])
RegisterEvent(80, "Pillar", handlers[80], "Pillar")
RegisterEvent(140, "Pillar destroyed", handlers[140])
RegisterEvent(81, "Pillar", handlers[81], "Pillar")
RegisterEvent(141, "Pillar destroyed", handlers[141])
RegisterEvent(82, "Pillar", handlers[82], "Pillar")
RegisterEvent(142, "Pillar destroyed", handlers[142])
RegisterEvent(83, "Pillar", handlers[83], "Pillar")
RegisterEvent(143, "Pillar destroyed", handlers[143])
RegisterEvent(84, "Pillar", handlers[84], "Pillar")
RegisterEvent(144, "Pillar destroyed", handlers[144])
RegisterEvent(85, "Pillar", handlers[85], "Pillar")
RegisterEvent(145, "Pillar destroyed", handlers[145])
RegisterEvent(86, "Pillar", handlers[86], "Pillar")
RegisterEvent(146, "Pillar destroyed", handlers[146])
RegisterEvent(87, "Pillar", handlers[87], "Pillar")
RegisterEvent(147, "Pillar destroyed", handlers[147])
RegisterEvent(88, "Pillar", handlers[88], "Pillar")
RegisterEvent(148, "Pillar destroyed", handlers[148])
RegisterEvent(89, "Pillar", handlers[89], "Pillar")
RegisterEvent(149, "Pillar destroyed", handlers[149])
RegisterEvent(90, "Pillar", handlers[90], "Pillar")
RegisterEvent(150, "Pillar destroyed", handlers[150])
RegisterEvent(60, "Dragon trigger", handlers[60])
RegisterMapTimerEvent(96, seconds(3), handlers[96], "Dragon trigger poll", "", seconds(3))
RegisterMapTimerEvent(97, seconds(3), handlers[97], "Dragon mutant spawns", "", seconds(3))
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(30045, "Bone Pile", handlers[30045], "Bone Pile")
RegisterEvent(30046, "Bone Pile", handlers[30046], "Bone Pile")
RegisterEvent(30047, "Bone Pile", handlers[30047], "Bone Pile")
RegisterMonsterKilledHook(95, "Monster killed", handlers[95])
