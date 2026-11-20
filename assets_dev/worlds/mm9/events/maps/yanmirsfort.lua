-- Yanmir's Fort, MM9 rework (level_generation/projects/mm9r_yanmirsfort/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {Door1 = 53, Door10 = 50, Door11 = 51, Door12 = 52, Door1a = 3, Door1a0 = 1, Door1a1 = 7, Door1a10 = 5, Door1a2 = 9, Door1a20 = 25, Door1a21 = 27, Door1a22 = 29, Door1a23 = 31, Door1a24 = 33, Door1a27 = 36, Door1a29 = 38, Door1a3 = 11, Door1a30 = 40, Door1a31 = 42, Door1a35 = 44, Door1a36 = 46, Door1a4 = 13, Door1a5 = 15, Door1a6 = 17, Door1a7 = 19, Door1a8 = 21, Door1a9 = 23, Door1b = 4, Door1b0 = 2, Door1b1 = 8, Door1b10 = 6, Door1b2 = 10, Door1b20 = 26, Door1b21 = 28, Door1b22 = 30, Door1b23 = 32, Door1b24 = 34, Door1b27 = 35, Door1b29 = 37, Door1b3 = 12, Door1b30 = 39, Door1b31 = 41, Door1b35 = 43, Door1b36 = 45, Door1b4 = 14, Door1b5 = 16, Door1b6 = 18, Door1b7 = 20, Door1b8 = 22, Door1b9 = 24, Door2 = 54, Door3 = 55, Door4 = 56, Door5 = 57, Door6 = 58, Door7 = 59, Door8 = 60, Door9 = 49, DoorTeleportLeft = 48, DoorTeleportRight = 47, FallingFloor0 = 71, Planks0 = 73, RotatingDoor61 = 61, RotatingDoor62 = 62, RotatingDoor63 = 63, RotatingDoor64 = 64, RotatingDoor65 = 65, RotatingDoor66 = 66, RotatingDoor67 = 67, Secretdoor = 68, Secretdoor_INV = 69, Xbeams0 = 72, YanDstruct0 = 70}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}, [44] = {3}, [45] = {4}, [46] = {5}, [47] = {6}, [48] = {7}, [49] = {8}, [50] = {9}, [51] = {10}}})

local GROUPS = {["DPortal0"] = {1, 2}, ["DPortal1"] = {3, 4}, ["DPortal10"] = {5, 6}, ["DPortal11"] = {7, 8}, ["DPortal12"] = {9, 10}, ["DPortal13"] = {11, 12}, ["DPortal14"] = {13, 14}, ["DPortal15"] = {15, 16}, ["DPortal16"] = {17, 18}, ["DPortal17"] = {19, 20}, ["DPortal18"] = {21, 22}, ["DPortal19"] = {23, 24}, ["DPortal20"] = {25, 26}, ["DPortal21"] = {27, 28}, ["DPortal22"] = {29, 30}, ["DPortal23"] = {31, 32}, ["DPortal24"] = {33, 34}, ["DPortal27"] = {35, 36}, ["DPortal29"] = {37, 38}, ["DPortal30"] = {39, 40}, ["DPortal31"] = {41, 42}, ["DPortal35"] = {43, 44}, ["DPortal36"] = {45, 46}, ["DPortal37"] = {47, 48}, ["Portal10"] = {49, 50}, ["Portal12"] = {51, 52}, ["Portal2"] = {53, 54}, ["Portal4"] = {55, 56}, ["Portal6"] = {57, 58}, ["Portal8"] = {59, 60}, ["RotatingDoor61"] = {61}, ["RotatingDoor62"] = {62}, ["RotatingDoor63"] = {63}, ["RotatingDoor64"] = {64}, ["RotatingDoor65"] = {65}, ["RotatingDoor66"] = {66}, ["RotatingDoor67"] = {67}, ["Secretdoor"] = {68, 69}, ["TrapFloor"] = {70, 71}, ["TrapPlanks"] = {72, 73}}
local function openGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Open) end end
local function closeGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Close) end end
local function toggleGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Trigger) end end
local function inBox(b, x, y, z) return x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] and z + 170 >= b[1][3] and z <= b[2][3] end
local BOX = {EndOfWorld = {{-82, -10854, -9175}, {1065, -6554, -768}}, SquishTrigger0 = {{-4215, -2874, -5}, {-3895, -2042, 251}}, SquishTrigger1 = {{-1635, 3025, 691}, {-1315, 3857, 947}}, Trigger10 = {{-4701, 2917, 655}, {-4474, 3964, 983}}, Trigger6 = {{50, 4264, 655}, {933, 4584, 983}}, Trigger7 = {{-5521, -365, 0}, {-4637, -45, 328}}, Trigger8 = {{787, -19037, 0}, {1015, -18318, 328}}, Trigger9 = {{16352, -3063, -123}, {17071, -2835, 205}}, TriggerYanmirTrap = {{123, -9513, -5}, {891, -6697, 251}}}
local YANMIR = 71
local GIANTS = {55, 56, 57, 58}
local SUPPORT_HINT = {"PerceptionBrush2", "PerceptionBrush5", "PerceptionBrush3", "PerceptionBrush6", "PerceptionBrush4", "PerceptionBrush7"}
local HINTS = {PerceptionBrush0 = 450, PerceptionBrush1 = 451, PerceptionBrush2 = 452, PerceptionBrush3 = 453, PerceptionBrush4 = 454, PerceptionBrush5 = 455, PerceptionBrush6 = 456, PerceptionBrush7 = 457}
local KICK_DOORS = {{"DPortal0", 492, 4628, 655}, {"DPortal1", -5079, 5202, 655}, {"DPortal10", -5693, 1065, 0}, {"DPortal11", 2335, 3441, 655}, {"DPortal12", -1352, 3441, 655}, {"DPortal13", -7987, 3441, 655}, {"DPortal14", 4178, 3441, 328}, {"DPortal15", 6267, 5079, 328}, {"DPortal16", 7864, -1843, 0}, {"DPortal17", 6554, -4219, 0}, {"DPortal18", -5079, -41, 0}, {"DPortal19", 492, -5612, 0}, {"DPortal20", 492, -11182, 0}, {"DPortal21", -1270, -7864, 0}, {"DPortal22", -3973, -2458, 0}, {"DPortal23", 4956, -2458, 0}, {"DPortal24", 9236, -2458, 0}, {"DPortal27", 17654, -16056, 0}, {"DPortal29", 696, -18678, 0}, {"DPortal30", 3564, -20316, 0}, {"DPortal31", -328, -20357, 0}, {"DPortal35", 16712, -2662, 0}, {"DPortal36", 18678, -13804, 0}, {"Portal10", 14694, -8847, 0}, {"Portal12", 4864, -13763, 0}, {"Portal2", 6226, -16988, 0}, {"Portal4", 7537, -11090, 0}, {"Portal6", 11796, -9492, 0}, {"Portal8", 9144, -9503, 0}}

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(1, DoorAction.Trigger) evt.SetDoorState(2, DoorAction.Trigger) end   -- DPortal0
handlers[102] = function() evt.SetDoorState(3, DoorAction.Trigger) evt.SetDoorState(4, DoorAction.Trigger) end   -- DPortal1
handlers[103] = function() evt.SetDoorState(5, DoorAction.Trigger) evt.SetDoorState(6, DoorAction.Trigger) end   -- DPortal10
handlers[104] = function() evt.SetDoorState(7, DoorAction.Trigger) evt.SetDoorState(8, DoorAction.Trigger) end   -- DPortal11
handlers[105] = function() evt.SetDoorState(9, DoorAction.Trigger) evt.SetDoorState(10, DoorAction.Trigger) end   -- DPortal12
handlers[106] = function() evt.SetDoorState(11, DoorAction.Trigger) evt.SetDoorState(12, DoorAction.Trigger) end   -- DPortal13
handlers[107] = function() evt.SetDoorState(13, DoorAction.Trigger) evt.SetDoorState(14, DoorAction.Trigger) end   -- DPortal14
handlers[108] = function() evt.SetDoorState(15, DoorAction.Trigger) evt.SetDoorState(16, DoorAction.Trigger) end   -- DPortal15
handlers[109] = function() evt.SetDoorState(17, DoorAction.Trigger) evt.SetDoorState(18, DoorAction.Trigger) end   -- DPortal16
handlers[110] = function() evt.SetDoorState(19, DoorAction.Trigger) evt.SetDoorState(20, DoorAction.Trigger) end   -- DPortal17
handlers[111] = function() evt.SetDoorState(21, DoorAction.Trigger) evt.SetDoorState(22, DoorAction.Trigger) end   -- DPortal18
handlers[112] = function() evt.SetDoorState(23, DoorAction.Trigger) evt.SetDoorState(24, DoorAction.Trigger) end   -- DPortal19
handlers[113] = function() evt.SetDoorState(25, DoorAction.Trigger) evt.SetDoorState(26, DoorAction.Trigger) end   -- DPortal20
handlers[114] = function() evt.SetDoorState(27, DoorAction.Trigger) evt.SetDoorState(28, DoorAction.Trigger) end   -- DPortal21
handlers[115] = function() evt.SetDoorState(29, DoorAction.Trigger) evt.SetDoorState(30, DoorAction.Trigger) end   -- DPortal22
handlers[116] = function() evt.SetDoorState(31, DoorAction.Trigger) evt.SetDoorState(32, DoorAction.Trigger) end   -- DPortal23
handlers[117] = function() evt.SetDoorState(33, DoorAction.Trigger) evt.SetDoorState(34, DoorAction.Trigger) end   -- DPortal24
handlers[118] = function() evt.SetDoorState(35, DoorAction.Trigger) evt.SetDoorState(36, DoorAction.Trigger) end   -- DPortal27
handlers[119] = function() evt.SetDoorState(37, DoorAction.Trigger) evt.SetDoorState(38, DoorAction.Trigger) end   -- DPortal29
handlers[120] = function() evt.SetDoorState(39, DoorAction.Trigger) evt.SetDoorState(40, DoorAction.Trigger) end   -- DPortal30
handlers[121] = function() evt.SetDoorState(41, DoorAction.Trigger) evt.SetDoorState(42, DoorAction.Trigger) end   -- DPortal31
handlers[122] = function() evt.SetDoorState(43, DoorAction.Trigger) evt.SetDoorState(44, DoorAction.Trigger) end   -- DPortal35
handlers[123] = function() evt.SetDoorState(45, DoorAction.Trigger) evt.SetDoorState(46, DoorAction.Trigger) end   -- DPortal36
handlers[124] = function() evt.SetDoorState(49, DoorAction.Trigger) evt.SetDoorState(50, DoorAction.Trigger) end   -- Portal10
handlers[125] = function() evt.SetDoorState(51, DoorAction.Trigger) evt.SetDoorState(52, DoorAction.Trigger) end   -- Portal12
handlers[126] = function() evt.SetDoorState(53, DoorAction.Trigger) evt.SetDoorState(54, DoorAction.Trigger) end   -- Portal2
handlers[127] = function() evt.SetDoorState(55, DoorAction.Trigger) evt.SetDoorState(56, DoorAction.Trigger) end   -- Portal4
handlers[128] = function() evt.SetDoorState(57, DoorAction.Trigger) evt.SetDoorState(58, DoorAction.Trigger) end   -- Portal6
handlers[129] = function() evt.SetDoorState(59, DoorAction.Trigger) evt.SetDoorState(60, DoorAction.Trigger) end   -- Portal8

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest10
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest1
handlers[43] = function() evt.OpenChest(2) end   -- TreasureChest5
handlers[44] = function() evt.OpenChest(3) end   -- TreasureChest6
handlers[45] = function() evt.OpenChest(4) end   -- TreasureChest7
handlers[46] = function() evt.OpenChest(5) end   -- TreasureChest9
handlers[47] = function() evt.OpenChest(6) end   -- TreasureChest8
handlers[48] = function() evt.OpenChest(7) end   -- TreasureChest12
handlers[49] = function() evt.OpenChest(8) end   -- TreasureChest2
handlers[50] = function() evt.OpenChest(9) end   -- TChestWNote4
handlers[51] = function() evt.OpenChest(10) end   -- TreasureChest0


-- PerceptionBrushes: the secret wall (0) and the trap hall's floor (1) show to a party with Perception 10; the six
-- supports' (2-7) have no PerceptionValue and show until their support breaks (YanmirTrap.scr :Init).
local function perceptive() return evt.CheckSkill(29, 0, 10) end
local function hintGone(name)
    if name == "PerceptionBrush0" then return var("SecretOpen") == 1 end
    if name == "PerceptionBrush1" then return var("TrapFired") == 1 end
    for k, hint in ipairs(SUPPORT_HINT) do
        if hint == name then return var("Support" .. (k - 1)) == 1 end
    end
    return false
end
function updateHints()
    local sees = perceptive()
    set("PerceptiveParty", sees and 1 or 0)
    for name, cog in pairs(HINTS) do
        local needs = name == "PerceptionBrush0" or name == "PerceptionBrush1"
        evt.SetFacetBit(cog, FacetBits.Invisible, (needs and not sees) or hintGone(name))
    end
end

-- YanmirTrap.scr: each broken support (DestructableBrush0-5, HitPoints 1; DeathTrigger Trigger0-5: its
-- PerceptionBrush off, "SupportBroken" to YanmirTrap) counts; at six TriggerYanmirTrap turns on. The supports
-- are scene destructibles: a weapon hit (or a click: the shared killing blow) breaks one and runs its event;
-- the event run any other way breaks it too.
local SUPPORT_ID = {759, 760, 761, 762, 763, 764}
local function breakSupport(k)
    if var("Support" .. k) == 1 then return end
    set("Support" .. k, 1)
    evt.DestroyDestructible(SUPPORT_ID[k + 1])
    local broken = 0
    for j = 0, 5 do broken = broken + var("Support" .. j) end
    if broken >= 6 then set("TrapArmed", 1) end
    updateHints()
end
handlers[200] = function() breakSupport(0) end   -- DestructableBrush0
handlers[201] = function() breakSupport(1) end   -- DestructableBrush1
handlers[202] = function() breakSupport(2) end   -- DestructableBrush2
handlers[203] = function() breakSupport(3) end   -- DestructableBrush3
handlers[204] = function() breakSupport(4) end   -- DestructableBrush4
handlers[205] = function() breakSupport(5) end   -- DestructableBrush5

-- Yanmir (YanmirBase.scr). :Reset CanDamage FALSE: nothing hurts him (TELP 1.3). :GiveEeps: key 69 and the
-- experience on the quest (key 68), else key 173; 8000 by the trap (:OnTimeToDie), 5000 on any other death (:OnDeath).
local function giveEeps(amount)
    if MM9.hasKey(69) == 0 and MM9.hasKey(68) == 1 then
        MM9.giveKey(69); MM9.giveExperience(amount); MM9.playSound("sounds/events/quest.wav")
        return
    end
    if MM9.hasKey(173) == 0 then
        MM9.giveKey(173); MM9.giveExperience(amount); MM9.playSound("sounds/events/quest.wav")
    end
end
local function wakeYanmir()      -- SquishTrigger0/1: "Squish" -> :Begin (wandering, hunting bugs)
    if var("YanmirAwake") == 1 then return end
    if not MM9.receives("yanmirsfort", "Yanmir0", "Squish", YANMIR) then return end   -- dead: none
    set("YanmirAwake", 1)
    evt.WakeActor(YANMIR)
end
-- TriggerYanmirTrap (AIOnly, turned on by YanmirTrap.scr at six supports) -> Yanmir :OnTimeToDie: the
-- cinematic yanmir_death (cutscene.py): YanmirCamera on the trap hall, the key and the experience, his run
-- to YanmirPathA4, startDie (its DestroyFloor key: YanDstruct0 destroyed, FallingFloor0 drops onto Planks0,
-- which breaks with Xbeams0), Fall, removed at the end of the world (Yanmir_EndOfWorld.scr). :DoCamera keeps
-- the camera off for a party on an AIRail tagged 555 (it sees the hall): the same steps on the T_FALL timer.
local EXP_TRAP = 8000
local WATCH = {{{-82, -7291, 0}, {1065, -5612, 41}}, {{-82, -8438, 0}, {1065, -7291, 41}}, {{-82, -11428, 0}, {1065, -8438, 41}}, {{-1270, -8438, 0}, {-82, -7291, 41}}, {{164, -11141, -983}, {819, -6881, -942}}, {{164, -11551, -983}, {819, -11141, -942}}}
local function partyWatches()
    local x, y, z = evt.GetPartyPosition()
    for _, b in ipairs(WATCH) do
        if inBox(b, x, y, z) then return true end
    end
    return false
end
local function trapFires()
    if var("TrapFired") == 1 then return end
    set("TrapFired", 1)
    if not partyWatches() then
        MM9Cinematic.start("yanmir_death")
        return
    end
    set("FallStage", 1)
    MM9Cinematic.runStep("yanmir_death", 1)
    evt.StartTimer(151, seconds(2))
end
handlers[151] = function()   -- the watched fall: FallDown, the floor, the drop, removed
    evt.StopTimer(151)
    local stage = var("FallStage")
    if stage == 1 then
        set("FallStage", 2)
        evt.PlayActorClip(YANMIR, "StartDie", false)
        evt.StartTimer(151, seconds(1.5))
    elseif stage == 2 then
        set("FallStage", 3)
        MM9Cinematic.runStep("yanmir_death", 2); MM9Cinematic.runStep("yanmir_death", 3)
        evt.PlaySoundName("events/stonecrumble.wav", 0, 0, 0)
        evt.PlayActorClip(YANMIR, "Fall", true)
        evt.SetMapActorPosition(YANMIR, 492, -8192, -8960)
        evt.StartTimer(151, seconds(2.5))
    elseif stage == 3 then
        set("FallStage", 4)
        MM9Cinematic.finish("yanmir_death")
    end
end
handlers[241] = function(context)
    if context.actorIndex == YANMIR then evt.SetHookDamage(0) end
end

-- Monsters killed. YanmirBase.scr :OnDeath (any death but the trap): the key and 5 000. The Spawners (Spawner0-5
-- DefaultSpawn "Yeti ...", Spawner6 "Thrall ..."): each Yeti with a DeathTriggerTarget sends one more from its
-- spawner. YanmirFort_BugSpawn.scr: an Ice Lobbercicle of Respawn0-3 (and every one they send) comes back at
-- its Respawn point 600-900 s later (:OnRespawnMe), when the party is not near (:DoSpawn).
local SPAWNERS = {Spawner0 = {monster = 9200, p = {4669, 2458, 410}}, Spawner1 = {monster = 9200, p = {-7782, 737, 573}}, Spawner2 = {monster = 9200, p = {5079, -20480, 164}}, Spawner3 = {monster = 9200, p = {6226, -16794, 164}}, Spawner4 = {monster = 9200, p = {14909, -8847, 164}}, Spawner5 = {monster = 9200, p = {18678, -13435, 164}}, Spawner6 = {monster = 9091, p = {-164, 3932, 819}}}
local RESPAWNS = {Respawn0 = {1085, -3569, 571}, Respawn1 = {402, -9206, 532}, Respawn2 = {5161, 5146, 852}, Respawn3 = {6387, -3512, 466}}
local DEATH_SPAWN = {[0] = "Spawner2", [1] = "Spawner3", [2] = "Spawner2", [14] = "Spawner0", [41] = "Spawner3", [42] = "Spawner2", [47] = "Spawner4", [48] = "Spawner4", [49] = "Spawner5"}
local BUG_RESPAWN = {[59] = "Respawn0", [60] = "Respawn0", [61] = "Respawn1", [62] = "Respawn2", [63] = "Respawn3"}
local PLACED = 72
local function spawnFrom(name)
    local s = SPAWNERS[name]
    if s == nil then return end
    evt.SummonMonstersById({monster = s.monster, x = s.p[1], y = s.p[2], z = s.p[3], radius = 32, group = 4, count = 1})
    set("Spawned" .. name, var("Spawned" .. name) + 1)
end
local function nearestRespawn(x, y)
    local best, bestName = nil, nil
    for name, p in pairs(RESPAWNS) do
        local d = (p[1] - x) ^ 2 + (p[2] - y) ^ 2
        if best == nil or d < best then best, bestName = d, name end
    end
    return bestName
end
handlers[240] = function(context)
    local index = context.actorIndex
    if index == YANMIR then
        set("YanmirGone", 1)
        if var("TrapFired") == 0 then giveEeps(5000) end
        return
    end
    if DEATH_SPAWN[index] ~= nil then spawnFrom(DEATH_SPAWN[index]) end
    local respawn = BUG_RESPAWN[index]
    if respawn == nil and index >= PLACED and context.monsterId == 9105 then
        local x, y = evt.GetMapActorPosition(index)
        if x ~= nil then respawn = nearestRespawn(x, y) end
    end
    if respawn ~= nil then
        set("BugDue" .. respawn, MM9.random(600, 900))
        set("BugsQueued", var("BugsQueued") + 1)
    end
end
local function tickRespawns()       -- once a second
    local x, y = evt.GetPartyPosition()
    for name, p in pairs(RESPAWNS) do
        local due = var("BugDue" .. name)
        if due > 1 then set("BugDue" .. name, due - 1)
        elseif due == 1 then
            if (p[1] - x) ^ 2 + (p[2] - y) ^ 2 > 2000 ^ 2 then
                set("BugDue" .. name, 0)
                evt.SummonMonstersById({monster = 9105, x = p[1], y = p[2], z = p[3], radius = 16, group = 5, count = 1})
                set("BugsRespawned", var("BugsRespawned") + 1)
            else
                set("BugDue" .. name, 5)     -- :DoSpawn waits while the player can see it
            end
        end
    end
end

-- The secret wall (Secretdoor: PushOpen, OpenTrigger "lock": it opens once and stays open).
handlers[210] = function()
    if var("SecretOpen") == 1 then return end
    set("SecretOpen", 1)
    openGroup("Secretdoor")
    updateHints()
end

-- Yanmir's key (YanmirKey.scr :GiveKeyToPlayer) is a world item (570, dungeon/pickups.py) that gives key 7001;
-- :UnlockCages: with it the teleporter doors (DoorTeleportRight/Left) and the cages (RotatingDoor61-67) open.
-- The teleporter doors and the cages are Locked until the key; then they open on a click.
handlers[211] = function()
    if MM9.hasKey(7001) == 0 then evt.StatusText("The door is locked.") return end
    toggleGroup("DPortal37")
end
handlers[220] = function()   -- RotatingDoor61
    if MM9.hasKey(7001) == 0 then evt.StatusText("The cage is locked.") return end
    toggleGroup("RotatingDoor61")
end
handlers[221] = function()   -- RotatingDoor62
    if MM9.hasKey(7001) == 0 then evt.StatusText("The cage is locked.") return end
    toggleGroup("RotatingDoor62")
end
handlers[222] = function()   -- RotatingDoor63
    if MM9.hasKey(7001) == 0 then evt.StatusText("The cage is locked.") return end
    toggleGroup("RotatingDoor63")
end
handlers[223] = function()   -- RotatingDoor64
    if MM9.hasKey(7001) == 0 then evt.StatusText("The cage is locked.") return end
    toggleGroup("RotatingDoor64")
end
handlers[224] = function()   -- RotatingDoor65
    if MM9.hasKey(7001) == 0 then evt.StatusText("The cage is locked.") return end
    toggleGroup("RotatingDoor65")
end
handlers[225] = function()   -- RotatingDoor66
    if MM9.hasKey(7001) == 0 then evt.StatusText("The cage is locked.") return end
    toggleGroup("RotatingDoor66")
end
handlers[226] = function()   -- RotatingDoor67
    if MM9.hasKey(7001) == 0 then evt.StatusText("The cage is locked.") return end
    toggleGroup("RotatingDoor67")
end

-- The children (YanmirChild.scr, ScriptParams TPS2). :ShoutForHelp: the first child to see the party calls for
-- help once per visit (RolloverText 200, or 201 with key 7001). :OnUse: with key 7001 the child
-- follows the party to the teleporter and escapes through it (:EscapeLevel, RemoveObject); here a click with the
-- key sends it to the teleporter at once (no followers: README).
local CHILD = {ChildFar0 = 64, ChildFar2 = 65, ChildFar3 = 66, ChildFar1 = 67, ChildNear0 = 68, ChildNear1 = 69, ChildNear2 = 70}
local shouted = false
local function shoutForHelp()
    if shouted then return end
    for name, index in pairs(CHILD) do
        -- OnFoundPlayer: a dead child's callbacks do not fire (MM9.actorAlive)
        if var("Escaped" .. name) == 0 and MM9.actorAlive(index)
                and evt.IsMapActorWithinPartyDistance(index, 1536) then
            shouted = true
            if MM9.hasKey(7001) == 1 then
                evt.StatusText("Hey, you!  Help us outta here!  Hurry!!!")
            else
                evt.StatusText("Hey!  Did you find Yanmir's key?  Help us get out!")
            end
            set("ChildShouted", 1)
            return
        end
    end
end
local function rescue(name)
    if not MM9.receives("yanmirsfort", name, "use", CHILD[name]) then return end   -- a dead child: none
    if MM9.hasKey(7001) == 0 then MM9.openRude(433) return end   -- :OnUse Exit FALSE: DoRude
    if var("Escaped" .. name) == 1 then return end
    set("Escaped" .. name, 1)
    set("Rescued", var("Rescued") + 1)
    MM9.removeActor(CHILD[name])
    evt.StatusText("Thank you! The child runs for the teleporter.")
end
handlers[53618] = function() rescue("ChildFar0") end   -- ChildFar0, YanmirChild.scr :OnUse
handlers[53619] = function() rescue("ChildFar2") end   -- ChildFar2, YanmirChild.scr :OnUse
handlers[53620] = function() rescue("ChildFar3") end   -- ChildFar3, YanmirChild.scr :OnUse
handlers[53621] = function() rescue("ChildFar1") end   -- ChildFar1, YanmirChild.scr :OnUse
handlers[53622] = function() rescue("ChildNear0") end   -- ChildNear0, YanmirChild.scr :OnUse
handlers[53623] = function() rescue("ChildNear1") end   -- ChildNear1, YanmirChild.scr :OnUse
handlers[53624] = function() rescue("ChildNear2") end   -- ChildNear2, YanmirChild.scr :OnUse

-- YanmirBase.scr :BD_OnDoor -> :KickDoor (PlayAnim KickDoor) -> its OpenDoor model key -> :OpenDoor
-- (stonedoorslam.wav, "Use" on the door): a shut door within 700 of Yanmir is kicked open (native monsters do
-- not open doors). He plays kick_door, and the next check, 0.5 s later (the key is at 0.488 s), opens the door
-- (Kicked 1: kicked, 2: open). No door state reaches the Lua, so only a door's first kick plays the clip:
-- one the party shut again opens as he passes. As MM9's KickDoor holds his path (SavePath), he stands
-- facing the door through the clip and walks on at the check after the opening (the clip's end).
local kickHold = 0
local function kickDoors()
    if kickHold > 0 then
        kickHold = kickHold - 1
        if kickHold == 0 then
            evt.SetActorImmobile(YANMIR, false)
            if var("TrapFired") == 0 then evt.ClearActorPresentation(YANMIR) end
        end
    end
    for _, d in ipairs(KICK_DOORS) do
        if var("Kicked" .. d[1]) == 1 then   -- kicked at the last check: the clip's OpenDoor key
            set("Kicked" .. d[1], 2)
            evt.PlaySoundName("door/stonedoorslam.wav", d[2], d[3], d[4])
            openGroup(d[1])
        end
    end
    if var("YanmirAwake") == 0 or var("YanmirGone") == 1 or not MM9.actorAlive(YANMIR) then return end
    local yx, yy, yz = evt.GetMapActorPosition(YANMIR)
    if yx == nil then return end
    for _, d in ipairs(KICK_DOORS) do
        if (d[2] - yx) ^ 2 + (d[3] - yy) ^ 2 < 700 ^ 2 and math.abs(d[4] - yz) < 600 then
            if var("Kicked" .. d[1]) == 0 then
                set("Kicks", var("Kicks") + 1)
                set("Kicked" .. d[1], 1)
                evt.PlayActorClip(YANMIR, "kick_door")
                evt.FaceActorTo(YANMIR, d[2], d[3], 0.15)
                evt.SetActorImmobile(YANMIR, true)
                kickHold = 2
            else
                openGroup(d[1])
            end
        end
    end
end

-- MM9's Trigger volumes, polled four times a second: SquishTrigger0/1 wake Yanmir; Trigger6-10 send their
-- spawner's monster once (MessageName1 "off"); TriggerYanmirTrap (AIOnly) fires on Yanmir once armed;
-- EndOfWorldTrigger: a party that falls through the trap hall's floor goes to Frosgard City (PlayerExit,
-- "FallingStart"); the fallen floor stops 399 LT down (README), MM9's shaft goes on to -3520.
local VOLUMES = {
    {name = "SquishTrigger0", run = wakeYanmir}, {name = "SquishTrigger1", run = wakeYanmir},
    {name = "Trigger6", run = function() spawnFrom("Spawner0") end},
    {name = "Trigger7", run = function() spawnFrom("Spawner1") end},
    {name = "Trigger8", run = function() spawnFrom("Spawner2") end},
    {name = "Trigger9", run = function() spawnFrom("Spawner4") end},
    {name = "Trigger10", run = function() spawnFrom("Spawner6") end},
}
local inside, polls = {}, 0
handlers[150] = function()
    evt.StartTimer(150, seconds(0.25))
    local x, y, z = evt.GetPartyPosition()
    polls = polls + 1
    for _, v in ipairs(VOLUMES) do
        local now = inBox(BOX[v.name], x, y, z)
        if now and not inside[v.name] and var("Done" .. v.name) == 0 then
            set("Done" .. v.name, 1)
            v.run()
        end
        inside[v.name] = now
    end
    -- "TimeToDie" from Yanmir's own touch: a dead or removed Yanmir takes none (MM9.actorAlive)
    if var("TrapArmed") == 1 and var("TrapFired") == 0 and MM9.actorAlive(YANMIR) then
        local yx, yy, yz = evt.GetMapActorPosition(YANMIR)
        local b = BOX.TriggerYanmirTrap
        if yx ~= nil and yx >= b[1][1] and yx <= b[2][1] and yy >= b[1][2] and yy <= b[2][2] then trapFires() end
    end
    if polls % 2 == 0 then kickDoors() end
    if var("TrapFired") == 1 and inBox(BOX.EndOfWorld, x, y, z) and var("FellToCity") == 0 then
        set("FellToCity", 1)
        evt.MoveToMap(-11633, -9830, -327, 210, 0, 0, 0, 0, "frosgardcity.blv")
    end
    shoutForHelp()
    if polls % 4 == 0 then tickRespawns() end
    if polls % 12 == 0 then updateHints() end
end

handlers[1] = function()   -- map load: the scripts' OnPostStartWorld / OnPostMiniSaveLoad
    if var("TrapFired") == 1 then openGroup("TrapFloor"); openGroup("TrapPlanks") end
    if var("TrapFired") == 1 and var("YanmirGone") == 0 then MM9Cinematic.finish("yanmir_death") end   -- yanmir_death's steps
    if var("SecretOpen") == 1 then openGroup("Secretdoor") end
    -- YanmirHidden.scr :InitYanmirHidden: Yanmir gone, the Forest Giants are there (visible, solid, titan.scr)
    if var("YanmirGone") == 1 then
        MM9.removeActor(YANMIR)
        if var("GiantsOut") == 0 then
            set("GiantsOut", 1)
            evt.SetMonGroupBit(2, MonsterBits.Invisible, false)
        end
    end
    if var("YanmirAwake") == 1 and var("YanmirGone") == 0 then
        evt.SetActorImmobile(YANMIR, false)   -- a kick saved half way (kickDoors' hold is runtime only)
        evt.WakeActor(YANMIR)
    end
    for name, _ in pairs(CHILD) do
        if var("Escaped" .. name) == 1 then MM9.removeActor(CHILD[name]) end
    end
    updateHints()
    evt.StartTimer(150, seconds(0.25))
end
-- MM9's breakable brushes once built as click movers (destructibles.build_breakables): weapons break
-- them; a click still does, as a killing blow (refused while MM9's CanDamage is off).
handlers[38759] = function() evt.DamageDestructible(759, 1000000) end   -- DestructableBrush0
handlers[38760] = function() evt.DamageDestructible(760, 1000000) end   -- DestructableBrush1
handlers[38761] = function() evt.DamageDestructible(761, 1000000) end   -- DestructableBrush2
handlers[38762] = function() evt.DamageDestructible(762, 1000000) end   -- DestructableBrush3
handlers[38763] = function() evt.DamageDestructible(763, 1000000) end   -- DestructableBrush4
handlers[38764] = function() evt.DamageDestructible(764, 1000000) end   -- DestructableBrush5


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
RegisterEvent(114, "Door", handlers[114], "Door")
RegisterEvent(115, "Door", handlers[115], "Door")
RegisterEvent(116, "Door", handlers[116], "Door")
RegisterEvent(117, "Door", handlers[117], "Door")
RegisterEvent(118, "Door", handlers[118], "Door")
RegisterEvent(119, "Door", handlers[119], "Door")
RegisterEvent(120, "Door", handlers[120], "Door")
RegisterEvent(121, "Door", handlers[121], "Door")
RegisterEvent(122, "Door", handlers[122], "Door")
RegisterEvent(123, "Door", handlers[123], "Door")
RegisterEvent(124, "Door", handlers[124], "Door")
RegisterEvent(125, "Door", handlers[125], "Door")
RegisterEvent(126, "Door", handlers[126], "Door")
RegisterEvent(127, "Door", handlers[127], "Door")
RegisterEvent(128, "Door", handlers[128], "Door")
RegisterEvent(129, "Door", handlers[129], "Door")
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(43, "Chest", handlers[43], "Chest")
RegisterEvent(44, "Chest", handlers[44], "Chest")
RegisterEvent(45, "Chest", handlers[45], "Chest")
RegisterEvent(46, "Chest", handlers[46], "Chest")
RegisterEvent(47, "Chest", handlers[47], "Chest")
RegisterEvent(48, "Chest", handlers[48], "Chest")
RegisterEvent(49, "Chest", handlers[49], "Chest")
RegisterEvent(50, "Chest", handlers[50], "Chest")
RegisterEvent(51, "Chest", handlers[51], "Chest")
RegisterEvent(200, "Wooden support", handlers[200])
RegisterEvent(201, "Wooden support", handlers[201])
RegisterEvent(202, "Wooden support", handlers[202])
RegisterEvent(203, "Wooden support", handlers[203])
RegisterEvent(204, "Wooden support", handlers[204])
RegisterEvent(205, "Wooden support", handlers[205])
RegisterMapTimerEvent(151, seconds(3), handlers[151], "Yanmir falls", "", seconds(3))
RegisterEvent(210, "Wall", handlers[210], "Wall")
RegisterEvent(211, "Door", handlers[211], "Door")
RegisterEvent(220, "Cage", handlers[220], "Cage")
RegisterEvent(221, "Cage", handlers[221], "Cage")
RegisterEvent(222, "Cage", handlers[222], "Cage")
RegisterEvent(223, "Cage", handlers[223], "Cage")
RegisterEvent(224, "Cage", handlers[224], "Cage")
RegisterEvent(225, "Cage", handlers[225], "Cage")
RegisterEvent(226, "Cage", handlers[226], "Cage")
RegisterEvent(53618, "ChildFar0", handlers[53618])
RegisterEvent(53619, "ChildFar2", handlers[53619])
RegisterEvent(53620, "ChildFar3", handlers[53620])
RegisterEvent(53621, "ChildFar1", handlers[53621])
RegisterEvent(53622, "ChildNear0", handlers[53622])
RegisterEvent(53623, "ChildNear1", handlers[53623])
RegisterEvent(53624, "ChildNear2", handlers[53624])
RegisterMapTimerEvent(150, seconds(3), handlers[150], "Trigger volumes", "", seconds(3))
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(38759, "DestructableBrush0", handlers[38759], "Boards")
RegisterEvent(38760, "DestructableBrush1", handlers[38760], "Boards")
RegisterEvent(38761, "DestructableBrush2", handlers[38761], "Boards")
RegisterEvent(38762, "DestructableBrush3", handlers[38762], "Boards")
RegisterEvent(38763, "DestructableBrush4", handlers[38763], "Boards")
RegisterEvent(38764, "DestructableBrush5", handlers[38764], "Boards")
RegisterMonsterKilledHook(240, "Monster killed", handlers[240])
RegisterMonsterDamageHook(241, "Yanmir cannot be hurt", handlers[241])


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

-- Cinematic yanmir_death (YanmirBase.scr :OnTimeToDie, Yanmir_Camera.scr): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["yanmir_death"] = {
    { "experience", function()
        giveEeps(EXP_TRAP)
        updateHints()
    end },
    { "floor", function()
        openGroup("TrapFloor")
    end },
    { "planks", function()
        openGroup("TrapPlanks")
    end },
    { "gone", function()
        set("YanmirGone", 1)
        MM9.removeActor(YANMIR)
    end },
}
RegisterEvent(36001, "Cinema yanmir_death: experience", function() MM9Cinematic.runStep("yanmir_death", 1) end)
RegisterEvent(36002, "Cinema yanmir_death: floor", function() MM9Cinematic.runStep("yanmir_death", 2) end)
RegisterEvent(36003, "Cinema yanmir_death: planks", function() MM9Cinematic.runStep("yanmir_death", 3) end)
RegisterEvent(36004, "Cinema yanmir_death: gone", function() MM9Cinematic.runStep("yanmir_death", 4) end)
RegisterEvent(36000, "Cinema yanmir_death: done", function() MM9Cinematic.finish("yanmir_death") end)
MM9Cinematic.play["yanmir_death"] = function()
    if evt.GetMapVar("Cinema.yanmir_death.started", 0) == 0 then
        evt.SetMapVar("Cinema.yanmir_death.started", 1)
        evt.PlayCinematic("yanmir_death", 36000)
    end
end
