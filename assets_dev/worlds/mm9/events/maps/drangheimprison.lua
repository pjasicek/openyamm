-- Drangheim Prison, MM9 rework (level_generation/projects/mm9r_drangheimprison/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {BarrackDoor02 = 1, BarrackDoor1 = 2, Celldoor1 = 7, Celldoor10 = 8, Celldoor11 = 9, Celldoor12 = 10, Celldoor13 = 11, Celldoor14 = 12, Celldoor15 = 13, Celldoor16 = 14, Celldoor17 = 15, Celldoor18 = 16, Celldoor2 = 17, Celldoor25 = 18, Celldoor26 = 19, Celldoor27 = 20, Celldoor28 = 21, Celldoor29 = 22, Celldoor3 = 23, Celldoor30 = 24, Celldoor31 = 25, Celldoor32 = 26, Celldoor33 = 27, Celldoor34 = 28, Celldoor35 = 29, Celldoor36 = 30, Celldoor37 = 31, Celldoor38 = 32, Celldoor4 = 33, Celldoor5 = 34, Celldoor6 = 35, Celldoor7 = 36, Celldoor8 = 37, Celldoor9 = 38, DDoor10a = 45, DDoor10b = 46, DDoor11a = 47, DDoor11b = 48, DDoor3a = 49, DDoor3b = 50, DDoor4a = 51, DDoor4b = 52, DDoor5a = 53, DDoor5b = 54, DDoor6a = 55, DDoor6b = 56, DDoor7a = 57, DDoor7b = 58, DDoor8a = 59, DDoor8b = 60, DDoor9a = 61, DDoor9b = 62, Door0 = 63, Door1 = 64, Door2 = 65, ElevatorDoorL = 68, ElevatorDoorR = 69, HallDoor1 = 72, HallDoor2 = 73, HallDoor3 = 74, HallDoor4 = 75, LeftDoor0 = 78, LeftDoor1a = 71, Lid1 = 83, LidWheel1 = 82, MessHallDoor0 = 79, RightDoor0 = 77, RightDoor1a = 70, RotatingDoor1 = 67, RotatingDoor10 = 39, RotatingDoor11 = 40, RotatingDoor3 = 76, RotatingDoor6 = 41, RotatingDoor7 = 42, RotatingDoor8 = 43, RotatingDoor9 = 44, SecretDoor0 = 80, SingleDoor1 = 81, SingleDoor9 = 66, blever0 = 84, blever1 = 85, blever2 = 86, guardstation1door = 3, guardstation1door0 = 4, guardstation1door1 = 5, guardstation1door3 = 6, lever0 = 87, lever1 = 88, lever10 = 89, lever11 = 90, lever12 = 91, lever15 = 92, lever17 = 93, lever2 = 94, lever24 = 95, lever25 = 96, lever26 = 97, lever27 = 98, lever28 = 99, lever3 = 100, lever4 = 101, lever5 = 102, lever6 = 103, lever7 = 104, lever8 = 105, lever9 = 106}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}, [44] = {3}, [45] = {4}, [46] = {5}}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(1, DoorAction.Trigger) end   -- BarrackDoor02
handlers[102] = function() evt.SetDoorState(2, DoorAction.Trigger) end   -- BarrackDoor1
handlers[103] = function() evt.SetDoorState(3, DoorAction.Trigger) end   -- Booth0
handlers[104] = function() evt.SetDoorState(4, DoorAction.Trigger) end   -- Booth1
handlers[105] = function() evt.SetDoorState(5, DoorAction.Trigger) end   -- Booth2
handlers[106] = function() evt.SetDoorState(6, DoorAction.Trigger) end   -- Booth3
handlers[107] = function() evt.SetDoorState(25, DoorAction.Trigger) end   -- Celldoor31
handlers[108] = function() evt.SetDoorState(29, DoorAction.Trigger) end   -- Celldoor35
handlers[109] = function() evt.SetDoorState(31, DoorAction.Trigger) end   -- Celldoor37
handlers[110] = function() evt.SetDoorState(45, DoorAction.Trigger) evt.SetDoorState(46, DoorAction.Trigger) end   -- DDoor10
handlers[111] = function() evt.SetDoorState(47, DoorAction.Trigger) evt.SetDoorState(48, DoorAction.Trigger) end   -- DDoor11
handlers[112] = function() evt.SetDoorState(49, DoorAction.Trigger) evt.SetDoorState(50, DoorAction.Trigger) end   -- DDoor3
handlers[113] = function() evt.SetDoorState(51, DoorAction.Trigger) evt.SetDoorState(52, DoorAction.Trigger) end   -- DDoor4
handlers[114] = function() evt.SetDoorState(53, DoorAction.Trigger) evt.SetDoorState(54, DoorAction.Trigger) end   -- DDoor5
handlers[115] = function() evt.SetDoorState(55, DoorAction.Trigger) evt.SetDoorState(56, DoorAction.Trigger) end   -- DDoor6
handlers[116] = function() evt.SetDoorState(57, DoorAction.Trigger) evt.SetDoorState(58, DoorAction.Trigger) end   -- DDoor7
handlers[117] = function() evt.SetDoorState(59, DoorAction.Trigger) evt.SetDoorState(60, DoorAction.Trigger) end   -- DDoor8
handlers[118] = function() evt.SetDoorState(61, DoorAction.Trigger) evt.SetDoorState(62, DoorAction.Trigger) end   -- DDoor9
handlers[119] = function() evt.SetDoorState(63, DoorAction.Trigger) end   -- Door0
handlers[120] = function() evt.SetDoorState(65, DoorAction.Trigger) end   -- Door2
handlers[121] = function() evt.SetDoorState(66, DoorAction.Trigger) evt.SetDoorState(67, DoorAction.Trigger) end   -- Door9
handlers[122] = function() evt.SetDoorState(68, DoorAction.Trigger) evt.SetDoorState(69, DoorAction.Trigger) end   -- ElevatorDoor
handlers[123] = function() evt.SetDoorState(70, DoorAction.Trigger) evt.SetDoorState(71, DoorAction.Trigger) end   -- EntryDoor
handlers[124] = function() evt.SetDoorState(72, DoorAction.Trigger) end   -- HallDoor1
handlers[125] = function() evt.SetDoorState(73, DoorAction.Trigger) end   -- HallDoor2
handlers[126] = function() evt.SetDoorState(74, DoorAction.Trigger) end   -- HallDoor3
handlers[127] = function() evt.SetDoorState(75, DoorAction.Trigger) end   -- HallDoor4
handlers[128] = function() evt.SetDoorState(79, DoorAction.Trigger) end   -- MessHallDoor0
handlers[129] = function() evt.SetDoorState(80, DoorAction.Trigger) end   -- SecretDoor0
handlers[130] = function() evt.SetDoorState(81, DoorAction.Trigger) end   -- SingleDoor1

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- Blackbox
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest4
handlers[43] = function() evt.OpenChest(2) end   -- TreasureChest5
handlers[44] = function() evt.OpenChest(3) end   -- TreasureChest6
handlers[45] = function() evt.OpenChest(4) end   -- TreasureChest3
handlers[46] = function() evt.OpenChest(5) end   -- TreasureChest2

local function arm(timer, delay) set("Armed" .. timer, 1); evt.StartTimer(timer, seconds(delay)) end
local function fired(timer)
    evt.StopTimer(timer)
    if var("Armed" .. timer) ~= 1 then return false end
    set("Armed" .. timer, 0)
    return true
end
local function give(raw, source)
    local item = MM9.ItemIds[raw]
    if item ~= nil and evt.GivePartyMemberItem(math.max(0, evt.GetCurrentPlayerIndex()), item) then return true end
    return MM9.giveItem(raw, source)
end

-- The pass and the alarm (DrangheimHostility.inc, DP_CheckPass.inc, Guardhelp.scr, GuardToNegate.scr): a guard
-- lets the party be while it holds the visitor's pass (key 5007) and has not raised the alarm (key
-- 5006); the gate guards (GuardRude.scr) mind only the alarm.
local INNER_GROUPS = {1, 3, 4, 6, 7, 8}
-- The gate guards (GuardRude.scr :StartWork): 1 in 20 sleeps from the map's start (LoopAnim sleep)
-- until a click wakes him (:OnUse :Wakeup, PlayAnim Stand) or the alarm sounds.
local GATE = {Guard0 = {actor = 52, rude = 425}, Guard1 = {actor = 53, rude = 425}, Guard2 = {actor = 54, rude = 426}}
local function wake(name)
    if var("Asleep" .. name) == 0 then return end
    set("Asleep" .. name, 0)
    evt.ClearActorPresentation(GATE[name].actor)
end
local function rollSleep(name, step)
    local asleep = MM9.hasKey(5006) == 0 and evt.RandomBetween(1, 20, step) == 1
    set("Asleep" .. name, asleep and 1 or 0)
    if asleep then evt.PlayActorClip(GATE[name].actor, "sleep", true) end
end
local function applyHostility()
    local alarm = MM9.hasKey(5006) == 1
    local visitor = MM9.hasKey(5007) == 1 and not alarm
    for _, group in ipairs(INNER_GROUPS) do evt.SetMonGroupBit(group, MonsterBits.Hostile, not visitor) end
    evt.SetMonGroupBit(5, MonsterBits.Hostile, false)   -- the smith never turns (DrangheimSmith.scr)
    evt.SetMonGroupBit(2, MonsterBits.Hostile, alarm)
    -- the alarm's AddEnemy Player: MM9's monster AI walks the gate guards from their posts at the party
    if alarm then
        evt.SetActorImmobile(52, false); wake("Guard0")   -- Guard0
        evt.SetActorImmobile(53, false); wake("Guard1")   -- Guard1
        evt.SetActorImmobile(54, false); wake("Guard2")   -- Guard2
    end
end
local function alarm()    -- TurnHostilityOn, AlarmControl.scr OnAlarm
    if MM9.hasKey(5006) == 0 then
        MM9.giveKey(5006)
        evt.PlaySoundName("events/alarmbell.wav", 0, 0, 0)
    end
    applyHostility()
end
local GUARD_MONSTERS = {[9111] = true, [9112] = true, [9113] = true}
-- DrangheimHostility.inc OnDamage/OnDeath: only the player's blow (IsPlayer) turns a guard on; a Nagate's does not
handlers[96] = function(context) if GUARD_MONSTERS[context.monsterId] and context.byParty then alarm() end end
handlers[97] = function(context) if GUARD_MONSTERS[context.monsterId] and context.byParty then alarm() end end

-- The gate guards (GuardRude.scr :OnRude, :OnMove): the alarm given in the talk goes off; with the pass Guard2
-- (dialogue 426) hands over the Visitor's Pass item (446) and Guard0/1 step aside to their markers.
handlers[54033] = function() wake("Guard0"); MM9.openRude(425, 52) end   -- Guard0 :OnUse
handlers[51033] = function()   -- Guard0
    if MM9.hasKey(5006) == 1 then alarm() return end
    if MM9.hasKey(5007) == 0 then return end
    applyHostility()
    set("AsideGuard0", 1)
    evt.SetMapActorPosition(52, -1751, -6728, -2232)
end
handlers[54034] = function() wake("Guard1"); MM9.openRude(425, 53) end   -- Guard1 :OnUse
handlers[51034] = function()   -- Guard1
    if MM9.hasKey(5006) == 1 then alarm() return end
    if MM9.hasKey(5007) == 0 then return end
    applyHostility()
    set("AsideGuard1", 1)
    evt.SetMapActorPosition(53, -2591, -6717, -2232)
end
handlers[54035] = function() wake("Guard2"); MM9.openRude(426, 54) end   -- Guard2 :OnUse
handlers[51035] = function()   -- Guard2
    if MM9.hasKey(5006) == 1 then alarm() return end
    if MM9.hasKey(5007) == 0 then return end
    applyHostility()
    if MM9.hasItem(446, "drangheimprison:Guard2") == 0 then give(446, "drangheimprison:Guard2") end
end

-- The cook, Aymril Banito (NPC419.scr :OnRude, :Call, :Unlock): with the deal (key 5004) he gives key
-- 5005 and unlocks the cow pen's door (Celldoor29); any other end of the talk calls the guards.
handlers[51039] = function()
    if MM9.hasKey(5004) == 1 then MM9.giveKey(5005) else alarm() end
end
handlers[231] = function()   -- Celldoor29: locked until the cook unlocks it (NPC419.scr :Main)
    if MM9.hasKey(5005) == 1 then evt.SetDoorState(DOORS.Celldoor29, DoorAction.Trigger) else evt.StatusText("The door is locked.") end
end

-- His brother Antoni (NPC427.scr :OnRude, :OnVanish): freed (key 369), the reward once (key 370, 4000 experience), then he is gone (MM9: runs to AntoniMarker, vanishes).
handlers[51044] = function()
    if MM9.hasKey(369) == 0 then return end
    if MM9.hasKey(370) == 0 then
        MM9.giveKey(370)
        MM9.giveExperience(4000)
        MM9.playSound("sounds/events/quest.wav")
    end
    MM9.removeActor(59)
end

-- Ivsar Forktooth (NPC90.scr :Onrude, :FollowPlayer): key 194 is taken, and unless he is home (key 21) walking out with him is the alarm. MM9 has him follow;
-- here, sent by Bjarni (key 17), he goes ahead ("If we get separated I'll meet you outside").
handlers[50068] = function()
    if MM9.hasKey(194) == 1 and MM9.hasKey(242) == 0 then MM9.openRude(90) return end
    MM9.takeKey(194)
    if MM9.hasKey(21) == 1 then return end
    alarm()
    if MM9.hasKey(17) == 1 then MM9.removeActor(41) end
end

-- The prisoners (DrangheimPrisoner.scr :OnPlayerRescue): a party without the pass gets 500 experience for each once; dialogue 431.
handlers[54067] = function()   -- InterrPrisoner0
    if MM9.hasKey(5007) == 0 and var("RescuedInterrPrisoner0") == 0 then
        set("RescuedInterrPrisoner0", 1)
        MM9.giveExperience(500)
    end
    MM9.openRude(431)
end
handlers[54068] = function()   -- InterrPrisoner1
    if MM9.hasKey(5007) == 0 and var("RescuedInterrPrisoner1") == 0 then
        set("RescuedInterrPrisoner1", 1)
        MM9.giveExperience(500)
    end
    MM9.openRude(431)
end
handlers[54069] = function()   -- InterrPrisoner2
    if MM9.hasKey(5007) == 0 and var("RescuedInterrPrisoner2") == 0 then
        set("RescuedInterrPrisoner2", 1)
        MM9.giveExperience(500)
    end
    MM9.openRude(431)
end

-- The cell levers (the lever objects' OpenTrigger/CloseTrigger): a lever unlocks and opens its cell, back shuts and locks it.
handlers[230] = function() evt.StatusText("The door is locked.") end
handlers[200] = function() evt.SetDoorState(DOORS.lever0, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor1, DoorAction.Trigger) end
handlers[201] = function() evt.SetDoorState(DOORS.lever1, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor2, DoorAction.Trigger) end
handlers[202] = function() evt.SetDoorState(DOORS.lever2, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor3, DoorAction.Trigger) end
handlers[203] = function() evt.SetDoorState(DOORS.lever3, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor4, DoorAction.Trigger) end
handlers[204] = function() evt.SetDoorState(DOORS.lever4, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor5, DoorAction.Trigger) end
handlers[205] = function() evt.SetDoorState(DOORS.lever5, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor6, DoorAction.Trigger) end
handlers[206] = function() evt.SetDoorState(DOORS.lever6, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor8, DoorAction.Trigger) end
handlers[207] = function() evt.SetDoorState(DOORS.lever7, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor9, DoorAction.Trigger) end
handlers[208] = function() evt.SetDoorState(DOORS.lever8, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor11, DoorAction.Trigger) end
handlers[209] = function() evt.SetDoorState(DOORS.lever9, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor12, DoorAction.Trigger) end
handlers[210] = function() evt.SetDoorState(DOORS.lever10, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor10, DoorAction.Trigger) end
handlers[211] = function() evt.SetDoorState(DOORS.lever11, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor7, DoorAction.Trigger) end
handlers[212] = function() evt.SetDoorState(DOORS.lever12, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor17, DoorAction.Trigger) end
handlers[213] = function() evt.SetDoorState(DOORS.lever15, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor13, DoorAction.Trigger) end
handlers[214] = function() evt.SetDoorState(DOORS.lever17, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor18, DoorAction.Trigger) end
handlers[215] = function() evt.SetDoorState(DOORS.lever24, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor25, DoorAction.Trigger) end
handlers[216] = function() evt.SetDoorState(DOORS.lever25, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor26, DoorAction.Trigger) end
handlers[217] = function() evt.SetDoorState(DOORS.lever26, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor27, DoorAction.Trigger) end
handlers[218] = function() evt.SetDoorState(DOORS.lever27, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor28, DoorAction.Trigger) end
handlers[219] = function() evt.SetDoorState(DOORS.lever28, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor30, DoorAction.Trigger) end
handlers[220] = function() evt.SetDoorState(DOORS.blever0, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor14, DoorAction.Trigger) end
handlers[221] = function() evt.SetDoorState(DOORS.blever1, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor16, DoorAction.Trigger) end
handlers[222] = function() evt.SetDoorState(DOORS.blever2, DoorAction.Trigger) evt.SetDoorState(DOORS.Celldoor15, DoorAction.Trigger) end

-- The well's lid (Lid1, LidWheel1): a click swings it over the shaft and turns its wheel (their triggers).
handlers[240] = function() evt.SetDoorState(DOORS.Lid1, DoorAction.Trigger); evt.SetDoorState(DOORS.LidWheel1, DoorAction.Trigger) end
handlers[241] = function() evt.SetDoorState(DOORS.RotatingDoor3, DoorAction.Trigger) end   -- over Ladder0

-- The smith (DrangheimSmith.scr :AnvilLoop, :PlayRandomSound, :CoolWeapon, :ReturnWeapon; the grate's Open/CloseTrigger turn him off and on):
-- his round is his marker path (the scene); he hammers at the anvil, a blow's clang every 3 s while he is there
-- and the grate is shut. Off (:TurnOff) he stops where he is.
local SMITH, ANVIL = 60, {-371, -2034, -410}
local function smithAtWork() evt.SetActorImmobile(SMITH, var("SmithOff") == 1) end
handlers[232] = function()
    evt.SetDoorState(DOORS.Door1, DoorAction.Trigger)
    set("SmithOff", 1 - var("SmithOff"))
    smithAtWork()
end
local function smithAtAnvil()
    local x, y = evt.GetMapActorPosition(SMITH)
    return x ~= nil and (x - ANVIL[1]) ^ 2 + (y - ANVIL[2]) ^ 2 < 160 ^ 2
end
handlers[261] = function()
    if var("SmithOff") == 0 and evt.IsMapActorWithinPartyDistance(SMITH, 1400) and smithAtAnvil()
        and not evt.CheckMonstersKilled(ActorKillCheck.Group, 5, 0, false) then
        evt.PlaySoundName("events/metalmetal0" .. evt.RandomBetween(1, 5, 1) .. ".wav", -307, -2028, -399)
    end
end
-- His tool in his right hand (:AttachHammer, :AttachSword): the sword once he leaves the anvil (:CoolWeapon),
-- the hammer again at the weapon rack (:OnReturnedWeapon). Polled every 0.5 s.
local RACK = {-1292, -2150, -410}
local SMITH_TOOLS = {[0] = "worlds/mm9/models/mm9_item_hammer.glb", [1] = "worlds/mm9/models/mm9_item_kirasword.glb"}
handlers[263] = function()
    evt.StartTimer(263, seconds(0.5))
    if evt.CheckMonstersKilled(ActorKillCheck.Group, 5, 0, false) then return end
    local x, y = evt.GetMapActorPosition(SMITH)
    if x == nil then return end
    local atAnvil, sword = smithAtAnvil(), var("SmithSword")
    local want = sword
    if sword == 0 and var("SmithAtAnvil") == 1 and not atAnvil then want = 1 end
    if sword == 1 and (x - RACK[1]) ^ 2 + (y - RACK[2]) ^ 2 < 160 ^ 2 then want = 0 end
    set("SmithAtAnvil", atAnvil and 1 or 0)
    if want == sword then return end
    set("SmithSword", want)
    evt.DetachActorItem(SMITH, "Socket_RHand1")
    evt.AttachActorItem(SMITH, SMITH_TOOLS[want], "Socket_RHand1")
end

-- The interrogation (DrangheimInterrogator.scr; either TriggerBeatings pad, once). For each of the three
-- prisoners: the interrogator walks to his cell's marker; the warden's lever opens the cell (aware); the
-- interrogator calls him out (fidget2), he comes out and cowers; the interrogator signals (aware) and the cell
-- shuts; the prisoner follows him along MarkerBeating<k+1>-9; the doorman opens the interrogation room at 8 and
-- shuts it at 9; the beating sounds; the door opens and they walk back, the door shutting behind them; the
-- cell opens, the interrogator sends him in (fidget1), he walks to his CellMarker and the cell shuts. It stops
-- when the warden, the doorman or the interrogator is dead or the alarm is up (MM9: OnObjectLinkBroken,
-- hostility). A walk not done in 25 s (or under way when the game was saved) ends at its point at once.
local MARKERS = {[0] = {942, -4342, -2232}, [1] = {328, -4342, -2232}, [2] = {328, -4342, -2232}, [3] = {164, -4342, -2232}, [4] = {-655, -4342, -2232}, [5] = {-1556, -4342, -2232}, [6] = {-1884, -4669, -2232}, [7] = {-2130, -4997, -2232}, [8] = {-2130, -5571, -2232}, [9] = {-3031, -5489, -2232}}
local BEATEN = {{prisoner = 64, lever = DOORS.blever0, cell = DOORS.Celldoor14, pick = {951, -4452, -2232}, home = {983, -4997, -2232}}, {prisoner = 65, lever = DOORS.blever2, cell = DOORS.Celldoor15, pick = {320, -4232, -2232}, home = {328, -3686, -2232}}, {prisoner = 66, lever = DOORS.blever1, cell = DOORS.Celldoor16, pick = {319, -4452, -2232}, home = {328, -4997, -2232}}}
local INTERR, WARDEN, IN_ROOM = 63, 62, {-3200, -5489, -2232}
local CELL_WAIT, DOOR_WAIT, BEAT_SECONDS, LEG_TIMEOUT = 3, 4, 8, 25
local function beatingOff() return MM9.hasKey(5006) == 1 or evt.CheckMonstersKilled(ActorKillCheck.Group, 6, 0, false) or evt.CheckMonstersKilled(ActorKillCheck.Group, 7, 0, false) or evt.CheckMonstersKilled(ActorKillCheck.Group, 8, 0, false) end
local function beatStep(delay) arm(260, delay) end
local function openGroupInterr() open("RightDoor0"); open("LeftDoor0") end
local function closeGroupInterr() close("RightDoor0"); close("LeftDoor0") end
local function cellLever(b, opening)   -- DrangheimWarden.scr :OpenCell / :CloseCell
    evt.PlayActorClip(WARDEN, "aware")
    local action = opening and DoorAction.Open or DoorAction.Close
    evt.SetDoorState(b.lever, action); evt.SetDoorState(b.cell, action)
end
local function route(from, to)   -- the markers between, one of two that stand on the same spot (1, 2) dropped
    local out, step = {}, from <= to and 1 or -1
    for i = from, to, step do
        local m, last = MARKERS[i], out[#out]
        if last == nil or m[1] ~= last[1] or m[2] ~= last[2] then out[#out + 1] = m end
    end
    return out
end
local function plan(k)   -- prisoner k (0-2): {run, wait} or a walk {i = point, p = point}
    local b, steps = BEATEN[k + 1], {}
    local function add(step) steps[#steps + 1] = step end
    add({i = MARKERS[k]})
    add({run = function() cellLever(b, true) end, wait = CELL_WAIT})
    add({run = function() evt.PlayActorClip(INTERR, "fidget2") end, wait = 2})   -- ANIM_COMEOUT
    add({p = b.pick})
    add({run = function() evt.PlayActorClip(b.prisoner, "cower") end, wait = 1.2})
    add({run = function() evt.PlayActorClip(INTERR, "aware"); cellLever(b, false) end, wait = CELL_WAIT})
    local out = route(k, 8)
    for n = 2, #out do add({i = out[n], p = out[n - 1]}) end
    add({run = openGroupInterr, wait = DOOR_WAIT})
    add({i = MARKERS[9], p = IN_ROOM})
    add({run = closeGroupInterr, wait = DOOR_WAIT})
    add({run = function() evt.PlaySoundName("events/beatdownmix8bit.wav", -3031, -5489, -2232) end, wait = BEAT_SECONDS})
    add({run = openGroupInterr, wait = DOOR_WAIT})
    local back = route(9, k)
    for n = 2, #back do
        add({i = back[n], p = back[n - 1]})
        if n == 3 then add({run = closeGroupInterr, wait = 0.5}) end   -- both past the door (8)
    end
    add({run = function() cellLever(b, true) end, wait = CELL_WAIT})
    add({run = function() evt.PlayActorClip(INTERR, "fidget") end, wait = 2})   -- ANIM_GOBACK
    add({p = b.home})
    add({run = function() cellLever(b, false) end, wait = 4})
    return steps
end
local function walker(step) return step.i and INTERR or nil, step.p and BEATEN[var("BeatPrisoner")].prisoner or nil end
local function runBeat()   -- the next step; each clip has ended by then (its step's wait): let them go
    local k = var("BeatPrisoner")
    for _, a in ipairs({INTERR, WARDEN, BEATEN[k].prisoner}) do evt.ClearActorPresentation(a) end
    if beatingOff() then set("Beatings", 2) return end
    local step = plan(k - 1)[var("BeatStep")]
    if step == nil then   -- this prisoner is back: the next
        if k >= #BEATEN then set("Beatings", 2) return end
        set("BeatPrisoner", k + 1); set("BeatStep", 1)
        return runBeat()
    end
    set("BeatWalk", var("BeatStep"))
    set("BeatStep", var("BeatStep") + 1)
    if step.run then step.run(); beatStep(step.wait) return end
    local i, p = walker(step)
    set("WaitI", i and 1 or 0); set("WaitP", p and 1 or 0)
    if i then evt.ClearActorPresentation(i); evt.MoveActorTo(i, step.i[1], step.i[2], step.i[3], 254) end
    if p then evt.ClearActorPresentation(p); evt.MoveActorTo(p, step.p[1], step.p[2], step.p[3], 255) end
    beatStep(LEG_TIMEOUT)
end
local function startBeatings()
    if var("Beatings") ~= 0 then return end
    set("Beatings", 1)
    set("BeatPrisoner", 1)
    set("BeatStep", 1)
    beatStep(1)
end
handlers[250] = function() startBeatings() end
handlers[251] = function() startBeatings() end
handlers[233] = function() evt.StatusText("The door is locked.") end
handlers[260] = function()
    if not fired(260) or var("Beatings") ~= 1 then return end
    if var("WaitI") == 1 or var("WaitP") == 1 then   -- the walk took too long, or a load ended it: there
        local step = plan(var("BeatPrisoner") - 1)[var("BeatWalk")]
        local i, p = walker(step)
        if i and var("WaitI") == 1 then evt.StopActorMove(i); evt.SetMapActorPosition(i, step.i[1], step.i[2], step.i[3]) end
        if p and var("WaitP") == 1 then evt.StopActorMove(p); evt.SetMapActorPosition(p, step.p[1], step.p[2], step.p[3]) end
        set("WaitI", 0); set("WaitP", 0)
    end
    runBeat()
end
local function arrived(flag)
    if var("Beatings") ~= 1 or var(flag) == 0 then return end
    set(flag, 0)
    if var("WaitI") == 1 or var("WaitP") == 1 then return end
    evt.StopTimer(260); set("Armed260", 0)
    runBeat()
end
handlers[254] = function() arrived("WaitI") end
handlers[255] = function() arrived("WaitP") end

-- The barracks guards (GuardToNegate.scr): enemies of the Nagate; the party at DDoor5 sets them off (MM9: they
-- run to the barracks; here they call out and fight what they meet).
handlers[252] = function()
    if var("BarracksCalled") == 1 then return end
    set("BarracksCalled", 1)
    -- the call is BarracksGuard2's (GuardToNegate.scr :FaceEachOther): dead, it takes no Hello
    if not MM9.receives("drangheimprison", "BarracksGuard2", "Hello", 71) then return end
    evt.PlaySoundName("vo/irequireassistance.wav", 0, 0, 0)
end
-- The PerceptionBrushes: the red glow on the secret doors shows to a party with Perception 12 or better
-- (MM9's PerceptionValue; the BLV holds them visible so that they are lightmapped). On load and every 3 s.
local HINTS = {300, 301, 302, 303, 304, 305}
local function updateHints()
    local want = evt.CheckSkill(29, 0, 12) and 2 or 1
    if var("PerceptionHints") == want then return end
    set("PerceptionHints", want)
    for _, cog in ipairs(HINTS) do evt.SetFacetBit(cog, FacetBits.Invisible, want == 1) end
end
handlers[262] = updateHints
handlers[1] = function()   -- map load
    applyHostility()
    -- saves made before 2026-11-08 hold every guard row's AddEnemy Nagate: cleared (the group rows win)
    evt.SetMonsterRelation(9111, 9081, 0); evt.SetMonsterRelation(9081, 9111, 0)
    evt.SetMonsterRelation(9111, 9082, 0); evt.SetMonsterRelation(9082, 9111, 0)
    evt.SetMonsterRelation(9111, 9083, 0); evt.SetMonsterRelation(9083, 9111, 0)
    evt.SetMonsterRelation(9112, 9081, 0); evt.SetMonsterRelation(9081, 9112, 0)
    evt.SetMonsterRelation(9112, 9082, 0); evt.SetMonsterRelation(9082, 9112, 0)
    evt.SetMonsterRelation(9112, 9083, 0); evt.SetMonsterRelation(9083, 9112, 0)
    evt.SetMonsterRelation(9113, 9081, 0); evt.SetMonsterRelation(9081, 9113, 0)
    evt.SetMonsterRelation(9113, 9082, 0); evt.SetMonsterRelation(9082, 9113, 0)
    evt.SetMonsterRelation(9113, 9083, 0); evt.SetMonsterRelation(9083, 9113, 0)
    evt.SetMonsterRelation({group = 4}, 9081, 2); evt.SetMonsterRelation(9081, {group = 4}, 2)
    evt.SetMonsterRelation({group = 4}, 9082, 2); evt.SetMonsterRelation(9082, {group = 4}, 2)
    evt.SetMonsterRelation({group = 4}, 9083, 2); evt.SetMonsterRelation(9083, {group = 4}, 2)
    if MM9.hasKey(242) == 1 or MM9.hasKey(17) == 1 then MM9.removeActor(41) end
    if MM9.hasKey(370) == 1 then MM9.removeActor(59) end
    if var("AsideGuard0") == 1 then evt.SetMapActorPosition(52, -1751, -6728, -2232) end
    if var("AsideGuard1") == 1 then evt.SetMapActorPosition(53, -2591, -6717, -2232) end
    smithAtWork()
    evt.StartTimer(263, seconds(0.5))
    rollSleep("Guard0", 1)
    rollSleep("Guard1", 2)
    rollSleep("Guard2", 3)
    updateHints()
end
-- MM9's greeting voices (dungeon/voices.py): a click on these people plays their GreetingSound or the
-- voice their script's :OnUse plays, then opens their dialogue (or runs the map's own click).
handlers[53068] = function() MM9.playSound("voices/npc/npc_090.wav"); MM9.openRude(90) end   -- Ivsar

-- MM9's BonePile objects (dungeon/objects.py): a click searches the pile (evt.SearchLootProp: its
-- TreasureLevel loot once, DiseaseChance; the pile stays).
handlers[30495] = function() evt.SearchLootProp("mm9:drangheimprison:object:495") end   -- Bonepile1
handlers[30496] = function() evt.SearchLootProp("mm9:drangheimprison:object:496") end   -- Bonepile0
handlers[30503] = function() evt.SearchLootProp("mm9:drangheimprison:object:503") end   -- Trashpile1
handlers[30504] = function() evt.SearchLootProp("mm9:drangheimprison:object:504") end   -- Trashpile2
handlers[30505] = function() evt.SearchLootProp("mm9:drangheimprison:object:505") end   -- Trashpile3
handlers[30506] = function() evt.SearchLootProp("mm9:drangheimprison:object:506") end   -- Trashpile4
handlers[30507] = function() evt.SearchLootProp("mm9:drangheimprison:object:507") end   -- Trashpile5
handlers[30508] = function() evt.SearchLootProp("mm9:drangheimprison:object:508") end   -- Trashpile6
handlers[30509] = function() evt.SearchLootProp("mm9:drangheimprison:object:509") end   -- Trashpile7
handlers[30510] = function() evt.SearchLootProp("mm9:drangheimprison:object:510") end   -- Trashpile8
handlers[30511] = function() evt.SearchLootProp("mm9:drangheimprison:object:511") end   -- Trashpile9
handlers[30512] = function() evt.SearchLootProp("mm9:drangheimprison:object:512") end   -- Trashpile10
handlers[30513] = function() evt.SearchLootProp("mm9:drangheimprison:object:513") end   -- Trashpile0


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
RegisterEvent(130, "Door", handlers[130], "Door")
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(43, "Chest", handlers[43], "Chest")
RegisterEvent(44, "Chest", handlers[44], "Chest")
RegisterEvent(45, "Chest", handlers[45], "Chest")
RegisterEvent(46, "Chest", handlers[46], "Chest")
RegisterEvent(54033, "Guard0", handlers[54033])
RegisterEvent(51033, "Guard0", handlers[51033])
RegisterEvent(54034, "Guard1", handlers[54034])
RegisterEvent(51034, "Guard1", handlers[51034])
RegisterEvent(54035, "Guard2", handlers[54035])
RegisterEvent(51035, "Guard2", handlers[51035])
RegisterEvent(51039, "Aymril Banito", handlers[51039])
RegisterEvent(231, "Cell door", handlers[231], "Door")
RegisterEvent(51044, "Antoni Banito", handlers[51044])
RegisterEvent(50068, "Ivsar Forktooth", handlers[50068])
RegisterEvent(54067, "InterrPrisoner0", handlers[54067])
RegisterEvent(54068, "InterrPrisoner1", handlers[54068])
RegisterEvent(54069, "InterrPrisoner2", handlers[54069])
RegisterEvent(230, "Cell door", handlers[230], "Door")
RegisterEvent(200, "Lever", handlers[200], "Lever")
RegisterEvent(201, "Lever", handlers[201], "Lever")
RegisterEvent(202, "Lever", handlers[202], "Lever")
RegisterEvent(203, "Lever", handlers[203], "Lever")
RegisterEvent(204, "Lever", handlers[204], "Lever")
RegisterEvent(205, "Lever", handlers[205], "Lever")
RegisterEvent(206, "Lever", handlers[206], "Lever")
RegisterEvent(207, "Lever", handlers[207], "Lever")
RegisterEvent(208, "Lever", handlers[208], "Lever")
RegisterEvent(209, "Lever", handlers[209], "Lever")
RegisterEvent(210, "Lever", handlers[210], "Lever")
RegisterEvent(211, "Lever", handlers[211], "Lever")
RegisterEvent(212, "Lever", handlers[212], "Lever")
RegisterEvent(213, "Lever", handlers[213], "Lever")
RegisterEvent(214, "Lever", handlers[214], "Lever")
RegisterEvent(215, "Lever", handlers[215], "Lever")
RegisterEvent(216, "Lever", handlers[216], "Lever")
RegisterEvent(217, "Lever", handlers[217], "Lever")
RegisterEvent(218, "Lever", handlers[218], "Lever")
RegisterEvent(219, "Lever", handlers[219], "Lever")
RegisterEvent(220, "Lever", handlers[220], "Lever")
RegisterEvent(221, "Lever", handlers[221], "Lever")
RegisterEvent(222, "Lever", handlers[222], "Lever")
RegisterEvent(232, "Grate", handlers[232], "Grate")
RegisterMapTimerEvent(261, seconds(3), handlers[261], "Smith", "", seconds(3))
RegisterMapTimerEvent(263, seconds(3), handlers[263], "Smith's tools", "", seconds(3))
RegisterEvent(240, "Well lid", handlers[240], "Lid")
RegisterEvent(241, "Hatch", handlers[241], "Hatch")
RegisterEvent(250, "TriggerBeatings0", handlers[250])
RegisterEvent(251, "TriggerBeatings1", handlers[251])
RegisterEvent(233, "Door", handlers[233], "Door")
RegisterMapTimerEvent(260, seconds(3), handlers[260], "Interrogation", "", seconds(3))
RegisterEvent(254, "Interrogator arrives", handlers[254])
RegisterEvent(255, "Prisoner arrives", handlers[255])
RegisterEvent(252, "NagGuardTrigger0", handlers[252])
RegisterMapTimerEvent(262, seconds(3), handlers[262], "Perception hints", "", seconds(3))
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(53068, "Ivsar Forktooth", handlers[53068])
RegisterEvent(30495, "Bone Pile", handlers[30495], "Bone Pile")
RegisterEvent(30496, "Bone Pile", handlers[30496], "Bone Pile")
RegisterEvent(30503, "Trash Pile", handlers[30503], "Trash Pile")
RegisterEvent(30504, "Trash Pile", handlers[30504], "Trash Pile")
RegisterEvent(30505, "Trash Pile", handlers[30505], "Trash Pile")
RegisterEvent(30506, "Trash Pile", handlers[30506], "Trash Pile")
RegisterEvent(30507, "Trash Pile", handlers[30507], "Trash Pile")
RegisterEvent(30508, "Trash Pile", handlers[30508], "Trash Pile")
RegisterEvent(30509, "Trash Pile", handlers[30509], "Trash Pile")
RegisterEvent(30510, "Trash Pile", handlers[30510], "Trash Pile")
RegisterEvent(30511, "Trash Pile", handlers[30511], "Trash Pile")
RegisterEvent(30512, "Trash Pile", handlers[30512], "Trash Pile")
RegisterEvent(30513, "Trash Pile", handlers[30513], "Trash Pile")
RegisterMonsterDamageHook(96, "Guards hurt", handlers[96])
RegisterMonsterKilledHook(97, "Guards killed", handlers[97])
