-- Thjorgard City, MM9 rework (level_generation/projects/mm9r_thjorgardcity/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {["ApothDoor0"] = 1, ["Armor-Forge0"] = 2, ["ArmorBeddoor0"] = 3, ["ArmordoorL0"] = 4, ["ArmordoorR0"] = 5, ["BankdoorL"] = 7, ["BankdoorR"] = 6, ["BembStudy1"] = 8, ["BembStudy2"] = 9, ["BembdoorL"] = 11, ["BembdoorR"] = 10, ["BembgateL"] = 13, ["BembgateR"] = 12, ["Door10"] = 14, ["Door11"] = 15, ["Door12"] = 16, ["Door13"] = 17, ["Door14"] = 18, ["Door15"] = 19, ["Door16"] = 20, ["Door17"] = 21, ["Door18"] = 22, ["Door19"] = 23, ["Door2"] = 24, ["Door20"] = 25, ["Door21"] = 26, ["Door22"] = 27, ["Door23"] = 28, ["Door24"] = 29, ["Door25"] = 30, ["Door26"] = 31, ["Door27"] = 32, ["Door28"] = 33, ["Door29"] = 34, ["Door3"] = 35, ["Door30"] = 36, ["Door31"] = 37, ["Door32"] = 38, ["Door33"] = 39, ["Door34"] = 40, ["Door35"] = 41, ["Door36"] = 42, ["Door37"] = 43, ["Door38"] = 44, ["Door39"] = 45, ["Door4"] = 46, ["Door40"] = 47, ["Door41"] = 48, ["Door42"] = 49, ["Door43"] = 50, ["Door44"] = 51, ["Door45"] = 52, ["Door46"] = 53, ["Door47"] = 54, ["Door48"] = 55, ["Door49"] = 56, ["Door5"] = 57, ["Door50"] = 58, ["Door51"] = 59, ["Door52"] = 60, ["Door53"] = 61, ["Door54"] = 62, ["Door55"] = 63, ["Door56"] = 64, ["Door57"] = 65, ["Door58"] = 66, ["Door59"] = 67, ["Door6"] = 68, ["Door60"] = 69, ["Door61"] = 70, ["Door62"] = 71, ["Door63"] = 72, ["Door64"] = 73, ["Door65"] = 74, ["Door66"] = 75, ["Door67"] = 76, ["Door68"] = 77, ["Door69"] = 78, ["Door7"] = 79, ["Door70"] = 80, ["Door71"] = 81, ["Door8"] = 82, ["Door9"] = 83, ["ForgedoorL0"] = 84, ["ForgedoorR0"] = 85, ["HearingroomL"] = 87, ["HearingroomR"] = 86, ["LibrarydoorL"] = 88, ["LibrarydoorR"] = 89, ["MageDoorL"] = 90, ["MageDoorR"] = 91, ["MeetingroomL"] = 93, ["MeetingroomR"] = 92, ["Officedoor"] = 94, ["PalacedoorL"] = 95, ["PalacedoorR"] = 96, ["RotatingDoor0"] = 97, ["RotatingDoor1"] = 98, ["RotatingDoor10"] = 99, ["RotatingDoor11"] = 100, ["RotatingDoor12"] = 101, ["RotatingDoor13"] = 102, ["RotatingDoor14"] = 103, ["RotatingDoor15"] = 104, ["RotatingDoor16"] = 105, ["RotatingDoor17"] = 106, ["RotatingDoor18"] = 107, ["RotatingDoor19"] = 108, ["RotatingDoor2"] = 109, ["RotatingDoor20"] = 110, ["RotatingDoor21"] = 111, ["RotatingDoor22"] = 112, ["RotatingDoor23"] = 113, ["RotatingDoor24"] = 114, ["RotatingDoor25"] = 115, ["RotatingDoor26"] = 116, ["RotatingDoor27"] = 117, ["RotatingDoor3"] = 118, ["RotatingDoor4"] = 119, ["RotatingDoor5"] = 120, ["RotatingDoor6"] = 121, ["RotatingDoor7"] = 122, ["RotatingDoor8"] = 123, ["RotatingDoor9"] = 124, ["StoredoorL"] = 125, ["StoredoorR"] = 126, ["THDLL"] = 127, ["THDLR"] = 128, ["THDRL"] = 130, ["THDRR"] = 129, ["TaverndoorL"] = 131, ["TaverndoorR"] = 132, ["TavernkitchenL"] = 133, ["TavernkitchenR"] = 134, ["Tavernstoreroom"] = 135, ["TempledoorL"] = 136, ["TempledoorR"] = 137, ["TownhallL"] = 138, ["TownhallR"] = 139, ["TraininghalldoorL"] = 141, ["TraininghalldoorR"] = 140, ["Weapon-Forge0"] = 142, ["WeaponBeddoor0"] = 143, ["WeapondoorL0"] = 145, ["WeapondoorR0"] = 144}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 906, 902}, onLeave = {}, timers = {}, openedChestIds = {}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(1, DoorAction.Trigger) end   -- ApothDoor0
handlers[102] = function() evt.SetDoorState(2, DoorAction.Trigger) end   -- Armor-Forge0
handlers[103] = function() evt.SetDoorState(3, DoorAction.Trigger) end   -- ArmorBeddoor0
handlers[104] = function() evt.SetDoorState(4, DoorAction.Trigger) evt.SetDoorState(5, DoorAction.Trigger) end   -- ArmordoorL0
handlers[105] = function() evt.SetDoorState(6, DoorAction.Trigger) evt.SetDoorState(7, DoorAction.Trigger) end   -- BankdoorL
handlers[106] = function() evt.SetDoorState(8, DoorAction.Trigger) end   -- BembStudy1
handlers[107] = function() evt.SetDoorState(9, DoorAction.Trigger) end   -- BembStudy2
handlers[108] = function() evt.SetDoorState(10, DoorAction.Trigger) evt.SetDoorState(11, DoorAction.Trigger) end   -- BembdoorL
handlers[109] = function() evt.SetDoorState(19, DoorAction.Trigger) end   -- Door15
handlers[110] = function() evt.SetDoorState(84, DoorAction.Trigger) evt.SetDoorState(85, DoorAction.Trigger) end   -- ForgedoorL0
handlers[111] = function() evt.SetDoorState(86, DoorAction.Trigger) evt.SetDoorState(87, DoorAction.Trigger) end   -- HearingroomL
handlers[112] = function() evt.SetDoorState(88, DoorAction.Trigger) evt.SetDoorState(89, DoorAction.Trigger) end   -- LibrarydoorL
handlers[113] = function() evt.SetDoorState(90, DoorAction.Trigger) evt.SetDoorState(91, DoorAction.Trigger) end   -- MageDoorL
handlers[114] = function() evt.SetDoorState(92, DoorAction.Trigger) evt.SetDoorState(93, DoorAction.Trigger) end   -- MeetingroomL
handlers[115] = function() evt.SetDoorState(94, DoorAction.Trigger) end   -- Officedoor
handlers[116] = function() evt.SetDoorState(95, DoorAction.Trigger) evt.SetDoorState(96, DoorAction.Trigger) end   -- PalacedoorL
handlers[117] = function() evt.SetDoorState(97, DoorAction.Trigger) end   -- RotatingDoor0
handlers[118] = function() evt.SetDoorState(98, DoorAction.Trigger) end   -- RotatingDoor1
handlers[119] = function() evt.SetDoorState(99, DoorAction.Trigger) end   -- RotatingDoor10
handlers[120] = function() evt.SetDoorState(100, DoorAction.Trigger) evt.SetDoorState(101, DoorAction.Trigger) end   -- RotatingDoor11
handlers[121] = function() evt.SetDoorState(102, DoorAction.Trigger) evt.SetDoorState(103, DoorAction.Trigger) end   -- RotatingDoor13
handlers[122] = function() evt.SetDoorState(104, DoorAction.Trigger) end   -- RotatingDoor15
handlers[123] = function() evt.SetDoorState(105, DoorAction.Trigger) evt.SetDoorState(106, DoorAction.Trigger) end   -- RotatingDoor16
handlers[124] = function() evt.SetDoorState(107, DoorAction.Trigger) evt.SetDoorState(108, DoorAction.Trigger) end   -- RotatingDoor18
handlers[125] = function() evt.SetDoorState(109, DoorAction.Trigger) end   -- RotatingDoor2
handlers[126] = function() evt.SetDoorState(110, DoorAction.Trigger) end   -- RotatingDoor20
handlers[127] = function() evt.SetDoorState(111, DoorAction.Trigger) end   -- RotatingDoor21
handlers[128] = function() evt.SetDoorState(112, DoorAction.Trigger) evt.SetDoorState(113, DoorAction.Trigger) end   -- RotatingDoor22
handlers[129] = function() evt.SetDoorState(114, DoorAction.Trigger) evt.SetDoorState(115, DoorAction.Trigger) end   -- RotatingDoor24
handlers[130] = function() evt.SetDoorState(116, DoorAction.Trigger) end   -- RotatingDoor26
handlers[131] = function() evt.SetDoorState(117, DoorAction.Trigger) end   -- RotatingDoor27
handlers[132] = function() evt.SetDoorState(118, DoorAction.Trigger) evt.SetDoorState(119, DoorAction.Trigger) end   -- RotatingDoor3
handlers[133] = function() evt.SetDoorState(120, DoorAction.Trigger) end   -- RotatingDoor5
handlers[134] = function() evt.SetDoorState(121, DoorAction.Trigger) end   -- RotatingDoor6
handlers[135] = function() evt.SetDoorState(122, DoorAction.Trigger) end   -- RotatingDoor7
handlers[136] = function() evt.SetDoorState(123, DoorAction.Trigger) end   -- RotatingDoor8
handlers[137] = function() evt.SetDoorState(124, DoorAction.Trigger) end   -- RotatingDoor9
handlers[138] = function() evt.SetDoorState(125, DoorAction.Trigger) evt.SetDoorState(126, DoorAction.Trigger) end   -- StoredoorL
handlers[139] = function() evt.SetDoorState(127, DoorAction.Trigger) evt.SetDoorState(128, DoorAction.Trigger) end   -- THDLL
handlers[140] = function() evt.SetDoorState(129, DoorAction.Trigger) evt.SetDoorState(130, DoorAction.Trigger) end   -- THDRL
handlers[141] = function() evt.SetDoorState(131, DoorAction.Trigger) evt.SetDoorState(132, DoorAction.Trigger) end   -- TaverndoorL
handlers[142] = function() evt.SetDoorState(133, DoorAction.Trigger) evt.SetDoorState(134, DoorAction.Trigger) end   -- TavernkitchenL
handlers[143] = function() evt.SetDoorState(135, DoorAction.Trigger) end   -- Tavernstoreroom
handlers[144] = function() evt.SetDoorState(136, DoorAction.Trigger) evt.SetDoorState(137, DoorAction.Trigger) end   -- TempledoorL
handlers[145] = function() evt.SetDoorState(138, DoorAction.Trigger) evt.SetDoorState(139, DoorAction.Trigger) end   -- TownhallL
handlers[146] = function() evt.SetDoorState(140, DoorAction.Trigger) evt.SetDoorState(141, DoorAction.Trigger) end   -- TraininghalldoorL
handlers[147] = function() evt.SetDoorState(142, DoorAction.Trigger) end   -- Weapon-Forge0
handlers[148] = function() evt.SetDoorState(143, DoorAction.Trigger) end   -- WeaponBeddoor0
handlers[149] = function() evt.SetDoorState(144, DoorAction.Trigger) evt.SetDoorState(145, DoorAction.Trigger) end   -- WeapondoorL0
handlers[150] = function() evt.SetDoorState(12, DoorAction.Trigger) evt.SetDoorState(13, DoorAction.Trigger) end   -- BembgateL

-- Chests (MM9 TreasureChest objects; loot records in the scene).

local function has(k) return MM9.hasKey(k) == 1 end
local function quest() MM9.playSound("sounds/events/quest.wav") end
local function show(a, on) evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end
local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; if gold > 0 then MM9.giveGold(gold) end; quest() end
-- GivePromo <class>: every eligible member at once (MM9.promoteParty: the quest -> class-line table; MM9's
-- per-character keys are not used: devdocs/mm9/MM9_RUDE_SCR_INTEGRATION.md "Promotions And Classes")
local function promote(class, first) MM9.promoteParty(class) end

-- MM9's locked doors (Locked 1, MoveDist 0, no key): the 69 linear doors of the facades and upper rooms.
handlers[230] = function()
    evt.PlaySoundName("door/doorlock01.wav", 0, 0, 0)
    evt.StatusText("The door is locked.")
end

-- ForadWorld.scr (ScriptObject0, "Thjorgard"): key 1025 is the party's location while here (keys
-- 1024-1033 are the towns'); key 5017 closes the shops from 20:00 to 06:00 (their dialogues forbid or require it).
local function shopHours()
    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24
    local closed = hour >= 20 or hour < 6
    if closed and not has(5017) then MM9.giveKey(5017) elseif not closed and has(5017) then MM9.takeKey(5017) end
end

-- BankOrb.scr (Ragnar Gjalpssen, RUDE 13: nKey 335, nKey2 323): the Orb of Linking. A click with the orb (item
-- 252) after the quest (key 322) unlocks the row that installs it (key 330); the exit places it (key 323) and the
-- sixth bank's orb pays 20 000 experience and 15 000 gold (key 337; banks' keys 331-336).
handlers[54048] = function()
    if not has(323) and has(322) and MM9.hasItem(252, "thjorgardcity:Ragnar") == 1 then MM9.giveKey(330) end
    MM9.openRude(13)
end
handlers[51048] = function()
    if not has(330) then return end
    MM9.takeKey(330)
    if not has(335) then return end
    quest(); MM9.takeItem(252, "thjorgardcity:Ragnar"); MM9.giveKey(323)
    if has(337) then return end
    for k = 331, 336 do if not has(k) then return end end
    reward(337, 12500, 15000) -- MM9 GiveExp 20000, mm9_quest_xp_profile.yml
end

-- NPC4.scr (Johannes Bem, RUDE 4): Scholar to Mage. With 293 the first task's item is swapped (242 -> 244, key
-- 288); with 493 the reward (item 243 taken, key 294, 5 000 gold, 63 000 experience) and the promotion of the
-- characters holding keys 429-432.
handlers[51044] = function()
    if not has(288) and has(293) then
        MM9.takeItem(242, "thjorgardcity:Johannes"); MM9.giveItem(244, "thjorgardcity:Johannes"); MM9.giveKey(288); quest()
        return
    end
    if not has(294) and has(493) then
        MM9.takeItem(243, "thjorgardcity:Johannes"); reward(294, 37500, 5000); promote("Mage", 429) -- MM9 GiveExp 63000, mm9_quest_xp_profile.yml
    end
end

-- NPC161.scr (Tymon the Nord, RUDE 161): Initiate to Scholar. :ScholarCheck: unless done (201), a character
-- holding 425-428 gives 201. MM9's engine set those per-character keys from the class check of "We are seeking
-- promotion to Scholar" (its granted code 2081, kept as key 2081); here: that row asked, whoever is in the party
-- (every promotion quest is offered to any party, the user 2026-11-08, dialogue/promotions.yml). With 203
-- (24 500 experience) or 204 (11 000) and 1 000 gold: key 205 and the promotion of the members eligible.
handlers[51058] = function()
    if not has(201) and has(2081) then MM9.giveKey(201); quest() end
    if has(205) then return end
    if has(203) then reward(205, 16500, 1000); promote("Scholar", 425) -- MM9 GiveExp 24500, mm9_quest_xp_profile.yml
    elseif has(204) then reward(205, 11000, 1000); promote("Scholar", 425) end
end

-- NPC3.scr (Sven Forkbeard, the Jarl, RUDE 3; United.inc). The click: the five clans (82, 38, 51, 63, 74 -> 178).
-- The exit: the battle (104 -> 486), Thjorad Mine (32 -> 163, 12 000 experience, 6 000 gold, item 197 taken), the
-- refinery (33 -> 177, 68 004, 3 000), the clans united (83 -> 179, 26 500, 6 000), the lifesaver (234 -> 235,
-- 5 000 experience, 10 000 gold).
handlers[54098] = function()
    if not has(178) then
        local n = 0
        for _, k in ipairs({82, 38, 51, 63, 74}) do if has(k) then n = n + 1 end end
        if n == 5 then MM9.giveKey(178) end
    end
    MM9.openRude(3)
end
handlers[51098] = function()
    if has(104) and not has(486) then MM9.giveKey(486); quest() end
    if not has(163) and has(32) then reward(163, 12000, 6000); MM9.takeItem(197, "thjorgardcity:Sven") end
    if not has(177) and has(33) then reward(177, 22500, 3000) end -- MM9 GiveExp 68004, mm9_quest_xp_profile.yml
    if not has(179) and has(83) then MM9.giveKey(179); MM9.giveExperience(12500); MM9.giveGold(6000) end -- MM9 GiveExp 26500, mm9_quest_xp_profile.yml
    if not has(235) and has(234) then MM9.giveExperience(5000); MM9.giveGold(10000); quest(); MM9.giveKey(235) end
end

-- NPC5.scr (Gunnar Thjorsmith, the smith, RUDE 5). The click: Thjorad ore in the packs (items 359, 360, 361) unlocks
-- its row (395 + 396, 397, 398). The exit: after the smithing (464) the ore is paid (399: 700, 400: 1 500, 463:
-- 3 000 gold, the ore taken) and keys 395-400, 463, 464 cleared; the refinery's part (9513 -> 9514, item 398 ->
-- 399).
handlers[54077] = function()
    if MM9.hasItem(359, "thjorgardcity:Gunnar") == 1 then MM9.giveKey(395); MM9.giveKey(396) end
    if MM9.hasItem(360, "thjorgardcity:Gunnar") == 1 then MM9.giveKey(395); MM9.giveKey(397) end
    if MM9.hasItem(361, "thjorgardcity:Gunnar") == 1 then MM9.giveKey(395); MM9.giveKey(398) end
    MM9.openRude(5)
end
handlers[51077] = function()
    if has(464) then
        if has(399) then MM9.takeItem(359, "thjorgardcity:Gunnar"); MM9.giveGold(700) end
        if has(400) then MM9.takeItem(360, "thjorgardcity:Gunnar"); MM9.giveGold(1500) end
        if has(463) then MM9.takeItem(361, "thjorgardcity:Gunnar"); MM9.giveGold(3000) end
        for _, k in ipairs({395, 396, 397, 398, 399, 400, 463, 464}) do MM9.takeKey(k) end
    end
    if not has(9514) and has(9513) then
        MM9.takeItem(398, "thjorgardcity:Gunnar"); MM9.giveItem(399, "thjorgardcity:Gunnar"); MM9.giveKey(9514); quest()
    end
end

-- NPC7.scr (Hjarrand Fixer, RUDE 7; not at the refinery): the payment for fixing the refinery's machine. With 360
-- (1 000 gold) or 361 (2 000) and the gold: key 362, 363 cleared; without the gold: key 363 (MM9 plays a voice).
-- He leaves the city once paid (hidden on 362).
handlers[51066] = function()
    if has(362) then return end
    for _, cost in ipairs({{360, 1000}, {361, 2000}}) do
        if has(cost[1]) then
            if MM9.hasGold(cost[2]) == 1 then MM9.takeGold(cost[2]); MM9.giveKey(362); MM9.takeKey(363); quest()
            else MM9.giveKey(363) end
            return
        end
    end
end

-- NPC416.scr (Harris Willington, RUDE 416) :OnDeath: the prize quest's key 233.
handlers[270] = function(context)
    if context.actorIndex == 2 then MM9.giveKey(233) end
end

-- NPC378.scr (Thorolf Ratatoskssen, two copies, RUDE 378): the messenger. Talking to one removes the other; after
-- the message (key 84) or the summons (key 107) he vanishes by town portal; with 83 or 106 alone the dialogue
-- reopens (it cannot be skipped).
handlers[54105] = function() MM9.removeActor(58); MM9.openRude(378) end
handlers[51105] = function()
    if has(107) or has(84) then MM9.clientFx(57, "mm9:town_portal"); MM9.removeActor(57); MM9.removeActor(58)
    elseif has(106) or has(83) then MM9.openRude(378) end
end
handlers[54106] = function() MM9.removeActor(57); MM9.openRude(378) end
handlers[51106] = function()
    if has(107) or has(84) then MM9.clientFx(58, "mm9:town_portal"); MM9.removeActor(58); MM9.removeActor(57)
    elseif has(106) or has(83) then MM9.openRude(378) end
end

-- BookLetter.scr letters (BOOK AND SCROLL TEXT.csv rows), Book.scr books (no text in MM9), TownPortal.scr,
-- GreatBookKey.scr, the well.
-- BookKey: GreatBookKey.scr. Shown only with key 375 (its 'appear' message, which nothing in MM9
-- sends) and gone with 374. A click with the Great Book (item 243) gives items 560, 244 and 347 and
-- takes the key (374); without it the click gives item 244 (MM9 does).
local function bookKeyShown() return has(375) and not has(374) end
handlers[330] = function()
    if not bookKeyShown() then return end
    if MM9.hasItem(243, "thjorgardcity:BookKey") == 1 then
        MM9.giveItem(560, "thjorgardcity:BookKey"); MM9.giveItem(244, "thjorgardcity:BookKey"); MM9.giveItem(347, "thjorgardcity:BookKey")
        MM9.giveKey(374); evt.SetSprite(400, 0, "0")
    else MM9.giveItem(244, "thjorgardcity:BookKey") end
end
-- TownPortal0: TownPortal.scr "Thjorgard": cleansing the altar gives key 5011 and MM9 swaps its dirty skin for
-- the clean one: TownPortal0 (SetSprite 490) hides and TownPortal0Clean (491, the clean
-- altar at its place) shows; the map load does the same once the key is set (:Init FixCheck).
local function townPortalAltar()
    local clean = has(5011)
    evt.SetSprite(490, clean and 0 or 1, "0"); evt.SetSprite(491, clean and 1 or 0, "0")
end
handlers[331] = function()
    if has(5011) then return end
    MM9.giveKey(5011); quest()
    townPortalAltar()
    evt.StatusText("The altar is cleansed.")
end
handlers[332] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0) end   -- Book1 (Book.scr: pages turn, no text)
handlers[333] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0) end   -- Book2 (Book.scr: pages turn, no text)
handlers[334] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Invoice for services\n\nBrevan Ketilssen agrees to pay the sum of 400 gold for transportation of 10 lbs. of Elemental Thjorad.") end   -- Prop3 (424)
handlers[335] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Letter to Eloise\n\nMy dearest Eloise,\nI know your father forbids our relationship, but I find myself thinking of you day after day.  Please, I implore you.  Meet me at our field in Thjorgard.  I have made plans to spirit away to Sturmford to be married.\nMy undying love,\nHrolf") end   -- Prop4 (425)
handlers[336] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Invoice\n\n30 lbs Wheat                   10 gold\n100 Gallons Ale               60 gold\n35 Gallons Mead              20 gold\n10 lbs Assorted Nuts        10 gold\nTotal                              100 gold\nMoney due upon receipt.") end   -- Prop5 (427)
handlers[337] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Letter to Gunnar\n\nGunnar,\nBecause of your recent activities, and your constant refusal to join with the other Thjoradric Smiths, I'm afraid we are going to have to restrict your supply of Elemental Thjorad.  In addition, you will be paying an additional 20 gold per ounce.  You've been a good friend to me over the years, but this is business, and I've got the other Thjoradric Smiths to think of.  I'm sorry to do this, but you've forced my hand.\nAtli") end   -- Prop6 (428)
handlers[338] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Wanted\n\nFor the theft of 40 lbs of Elemental Thjorad.  Bjarni Gusmundssen.  50 gold reward.") end   -- Prop7 (429)
-- WellMMIX0: MM9's WellMMIX, its class's use (dungeon/objects.py bonus_call: the party's Endurance +5,
-- once).
handlers[339] = function() MM9.useWell(1765, 2, 2, 5, 0, 4) end

local function poll()
    shopHours()
    evt.StartTimer(260, seconds(1))
end
handlers[260] = poll
handlers[1] = function()   -- map load
    for k = 1024, 1033 do if k ~= 1025 and has(k) then MM9.takeKey(k) end end
    MM9.giveKey(1025)
    show(50, (not has(40)) or has(108))   -- NPC3.scr :Init (gone on 40 unless 108)
    show(21, not has(362))   -- NPC7.scr :Init: Hjarrand leaves once paid
    show(28, not has(450))   -- Retainer.scr: Hrolf Spearmaster, hidden while hired
    show(31, not has(452))   -- Retainer.scr: Arienh A'Klindor, hidden while hired
    show(54, not has(453))   -- RandverRetainer.scr: Randver, hidden while hired
    local thorolf = has(83) and not has(84)   -- NPC378.scr :Init (only Frosgard's third copy comes on 106)
    show(57, thorolf); show(58, thorolf)
    townPortalAltar()   -- TownPortal.scr :Init (FixCheck): the clean altar once its key is set
    evt.SetSprite(400, bookKeyShown() and 1 or 0, "0")   -- GreatBookKey.scr :Init
    poll()
end
-- MM9's approach talks (dungeon/lua.py approach_talk): an NPC whose script talks when the party comes
-- within 16 LT of his body (OnTargetWithinDist / RunTo 16 -> DoRude). reach: the feet's distance at which
-- he talks; sight > 0: he runs to the party once he sees it within that range. Once per visit.
local APPROACH_TALKS = {
    {actor = 57, reach = 109, sight = 1536, armed = function() return not has(107) and (not has(84) or has(106)) end,
        talk = function() MM9.removeActor(58); MM9.openRude(378, 57); MM9.playSound("voices/npc/npc_378.wav") end},   -- Thorolf0: NPC378.scr :OnFound RunTo 16 :Talk
    {actor = 58, reach = 109, sight = 1536, armed = function() return not has(107) and (not has(84) or has(106)) end,
        talk = function() MM9.removeActor(57); MM9.openRude(378, 58); MM9.playSound("voices/npc/npc_378.wav") end},   -- Thorolf1: NPC378.scr :OnFound RunTo 16 :Talk
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
handlers[54044] = function() MM9.playSound("voices/npc/npc_004.wav"); MM9.openRude(4) end   -- Johannes
handlers[54046] = function() MM9.playSound("voices/npc/npc_017.wav"); MM9.openRude(17) end   -- Hreidmar
handlers[54047] = function() MM9.playSound("voices/npc/npc_088.wav"); MM9.openRude(416) end   -- Harris
do local own = handlers[54048]; handlers[54048] = function() MM9.playSound("voices/npc/npc_013.wav"); own() end end   -- Ragnar
handlers[54064] = function() MM9.playSound("voices/npc/npc_021.wav"); MM9.openRude(21) end   -- ShopkeeperHuman2MaleA0
handlers[54065] = function() MM9.playSound("voices/npc/npc_020.wav"); MM9.openRude(20) end   -- ShopkeeperElfMaleA0
handlers[54066] = function() MM9.playSound("voices/npc/npc_007.wav"); MM9.openRude(7) end   -- ShopkeeperElfFemaleB8
handlers[54067] = function() MM9.playSound("voices/npc/npc_016.wav"); MM9.openRude(16) end   -- ShopkeeperElfFemaleB7
handlers[54068] = function() MM9.playSound("voices/npc/npc_006.wav"); MM9.openRude(6) end   -- ShopkeeperElfFemaleB6
handlers[54069] = function() MM9.playSound("voices/npc/npc_014.wav"); MM9.openRude(14) end   -- ShopkeeperElfFemaleB5
handlers[54070] = function() MM9.playSound("voices/npc/npc_019.wav"); MM9.openRude(19) end   -- ShopkeeperElfFemaleB4
handlers[54071] = function() MM9.playSound("voices/npc/npc_012.wav"); MM9.openRude(12) end   -- ShopkeeperElfFemaleB3
handlers[54072] = function() MM9.playSound("voices/npc/npc_015.wav"); MM9.openRude(15) end   -- ShopkeeperElfFemaleB2
handlers[54073] = function() MM9.playSound("voices/npc/npc_042.wav"); MM9.openRude(42) end   -- ShopkeeperElfFemaleB11
handlers[54074] = function() MM9.playSound("voices/npc/npc_010.wav"); MM9.openRude(10) end   -- ShopkeeperElfFemaleB0
handlers[54075] = function() MM9.playSound("voices/npc/npc_253.wav"); MM9.openRude(253) end   -- Hreidmar0
handlers[54076] = function() MM9.playSound("voices/npc/npc_044.wav"); MM9.openRude(44) end   -- ShopkeeperElfFemaleB10
do local own = handlers[54077]; handlers[54077] = function() MM9.playSound("voices/npc/npc_005.wav"); own() end end   -- ShopkeeperElfFemaleB1
handlers[54099] = function() MM9.playSound("voices/npc/npc_250.wav"); MM9.openRude(250) end   -- CommonerHumanFemaleA0
handlers[54100] = function() MM9.playSound("voices/npc/npc_251.wav"); MM9.openRude(251) end   -- CommonerHumanFemaleA1
handlers[54101] = function() MM9.playSound("voices/npc/npc_252.wav"); MM9.openRude(252) end   -- CommonerHumanFemaleA2
handlers[54102] = function() MM9.playSound("voices/npc/npc_085.wav"); MM9.openRude(85) end   -- ShopkeeperElfFemaleB12

-- MM9's bonus props (dungeon/objects.py bonus_lines; the use of each class, object.lto): wells, cauldrons,
-- cook pots and clovers.
handlers[31763] = function() MM9.useClover(1763, "thjorgardcity:Clover1") end   -- Clover1 (Clover)
handlers[31764] = function() MM9.useClover(1764, "thjorgardcity:Clover2") end   -- Clover2 (Clover)

-- MM9's PerceptionBrushes (dungeon/perception.py): the red glow shows to a party whose Perception reaches the
-- brush's PerceptionValue, checked on load and every 3 s; map Lua turns one off for good with
-- set("HintOff<cog>", 1) (MM9's Off message to the brush).
local HINTS = {[24020] = 1, [24021] = 1, [24022] = 1, [24023] = 1, [24024] = 1, [24025] = 1, [24026] = 1, [24027] = 1, [24028] = 1, [24029] = 1, [24030] = 1, [24031] = 1, [24032] = 1, [24033] = 1, [24034] = 1, [24035] = 1, [24036] = 1, [24037] = 1, [24038] = 1, [24039] = 1, [24040] = 1, [24041] = 1, [24042] = 1, [24043] = 1}
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
RegisterEvent(131, "Door", handlers[131], "Door")
RegisterEvent(132, "Door", handlers[132], "Door")
RegisterEvent(133, "Door", handlers[133], "Door")
RegisterEvent(134, "Door", handlers[134], "Door")
RegisterEvent(135, "Door", handlers[135], "Door")
RegisterEvent(136, "Door", handlers[136], "Door")
RegisterEvent(137, "Door", handlers[137], "Door")
RegisterEvent(138, "Door", handlers[138], "Door")
RegisterEvent(139, "Door", handlers[139], "Door")
RegisterEvent(140, "Door", handlers[140], "Door")
RegisterEvent(141, "Door", handlers[141], "Door")
RegisterEvent(142, "Door", handlers[142], "Door")
RegisterEvent(143, "Door", handlers[143], "Door")
RegisterEvent(144, "Door", handlers[144], "Door")
RegisterEvent(145, "Door", handlers[145], "Door")
RegisterEvent(146, "Door", handlers[146], "Door")
RegisterEvent(147, "Door", handlers[147], "Door")
RegisterEvent(148, "Door", handlers[148], "Door")
RegisterEvent(149, "Door", handlers[149], "Door")
RegisterEvent(150, "Door", handlers[150], "Door")
RegisterEvent(230, "Locked door", handlers[230], "Door")
RegisterEvent(54048, "Ragnar Gjalpssen", handlers[54048])
RegisterEvent(51048, "Bank", handlers[51048])
RegisterEvent(51044, "Johannes Bem", handlers[51044])
RegisterEvent(51058, "Tymon", handlers[51058])
RegisterEvent(54098, "Sven Forkbeard", handlers[54098])
RegisterEvent(51098, "Sven", handlers[51098])
RegisterEvent(54077, "Gunnar Thjorsmith", handlers[54077])
RegisterEvent(51077, "Gunnar", handlers[51077])
RegisterEvent(51066, "Hjarrand", handlers[51066])
RegisterEvent(54105, "Thorolf", handlers[54105])
RegisterEvent(51105, "Thorolf", handlers[51105])
RegisterEvent(54106, "Thorolf", handlers[54106])
RegisterEvent(51106, "Thorolf", handlers[51106])
RegisterEvent(330, "BookKey", handlers[330], "Book")
RegisterEvent(331, "TownPortal0", handlers[331], "Altar")
RegisterEvent(332, "Book1", handlers[332], "Book")
RegisterEvent(333, "Book2", handlers[333], "Book")
RegisterEvent(334, "Prop3", handlers[334], "Read")
RegisterEvent(335, "Prop4", handlers[335], "Read")
RegisterEvent(336, "Prop5", handlers[336], "Read")
RegisterEvent(337, "Prop6", handlers[337], "Read")
RegisterEvent(338, "Prop7", handlers[338], "Read")
RegisterEvent(339, "WellMMIX0", handlers[339], "Well")
RegisterMapTimerEvent(260, seconds(3), handlers[260], "Poll", "", seconds(3))
RegisterEvent(1, "Map load", handlers[1])
RegisterMapTimerEvent(906, seconds(3), handlers[906], "Approach talks", "", seconds(3))
RegisterEvent(54044, "Johannes Bem", handlers[54044])
RegisterEvent(54046, "Hreidmar the Fat", handlers[54046])
RegisterEvent(54047, "Harris Willington", handlers[54047])
RegisterEvent(54064, "Hal'an Swordstrong", handlers[54064])
RegisterEvent(54065, "Corcc A'Dorad", handlers[54065])
RegisterEvent(54066, "Hjarrand Fixer", handlers[54066])
RegisterEvent(54067, "Iosobail A'Tryht", handlers[54067])
RegisterEvent(54068, "Snorri the Fist", handlers[54068])
RegisterEvent(54069, "James the Berserk", handlers[54069])
RegisterEvent(54070, "Thora Ketilsdottir", handlers[54070])
RegisterEvent(54071, "Geirrod A'Ghrie", handlers[54071])
RegisterEvent(54072, "Muiredach A'Lanth", handlers[54072])
RegisterEvent(54073, "Hrolf Spearmaster", handlers[54073])
RegisterEvent(54074, "Sitheag A'Mor", handlers[54074])
RegisterEvent(54075, "Huber Carryall", handlers[54075])
RegisterEvent(54076, "Arienh A'Klindor", handlers[54076])
RegisterEvent(54099, "Bergthora the Pale", handlers[54099])
RegisterEvent(54100, "Cobthach the Elder", handlers[54100])
RegisterEvent(54101, "Fafnir Framissen", handlers[54101])
RegisterEvent(54102, "Randver Headcrusher", handlers[54102])
RegisterEvent(31763, "Clover", handlers[31763], "Pick")
RegisterEvent(31764, "Clover", handlers[31764], "Pick")
RegisterMapTimerEvent(901, seconds(3), handlers[901], "Perception hints", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
RegisterMonsterKilledHook(270, "Harris Willington", handlers[270])
