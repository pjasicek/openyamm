-- Dook's Castle, MM9 rework (level_generation/projects/mm9r_dookscastle/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {Tempbutton_INV = 1, doorslide = 16, double_door_left_01 = 2, double_door_left_02 = 4, double_door_left_03 = 6, double_door_left_04 = 8, double_door_left_05 = 10, double_door_left_06 = 12, double_door_left_07 = 14, double_door_right_01 = 3, double_door_right_02 = 5, double_door_right_03 = 7, double_door_right_04 = 9, double_door_right_05 = 11, double_door_right_06 = 13, double_door_right_07 = 15}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}, [44] = {3}, [45] = {4}, [46] = {5}, [47] = {6}}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(2, DoorAction.Trigger) evt.SetDoorState(3, DoorAction.Trigger) end   -- door01
handlers[102] = function() evt.SetDoorState(4, DoorAction.Trigger) evt.SetDoorState(5, DoorAction.Trigger) end   -- door02
handlers[103] = function() evt.SetDoorState(6, DoorAction.Trigger) evt.SetDoorState(7, DoorAction.Trigger) end   -- door03
handlers[104] = function() evt.SetDoorState(8, DoorAction.Trigger) evt.SetDoorState(9, DoorAction.Trigger) end   -- door04
handlers[105] = function() evt.SetDoorState(10, DoorAction.Trigger) evt.SetDoorState(11, DoorAction.Trigger) end   -- door05
handlers[106] = function() evt.SetDoorState(12, DoorAction.Trigger) evt.SetDoorState(13, DoorAction.Trigger) end   -- door06
handlers[107] = function() evt.SetDoorState(14, DoorAction.Trigger) evt.SetDoorState(15, DoorAction.Trigger) end   -- door07

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest1
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest2
handlers[43] = function() evt.OpenChest(2) end   -- TreasureChest3
handlers[44] = function() evt.OpenChest(3) end   -- TreasureChest4
handlers[45] = function() evt.OpenChest(4) end   -- TreasureChest5
handlers[46] = function() evt.OpenChest(5) end   -- TreasureChest0
handlers[47] = function() evt.OpenChest(6) end   -- TreasureChest6

-- The guards (DookGuardBasic.scr, DC_sargent.scr, DookSleepGaurd.scr, all #include DookHostility.inc): they
-- AddFriend Player while the ScriptObject DOOK_HOSTILITY stands; its removal (the secret door's
-- OpenTrigger, or TurnHostilityOn when the party hurts or kills a guard, with the alarm bell) makes every guard
-- AddEnemy Player. Map variable Hostile carries the removal.
local GUARD_MONSTERS = {[9103] = true, [9104] = true}
local SLEEPERS = {43, 44, 45, 46}
local function applyHostility()
    local hostile = var("Hostile") == 1
    evt.SetMonGroupBit(1, MonsterBits.Hostile, hostile)
    evt.SetMonGroupBit(3, MonsterBits.Hostile, hostile)
    if hostile then for _, index in ipairs(SLEEPERS) do evt.WakeActor(index) end end
end
local function hostility(bell)
    if var("Hostile") == 1 then return end
    set("Hostile", 1)
    if bell then evt.PlaySoundName("events/alarmbell.wav", 0, 0, 0) end
    applyHostility()
end
handlers[96] = function(context) if GUARD_MONSTERS[context.monsterId] then hostility(true) end end
handlers[97] = function(context) if GUARD_MONSTERS[context.monsterId] then hostility(true) end end

-- The shield over Tempbutton (RotatingDoor, OpenTriggers: doorslide open, Tempbutton lock): the secret door
-- slides open and stays (Sticky, no close wait); its OpenTrigger removes DOOK_HOSTILITY.
handlers[70] = function()
    if var("SecretOpen") == 1 then return end
    set("SecretOpen", 1)
    open("Tempbutton_INV")
    open("doorslide")
    evt.PlaySoundName("door/doorlatch02.wav", 0, 0, 0)
    evt.PlaySoundName("events/boulderroll.wav", 0, 0, 0)
    hostility(false)
end

-- SleepTrigger -> SleepCaptain StartUp (DC_sargent.scr): the sargent walks to SMkr0 (:StartUp), then to
-- HallwaySleeper0..3 in turn (:WakeGuards): at each he turns to it and wakes it (:WakeGuardUp, Trigger
-- WakeUp: it cowers, then stands watch), waits 3 s and goes on; then he walks to SMkr1 and stays (:dn).
-- MM9's PlayAnim aware there is not carried: his body (MM9's DookMilitia.abc too) has no such clip.
-- Map variable SleepWoken: 0 not started, k walking to sleeper k or waiting after it, 5 walking to SMkr1, 6 done.
-- A dead sargent takes no StartUp, and once dead it walks to no more sleepers (MM9.receives); the alarm
-- (DookHostility.inc AddEnemy) ends his round: he fights, and the alarm wakes every sleeper. Walks are not
-- saved: a load during the round, or a walk not done in 20 s, finishes it where it was going.
local CAPTAIN = 42
local ROUND = {44, 43, 46, 45}   -- HallwaySleeper0..3
local ROUND_STOPS = {{105, 5694, 411}, {-105, 5857, 411}, {105, 6421, 411}, {-105, 6533, 411}}   -- in front of each
local SMKR0, SMKR1 = {23, 5243, 411}, {82, 6922, 411}
local round = {walking = false, wait = 0, ticks = 0}
local function roundOver() return var("Hostile") == 1 or not MM9.actorAlive(CAPTAIN) end
local function sargentWalk(p, event)
    round.walking, round.ticks, round.event, round.point = true, 0, event, p
    evt.MoveActorTo(CAPTAIN, p[1], p[2], p[3], event)
    evt.StartTimer(200, seconds(1))
end
local function wakeGuards()   -- :WakeGuards
    local step = var("SleepWoken")
    if step <= #ROUND then sargentWalk(ROUND_STOPS[step], 211)
    else set("SleepWoken", #ROUND + 1); sargentWalk(SMKR1, 212) end
end
handlers[73] = function()
    if var("SleepWoken") ~= 0 then return end
    if not MM9.receives("dookscastle", "SleepCaptain", "StartUp", CAPTAIN) then return end
    set("SleepWoken", 1)
    sargentWalk(SMKR0, 210)
end
handlers[210] = function()
    round.walking = false
    if roundOver() or var("SleepWoken") ~= 1 then return end
    wakeGuards()
end
handlers[211] = function()   -- :WakeGuardUp
    round.walking = false
    local step = var("SleepWoken")
    if roundOver() or step < 1 or step > #ROUND then return end
    local x, y = evt.GetMapActorPosition(ROUND[step])
    if x ~= nil then evt.FaceActorTo(CAPTAIN, x, y, 0.5) end
    evt.WakeActor(ROUND[step])
    set("SleepWoken", step + 1)
    round.wait = 3
    evt.StartTimer(200, seconds(1))
end
handlers[212] = function()   -- :dn
    round.walking = false
    if var("SleepWoken") == #ROUND + 1 then set("SleepWoken", #ROUND + 2) end
end
handlers[200] = function()
    evt.StopTimer(200)
    local step = var("SleepWoken")
    if step == 0 or step > #ROUND + 1 then return end
    if roundOver() then evt.StopActorMove(CAPTAIN) return end
    if round.walking then
        round.ticks = round.ticks + 1
        if round.ticks >= 20 then
            local p = round.point
            evt.StopActorMove(CAPTAIN)
            evt.SetMapActorPosition(CAPTAIN, p[1], p[2], p[3])
            handlers[round.event]()
            return
        end
    elseif round.wait > 0 then
        round.wait = round.wait - 1
        if round.wait == 0 then wakeGuards() return end
    else
        return
    end
    evt.StartTimer(200, seconds(1))
end
local function finishRound()   -- a load during the round
    local step = var("SleepWoken")
    if step == 0 or step > #ROUND + 1 then return end
    for k = math.max(step, 1), #ROUND do evt.WakeActor(ROUND[k]) end
    set("SleepWoken", #ROUND + 2)
    if MM9.actorAlive(CAPTAIN) and var("Hostile") ~= 1 then evt.SetMapActorPosition(CAPTAIN, SMKR1[1], SMKR1[2], SMKR1[3]) end
end

-- The touch Triggers, polled four times a second (fire on any part of the party in the box, then Off).
local function inBox(b, x, y, z) return x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] and z + 170 >= b[1][3] and z <= b[2][3] end
local BOXES = {{name = "SleepTrigger", event = 73, box = {{-218, 3886, 404}, {218, 4142, 660}}}, {name = "ScurryTrigger0", event = 74, box = {{11540, 8125, -2455}, {12052, 9405, -2199}}}, {name = "ScurryTrigger1", event = 75, box = {{5376, 7260, -1137}, {6912, 8796, -1009}}}}
handlers[201] = function()
    evt.StartTimer(201, seconds(0.25))
    local x, y, z = evt.GetPartyPosition()
    for _, b in ipairs(BOXES) do
        if var("Fired" .. b.name) == 0 and inBox(b.box, x, y, z) then
            set("Fired" .. b.name, 1)
            handlers[b.event]()
        end
    end
end

-- ScurryCreature.scr: the small basilisks run to their HideMarker at six times their speed and vanish (Hide,
-- sent by ScurryTrigger0/1, which then turn Off).
handlers[74] = function()   -- ScurryTrigger0
    if var("ScurryTrigger0") == 1 then return end
    set("ScurryTrigger0", 1)
    evt.PlaySoundName("animsounds/dragonredhop.wav", 0, 0, 0)
    if MM9.receives("dookscastle", "ScurryBasilisk0", "Hide", 34) then MM9.removeActor(34) end
    if MM9.receives("dookscastle", "ScurryBasilisk1", "Hide", 35) then MM9.removeActor(35) end
    if MM9.receives("dookscastle", "ScurryBasilisk2", "Hide", 36) then MM9.removeActor(36) end
end
handlers[75] = function()   -- ScurryTrigger1
    if var("ScurryTrigger1") == 1 then return end
    set("ScurryTrigger1", 1)
    evt.PlaySoundName("animsounds/dragonredhop.wav", 0, 0, 0)
    if MM9.receives("dookscastle", "ScurryBasilisk3", "Hide", 38) then MM9.removeActor(38) end
    if MM9.receives("dookscastle", "ScurryBasilisk4", "Hide", 41) then MM9.removeActor(41) end
    if MM9.receives("dookscastle", "ScurryBasilisk5", "Hide", 39) then MM9.removeActor(39) end
end

-- Prop5: BookLetter.scr "492 Letter" (DoLetter 492).
handlers[71] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Attention all Guards\n\nI know there is great interest in what my soldiers are doing in the caverns below this castle.  I hereby order you to not go down there any longer.  The guards you bother by taking the passage have earned their sleep from being on watch all day.  Suffice to say that you will all be greatly rewarded when I retrieve what is down there.\n\nThank you for your patience,\nYour Dook") end

-- Prop6: BookLetter.scr "493 Letter" (DoLetter 493).
handlers[72] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Letter to the Dook\n\nMy Lord Dook,\nFor three nights in a row now, the Watch Captain has walked by me while I was at my post and beat me on the head.  He says it's to make sure that I wasn't sleeping, but when I move to make sure he knows I'm not sleeping, he beats me harder for not staying at attention.  I'm not the only guard who has been complaining about this, nor the only one who would be happy if he were fired.\n\nA Concerned Guard") end

-- Map load: the guards' hostility as saved (DookHostility.inc OnPostMiniSaveLoad), the secret door's state.
handlers[1] = function()
    applyHostility()
    finishRound()
    evt.StartTimer(201, seconds(0.25))
    if var("SecretOpen") == 1 then open("Tempbutton_INV") open("doorslide") end
end

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
RegisterEvent(45, "Chest", handlers[45], "Chest")
RegisterEvent(46, "Chest", handlers[46], "Chest")
RegisterEvent(47, "Chest", handlers[47], "Chest")
RegisterEvent(70, "Shield", handlers[70], "Shield")
RegisterEvent(73, "SleepTrigger", handlers[73])
RegisterMapTimerEvent(200, seconds(3), handlers[200], "Wake", "", seconds(3))
RegisterEvent(210, "Sargent", handlers[210])
RegisterEvent(211, "Sargent", handlers[211])
RegisterEvent(212, "Sargent", handlers[212])
RegisterMapTimerEvent(201, seconds(3), handlers[201], "Trigger volumes", "", seconds(3))
RegisterEvent(74, "ScurryTrigger0", handlers[74])
RegisterEvent(75, "ScurryTrigger1", handlers[75])
RegisterEvent(71, "Letter", handlers[71], "Letter")
RegisterEvent(72, "Letter", handlers[72], "Letter")
RegisterEvent(1, "Map load", handlers[1])
RegisterMonsterDamageHook(96, "Guards hurt", handlers[96])
RegisterMonsterKilledHook(97, "Guards killed", handlers[97])
