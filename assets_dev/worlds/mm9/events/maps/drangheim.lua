-- Drangheim, MM9 rework (level_generation/projects/mm9r_drangheim/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {Door0 = 1, RotatingDoor0 = 2, ["cottage door"] = 3}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 902}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}, [44] = {3}}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[103] = function() evt.SetDoorState(3, DoorAction.Trigger) end   -- cottage_door

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest0
handlers[42] = function() evt.OpenChest(1) end   -- Prop11
handlers[43] = function() evt.OpenChest(2) end   -- TreasureChest1
handlers[44] = function() evt.OpenChest(3) end   -- TreasureChest2

local function has(k) return MM9.hasKey(k) == 1 end
local function quest() MM9.playSound("sounds/events/quest.wav") end
local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; if gold > 0 then MM9.giveGold(gold) end; quest() end

-- Doors MM9 never opens (Door0): a click says so (doorlock01.wav).
local function lockedDoor() evt.PlaySoundName("door/doorlock01.wav", 0, 0, 0); evt.StatusText("The door is locked.") end
handlers[101] = lockedDoor
-- doorlock.scr (RotatingDoor0): it opens only while the party carries item 244.
handlers[102] = function()
    if MM9.hasItem(244, "drangheim:RotatingDoor0") == 1 then evt.SetDoorState(2, DoorAction.Trigger)
    else evt.PlaySoundName("door/doorlock01.wav", 0, 0, 0); evt.StatusText("The door is locked.") end
end
-- ForadWorld.scr (ScriptObject0, "drangheim"): key 1027 is the party's location while here (keys
-- 1024-1033), and key 5017 closes the shops from 20:00 to 06:00 (MM9's dialogues test it).
local function shopHours()
    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24
    local closed = hour >= 20 or hour < 6
    if closed and not has(5017) then MM9.giveKey(5017) elseif not closed and has(5017) then MM9.takeKey(5017) end
end
handlers[260] = function() shopHours() end

-- NPC90.scr (Ivsar Forktooth, "Drangheim Main"/"Drangheim Well"): shown with key 17 until 242.
local IVSAR = {[24] = 33, [114] = 38}
local function ivsarShow(on)
    for _, a in pairs(IVSAR) do evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end
end
-- :OnUse ("drangheim"): key 194, the other copy goes, his voice and RUDE 90 (row "What is it, General?").
local function ivsarUse(source)
    if not has(17) or has(242) then return end
    MM9.giveKey(194)
    for index, a in pairs(IVSAR) do
        if index ~= source then evt.SetMonsterBit(a, ActorAttribute.Invisible, 1) end
    end
    MM9.playSound("voices/npc/npc_090.wav")
    MM9.openRude(90)
end
-- :OnRude (the exit): with 242 he is on his way to Sturmford: key 194 taken, both copies gone.
local function ivsarExit()
    if has(242) then MM9.takeKey(194); ivsarShow(false) end
end
handlers[53024] = function() ivsarUse(24) end   -- PrisonerHuman2MaleA0: click
handlers[56024] = function() ivsarUse(24) end   -- PrisonerHuman2MaleA0: OnFoundPlayer
handlers[50024] = ivsarExit   -- PrisonerHuman2MaleA0: RUDE exit
handlers[53114] = function() ivsarUse(114) end   -- PrisonerHuman2MaleA1: click
handlers[56114] = function() ivsarUse(114) end   -- PrisonerHuman2MaleA1: OnFoundPlayer
handlers[50114] = ivsarExit   -- PrisonerHuman2MaleA1: RUDE exit

-- The great book (RealBook.scr): shown or gone by its keys on every load; a click takes it.
handlers.regionLoad = function()
    evt.SetSprite(400, (not has(283) and not has(284)) and 1 or 0, "0")   -- Capstone0 (realbook.scr)
    ivsarShow(has(17) and not has(242))   -- Ivsar Forktooth (NPC90.scr :Init)
end

handlers[330] = function()   -- Capstone0 (realbook.scr)
    if has(283) or MM9.hasItem(244, "drangheim:RealBook") ~= 1 then return end
    MM9.giveItem(347, "drangheim:RealBook"); MM9.giveItem(560, "drangheim:RealBook")
    MM9.giveKey(283); MM9.giveKey(290)
    evt.SetSprite(400, 0, "0")
end

-- NPC91-93.scr: the owners reward their item on the dialogue's exit (keys 133-135 from their RUDE rows).
handlers[50030] = function()   -- Hring, NPC91.scr
    if has(133) and not has(200) then MM9.takeItem(371, "drangheim:RUDEProp6"); reward(200, 2000, 500) end
end
handlers[50029] = function()   -- Ragnheid, NPC92.scr
    if has(134) and not has(198) then MM9.takeItem(372, "drangheim:RUDEProp7"); reward(198, 2000, 500) end
end
handlers[50031] = function()   -- Tyock, NPC93.scr
    if has(135) and not has(199) then MM9.takeItem(370, "drangheim:RUDEProp8"); reward(199, 2000, 500) end
end
-- YobboeMan (TM_HardRock.scr "6 129 6000"): the bandits' deaths send "OneDown";
-- the 6th gives key 129 and 6000 experience, once (Bandit0, Bandit1, Burgler0, Burgler1, Burgler2, Burgler3, Burgler4).
local YOBBOES = {[25] = true, [26] = true, [31] = true, [30] = true, [27] = true, [28] = true, [29] = true}
handlers[601] = function(context)
    if not YOBBOES[context.actorIndex] or has(129) then return end
    set("YobboesDown", var("YobboesDown") + 1)
    if var("YobboesDown") >= 6 then reward(129, 6000, 0) end
end

handlers[1] = function()
    for k = 1024, 1033 do MM9.takeKey(k) end
    MM9.giveKey(1027)
    shopHours()
    if handlers.regionLoad then handlers.regionLoad() end
end

-- MM9's greeting voices (dungeon/voices.py): a click on these people plays their GreetingSound or the
-- voice their script's :OnUse plays, then opens their dialogue (or runs the map's own click).
handlers[53023] = function() MM9.playSound("voices/npc/npc_103.wav"); MM9.openRude(103) end   -- ShopkeeperHuman2MaleA0
handlers[53029] = function() MM9.playSound("voices/npc/npc_092.wav"); MM9.openRude(92) end   -- RUDEProp7
handlers[53030] = function() MM9.playSound("voices/npc/npc_091.wav"); MM9.openRude(91) end   -- RUDEProp6
handlers[53031] = function() MM9.playSound("voices/npc/npc_093.wav"); MM9.openRude(93) end   -- RUDEProp8

-- MM9's BonePile objects (dungeon/objects.py): a click searches the pile (evt.SearchLootProp: its
-- TreasureLevel loot once, DiseaseChance; the pile stays).
handlers[30190] = function() evt.SearchLootProp("mm9:drangheim:object:190") end   -- BonePile0
handlers[30191] = function() evt.SearchLootProp("mm9:drangheim:object:191") end   -- BonePile1
handlers[30192] = function() evt.SearchLootProp("mm9:drangheim:object:192") end   -- BonePile2

-- MM9's bonus props (dungeon/objects.py bonus_lines; the use of each class, object.lto): wells, cauldrons,
-- cook pots and clovers.
handlers[30138] = function() MM9.useCookpot(138, 40, 4, 10, 16) end   -- obj_Cookpot0 (Cookpot)
handlers[30166] = function() MM9.useCauldron(166, 0, 5) end   -- obj_Cauldron0 (Cauldron)

-- MM9's PerceptionBrushes (dungeon/perception.py): the red glow shows to a party whose Perception reaches the
-- brush's PerceptionValue, checked on load and every 3 s; map Lua turns one off for good with
-- set("HintOff<cog>", 1) (MM9's Off message to the brush).
local HINTS = {[23126] = 1, [23127] = 1, [23128] = 8, [23129] = 1, [23130] = 1, [23196] = 1}
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

RegisterEvent(103, "Door", handlers[103], "Door")
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(43, "Chest", handlers[43], "Chest")
RegisterEvent(44, "Chest", handlers[44], "Chest")
RegisterEvent(101, "Locked door", handlers[101], "Door")
RegisterEvent(102, "Locked door", handlers[102], "Door")
RegisterMapTimerEvent(260, seconds(3), handlers[260], "Shop hours", "", seconds(3))
RegisterEvent(330, "Capstone0", handlers[330], "Prop")
RegisterEvent(50030, "RUDEProp6", handlers[50030])
RegisterEvent(50029, "RUDEProp7", handlers[50029])
RegisterEvent(50031, "RUDEProp8", handlers[50031])
RegisterEvent(53024, "Ivsar Forktooth", handlers[53024])
RegisterEvent(56024, "Ivsar Forktooth", handlers[56024])
RegisterEvent(50024, "Ivsar Forktooth", handlers[50024])
RegisterEvent(53114, "Ivsar Forktooth", handlers[53114])
RegisterEvent(56114, "Ivsar Forktooth", handlers[56114])
RegisterEvent(50114, "Ivsar Forktooth", handlers[50114])
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(53023, "Svein Hjarrandssen", handlers[53023])
RegisterEvent(53029, "Ragnheid Lifegiver", handlers[53029])
RegisterEvent(53030, "Hring the Plowhands", handlers[53030])
RegisterEvent(53031, "Tyock A'Norta a'leipshi", handlers[53031])
RegisterEvent(30190, "Bone Pile", handlers[30190], "Bone Pile")
RegisterEvent(30191, "Bone Pile", handlers[30191], "Bone Pile")
RegisterEvent(30192, "Bone Pile", handlers[30192], "Bone Pile")
RegisterEvent(30138, "Cook pot", handlers[30138], "Eat")
RegisterEvent(30166, "Cauldron", handlers[30166], "Drink")
RegisterMapTimerEvent(901, seconds(3), handlers[901], "Perception hints", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
RegisterMonsterKilledHook(601, "Yobboes down", handlers[601])
