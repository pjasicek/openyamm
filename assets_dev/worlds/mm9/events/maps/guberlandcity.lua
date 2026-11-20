-- Guberland City, MM9 rework (level_generation/projects/mm9r_guberlandcity/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {["Apothdoor"] = 1, ["BankL"] = 2, ["BankR"] = 3, ["Bar"] = 4, ["Curtain"] = 5, ["Door0"] = 6, ["Door1"] = 7, ["Door10"] = 8, ["Door11"] = 9, ["Door12"] = 10, ["Door13"] = 11, ["Door14"] = 12, ["Door15"] = 13, ["Door16"] = 14, ["Door17"] = 15, ["Door18"] = 16, ["Door19"] = 17, ["Door2"] = 18, ["Door20"] = 19, ["Door21"] = 20, ["Door22"] = 21, ["Door23"] = 22, ["Door24"] = 23, ["Door25"] = 24, ["Door26"] = 25, ["Door27"] = 26, ["Door28"] = 27, ["Door29"] = 28, ["Door3"] = 29, ["Door30"] = 30, ["Door31"] = 31, ["Door32"] = 32, ["Door4"] = 33, ["Door6"] = 34, ["Door7"] = 35, ["Door8"] = 36, ["Door9"] = 37, ["Gate1L"] = 38, ["Gate1R"] = 39, ["Gate2L"] = 40, ["Gate2R"] = 41, ["Gate3L"] = 42, ["Gate3R"] = 43, ["Gate4L"] = 44, ["Gate4R"] = 45, ["Gate5L"] = 46, ["Gate5R"] = 47, ["Gate6L"] = 48, ["Gate6R"] = 49, ["Gate7L"] = 50, ["Gate7R"] = 51, ["Gate8L"] = 52, ["Gate8R"] = 53, ["Magidoor"] = 54, ["PalaceL"] = 55, ["PalaceR"] = 56, ["RotatingDoor0"] = 57, ["RotatingDoor1"] = 58, ["RotatingDoor10"] = 59, ["RotatingDoor11"] = 60, ["RotatingDoor12"] = 61, ["RotatingDoor13"] = 62, ["RotatingDoor16"] = 63, ["RotatingDoor17"] = 64, ["RotatingDoor19"] = 65, ["RotatingDoor2"] = 66, ["RotatingDoor20"] = 67, ["RotatingDoor3"] = 68, ["RotatingDoor4"] = 69, ["RotatingDoor7"] = 70, ["TavernL"] = 71, ["TavernR"] = 72, ["TempleL"] = 73, ["TempleR"] = 74, ["ThroneL"] = 75, ["ThroneR"] = 76}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 906, 902, 907}, onLeave = {}, timers = {}, openedChestIds = {}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(1, DoorAction.Trigger) end   -- Apothdoor
handlers[102] = function() evt.SetDoorState(2, DoorAction.Trigger) evt.SetDoorState(3, DoorAction.Trigger) end   -- BankL
handlers[103] = function() evt.SetDoorState(38, DoorAction.Trigger) evt.SetDoorState(39, DoorAction.Trigger) end   -- Gate1L
handlers[104] = function() evt.SetDoorState(40, DoorAction.Trigger) evt.SetDoorState(41, DoorAction.Trigger) end   -- Gate2L
handlers[105] = function() evt.SetDoorState(42, DoorAction.Trigger) evt.SetDoorState(43, DoorAction.Trigger) end   -- Gate3L
handlers[106] = function() evt.SetDoorState(44, DoorAction.Trigger) evt.SetDoorState(45, DoorAction.Trigger) end   -- Gate4L
handlers[107] = function() evt.SetDoorState(46, DoorAction.Trigger) evt.SetDoorState(47, DoorAction.Trigger) end   -- Gate5L
handlers[108] = function() evt.SetDoorState(48, DoorAction.Trigger) evt.SetDoorState(49, DoorAction.Trigger) end   -- Gate6L
handlers[109] = function() evt.SetDoorState(50, DoorAction.Trigger) evt.SetDoorState(51, DoorAction.Trigger) end   -- Gate7L
handlers[110] = function() evt.SetDoorState(52, DoorAction.Trigger) evt.SetDoorState(53, DoorAction.Trigger) end   -- Gate8L
handlers[111] = function() evt.SetDoorState(54, DoorAction.Trigger) end   -- Magidoor
handlers[112] = function() evt.SetDoorState(55, DoorAction.Trigger) evt.SetDoorState(56, DoorAction.Trigger) end   -- PalaceL
handlers[113] = function() evt.SetDoorState(57, DoorAction.Trigger) end   -- RotatingDoor0
handlers[114] = function() evt.SetDoorState(58, DoorAction.Trigger) end   -- RotatingDoor1
handlers[115] = function() evt.SetDoorState(59, DoorAction.Trigger) end   -- RotatingDoor10
handlers[116] = function() evt.SetDoorState(60, DoorAction.Trigger) end   -- RotatingDoor11
handlers[117] = function() evt.SetDoorState(63, DoorAction.Trigger) end   -- RotatingDoor16
handlers[118] = function() evt.SetDoorState(64, DoorAction.Trigger) end   -- RotatingDoor17
handlers[119] = function() evt.SetDoorState(65, DoorAction.Trigger) end   -- RotatingDoor19
handlers[120] = function() evt.SetDoorState(66, DoorAction.Trigger) end   -- RotatingDoor2
handlers[121] = function() evt.SetDoorState(67, DoorAction.Trigger) end   -- RotatingDoor20
handlers[122] = function() evt.SetDoorState(69, DoorAction.Trigger) end   -- RotatingDoor4
handlers[123] = function() evt.SetDoorState(70, DoorAction.Trigger) end   -- RotatingDoor7
handlers[124] = function() evt.SetDoorState(71, DoorAction.Trigger) evt.SetDoorState(72, DoorAction.Trigger) end   -- TavernL
handlers[125] = function() evt.SetDoorState(73, DoorAction.Trigger) evt.SetDoorState(74, DoorAction.Trigger) end   -- TempleL
handlers[126] = function() evt.SetDoorState(75, DoorAction.Trigger) evt.SetDoorState(76, DoorAction.Trigger) end   -- ThroneL

-- Chests (MM9 TreasureChest objects; loot records in the scene).

local function has(k) return MM9.hasKey(k) == 1 end
local function quest() MM9.playSound("sounds/events/quest.wav") end
local function show(a, on) evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end
local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; if gold > 0 then MM9.giveGold(gold) end; quest() end
-- GivePromo <class>: every eligible member at once (MM9.promoteParty: the quest -> class-line table; MM9's
-- per-character keys are not used: devdocs/mm9/MM9_RUDE_SCR_INTEGRATION.md "Promotions And Classes")
local function promote(class, first) MM9.promoteParty(class) end

-- MM9's locked doors (Locked 1, no key): the 34 facade doors and the two locked smithy doors.
handlers[230] = function()
    evt.PlaySoundName("door/doorlock01.wav", 0, 0, 0)
    evt.StatusText("The door is locked.")
end
-- RotatingDoor3: Nutty Nurtigan's sickroom (Locked 1, Sticky). NPC142.scr unlocks it when the apothecary
-- hands over the potion (key 373); NPC131.scr opens it once he is cured (key 211).
handlers[231] = function()
    if has(373) or has(211) then evt.SetDoorState(DOORS["RotatingDoor3"], DoorAction.Trigger)
    else handlers[230]() end
end

-- ForadWorld.scr (ScriptObject0, "Guberland"): key 1028 is the party's location while here (keys
-- 1024-1033 are the towns'); key 5017 closes the shops from 20:00 to 06:00 (their dialogues forbid or require it).
local function shopHours()
    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24
    local closed = hour >= 20 or hour < 6
    if closed and not has(5017) then MM9.giveKey(5017) elseif not closed and has(5017) then MM9.takeKey(5017) end
end

-- The bar's flap and the stage curtain: a click opens or shuts them.
handlers[240] = function() evt.SetDoorState(DOORS["Bar"], DoorAction.Trigger) end   -- Bar
handlers[241] = function() evt.SetDoorState(DOORS["Curtain"], DoorAction.Trigger) end   -- Curtain

-- The eight quarter gates (Gate<n>L/R, linear Doors sliding 120 LT): MM9's Gate<n>trigger boxes (128 LT each way
-- round the gate) toggle the pair once (and turn themselves off); here a 0.25 s poll opens a shut gate whenever
-- the party stands in its box. A click toggles a gate as any door.
local GATES = {{"Gate1", -6594, -5858, -9051, -8316}, {"Gate2", 4548, 5283, -10034, -9299}, {"Gate3", -6594, -5858, -10034, -9299}, {"Gate4", 4548, 5283, -9051, -8316}, {"Gate5", -1515, -779, -3317, -2581}, {"Gate6", -532, 204, -4791, -4056}, {"Gate7", -532, 204, -13966, -13231}, {"Gate8", -1515, -779, -15441, -14706}}
local function gates()
    local x, y = evt.GetPartyPosition()
    for _, g in ipairs(GATES) do
        if x >= g[2] and x <= g[3] and y >= g[4] and y <= g[5] then
            if var(g[1] .. "Open") == 0 then
                set(g[1] .. "Open", 1)
                open(g[1] .. "L"); open(g[1] .. "R")
            end
        elseif var(g[1] .. "Open") == 1 then
            set(g[1] .. "Open", 0)   -- re-armed once the party has left the box
        end
    end
end
handlers[261] = function() gates(); evt.StartTimer(261, seconds(0.25)) end

-- BankOrb.scr (Ottar Gizurssen, RUDE 140: nKey 332, nKey2 326): the Orb of Linking. A click with the
-- orb (item 252) after the quest (key 322) unlocks the row that installs it (key 330); the exit places it and the
-- sixth bank's orb pays 20 000 experience and 15 000 gold (key 337; banks' keys 331-336).
handlers[53814] = function()
    if not has(326) and has(322) and MM9.hasItem(252, "guberlandcity:Ottar") == 1 then MM9.giveKey(330) end
    MM9.openRude(140)
end
handlers[50814] = function()
    if not has(330) then return end
    MM9.takeKey(330)
    if not has(332) then return end
    quest(); MM9.takeItem(252, "guberlandcity:Ottar"); MM9.giveKey(326)
    if has(337) then return end
    for k = 331, 336 do if not has(k) then return end end
    reward(337, 12500, 15000) -- MM9 GiveExp 20000, mm9_quest_xp_profile.yml
end

-- NPC127.scr (Markel the Great, the Jarl, RUDE 127; United.inc). The click: the five clans (82, 38, 51, 34, 74
-- -> 178). The exit: the Book of Rules (61 -> 167, 10 000 experience, 3 000 gold, item 391 taken), Ivan the Smart
-- (62 -> 165, 26 000, 3 000, item 400 taken), the Dook (66 -> 168, 40 000, 3 000), the clans united (83 -> 179,
-- 26 500, 6 000). Hidden on 40 unless 108.
handlers[53815] = function()
    if not has(178) then
        local n = 0
        for _, k in ipairs({82, 38, 51, 34, 74}) do if has(k) then n = n + 1 end end
        if n == 5 then MM9.giveKey(178) end
    end
    MM9.openRude(127)
end
handlers[50815] = function()
    if not has(167) and has(61) then reward(167, 10000, 3000); MM9.takeItem(391, "guberlandcity:Markel") end
    if not has(165) and has(62) then reward(165, 16500, 3000); MM9.takeItem(400, "guberlandcity:Markel") end -- MM9 GiveExp 26000, mm9_quest_xp_profile.yml
    if not has(168) and has(66) then reward(168, 12500, 3000) end -- MM9 GiveExp 40000, mm9_quest_xp_profile.yml
    if not has(179) and has(83) then MM9.giveKey(179); MM9.giveExperience(12500); MM9.giveGold(6000) end -- MM9 GiveExp 26500, mm9_quest_xp_profile.yml
end

-- NPC128.scr (Tjolnir the Super-neat, RUDE 128): Initiate to Healer. :Promocheck: a character holding 437-440
-- gives 206 (MM9's engine set those keys from the class check of "We are seeking promotion from Initiate to
-- Healer", code 2083, kept as key 2083; here: that row asked, whoever is in the party: every promotion quest is
-- offered to any party, the user 2026-11-08, dialogue/promotions.yml). With Nurtigan cured (212) and not 213:
-- 24 500 experience, 1 000 gold, key 213, the promotion of the members eligible.
handlers[50813] = function()
    if not has(206) and has(2083) then MM9.giveKey(206) end
    if not has(213) and has(212) then reward(213, 16500, 1000); promote("Healer", 437) end -- MM9 GiveExp 24500, mm9_quest_xp_profile.yml
end

-- NPC129.scr (Gray Slemnir, RUDE 129): Healer to Priest. :Givequest: a character holding 441-444 gives the quest
-- keys 250, 251, 252 (the class check of "We are seeking promotion", code 2084, kept as key 2084; here: that
-- row asked, whoever is in the party). With 260 and not 261: 63 000 experience, 5 000 gold, key 261, items 241
-- and 430 taken, the promotion of the members eligible.
handlers[50811] = function()
    if not has(250) and has(2084) then
        MM9.giveKey(250); MM9.giveKey(251); MM9.giveKey(252)
    end
    if not has(261) and has(260) then
        reward(261, 37500, 5000); MM9.takeItem(241, "guberlandcity:Gray"); MM9.takeItem(430, "guberlandcity:Gray") -- MM9 GiveExp 63000, mm9_quest_xp_profile.yml
        promote("Priest", 441)
    end
end

-- NPC141.scr (the tavern keeper, RUDE 141): the keg delivered (304, not 306): key 306, item 249 taken, 500 gold,
-- 5 000 experience.
handlers[50836] = function()
    if not has(306) and has(304) then reward(306, 5000, 500); MM9.takeItem(249, "guberlandcity:Tavern") end
end

-- NPC142.scr (Skarphedinn Njalssen, the apothecary, RUDE 142). The click: with item 240 and key 206, key 207.
-- The exit: with 208 item 240 is taken and the potion is ready two game hours later (key 209); with 210 and not
-- 373 the sickroom door (RotatingDoor3) is unlocked, item 558 given, key 373.
handlers[53821] = function()
    if MM9.hasItem(240, "guberlandcity:Skarphedinn") == 1 and has(206) then MM9.giveKey(207) end
    MM9.openRude(142)
end
handlers[50821] = function()
    if has(208) and not has(209) and var("PotionReadyAt") == 0 then
        MM9.takeItem(240, "guberlandcity:Skarphedinn")
        set("PotionReadyAt", math.floor(evt.CurrentGameMinutes()) + 120)
    end
    if has(210) and not has(373) then
        MM9.giveItem(558, "guberlandcity:Skarphedinn"); MM9.giveKey(373); quest()
    end
end

-- NPC131.scr (Nutty Nurtigan, RUDE 131, in his sickroom): cured (211) with the potion (item 558) on the dialogue's
-- close, the potion is taken and he leaves the sickroom (MM9 walks him to Marker0 and wanders; here the door
-- opens and he stays). On load with 211 the door stands open.
handlers[50871] = function()
    if has(211) and MM9.hasItem(558, "guberlandcity:Nurtigan") == 1 then
        MM9.takeItem(558, "guberlandcity:Nurtigan"); open("RotatingDoor3")
    end
end

-- NPC378.scr (Thorolf Ratatoskssen, two copies, RUDE 378): the messenger. Talking to one removes the other; after
-- the message (key 84) or the summons (key 107) he vanishes by town portal; with 83 or 106 alone the dialogue
-- reopens (it cannot be skipped).
handlers[53837] = function() MM9.removeActor(35); MM9.openRude(378) end
handlers[50837] = function()
    if has(107) or has(84) then MM9.clientFx(34, "mm9:town_portal"); MM9.removeActor(34); MM9.removeActor(35)
    elseif has(106) or has(83) then MM9.openRude(378) end
end
handlers[53838] = function() MM9.removeActor(34); MM9.openRude(378) end
handlers[50838] = function()
    if has(107) or has(84) then MM9.clientFx(35, "mm9:town_portal"); MM9.removeActor(35); MM9.removeActor(34)
    elseif has(106) or has(83) then MM9.openRude(378) end
end

-- BookLetter.scr letters (BOOK AND SCROLL TEXT.csv rows), Book.scr (no text in MM9), TownPortal.scr, the well.
handlers[330] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("The Guberland Players\n\nNow Presenting:\nThe Death of Emperor Trislan\n2:30 and 4:30 daily") end   -- Prop1 (569)
handlers[331] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0) end   -- Book1 (Book.scr: pages turn, no text)
handlers[332] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Awards Won by Markel\n\nAll these awards were won at The Gathering by Markel the Great, fair and square!") end   -- Sign4 (578)
-- TownPortal0: TownPortal.scr "Guberland": cleansing the altar gives key 5014 and MM9 swaps its dirty skin for
-- the clean one: TownPortal0 (SetSprite 490) hides and TownPortal0Clean (491, the clean
-- altar at its place) shows; the map load does the same once the key is set (:Init FixCheck).
local function townPortalAltar()
    local clean = has(5014)
    evt.SetSprite(490, clean and 0 or 1, "0"); evt.SetSprite(491, clean and 1 or 0, "0")
end
handlers[333] = function()
    if has(5014) then return end
    MM9.giveKey(5014); quest()
    townPortalAltar()
    evt.StatusText("The altar is cleansed.")
end
-- Well0: MM9's WellMMIX, its class's use (dungeon/objects.py bonus_call).
handlers[334] = function() MM9.useWell(746, 2, 4, 5, 0, 4) end
handlers[335] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Letter to Sevanna\n\nMy dearest Sevanna,\nI had the most wonderful time last night.  Maybe I'm too soft for a warrior, but I have always been fond of the moonlit walks on the sand.  I hope it wasn't too much of a bother that I had to unlock my eyes from yours to slay that sea monster.  I'm also sorry I accidentally landed some of its ichor on your dress.  \n\nWith all the hope in the world that I shall see you tomorrow,\nNurtigan") end   -- Prop5 (459)
handlers[336] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Letter to Nurtigan\n\nSweet Nurtigan,\nOur date yesterday was wonderful.  I really loved the way you dispatched that Nagate without even having to draw your sword.  Your skill with the sword is unmatched.  Please, feel free to call on me at any time.\n\nYour sweetkins,\nLoriana") end   -- Prop6 (460)
handlers[337] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Be it Known\n\nYour true dook has arrived.  Fealty oaths shall be happily accepted throughout the summer and autumn.  If you wish, you may donate money at the front gate of the Dook's castle.") end   -- Prop7 (461)

-- Markel's awards (Prize0-5 on the shelf of his hall; Sign4: "Awards Won by Markel ... at The Gathering"): the
-- Thing's Stuffed Dragon (item 395). MM9 has them as set dressing; here they are world items taken once Markel is
-- dead (key 40, dungeon/pickups.py), an OpenYAMM way past the Thing's games on Yrsa's errand: the first taken
-- while the errand runs (93, not 94) counts as the prize won (94: Bikki takes it, the Jarls leave the council).
-- No experience: the Thing's 10 000 is for winning its games.
handlers[250] = function()
    if has(93) and not has(94) then
        MM9.giveKey(94); quest()
        evt.StatusText("Markel the Great will not miss one of his prizes.")
    end
end

-- The players' cues (Narrator.scr, Trislan.scr, Abriel.scr, Wilam.scr, Ralof.scr, Leffery.scr): walks, faces
-- and clips at THEPLAY.scr's times from the first line (convert.py citylua.play_cues). A walk's arrival
-- (EV_ARRIVE + k) runs what MM9 does there: faces whom it targets, and the slap.
local P = {Narrator = 0, Wilam = 1, Trislan = 2, Abriel = 3, Ralof = 4, Leffery = 5}
local ARRIVAL = {Narrator = 270, Wilam = 271, Trislan = 272, Abriel = 273, Ralof = 274, Leffery = 275}
local MARKS = {Trislan1 = {-2580, -3830, 82}, Trislan2 = {-2294, -3707, 82}, Trislan3 = {-2560, -3912, 82}, Abriel1 = {-2621, -3748, 82}, Abriel2 = {-2294, -3584, 82}, Abriel3 = {-2458, -3789, 82}, Abriel4 = {-2437, -3912, 82}, Ralof1 = {-2744, -3871, 82}, Ralof2 = {-2949, -3748, 82}, Ralof3 = {-2683, -3912, 82}, Wilam1 = {-2744, -3584, 82}, Wilam2 = {-2744, -3789, 82}, Wilam3 = {-2949, -3666, 82}, Wilam4 = {-2949, -3912, 82}, Leffery1 = {-2499, -3666, 82}, Leffery2 = {-2949, -3584, 82}, Leffery3 = {-2826, -3912, 82}, peasant2 = {-2565, -4608, 0}}
local HOME = {Narrator = {-2335, -3871, 83}, Wilam = {-2949, -3666, 83}, Trislan = {-2294, -3707, 83}, Abriel = {-2294, -3584, 83}, Ralof = {-2949, -3748, 83}, Leffery = {-2949, -3584, 83}}
local function place(name)
    if P[name] then return evt.GetMapActorPosition(P[name]) end
    local m = MARKS[name]
    return m[1], m[2], m[3]
end
local function loop(who, clip) evt.PlayActorClip(P[who], clip, true) end
local function stop(who) evt.PlayActorClip(P[who], "") end
local function face(who, name)
    local x, y = place(name)
    if x ~= nil then evt.FaceActorTo(P[who], x, y, 0.4) end
end
local function sound(name, who)
    local x, y, z = place(who)
    if x ~= nil then evt.PlaySoundName(name, math.floor(x), math.floor(y), math.floor(z)) end
end
local onArrival = {}
local function walk(who, name, arrive)
    local x, y, z = place(name)
    if x == nil then return end
    evt.ClearActorPresentation(P[who])
    onArrival[who] = arrive
    evt.MoveActorTo(P[who], x, y, z, ARRIVAL[who])
end
local function arrived(who)
    local f = onArrival[who]
    onArrival[who] = nil
    if f ~= nil and var("PlayLine") > 0 then f() end
end
handlers[270] = function() arrived("Narrator") end
handlers[271] = function() arrived("Wilam") end
handlers[272] = function() arrived("Trislan") end
handlers[273] = function() arrived("Abriel") end
handlers[274] = function() arrived("Ralof") end
handlers[275] = function() arrived("Leffery") end
local CUES = {
    {0.00, function()
        loop("Narrator", "conv2")
    end},
    {6.09, function()
        loop("Narrator", "conv3")
        face("Narrator", "Abriel1")
        walk("Trislan", "Trislan1", function() face("Trislan", "Abriel") end)
        walk("Abriel", "Abriel1", function() face("Abriel", "Trislan") end)
    end},
    {11.08, function()
        stop("Narrator")
        loop("Trislan", "conv1")
    end},
    {17.26, function()
        stop("Trislan")
        loop("Abriel", "conv2")
    end},
    {30.44, function()
        stop("Abriel")
        loop("Trislan", "conv3")
    end},
    {34.10, function()
        stop("Trislan")
        loop("Abriel", "conv2")
    end},
    {44.32, function()
        stop("Abriel")
        loop("Trislan", "conv3")
    end},
    {47.53, function()
        stop("Trislan")
        loop("Abriel", "conv2")
    end},
    {51.55, function()
        stop("Abriel")
        loop("Narrator", "conv3")
        walk("Trislan", "Trislan2", function() face("Trislan", "Wilam") end)
        walk("Abriel", "Abriel2", function() face("Abriel", "Wilam") end)
        walk("Ralof", "Ralof1", function() face("Ralof", "Wilam") end)
        walk("Wilam", "Wilam1")
        walk("Leffery", "Leffery1", function() face("Leffery", "Ralof") end)
    end},
    {55.55, function()
        stop("Narrator")
    end},
    {56.26, function()
        loop("Wilam", "conv2")
    end},
    {57.26, function()
        walk("Wilam", "Wilam2", function() face("Wilam", "Ralof"); loop("Wilam", "conv3") end)
    end},
    {63.20, function()
        stop("Wilam")
        face("Ralof", "Wilam")
        loop("Ralof", "conv1")
    end},
    {72.47, function()
        stop("Ralof")
        loop("Leffery", "conv2")
    end},
    {74.27, function()
        stop("Leffery")
        face("Ralof", "Leffery")
        loop("Ralof", "conv1")
    end},
    {79.27, function()
        face("Ralof", "Wilam")
        loop("Ralof", "conv2")
    end},
    {94.39, function()
        stop("Ralof")
        stop("Wilam")
        walk("Abriel", "Ralof", function() face("Abriel", "Ralof"); evt.PlayActorClip(P.Abriel, {"attack_melee", "conv2"}, true); evt.PlayActorClip(P.Ralof, {"hit"}, false); sound("weapons/fleshhit03.wav", "Ralof") end)
    end},
    {115.15, function()
        stop("Abriel")
        loop("Ralof", "conv1")
    end},
    {119.60, function()
        stop("Ralof")
        loop("Narrator", "conv1")
    end},
    {123.60, function()
        stop("Narrator")
        walk("Abriel", "Abriel2", function() face("Abriel", "Wilam") end)
        walk("Ralof", "Ralof2", function() face("Ralof", "Trislan") end)
        walk("Wilam", "Wilam3", function() face("Wilam", "Trislan") end)
        walk("Leffery", "Leffery2", function() face("Leffery", "Trislan") end)
    end},
    {124.24, function()
        loop("Narrator", "conv1")
        walk("Trislan", "Trislan1", function() face("Trislan", "Ralof") end)
    end},
    {125.24, function()
        walk("Abriel", "Abriel3", function() face("Abriel", "Ralof") end)
    end},
    {129.42, function()
        stop("Narrator")
        face("Trislan", "Ralof")
        loop("Trislan", "conv2")
    end},
    {129.74, function()
        walk("Ralof", "Trislan", function() face("Ralof", "Trislan") end)
    end},
    {130.74, function()
        walk("Leffery", "Wilam2", function() face("Leffery", "Trislan") end)
        walk("Wilam", "Ralof1", function() face("Wilam", "Trislan") end)
    end},
    {132.14, function()
        stop("Trislan")
        loop("Ralof", "conv4")
    end},
    {138.06, function()
        stop("Ralof")
        loop("Trislan", "conv2")
    end},
    {141.96, function()
        stop("Trislan")
        loop("Ralof", "conv1")
    end},
    {144.96, function()
        stop("Ralof")
        evt.PlayActorClip(P.Ralof, {"attack_melee"}, false)
    end},
    {145.56, function()
        sound("weapons/fleshhit04.wav", "Trislan")
    end},
    {145.73, function()
        evt.PlayActorClip(P.Trislan, {"play_death", "play_getup"}, false)
    end},
    {149.60, function()
        loop("Narrator", "conv3")
        face("Narrator", "peasant2")
    end},
    {162.60, function()
        walk("Ralof", "Ralof3", function() face("Ralof", "peasant2") end)
        walk("Wilam", "Wilam4", function() face("Wilam", "peasant2") end)
        walk("Leffery", "Leffery3", function() face("Leffery", "peasant2") end)
        walk("Abriel", "Abriel4", function() face("Abriel", "peasant2") end)
        walk("Trislan", "Trislan3", function() face("Trislan", "peasant2") end)
    end},
    {163.82, function()
        loop("Narrator", "conv3")
    end},
    {164.82, function()
        stop("Narrator")
        evt.PlayActorClip(P.Wilam, {"bow"}, false)
        evt.PlayActorClip(P.Leffery, {"bow"}, false)
        evt.PlayActorClip(P.Abriel, {"bow"}, false)
        evt.PlayActorClip(P.Trislan, {"bow"}, false)
    end},
    {174.29, function()
        walk("Trislan", "Trislan2", function() face("Trislan", "Wilam") end)
        walk("Abriel", "Abriel2", function() face("Abriel", "Wilam") end)
        walk("Ralof", "Ralof2", function() face("Ralof", "Trislan") end)
        walk("Wilam", "Wilam3", function() face("Wilam", "Trislan") end)
        walk("Leffery", "Leffery2", function() face("Leffery", "Trislan") end)
    end},
}
local cue = 0
local function playCues(delay)
    cue = 1
    evt.StartTimer(263, seconds(delay + CUES[1][1]))
end
handlers[263] = function()
    evt.StopTimer(263)
    if cue < 1 or cue > #CUES then return end
    if var("PlayLine") == 0 then cue = 0 return end   -- the show stopped
    local at = CUES[cue][1]
    CUES[cue][2]()
    cue = cue + 1
    if cue <= #CUES then evt.StartTimer(263, seconds(CUES[cue][1] - at)) else cue = 0 end
end
local function playersHome()   -- a show left half-way: the players back at their places
    for who, p in pairs(HOME) do
        evt.ClearActorPresentation(P[who])
        evt.SetMapActorPosition(P[who], p[1], p[2], p[3])
    end
end

-- The Guberland Players' show (Narrator.scr @m 14:30 and 16:30; the lines and their timing from THEPLAY.scr):
-- the curtain opens, each line plays at its speaker's place on the stage, the curtain closes after the bow.
-- PlayLine: the next line (0: no show); PlayDue guards the repeating timer. A row's `to`: the players'
-- messages that must reach a living receiver (MM9.receives) for it to play; else the show stops there, the
-- curtain open (MM9's chain never reaches the Narrator's :Exit), except a `side` line, which stays silent.
local PLAY = {
    {"voices/cinema/guberlandplay/01.wav", -2335, -3871, 205, 6.09},   -- narrator
    {"voices/cinema/guberlandplay/02.wav", -2335, -3871, 205, 4.99},   -- narrator
    {"voices/cinema/guberlandplay/03.wav", -2294, -3707, 205, 6.18, to = {{"Trislan", 2, "Walk1"}}},   -- trislan
    {"voices/cinema/guberlandplay/04.wav", -2294, -3584, 205, 13.18, to = {{"Abriel", 3, "Speak4"}}},   -- abriel
    {"voices/cinema/guberlandplay/05.wav", -2294, -3707, 205, 3.66, to = {{"Trislan", 2, "Speak5"}}},   -- trislan
    {"voices/cinema/guberlandplay/06.wav", -2294, -3584, 205, 10.22, to = {{"Abriel", 3, "Speak6"}}},   -- abriel
    {"voices/cinema/guberlandplay/07.wav", -2294, -3707, 205, 3.21, to = {{"Trislan", 2, "Speak7"}}},   -- trislan
    {"voices/cinema/guberlandplay/08.wav", -2294, -3584, 205, 4.02, to = {{"Abriel", 3, "Speak8"}}},   -- abriel
    {"voices/cinema/guberlandplay/09.wav", -2335, -3871, 205, 4.71, to = {{"Narrator", 0, "Speak9"}}},   -- narrator
    {"voices/cinema/guberlandplay/10.wav", -2949, -3666, 205, 6.94, to = {{"Wilam", 1, "Speak9"}}},   -- wilam
    {"voices/cinema/guberlandplay/11.wav", -2949, -3748, 205, 9.27, to = {{"Ralof", 4, "Speak11"}}},   -- ralof
    {"voices/cinema/guberlandplay/12.wav", -2949, -3584, 205, 1.8, to = {{"Leffery", 5, "Speak12"}}},   -- leffery
    {"voices/cinema/guberlandplay/13b.wav", -2949, -3748, 205, 20.12, to = {{"Ralof", 4, "Speak13"}}},   -- ralof
    {"voices/cinema/guberlandplay/14.wav", -2949, -3584, 205, 0.65, to = {{"Leffery", 5, "Speak14"}}, side = true},   -- leffery
    {"voices/cinema/guberlandplay/15.wav", -2294, -3584, 205, 3.1, to = {{"Abriel", 3, "Speak14"}}},   -- abriel
    {"voices/cinema/guberlandplay/16.wav", -2949, -3748, 205, 1.8, to = {{"Ralof", 4, "Speak16"}}},   -- ralof
    {"voices/cinema/guberlandplay/17.wav", -2294, -3584, 205, 6.85, to = {{"Abriel", 3, "Speak17"}}},   -- abriel
    {"voices/cinema/guberlandplay/18.wav", -2949, -3748, 205, 1.46, to = {{"Ralof", 4, "Speak18"}}},   -- ralof
    {"voices/cinema/guberlandplay/19.wav", -2294, -3584, 205, 6.9, to = {{"Abriel", 3, "Speak19"}}},   -- abriel
    {"voices/cinema/guberlandplay/20.wav", -2949, -3748, 205, 4.45, to = {{"Ralof", 4, "Speak20"}}},   -- ralof
    {"voices/cinema/guberlandplay/21.wav", -2335, -3871, 205, 4.64, to = {{"Narrator", 0, "Speak21"}}},   -- narrator
    {"voices/cinema/guberlandplay/22.wav", -2335, -3871, 205, 5.18, to = {{"Abriel", 3, "Exit"}, {"Narrator", 0, "Speak22"}}},   -- narrator
    {"voices/cinema/guberlandplay/23.wav", -2294, -3707, 205, 2.72, to = {{"Ralof", 4, "Walk2"}, {"Trislan", 2, "Speak23"}}},   -- trislan
    {"voices/cinema/guberlandplay/24.wav", -2949, -3748, 205, 5.92, to = {{"Ralof", 4, "Speak24"}}},   -- ralof
    {"voices/cinema/guberlandplay/25.wav", -2294, -3707, 205, 3.9, to = {{"Trislan", 2, "Speak25"}}},   -- trislan
    {"voices/cinema/guberlandplay/26.wav", -2949, -3748, 205, 3.77, to = {{"Ralof", 4, "Speak26"}}},   -- ralof
    {"voices/cinema/guberlandplay/27a.wav", -2294, -3707, 205, 3.87, to = {{"Trislan", 2, "Die"}}},   -- trislan
    {"voices/cinema/guberlandplay/27.wav", -2335, -3871, 205, 14.22, to = {{"Narrator", 0, "Speak27"}}},   -- narrator
    {"voices/cinema/guberlandplay/28.wav", -2335, -3871, 205, 5.97},   -- narrator
}
local function playReaches(line)
    for _, m in ipairs(line.to or {}) do
        if not MM9.receives("guberlandcity", m[1], m[3], m[2]) then return false end
    end
    return true
end
local PLAY_STARTS = {[870] = true, [990] = true}
local function playCurtain(open) evt.SetDoorState(DOORS["Curtain"], open and DoorAction.Open or DoorAction.Close) end
local function playNext(delay)
    set("PlayDue", 1)
    evt.StartTimer(262, seconds(delay))
end
handlers[262] = function()
    evt.StopTimer(262)
    if var("PlayDue") ~= 1 then return end
    set("PlayDue", 0)
    local i = var("PlayLine")
    if i < 1 then return end
    if i > #PLAY then set("PlayLine", 0); playCurtain(false) return end   -- the bow is over
    local line = PLAY[i]
    if playReaches(line) then evt.PlaySoundName(line[1], line[2], line[3], line[4])
    elseif not line.side then set("PlayLine", 0) return end
    set("PlayLine", i + 1)
    playNext(i < #PLAY and line[5] or line[5] + 5)
end
local function playSchedule()
    local now = math.floor(evt.CurrentGameMinutes())
    if PLAY_STARTS[now % 1440] and var("PlayLine") == 0 and var("PlayStartedAt") ~= now then
        set("PlayStartedAt", now)
        set("PlayShows", var("PlayShows") + 1)
        set("PlayLine", 1)
        playCurtain(true)
        playNext(2)
        playCues(2)
    end
end

local function poll()
    shopHours()
    playSchedule()
    local ready = var("PotionReadyAt")   -- NPC142.scr :Givekey (@m two hours after the order)
    if ready > 0 and evt.CurrentGameMinutes() >= ready then set("PotionReadyAt", 0); MM9.giveKey(209) end
    evt.StartTimer(260, seconds(1))
end
handlers[260] = poll
handlers[1] = function()   -- map load
    for k = 1024, 1033 do if k ~= 1028 and has(k) then MM9.takeKey(k) end end
    MM9.giveKey(1028)
    show(13, (not has(40)) or has(108))   -- NPC127.scr :Init (gone on 40 unless 108)
    show(21, not has(457))   -- Retainer.scr (457): hidden while hired
    show(22, not has(459))   -- Retainer.scr (459): hidden while hired
    local thorolf = has(83) and not has(84)   -- NPC378.scr :Init (only Frosgard's third copy comes on 106)
    show(34, thorolf); show(35, thorolf)
    if has(211) then open("RotatingDoor3") end   -- NPC131.scr :Init: Nurtigan cured, the door open
    townPortalAltar()   -- TownPortal.scr :Init (FixCheck): the clean altar once its key is set
    if var("PlayLine") > 0 then set("PlayLine", 0); playCurtain(false); playersHome() end   -- a show left half-way
    poll()
    handlers[261]()
end
-- MM9's approach talks (dungeon/lua.py approach_talk): an NPC whose script talks when the party comes
-- within 16 LT of his body (OnTargetWithinDist / RunTo 16 -> DoRude). reach: the feet's distance at which
-- he talks; sight > 0: he runs to the party once he sees it within that range. Once per visit.
local APPROACH_TALKS = {
    {actor = 34, reach = 109, sight = 1536, armed = function() return not has(107) and (not has(84) or has(106)) end,
        talk = function() MM9.removeActor(35); MM9.openRude(378, 34); MM9.playSound("voices/npc/npc_378.wav") end},   -- Thorolf0: NPC378.scr :OnFound RunTo 16 :Talk
    {actor = 35, reach = 109, sight = 1536, armed = function() return not has(107) and (not has(84) or has(106)) end,
        talk = function() MM9.removeActor(34); MM9.openRude(378, 35); MM9.playSound("voices/npc/npc_378.wav") end},   -- Thorolf1: NPC378.scr :OnFound RunTo 16 :Talk
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
handlers[53811] = function() MM9.playSound("voices/npc/npc_129.wav"); MM9.openRude(129) end   -- ShopkeeperHuman2MaleA2
handlers[53812] = function() MM9.playSound("voices/npc/npc_143.wav"); MM9.openRude(143) end   -- ShopkeeperHuman2MaleA0
handlers[53813] = function() MM9.playSound("voices/npc/npc_128.wav"); MM9.openRude(128) end   -- ShopkeeperHuman2MaleA1
do local own = handlers[53814]; handlers[53814] = function() MM9.playSound("voices/npc/npc_140.wav"); own() end end   -- ShopkeeperHuman2MaleA7
do local own = handlers[53815]; handlers[53815] = function() MM9.playSound("voices/npc/npc_127.wav"); own() end end   -- MarkeltheGreat0
handlers[53816] = function() MM9.playSound("voices/npc/npc_147.wav"); MM9.openRude(147) end   -- ShopkeeperHuman2MaleA10
handlers[53817] = function() MM9.playSound("voices/npc/npc_146.wav"); MM9.openRude(146) end   -- ShopkeeperHuman2MaleA11
handlers[53818] = function() MM9.playSound("voices/npc/npc_134.wav"); MM9.openRude(134) end   -- ShopkeeperHuman2MaleA4
handlers[53819] = function() MM9.playSound("voices/npc/npc_135.wav"); MM9.openRude(135) end   -- ShopkeeperHuman2MaleA5
handlers[53820] = function() MM9.playSound("voices/npc/npc_137.wav"); MM9.openRude(137) end   -- ShopkeeperHuman2MaleA6
do local own = handlers[53821]; handlers[53821] = function() MM9.playSound("voices/npc/npc_142.wav"); own() end end   -- ShopkeeperHuman2MaleA8
handlers[53822] = function() MM9.playSound("voices/npc/npc_145.wav"); MM9.openRude(145) end   -- ShopkeeperHuman2MaleA9
handlers[53823] = function() MM9.playSound("voices/npc/npc_177.wav"); MM9.openRude(177) end   -- ShopkeeperHuman2MaleA12
handlers[53824] = function() MM9.playSound("voices/npc/npc_179.wav"); MM9.openRude(179) end   -- ShopkeeperHuman2MaleA13
handlers[53836] = function() MM9.playSound("voices/npc/npc_141.wav"); MM9.openRude(141) end   -- ShopkeeperHalfOrcFemaleA
handlers[53871] = function() MM9.playSound("voices/npc/npc_131.wav"); MM9.openRude(131) end   -- CommonerHumanMaleA0

-- MM9's bonus props (dungeon/objects.py bonus_lines; the use of each class, object.lto): wells, cauldrons,
-- cook pots and clovers.
handlers[30899] = function() MM9.useClover(899, "guberlandcity:Clover0") end   -- Clover0 (Clover)
handlers[30900] = function() MM9.useClover(900, "guberlandcity:Clover1") end   -- Clover1 (Clover)

-- MM9's PerceptionBrushes (dungeon/perception.py): the red glow shows to a party whose Perception reaches the
-- brush's PerceptionValue, checked on load and every 3 s; map Lua turns one off for good with
-- set("HintOff<cog>", 1) (MM9's Off message to the brush).
local HINTS = {[23876] = 1, [23877] = 1, [23878] = 1, [23879] = 1, [23880] = 1, [23881] = 1, [23882] = 1, [23883] = 1, [23898] = 1}
handlers[901] = function()
    for cog, value in pairs(HINTS) do
        local want = (var("HintOff" .. cog) == 0 and evt.CheckSkill(29, 0, value)) and 2 or 1
        if var("Hint" .. cog) ~= want then
            set("Hint" .. cog, want)
            evt.SetFacetBit(cog, FacetBits.Invisible, want == 1)
        end
    end
end
-- MM9's touch Triggers switching AmbientSounds (dungeon/objects.py): entering one sends its On / Off / Toggle
-- (the scene sound's map variable AmbientSound<key>: 1 on, 2 off); ActivationCount limits the uses.
local SOUND_TRIGGERS = {
    {name = "Trigger0", box = {{-4594, -13103, -216}, {-1960, -12947, 210}}, uses = 0, switches = {{756, "on", false}}},
    {name = "Trigger1", box = {{-4466, -12781, -216}, {-2088, -12451, 210}}, uses = 0, switches = {{756, "off", false}}},
}
local soundInside = {}
handlers[903] = function()
    local x, y, z = evt.GetPartyPosition()
    for _, t in ipairs(SOUND_TRIGGERS) do
        local b = t.box
        local now = x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] and z >= b[1][3] and z <= b[2][3]
        if now and not soundInside[t.name] and (t.uses == 0 or var("SoundUses" .. t.name) < t.uses) then
            set("SoundUses" .. t.name, var("SoundUses" .. t.name) + 1)
            for _, s in ipairs(t.switches) do
                local name = "AmbientSound" .. s[1]
                local on = var(name) == 1 or (var(name) == 0 and s[3])
                local want = (s[2] == "on" or (s[2] == "toggle" and not on)) and 1 or 2
                set(name, want)
            end
        end
        soundInside[t.name] = now
    end
    evt.StartTimer(903, seconds(0.25))
end
handlers[902] = function()   -- map load: the shared objects
    for cog, _ in pairs(HINTS) do set("Hint" .. cog, 0) end
    handlers[901]()
    handlers[903]()
end

-- MM9's people posed by their scripts' :Init loopanim (dungeon/lua.py init_poses): every load.
handlers[907] = function()
    evt.PlayActorClip(13, "sit", true); evt.FaceActorTo(13, -2722, -9175, 0)   -- Markel the Great: NPC127.scr :Init loopanim
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
RegisterEvent(230, "Locked door", handlers[230], "Door")
RegisterEvent(231, "Sickroom door", handlers[231], "Door")
RegisterEvent(240, "Bar", handlers[240], "Door")
RegisterEvent(241, "Curtain", handlers[241], "Door")
RegisterMapTimerEvent(261, seconds(3), handlers[261], "Gates", "", seconds(3))
RegisterEvent(53814, "Ottar Gizurssen", handlers[53814])
RegisterEvent(50814, "Bank", handlers[50814])
RegisterEvent(53815, "Markel the Great", handlers[53815])
RegisterEvent(50815, "Markel", handlers[50815])
RegisterEvent(50813, "Tjolnir", handlers[50813])
RegisterEvent(50811, "Gray Slemnir", handlers[50811])
RegisterEvent(50836, "Tavern keeper", handlers[50836])
RegisterEvent(53821, "Skarphedinn", handlers[53821])
RegisterEvent(50821, "Skarphedinn", handlers[50821])
RegisterEvent(50871, "Nurtigan", handlers[50871])
RegisterEvent(53837, "Thorolf", handlers[53837])
RegisterEvent(50837, "Thorolf", handlers[50837])
RegisterEvent(53838, "Thorolf", handlers[53838])
RegisterEvent(50838, "Thorolf", handlers[50838])
RegisterEvent(330, "Prop1", handlers[330], "Read")
RegisterEvent(331, "Book1", handlers[331], "Book")
RegisterEvent(332, "Sign4", handlers[332], "Read")
RegisterEvent(333, "TownPortal0", handlers[333], "Altar")
RegisterEvent(334, "Well0", handlers[334], "Well")
RegisterEvent(335, "Prop5", handlers[335], "Read")
RegisterEvent(336, "Prop6", handlers[336], "Read")
RegisterEvent(337, "Prop7", handlers[337], "Read")
RegisterEvent(250, "Markel's awards", handlers[250])
RegisterMapTimerEvent(263, seconds(3), handlers[263], "The players' cues", "", seconds(3))
RegisterEvent(270, "Narrator arrives", handlers[270])
RegisterEvent(271, "Wilam arrives", handlers[271])
RegisterEvent(272, "Trislan arrives", handlers[272])
RegisterEvent(273, "Abriel arrives", handlers[273])
RegisterEvent(274, "Ralof arrives", handlers[274])
RegisterEvent(275, "Leffery arrives", handlers[275])
RegisterMapTimerEvent(262, seconds(3), handlers[262], "The play", "", seconds(3))
RegisterMapTimerEvent(260, seconds(3), handlers[260], "Poll", "", seconds(3))
RegisterEvent(1, "Map load", handlers[1])
RegisterMapTimerEvent(906, seconds(3), handlers[906], "Approach talks", "", seconds(3))
RegisterEvent(53811, "Gray Slemnir", handlers[53811])
RegisterEvent(53812, "Eylif Svenssen", handlers[53812])
RegisterEvent(53813, "Tjolnir the Super-neat", handlers[53813])
RegisterEvent(53816, "Kiren Tridor", handlers[53816])
RegisterEvent(53817, "Egil the Booknose", handlers[53817])
RegisterEvent(53818, "Siln Threki", handlers[53818])
RegisterEvent(53819, "Skallagrim Hrafnssen", handlers[53819])
RegisterEvent(53820, "Trian A'Lyrae", handlers[53820])
RegisterEvent(53822, "Forannan A'Velsi", handlers[53822])
RegisterEvent(53823, "Alberik Gusmundssen", handlers[53823])
RegisterEvent(53824, "Ehwaz", handlers[53824])
RegisterEvent(53836, "Aklai Dorka", handlers[53836])
RegisterEvent(53871, "Nutty Nurtigan", handlers[53871])
RegisterEvent(30899, "Clover", handlers[30899], "Pick")
RegisterEvent(30900, "Clover", handlers[30900], "Pick")
RegisterMapTimerEvent(901, seconds(3), handlers[901], "Perception hints", "", seconds(3))
RegisterMapTimerEvent(903, seconds(3), handlers[903], "Ambient triggers", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
RegisterEvent(907, "Script poses", handlers[907])
