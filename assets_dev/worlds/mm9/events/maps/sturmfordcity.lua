-- Sturmford City, MM9 rework (level_generation/projects/mm9r_sturmfordcity/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {ArchDoorLeft = 1, ArchDoorRight = 2, Backdoor = 3, BeetHovengrate = 4, BeetHovengrate_INV = 5, Churchdoor1 = 6, Churchdoor2 = 7, ChurchdoorL = 9, ChurchdoorR = 8, Door0 = 10, Door1 = 11, Door11 = 12, Door12 = 13, Door13 = 14, Door14 = 15, Door15 = 16, Door16 = 17, Door17 = 18, Door18 = 19, Door19 = 20, Door2 = 21, Door20 = 22, Door21 = 23, Door22 = 24, Door23 = 25, Door24 = 26, Door25 = 27, Door26 = 28, Door27 = 29, Door28 = 30, Door29 = 31, Door3 = 32, Door30 = 33, Door31 = 34, Door32 = 35, Door33 = 36, Door34 = 37, Door35 = 38, Door36 = 39, Door37 = 40, Door38 = 41, Door4 = 42, Door5 = 43, Door6 = 44, Door7 = 45, Door8 = 46, Door9 = 47, GenStoreDoor1 = 48, GenStoreDoor2 = 49, Jaildoor = 50, LibraryL = 52, LibraryR = 51, MagiL = 53, MagiR = 54, PalacedoorL = 55, PalacedoorR = 56, RotatingDoor0 = 57, RotatingDoor1 = 58, RotatingDoor10 = 60, RotatingDoor11 = 61, RotatingDoor12 = 63, RotatingDoor13 = 64, RotatingDoor14 = 65, RotatingDoor15 = 66, RotatingDoor16 = 67, RotatingDoor17 = 68, RotatingDoor18 = 69, RotatingDoor19 = 71, RotatingDoor2 = 72, RotatingDoor20 = 62, RotatingDoor21 = 74, RotatingDoor22 = 75, RotatingDoor23 = 76, RotatingDoor24 = 77, RotatingDoor25 = 79, RotatingDoor26 = 78, RotatingDoor27 = 80, RotatingDoor28 = 81, RotatingDoor29 = 82, RotatingDoor3 = 73, RotatingDoor30 = 83, RotatingDoor31 = 84, RotatingDoor32 = 85, RotatingDoor4 = 86, RotatingDoor5 = 87, RotatingDoor6 = 59, RotatingDoor7 = 88, RotatingDoor8 = 70, RotatingDoor9 = 89, Templegate1L = 90, Templegate2L = 91, TestHouse1 = 92, ThronedoorL = 93, ThronedoorR = 94, Towngate1L = 95, bankdoorL = 96, bankdoorR = 97, barflap1 = 98, barflap2 = 99, f10doorl = 100, f10doorl0 = 101, f10doorl2 = 102, f10doorr = 103, f10doorr0 = 104, vaultdoor = 105}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 906, 902}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(1, DoorAction.Trigger) evt.SetDoorState(2, DoorAction.Trigger) end   -- ArchDoorLeft
handlers[102] = function() evt.SetDoorState(3, DoorAction.Trigger) end   -- Backdoor
handlers[103] = function() evt.SetDoorState(6, DoorAction.Trigger) end   -- Churchdoor1
handlers[104] = function() evt.SetDoorState(7, DoorAction.Trigger) end   -- Churchdoor2
handlers[105] = function() evt.SetDoorState(8, DoorAction.Trigger) evt.SetDoorState(9, DoorAction.Trigger) end   -- ChurchdoorL
handlers[106] = function() evt.SetDoorState(11, DoorAction.Trigger) end   -- Door1
handlers[107] = function() evt.SetDoorState(21, DoorAction.Trigger) end   -- Door2
handlers[108] = function() evt.SetDoorState(32, DoorAction.Trigger) end   -- Door3
handlers[109] = function() evt.SetDoorState(42, DoorAction.Trigger) end   -- Door4
handlers[110] = function() evt.SetDoorState(48, DoorAction.Trigger) evt.SetDoorState(49, DoorAction.Trigger) end   -- GenStoreDoor1
handlers[111] = function() evt.SetDoorState(51, DoorAction.Trigger) evt.SetDoorState(52, DoorAction.Trigger) end   -- LibraryL
handlers[112] = function() evt.SetDoorState(53, DoorAction.Trigger) evt.SetDoorState(54, DoorAction.Trigger) end   -- MagiL
handlers[113] = function() evt.SetDoorState(55, DoorAction.Trigger) evt.SetDoorState(56, DoorAction.Trigger) end   -- PalacedoorL
handlers[114] = function() evt.SetDoorState(57, DoorAction.Trigger) evt.SetDoorState(58, DoorAction.Trigger) end   -- RotatingDoor0
handlers[115] = function() evt.SetDoorState(59, DoorAction.Trigger) evt.SetDoorState(60, DoorAction.Trigger) end   -- RotatingDoor10
handlers[116] = function() evt.SetDoorState(61, DoorAction.Trigger) evt.SetDoorState(62, DoorAction.Trigger) end   -- RotatingDoor11
handlers[117] = function() evt.SetDoorState(63, DoorAction.Trigger) evt.SetDoorState(64, DoorAction.Trigger) end   -- RotatingDoor12
handlers[118] = function() evt.SetDoorState(65, DoorAction.Trigger) end   -- RotatingDoor14
handlers[119] = function() evt.SetDoorState(66, DoorAction.Trigger) end   -- RotatingDoor15
handlers[120] = function() evt.SetDoorState(68, DoorAction.Trigger) end   -- RotatingDoor17
handlers[121] = function() evt.SetDoorState(70, DoorAction.Trigger) evt.SetDoorState(71, DoorAction.Trigger) end   -- RotatingDoor19
handlers[122] = function() evt.SetDoorState(74, DoorAction.Trigger) evt.SetDoorState(75, DoorAction.Trigger) end   -- RotatingDoor21
handlers[123] = function() evt.SetDoorState(76, DoorAction.Trigger) evt.SetDoorState(77, DoorAction.Trigger) end   -- RotatingDoor23
handlers[124] = function() evt.SetDoorState(78, DoorAction.Trigger) evt.SetDoorState(79, DoorAction.Trigger) end   -- RotatingDoor25
handlers[125] = function() evt.SetDoorState(80, DoorAction.Trigger) end   -- RotatingDoor27
handlers[126] = function() evt.SetDoorState(81, DoorAction.Trigger) end   -- RotatingDoor28
handlers[127] = function() evt.SetDoorState(82, DoorAction.Trigger) end   -- RotatingDoor29
handlers[128] = function() evt.SetDoorState(83, DoorAction.Trigger) evt.SetDoorState(84, DoorAction.Trigger) end   -- RotatingDoor30
handlers[129] = function() evt.SetDoorState(85, DoorAction.Trigger) end   -- RotatingDoor32
handlers[130] = function() evt.SetDoorState(86, DoorAction.Trigger) evt.SetDoorState(87, DoorAction.Trigger) end   -- RotatingDoor4
handlers[131] = function() evt.SetDoorState(90, DoorAction.Trigger) end   -- Templegate1L
handlers[132] = function() evt.SetDoorState(91, DoorAction.Trigger) end   -- Templegate2L
handlers[133] = function() evt.SetDoorState(93, DoorAction.Trigger) evt.SetDoorState(94, DoorAction.Trigger) end   -- ThronedoorL
handlers[134] = function() evt.SetDoorState(95, DoorAction.Trigger) end   -- Towngate1L
handlers[135] = function() evt.SetDoorState(96, DoorAction.Trigger) evt.SetDoorState(97, DoorAction.Trigger) end   -- bankdoorL
handlers[136] = function() evt.SetDoorState(102, DoorAction.Trigger) end   -- f10doorl2

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureBag0
handlers[42] = function() evt.OpenChest(1) end   -- TreasureBag1

local function has(k) return MM9.hasKey(k) == 1 end
local function quest() MM9.playSound("sounds/events/quest.wav") end
local function show(a, on) evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end
local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; if gold > 0 then MM9.giveGold(gold) end; quest() end

-- MM9's locked doors (Locked 1, no key): the facades' doors and the locked swing doors.
handlers[230] = function()
    evt.PlaySoundName("door/doorlock01.wav", 0, 0, 0)
    evt.StatusText("The door is locked.")
end
-- The jail door (Jaildoor, Locked 1): the prison guard opens and locks it (Sturmguard.scr).
handlers[231] = function()
    if var("JailOpen") == 1 then evt.SetDoorState(DOORS.Jaildoor, DoorAction.Trigger) else handlers[230]() end
end

-- ForadWorld.scr (ScriptObject0, "Sturmford"): key 1026 is the party's location while here (keys 1024-1033
-- are the towns'); key 5017 closes the shops from 20:00 to 06:00 (42 MM9 dialogues forbid or require it).
local function shopHours()
    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24
    local closed = hour >= 20 or hour < 6
    if closed and not has(5017) then MM9.giveKey(5017) elseif not closed and has(5017) then MM9.takeKey(5017) end
end

-- Chedian's dimensional travel pedestal (not MM9's: the user, 2026-11-09), as on the other continents.
handlers[250] = function() evt.OpenDimensionDoor() end

-- Hatches, the grate, the tavern's back door and the bar's flap: a click opens or shuts them.
handlers[240] = function() evt.SetDoorState(DOORS["RotatingDoor7"], DoorAction.Trigger) end   -- RotatingDoor7
handlers[241] = function() evt.SetDoorState(DOORS["RotatingDoor9"], DoorAction.Trigger) end   -- RotatingDoor9
handlers[242] = function() evt.SetDoorState(DOORS["BeetHovengrate"], DoorAction.Trigger) evt.SetDoorState(DOORS["BeetHovengrate_INV"], DoorAction.Trigger) end   -- BeetHovengrate
handlers[243] = function() evt.SetDoorState(DOORS["RotatingDoor2"], DoorAction.Trigger) evt.SetDoorState(DOORS["RotatingDoor3"], DoorAction.Trigger) end   -- RotatingDoor2
handlers[244] = function() evt.SetDoorState(DOORS["barflap1"], DoorAction.Trigger) evt.SetDoorState(DOORS["barflap2"], DoorAction.Trigger) end   -- barflap1

-- Hatlati Oord (NPC48.scr, RUDE 48), arrested: in the cell, the door shut and locked, key 5009 (MM9 walks him
-- there behind the guard).
local function jailHatlati()
    evt.SetMapActorPosition(12, 5693, 5120, 19743)
    set("JailOpen", 0); close("Jaildoor")
    MM9.giveKey(5009)
end

-- Bankorb.scr (Herdis the Stout, RUDE 56): the Orb of Linking. A click with the orb (item 252) after the quest
-- (key 322) unlocks the row that installs it (key 330); the exit places it (key 324) and the sixth bank's orb
-- pays 20 000 experience and 15 000 gold (key 337; banks' keys 331-336).
handlers[53830] = function()
    if not has(324) and has(322) and MM9.hasItem(252, "sturmfordcity:Banker") == 1 then MM9.giveKey(330) end
    MM9.openRude(56)
end
handlers[50830] = function()
    if not has(330) then return end
    MM9.takeKey(330)
    if not has(336) then return end
    quest(); MM9.takeItem(252, "sturmfordcity:Banker"); MM9.giveKey(324)
    if has(337) then return end
    for k = 331, 336 do if not has(k) then return end end
    reward(337, 12500, 15000) -- MM9 GiveExp 20000, mm9_quest_xp_profile.yml
end

-- Beathag.scr (the healer, RUDE 58): a party that broke a temple window (key 5002) and offered to pay (5003)
-- pays 700 gold on leaving. (The 11 windows are glass faces here, not breakable: README.)
handlers[50787] = function()
    if has(5002) and has(5003) then
        if MM9.hasGold(700) == 1 then MM9.takeGold(700); MM9.takeKey(5002); MM9.takeKey(5003)
        else evt.StatusText("You don't have enough gold.") end
    end
end

-- SpiesLikeUs.scr (Bjarni Herjolfssen, RUDE 46): told of Randver (key 18): 2 000 experience, 500 gold (key 471).
handlers[50788] = function()
    if not has(471) and has(18) then reward(471, 2000, 500) end
end

-- Randverrun.scr (Randver the Storm, RUDE 51): asked about sabotage (key 15): 800 experience (key 495) and he
-- vanishes by town portal (MM9 runs him to RandverHide first); gone on every later visit.
handlers[50841] = function()
    if not has(15) then return end
    if not has(495) then MM9.giveKey(495); MM9.giveExperience(800) end
    quest()
    MM9.clientFx(39, "mm9:town_portal")   -- :Vanish: DoClientFX g_hmyObject, Ceffect
    MM9.removeActor(39)
end

-- NPC61.scr (Fridleif Gjukissen, the clerk, RUDE 61): the Basilisk Skin (item 380 or 591) with the labours
-- taken (key 214) unlocks its row (215); the Gladiator promotion (key 26 -> 221, 63 000 experience, 5 000 gold,
-- every character holding key 409-412); with Kira's Shield delivered (219) the shield (item 375) is taken.
handlers[53833] = function()
    if has(214) and (MM9.hasItem(380, "sturmfordcity:Clerk") == 1
        or MM9.hasItem(591, "sturmfordcity:Clerk") == 1) then MM9.giveKey(215) end
    MM9.openRude(61)
end
handlers[50833] = function()
    if not has(221) and has(26) then
        reward(221, 37500, 5000) -- MM9 GiveExp 63000, mm9_quest_xp_profile.yml
        MM9.promoteParty("Gladiator")   -- every eligible member (not MM9's per-character keys 409-412)
    end
    if has(219) and MM9.hasItem(375, "sturmfordcity:Clerk") == 1 then MM9.takeItem(375, "sturmfordcity:Clerk") end
end

-- Sturmguard.scr (the prison guard; the DAT gives him no dialogue, his script opens 425): the jail door (keys
-- 5018 open, 5019 close and lock) and Hatlati's arrest (key 154 -> in the cell, key 5009).
handlers[54323] = function()
    MM9.giveKey(5008)
    MM9.openRude(425)
end
handlers[51323] = function()
    MM9.takeKey(5008)
    if has(5019) then MM9.takeKey(5018); MM9.takeKey(5019); set("JailOpen", 0); close("Jaildoor")
    elseif has(5018) then set("JailOpen", 1); open("Jaildoor") end
    if has(5009) or not has(154) then return end
    -- the guard sends Hatlati GotoJail and opens the cell for him: a dead Hatlati takes no message
    -- (MM9.receives), so the door stays open and he never walks in (no key 5009)
    if MM9.receives("sturmfordcity", "Hatlati", "GotoJail", 12) then jailHatlati()
    else set("JailOpen", 1); open("Jaildoor") end
end

-- NPC90.scr (Ivsar Forktooth, RUDE 90): leaving with him (key 194 taken) sends him home: key 196 enables
-- Bjarni's reward row. MM9 also gives Drangheim Prison's alarm key 5006 here (a source quirk, left out: README).
handlers[50829] = function()
    MM9.takeKey(194)
    if not has(21) then MM9.giveKey(196) end
end

-- NPC378.scr (Thorolf Ratatoskssen, two copies, RUDE 378): the messenger. Talking to one removes the other; after
-- the message (key 84) or the summons (key 107) he vanishes by town portal; with 83 or 106 alone the dialogue
-- reopens (it cannot be skipped).
handlers[54327] = function() MM9.removeActor(45); MM9.openRude(378) end
handlers[51327] = function()
    if has(107) or has(84) then MM9.clientFx(44, "mm9:town_portal"); MM9.removeActor(44); MM9.removeActor(45)
    elseif has(106) or has(83) then MM9.openRude(378) end
end
handlers[54328] = function() MM9.removeActor(44); MM9.openRude(378) end
handlers[51328] = function()
    if has(107) or has(84) then MM9.clientFx(45, "mm9:town_portal"); MM9.removeActor(45); MM9.removeActor(44)
    elseif has(106) or has(83) then MM9.openRude(378) end
end

-- LudwigVan.scr :OnRudeExit (Ludwig Van, RUDE 47): his manuscript found (key 19): 12 000 experience, 2 000 gold,
-- the manuscript (item 248) taken (key 116).
local function ludwigExit()
    if not has(116) and has(19) then
        reward(116, 10500, 2000); MM9.takeItem(248, "sturmfordcity:Ludwig") -- MM9 GiveExp 12000, mm9_quest_xp_profile.yml
    end
end
-- Bjarni.scr :OnRudeExit (Jarl Bjarni Thorvaldssen, RUDE 45): Ivsar rescued (key 21: 117, 42 000 experience,
-- 3 500 gold, Ivsar to his marker by the throne); the love letter (22: item 247, key 150) and its answer (24 or
-- 25: 151, 15 200 experience, 2 000 gold); Anskram Keep (41: 149, 20 000, 3 000); the clans united (83: 179,
-- 26 500, 6 000).
local function bjarniExit()
    if not has(117) and has(21) then
        reward(117, 16500, 3500) -- MM9 GiveExp 42000, mm9_quest_xp_profile.yml
        if MM9.receives("sturmfordcity", "Ivsar", "stop", 27) then evt.SetMapActorPosition(27, 7168, 7660, 19722) end
    end
    if has(22) and not has(150) then MM9.giveKey(150); MM9.giveItem(247, "sturmfordcity:Bjarni") end
    if (has(24) or has(25)) and not has(151) then reward(151, 12500, 2000) end -- MM9 GiveExp 15200, mm9_quest_xp_profile.yml
    if not has(149) and has(41) then reward(149, 10500, 3000) end -- MM9 GiveExp 20000, mm9_quest_xp_profile.yml
    if not has(179) and has(83) then MM9.giveKey(179); MM9.giveExperience(12500); MM9.giveGold(6000) end -- MM9 GiveExp 26500, mm9_quest_xp_profile.yml
end

-- MM9's RUDEProps: people posed as props (actors looping their pose); their scripts' use and exit parts.
handlers[53786] = function()   -- Bartender (Sturmgaardinn.scr)
    MM9.playSound("voices/npc/npc_057.wav")
    MM9.openRude(57)
end
handlers[53789] = function()   -- Ludwig (LudwigVan.scr)
    evt.PlayActorClip(49, {"ludwig_lookup", "ludwig_writing"}, true)
    MM9.playSound("voices/npc/npc_047.wav")
    MM9.openRude(47)
end
handlers[50789] = function() ludwigExit() end
handlers[53799] = function()   -- RUDEProp0 (tryggvaspeech.scr)
    MM9.openRude(63)
end
handlers[53800] = function()   -- CommonerHumanMaleA5 (scripts\PropAnim.scr)
    MM9.openRude(428)
end
handlers[53801] = function()   -- CommonerElfFemaleA1 (akeretainer.scr)
    MM9.openRude(86)
end
handlers[53805] = function()   -- Halfdan (scripts\PropAnim.scr)
    MM9.openRude(76)
end
handlers[53806] = function()   -- RUDEProp1 (erccspeech.scr)
    evt.StatusText("He is too drunk to talk.")
end
handlers[53807] = function()   -- CommonerHumanMaleA6 (scripts\PropAnim.scr)
    MM9.openRude(428)
end
handlers[53808] = function()   -- Bjarni (Bjarni.scr)
    if has(214) and (MM9.hasItem(380, "sturmfordcity:Bjarni") == 1
        or MM9.hasItem(591, "sturmfordcity:Bjarni") == 1) then MM9.giveKey(215) end
    if not has(178) and has(82) and has(34) and has(51) and has(63) and has(74) then MM9.giveKey(178) end
    MM9.playSound("voices/npc/npc_045.wav")
    MM9.openRude(45)
end
handlers[50808] = function() bjarniExit() end

-- BookLetter.scr letters (BOOK AND SCROLL TEXT.csv rows), Book.scr books (no text in MM9), TownPortal.scr.
handlers[330] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0) end   -- Books1 (Book.scr: pages turn, no text)
handlers[331] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0) end   -- Books0 (Book.scr: pages turn, no text)
handlers[332] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0) end   -- Books (Book.scr: pages turn, no text)
handlers[333] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Chapter One\n\nElise had been my love.  That much had always been for certain.  It was unfortunate that the day at the carriage had gone so badly.  I had always wanted to tell her how much she meant to me, and had planned to right there as she was climbing aboard.  How could I have known that her foot would slip when I pulled her back to me?  It wasn't as if the mud had made things that slippery.\nI had to put her from my mind.  It was distracting me from my job as Worldly Hero.  I couldn't think of her.  I had to keep my mind on what I was doing.  One misstep and it was all over.\nStill, Elise held my heart, I could do nothing without her.  She had always been my reason for being.\n\"Oops,\" Enril said.") end   -- Prop0 (449)
handlers[334] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Wanted\n\nSoldiers to fight against Drangheim.\nMust be skilled in fighting\nMust have own horse, sword, and armor.\n\nInquire at the hall of Halfdan the Strong.") end   -- Prop1 (450)
handlers[335] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Invoice for Services\n\nHerdis the Stout shall pay the sum of 500 gold for the extermination of rats from her basement.\n\nHeroes, LLC\nMegan the Mage, President\nBodil the Priest, Treasurer\nSir Roderic the Gladiator, Security\nGanir the Assassin, Security") end   -- Prop3 (452)
handlers[336] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Letter to Skallgrim\n\nSkallgrim,\nI've seen you come home late and drunk for the last time.  I've taken up with your brother Janir.  At least he takes me with him when he goes out drinking!  Maybe we'll see you at the wedding.\nCicilia") end   -- Prop4 (453)
-- TownPortal0: TownPortal.scr "Sturmford": cleansing the altar gives key 5012 and MM9 swaps its dirty skin for
-- the clean one: TownPortal0 (SetSprite 490) hides and TownPortal0Clean (491, the clean
-- altar at its place) shows; the map load does the same once the key is set (:Init FixCheck).
local function townPortalAltar()
    local clean = has(5012)
    evt.SetSprite(490, clean and 0 or 1, "0"); evt.SetSprite(491, clean and 1 or 0, "0")
end
handlers[337] = function()
    if has(5012) then return end
    MM9.giveKey(5012); quest()
    townPortalAltar()
    evt.StatusText("The altar is cleansed.")
end
handlers[338] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Letter to Children\n\nTo My Children,\nI've gone to earn some money to stop us from starving.  Fear not, I shall return soon.\nHatlati") end   -- Prop7 (451)

-- The barks: Trigger1 and Trigger2 (once each) send 'blabber'. TryggvaSpeech.scr (RUDEProp0, Tryggva at his
-- table): one of his four drunken lines (Tryygva01-04, at random); ErccSpeech.scr (RudeProp1, Ercc): with no key
-- 113, key 113, ercc01 and, as he passes out, ercc02. At the speaker (MM9: Playsound radius 512).
local BARKS = {{name = "Trigger1", box = {{-610, -1192, 19635}, {-45, -626, 20133}}}, {name = "Trigger2", box = {{-498, -198, 19543}, {88, 388, 20225}}}}
local function barked(name)
    if name == "Trigger1" then
        evt.PlaySoundName("voices/cinema/tryygva0" .. MM9.random(1, 4) .. ".wav", -325, -1004, 19969)
        evt.PlayActorClip(50, {"conv_seated", "conv_seated", "listen"}, true)
    elseif not has(113) then
        MM9.giveKey(113)
        evt.PlaySoundName("voices/cinema/ercc01.wav", -123, 0, 19969)
        evt.PlayActorClip(54, {"ercc01a", "ercc01b", "ercc01c", "ercc02", "ercc_out"}, true)
        set("ErccDue", 1)
        evt.StartTimer(261, seconds(66))
    end
end
handlers[261] = function()
    evt.StopTimer(261)
    if var("ErccDue") ~= 1 then return end
    set("ErccDue", 0)
    evt.PlaySoundName("voices/cinema/ercc02.wav", -123, 0, 19969)
end
local function barks()
    local x, y, z = evt.GetPartyPosition()
    for _, t in ipairs(BARKS) do
        local b = t.box
        if var("Barked" .. t.name) == 0 and x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2]
                and z >= b[1][3] and z <= b[2][3] then
            set("Barked" .. t.name, 1)
            barked(t.name)
        end
    end
end
local function poll()
    shopHours()
    barks()
    evt.StartTimer(260, seconds(1))
end
handlers[260] = poll
handlers[1] = function()   -- map load
    for k = 1024, 1033 do if k ~= 1026 and has(k) then MM9.takeKey(k) end end
    MM9.giveKey(1026)
    if var("JailOpen") == 1 then open("Jaildoor") end
    show(27, has(242))   -- NPC90.scr :Init (Sturmford): here once he made it home (242)
    townPortalAltar()   -- TownPortal.scr :Init (FixCheck): the clean altar once its key is set
    if has(117) and MM9.actorAlive(27) then evt.SetMapActorPosition(27, 7168, 7660, 19722) end   -- TELP intent
    if has(15) then MM9.removeActor(39) end   -- Randverrun.scr :Init
    local thorolf = has(83) and not has(84)   -- NPC378.scr :Init (Frosgard's third copy: 106)
    show(44, thorolf); show(45, thorolf)
    show(41, not has(451))   -- Retainer.scr: Tesar Olin, hidden while hired
    if has(157) then evt.SetMapActorPosition(22, 4260, 19538, 19743) end   -- NPC49.scr
    if has(154) and MM9.actorAlive(12) then jailHatlati() end   -- NPC48.scr :Init
    evt.PlayActorClip(48, "innkeeper2", true); evt.FaceActorTo(48, -625, 1035, 0)   -- Kenneth Wartooth: LoopAnim innkeeper2
    evt.PlayActorClip(49, "ludwig_writing", true); evt.FaceActorTo(49, 4305, 2145, 0)   -- Ludwig Van: LoopAnim ludwig_writing
    evt.PlayActorClip(50, "listen", true); evt.FaceActorTo(50, -325, -748, 0)   -- Tryygva the Hammer: LoopAnim listen
    evt.PlayActorClip(51, "sitting", true); evt.FaceActorTo(51, -1229, 453, 0)   -- Peasant: LoopAnim sitting
    evt.PlayActorClip(52, "sitting", true); evt.FaceActorTo(52, -3553, 13172, 0)   -- Ake the Righteous: LoopAnim sitting
    evt.PlayActorClip(53, "listen", true); evt.FaceActorTo(53, -328, -1070, 0)   -- Halfdan Doorsbane: LoopAnim listen
    evt.PlayActorClip(54, "ercc_sitting", true); evt.FaceActorTo(54, -123, 256, 0)   -- Ercc: LoopAnim ercc_sitting
    evt.PlayActorClip(55, "sitting2", true); evt.FaceActorTo(55, -942, 950, 0)   -- Peasant: LoopAnim sitting2
    evt.PlayActorClip(56, "sit", true); evt.FaceActorTo(56, 7055, 8192, 0)   -- Bjarni Thorvaldssen: LoopAnim sit
    show(52, not has(454))   -- AkeRetainer.scr: away while hired
    show(56, not (has(40) and not has(108)))   -- Bjarni.scr :Init Vanish
    poll()
end
-- MM9's approach talks (dungeon/lua.py approach_talk): an NPC whose script talks when the party comes
-- within 16 LT of his body (OnTargetWithinDist / RunTo 16 -> DoRude). reach: the feet's distance at which
-- he talks; sight > 0: he runs to the party once he sees it within that range. Once per visit.
local APPROACH_TALKS = {
    {actor = 44, reach = 109, sight = 1536, armed = function() return not has(107) and (not has(84) or has(106)) end,
        talk = function() MM9.removeActor(45); MM9.openRude(378, 44); MM9.playSound("voices/npc/npc_378.wav") end},   -- Thorolf0: NPC378.scr :OnFound RunTo 16 :Talk
    {actor = 45, reach = 109, sight = 1536, armed = function() return not has(107) and (not has(84) or has(106)) end,
        talk = function() MM9.removeActor(44); MM9.openRude(378, 45); MM9.playSound("voices/npc/npc_378.wav") end},   -- Thorolf1: NPC378.scr :OnFound RunTo 16 :Talk
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
handlers[53787] = function() MM9.playSound("voices/npc/npc_058.wav"); MM9.openRude(58) end   -- Healer
handlers[53788] = function() MM9.playSound("voices/npc/npc_046.wav"); MM9.openRude(46) end   -- CommonerHumanMaleA4
handlers[53802] = function() MM9.playSound("voices/npc/npc_062.wav"); MM9.openRude(62) end   -- Trainer
handlers[53829] = function() MM9.playSound("voices/npc/npc_090.wav"); MM9.openRude(90) end   -- Ivsar
do local own = handlers[53830]; handlers[53830] = function() MM9.playSound("voices/npc/npc_056.wav"); own() end end   -- Banker
handlers[53831] = function() MM9.playSound("voices/npc/npc_054.wav"); MM9.openRude(54) end   -- Armorer
handlers[53832] = function() MM9.playSound("voices/npc/npc_053.wav"); MM9.openRude(53) end   -- Blacksmith
do local own = handlers[53833]; handlers[53833] = function() MM9.playSound("voices/npc/npc_061.wav"); own() end end   -- Clerk
handlers[53834] = function() MM9.playSound("voices/npc/npc_059.wav"); MM9.openRude(59) end   -- Shopkeeper
handlers[53841] = function() MM9.playSound("voices/npc/npc_051.wav"); MM9.openRude(51) end   -- RUDEProp3
handlers[53842] = function() MM9.playSound("voices/npc/npc_050.wav"); MM9.openRude(50) end   -- Magi
handlers[53843] = function() MM9.playSound("voices/npc/npc_043.wav"); MM9.openRude(43) end   -- CommonerHalfOrcMaleA0
handlers[54357] = function() MM9.playSound("voices/npc/npc_202.wav"); MM9.openRude(202) end   -- Shopkeeper0

-- MM9's bonus props (dungeon/objects.py bonus_lines; the use of each class, object.lto): wells, cauldrons,
-- cook pots and clovers.
handlers[31390] = function() MM9.useClover(1390, "sturmfordcity:Clover0") end   -- Clover0 (Clover)
handlers[31391] = function() MM9.useClover(1391, "sturmfordcity:Clover1") end   -- Clover1 (Clover)

-- MM9's PerceptionBrushes (dungeon/perception.py): the red glow shows to a party whose Perception reaches the
-- brush's PerceptionValue, checked on load and every 3 s; map Lua turns one off for good with
-- set("HintOff<cog>", 1) (MM9's Off message to the brush).
local HINTS = {[24332] = 1, [24333] = 1, [24334] = 1, [24335] = 1, [24336] = 1, [24337] = 1, [24338] = 1, [24339] = 1, [24340] = 1, [24341] = 1, [24342] = 1, [24343] = 1, [24344] = 1, [24345] = 1, [24346] = 1, [24347] = 1, [24348] = 1, [24349] = 1, [24350] = 1, [24351] = 1, [24352] = 1, [24353] = 1, [24354] = 1, [24394] = 1}
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
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(230, "Locked door", handlers[230], "Door")
RegisterEvent(231, "Jail door", handlers[231], "Door")
RegisterEvent(250, "Dimensional Travel", handlers[250], "Dimensional Travel")
RegisterEvent(240, "RotatingDoor7", handlers[240], "Door")
RegisterEvent(241, "RotatingDoor9", handlers[241], "Door")
RegisterEvent(242, "BeetHovengrate", handlers[242], "Door")
RegisterEvent(243, "RotatingDoor2", handlers[243], "Door")
RegisterEvent(244, "barflap1", handlers[244], "Door")
RegisterEvent(53830, "Herdis the Stout", handlers[53830])
RegisterEvent(50830, "Bank", handlers[50830])
RegisterEvent(50787, "Beathag", handlers[50787])
RegisterEvent(50788, "Bjarni Herjolfssen", handlers[50788])
RegisterEvent(50841, "Randver", handlers[50841])
RegisterEvent(53833, "Fridleif", handlers[53833])
RegisterEvent(50833, "Fridleif", handlers[50833])
RegisterEvent(54323, "Guard", handlers[54323])
RegisterEvent(51323, "Guard", handlers[51323])
RegisterEvent(50829, "Ivsar", handlers[50829])
RegisterEvent(54327, "Thorolf", handlers[54327])
RegisterEvent(51327, "Thorolf", handlers[51327])
RegisterEvent(54328, "Thorolf", handlers[54328])
RegisterEvent(51328, "Thorolf", handlers[51328])
RegisterEvent(53786, "Bartender", handlers[53786])
RegisterEvent(53789, "Ludwig", handlers[53789])
RegisterEvent(50789, "Ludwig", handlers[50789])
RegisterEvent(53799, "RUDEProp0", handlers[53799])
RegisterEvent(53800, "CommonerHumanMaleA5", handlers[53800])
RegisterEvent(53801, "CommonerElfFemaleA1", handlers[53801])
RegisterEvent(53805, "Halfdan", handlers[53805])
RegisterEvent(53806, "RUDEProp1", handlers[53806])
RegisterEvent(53807, "CommonerHumanMaleA6", handlers[53807])
RegisterEvent(53808, "Bjarni", handlers[53808])
RegisterEvent(50808, "Bjarni", handlers[50808])
RegisterEvent(330, "Books1", handlers[330], "Book")
RegisterEvent(331, "Books0", handlers[331], "Book")
RegisterEvent(332, "Books", handlers[332], "Book")
RegisterEvent(333, "Prop0", handlers[333], "Read")
RegisterEvent(334, "Prop1", handlers[334], "Read")
RegisterEvent(335, "Prop3", handlers[335], "Read")
RegisterEvent(336, "Prop4", handlers[336], "Read")
RegisterEvent(337, "TownPortal0", handlers[337], "Altar")
RegisterEvent(338, "Prop7", handlers[338], "Read")
RegisterMapTimerEvent(260, seconds(3), handlers[260], "Poll", "", seconds(3))
RegisterEvent(1, "Map load", handlers[1])
RegisterMapTimerEvent(261, seconds(3), handlers[261], "Ercc passes out", "", seconds(3))
RegisterMapTimerEvent(906, seconds(3), handlers[906], "Approach talks", "", seconds(3))
RegisterEvent(53787, "Beathag A'Dorad", handlers[53787])
RegisterEvent(53788, "Bjarni Herjolfssen", handlers[53788])
RegisterEvent(53802, "Tjorvi Isleifson", handlers[53802])
RegisterEvent(53829, "Ivsar Forktooth", handlers[53829])
RegisterEvent(53831, "Halfdan Steelhands", handlers[53831])
RegisterEvent(53832, "Ketil Blacksmith", handlers[53832])
RegisterEvent(53834, "Tadc A'Norta a'thrakan", handlers[53834])
RegisterEvent(53841, "Randver the Storm", handlers[53841])
RegisterEvent(53842, "Injor Gostat", handlers[53842])
RegisterEvent(53843, "Tesar Olin", handlers[53843])
RegisterEvent(54357, "Eva A'Washadi", handlers[54357])
RegisterEvent(31390, "Clover", handlers[31390], "Pick")
RegisterEvent(31391, "Clover", handlers[31391], "Pick")
RegisterMapTimerEvent(901, seconds(3), handlers[901], "Perception hints", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
