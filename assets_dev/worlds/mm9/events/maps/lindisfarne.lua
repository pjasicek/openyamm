-- Lindisfarne, MM9 rework (level_generation/projects/mm9r_lindisfarne/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {BlacksmithDoor1 = 1, BlacksmithDoor2 = 2, InnDoor1 = 3, OutfitterDoor1 = 4, OutfitterDoor2 = 5, RotatingDoor0 = 6, RotatingDoor1 = 7, RotatingDoor2 = 8, RotatingDoor3 = 9, RotatingDoor8 = 10, RotatingDoor9 = 11, TempleDoubleDoor1 = 13, TempleDoubleDoor2 = 12}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 902}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[104] = function() evt.SetDoorState(4, DoorAction.Trigger) evt.SetDoorState(5, DoorAction.Trigger) end   -- OutfitterDoor1
handlers[105] = function() evt.SetDoorState(6, DoorAction.Trigger) end   -- RotatingDoor0
handlers[106] = function() evt.SetDoorState(7, DoorAction.Trigger) end   -- RotatingDoor1
handlers[107] = function() evt.SetDoorState(8, DoorAction.Trigger) end   -- RotatingDoor2
handlers[108] = function() evt.SetDoorState(9, DoorAction.Trigger) end   -- RotatingDoor3
handlers[109] = function() evt.SetDoorState(10, DoorAction.Trigger) end   -- RotatingDoor8
handlers[110] = function() evt.SetDoorState(11, DoorAction.Trigger) end   -- RotatingDoor9
handlers[111] = function() evt.SetDoorState(12, DoorAction.Trigger) evt.SetDoorState(13, DoorAction.Trigger) end   -- TempleDoubleDoor2

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest0

local function has(k) return MM9.hasKey(k) == 1 end
local function quest() MM9.playSound("sounds/events/quest.wav") end
local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; if gold > 0 then MM9.giveGold(gold) end; quest() end

-- Doors MM9 never opens (BlacksmithDoor1, BlacksmithDoor2, InnDoor1): a click says so (doorlock01.wav).
local function lockedDoor() evt.PlaySoundName("door/doorlock01.wav", 0, 0, 0); evt.StatusText("The door is locked.") end
handlers[101] = lockedDoor
handlers[102] = lockedDoor
handlers[103] = lockedDoor
-- ForadWorld.scr (ScriptObject0, "lindisfarne"): key 1031 is the party's location while here (keys
-- 1024-1033), and key 5017 closes the shops from 20:00 to 06:00 (MM9's dialogues test it).
local function shopHours()
    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24
    local closed = hour >= 20 or hour < 6
    if closed and not has(5017) then MM9.giveKey(5017) elseif not closed and has(5017) then MM9.takeKey(5017) end
end
handlers[260] = function() shopHours() end

-- StatStone0 (StatStone: Stat 2 Endurance, +10 for 3700 s)
handlers[390] = function()
    if evt.CurrentGameMinutes() < var("StatStoneUntil0") then
        evt.StatusText("The stone's power is still with you.") return
    end
    evt.ApplyPartyPrimaryStatBuff(3, 10, 3700)
    set("StatStoneUntil0", evt.CurrentGameMinutes() + 62)
    evt.PlaySoundName("events/dingbell.wav", 0, 0, 0)
    evt.StatusText("+10 Endurance for 1.02778 hours")
end
handlers[330] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0) end   -- Books0 (Book.scr: pages turn, no text)

-- Retainer.scr :Init: a retainer is hidden while hired (its key) and back once dismissed.
handlers.regionLoad = function()
    evt.SetMonsterBit(50, ActorAttribute.Invisible, has(462) and 1 or 0)   -- CommonerHuman2MaleA16, key 462
end

-- MAGREEB.scr :OnFoundTarget: a Magreeb that finds the party during the Scholar quest (201, not 202) gives
-- key 202 and the quest sound (Magreeb20, Magreeb21, Magreeb22, Magreeb23, Magreeb24, Magreeb25, Magreeb30, Magreeb31, Magreeb26, Magreeb32, Magreeb33, Magreeb27, Magreeb28, Magreeb29, Magreeb210, Magreeb211).
local MAGREEBS = {{15, 3379}, {16, 3379}, {17, 3379}, {18, 3379}, {19, 3379}, {20, 3379}, {21, 3379}, {22, 3379}, {23, 3379}, {24, 3379}, {25, 3379}, {26, 3379}, {27, 3379}, {28, 3379}, {29, 3379}, {40, 3379}}
handlers[340] = function()
    if not has(201) or has(202) then return end
    for _, m in ipairs(MAGREEBS) do
        if evt.ActorSeesParty(m[1], m[2]) then
            MM9.giveKey(202); MM9.playSound("sounds/events/quest.wav")
            return
        end
    end
end

handlers[1] = function()
    for k = 1024, 1033 do MM9.takeKey(k) end
    MM9.giveKey(1031)
    shopHours()
    if handlers.regionLoad then handlers.regionLoad() end
end

-- MM9's greeting voices (dungeon/voices.py): a click on these people plays their GreetingSound or the
-- voice their script's :OnUse plays, then opens their dialogue (or runs the map's own click).
handlers[53296] = function() MM9.playSound("voices/npc/npc_308.wav"); MM9.openRude(308) end   -- CommonerHuman2MaleA16
handlers[53304] = function() MM9.playSound("voices/npc/npc_288.wav"); MM9.openRude(288) end   -- CommonerHuman2MaleB0
handlers[53305] = function() MM9.playSound("voices/npc/npc_285.wav"); MM9.openRude(285) end   -- CommonerHuman2MaleB1
handlers[53306] = function() MM9.playSound("voices/npc/npc_286.wav"); MM9.openRude(286) end   -- CommonerHuman2MaleB2
handlers[53307] = function() MM9.playSound("voices/npc/npc_287.wav"); MM9.openRude(287) end   -- CommonerHuman2MaleB3

-- MM9's bonus props (dungeon/objects.py bonus_lines; the use of each class, object.lto): wells, cauldrons,
-- cook pots and clovers.
handlers[30318] = function() MM9.useWell(318, 3, 1, 5, 0, 4) end   -- obj_WellMMIX0 (WellMMIX)
handlers[30334] = function() MM9.useCookpot(334, 50, 0, 10, 16) end   -- obj_Cookpot0 (Cookpot)
handlers[30345] = function() MM9.useCookpot(345, 50, 0, 10, 16) end   -- obj_Cookpot1 (Cookpot)
handlers[30375] = function() MM9.useCauldron(375, 3, 5) end   -- obj_Cauldron0 (Cauldron)
handlers[30385] = function() MM9.useClover(385, "lindisfarne:Clover0") end   -- obj_Clover0 (Clover)
handlers[30386] = function() MM9.useClover(386, "lindisfarne:Clover1") end   -- obj_Clover1 (Clover)
handlers[30387] = function() MM9.useClover(387, "lindisfarne:Clover2") end   -- obj_Clover2 (Clover)

-- MM9's PerceptionBrushes (dungeon/perception.py): the red glow shows to a party whose Perception reaches the
-- brush's PerceptionValue, checked on load and every 3 s; map Lua turns one off for good with
-- set("HintOff<cog>", 1) (MM9's Off message to the brush).
local HINTS = {[23027] = 1, [23028] = 1, [23029] = 1, [23030] = 1, [23031] = 1, [23032] = 1, [23033] = 1, [23034] = 1, [23035] = 1, [23036] = 1}
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

RegisterEvent(104, "Door", handlers[104], "Door")
RegisterEvent(105, "Door", handlers[105], "Door")
RegisterEvent(106, "Door", handlers[106], "Door")
RegisterEvent(107, "Door", handlers[107], "Door")
RegisterEvent(108, "Door", handlers[108], "Door")
RegisterEvent(109, "Door", handlers[109], "Door")
RegisterEvent(110, "Door", handlers[110], "Door")
RegisterEvent(111, "Door", handlers[111], "Door")
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(101, "Locked door", handlers[101], "Door")
RegisterEvent(102, "Locked door", handlers[102], "Door")
RegisterEvent(103, "Locked door", handlers[103], "Door")
RegisterMapTimerEvent(260, seconds(3), handlers[260], "Shop hours", "", seconds(3))
RegisterEvent(390, "Stat stone", handlers[390], "Touch")
RegisterEvent(330, "Books0", handlers[330], "Book")
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(53296, "Florie de Latharna A'Washadi", handlers[53296])
RegisterEvent(53304, "Herimgr the Ropewise", handlers[53304])
RegisterEvent(53305, "Rober Rachnid", handlers[53305])
RegisterEvent(53306, "Grymmwild Leaftoucher", handlers[53306])
RegisterEvent(53307, "Randall Stacey", handlers[53307])
RegisterEvent(30318, "Well", handlers[30318], "Drink")
RegisterEvent(30334, "Cook pot", handlers[30334], "Eat")
RegisterEvent(30345, "Cook pot", handlers[30345], "Eat")
RegisterEvent(30375, "Cauldron", handlers[30375], "Drink")
RegisterEvent(30385, "Clover", handlers[30385], "Pick")
RegisterEvent(30386, "Clover", handlers[30386], "Pick")
RegisterEvent(30387, "Clover", handlers[30387], "Pick")
RegisterMapTimerEvent(901, seconds(3), handlers[901], "Perception hints", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
RegisterMapTimerEvent(340, seconds(1), handlers[340], "Magreebs", "", seconds(1))
