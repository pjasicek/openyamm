-- Temple of Honk, MM9 rework (level_generation/projects/mm9r_templeofhonk/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {DoubleDoorL1 = 1, DoubleDoorL10 = 3, DoubleDoorL11 = 5, DoubleDoorL12 = 7, DoubleDoorL13 = 9, DoubleDoorL14 = 11, DoubleDoorL2 = 13, DoubleDoorL3 = 15, DoubleDoorL4 = 17, DoubleDoorL5 = 19, DoubleDoorL6 = 21, DoubleDoorL7 = 23, DoubleDoorL9 = 25, DoubleDoorR1 = 2, DoubleDoorR10 = 4, DoubleDoorR11 = 6, DoubleDoorR12 = 8, DoubleDoorR13 = 10, DoubleDoorR14 = 12, DoubleDoorR2 = 14, DoubleDoorR3 = 16, DoubleDoorR4 = 18, DoubleDoorR5 = 20, DoubleDoorR6 = 22, DoubleDoorR7 = 24, DoubleDoorR9 = 26, HButton = 27, HCornerStone = 28, KButton = 29, KCornerStone = 30, NButton = 31, NCornerStone = 32, OButton = 33, OCornerStone = 34, SecretDoor = 35}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {902}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}, [44] = {3}, [45] = {4}}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(1, DoorAction.Trigger) evt.SetDoorState(2, DoorAction.Trigger) end   -- DoubleDoor1
handlers[102] = function() evt.SetDoorState(3, DoorAction.Trigger) evt.SetDoorState(4, DoorAction.Trigger) end   -- DoubleDoor10
handlers[103] = function() evt.SetDoorState(5, DoorAction.Trigger) evt.SetDoorState(6, DoorAction.Trigger) end   -- DoubleDoor11
handlers[104] = function() evt.SetDoorState(7, DoorAction.Trigger) evt.SetDoorState(8, DoorAction.Trigger) end   -- DoubleDoor12
handlers[105] = function() evt.SetDoorState(11, DoorAction.Trigger) evt.SetDoorState(12, DoorAction.Trigger) end   -- DoubleDoor14
handlers[106] = function() evt.SetDoorState(13, DoorAction.Trigger) evt.SetDoorState(14, DoorAction.Trigger) end   -- DoubleDoor2
handlers[107] = function() evt.SetDoorState(15, DoorAction.Trigger) evt.SetDoorState(16, DoorAction.Trigger) end   -- DoubleDoor3
handlers[108] = function() evt.SetDoorState(17, DoorAction.Trigger) evt.SetDoorState(18, DoorAction.Trigger) end   -- DoubleDoor4
handlers[109] = function() evt.SetDoorState(19, DoorAction.Trigger) evt.SetDoorState(20, DoorAction.Trigger) end   -- DoubleDoor5
handlers[110] = function() evt.SetDoorState(21, DoorAction.Trigger) evt.SetDoorState(22, DoorAction.Trigger) end   -- DoubleDoor6
handlers[111] = function() evt.SetDoorState(23, DoorAction.Trigger) evt.SetDoorState(24, DoorAction.Trigger) end   -- DoubleDoor7
handlers[112] = function() evt.SetDoorState(25, DoorAction.Trigger) evt.SetDoorState(26, DoorAction.Trigger) end   -- DoubleDoor9

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- CollectionChest
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest3
handlers[43] = function() evt.OpenChest(2) end   -- TreasureChest2
handlers[44] = function() evt.OpenChest(3) end   -- TreasureChest0
handlers[45] = function() evt.OpenChest(4) end   -- TreasureChest1

-- The Honks (HonkHostility.inc): the party's friends until it hurts or kills one or steals from them.
local HONKS = {[9186] = true, [9187] = true, [9216] = true, [9293] = true}
local function honksHostile()
    if var("HonksHostile") == 1 then return end
    set("HonksHostile", 1)
    evt.SetMonGroupBit(1, MonsterBits.Hostile, true)
end
handlers[96] = function(context)
    if HONKS[context.monsterId] then honksHostile() end
end
handlers[97] = function(context)
    if HONKS[context.monsterId] then honksHostile() end
end

-- DoubleDoor13 (Honk.scr): unlocked for a party on the Golden Honk quest (key 343).
handlers[130] = function()
    if MM9.hasKey(343) == 0 then evt.StatusText("The door is locked.") return end
    evt.SetDoorState(DOORS.DoubleDoorL13, DoorAction.Trigger)
    evt.SetDoorState(DOORS.DoubleDoorR13, DoorAction.Trigger)
end

-- The accountant's key (HonkKey.scr): a world item (445); its pickup gives key 7000, which unlocks the HONK buttons. Stolen
-- under the accountant's eyes (within 200 LT) it turns the Honks hostile.
handlers[75] = function()
    if MM9.hasKey(7000) == 1 then return end
    MM9.giveKey(7000)
    if not evt.CheckMonstersKilled(ActorKillCheck.ActorIdOe, 14, 0, false) then
        local x, y, z = evt.GetMapActorPosition(14)
        if x ~= nil and math.sqrt((x - 819) ^ 2 + (y - 6758) ^ 2) <= 512 then
            set("KeyStolenSeen", 1)
            honksHostile()
        end
    end
end

-- The HONK buttons (HonkSecretDoor.scr): locked until the party has the accountant's key. Each raises its
-- corner stone out of the pool (MM9 48 LT at 15 LT/s); the fourth stone decides: H, O, N, K opens the secret
-- door (it shuts after 10 s, as MM9's CloseWaitTime), any other order sinks the stones and buttons again.
-- Everything resets 20 s after the door opens.
local ORDER = "HONK"
local function resetButtons()
    for i = 1, 4 do
        local letter = string.sub(ORDER, i, i)
        close(letter .. "CornerStone"); close(letter .. "Button"); set("Pressed" .. letter, 0)
    end
    set("HonkCount", 0); set("HonkWrong", 0)
end
local function press(letter, position)
    if MM9.hasKey(7000) == 0 then evt.StatusText("The button will not move.") return end
    if var("Pressed" .. letter) == 1 or var("Pending") ~= 0 then return end
    set("Pressed" .. letter, 1)
    open(letter .. "Button"); open(letter .. "CornerStone")
    local count = var("HonkCount") + 1
    set("HonkCount", count)
    if count ~= position then set("HonkWrong", 1) end
    if count == 4 then
        if var("HonkWrong") == 0 then set("Pending", 1) else set("Pending", 2) end
        evt.StartTimer(150, seconds(4))
    end
end
handlers[150] = function()   -- the fourth stone has risen
    evt.StopTimer(150)
    local pending = var("Pending")
    if pending == 1 then
        set("Pending", 3); set("VaultOpened", var("VaultOpened") + 1)
        open("SecretDoor")
        evt.StartTimer(152, seconds(10)); evt.StartTimer(153, seconds(20))
    elseif pending == 2 then
        set("Pending", 0); resetButtons()
    end
end
handlers[152] = function() evt.StopTimer(152); if var("Pending") == 3 then close("SecretDoor") end end
handlers[153] = function() evt.StopTimer(153); if var("Pending") == 3 then set("Pending", 0); resetButtons() end end
-- UnlockDoorTrig: from inside the treasury the secret door opens again (MM9 Trigger -> secretdoor open).
handlers[70] = function()
    open("SecretDoor")
    evt.StartTimer(151, seconds(10))
end
handlers[151] = function() evt.StopTimer(151); if var("Pending") ~= 3 then close("SecretDoor") end end
handlers[61] = function() press("H", 1) end   -- HButton
handlers[62] = function() press("O", 2) end   -- OButton
handlers[63] = function() press("N", 3) end   -- NButton
handlers[64] = function() press("K", 4) end   -- KButton

-- The Golden Honk (Honk.scr): a world item (369); its pickup gives key 344 on the quest (key 343), 345 without; the Honks turn hostile.
handlers[76] = function()
    local taken = MM9.hasKey(343) == 1 and 344 or 345
    if MM9.hasKey(taken) == 1 then return end
    MM9.giveKey(taken)
    honksHostile()
end

-- The Honk ceremony (HonkLeader.scr, HonkFollower.scr): the bell at 6:15 and 18:15 and the followers walk
-- their CeremonyMarker lists to the pulpit (routine go), face it and worship (worship); from the first
-- arrival the leader paces and preaches (preach, a thunder at him). At 7:15 and 19:15 (MM9 6:45, 18:45: the
-- walk takes longer here) the followers walk back (home) and wander again; the leader loops prop-stand.
-- HonkAccountant.scr: at 7:00 and 19:00 the accountant walks PathMarker0-13 and back (trip). Routines are
-- runtime only: this check sets them again.
local CEREMONIES = {{375, 435}, {1095, 1155}}
local LEADER = 3
local FOLLOWERS = {{4, {492, 3113}, {4915, 3113}}, {5, {492, 3113}, {4915, 3113}}, {6, {492, 3113}, {4915, 3113}}, {7, {492, 3113}, {4915, 3113}}, {8, {-655, 3604}, {4915, 3523}}, {9, {-655, 3604}, {4915, 3523}}, {10, {-655, 3604}, {4915, 3523}}, {11, {-655, 3604}, {4915, 3523}}, {12, {-655, 3604}, {4915, 3523}}, {13, {-655, 3604}, {4915, 3523}}}   -- actor, first and last marker
local ACCOUNTANT, ACCOUNTANT_HOME = 14, {1229, 6636}
local TRIPS = {420, 1140}
local routine = {}
local function setRoutine(actor, name)
    routine[actor] = name
    evt.SetActorRoutine(actor, name)   -- the same name again keeps its step
end
local function near(actor, p)
    local x, y = evt.GetMapActorPosition(actor)
    return x ~= nil and (x - p[1]) ^ 2 + (y - p[2]) ^ 2 <= 400 ^ 2
end
local function leaderSound(name)
    local x, y, z = evt.GetMapActorPosition(LEADER)
    if x ~= nil then evt.PlaySoundName(name, math.floor(x), math.floor(y), math.floor(z)) end
end
local function followers(ceremony)   -- whether one has arrived (FollowerReady)
    local arrived = false
    for _, f in ipairs(FOLLOWERS) do
        local actor, r = f[1], routine[f[1]]
        if ceremony then
            if r == "worship" or near(actor, f[3]) then
                setRoutine(actor, "worship")   -- at the pulpit (or loaded there)
            else
                setRoutine(actor, "go")
            end
            arrived = arrived or routine[actor] == "worship"
        elseif r == "go" or r == "worship" or (r == "home" and not near(actor, f[2])) then
            setRoutine(actor, "home")   -- EndCeremony: back along the list
        else
            setRoutine(actor, "")   -- wander
        end
    end
    return arrived
end
handlers[154] = function()
    if var("HonksHostile") == 1 then
        setRoutine(LEADER, ""); setRoutine(ACCOUNTANT, "")
        for _, f in ipairs(FOLLOWERS) do setRoutine(f[1], "") end
        return
    end
    local now = math.floor(evt.CurrentGameMinutes())
    local minute, day = now % 1440, math.floor(now / 1440)
    local ceremony = false
    for k, span in ipairs(CEREMONIES) do
        if minute >= span[1] and minute < span[2] then
            ceremony = true
            local id = day * 2 + k
            if var("CeremonyRung") ~= id then
                set("CeremonyRung", id); set("Ceremonies", var("Ceremonies") + 1)
                leaderSound("events/churchbellring.wav")   -- RingGong
            end
        end
    end
    if followers(ceremony) then
        setRoutine(LEADER, "preach")
        if var("CeremonyStep") % 2 == 0 then
            leaderSound("ambient/thunder/thunder0" .. MM9.random(1, 4) .. ".wav")   -- RandomPreach
        end
        set("CeremonyStep", var("CeremonyStep") + 1)
    else
        setRoutine(LEADER, "")
    end
    local trip = false
    for k, start in ipairs(TRIPS) do
        if minute >= start and minute < start + 15 then
            trip = true
            if var("AccountantTrip") ~= day * 2 + k then
                set("AccountantTrip", day * 2 + k); setRoutine(ACCOUNTANT, "trip")
            end
        end
    end
    if routine[ACCOUNTANT] == "trip" and not trip and near(ACCOUNTANT, ACCOUNTANT_HOME) then
        setRoutine(ACCOUNTANT, "")   -- back at PathMarker0
    elseif routine[ACCOUNTANT] ~= nil then
        setRoutine(ACCOUNTANT, routine[ACCOUNTANT])
    end
end

-- MM9's PerceptionBrushes (dungeon/perception.py): the red glow shows to a party whose Perception reaches the
-- brush's PerceptionValue, checked on load and every 3 s; map Lua turns one off for good with
-- set("HintOff<cog>", 1) (MM9's Off message to the brush).
local HINTS = {[23591] = 8}
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
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(43, "Chest", handlers[43], "Chest")
RegisterEvent(44, "Chest", handlers[44], "Chest")
RegisterEvent(45, "Chest", handlers[45], "Chest")
RegisterEvent(130, "Door", handlers[130], "Door")
RegisterEvent(75, "Key", handlers[75])
RegisterEvent(61, "H button", handlers[61], "Button")
RegisterEvent(62, "O button", handlers[62], "Button")
RegisterEvent(63, "N button", handlers[63], "Button")
RegisterEvent(64, "K button", handlers[64], "Button")
RegisterMapTimerEvent(150, seconds(3), handlers[150], "HONK stones risen", "", seconds(3))
RegisterMapTimerEvent(152, seconds(3), handlers[152], "Secret door shuts", "", seconds(3))
RegisterMapTimerEvent(153, seconds(3), handlers[153], "HONK buttons reset", "", seconds(3))
RegisterMapTimerEvent(151, seconds(3), handlers[151], "Secret door shuts (inside)", "", seconds(3))
RegisterEvent(70, "UnlockDoorTrig", handlers[70])
RegisterEvent(76, "Golden Honk", handlers[76])
RegisterMapTimerEvent(154, seconds(3), handlers[154], "Honk ceremony", "", seconds(3))
RegisterMapTimerEvent(901, seconds(3), handlers[901], "Perception hints", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
RegisterMonsterDamageHook(96, "Honk hostility", handlers[96])
RegisterMonsterKilledHook(97, "Honk hostility", handlers[97])
