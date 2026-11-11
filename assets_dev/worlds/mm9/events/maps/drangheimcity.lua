-- Drangheim City, MM9 rework (level_generation/projects/mm9r_drangheimcity/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {AlchemistDoorLeft = 2, AlchemistDoorRight = 1, BlacksmithDoor0 = 3, BlacksmithDoor1 = 4, HouseDoor1 = 5, HouseDoor2 = 6, InnDoorLeft = 8, InnDoorRight = 7, MayorHouseDoor = 9, MayorHouseDoor2 = 10, MayorHouseDoor3 = 11, NewHouseDoor0 = 13, NewHouseDoor1 = 12, RotatingDoor0 = 14, RotatingDoor1 = 16, RotatingDoor2 = 15, RotatingDoor3 = 17, SettlersDoor = 18, SettlersDoor0 = 19, SmalHouse1Door = 20, SmalHouse2Door = 21, SmithShackDoor = 22, StairDoor = 23, StoreDoor1 = 24, StoreDoor2 = 25, TempleDoorLeft = 27, TempleDoorRight = 26, TempleUpperDoor = 28, TowerDoor = 29, TownHallDoorLeft = 31, TownHallDoorRight = 30, TrainingDoor0 = 33, TrainingDoor1 = 32}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 906, 902}, onLeave = {}, timers = {}, openedChestIds = {}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(3, DoorAction.Trigger) evt.SetDoorState(4, DoorAction.Trigger) end   -- BlacksmithDoor0
handlers[102] = function() evt.SetDoorState(7, DoorAction.Trigger) evt.SetDoorState(8, DoorAction.Trigger) end   -- InnDoorLeft
handlers[103] = function() evt.SetDoorState(9, DoorAction.Trigger) end   -- MayorHouseDoor
handlers[104] = function() evt.SetDoorState(10, DoorAction.Trigger) end   -- MayorHouseDoor2
handlers[105] = function() evt.SetDoorState(11, DoorAction.Trigger) end   -- MayorHouseDoor3
handlers[106] = function() evt.SetDoorState(12, DoorAction.Trigger) evt.SetDoorState(13, DoorAction.Trigger) end   -- NewHouseDoor0
handlers[107] = function() evt.SetDoorState(14, DoorAction.Trigger) evt.SetDoorState(15, DoorAction.Trigger) end   -- RotatingDoor0
handlers[108] = function() evt.SetDoorState(17, DoorAction.Trigger) end   -- RotatingDoor3
handlers[109] = function() evt.SetDoorState(18, DoorAction.Trigger) end   -- SettlersDoor
handlers[110] = function() evt.SetDoorState(19, DoorAction.Trigger) end   -- SettlersDoor0
handlers[111] = function() evt.SetDoorState(20, DoorAction.Trigger) end   -- SmalHouse1Door
handlers[112] = function() evt.SetDoorState(21, DoorAction.Trigger) end   -- SmalHouse2Door
handlers[113] = function() evt.SetDoorState(24, DoorAction.Trigger) evt.SetDoorState(25, DoorAction.Trigger) end   -- StoreDoor1
handlers[114] = function() evt.SetDoorState(26, DoorAction.Trigger) evt.SetDoorState(27, DoorAction.Trigger) end   -- TempleDoorLeft
handlers[115] = function() evt.SetDoorState(28, DoorAction.Trigger) end   -- TempleUpperDoor
handlers[116] = function() evt.SetDoorState(29, DoorAction.Trigger) end   -- TowerDoor
handlers[117] = function() evt.SetDoorState(32, DoorAction.Trigger) evt.SetDoorState(33, DoorAction.Trigger) end   -- TrainingDoor0

-- Chests (MM9 TreasureChest objects; loot records in the scene).

local function has(k) return MM9.hasKey(k) == 1 end
local function quest() MM9.playSound("sounds/events/quest.wav") end
local function show(a, on) evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end
local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; if gold > 0 then MM9.giveGold(gold) end; quest() end

-- MM9's locked doors (Locked 1, no key): the smith's shack, the stair door, the tavern's back door, a house and
-- Klusos House's front door (its exit volume in front of the door takes the party in).
handlers[230] = function()
    evt.PlaySoundName("door/doorlock01.wav", 0, 0, 0)
    evt.StatusText("The door is locked.")
end

-- ForadWorld.scr (ScriptObject0, "Drangheim"): key 1027 is the party's location while here (keys
-- 1024-1033 are the towns'); key 5017 closes the shops from 20:00 to 06:00 (MM9 dialogues forbid or require it).
local function shopHours()
    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24
    local closed = hour >= 20 or hour < 6
    if closed and not has(5017) then MM9.giveKey(5017) elseif not closed and has(5017) then MM9.takeKey(5017) end
end

-- The town hall's double door: a click opens or shuts both leaves.
handlers[240] = function() evt.SetDoorState(DOORS["TownHallDoorRight"], DoorAction.Trigger) evt.SetDoorState(DOORS["TownHallDoorLeft"], DoorAction.Trigger) end   -- TownHallDoorLeft

-- BankOrb.scr (Ingimar's bank, RUDE 100): the Orb of Linking. A click with the orb (item 252) after the quest
-- (key 322) unlocks the row that installs it (key 330); the exit places it (key 334 -> 325) and
-- the sixth bank's orb pays 20 000 experience and 15 000 gold (key 337; banks' keys 331-336).
handlers[53329] = function()
    if not has(325) and has(322) and MM9.hasItem(252, "drangheimcity:Banker") == 1 then MM9.giveKey(330) end
    MM9.openRude(100)
end
handlers[50329] = function()
    if not has(330) then return end
    MM9.takeKey(330)
    if not has(334) then return end
    quest(); MM9.takeItem(252, "drangheimcity:Banker"); MM9.giveKey(325)
    if has(337) then return end
    for k = 331, 336 do if not has(k) then return end end
    reward(337, 12500, 15000) -- MM9 GiveExp 20000, mm9_quest_xp_profile.yml
end

-- NPC87.scr (Sigmund the Stressed, Jarl of Drangheim, RUDE 87). The click (OnUse -> United.inc OnCheck): the
-- other five clans' keys (82 Kira, 38 Bjarni, 34 Sven, 63 Markel, 74 Tryygva) give key 178. The exit: key 44
-- gives item 596 (key 489); the gossip (55: 300, 5 000 experience, 5 000 gold); Fort Stenig (49: 171, 32 000,
-- 7 000); Crona Kiga (50: 170, 52 000, 10 000, item 390 taken); the clans united (83: 179, 26 500, 6 000).
handlers[53334] = function()
    if not has(178) and has(82) and has(38) and has(34) and has(63) and has(74) then MM9.giveKey(178) end
    MM9.openRude(87)
end
-- Deviation (the user, 2026-11-08): a party that took the Crona Kiga before the task (the pedestal's key 169)
-- and shows it after "We've already retrieved that." (key 46) has done the task: key 50, which MM9's rows never
-- grant on that path, so Drangheim's pledge (49 and 50) stayed out of reach. Before the rewards below.
handlers[50334] = function()
    if not has(50) and has(169) and has(46) and MM9.hasItem(390, "drangheimcity:Sigmund") == 1 then MM9.giveKey(50) end
    if not has(489) and has(44) then MM9.giveItem(596, "drangheimcity:Sigmund"); MM9.giveKey(489) end
    if not has(300) and has(55) then reward(300, 5000, 5000) end
    if not has(171) and has(49) then reward(171, 16500, 7000) end -- MM9 GiveExp 32000, mm9_quest_xp_profile.yml
    if not has(170) and has(50) then reward(170, 12500, 10000); MM9.takeItem(390, "drangheimcity:Sigmund") end -- MM9 GiveExp 52000, mm9_quest_xp_profile.yml
    if not has(179) and has(83) then reward(179, 12500, 6000) end -- MM9 GiveExp 26500, mm9_quest_xp_profile.yml
end

-- NPC88.scr (Atli the Quick, RUDE 88): the Assassin's trial done (key 226): key 227, 63 000 experience,
-- 5 000 gold, every character holding key 405-408 promoted to Assassin.
handlers[50347] = function()
    if not has(227) and has(226) then
        reward(227, 37500, 5000) -- MM9 GiveExp 63000, mm9_quest_xp_profile.yml
        MM9.promoteParty("Assassin")
    end
end

-- NPC89.scr (Keith Bloodaxe, RUDE 89): Atli taken where he goes (key 136): key 137, 24 500 experience,
-- 5 000 gold, every character holding key 413-416 promoted to Crusader.
handlers[50320] = function()
    if not has(137) and has(136) then
        reward(137, 16500, 5000) -- MM9 GiveExp 24500, mm9_quest_xp_profile.yml
        MM9.promoteParty("Crusader")
    end
end

-- NPC95.scr (Guaire A'Velsi, a Bandit, RUDE 95): Atli's assassination target. Shown (300 hit points) once Atli
-- gave the task (key 222); his death gives key 225 and he is gone for good.
local BANDIT = 38
handlers[97] = function(context)
    if context.actorIndex == BANDIT and not has(225) then MM9.giveKey(225) end
end

-- NPC378.scr (Thorolf Ratatoskssen, two copies, RUDE 378): the messenger. Talking to one removes the other; after
-- the message (key 84) or the summons (key 107) he vanishes by town portal; with 83 or 106 alone the dialogue
-- reopens (it cannot be skipped).
handlers[53335] = function() MM9.removeActor(22); MM9.openRude(378) end
handlers[50335] = function()
    if has(107) or has(84) then MM9.clientFx(21, "mm9:town_portal"); MM9.removeActor(21); MM9.removeActor(22)
    elseif has(106) or has(83) then MM9.openRude(378) end
end
handlers[53336] = function() MM9.removeActor(21); MM9.openRude(378) end
handlers[50336] = function()
    if has(107) or has(84) then MM9.clientFx(22, "mm9:town_portal"); MM9.removeActor(22); MM9.removeActor(21)
    elseif has(106) or has(83) then MM9.openRude(378) end
end

-- NPC110.scr / NPC109.scr (Hrolf Anfarssen and Alfrigg Hafnarssen): the first time Hrolf sees the party
-- (OnFoundPlayer :OnStart, without key 5010) they quarrel, the cinematic dwarves_and_humans, and
-- fight (its steps, at the end of this file). On a later load Hrolf stands at HrolfMarker (:Init).
local function hrolfAway()
    evt.SetMapActorPosition(13, 17859, -6349, 346)
end
handlers[56326] = function()
    if not has(5010) then MM9Cinematic.start("dwarves_and_humans") end
end

-- BookLetter.scr letters (BOOK AND SCROLL TEXT.csv rows), Book.scr's book (no text in MM9), TownPortal.scr.
-- TownPortal0: TownPortal.scr "Drangheim": cleansing the altar gives key 5013 and MM9 swaps its dirty skin for
-- the clean one: TownPortal0 (SetSprite 490) hides and TownPortal0Clean (491, the clean
-- altar at its place) shows; the map load does the same once the key is set (:Init FixCheck).
local function townPortalAltar()
    local clean = has(5013)
    evt.SetSprite(490, clean and 0 or 1, "0"); evt.SetSprite(491, clean and 1 or 0, "0")
end
handlers[330] = function()
    if has(5013) then return end
    MM9.giveKey(5013); quest()
    townPortalAltar()
    evt.StatusText("The altar is cleansed.")
end
handlers[331] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0) end   -- Book1 (Book.scr: pages turn, no text)
handlers[332] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("The Study of Poltergeist\n\nThe chain shirt known as Poltergiest has been in the collection for years.  After studying it in detail for six months, I can find no concrete evidence for the claims that it was made from ghost, though I did experience some unusual events during that time.\nOn the fifth day of my research, I thought I heard someone in the laboratory playing with the shirt.  When I returned to the lab, it was about ten degrees cooler than it should have been, and was as empty as I had left it.\nOn the eighteenth day, during my study of the unusually pale color of the links, I felt a strange hand on my shoulder.  When I turned, no one was there.\nOn the ninetieth day, Sven, one of my assistants ran screaming from the lab.  He has not been back since.") end   -- Prop17 (458)
handlers[333] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Letter to Nicolai\n\nMy son Nicolai\nThings have begun to look very bad around here.  I've heard that Armageddon's Blade has been forged.  I will be traveling soon to Antagarich to try and stop the madness.  \nWhile I'm gone, you will be in charge.  I suspect you are old enough now.  Should anything happen to me, you will become King.\nBe mindful of your duties son, and stay vigilant of the Kreegan.  They are still out there, and who knows when their numbers will surge.  If that happens, they will attack again.\nAs always, you have my love.\nYour father, \nRoland Ironfist") end   -- Prop16 (457)
handlers[334] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Letter to Sigmund\n\nJarl Sigmund,\nI really wish you would do something about the Yobboes who have taken up near our village.  They very frequently come into our village and steal things!  Why, they even stole my daughter's dolly!  Please, I implore you.  Send some of your soldiers down to root these people out!\nIosobail A'Norta") end   -- Prop15 (455)
handlers[335] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("About Sturmford\n\nHave you been to Sturmford?  We here at the Drangheim Defense Force have, and are more than happy to share our experiences with you.\nIn Sturmford, anyone who is not native is forced to surrender their arms and wear their hair in ponytails!\nTheir woman all dress like the men, and wear iron-barred masks to keep them in line.\nHelp us rid the world of these people!\nJoin at the House of Thrylgrin") end   -- Prop14 (454)

-- NPC87.scr :Init -> :Vanish: with key 108 Sigmund is back and loops Sit (LoopAnim Sit 0 DoNothing), facing as
-- placed (the fire; MM9 places no chair there); the load and the poll (the key given while here) seat him.
local sigmundSeated = false
local function sigmundSits()
    if sigmundSeated or not has(108) then return end
    sigmundSeated = true
    evt.PlayActorClip(20, "sit", true); evt.FaceActorTo(20, 18749, -5530, 0)
end

local function poll()
    shopHours()
    sigmundSits()
    if not has(225) and has(222) and var("BanditShown") == 0 then set("BanditShown", 1); show(BANDIT, true) end
    evt.StartTimer(260, seconds(1))
end
handlers[260] = poll
handlers[1] = function()   -- map load
    for k = 1024, 1033 do if k ~= 1027 and has(k) then MM9.takeKey(k) end end
    MM9.giveKey(1027)
    -- NPC87.scr :Init: Sigmund is away while key 40 is set, back with 108
    show(20, not (has(40) and not has(108)))
    sigmundSits()
    local thorolf = has(83) and not has(84)   -- NPC378.scr :Init (only Frosgard's third copy comes on 106)
    show(21, thorolf); show(22, thorolf)
    show(18, not has(456))   -- Retainer.scr: Edina A'Mor, hidden while hired
    show(19, not has(455))   -- Retainer.scr: Beagan A'Ghrie, hidden while hired
    show(30, not has(121))   -- NPC414.scr: Nicolai Ironfist moves to Guberland on key 121
    -- NPC95.scr :Init: Guaire A'Velsi is here once Atli gave his task (222), gone once he is dead (225)
    if has(225) then MM9.removeActor(BANDIT) else show(BANDIT, has(222)) end
    if has(5010) then hrolfAway() end   -- NPC110.scr :Init
    townPortalAltar()   -- TownPortal.scr :Init (FixCheck): the clean altar once its key is set
    poll()
end
-- MM9's approach talks (dungeon/lua.py approach_talk): an NPC whose script talks when the party comes
-- within 16 LT of his body (OnTargetWithinDist / RunTo 16 -> DoRude). reach: the feet's distance at which
-- he talks; sight > 0: he runs to the party once he sees it within that range. Once per visit.
local APPROACH_TALKS = {
    {actor = 21, reach = 109, sight = 1536, armed = function() return not has(107) and (not has(84) or has(106)) end,
        talk = function() MM9.removeActor(22); MM9.openRude(378, 21); MM9.playSound("voices/npc/npc_378.wav") end},   -- Thorolf0: NPC378.scr :OnFound RunTo 16 :Talk
    {actor = 22, reach = 109, sight = 1536, armed = function() return not has(107) and (not has(84) or has(106)) end,
        talk = function() MM9.removeActor(21); MM9.openRude(378, 22); MM9.playSound("voices/npc/npc_378.wav") end},   -- Thorolf1: NPC378.scr :OnFound RunTo 16 :Talk
}
local approachDone = {}
handlers[906] = function()
    for k, t in ipairs(APPROACH_TALKS) do
        if not approachDone[k] and t.armed() then
            if evt.ActorSeesParty(t.actor, t.reach) then
                approachDone[k] = true
                if t.sight > 0 then evt.StopActorMove(t.actor) end
                t.talk()
            elseif t.sight > 0 and evt.ActorSeesParty(t.actor, t.sight) then
                local x, y, z = evt.GetPartyPosition()
                evt.MoveActorTo(t.actor, x, y, z, 0, true)
            end
        end
    end
    evt.StartTimer(906, seconds(0.25))
end

-- MM9's greeting voices (dungeon/voices.py): a click on these people plays their GreetingSound or the
-- voice their script's :OnUse plays, then opens their dialogue (or runs the map's own click).
handlers[53320] = function() MM9.playSound("voices/npc/npc_089.wav"); MM9.openRude(89) end   -- CommonerHuman2MaleA0
handlers[53328] = function() MM9.playSound("voices/npc/npc_099.wav"); MM9.openRude(99) end   -- ShopkeeperHumanFemaleA3
do local own = handlers[53329]; handlers[53329] = function() MM9.playSound("voices/npc/npc_100.wav"); own() end end   -- ShopkeeperHumanFemaleA4
handlers[53330] = function() MM9.playSound("voices/npc/npc_105.wav"); MM9.openRude(105) end   -- ShopkeeperHumanFemaleA7
handlers[53331] = function() MM9.playSound("voices/npc/npc_104.wav"); MM9.openRude(104) end   -- ShopkeeperHumanFemaleA6
handlers[53332] = function() MM9.playSound("voices/npc/npc_126.wav"); MM9.openRude(126) end   -- ShopkeeperHumanFemaleA8
handlers[53333] = function() MM9.playSound("voices/npc/npc_125.wav"); MM9.openRude(125) end   -- ShopkeeperHumanFemaleA9
do local own = handlers[53334]; handlers[53334] = function() MM9.playSound("voices/npc/npc_087.wav"); own() end end   -- SigmundtheStressed0
handlers[53337] = function() MM9.playSound("voices/npc/npc_096.wav"); MM9.openRude(96) end   -- CommonerElfMaleA2
handlers[53343] = function() MM9.playSound("voices/npc/npc_098.wav"); MM9.openRude(98) end   -- ShopkeeperHumanFemaleA2
handlers[53344] = function() MM9.playSound("voices/npc/npc_414.wav"); MM9.openRude(414) end   -- Niclolai
handlers[53347] = function() MM9.playSound("voices/npc/npc_088.wav"); MM9.openRude(88) end   -- CommonerElfMaleA0
handlers[53349] = function() MM9.playSound("voices/npc/npc_101.wav"); MM9.openRude(101) end   -- ShopkeeperHumanFemaleA0
handlers[53350] = function() MM9.playSound("voices/npc/npc_102.wav"); MM9.openRude(102) end   -- ShopkeeperHumanFemaleA5
handlers[53351] = function() MM9.playSound("voices/npc/npc_097.wav"); MM9.openRude(97) end   -- ShopkeeperHumanFemaleA1
handlers[53352] = function() MM9.playSound("voices/npc/npc_095.wav"); MM9.openRude(95) end   -- CommonerElfMaleA1

-- MM9's bonus props (dungeon/objects.py bonus_lines; the use of each class, object.lto): wells, cauldrons,
-- cook pots and clovers.
handlers[30625] = function() MM9.useWell(625, 3, 4, 10, 3700, 12) end   -- WellMMIX0 (WellMMIX)
handlers[30632] = function() MM9.useClover(632, "drangheimcity:Clover0") end   -- Clover0 (Clover)
handlers[30633] = function() MM9.useClover(633, "drangheimcity:Clover1") end   -- Clover1 (Clover)

-- MM9's PerceptionBrushes (dungeon/perception.py): the red glow shows to a party whose Perception reaches the
-- brush's PerceptionValue, checked on load and every 3 s; map Lua turns one off for good with
-- set("HintOff<cog>", 1) (MM9's Off message to the brush).
local HINTS = {[23634] = 1, [23635] = 1, [23636] = 1, [23637] = 0, [23638] = 1, [23639] = 1, [23640] = 1, [23641] = 1, [23642] = 1, [23643] = 1, [23644] = 1, [23645] = 1, [23646] = 1, [23647] = 1, [23648] = 1, [23649] = 1, [23650] = 1}
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
RegisterEvent(113, "Door", handlers[113], "Door")
RegisterEvent(114, "Door", handlers[114], "Door")
RegisterEvent(115, "Door", handlers[115], "Door")
RegisterEvent(116, "Door", handlers[116], "Door")
RegisterEvent(117, "Door", handlers[117], "Door")
RegisterEvent(230, "Locked door", handlers[230], "Door")
RegisterEvent(240, "TownHallDoorLeft", handlers[240], "Door")
RegisterEvent(53329, "Ingimar's bank", handlers[53329])
RegisterEvent(50329, "Bank", handlers[50329])
RegisterEvent(53334, "Sigmund", handlers[53334])
RegisterEvent(50334, "Sigmund", handlers[50334])
RegisterEvent(50347, "Atli", handlers[50347])
RegisterEvent(50320, "Keith Bloodaxe", handlers[50320])
RegisterEvent(56326, "Hrolf", handlers[56326])
RegisterEvent(53335, "Thorolf", handlers[53335])
RegisterEvent(50335, "Thorolf", handlers[50335])
RegisterEvent(53336, "Thorolf", handlers[53336])
RegisterEvent(50336, "Thorolf", handlers[50336])
RegisterEvent(330, "TownPortal0", handlers[330], "Altar")
RegisterEvent(331, "Book1", handlers[331], "Book")
RegisterEvent(332, "Prop17", handlers[332], "Read")
RegisterEvent(333, "Prop16", handlers[333], "Read")
RegisterEvent(334, "Prop15", handlers[334], "Read")
RegisterEvent(335, "Prop14", handlers[335], "Read")
RegisterMapTimerEvent(260, seconds(3), handlers[260], "Poll", "", seconds(3))
RegisterEvent(1, "Map load", handlers[1])
RegisterMapTimerEvent(906, seconds(3), handlers[906], "Approach talks", "", seconds(3))
RegisterEvent(53320, "Keith Bloodaxe", handlers[53320])
RegisterEvent(53328, "Daonai A'Norta a'meich", handlers[53328])
RegisterEvent(53330, "Skuli Thorsteinssen", handlers[53330])
RegisterEvent(53331, "Sigtrygg Silkbeard", handlers[53331])
RegisterEvent(53332, "Edina A'Mor", handlers[53332])
RegisterEvent(53333, "Beagan A'Ghrie", handlers[53333])
RegisterEvent(53337, "Greudach A'Dorad", handlers[53337])
RegisterEvent(53343, "Rannveig Olafsdotir", handlers[53343])
RegisterEvent(53344, "Nicolai Ironfist", handlers[53344])
RegisterEvent(53347, "Atli the Quick", handlers[53347])
RegisterEvent(53349, "Thorkatla the Indiscreet", handlers[53349])
RegisterEvent(53350, "Louhi Fresdotir", handlers[53350])
RegisterEvent(53351, "Fintan A'Dlinn", handlers[53351])
RegisterEvent(53352, "Guaire A'Velsi", handlers[53352])
RegisterEvent(30625, "Well", handlers[30625], "Drink")
RegisterEvent(30632, "Clover", handlers[30632], "Pick")
RegisterEvent(30633, "Clover", handlers[30633], "Pick")
RegisterMapTimerEvent(901, seconds(3), handlers[901], "Perception hints", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
RegisterMonsterKilledHook(97, "Guaire killed", handlers[97])


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

-- Cinematic dwarves_and_humans (NPC110.scr :OnStart..:Trigger8, NPC109.scr): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["dwarves_and_humans"] = {
    { "key", function()
        MM9.giveKey(5010)
    end },
    { "fight", function()
        if MM9.actorAlive(13) and MM9.receives("drangheimcity", "Alfrigg", "Fight", 0) then
            evt.SetMonsterRelation(9051, 9008, 1)
            evt.SetMonsterRelation(9008, 9051, 1)
        end
    end },
}
RegisterEvent(36001, "Cinema dwarves_and_humans: key", function() MM9Cinematic.runStep("dwarves_and_humans", 1) end)
RegisterEvent(36002, "Cinema dwarves_and_humans: fight", function() MM9Cinematic.runStep("dwarves_and_humans", 2) end)
RegisterEvent(36000, "Cinema dwarves_and_humans: done", function() MM9Cinematic.finish("dwarves_and_humans") end)
MM9Cinematic.play["dwarves_and_humans"] = function()
    if evt.GetMapVar("Cinema.dwarves_and_humans.started", 0) == 0 then
        evt.SetMapVar("Cinema.dwarves_and_humans.started", 1)
        evt.PlayCinematic("dwarves_and_humans", 36000)
    end
end
-- NPC110.scr / NPC109.scr :OnTargetDead: the first of Hrolf and Alfrigg to die ends their fight (the
-- survivor's RemoveEnemy; the quarrel's fight step set the relations).
handlers[36020] = function(context)
    if context.actorIndex ~= 13 and context.actorIndex ~= 0 then return end
    if evt.GetMapVar("Cinema.dwarves_and_humans.step.fight", 0) == 0 then return end
    evt.SetMonsterRelation(9051, 9008, 0); evt.SetMonsterRelation(9008, 9051, 0)
end
RegisterMonsterKilledHook(36020, "Hrolf and Alfrigg's fight", handlers[36020])
