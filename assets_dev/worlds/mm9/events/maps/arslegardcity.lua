-- Arslegard City, MM9 rework (level_generation/projects/mm9r_arslegardcity/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {ArmorDoor0 = 1, ArmorDoor1 = 2, BankDoor0 = 3, BankDoor1 = 4, ClankDoor1 = 5, ClankDoor2 = 6, CounterDoor = 7, Door0 = 8, GeneralDoor0 = 9, GeneralDoor1 = 10, GeneralDoor2 = 12, GeneralDoor3 = 11, LibraryDoor0 = 14, LibraryDoor1 = 13, MagicDoor0 = 15, MagicDoor1 = 16, NjamBackDoor0 = 17, NjamDoor0 = 18, NjamDoor1 = 19, Njamdoor = 20, RotatingDoor0 = 22, RotatingDoor1 = 21, TavernDoor0 = 23, TavernDoor1 = 24, TempleDoor0 = 26, TempleDoor1 = 25, TrainingDoor0 = 27, TrainingDoor1 = 28, WeaponDoor0 = 29, WeaponDoor1 = 30}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1}, onLeave = {}, timers = {}, openedChestIds = {}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(1, DoorAction.Trigger) evt.SetDoorState(2, DoorAction.Trigger) end   -- ArmorDoor0
handlers[102] = function() evt.SetDoorState(3, DoorAction.Trigger) evt.SetDoorState(4, DoorAction.Trigger) end   -- BankDoor0
handlers[103] = function() evt.SetDoorState(9, DoorAction.Trigger) evt.SetDoorState(10, DoorAction.Trigger) end   -- GeneralDoor0
handlers[104] = function() evt.SetDoorState(11, DoorAction.Trigger) evt.SetDoorState(12, DoorAction.Trigger) end   -- GeneralDoor2
handlers[105] = function() evt.SetDoorState(13, DoorAction.Trigger) evt.SetDoorState(14, DoorAction.Trigger) end   -- LibraryDoor0
handlers[106] = function() evt.SetDoorState(15, DoorAction.Trigger) evt.SetDoorState(16, DoorAction.Trigger) end   -- MagicDoor0
handlers[107] = function() evt.SetDoorState(23, DoorAction.Trigger) evt.SetDoorState(24, DoorAction.Trigger) end   -- TavernDoor0
handlers[108] = function() evt.SetDoorState(25, DoorAction.Trigger) evt.SetDoorState(26, DoorAction.Trigger) end   -- TempleDoor0
handlers[109] = function() evt.SetDoorState(27, DoorAction.Trigger) evt.SetDoorState(28, DoorAction.Trigger) end   -- TrainingDoor0
handlers[110] = function() evt.SetDoorState(29, DoorAction.Trigger) evt.SetDoorState(30, DoorAction.Trigger) end   -- WeaponDoor0
handlers[111] = function() evt.SetDoorState(7, DoorAction.Trigger) end   -- CounterDoor

local function has(k) return MM9.hasKey(k) == 1 end
local function quest() MM9.playSound("sounds/events/quest.wav") end
local function show(a, on) evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end
local function locked()
    evt.PlaySoundName("door/doorlock01.wav", 0, 0, 0)
    evt.StatusText("The door is locked.")
end

-- MM9's locked doors that nothing here unlocks (Locked 1): the Thousand Terrors' double door, Njam's back door.
handlers[230] = locked
-- NjamDoor0/1 (Doorlock.scr 576): Njam's Key (576, Krohn's reward in the Hall of the Gods) opens
-- them; without it they are locked.
handlers[231] = function()
    if var("NjamHouseOpen") == 1 or MM9.hasItem(576, "arslegardcity:NjamDoor0") == 1 then
        set("NjamHouseOpen", 1); evt.SetDoorState(DOORS["NjamDoor0"], DoorAction.Trigger) evt.SetDoorState(DOORS["NjamDoor1"], DoorAction.Trigger)
    else locked() end
end
-- Njamdoor (Locked, Sticky): Njam's own door, unlocked by his chase (NjamChase.scr, key 470).
handlers[232] = function()
    if has(470) then evt.SetDoorState(DOORS["Njamdoor"], DoorAction.Trigger) else locked() end
end
-- RotatingDoor0/1, the Great Gate (Locked): WritMan.scr unlocks and opens it (key 9515).
handlers[233] = function()
    if has(9515) then evt.SetDoorState(DOORS["RotatingDoor1"], DoorAction.Trigger) evt.SetDoorState(DOORS["RotatingDoor0"], DoorAction.Trigger) else locked() end
end

-- NjamChase.scr (Njam the Meddler, Trigger0 'Chase' in his house): with the chase on (key 108) and
-- not yet run (470): his door unlocked, key 470, 226 000 experience, the quest sound,
-- and Njam attacks the party (Addenemy player; :Chase: Target the player, so his behaviour, njam.lua's
-- njamchase.scr mode, gets the "Chase" trigger). A hit on him starts it too (OnDamage Chase). Gone once it
-- ran (:Init: removed with 470).
local function njamChase()
    if has(470) or not has(108) then return end
    MM9.giveKey(470); MM9.giveExperience(22500); quest() -- MM9 GiveExp 226000, mm9_quest_xp_profile.yml
    set("NjamChase", 1)
    evt.SetMonGroupBit(4, MonsterBits.Hostile, true)
    evt.TriggerActor(34, "Chase")
    -- the converter placed him still (MM9 gives him no wander); the chase is MM9's monster AI: he walks
    evt.SetActorImmobile(34, false)
    -- MM9 unlocks Njamdoor "and him to go through it" (BaseDoor); a Locked door gets no ai_open here,
    -- so the chase opens it
    evt.SetDoorState(DOORS["Njamdoor"], DoorAction.Open)
end
-- Trigger0's Chase is a message to Njam: a dead (or removed) Njam takes none (MM9.receives), so no key, no
-- experience and his door stays locked.
handlers[240] = function()
    local njam = 34
    if MM9.receives("arslegardcity", "NjamtheMeddler0", "Chase", njam) then njamChase() end
end

-- NPC334.scr (Hanndl the Gatekeeper, RUDE 334, by the gate): with Gungnir's errand (key 353) and Gungnir (item
-- 189) a click unlocks its row (354); the exit after the errand (356 without 357) takes Gungnir and pays 40 000
-- gold and 5 000 experience (357).
handlers[53113] = function()
    if has(353) and MM9.hasItem(189, "arslegardcity:Hanndl") == 1 then MM9.giveKey(354) end
    MM9.openRude(334)
end
handlers[50113] = function()
    if not has(357) and has(356) then
        MM9.takeItem(189, "arslegardcity:Hanndl"); MM9.giveKey(357); MM9.giveGold(40000); MM9.giveExperience(5000)
        quest()
    end
end

-- NPC339.scr (Jokull the Ugly, RUDE 339, the Stumbling Hero): the exit after the bathhouse is cleaned (351
-- without 352) pays 80 000 experience and 5 000 gold (352).
handlers[50104] = function()
    if not has(352) and has(351) then
        MM9.giveKey(352); MM9.giveExperience(18500) -- MM9 GiveExp 80000, mm9_quest_xp_profile.yml
        MM9.giveGold(5000); quest()
    end
end

-- NPC3.scr (Sven Forkbeard, RUDE 3, "Arslegard"): here with key 102, gone with 104. The click (United.inc
-- :OnCheck, Sven's keys 82, 38, 51, 63, 74): the five clans united gives key 178. The exit: GoGetEm (104 -> 486),
-- Thjorad (32 -> 163, 12 000 experience, 6 000 gold, item 197 taken), Refinery (33 -> 177, 68 004, 3 000),
-- United (83 -> 179, 26 500, 6 000), Lifesaver (234 -> 235, 5 000 experience, 10 000 gold).
handlers[53152] = function()
    if not has(178) and has(82) and has(38) and has(51) and has(63) and has(74) then MM9.giveKey(178) end
    MM9.openRude(3)
end
handlers[50152] = function()
    if has(104) and not has(486) then MM9.giveKey(486); quest() end
    if not has(163) and has(32) then
        MM9.giveKey(163); MM9.giveExperience(12000); MM9.giveGold(6000); quest()
        MM9.takeItem(197, "arslegardcity:Sven")
    end
    if not has(177) and has(33) then MM9.giveKey(177); MM9.giveExperience(22500); MM9.giveGold(3000); quest() end -- MM9 GiveExp 68004, mm9_quest_xp_profile.yml
    if not has(179) and has(83) then MM9.giveKey(179); MM9.giveExperience(12500); MM9.giveGold(6000) end -- MM9 GiveExp 26500, mm9_quest_xp_profile.yml
    if not has(235) and has(234) then MM9.giveExperience(5000); MM9.giveGold(10000); quest(); MM9.giveKey(235) end
    show(33, has(102) and not has(104))
end

-- The Great Gate scenes (FateMan.scr, WritMan.scr: both run their :OnLose on every arrival, `wait 1 .1 OnLose`)
-- as the camera cinemas gate_fate and gate_writ (arslegardcity.cinematics.yml, gate_cinematics.py; their
-- gameplay steps are the MM9Cinematic events at the end of this file, which also run on a skip).
-- FateMan.scr, once (without key 98): Hanndl at the peephole sends the party for a Writ of Fate; key
-- 98, 46 000 experience and `trigger ExitTrigger2`: the move to the Dark Passageway (darkpassageway.blv).
local function fateMan()
    if has(98) then return false end
    MM9Cinematic.start("gate_fate")
    return true
end
-- WritMan.scr: with the Writ shown (key 100) and not yet done (9515): key 9515,
-- Hanndl reads it, 170 000 experience, Hanndl (the gate's actor) removed, the Great Gate unlocked and opened
-- (it closes again after MM9's CloseWaitTime; a click opens it from then on). Done: Hanndl removed (map load).
local function writMan()
    if not has(100) or has(9515) then return end
    MM9Cinematic.start("gate_writ")
end

-- BookLetter.scr letters (BOOK AND SCROLL TEXT.csv rows), Book.scr books (no text in MM9).
handlers[330] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Bill of Sale\n\nThe Arslegard Bathhouse purchase by Jokull the Ugly for the sum of 40,000 gold.\nThe bathhouse was purchased \"As is\".  No guarantees are made about it's suitability for function.") end   -- Prop84 (479)
handlers[331] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Letter to Rocnir\n\nRocnir,\nYou are a fool, aren't you?  Do you not know what is in the Dark Passageway?  There is a reason Krohn himself had difficulty going through it to meet the Wyrdes.  I am not going to pay for your funeral when you come back dead.  And don't give me that \"You're already dead\" excuse again, because I'm sure what's in there will find a way to make you dead permanently!\n\nHafgrim") end   -- Prop85 (481)
handlers[332] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Wanted Winemakers\n\nThe Stumbling Hero is looking for someone who made good wine when they were alive.  Visit Jokull the Ugly at the tavern if you qualify.") end   -- Prop87 (482)
handlers[333] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0) end   -- Books0 (Book.scr: pages turn, no text)
handlers[334] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0) end   -- Books1 (Book.scr: pages turn, no text)
handlers[335] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0) end   -- Books2 (Book.scr: pages turn, no text)
handlers[336] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0) end   -- Books3 (Book.scr: pages turn, no text)
handlers[337] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0) end   -- Books4 (Book.scr: pages turn, no text)

-- The gate scene starts as MM9's does, about 3 s after the arrival (`wait 1 .1 OnLose`, ScreenFadeOut 1, `wait 1
-- 2 OnStart`): three polls. The cinematics begin at MM9's :OnStart.
local arrivalPolls = 0
local function poll()
    arrivalPolls = arrivalPolls + 1
    if arrivalPolls == 3 and not fateMan() then writMan() end
    evt.StartTimer(260, seconds(1))
end
handlers[260] = poll
handlers[1] = function()   -- map load
    show(33, has(102) and not has(104))   -- NPC3.scr :Init (Arslegard)
    if has(470) and var("NjamChase") == 0 then MM9.removeActor(34) end   -- NjamChase.scr :Init
    if var("NjamChase") == 1 then evt.SetActorImmobile(34, false) end   -- a chase saved before the release (njamChase)
    if has(470) then evt.SetDoorState(DOORS["Njamdoor"], DoorAction.Open) end
    if has(9515) then MM9.removeActor(35) end   -- WritMan.scr :DeleteHanndl
    poll()
end
handlers[241] = function(context) if context.actorIndex == 34 then njamChase() end end
-- MM9's greeting voices (dungeon/voices.py): a click on these people plays their GreetingSound or the
-- voice their script's :OnUse plays, then opens their dialogue (or runs the map's own click).
handlers[53104] = function() MM9.playSound("voices/npc/npc_339.wav"); MM9.openRude(339) end   -- ShopkeeperHuman2MaleA0
handlers[53105] = function() MM9.playSound("voices/npc/npc_346.wav"); MM9.openRude(346) end   -- ShopkeeperHuman2MaleA1
handlers[53106] = function() MM9.playSound("voices/npc/npc_343.wav"); MM9.openRude(343) end   -- ShopkeeperHuman2MaleA2
handlers[53107] = function() MM9.playSound("voices/npc/npc_348.wav"); MM9.openRude(348) end   -- ShopkeeperHuman2MaleA3
handlers[53108] = function() MM9.playSound("voices/npc/npc_350.wav"); MM9.openRude(350) end   -- ShopkeeperHuman2MaleA4
handlers[53109] = function() MM9.playSound("voices/npc/npc_349.wav"); MM9.openRude(349) end   -- ShopkeeperHuman2MaleA5
handlers[53110] = function() MM9.playSound("voices/npc/npc_341.wav"); MM9.openRude(341) end   -- ShopkeeperHuman2MaleA6
handlers[53111] = function() MM9.playSound("voices/npc/npc_340.wav"); MM9.openRude(340) end   -- ShopkeeperHuman2MaleA7
handlers[53112] = function() MM9.playSound("voices/npc/npc_351.wav"); MM9.openRude(351) end   -- ShopkeeperHuman2MaleA8
do local own = handlers[53113]; handlers[53113] = function() MM9.playSound("voices/npc/npc_334.wav"); own() end end   -- Hanndl1
do local own = handlers[53152]; handlers[53152] = function() MM9.playSound("voices/npc/npc_003.wav"); own() end end   -- SvenSvenssen0


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
RegisterEvent(230, "Locked door", handlers[230], "Door")
RegisterEvent(231, "Njam's door", handlers[231], "Door")
RegisterEvent(232, "Door", handlers[232], "Door")
RegisterEvent(233, "The Great Gate", handlers[233], "Door")
RegisterEvent(240, "Njam's house", handlers[240])
RegisterEvent(53113, "Hanndl", handlers[53113])
RegisterEvent(50113, "Hanndl", handlers[50113])
RegisterEvent(50104, "Jokull the Ugly", handlers[50104])
RegisterEvent(53152, "Sven", handlers[53152])
RegisterEvent(50152, "Sven", handlers[50152])
RegisterEvent(330, "Prop84", handlers[330], "Read")
RegisterEvent(331, "Prop85", handlers[331], "Read")
RegisterEvent(332, "Prop87", handlers[332], "Read")
RegisterEvent(333, "Books0", handlers[333], "Book")
RegisterEvent(334, "Books1", handlers[334], "Book")
RegisterEvent(335, "Books2", handlers[335], "Book")
RegisterEvent(336, "Books3", handlers[336], "Book")
RegisterEvent(337, "Books4", handlers[337], "Book")
RegisterMapTimerEvent(260, seconds(3), handlers[260], "Poll", "", seconds(3))
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(53104, "Jokull the Ugly", handlers[53104])
RegisterEvent(53105, "Hedin the Swyndlr", handlers[53105])
RegisterEvent(53106, "Thuridr the Able", handlers[53106])
RegisterEvent(53107, "Sigmund Halfhands", handlers[53107])
RegisterEvent(53108, "Hjordisa Alfgeirdotir", handlers[53108])
RegisterEvent(53109, "Fenja Adilsdotir", handlers[53109])
RegisterEvent(53110, "Grim Olfassen", handlers[53110])
RegisterEvent(53111, "Talik the Fist", handlers[53111])
RegisterEvent(53112, "Stu Grimssen", handlers[53112])
RegisterMonsterDamageHook(241, "Njam hurt", handlers[241])


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

-- Cinematic gate_fate (FateMan.scr :OnLose..:ExitIN (Fateman), LoseCam1/2.scr, Hanndl.scr): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["gate_fate"] = {
    { "key", function()
        MM9.giveKey(98)
    end },
    { "peephole_open", function()
        open("Door0")
    end },
    { "peephole_close", function()
        close("Door0")
    end },
    { "experience", function()
        MM9.giveExperience(18500) -- MM9 GiveExp 46000, mm9_quest_xp_profile.yml
    end },
    { "exit", function()
        set("FateMoved", var("FateMoved") + 1)
        evt.MoveToMap(-18995, 1393, 1, 1536, 0, 0, 0, 0, "darkpassageway.blv")   -- ExitTrigger2's row
    end },
}
RegisterEvent(36001, "Cinema gate_fate: key", function() MM9Cinematic.runStep("gate_fate", 1) end)
RegisterEvent(36002, "Cinema gate_fate: peephole_open", function() MM9Cinematic.runStep("gate_fate", 2) end)
RegisterEvent(36003, "Cinema gate_fate: peephole_close", function() MM9Cinematic.runStep("gate_fate", 3) end)
RegisterEvent(36004, "Cinema gate_fate: experience", function() MM9Cinematic.runStep("gate_fate", 4) end)
RegisterEvent(36005, "Cinema gate_fate: exit", function() MM9Cinematic.runStep("gate_fate", 5) end)
RegisterEvent(36000, "Cinema gate_fate: done", function() MM9Cinematic.finish("gate_fate") end)
MM9Cinematic.play["gate_fate"] = function()
    if evt.GetMapVar("Cinema.gate_fate.started", 0) == 0 then
        evt.SetMapVar("Cinema.gate_fate.started", 1)
        evt.PlayCinematic("gate_fate", 36000)
    end
end

-- Cinematic gate_writ (WritMan.scr :OnLose..:FadeIn (Writman), LoseCam1/2/3.scr, Hanndl.scr): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["gate_writ"] = {
    { "key", function()
        MM9.giveKey(9515)
    end },
    { "peephole_open", function()
        open("Door0")
    end },
    { "peephole_close", function()
        close("Door0")
    end },
    { "experience", function()
        MM9.giveExperience(22500) -- MM9 GiveExp 170000, mm9_quest_xp_profile.yml
    end },
    { "gate", function()
        MM9.removeActor(35)   -- DeleteHanndl
        open("RotatingDoor1") open("RotatingDoor0")
    end },
}
RegisterEvent(36051, "Cinema gate_writ: key", function() MM9Cinematic.runStep("gate_writ", 1) end)
RegisterEvent(36052, "Cinema gate_writ: peephole_open", function() MM9Cinematic.runStep("gate_writ", 2) end)
RegisterEvent(36053, "Cinema gate_writ: peephole_close", function() MM9Cinematic.runStep("gate_writ", 3) end)
RegisterEvent(36054, "Cinema gate_writ: experience", function() MM9Cinematic.runStep("gate_writ", 4) end)
RegisterEvent(36055, "Cinema gate_writ: gate", function() MM9Cinematic.runStep("gate_writ", 5) end)
RegisterEvent(36050, "Cinema gate_writ: done", function() MM9Cinematic.finish("gate_writ") end)
MM9Cinematic.play["gate_writ"] = function()
    if evt.GetMapVar("Cinema.gate_writ.started", 0) == 0 then
        evt.SetMapVar("Cinema.gate_writ.started", 1)
        evt.PlayCinematic("gate_writ", 36050)
    end
end
