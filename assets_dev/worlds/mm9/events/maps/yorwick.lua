-- Yorwick, MM9 rework (level_generation/projects/mm9r_yorwick/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {CTgate = 1, OutfitterDoor1 = 2, OutfitterDoor2 = 3, RotatingDoor0 = 4, RotatingDoor1 = 5, RotatingDoor2 = 6, RotatingDoor3 = 7, StoreFrontDoor = 8}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 902}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[102] = function() evt.SetDoorState(2, DoorAction.Trigger) evt.SetDoorState(3, DoorAction.Trigger) end   -- OutfitterDoor1
handlers[103] = function() evt.SetDoorState(4, DoorAction.Trigger) end   -- RotatingDoor0
handlers[104] = function() evt.SetDoorState(5, DoorAction.Trigger) end   -- RotatingDoor1
handlers[105] = function() evt.SetDoorState(6, DoorAction.Trigger) end   -- RotatingDoor2
handlers[106] = function() evt.SetDoorState(7, DoorAction.Trigger) end   -- RotatingDoor3
handlers[107] = function() evt.SetDoorState(8, DoorAction.Trigger) end   -- StoreFrontDoor

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest0
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest1

local function has(k) return MM9.hasKey(k) == 1 end
local function quest() MM9.playSound("sounds/events/quest.wav") end
local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; if gold > 0 then MM9.giveGold(gold) end; quest() end

-- CTgate is barred by gateboard (destructibles whose DeathTrigger opens it): a click says so until they are broken; breaking the last opens the door (and tells the region's
-- handlers.barredOpened).
handlers[360] = function()
    if not (evt.IsDestructibleDestroyed(23)) then return end
    evt.SetDoorState(1, DoorAction.Open)
    if handlers.barredOpened then handlers.barredOpened("CTgate") end
end
handlers[101] = function()
    if evt.IsDestructibleDestroyed(23) then evt.SetDoorState(1, DoorAction.Open)
    else evt.PlaySoundName("door/doorlock01.wav", 0, 0, 0); evt.StatusText("It is barred.") end
end
-- ForadWorld.scr (ScriptObject0, "yorwick"): key 1032 is the party's location while here (keys
-- 1024-1033), and key 5017 closes the shops from 20:00 to 06:00 (MM9's dialogues test it).
local function shopHours()
    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24
    local closed = hour >= 20 or hour < 6
    if closed and not has(5017) then MM9.giveKey(5017) elseif not closed and has(5017) then MM9.takeKey(5017) end
end
handlers[260] = function() shopHours() end

-- StatStone0 (StatStone: Stat 1 Magic, +50 for 3700 s)
handlers[390] = function()
    if evt.CurrentGameMinutes() < var("StatStoneUntil0") then
        evt.StatusText("The stone's power is still with you.") return
    end
    evt.ApplyPartyPrimaryStatBuff(1, 50, 3700) evt.ApplyPartyPrimaryStatBuff(2, 50, 3700)
    set("StatStoneUntil0", evt.CurrentGameMinutes() + 62)
    evt.PlaySoundName("events/dingbell.wav", 0, 0, 0)
    evt.StatusText("+50 Magic for 1.02778 hours")
end
-- BookLetter.scr letters (BOOK AND SCROLL TEXT.csv rows).
handlers[330] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Invoice from Freetown\n\n12 Head of Sheep             20 Gold\n130 Gallons of Ale           120 Gold\nProtection from Evil        1000 Gold\nTotal                             1140 Gold\n\nDue To Tax Collector") end   -- Prop80 (477)
handlers[331] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Letter to Gorig\n\nGorig,\nI've just seen this season's invoice from Freetown.  I don't know where the Queen thinks we are going to get that much gold!  The only way we'll be able to get that much money is to take the loan Kira the Cold offered us.  Borrowing from one tyrant to pay another if you ask me!  I order you to find another way to obtain enough money to pay the queen.\n\nMayor Gorge") end   -- Prop81 (478)
handlers[332] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("To all residents:\n\nThere are rumors of an army to the west that will be upon us very soon.  I urge you all to not take up arms against them.  The Framish Queen has not promised us any soldiers, and I suspect that Freetown may already have been taken.  The sooner we allow these soldiers to come and go, the safer we all shall be.\n\nMayor Gorge") end   -- Prop82 (475)
handlers[333] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Letter to Kjara\n\nDear Kjara,\nI am truly sorry about your last visit.  Along with this letter, I shall send a new cart to replace the one that was destroyed by the magic mines.  I know you said that it wasn't my responsibility and that we all live with the threat of the mines, but those mines were on my land.  I beg you to take the cart as compensation.\n\nGunnar") end   -- Prop83 (474)
handlers[334] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Letter to Tamur\n\nLord Tamur,\nOur advance scouts have reported that the town of Yorwick should be easy pickings, and could possibly be a strong base to launch attacks into Chedian.  The Grein River is a formidable obstacle, and we should take steps to secure its crossing points.  \nOnce that is done, securing a supply of Elemental Thjorad should be a mere few months away at most.\n\nR.D.") end   -- Prop84 (476)

-- Svenspeech.scr :Init with SvenShowTake.inc: the battlefield's tableau (SetSprite key 401) and Sven
-- (actor 75) are shown only while Bikki's prize is delivered (key 95) and the battle not seen (key 97);
-- then the cinematic battlefield_sven plays (its :Award gives key 97 and the experience).
local function battlefield(shown)
    evt.SetSprite(401, shown and 1 or 0, "0")
    evt.SetMonsterBit(75, ActorAttribute.Invisible, shown and 0 or 1)   -- Sven
end

-- Hidemodel.scr :Init (Prop2) shows the Penance Quest's prop once key 102 is held.
handlers.regionLoad = function()
    evt.SetSprite(400, (has(102)) and 1 or 0, "0")   -- Prop2 (hidemodel.scr "102 Unhide")
    local battle = has(95) and not has(97)
    battlefield(battle)   -- Sven (svenspeech.scr :Init)
    if battle then MM9Cinematic.start("battlefield_sven") end
end

-- NPC312.scr :OnRude (Mary, RUDE 312): her sheep back (key 467 from her row "Here's your sheep"): 2 gold,
-- 20 000 experience, key 468.
handlers[50226] = function()
    if has(467) and not has(468) then reward(468, 18500, 2) end -- MM9 GiveExp 20000, mm9_quest_xp_profile.yml
end

-- MarySheep.scr :OnUse (the ewe, actor 73): it follows the party (FollowPlayer.inc) until it is within
-- 512 LT of Mary (actor 50; NPC312.scr :RuntoMe): key 466, and it runs to her and stays.
-- MM9's lifecycle (MM9.receives, MM9.actorAlive): the click sends Mary "Target", which a slain Mary does not
-- take (map var EweUnwatched 1: no key from this walk); :RuntoMe is her OnTargetWithinDist, which fires only
-- while she lives; a slain ewe follows no more and takes no RuntoMe.
handlers[53249] = function()   -- Ewe0
    if has(466) or var("EweFollow") ~= 0 then return end
    set("EweFollow", 1)
    set("EweUnwatched", MM9.receives("yorwick", "CommonerChildHuman2ChildA0", "Target", 50) and 0 or 1)
end
handlers[340] = function()
    if var("EweFollow") ~= 1 then return end
    local ex, ey = evt.GetMapActorPosition(73)
    local mx, my, mz = evt.GetMapActorPosition(50)
    if ex == nil or mx == nil then return end
    if var("EweUnwatched") == 0 and MM9.actorAlive(50) and (ex - mx) ^ 2 + (ey - my) ^ 2 <= 1311 ^ 2 then
        set("EweFollow", 2)
        MM9.giveKey(466)
        if MM9.receives("yorwick", "Ewe0", "RuntoMe", 73) then
            evt.MoveActorTo(73, mx, my, mz, 0, true)   -- :OnRun: runto Mary
        end
        return
    end
    if not MM9.actorAlive(73) then return end   -- FollowPlayer.inc: the ewe's own walk
    local px, py, pz = evt.GetPartyPosition()
    local gap = math.sqrt((ex - px) ^ 2 + (ey - py) ^ 2)
    if gap > 300 then evt.MoveActorTo(73, px, py, pz, 0, gap > 1200)
    else evt.StopActorMove(73) end
end



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

-- Cinematic battlefield_sven (Svenspeech.scr :Init..:FadeOut2, BattleCam1.scr): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["battlefield_sven"] = {
    { "start", function()
        battlefield(true)   -- SvenShowTake.inc :RemoveAll with ShowAll TRUE (:Init)
        set("AmbientSound261", 2)   -- AmbientSound0 off (:OnStart)
        set("AmbientSound262", 2)   -- AmbientSound1 off (:OnStart)
        set("AmbientSound263", 2)   -- AmbientSound2 off (:OnStart)
        set("AmbientSound264", 2)   -- AmbientSound3 off (:OnStart)
        set("AmbientSound265", 2)   -- AmbientSound4 off (:OnStart)
        set("AmbientSound266", 2)   -- AmbientSound5 off (:OnStart)
        set("AmbientSound267", 2)   -- AmbientSound6 off (:OnStart)
        set("AmbientSound268", 2)   -- AmbientSound7 off (:OnStart)
    end },
    { "award", function()
        if not has(97) and has(95) then MM9.giveKey(97); MM9.giveExperience(18500) end
    end },
    { "finale", function()
        set("AmbientSound261", 1)   -- AmbientSound0 on
        set("AmbientSound262", 1)   -- AmbientSound1 on
        set("AmbientSound263", 1)   -- AmbientSound2 on
        set("AmbientSound264", 1)   -- AmbientSound3 on
        set("AmbientSound265", 1)   -- AmbientSound4 on
        set("AmbientSound266", 1)   -- AmbientSound5 on
        set("AmbientSound267", 1)   -- AmbientSound6 on
        set("AmbientSound268", 1)   -- AmbientSound7 on
        battlefield(false)   -- the tableau as every later load leaves it (:Init with key 97)
    end },
}
RegisterEvent(36001, "Cinema battlefield_sven: start", function() MM9Cinematic.runStep("battlefield_sven", 1) end)
RegisterEvent(36002, "Cinema battlefield_sven: award", function() MM9Cinematic.runStep("battlefield_sven", 2) end)
RegisterEvent(36003, "Cinema battlefield_sven: finale", function() MM9Cinematic.runStep("battlefield_sven", 3) end)
RegisterEvent(36000, "Cinema battlefield_sven: done", function() MM9Cinematic.finish("battlefield_sven") end)
MM9Cinematic.play["battlefield_sven"] = function()
    if evt.GetMapVar("Cinema.battlefield_sven.started", 0) == 0 then
        evt.SetMapVar("Cinema.battlefield_sven.started", 1)
        evt.PlayCinematic("battlefield_sven", 36000)
    end
end

handlers[1] = function()
    for k = 1024, 1033 do MM9.takeKey(k) end
    MM9.giveKey(1032)
    shopHours()
    if handlers.regionLoad then handlers.regionLoad() end
end

-- MM9's greeting voices (dungeon/voices.py): a click on these people plays their GreetingSound or the
-- voice their script's :OnUse plays, then opens their dialogue (or runs the map's own click).
handlers[53226] = function() MM9.playSound("voices/npc/npc_312.wav"); MM9.openRude(312) end   -- CommonerChildHuman2ChildA0
handlers[53242] = function() MM9.playSound("voices/npc/npc_313.wav"); MM9.openRude(313) end   -- CommonerHuman2FemaleA0
handlers[53415] = function() MM9.playSound("voices/npc/npc_314.wav"); MM9.openRude(314) end   -- CommonerFemale1

-- MM9's bonus props (dungeon/objects.py bonus_lines; the use of each class, object.lto): wells, cauldrons,
-- cook pots and clovers.
handlers[30107] = function() MM9.useCauldron(107, 0, 15) end   -- obj_Cauldron0 (Cauldron)
handlers[30153] = function() MM9.useCauldron(153, 1, 15) end   -- obj_Cauldron1 (Cauldron)
handlers[30183] = function() MM9.useCauldron(183, 4, 10) end   -- obj_Cauldron2 (Cauldron)

-- MM9's PerceptionBrushes (dungeon/perception.py): the red glow shows to a party whose Perception reaches the
-- brush's PerceptionValue, checked on load and every 3 s; map Lua turns one off for good with
-- set("HintOff<cog>", 1) (MM9's Off message to the brush).
local HINTS = {[23211] = 0, [23212] = 0, [23213] = 0, [23214] = 0, [23215] = 0, [23216] = 0, [23217] = 0, [23218] = 0, [23219] = 0}
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

RegisterEvent(102, "Door", handlers[102], "Door")
RegisterEvent(103, "Door", handlers[103], "Door")
RegisterEvent(104, "Door", handlers[104], "Door")
RegisterEvent(105, "Door", handlers[105], "Door")
RegisterEvent(106, "Door", handlers[106], "Door")
RegisterEvent(107, "Door", handlers[107], "Door")
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(360, "CTgate unbarred", handlers[360])
RegisterEvent(101, "Barred door", handlers[101], "Door")
RegisterMapTimerEvent(260, seconds(3), handlers[260], "Shop hours", "", seconds(3))
RegisterEvent(390, "Stat stone", handlers[390], "Touch")
RegisterEvent(330, "Prop80", handlers[330], "Read")
RegisterEvent(331, "Prop81", handlers[331], "Read")
RegisterEvent(332, "Prop82", handlers[332], "Read")
RegisterEvent(333, "Prop83", handlers[333], "Read")
RegisterEvent(334, "Prop84", handlers[334], "Read")
RegisterEvent(50226, "Mary", handlers[50226])
RegisterEvent(53249, "Mary's ewe", handlers[53249])
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(53226, "Mary Sheepherder", handlers[53226])
RegisterEvent(53242, "Forbhlaith A'Mor", handlers[53242])
RegisterEvent(53415, "Ulf the Unmemorable", handlers[53415])
RegisterEvent(30107, "Cauldron", handlers[30107], "Drink")
RegisterEvent(30153, "Cauldron", handlers[30153], "Drink")
RegisterEvent(30183, "Cauldron", handlers[30183], "Drink")
RegisterMapTimerEvent(901, seconds(3), handlers[901], "Perception hints", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
RegisterMapTimerEvent(340, seconds(0.5), handlers[340], "The ewe follows", "", seconds(0.5))
