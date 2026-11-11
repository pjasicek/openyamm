-- Thjorad Mine, MM9 rework (level_generation/projects/mm9r_thjoradmine/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {ABDoorBoards0 = 1, BarWall0 = 2, BarWall1 = 3, Door0 = 4, Door1 = 5, Door2 = 6, FallingBoard0 = 7, FallingWallTorch0 = 8, FallingWallTorch1 = 9, RotatingDoor0 = 10, RotatingDoor61 = 11, RotatingDoor62 = 12, RotatingDoor63 = 13, Spike0 = 14, Spike1 = 15, Spike10 = 16, Spike11 = 17, Spike12 = 18, Spike13 = 19, Spike14 = 20, Spike15 = 21, Spike16 = 22, Spike17 = 23, Spike2 = 24, Spike3 = 25, Spike4 = 26, Spike5 = 27, Spike6 = 28, Spike7 = 29, Spike8 = 30, Spike9 = 31, Stalagtite = 32, SteamValve0 = 33, Switch2 = 34, Switch3 = 35, Switch4 = 36, Switch5 = 37, deadboltbottom05 = 38, deadbolttop05 = 39, handletrigger05_INV = 40, slidingdoor05 = 41, switch05 = 42}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 902}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}, [44] = {3}, [45] = {4}, [46] = {5}, [47] = {6}, [48] = {7}, [49] = {8}, [50] = {9}, [51] = {10}, [52] = {11}, [53] = {12}, [54] = {13}, [55] = {14}}})

-- Doors: each MM9 door group opens and closes on a click.

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest0
handlers[42] = function() evt.OpenChest(1) end   -- Bin13
handlers[43] = function() evt.OpenChest(2) end   -- MineCar5
handlers[44] = function() evt.OpenChest(3) end   -- MineCar7
handlers[45] = function() evt.OpenChest(4) end   -- Bin16
handlers[46] = function() evt.OpenChest(5) end   -- MineCar9
handlers[47] = function() evt.OpenChest(6) end   -- MineCar4
handlers[48] = function() evt.OpenChest(7) end   -- MineCar1
handlers[49] = function() evt.OpenChest(8) end   -- MineCar0
handlers[50] = function() evt.OpenChest(9) end   -- MovingBin5
handlers[51] = function() evt.OpenChest(10) end   -- MineCar16
handlers[52] = function() evt.OpenChest(11) end   -- MineCar14
handlers[53] = function() evt.OpenChest(12) end   -- MineCar13
handlers[54] = function() evt.OpenChest(13) end   -- MineCar12
handlers[55] = function() evt.OpenChest(14) end   -- TreasureChest1

local function sound(name) evt.PlaySoundName(name, 0, 0, 0) end
local function dust(p, scale) evt.SpawnWorldEffect("mm9:smoke", p[1], p[2], p[3], scale or 1) end
local function hideHint(brush) evt.SetFacetBit(brush, FacetBits.Invisible, true) set("HintOff" .. brush, 1) end
local function sprite(cog, shown) evt.SetSprite(cog, shown) end
-- MM9's breakable brushes and barrels: scene destructibles by DAT name (evt.DestroyDestructible)
local BREAKABLE = {ABMineBoards0 = 602, ABMineBoards1 = 604, ABMineBoards2 = 654, ABMineBoards3 = 655, BustOutBrush0 = 718, BustOutBrush1 = 716, BustOutBrush2 = 717, CaveIn = 595, CaveWall0 = 27, CaveWall1 = 1347, CaveWall2 = 1348, CaveWall3 = 1349, CaveWall4 = 1350, DB_Barrel0 = 665, DB_Barrel1 = 666, DB_Barrel2 = 667, DB_Barrel3 = 664, DB_Barrel4 = 663, DB_Barrel5 = 662, DB_Barrel6 = 661, DB_Barrel7 = 660, DB_Barrel8 = 658, DB_Barrel9 = 659, DestructableBrush0 = 1345, MCarBlocker1 = 603, TorchHolder0 = 637, TorchHolder1 = 675, db12 = 0, db13 = 1, db14 = 2, db15 = 3, db16 = 4, db17 = 5, db18 = 6, db19 = 7, db20 = 8, db21 = 9, db22 = 10, db23 = 11}
local function destroy(name) evt.DestroyDestructible(BREAKABLE[name]) end
-- MM9's EarthQuake objects as camera shakes (MM9_CUTSCENES.md section 5): intensity ShakeAmount / 12, seconds
-- QuakeDuration + ShakeAmount / DecayRate, felt within OuterRadius of the object (MM9's range has no falloff).
local QUAKES = {DBQuakeObject0 = {0.167, 2.2, 12216, -13312, -1354, 768}, DBQuakeObject1 = {0.167, 2.2, 10639, -14925, -1549, 768}, DBQuakeObject2 = {0.083, 2.1, 6584, -14838, -1498, 512}, DBQuakeObject3 = {0.25, 2.0, 5714, -13066, -1108, 1792}, DBQuakeObject4 = {0.167, 2.2, 3, 4055, 148, 768}, DBQuakeObject5 = {0.167, 2.2, -1972, 1027, 1116, 768}, TunnelQuake2 = {0.167, 7.0, 26665, -2171, -1362, 1280}}
local function quake(name)
    local q = QUAKES[name]
    evt.CameraShake(q[1], q[2], q[3], q[4], q[5], q[6], q[6])
end
-- ThjoradQuake.scr (QuakeObject): every 300-600 s a quake at the party, 3-8 s at ShakeAmount 2-5.
handlers[207] = function()
    local amount = evt.RandomBetween(2, 5)
    evt.CameraShake(amount / 12, evt.RandomBetween(3, 8) + amount / 1)
    evt.StartTimer(207, seconds(evt.RandomBetween(300, 600)))
end

-- The entrance door (RotatingDoor Door2, Locked 1, no key): it only jiggles (doorlock02.wav); the exit volume
-- stands in front of it.
handlers[60] = function() sound("door/doorlock02.wav") end

-- The refinery's sliding door (doorportal05): its handle (handletrigger05, PushOpen) opens switch05, draws both
-- deadbolts and locks itself; switch05's OpenTrigger slides the door open (it shuts after 2.75 s), and switch05
-- unlocks the handle when it closes 10 s later: the door opens again from either side (a click on the door is
-- one on its handle). A map load ends a cycle a save cut short.
handlers[61] = function()
    if var("RefineryBusy") == 1 then return end
    set("RefineryBusy", 1)
    open("handletrigger05_INV") open("deadbolttop05") open("deadboltbottom05") open("switch05")
    open("slidingdoor05")
    evt.StartTimer(208, seconds(10))
end
handlers[208] = function() evt.StopTimer(208) set("RefineryBusy", 0) end

-- The lift gates either side of the refinery: Switch2/Switch3 raise and lower Door0 (Portal0), Switch4/Switch5
-- Door1 (Portal1); both levers of a gate swing with it (OpenTrigger/CloseTrigger wiring).
handlers[62] = function() evt.SetDoorState(DOORS.Door0, DoorAction.Trigger) evt.SetDoorState(DOORS.Switch2, DoorAction.Trigger) evt.SetDoorState(DOORS.Switch3, DoorAction.Trigger) end
handlers[63] = function() evt.SetDoorState(DOORS.Door1, DoorAction.Trigger) evt.SetDoorState(DOORS.Switch4, DoorAction.Trigger) evt.SetDoorState(DOORS.Switch5, DoorAction.Trigger) end

-- The spiked barricades (SpikeDoorA.scr on BarWall1, SpikeDoorB.scr on BarWall0, SpikeDoorOpen.scr on
-- ABDoorBoards0): Locked until six BoardSpikes are pulled (BoardSpike.scr: a click, metalwood04.wav, the spike
-- is gone and sends OnePulled); the sixth unlocks and opens it (Sticky). Its OpenTriggers: the barricade locks,
-- DBEffectsTrigger dust and a quake (not built), the perception light off.
local function pulledBarWall0()
    local n = 0
    if var("Spike12") == 1 then n = n + 1 end
    if var("Spike13") == 1 then n = n + 1 end
    if var("Spike14") == 1 then n = n + 1 end
    if var("Spike15") == 1 then n = n + 1 end
    if var("Spike16") == 1 then n = n + 1 end
    if var("Spike17") == 1 then n = n + 1 end
    return n
end
local function openBarWall0()
    if var("BarWall0Open") == 1 then return end
    set("BarWall0Open", 1)
    open("BarWall0")
    dust({-1972, 1027, 1075}, 1.5)
    quake("DBQuakeObject5")
    hideHint(313)
end
handlers[64] = function()   -- BarWall0
    if pulledBarWall0() == 6 then openBarWall0() else sound("door/doorlock02.wav") end
end
handlers[82] = function()   -- Spike12
    if var("Spike12") == 1 then return end
    set("Spike12", 1)
    sound("events/metalwood04.wav")
    open("Spike12")
    if pulledBarWall0() == 6 then openBarWall0() end
end
handlers[83] = function()   -- Spike13
    if var("Spike13") == 1 then return end
    set("Spike13", 1)
    sound("events/metalwood04.wav")
    open("Spike13")
    if pulledBarWall0() == 6 then openBarWall0() end
end
handlers[84] = function()   -- Spike14
    if var("Spike14") == 1 then return end
    set("Spike14", 1)
    sound("events/metalwood04.wav")
    open("Spike14")
    if pulledBarWall0() == 6 then openBarWall0() end
end
handlers[85] = function()   -- Spike15
    if var("Spike15") == 1 then return end
    set("Spike15", 1)
    sound("events/metalwood04.wav")
    open("Spike15")
    if pulledBarWall0() == 6 then openBarWall0() end
end
handlers[86] = function()   -- Spike16
    if var("Spike16") == 1 then return end
    set("Spike16", 1)
    sound("events/metalwood04.wav")
    open("Spike16")
    if pulledBarWall0() == 6 then openBarWall0() end
end
handlers[87] = function()   -- Spike17
    if var("Spike17") == 1 then return end
    set("Spike17", 1)
    sound("events/metalwood04.wav")
    open("Spike17")
    if pulledBarWall0() == 6 then openBarWall0() end
end
local function pulledBarWall1()
    local n = 0
    if var("Spike6") == 1 then n = n + 1 end
    if var("Spike7") == 1 then n = n + 1 end
    if var("Spike8") == 1 then n = n + 1 end
    if var("Spike9") == 1 then n = n + 1 end
    if var("Spike10") == 1 then n = n + 1 end
    if var("Spike11") == 1 then n = n + 1 end
    return n
end
local function openBarWall1()
    if var("BarWall1Open") == 1 then return end
    set("BarWall1Open", 1)
    open("BarWall1")
    dust({3, 4055, 108}, 1.5)
    quake("DBQuakeObject4")
    hideHint(314)
end
handlers[65] = function()   -- BarWall1
    if pulledBarWall1() == 6 then openBarWall1() else sound("door/doorlock02.wav") end
end
handlers[76] = function()   -- Spike6
    if var("Spike6") == 1 then return end
    set("Spike6", 1)
    sound("events/metalwood04.wav")
    open("Spike6")
    if pulledBarWall1() == 6 then openBarWall1() end
end
handlers[77] = function()   -- Spike7
    if var("Spike7") == 1 then return end
    set("Spike7", 1)
    sound("events/metalwood04.wav")
    open("Spike7")
    if pulledBarWall1() == 6 then openBarWall1() end
end
handlers[78] = function()   -- Spike8
    if var("Spike8") == 1 then return end
    set("Spike8", 1)
    sound("events/metalwood04.wav")
    open("Spike8")
    if pulledBarWall1() == 6 then openBarWall1() end
end
handlers[79] = function()   -- Spike9
    if var("Spike9") == 1 then return end
    set("Spike9", 1)
    sound("events/metalwood04.wav")
    open("Spike9")
    if pulledBarWall1() == 6 then openBarWall1() end
end
handlers[80] = function()   -- Spike10
    if var("Spike10") == 1 then return end
    set("Spike10", 1)
    sound("events/metalwood04.wav")
    open("Spike10")
    if pulledBarWall1() == 6 then openBarWall1() end
end
handlers[81] = function()   -- Spike11
    if var("Spike11") == 1 then return end
    set("Spike11", 1)
    sound("events/metalwood04.wav")
    open("Spike11")
    if pulledBarWall1() == 6 then openBarWall1() end
end
local function pulledABDoorBoards0()
    local n = 0
    if var("Spike0") == 1 then n = n + 1 end
    if var("Spike1") == 1 then n = n + 1 end
    if var("Spike2") == 1 then n = n + 1 end
    if var("Spike3") == 1 then n = n + 1 end
    if var("Spike4") == 1 then n = n + 1 end
    if var("Spike5") == 1 then n = n + 1 end
    return n
end
local function openABDoorBoards0()
    if var("ABDoorBoards0Open") == 1 then return end
    set("ABDoorBoards0Open", 1)
    open("ABDoorBoards0")
    dust({10639, -14925, -1590}, 1.5)
    quake("DBQuakeObject1")

    set("LightOff41428", 1); set("Light41428", 1); evt.SetLight(41428, false)
    set("LightOff41429", 1); set("Light41429", 1); evt.SetLight(41429, false)
end
handlers[66] = function()   -- ABDoorBoards0
    if pulledABDoorBoards0() == 6 then openABDoorBoards0() else sound("door/doorlock02.wav") end
end
handlers[70] = function()   -- Spike0
    if var("Spike0") == 1 then return end
    set("Spike0", 1)
    sound("events/metalwood04.wav")
    open("Spike0")
    if pulledABDoorBoards0() == 6 then openABDoorBoards0() end
end
handlers[71] = function()   -- Spike1
    if var("Spike1") == 1 then return end
    set("Spike1", 1)
    sound("events/metalwood04.wav")
    open("Spike1")
    if pulledABDoorBoards0() == 6 then openABDoorBoards0() end
end
handlers[72] = function()   -- Spike2
    if var("Spike2") == 1 then return end
    set("Spike2", 1)
    sound("events/metalwood04.wav")
    open("Spike2")
    if pulledABDoorBoards0() == 6 then openABDoorBoards0() end
end
handlers[73] = function()   -- Spike3
    if var("Spike3") == 1 then return end
    set("Spike3", 1)
    sound("events/metalwood04.wav")
    open("Spike3")
    if pulledABDoorBoards0() == 6 then openABDoorBoards0() end
end
handlers[74] = function()   -- Spike4
    if var("Spike4") == 1 then return end
    set("Spike4", 1)
    sound("events/metalwood04.wav")
    open("Spike4")
    if pulledABDoorBoards0() == 6 then openABDoorBoards0() end
end
handlers[75] = function()   -- Spike5
    if var("Spike5") == 1 then return end
    set("Spike5", 1)
    sound("events/metalwood04.wav")
    open("Spike5")
    if pulledABDoorBoards0() == 6 then openABDoorBoards0() end
end
handlers[170] = function() evt.SetDoorState(DOORS.RotatingDoor61, DoorAction.Trigger) end   -- RotatingDoor61
handlers[171] = function() evt.SetDoorState(DOORS.RotatingDoor62, DoorAction.Trigger) end   -- RotatingDoor62
handlers[172] = function() evt.SetDoorState(DOORS.RotatingDoor63, DoorAction.Trigger) end   -- RotatingDoor63

-- The hard rock (DestructableBrushes db12-db23, 1 HP, stonecrumble.wav; DamageTrigger: its PerceptionBrush off;
-- DeathTrigger: dw OneDown). dw runs tm_hardrock.scr "10 36 5000": the 10th block gives key 36,
-- the quest sound and the experience, and frees Ebora (FreeAtLast). Scene destructibles: the party's weapons
-- break them, a click too (the shared click); these are their destroyed events.
local function rocksBroken()
    local n = 0
    if var("db12") == 1 then n = n + 1 end
    if var("db13") == 1 then n = n + 1 end
    if var("db14") == 1 then n = n + 1 end
    if var("db15") == 1 then n = n + 1 end
    if var("db16") == 1 then n = n + 1 end
    if var("db17") == 1 then n = n + 1 end
    if var("db18") == 1 then n = n + 1 end
    if var("db19") == 1 then n = n + 1 end
    if var("db20") == 1 then n = n + 1 end
    if var("db21") == 1 then n = n + 1 end
    if var("db22") == 1 then n = n + 1 end
    if var("db23") == 1 then n = n + 1 end
    return n
end
local function freeEbora()   -- FreeAtLast to Ebora: a dead Ebora takes none (MM9.receives)
    if var("EboraFree") ~= 0 then return end
    if not MM9.receives("thjoradmine", "Ebora", "FreeAtLast", 46) then return end
    set("EboraFree", 1)
    MM9Cinematic.start("ebora_free")
end
handlers[90] = function()   -- db12
    if var("db12") == 1 then return end
    set("db12", 1)
    hideHint(304)
    if rocksBroken() == 10 and MM9.hasKey(36) == 0 then
        MM9.giveKey(36)
        MM9.playSound("sounds\\events\\quest.wav")
        MM9.giveExperience(5000)
        freeEbora()
    end
end
handlers[91] = function()   -- db13
    if var("db13") == 1 then return end
    set("db13", 1)
    hideHint(310)
    if rocksBroken() == 10 and MM9.hasKey(36) == 0 then
        MM9.giveKey(36)
        MM9.playSound("sounds\\events\\quest.wav")
        MM9.giveExperience(5000)
        freeEbora()
    end
end
handlers[92] = function()   -- db14
    if var("db14") == 1 then return end
    set("db14", 1)
    hideHint(305)
    if rocksBroken() == 10 and MM9.hasKey(36) == 0 then
        MM9.giveKey(36)
        MM9.playSound("sounds\\events\\quest.wav")
        MM9.giveExperience(5000)
        freeEbora()
    end
end
handlers[93] = function()   -- db15
    if var("db15") == 1 then return end
    set("db15", 1)
    hideHint(301)
    if rocksBroken() == 10 and MM9.hasKey(36) == 0 then
        MM9.giveKey(36)
        MM9.playSound("sounds\\events\\quest.wav")
        MM9.giveExperience(5000)
        freeEbora()
    end
end
handlers[94] = function()   -- db16
    if var("db16") == 1 then return end
    set("db16", 1)
    hideHint(303)
    if rocksBroken() == 10 and MM9.hasKey(36) == 0 then
        MM9.giveKey(36)
        MM9.playSound("sounds\\events\\quest.wav")
        MM9.giveExperience(5000)
        freeEbora()
    end
end
handlers[95] = function()   -- db17
    if var("db17") == 1 then return end
    set("db17", 1)
    hideHint(311)
    if rocksBroken() == 10 and MM9.hasKey(36) == 0 then
        MM9.giveKey(36)
        MM9.playSound("sounds\\events\\quest.wav")
        MM9.giveExperience(5000)
        freeEbora()
    end
end
handlers[96] = function()   -- db18
    if var("db18") == 1 then return end
    set("db18", 1)
    hideHint(307)
    if rocksBroken() == 10 and MM9.hasKey(36) == 0 then
        MM9.giveKey(36)
        MM9.playSound("sounds\\events\\quest.wav")
        MM9.giveExperience(5000)
        freeEbora()
    end
end
handlers[97] = function()   -- db19
    if var("db19") == 1 then return end
    set("db19", 1)
    hideHint(302)
    if rocksBroken() == 10 and MM9.hasKey(36) == 0 then
        MM9.giveKey(36)
        MM9.playSound("sounds\\events\\quest.wav")
        MM9.giveExperience(5000)
        freeEbora()
    end
end
handlers[98] = function()   -- db20
    if var("db20") == 1 then return end
    set("db20", 1)
    hideHint(312)
    if rocksBroken() == 10 and MM9.hasKey(36) == 0 then
        MM9.giveKey(36)
        MM9.playSound("sounds\\events\\quest.wav")
        MM9.giveExperience(5000)
        freeEbora()
    end
end
handlers[99] = function()   -- db21
    if var("db21") == 1 then return end
    set("db21", 1)
    hideHint(309)
    if rocksBroken() == 10 and MM9.hasKey(36) == 0 then
        MM9.giveKey(36)
        MM9.playSound("sounds\\events\\quest.wav")
        MM9.giveExperience(5000)
        freeEbora()
    end
end
handlers[100] = function()   -- db22
    if var("db22") == 1 then return end
    set("db22", 1)
    hideHint(306)
    if rocksBroken() == 10 and MM9.hasKey(36) == 0 then
        MM9.giveKey(36)
        MM9.playSound("sounds\\events\\quest.wav")
        MM9.giveExperience(5000)
        freeEbora()
    end
end
handlers[101] = function()   -- db23
    if var("db23") == 1 then return end
    set("db23", 1)
    hideHint(308)
    if rocksBroken() == 10 and MM9.hasKey(36) == 0 then
        MM9.giveKey(36)
        MM9.playSound("sounds\\events\\quest.wav")
        MM9.giveExperience(5000)
        freeEbora()
    end
end
-- EboraMines.scr :FreeAtLast (also on damage): the cinematic ebora_free (thjoradmine.cinematics.yml): the
-- camera on her, she taunts and vanishes in a column of fire; its gameplay steps are events 36001-36002.

-- The cave-in (Trigger7: CaveIn DamageOn, Destroy): the floor over the flooded cavern gives way under the party
-- (CaveIn's DeathTrigger: CaveInControl OneDown, tm_hardrock.scr "1 35 5000").
handlers[140] = function()
    if var("CaveIn") == 1 then return end
    set("CaveIn", 1)
    destroy("CaveIn")
end
handlers[215] = function()   -- CaveIn destroyed
    set("BrokenCaveIn", 1)
    if MM9.hasKey(35) == 0 then
        MM9.giveKey(35)
        MM9.playSound("sounds\\events\\quest.wav")
        MM9.giveExperience(5000)
    end
end

-- The gnolls' cages (TriggerHardRock -> TroglodyteGnoll0-2 ForceBreak, KingKong.scr: dragonredrattack3.wav,
-- the cage wall BustOutBrush<k> destroyed, the gnoll hunts the party). A click on a cage wall breaks it too.
-- Each gnoll breaks only its own wall (ScriptParams p0); a dead one takes no ForceBreak (MM9.receives) and
-- leaves its wall standing. :BreakCage swings at the wall as it breaks (PlayAnim hattack1: the model's
-- attack_melee); their ScriptParams name no ANIM_NAME, so nothing loops while they wait.
local GNOLLS = {9, 10, 11}
local BUSTOUT = {{"TroglodyteGnoll0", 9, "BustOutBrush0"}, {"TroglodyteGnoll1", 11, "BustOutBrush1"}, {"TroglodyteGnoll2", 10, "BustOutBrush2"}}   -- gnoll, its actor, its wall
local function bustOut(wall)
    if var(wall) == 1 then return end
    set(wall, 1)
    destroy(wall)
end
handlers[141] = function()
    if var("BustOut") == 1 then return end
    set("BustOut", 1)
    for _, g in ipairs(BUSTOUT) do
        if MM9.receives("thjoradmine", g[1], "ForceBreak", g[2]) then
            sound("animsounds/dragonredrattack3.wav")
            bustOut(g[3])
            evt.PlayActorClip(g[2], "attack_melee")
        end
    end
    evt.WakeGroup(3)
    evt.SetMonGroupBit(3, MonsterBits.Hostile, true)
end
handlers[111] = function() sound("events/crate_smash.wav") bustOut("BustOutBrush0") end   -- BustOutBrush0
handlers[112] = function() sound("events/crate_smash.wav") bustOut("BustOutBrush1") end   -- BustOutBrush1
handlers[113] = function() sound("events/crate_smash.wav") bustOut("BustOutBrush2") end   -- BustOutBrush2

-- The cave wall (CaveWall0-4, DestructableBrush, 10 HP each; DeathTrigger: AITrk528 On, an AI rail): weapons
-- break the pieces one by one; a click on any breaks all five.
handlers[102] = function()
    if var("CaveWall") == 1 then return end
    set("CaveWall", 1)
    destroy("CaveWall0")
    destroy("CaveWall1")
    destroy("CaveWall2")
    destroy("CaveWall3")
    destroy("CaveWall4")
end

-- The stalactite (DestructableBrush0, 1 HP; DamageTrigger plightofftrigger: PerceptionLight7-9 off;
-- DeathTrigger: Stalagtite toggle, a Door falling 160 LT at 300 LT/s): its destroyed event.
handlers[107] = function()
    if var("Stalactite") == 1 then return end
    set("Stalactite", 1)
    open("Stalagtite")
    set("LightOff41433", 1); set("Light41433", 1); evt.SetLight(41433, false)
    set("LightOff41434", 1); set("Light41434", 1); evt.SetLight(41434, false)
    set("LightOff41435", 1); set("Light41435", 1); evt.SetLight(41435, false)
    quake("TunnelQuake2")   -- the Stalagtite door's OpenTrigger: TunnelQuake2 On
end

-- The breakable brushes' destroyed events (scene destructibles; ABMineBoards0's DBEffectsTrigger0, ABMineBoards1's
-- DustObject3, ABMineBoards2's DBEffectsTrigger3, ABMineBoards3's DustObject15, TorchHolder1's DustOjbect5): each
-- marks Broken<name>.
handlers[210] = function() set("BrokenCaveWall0", 1) end   -- CaveWall0 destroyed
handlers[211] = function() set("BrokenCaveWall1", 1) end   -- CaveWall1 destroyed
handlers[212] = function() set("BrokenCaveWall2", 1) end   -- CaveWall2 destroyed
handlers[213] = function() set("BrokenCaveWall3", 1) end   -- CaveWall3 destroyed
handlers[214] = function() set("BrokenCaveWall4", 1) end   -- CaveWall4 destroyed
handlers[216] = function() set("BrokenABMineBoards0", 1) dust({12216, -13309, -1316}, 1.5) quake("DBQuakeObject0") end   -- ABMineBoards0 destroyed
handlers[217] = function() set("BrokenABMineBoards1", 1) sound("events/crate_smash.wav") dust({7777, -12093, -1288}, 1.5) end   -- ABMineBoards1 destroyed
handlers[218] = function() set("BrokenABMineBoards2", 1) quake("DBQuakeObject3") dust({5960, -13066, -1116}, 1.5) end   -- ABMineBoards2 destroyed
handlers[219] = function() set("BrokenABMineBoards3", 1) dust({5760, -13061, -1116}, 1.5) end   -- ABMineBoards3 destroyed
handlers[220] = function() set("BrokenMCarBlocker1", 1) end   -- MCarBlocker1 destroyed
handlers[221] = function() set("BrokenTorchHolder1", 1) dust({4490, -12995, -1085}, 0.5) end   -- TorchHolder1 destroyed
handlers[222] = function() set("BrokenBustOutBrush0", 1) end   -- BustOutBrush0 destroyed
handlers[223] = function() set("BrokenBustOutBrush1", 1) end   -- BustOutBrush1 destroyed
handlers[224] = function() set("BrokenBustOutBrush2", 1) end   -- BustOutBrush2 destroyed

-- The falling torch (TM_FallingTorch.scr on FallingWallTorch0; TorchHolder0, 1 HP, DeathTrigger TorchTrigger0:
-- broken by a hit or a click, and the torch falls to FallingTorchMarker0). Its flame, TM_TorchFlame.scr, waits
-- 3 s there (:StopHere), then destroys DB_Barrel0 .. DB_Barrel8 one after another (:StartSequence, :Barrel1-8;
-- DustObject6-14, EQHammerImpact.wav, crate_smash.wav), each an Exploding destructible: the shared explode()
-- deals its ExplodeDamage round it. DB_Barrel6/7 run BlowUpTheBoards.scr: ABMineBoards3/2 are destroyed.
local BARRELS = {"DB_Barrel0", "DB_Barrel1", "DB_Barrel2", "DB_Barrel3", "DB_Barrel4", "DB_Barrel5", "DB_Barrel6", "DB_Barrel7", "DB_Barrel8"}
local BARREL_WAIT = {3, 1, 0.5, 0.5, 0.4, 0.3, 0.2, 0.2, 0.1}
local BARREL_AT = {DB_Barrel0 = {4603, -12943, -1167}, DB_Barrel1 = {4669, -13107, -1167}, DB_Barrel2 = {4792, -13271, -1167}, DB_Barrel3 = {4915, -13394, -1167}, DB_Barrel4 = {5325, -13476, -1167}, DB_Barrel5 = {5530, -13394, -1167}, DB_Barrel6 = {5571, -13230, -1167}, DB_Barrel7 = {5530, -12902, -1167}, DB_Barrel8 = {5489, -12657, -1167}}
handlers[108] = function()   -- also TorchHolder0's destroyed event
    if var("Torch0") ~= 0 then return end
    set("Torch0", 1)
    destroy("TorchHolder0") open("FallingWallTorch0")
    set("LightOff41432", 1); set("Light41432", 1); evt.SetLight(41432, false)
    dust({4531, -13012, -1224}, 0.5)
    sound("events/steam_burst04.wav")
    evt.StartTimer(203, seconds(BARREL_WAIT[1]))
end
handlers[203] = function()
    local step = var("Torch0")
    if step == 0 or step > #BARRELS then evt.StopTimer(203) return end
    local b = BARRELS[step]
    destroy(b)
    dust(BARREL_AT[b], 1)
    sound("weapons/eqhammerimpact.wav") sound("events/crate_smash.wav")
    if b == "DB_Barrel7" then destroy("ABMineBoards2") end   -- BlowUpTheBoards.scr "ABMineBoards2"
    if b == "DB_Barrel6" then destroy("ABMineBoards3") end   -- BlowUpTheBoards.scr "ABMineBoards3"
    set("Torch0", step + 1)
    if step + 1 <= #BARRELS then evt.StartTimer(203, seconds(BARREL_WAIT[step + 1])) else evt.StopTimer(203) end
end

-- The mine cart (TM_MineCarA.scr, hit): Gears02.wav, MCarBlocker1 destroyed (PerceptionLight1 off, DustObject2),
-- the cart rolls to MCarAMarker0 at 100 LT/s, doorslammetal01.wav, ABMineBoards0 destroyed; its DamageTrigger
-- knocks FallingWallTorch1 loose (TM_FirstFallingTorch.scr, 0.6 s: TorchHolder1 destroyed), whose flame
-- (TM_FirstFallingFlame.scr "DB_Barrel9") lands, steam_burst04.wav, and 2 s later sets off DB_Barrel9.
-- The cart glides along the track (evt.MoveDecoration; MM9 plays none of its clips), its Gears02.wav loop the
-- scene's AmbientSound608 (on for the ride); at the marker its twin, standing there hidden, takes its
-- place: a moved decoration's collision stays where it was placed, the twin's blocks the track's end.
local CART_GLIDE, CART_SECONDS = {2524, -274, -169}, 9.94   -- 100 LT/s
handlers[110] = function()
    if var("Cart") ~= 0 then return end
    set("Cart", 1)
    set("AmbientSound608", 1)
    destroy("MCarBlocker1")
    set("LightOff41427", 1); set("Light41427", 1); evt.SetLight(41427, false)
    dust({9728, -13069, -1275}, 0.5)
    evt.MoveDecoration(402, CART_GLIDE[1], CART_GLIDE[2], CART_GLIDE[3], CART_SECONDS)
    evt.StartTimer(204, seconds(CART_SECONDS))
end
handlers[109] = function()
    if var("Torch1") ~= 0 then return end
    set("Torch1", 1)
    destroy("TorchHolder1") open("FallingWallTorch1")
    set("LightOff41426", 1); set("Light41426", 1); evt.SetLight(41426, false)
    sound("events/steam_burst04.wav")
    evt.StartTimer(204, seconds(2))
end
handlers[204] = function()
    if var("Cart") == 1 then
        set("Cart", 2)
        set("AmbientSound608", 2)   -- :StopHere: KillSound
        sprite(402, false) sprite(403, true)
        sound("door/doorslammetal01.wav")
        destroy("ABMineBoards0")   -- its destroyed event: the dust and the quake (DBEffectsTrigger0)
        handlers[109]()
        return
    end
    if var("Torch1") == 1 then
        set("Torch1", 2)
        destroy("DB_Barrel9")   -- TM_FirstFallingFlame.scr "DB_Barrel9": Destroy (it explodes)
        dust({12483, -13527, -1408}, 1)
        sound("weapons/eqhammerimpact.wav") sound("events/crate_smash.wav")
    end
    evt.StopTimer(204)
end

-- The falling board (FallingBoard0, PushOpen, Sticky, no closing): it falls once (OpenTriggers: lock,
-- DustObject4, DBQuakeObject2, PerceptionLight5 off).
handlers[67] = function()
    if var("FallingBoard") == 1 then return end
    set("FallingBoard", 1)
    open("FallingBoard0")
    set("LightOff41431", 1); set("Light41431", 1); evt.SetLight(41431, false)
    dust({6579, -14838, -1452}, 1)
    quake("DBQuakeObject2")
end

-- The steam valve (SteamValve0; OpenTriggers: PressuredWater0/1 On, BlueWater0 MoveWater): the jet of water
-- (TM_SteamWater.scr) shoots down the pipe to WaterMarker0 and smashes ABMineBoards1 (DustObject3); the valve
-- then locks open. The jet is not built: the boards break after its run (about a second).
handlers[68] = function()
    if var("Valve") ~= 0 then return end
    set("Valve", 1)
    open("SteamValve0")
    set("LightOff41430", 1); set("Light41430", 1); evt.SetLight(41430, false)
    sound("events/steam_burst04.wav")
    evt.SpawnWorldEffect("mm9:smokestack", 7880, -13396, -1326, 0.4)
    evt.StartTimer(205, seconds(1))
end
handlers[205] = function()
    if var("Valve") ~= 1 then evt.StopTimer(205) return end
    set("Valve", 2)
    destroy("ABMineBoards1")   -- its destroyed event: crate_smash.wav, DustObject3
    evt.StopTimer(205)
end

-- The slag extractor's hatch (RotatingDoor0; OpenTrigger PerceptionBrush0 off, CloseTrigger on).
handlers[69] = function()
    evt.SetDoorState(DOORS.RotatingDoor0, DoorAction.Trigger)
    hideHint(300)
end
-- The broken slag extractor (SlagExtractor.scr :OnUse): without key 9512 it gives item 398 and key 9512 and is
-- gone. :OnShow (sent by the base, SlagBase.scr, to a party holding item 399): 5000 experience, the quest sound,
-- the whole part in its place (SetModelFilenames Machine-Part_Whole), item 399 taken, key 37.
local function showSlag()
    local taken, fixed = MM9.hasKey(9512) == 1, MM9.hasKey(37) == 1
    sprite(400, not taken and not fixed)
    sprite(401, fixed)
end
handlers[130] = function()
    if MM9.hasKey(9512) == 1 or MM9.hasKey(37) == 1 then return end
    if MM9.giveItem(398, "thjoradmine:slag") then
        MM9.giveKey(9512)
        showSlag()
    end
end
handlers[131] = function()
    if MM9.hasKey(37) == 1 then return end
    if MM9.hasItem(399, "thjoradmine:slagbase") == 0 then return end
    MM9.giveExperience(5000)
    MM9.playSound("sounds\\events\\quest.wav")
    MM9.takeItem(399, "thjoradmine:slagbase")
    MM9.giveKey(37)
    showSlag()
end
-- Hjarrand the Fixer (NPC7.scr, Location "Refinery"): in the mine only once paid (key 362; :Init clears
-- visible, solid and gravity otherwise). When his dialogue closes, without key 364, he walks to MMarker1 and
-- paces to MMarker2, MMarker1 and MMarker2, rubbing his beard at each, walks to the Machine, gives key 364, looks
-- at the slag extractor (clip x) and walks off to MMarker3. HjarrandStop is the leg he walks (1-6, 7: done);
-- HjarrandMoving holds the poll off until the leg's arrival event runs (a map load drops the walk: the poll
-- sends him on the same leg again).
local HJARRAND = 45
local HJARRAND_STOPS = {{-2570, 1085, 0}, {-3092, 1065, 0}, {-2570, 1085, 0}, {-3092, 1065, 0}, {-2714, 1009, 0}, {-2908, 1270, 0}}
local function showHjarrand()
    evt.SetMonsterBit(HJARRAND, MonsterBits.Invisible, MM9.hasKey(362) == 0)
end
local function hjarrandWalk()   -- the poll
    local k = var("HjarrandStop")
    if k == 0 or k > #HJARRAND_STOPS or var("HjarrandMoving") == 1 then return end
    local wait = var("HjarrandWait")
    if wait > 0 then set("HjarrandWait", wait - 1) return end
    local p = HJARRAND_STOPS[k]
    evt.ClearActorPresentation(HJARRAND)
    if evt.MoveActorTo(HJARRAND, p[1], p[2], p[3], 180) then set("HjarrandMoving", 1) end
end
handlers[51399] = function()   -- Hjarrand: :OnRude, wait .5, :Refinery2
    if MM9.hasKey(362) == 0 or MM9.hasKey(364) == 1 or var("HjarrandStop") ~= 0 then return end
    set("HjarrandStop", 1) set("HjarrandWait", 2)
end
handlers[180] = function()   -- :OnArrive, :OnMarkMachine, :WalkAway's OnExit
    local k = var("HjarrandStop")
    set("HjarrandMoving", 0)
    if k == 0 or k > #HJARRAND_STOPS then return end
    set("HjarrandStop", k + 1)
    if k <= 4 then
        evt.PlayActorClip(HJARRAND, "rub_beard")
        set("HjarrandWait", 12)
    elseif k == 5 then
        MM9.giveKey(364)
        evt.FaceActorTo(HJARRAND, -2714, 945, 0.4)
        evt.PlayActorClip(HJARRAND, "x")
        set("HjarrandWait", 12)
    end
end
-- Gudrek the Miner (NPC8.scr :OnRude): with key 9510 he walks to Marker3, by the cave-in, and gives key 9511
-- on arrival. While the party is more than 256 LT (655) away he stops and faces it (OnTargetBeyondDist),
-- and walks on once it is within (OnTargetWithinDist). GudrekLead: 1 leading, 2 arrived; GudrekMoving as
-- HjarrandMoving.
local GUDREK = 42
local function gudrekLead()   -- the poll
    if var("GudrekLead") ~= 1 then return end
    local x, y = evt.GetMapActorPosition(GUDREK)
    if x == nil then return end
    local px, py = evt.GetPartyPosition()
    if (x - px) ^ 2 + (y - py) ^ 2 > 655 ^ 2 then
        if var("GudrekMoving") == 1 and evt.StopActorMove(GUDREK) then set("GudrekMoving", 0) end
        if var("GudrekMoving") == 0 then evt.FaceActorTo(GUDREK, px, py, 0.25) end
    elseif var("GudrekMoving") == 0 then
        evt.ClearActorPresentation(GUDREK)
        if evt.MoveActorTo(GUDREK, 6001, 1987, -1352, 181) then set("GudrekMoving", 1) end
    end
end
handlers[51396] = function()   -- Gudrek
    if MM9.hasKey(9510) == 0 or MM9.hasKey(9511) == 1 or var("GudrekLead") ~= 0 then return end
    set("GudrekLead", 1)
end
handlers[181] = function()   -- :OnExit
    set("GudrekMoving", 0)
    if var("GudrekLead") ~= 1 then return end
    set("GudrekLead", 2)
    evt.ClearActorPresentation(GUDREK)
    MM9.giveKey(9511)
end

-- The troglodyte spawns (SpawnMgr.scr "1 1 Troglodyte TriggerSpawn", SpawnLoc.scr on SpawnMarker0-6): each
-- TriggerLocation sends `spawn` to its marker (TriggerLocation0 three times, then the manager Off), one troglodyte
-- appears there and hunts the party; none once 10 of them have died. Each trigger fires once.
local SPAWNED = {SpawnMarker0 = {73, 74, 75}, SpawnMarker1 = {76, 77, 78}, SpawnMarker2 = {79, 80}, SpawnMarker3 = {81, 82, 83}, SpawnMarker4 = {84, 85, 86}, SpawnMarker5 = {87, 88, 89}, SpawnMarker6 = {90, 91, 92}}
local SPAWN_ACTOR = {[73] = true, [74] = true, [75] = true, [76] = true, [77] = true, [78] = true, [79] = true, [80] = true, [81] = true, [82] = true, [83] = true, [84] = true, [85] = true, [86] = true, [87] = true, [88] = true, [89] = true, [90] = true, [91] = true, [92] = true}
local function spawnAt(marker, count)
    if var("SpawnKilled") >= 10 then return end
    local list = SPAWNED[marker]
    for _, index in ipairs(list) do
        if count == 0 then return end
        local key = "Spawned" .. index
        if var(key) == 0 then
            set(key, 1)
            evt.SetMonsterBit(index, MonsterBits.Invisible, false)
            evt.SetMonsterBit(index, MonsterBits.Hostile, true)
            count = count - 1
        end
    end
end
handlers[197] = function(context)
    if SPAWN_ACTOR[context.actorIndex] then set("SpawnKilled", var("SpawnKilled") + 1) end
end
handlers[196] = function(context)
    if context.actorIndex == 46 then freeEbora() end   -- EboraMines.scr: OnDamage FreeAtLast
end
handlers[150] = function() spawnAt("SpawnMarker0", 3) end   -- TriggerLocation0
handlers[151] = function() spawnAt("SpawnMarker1", 1) end   -- TriggerLocation1A
handlers[152] = function() spawnAt("SpawnMarker1", 1) end   -- TriggerLocation1B
handlers[153] = function() spawnAt("SpawnMarker1", 1) end   -- TriggerLocation1C
handlers[154] = function() spawnAt("SpawnMarker2", 1) end   -- TriggerLocation2A
handlers[155] = function() spawnAt("SpawnMarker2", 1) end   -- TriggerLocation2B
handlers[156] = function() spawnAt("SpawnMarker3", 1) end   -- TriggerLocation3A
handlers[157] = function() spawnAt("SpawnMarker3", 1) end   -- TriggerLocation3B
handlers[158] = function() spawnAt("SpawnMarker3", 1) end   -- TriggerLocation3C
handlers[159] = function() spawnAt("SpawnMarker4", 1) end   -- TriggerLocation4A
handlers[160] = function() spawnAt("SpawnMarker4", 1) end   -- TriggerLocation4B
handlers[161] = function() spawnAt("SpawnMarker4", 1) end   -- TriggerLocation4C
handlers[162] = function() spawnAt("SpawnMarker5", 1) end   -- TriggerLocation5A
handlers[163] = function() spawnAt("SpawnMarker5", 1) end   -- TriggerLocation5B
handlers[164] = function() spawnAt("SpawnMarker5", 1) end   -- TriggerLocation5C
handlers[165] = function() spawnAt("SpawnMarker6", 1) end   -- TriggerLocation6A
handlers[166] = function() spawnAt("SpawnMarker6", 1) end   -- TriggerLocation6B
handlers[167] = function() spawnAt("SpawnMarker6", 1) end   -- TriggerLocation6C

-- The touch Triggers, polled four times a second (fire on any part of the party in the box, once).
local function inBox(b, x, y, z) return x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] and z + 170 >= b[1][3] and z <= b[2][3] end
local BOXES = {{name = "Trigger7", event = 140, box = {{6948, 2115, -1777}, {7716, 2883, -1009}}}, {name = "TriggerHardRock", event = 141, box = {{26327, -5048, -1172}, {26839, -4536, -916}}}, {name = "TriggerLocation0", event = 150, box = {{6257, -3466, -1160}, {6513, -3108, -904}}}, {name = "TriggerLocation1A", event = 151, box = {{9984, -1654, -1569}, {10240, -1398, -1313}}}, {name = "TriggerLocation1B", event = 152, box = {{12815, -1029, -1848}, {13071, -773, -1592}}}, {name = "TriggerLocation1C", event = 153, box = {{14781, -1275, -1684}, {15037, -1019, -1428}}}, {name = "TriggerLocation2A", event = 154, box = {{20188, -3732, -1521}, {20444, -3476, -1265}}}, {name = "TriggerLocation2B", event = 155, box = {{18714, -4388, -1521}, {18970, -4132, -1265}}}, {name = "TriggerLocation3A", event = 156, box = {{21335, -2422, -1603}, {21591, -2166, -1347}}}, {name = "TriggerLocation3B", event = 157, box = {{23137, -1521, -1569}, {23393, -1265, -1313}}}, {name = "TriggerLocation3C", event = 158, box = {{24325, -1398, -1439}, {24581, -1142, -1183}}}, {name = "TriggerLocation4A", event = 159, box = {{13307, -5862, -1603}, {13563, -5606, -1347}}}, {name = "TriggerLocation4B", event = 160, box = {{14618, -6927, -1569}, {14874, -6671, -1313}}}, {name = "TriggerLocation4C", event = 161, box = {{15928, -7173, -1684}, {16184, -6917, -1428}}}, {name = "TriggerLocation5A", event = 162, box = {{13307, -8975, -1439}, {13563, -8719, -1183}}}, {name = "TriggerLocation5B", event = 163, box = {{13962, -10778, -1733}, {14218, -10522, -1477}}}, {name = "TriggerLocation5C", event = 164, box = {{15764, -10778, -1603}, {16020, -10522, -1347}}}, {name = "TriggerLocation6A", event = 165, box = {{17894, -1439, -1459}, {18150, -1183, -1203}}}, {name = "TriggerLocation6B", event = 166, box = {{17731, 527, -1500}, {17987, 783, -1244}}}, {name = "TriggerLocation6C", event = 167, box = {{16092, 1674, -1664}, {16348, 1930, -1408}}}}
local BLOWUP = {DB_Barrel7 = "ABMineBoards2", DB_Barrel6 = "ABMineBoards3"}   -- BlowUpTheBoards.scr ScriptParams
handlers[201] = function()
    evt.StartTimer(201, seconds(0.25))
    hjarrandWalk()
    gudrekLead()
    local x, y, z = evt.GetPartyPosition()
    for _, b in ipairs(BOXES) do
        if var("Fired" .. b.name) == 0 and inBox(b.box, x, y, z) then
            set("Fired" .. b.name, 1)
            handlers[b.event]()
        end
    end
    -- BlowUpTheBoards.scr: DB_Barrel7/6's own DeathTrigger sends them HitMe however they broke (a shot, a
    -- neighbour's blast, the torch chain): a destroyed barrel keeps its script and breaks its boards.
    for barrel, boards in pairs(BLOWUP) do
        if evt.IsDestructibleDestroyed(BREAKABLE[barrel]) and not evt.IsDestructibleDestroyed(BREAKABLE[boards]) then
            sound("weapons/eqhammerimpact.wav") sound("events/crate_smash.wav")
            destroy(boards)
        end
    end
end

-- The PerceptionBrushes (PerceptionValue 8): the red glow shows to a party with that Perception;
-- a hint whose object was used stays off. On load and every 3 s.
local HINTS = {300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314}
local function updateHints()
    local want = evt.CheckSkill(29, 0, 8) and 2 or 1
    for _, cog in ipairs(HINTS) do
        evt.SetFacetBit(cog, FacetBits.Invisible, want == 1 or var("HintOff" .. cog) == 1)
    end
end
handlers[206] = updateHints

-- Sign0: BookLetter.scr "572 Letter" (DoLetter 572).
handlers[120] = function() sound("events/bookopen.wav") evt.SimpleMessage("West Mine and Refinery\n\nStep Carefully.") end
-- Sign1: BookLetter.scr "571 Letter" (DoLetter 571).
handlers[121] = function() sound("events/bookopen.wav") evt.SimpleMessage("East Mine.\n\nBeware of Troglodytes.") end
-- Sign2: BookLetter.scr "574 Letter" (DoLetter 574).
handlers[122] = function() sound("events/bookopen.wav") evt.SimpleMessage("Refinery\n\nDanger!  Hot water!") end
-- Sign3: BookLetter.scr "573 Letter" (DoLetter 573).
handlers[123] = function() sound("events/bookopen.wav") evt.SimpleMessage("West Mine\n\nDanger!  Risk of Cave in!") end
-- Sign4: BookLetter.scr "573 Letter" (DoLetter 573).
handlers[124] = function() sound("events/bookopen.wav") evt.SimpleMessage("West Mine\n\nDanger!  Risk of Cave in!") end
-- Sign5: BookLetter.scr "426 Letter" (DoLetter 426).
handlers[125] = function() sound("events/bookopen.wav") evt.SimpleMessage("To all Linesmen\n\nI don't believe you have been working hard enough to convince the foremen to increase Thjoradric output.  I suggest if you do not wish yourselves to be flogged, you will motivate them to increase ore production!\nHejr Emerssen\nProduction Accountant") end
-- Sign6: BookLetter.scr "486 Letter" (DoLetter 486).
handlers[126] = function() sound("events/bookopen.wav") evt.SimpleMessage("Memo\n\nAll miners are to wear their helmets at all times!  There will be no excuses!  If you get hurt because of your neglect to follow the rules, you WILL NOT be given any leeway.  If you have any issue with this, you can take it up with the Senior Foreman himself!\n\nHrolf Enrikssen\nForeman") end
-- Sign7: BookLetter.scr "487 Letter" (DoLetter 487).
handlers[127] = function() sound("events/bookopen.wav") evt.SimpleMessage("Warning\n\nThe mines are getting increasingly dangerous.  It seems that a few Troglodytes have broken through in the east mine.  Do not engage these creatures!  The Thjorad you produce is too valuable to waste your lives on trying to kill them.\n\nLari Roles\nLinesman") end
handlers[1] = function()
    evt.StartTimer(201, seconds(0.25))
    set("RefineryBusy", 0) set("HjarrandMoving", 0) set("GudrekMoving", 0)
    showSlag()
    showHjarrand()
    if var("EboraFree") == 1 or var("EboraFree") == 2 then MM9Cinematic.finish("ebora_free") end
    if var("EboraFree") >= 3 then MM9.removeActor(46) end
    evt.StartTimer(207, seconds(evt.RandomBetween(300, 600)))
    sprite(403, var("Cart") >= 2)
    sprite(402, var("Cart") < 2)
    -- the glide is runtime only: a cart on its way (or gone) stands at its end again
    if var("Cart") >= 1 then evt.MoveDecoration(402, CART_GLIDE[1], CART_GLIDE[2], CART_GLIDE[3], 0) end
    updateHints()
end

-- MM9's greeting voices (dungeon/voices.py): a click on these people plays their GreetingSound or the
-- voice their script's :OnUse plays, then opens their dialogue (or runs the map's own click).
handlers[54396] = function() MM9.playSound("voices/npc/npc_008.wav"); MM9.openRude(8) end   -- CommonerDwarfMaleB1
handlers[54397] = function() MM9.playSound("voices/npc/npc_011.wav"); MM9.openRude(11) end   -- CommonerDwarfMaleB2
handlers[54398] = function() MM9.playSound("voices/npc/npc_009.wav"); MM9.openRude(9) end   -- CommonerDwarfMaleB0
handlers[54399] = function() MM9.playSound("voices/npc/npc_007.wav"); MM9.openRude(7) end   -- CommonerDwarfMaleB4

-- MM9's BonePile objects (dungeon/objects.py): a click searches the pile (evt.SearchLootProp: its
-- TreasureLevel loot once, DiseaseChance; the pile stays).
handlers[30551] = function() evt.SearchLootProp("mm9:thjoradmine:object:551") end   -- Trashpile0
handlers[30552] = function() evt.SearchLootProp("mm9:thjoradmine:object:552") end   -- Trashpile1
handlers[30553] = function() evt.SearchLootProp("mm9:thjoradmine:object:553") end   -- Trashpile2
handlers[30554] = function() evt.SearchLootProp("mm9:thjoradmine:object:554") end   -- Trashpile3
handlers[30555] = function() evt.SearchLootProp("mm9:thjoradmine:object:555") end   -- Trashpile4
handlers[30556] = function() evt.SearchLootProp("mm9:thjoradmine:object:556") end   -- Trashpile5
handlers[30557] = function() evt.SearchLootProp("mm9:thjoradmine:object:557") end   -- Trashpile6
handlers[30558] = function() evt.SearchLootProp("mm9:thjoradmine:object:558") end   -- Trashpile7
handlers[30559] = function() evt.SearchLootProp("mm9:thjoradmine:object:559") end   -- Trashpile8
handlers[30560] = function() evt.SearchLootProp("mm9:thjoradmine:object:560") end   -- Trashpile9
handlers[30561] = function() evt.SearchLootProp("mm9:thjoradmine:object:561") end   -- Trashpile10

-- MM9's exploding destructibles (Exploding 1): breaking deals ExplodeDamage within DamageRadius of its
-- centre to the party and to the other exploding destructibles there (the next of a chain breaks then).
local EXPLODING = {[658] = {{5570, -12698, -1181}, 512, 100}, [659] = {{12513, -13414, -1406}, 512, 100}, [660] = {{5627, -12918, -1181}, 512, 100}, [661] = {{5668, -13204, -1181}, 512, 100}, [662] = {{5586, -13327, -1181}, 512, 100}, [663] = {{5381, -13409, -1181}, 512, 100}, [664] = {{5012, -13409, -1181}, 512, 100}, [665] = {{4685, -12959, -1181}, 512, 100}, [666] = {{4767, -13164, -1181}, 512, 100}, [667] = {{4890, -13286, -1181}, 512, 100}}
local function explode(id)
    local e = EXPLODING[id]
    local c, r = e[1], e[2]
    evt.SpawnWorldEffect("mm9:column_of_fire", c[1], c[2], c[3], 0.6)
    local x, y, z = evt.GetPartyPosition()
    local dz = math.max(0, c[3] - (z + 170), z - c[3])
    if (x - c[1]) ^ 2 + (y - c[2]) ^ 2 + dz ^ 2 <= r * r then
        evt.DamagePlayer(Players.All, const.Damage.Fire, e[3])
    end
    for other, o in pairs(EXPLODING) do
        local q = o[1]
        if other ~= id and (q[1] - c[1]) ^ 2 + (q[2] - c[2]) ^ 2 + (q[3] - c[3]) ^ 2 <= r * r then
            evt.DamageDestructible(other, e[3])
        end
    end
end
-- MM9's breaking destructibles: an urn's SpawnObject TreasureBag drops (evt.SpawnLootContainer).
handlers[30658] = function() explode(658) end   -- DB_Barrel8
handlers[30659] = function() explode(659) end   -- DB_Barrel9
handlers[30660] = function() explode(660) end   -- DB_Barrel7
handlers[30661] = function() explode(661) end   -- DB_Barrel6
handlers[30662] = function() explode(662) end   -- DB_Barrel5
handlers[30663] = function() explode(663) end   -- DB_Barrel4
handlers[30664] = function() explode(664) end   -- DB_Barrel3
handlers[30665] = function() explode(665) end   -- DB_Barrel0
handlers[30666] = function() explode(666) end   -- DB_Barrel1
handlers[30667] = function() explode(667) end   -- DB_Barrel2

-- MM9's breakable brushes once built as click movers (destructibles.build_breakables): weapons break
-- them; a click still does, as a killing blow (refused while MM9's CanDamage is off).
handlers[38000] = function() evt.DamageDestructible(0, 1000000) end   -- db12
handlers[38001] = function() evt.DamageDestructible(1, 1000000) end   -- db13
handlers[38002] = function() evt.DamageDestructible(2, 1000000) end   -- db14
handlers[38003] = function() evt.DamageDestructible(3, 1000000) end   -- db15
handlers[38004] = function() evt.DamageDestructible(4, 1000000) end   -- db16
handlers[38005] = function() evt.DamageDestructible(5, 1000000) end   -- db17
handlers[38006] = function() evt.DamageDestructible(6, 1000000) end   -- db18
handlers[38007] = function() evt.DamageDestructible(7, 1000000) end   -- db19
handlers[38008] = function() evt.DamageDestructible(8, 1000000) end   -- db20
handlers[38009] = function() evt.DamageDestructible(9, 1000000) end   -- db21
handlers[38010] = function() evt.DamageDestructible(10, 1000000) end   -- db22
handlers[38011] = function() evt.DamageDestructible(11, 1000000) end   -- db23
handlers[39345] = function() evt.DamageDestructible(1345, 1000000) end   -- DestructableBrush0

handlers[34675] = function() set("LightOff41426", 1); set("Light41426", 1); evt.SetLight(41426, false) end   -- TorchHolder1 damaged: its hint off

-- MM9's PerceptionLights (dungeon/lights.py perception_lights): the red hint lights shine for a party whose
-- Perception reaches their PerceptionValue (scene pulsing lights, evt.SetLight), checked on load and every
-- 3 s. MM9's Off message: set("LightOff<key>", 1) and evt.SetLight(key, false); On: set("LightOff<key>", 0).
local PERCEPTION_LIGHTS = {[41426] = 8, [41427] = 8, [41428] = 8, [41429] = 8, [41430] = 8, [41431] = 8, [41432] = 8, [41433] = 8, [41434] = 8, [41435] = 8}
handlers[904] = function()
    for key, value in pairs(PERCEPTION_LIGHTS) do
        local want = (var("LightOff" .. key) == 0 and evt.CheckSkill(29, 0, value)) and 2 or 1
        if var("Light" .. key) ~= want then
            set("Light" .. key, want)
            evt.SetLight(key, want == 2)
        end
    end
end
handlers[902] = function()   -- map load: the shared objects
    for key, _ in pairs(PERCEPTION_LIGHTS) do set("Light" .. key, 0) end
    handlers[904]()
end

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
RegisterEvent(52, "Chest", handlers[52], "Chest")
RegisterEvent(53, "Chest", handlers[53], "Chest")
RegisterEvent(54, "Chest", handlers[54], "Chest")
RegisterEvent(55, "Chest", handlers[55], "Chest")
RegisterEvent(51399, "Hjarrand", handlers[51399])
RegisterEvent(180, "Hjarrand arrives", handlers[180])
RegisterEvent(51396, "Gudrek", handlers[51396])
RegisterEvent(181, "Gudrek arrives", handlers[181])
RegisterEvent(60, "Locked door", handlers[60], "Door")
RegisterEvent(61, "Handle", handlers[61], "Door")
RegisterEvent(62, "Lever", handlers[62], "Lever")
RegisterEvent(63, "Lever", handlers[63], "Lever")
RegisterEvent(64, "BarWall0", handlers[64], "Door")
RegisterEvent(65, "BarWall1", handlers[65], "Door")
RegisterEvent(66, "ABDoorBoards0", handlers[66], "Door")
RegisterEvent(70, "Spike", handlers[70], "Spike")
RegisterEvent(71, "Spike", handlers[71], "Spike")
RegisterEvent(72, "Spike", handlers[72], "Spike")
RegisterEvent(73, "Spike", handlers[73], "Spike")
RegisterEvent(74, "Spike", handlers[74], "Spike")
RegisterEvent(75, "Spike", handlers[75], "Spike")
RegisterEvent(76, "Spike", handlers[76], "Spike")
RegisterEvent(77, "Spike", handlers[77], "Spike")
RegisterEvent(78, "Spike", handlers[78], "Spike")
RegisterEvent(79, "Spike", handlers[79], "Spike")
RegisterEvent(80, "Spike", handlers[80], "Spike")
RegisterEvent(81, "Spike", handlers[81], "Spike")
RegisterEvent(82, "Spike", handlers[82], "Spike")
RegisterEvent(83, "Spike", handlers[83], "Spike")
RegisterEvent(84, "Spike", handlers[84], "Spike")
RegisterEvent(85, "Spike", handlers[85], "Spike")
RegisterEvent(86, "Spike", handlers[86], "Spike")
RegisterEvent(87, "Spike", handlers[87], "Spike")
RegisterEvent(90, "Hard rock", handlers[90], "Rock")
RegisterEvent(91, "Hard rock", handlers[91], "Rock")
RegisterEvent(92, "Hard rock", handlers[92], "Rock")
RegisterEvent(93, "Hard rock", handlers[93], "Rock")
RegisterEvent(94, "Hard rock", handlers[94], "Rock")
RegisterEvent(95, "Hard rock", handlers[95], "Rock")
RegisterEvent(96, "Hard rock", handlers[96], "Rock")
RegisterEvent(97, "Hard rock", handlers[97], "Rock")
RegisterEvent(98, "Hard rock", handlers[98], "Rock")
RegisterEvent(99, "Hard rock", handlers[99], "Rock")
RegisterEvent(100, "Hard rock", handlers[100], "Rock")
RegisterEvent(101, "Hard rock", handlers[101], "Rock")
RegisterEvent(102, "Cave wall", handlers[102], "Rock")
RegisterEvent(107, "Stalactite", handlers[107], "Rock")
RegisterEvent(108, "Torch", handlers[108], "Torch")
RegisterEvent(109, "Torch", handlers[109], "Torch")
RegisterEvent(110, "Mine cart", handlers[110], "Mine cart")
RegisterEvent(67, "Board", handlers[67], "Board")
RegisterEvent(68, "Valve", handlers[68], "Valve")
RegisterEvent(69, "Hatch", handlers[69], "Hatch")
RegisterEvent(130, "Slag extractor", handlers[130], "Slag extractor")
RegisterEvent(131, "Machine", handlers[131], "Machine")
RegisterEvent(140, "Cave-in", handlers[140])
RegisterEvent(141, "TriggerHardRock", handlers[141])
RegisterEvent(111, "BustOutBrush0", handlers[111], "Wall")
RegisterEvent(112, "BustOutBrush1", handlers[112], "Wall")
RegisterEvent(113, "BustOutBrush2", handlers[113], "Wall")
RegisterEvent(210, "CaveWall0 destroyed", handlers[210])
RegisterEvent(211, "CaveWall1 destroyed", handlers[211])
RegisterEvent(212, "CaveWall2 destroyed", handlers[212])
RegisterEvent(213, "CaveWall3 destroyed", handlers[213])
RegisterEvent(214, "CaveWall4 destroyed", handlers[214])
RegisterEvent(215, "CaveIn destroyed", handlers[215])
RegisterEvent(216, "ABMineBoards0 destroyed", handlers[216])
RegisterEvent(217, "ABMineBoards1 destroyed", handlers[217])
RegisterEvent(218, "ABMineBoards2 destroyed", handlers[218])
RegisterEvent(219, "ABMineBoards3 destroyed", handlers[219])
RegisterEvent(220, "MCarBlocker1 destroyed", handlers[220])
RegisterEvent(221, "TorchHolder1 destroyed", handlers[221])
RegisterEvent(222, "BustOutBrush0 destroyed", handlers[222])
RegisterEvent(223, "BustOutBrush1 destroyed", handlers[223])
RegisterEvent(224, "BustOutBrush2 destroyed", handlers[224])
RegisterEvent(170, "Door", handlers[170], "Door")
RegisterEvent(171, "Door", handlers[171], "Door")
RegisterEvent(172, "Door", handlers[172], "Door")
RegisterEvent(150, "TriggerLocation0", handlers[150])
RegisterEvent(151, "TriggerLocation1A", handlers[151])
RegisterEvent(152, "TriggerLocation1B", handlers[152])
RegisterEvent(153, "TriggerLocation1C", handlers[153])
RegisterEvent(154, "TriggerLocation2A", handlers[154])
RegisterEvent(155, "TriggerLocation2B", handlers[155])
RegisterEvent(156, "TriggerLocation3A", handlers[156])
RegisterEvent(157, "TriggerLocation3B", handlers[157])
RegisterEvent(158, "TriggerLocation3C", handlers[158])
RegisterEvent(159, "TriggerLocation4A", handlers[159])
RegisterEvent(160, "TriggerLocation4B", handlers[160])
RegisterEvent(161, "TriggerLocation4C", handlers[161])
RegisterEvent(162, "TriggerLocation5A", handlers[162])
RegisterEvent(163, "TriggerLocation5B", handlers[163])
RegisterEvent(164, "TriggerLocation5C", handlers[164])
RegisterEvent(165, "TriggerLocation6A", handlers[165])
RegisterEvent(166, "TriggerLocation6B", handlers[166])
RegisterEvent(167, "TriggerLocation6C", handlers[167])
RegisterEvent(120, "Letter", handlers[120], "Letter")
RegisterEvent(121, "Letter", handlers[121], "Letter")
RegisterEvent(122, "Letter", handlers[122], "Letter")
RegisterEvent(123, "Letter", handlers[123], "Letter")
RegisterEvent(124, "Letter", handlers[124], "Letter")
RegisterEvent(125, "Letter", handlers[125], "Letter")
RegisterEvent(126, "Letter", handlers[126], "Letter")
RegisterEvent(127, "Letter", handlers[127], "Letter")
RegisterMapTimerEvent(201, seconds(3), handlers[201], "Trigger volumes", "", seconds(3))
RegisterMapTimerEvent(207, seconds(3), handlers[207], "Quake", "", seconds(3))
RegisterMapTimerEvent(203, seconds(3), handlers[203], "Barrels", "", seconds(3))
RegisterMapTimerEvent(204, seconds(3), handlers[204], "Mine cart", "", seconds(3))
RegisterMapTimerEvent(205, seconds(3), handlers[205], "Valve", "", seconds(3))
RegisterMapTimerEvent(206, seconds(3), handlers[206], "Perception hints", "", seconds(3))
RegisterMapTimerEvent(208, seconds(3), handlers[208], "Refinery handle", "", seconds(3))
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(54396, "Gudrek the Miner", handlers[54396])
RegisterEvent(54397, "Njal Bjarnissen", handlers[54397])
RegisterEvent(54398, "Ketil Strongpick", handlers[54398])
RegisterEvent(54399, "Hjarrand Fixer", handlers[54399])
RegisterEvent(30551, "Trash Pile", handlers[30551], "Trash Pile")
RegisterEvent(30552, "Trash Pile", handlers[30552], "Trash Pile")
RegisterEvent(30553, "Trash Pile", handlers[30553], "Trash Pile")
RegisterEvent(30554, "Trash Pile", handlers[30554], "Trash Pile")
RegisterEvent(30555, "Trash Pile", handlers[30555], "Trash Pile")
RegisterEvent(30556, "Trash Pile", handlers[30556], "Trash Pile")
RegisterEvent(30557, "Trash Pile", handlers[30557], "Trash Pile")
RegisterEvent(30558, "Trash Pile", handlers[30558], "Trash Pile")
RegisterEvent(30559, "Trash Pile", handlers[30559], "Trash Pile")
RegisterEvent(30560, "Trash Pile", handlers[30560], "Trash Pile")
RegisterEvent(30561, "Trash Pile", handlers[30561], "Trash Pile")
RegisterEvent(30658, "DB_Barrel8", handlers[30658])
RegisterEvent(30659, "DB_Barrel9", handlers[30659])
RegisterEvent(30660, "DB_Barrel7", handlers[30660])
RegisterEvent(30661, "DB_Barrel6", handlers[30661])
RegisterEvent(30662, "DB_Barrel5", handlers[30662])
RegisterEvent(30663, "DB_Barrel4", handlers[30663])
RegisterEvent(30664, "DB_Barrel3", handlers[30664])
RegisterEvent(30665, "DB_Barrel0", handlers[30665])
RegisterEvent(30666, "DB_Barrel1", handlers[30666])
RegisterEvent(30667, "DB_Barrel2", handlers[30667])
RegisterEvent(38000, "db12", handlers[38000], "Rocks")
RegisterEvent(38001, "db13", handlers[38001], "Rocks")
RegisterEvent(38002, "db14", handlers[38002], "Rocks")
RegisterEvent(38003, "db15", handlers[38003], "Rocks")
RegisterEvent(38004, "db16", handlers[38004], "Rocks")
RegisterEvent(38005, "db17", handlers[38005], "Rocks")
RegisterEvent(38006, "db18", handlers[38006], "Rocks")
RegisterEvent(38007, "db19", handlers[38007], "Rocks")
RegisterEvent(38008, "db20", handlers[38008], "Rocks")
RegisterEvent(38009, "db21", handlers[38009], "Rocks")
RegisterEvent(38010, "db22", handlers[38010], "Rocks")
RegisterEvent(38011, "db23", handlers[38011], "Rocks")
RegisterEvent(39345, "DestructableBrush0", handlers[39345], "Rocks")
RegisterEvent(34675, "TorchHolder1", handlers[34675])
RegisterMapTimerEvent(904, seconds(3), handlers[904], "Perception lights", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
RegisterMonsterDamageHook(196, "Ebora hurt", handlers[196])
RegisterMonsterKilledHook(197, "Spawn killed", handlers[197])


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

-- Cinematic ebora_free (EboraMines.scr :FreeAtLast, EboraCam1.scr): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["ebora_free"] = {
    { "fire", function()
        evt.SpawnWorldEffect("mm9:column_of_fire", 24712, -1501, -1169, 1)
        set("EboraFree", 3)
    end },
    { "removed", function()
        MM9.removeActor(46)
        set("EboraFree", 4)
    end },
}
RegisterEvent(36001, "Cinema ebora_free: fire", function() MM9Cinematic.runStep("ebora_free", 1) end)
RegisterEvent(36002, "Cinema ebora_free: removed", function() MM9Cinematic.runStep("ebora_free", 2) end)
RegisterEvent(36000, "Cinema ebora_free: done", function() MM9Cinematic.finish("ebora_free") end)
MM9Cinematic.play["ebora_free"] = function()
    if evt.GetMapVar("Cinema.ebora_free.started", 0) == 0 then
        evt.SetMapVar("Cinema.ebora_free.started", 1)
        evt.PlayCinematic("ebora_free", 36000)
    end
end
