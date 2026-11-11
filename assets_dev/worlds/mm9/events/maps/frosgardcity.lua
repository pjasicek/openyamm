-- Frosgard City, MM9 rework (level_generation/projects/mm9r_frosgardcity/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {Apothdoor = 1, Bankdoor_INV = 2, DestructableBrush14 = 26, DestructableBrush15 = 27, DestructableBrush16 = 28, DestructableBrush17 = 29, DestructableBrush18 = 30, DestructableBrush19 = 31, DestructableBrush20 = 32, DestructableBrush21 = 33, DestructableBrush22 = 34, DestructableBrush23 = 35, DestructableBrush24 = 36, DestructableBrush25 = 37, DestructableBrush26 = 38, DestructableBrush27 = 39, DestructableBrush28 = 40, DestructableBrush29 = 41, DestructableBrush30 = 42, DestructableBrush31 = 43, DestructableBrush32 = 44, DestructableBrush33 = 45, DestructableBrush34 = 46, DestructableBrush35 = 47, DestructableBrush36 = 48, DestructableBrush37 = 49, DestructableBrush38 = 50, DestructableBrush39 = 51, DestructableBrush40 = 52, DestructableBrush41 = 53, DestructableBrush42 = 54, DestructableBrush43 = 55, DestructableBrush44 = 56, DestructableBrush45 = 57, DestructableBrush46 = 58, DestructableBrush6 = 59, DestructableBrush7 = 60, DestructableBrush8 = 61, DestructableBrush9 = 62, Door0 = 3, Door1 = 4, Door10 = 5, Door11 = 6, Door12 = 7, Door13 = 8, Door14 = 9, Door15 = 10, Door16 = 11, Door17 = 12, Door18 = 13, Door19 = 14, Door2 = 15, Door20 = 16, Door21 = 17, Door22 = 18, Door23 = 19, Door4 = 20, Door5 = 21, Door6 = 22, Door7 = 23, Door8 = 24, Door9 = 25, Magidoor = 63, RDoor0 = 64, Taverndoor = 65, TempledoorL = 66, TempledoorR = 67, TownhallL = 69, TownhallR = 68, Trainingdoor = 70, WAdoorL = 71, WAdoorR = 72}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 906, 902, 907}, onLeave = {}, timers = {}, openedChestIds = {}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(1, DoorAction.Trigger) end   -- Apothdoor
handlers[102] = function() evt.SetDoorState(8, DoorAction.Trigger) end   -- Door13
handlers[103] = function() evt.SetDoorState(23, DoorAction.Trigger) end   -- Door7
handlers[104] = function() evt.SetDoorState(63, DoorAction.Trigger) end   -- Magidoor
handlers[105] = function() evt.SetDoorState(64, DoorAction.Trigger) end   -- RDoor0
handlers[106] = function() evt.SetDoorState(65, DoorAction.Trigger) end   -- Taverndoor
handlers[107] = function() evt.SetDoorState(66, DoorAction.Trigger) evt.SetDoorState(67, DoorAction.Trigger) end   -- TempledoorL
handlers[108] = function() evt.SetDoorState(68, DoorAction.Trigger) evt.SetDoorState(69, DoorAction.Trigger) end   -- TownhallL
handlers[109] = function() evt.SetDoorState(70, DoorAction.Trigger) end   -- Trainingdoor
handlers[110] = function() evt.SetDoorState(71, DoorAction.Trigger) evt.SetDoorState(72, DoorAction.Trigger) end   -- WAdoorL

-- Chests (MM9 TreasureChest objects; loot records in the scene).

local function has(k) return MM9.hasKey(k) == 1 end
local function quest() MM9.playSound("sounds/events/quest.wav") end
local function show(a, on) evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end
local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; if gold > 0 then MM9.giveGold(gold) end; quest() end
local function cog(c, on) evt.SetSprite(c, on and 1 or 0, "0") end

-- MM9's locked doors (Locked 1, no key): the facades' doors.
handlers[230] = function()
    evt.PlaySoundName("door/doorlock01.wav", 0, 0, 0)
    evt.StatusText("The door is locked.")
end

-- ForadWorld.scr (ScriptObject0, "Frosgard"): key 1029 is the party's location while here (keys 1024-1033
-- are the towns'); key 5017 closes the shops from 20:00 to 06:00.
local function shopHours()
    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24
    local closed = hour >= 20 or hour < 6
    if closed and not has(5017) then MM9.giveKey(5017) elseif not closed and has(5017) then MM9.takeKey(5017) end
end

-- NPC206.scr / BankOrb.inc (the banker Cormac A'Ghrie, RUDE 206) and the bank's counter hatch (Bankdoor: its
-- OpenTrigger sends the banker "bank"): a click on the hatch opens it and the banker's dialogue; with the orb
-- quest (322) and the Orb of Linking (item 252) the row that installs it is unlocked (330).
local BANK = {"Bankdoor_INV"}
local function bankHatch(on) for _, n in ipairs(BANK) do if on then open(n) else close(n) end end end
local function bankDialogue()
    if has(322) and MM9.hasItem(252, "frosgardcity:Banker") == 1 then MM9.giveKey(330) end
    MM9.openRude(206, 7)   -- the banker speaks (from the hatch too): his exit shuts it
end
handlers[231] = function()
    if var("BankOpen") == 0 then set("BankOpen", 1); bankHatch(true) end
    -- "bank" is a message to the banker: a dead banker takes none (MM9.receives); the hatch still opens
    if MM9.receives("frosgardcity", "Banker", "bank", 7) then bankDialogue() end
end
handlers[53553] = bankDialogue
-- BankOrb.inc :OnRude: the hatch shuts; the orb placed (330 taken; with 333 the orb taken, 327); six banks'
-- orbs (331-336): 337, 20 000 experience, 15 000 gold.
handlers[50553] = function()
    if var("BankOpen") == 1 then set("BankOpen", 0); bankHatch(false) end
    if not has(330) then return end
    MM9.takeKey(330)
    if not has(333) then return end
    quest(); MM9.takeItem(252, "frosgardcity:Banker"); MM9.giveKey(327)
    if has(337) then return end
    for k = 331, 336 do if not has(k) then return end end
    reward(337, 12500, 15000) -- MM9 GiveExp 20000, mm9_quest_xp_profile.yml
end

-- BreakIce.scr: the quest to free the frozen docks. Jarl Tryggva gives it (key 71); the powder seller (NPC215,
-- key 1022) puts a powder barrel on the ice by the docks (DestructableProp0). MM9: the barrel's death starts the
-- cannon (Shooter0, FrosgardShooter.scr), whose start runs BreakIce's cinema; here its click or its breaking
-- does, and the cinema is the cinematic break_ice: Shooter1-4 bolt the first floes, the rest break in MM9's
-- waves (each floe drops under the ocean surface) and :GivePoints gives 72 and 8 000 experience (with 71), else
-- 174 and 8 000: its steps (the block at the end of this file).
local ICE_ALL = {"DestructableBrush14", "DestructableBrush15", "DestructableBrush16", "DestructableBrush17", "DestructableBrush18", "DestructableBrush19", "DestructableBrush20", "DestructableBrush21", "DestructableBrush22", "DestructableBrush23", "DestructableBrush24", "DestructableBrush25", "DestructableBrush26", "DestructableBrush27", "DestructableBrush28", "DestructableBrush29", "DestructableBrush30", "DestructableBrush31", "DestructableBrush32", "DestructableBrush33", "DestructableBrush34", "DestructableBrush35", "DestructableBrush36", "DestructableBrush37", "DestructableBrush38", "DestructableBrush39", "DestructableBrush40", "DestructableBrush41", "DestructableBrush42", "DestructableBrush43", "DestructableBrush44", "DestructableBrush45", "DestructableBrush46", "DestructableBrush6", "DestructableBrush7", "DestructableBrush8", "DestructableBrush9"}
local function iceGone() for _, n in ipairs(ICE_ALL) do open(n) end end
local function floes(names) for _, n in ipairs(names) do if DOORS[n] then open(n) end end end
local function iceReward()   -- BreakIce.scr :GivePoints
    iceGone()
    if not has(72) and has(71) then MM9.giveKey(72); MM9.giveExperience(8000)
    elseif not has(174) then MM9.giveKey(174); MM9.giveExperience(8000) end
    quest()
end
-- FrosgardShooter.scr "Shoot" (Shooter0, under the ice): its Start (the barrel's death) fires FireBolts up at
-- Shoot0-5, one picked at random every 0.4 s, eight in all (:Target, nCounter 8), as the floes break.
local CANNON = {4260, -11796, -287}
local CANNON_AT = {{4260, -11796, 901}, {4588, -11305, 901}, {4915, -12370, 901}, {4096, -12616, 901}, {3359, -11960, 901}, {3604, -11305, 901}}
handlers[235] = function()
    local left = var("CannonShots")
    if left <= 0 or CANNON == nil then evt.StopTimer(235); return end
    local to = CANNON_AT[evt.RandomBetween(1, #CANNON_AT)]
    evt.FireMissile("Fire", CANNON[1], CANNON[2], CANNON[3], to[1], to[2], to[3], 0, "Fire", 0)
    MM9.launchSound("FireBolt", CANNON[1], CANNON[2], CANNON[3])
    set("CannonShots", left - 1)
    evt.StartTimer(235, seconds(0.4))
end
handlers[232] = function()   -- DestructableProp0, the powder barrel
    if not has(1022) or var("BarrelGone") == 1 then return end
    set("BarrelGone", 1); cog(404, false)
    MM9.playSound("sounds/events/iceimpact.wav")
    evt.StatusText("The powder barrel explodes!")
    set("CannonShots", 8); evt.StartTimer(235, seconds(0.1))
    MM9Cinematic.start("break_ice")
end

-- NPC215.scr (the powder seller, RUDE 215): the delivery (key 1022) puts the barrel on the ice. (His night
-- cannon test, Shooter6 from 22:00 to 04:00 with key 71, and Shooter5's test shot by DestructableProp1 are
-- not carried: no quest hangs on them.)
handlers[50571] = function()
    if has(1022) and var("BarrelGone") == 0 and not has(72) then cog(404, true) end
end

-- NPC209.scr (the dockmaster, RUDE 209): with the docks free (72), the dock schedule (item 562), key 378.
handlers[50554] = function()
    if not has(378) and has(72) then MM9.giveItem(562, "frosgardcity:Dockmaster"); MM9.giveKey(378) end
end

handlers[233] = function()   -- WellMMIX0: its class's use (dungeon/objects.py bonus_call)
    MM9.useWell(715, 2, 1, 5, 0, 4)
end

-- NPC180.scr (Jarl Tryggva Ravenlocks, RUDE 180; United.inc): the click checks the five clans (82, 38, 51, 63,
-- 74 -> 178); the exit: Yanmir's Fort (70 -> 172, 58 000 experience, 10 000 gold), the ice (73 -> 175, 30 000,
-- 3 000), the clans united (83 -> 179, 26 500, 6 000). Away during the battle (104) or on key 40, unless 108.
handlers[53075] = function()
    if not has(178) and has(82) and has(38) and has(51) and has(63) and has(34) then MM9.giveKey(178) end
    MM9.openRude(180)
end
handlers[50075] = function()
    if not has(172) and has(70) then reward(172, 18500, 10000) end -- MM9 GiveExp 58000, mm9_quest_xp_profile.yml
    if not has(175) and has(73) then reward(175, 12500, 3000) end -- MM9 GiveExp 30000, mm9_quest_xp_profile.yml
    if not has(179) and has(83) then reward(179, 12500, 6000) end -- MM9 GiveExp 26500, mm9_quest_xp_profile.yml
end

-- NPC181.scr (RUDE 181): the Ranger promotion (248 -> 249, 63 000 experience, 5 000 gold, every character
-- holding key 417-420); the click with item 184 gives key 241.
handlers[53593] = function()
    if MM9.hasItem(184, "frosgardcity:181") == 1 then MM9.giveKey(241) end
    MM9.openRude(181)
end
handlers[50593] = function()
    if not has(249) and has(248) then
        reward(249, 37500, 5000) -- MM9 GiveExp 63000, mm9_quest_xp_profile.yml
        MM9.promoteParty("Ranger")   -- every eligible member (not MM9's per-character keys 417-420)
    end
end
-- NPC183.scr (RUDE 183): with key 295, item 245 unless the party has it.
handlers[50559] = function()
    if has(295) and MM9.hasItem(245, "frosgardcity:183") ~= 1 then MM9.giveItem(245, "frosgardcity:183") end
end
-- NPC184.scr (the brewmaster, RUDE 184): the keg (302 -> 303, item 249); delivered (307 -> 308, 20 000
-- experience); the bad delivery (309 -> 310, 2 000 experience, 200 gold, the keg taken).
handlers[50560] = function()
    if not has(303) and has(302) then MM9.giveKey(303); MM9.giveItem(249, "frosgardcity:184") end
    if not has(308) and has(307) then reward(308, 12500, 0) end -- MM9 GiveExp 20000, mm9_quest_xp_profile.yml
    if not has(310) and has(309) then reward(310, 2000, 200); MM9.takeItem(249, "frosgardcity:184") end
end
-- NPC188.scr (RUDE 188): the ritual (257 -> 258, item 430, 5 000 experience).
handlers[50561] = function()
    if not has(258) and has(257) then reward(258, 5000, 0); MM9.giveItem(430, "frosgardcity:188") end
end
-- PLEDGE.inc (:Pledge, :CheckAllNPC, :reward), on the dialogue exit of NPC190/191/193/195/196/197/199 and
-- Pledge.scr (217, 218): with the pledge drive (265) and at most one of the pledges 269-274 missing (its loop
-- reads 269-275 and stops on a second missing one only before 275; 276 is never read): key 277, 5 000
-- experience, the quest sound, once.
local function pledge()
    if not has(265) or has(277) then return end
    local missing = 0
    for k = 269, 274 do if not has(k) then missing = missing + 1 end end
    if missing <= 1 then reward(277, 5000, 0) end
end
for _, index in ipairs({50563, 50565, 50585, 50586, 50567, 50569, 50590, 50595}) do handlers[index] = pledge end

-- NPC190.scr (RUDE 190): the maypole (267: 500 gold -> 268, the new maypole stands; without the gold 267 is
-- taken), then PLEDGE.inc's check.
local function maypole()
    cog(401, not has(268)); cog(402, has(268))   -- ChangeModel.scr (Prop0)
end
handlers[50562] = function()
    pledge()
    if not has(268) and has(267) then
        if MM9.hasGold(500) == 1 then MM9.takeGold(500); MM9.giveKey(268) else MM9.takeKey(267) end
    end
    maypole()
end

-- NPC309.scr (Tamur Leng, RUDE 309): hidden until the battle (BattleMan.scr); with key 106 his dialogue's
-- close: 190, 412 000 experience; he joins the party (AddNPC 309: the MM9 hireling, story companion) and leaves
-- the map; Thorolf appears (Thorolf2).
handlers[50069] = function()
    if has(190) or not has(106) then return end
    reward(190, 22500, 0) -- MM9 GiveExp 412000, mm9_quest_xp_profile.yml
    MM9.addHireling(309)
    MM9.removeActor(1)
    show(4, true)
end
-- Forad.scr (Forad Darre, "Hate"): hidden until the battle; the first click 480 and 800 experience; his
-- dialogue's close during the battle (104) turns him on the party; else 368 and 4 000 experience, gone on 29.
-- The click (:OnUse) also turns him to the party (FaceObject, 200 degrees a second) and bows (PlayAnim bow).
handlers[53048] = function()
    if not has(480) then reward(480, 800, 0) end
    local x, y = evt.GetPartyPosition()
    evt.FaceActorTo(0, x, y, 0.5); evt.PlayActorClip(0, "bow", false)
    MM9.openRude(2)
end
handlers[50048] = function()
    if has(104) then   -- Hate: AddEnemy Player; MM9's monster AI walks him at the party (placed still)
        set("ForadTalked", 1)   -- bTalking stays set: he never opens his dialogue by himself again
        evt.ClearActorPresentation(0)   -- the bow's facing goes back to his AI
        evt.SetMonGroupBit(4, MonsterBits.Hostile, true)
        evt.SetActorImmobile(0, false)
        return
    end
    if not has(368) then reward(368, 4000, 0) end
    if has(29) then MM9.removeActor(0) end
end
-- Forad.scr :OnAppear (BattleMan.scr's Appear: battle() below shows him): OnFoundPlayer OnTarget 256 ->
-- target the player, OnTargetWithinDist 16 :Talk: he opens his dialogue himself when the party comes near (the
-- approach talks' poll); with key 104 its close turns him on the party. :Talk and :OnUse set bTalking, which
-- only :Forad (no 104) clears: after that close he never talks by himself again, on later visits too (ForadTalked).
-- Forad.scr :OnDeath: once (key 494), 194 000 experience (capped) and the quest sound.
handlers[236] = function(context)
    if context.actorIndex ~= 0 or has(494) then return end
    reward(494, 18500, 0) -- MM9 GiveExp 194000, mm9_quest_xp_profile.yml
    MM9.playSound("sounds/events/quest.wav")
end

-- NPC378.scr (Thorolf Ratatoskssen, three copies, RUDE 378): Thorolf0/1 here with 83 until 84; talking to one
-- removes the other; Thorolf2 comes after Tamur Leng (106). 107 or 84: he vanishes; 106 or 83: the dialogue
-- reopens.
handlers[53071] = function() MM9.removeActor(3); MM9.openRude(378) end
handlers[50071] = function()
    if has(107) or has(84) then MM9.clientFx(2, "mm9:town_portal"); MM9.removeActor(2); MM9.removeActor(3)
    elseif has(106) or has(83) then MM9.openRude(378) end
end
handlers[53072] = function() MM9.removeActor(2); MM9.openRude(378) end
handlers[50072] = function()
    if has(107) or has(84) then MM9.clientFx(3, "mm9:town_portal"); MM9.removeActor(3); MM9.removeActor(2)
    elseif has(106) or has(83) then MM9.openRude(378) end
end
handlers[53073] = function() MM9.openRude(378) end
handlers[50073] = function()
    if has(107) or has(84) then MM9.clientFx(4, "mm9:town_portal"); MM9.removeActor(4)
    elseif has(106) or has(83) then MM9.openRude(378) end
end

-- BattleMan.scr: the Battle of Frosgard. Entering with key 104 (once: 377): Forad Darre and Tamur Leng appear,
-- the Horde attacks (HordeGrunt/Leader/Warrior: MM9 Horde A/B/C at Atlimarker, BadGuys0, 2, 3) and the clan
-- soldiers come (ClanSoldier/Corporal/Sergeant: the town guard row 9107 at GoodGuys, set against the Horde).
-- Trigger0 (Fight2, the touch line south of the square) adds a wave at BadGuys1 and soldiers at GoodGuys0.
local function summon(row, p, group, hostile, count)
    evt.SummonMonstersById({monster = row, x = p[1], y = p[2], z = p[3], radius = 96, count = count,
        group = group, hostile = hostile, loot = false})
end
-- HateNPC.scr (the Horde's spawn script): AddEnemy NPC, ClanSoldier, KiratheCold: the Horde also goes for the
-- townsfolk (their rows: 9017, 9018, 9024, 9025, 9026, 9027, 9039, 9040, 9043, 9044, 9045, 9050, 9051, 9052, 9053, 9055, 9250; one way, as AddEnemy: MM9's IsFriend asks both
-- sides, and the townsfolk's NPCBase loop flees). Kira the Cold is not in Frosgard City.
local function clansAgainstHorde()
    for _, h in ipairs({9129, 9130, 9131}) do evt.SetMonsterRelation(9107, h, 2); evt.SetMonsterRelation(h, 9107, 2) end
    for _, h in ipairs({9129, 9130, 9131}) do for _, t in ipairs({9017, 9018, 9024, 9025, 9026, 9027, 9039, 9040, 9043, 9044, 9045, 9050, 9051, 9052, 9053, 9055, 9250}) do evt.SetMonsterRelation(h, t, 2) end end
end
local function battle()
    MM9.giveKey(377)
    show(0, true); show(1, true)
    clansAgainstHorde()
    summon(9129, {7700, -901, 0}, 6, true, 2)   -- Atlimarker
    summon(9130, {7700, -901, 0}, 6, true, 1)   -- Atlimarker
    summon(9131, {7700, -901, 0}, 6, true, 1)   -- Atlimarker
    summon(9129, {5243, -4342, 0}, 6, true, 2)   -- BadGuys0
    summon(9130, {5243, -4342, 0}, 6, true, 1)   -- BadGuys0
    summon(9129, {5734, 4424, 19}, 6, true, 2)   -- BadGuys2
    summon(9130, {5734, 4424, 19}, 6, true, 1)   -- BadGuys2
    summon(9131, {-1393, -1638, 0}, 6, true, 2)   -- BadGuys3
    summon(9107, {7291, -2048, 0}, 7, false, 4)   -- GoodGuys
end
handlers[234] = function()   -- Trigger0 (BattleMan :OnFight2)
    if not has(104) or var("Fight2") == 1 then return end
    set("Fight2", 1); clansAgainstHorde()
    summon(9129, {5161, 1720, 0}, 6, true, 2)
    summon(9130, {5161, 1720, 0}, 6, true, 1)
    summon(9131, {5161, 1720, 0}, 6, true, 1)
    summon(9107, {2785, 1147, 0}, 7, false, 3)
end

-- BookLetter.scr letters (BOOK AND SCROLL TEXT.csv rows), Book.scr's book (no text in MM9), TownPortal.scr.
-- TownPortal0: TownPortal.scr "Frosgard": cleansing the altar gives key 5015 and MM9 swaps its dirty skin for
-- the clean one: TownPortal0 (SetSprite 490) hides and TownPortal0Clean (491, the clean
-- altar at its place) shows; the map load does the same once the key is set (:Init FixCheck).
local function townPortalAltar()
    local clean = has(5015)
    evt.SetSprite(490, clean and 0 or 1, "0"); evt.SetSprite(491, clean and 1 or 0, "0")
end
handlers[330] = function()
    if has(5015) then return end
    MM9.giveKey(5015); quest()
    townPortalAltar()
    evt.StatusText("The altar is cleansed.")
end
handlers[331] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0) end   -- Book1 (Book.scr: pages turn, no text)
handlers[332] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Warning\n\nThe Frost Giant has once again resumed activity.  It is recommended that you keep track of your children after dark, and under no circumstances should you let them wander near the magic waterfall.\n\nSigned,\nHelron Bjarnissen\nWatch Commander") end   -- Prop6 (462)
handlers[333] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Unfinshed letter to Gyira\n\nDear Gyira,\nI pray that this letter reaches you.  I am still in Frosgard after we parted ways six months ago.  The docks have all been frozen up, and there is no way for a ship to come in or out.  The countryside is too dangerous for me to travel to Thronheim.  I pray that the ice will break up soon, and I shall be able to reach you.\n\nYour friend,") end   -- Prop7 (463)
handlers[334] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Unfinished poem to the Green Man\n\nThe Green Man\nMay we say how bold,\nOr pray you are not too old\nTo come again to visit\nFor a pledge we will give it\n\nShould your return come soon\nTo bring the flowers...") end   -- Prop8 (464)
handlers[335] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Letter to Dockmaster\n\nDockmaster Streveens,\nI've been made away that there is some grain being kept in one of your warehouses.  I've also been made aware that due to your lack of proper handling, some of it has started rotting.  I shall be sending some men over to take charge of the warehouse.  I expect that you will give them your full cooperation, lest I take this up with Jarl Tryygva himself.\n\nWalteir") end   -- Prop9 (465)

-- NPC214.scr :OnStart (Douglas's OnFoundPlayer, SightDistance 600 LT): without key 111 he and Robert (NPC213.scr)
-- argue, the cinematic bob_and_doug (no cameras); here on the poll once he sees the party within that range.
local function banter()
    if not has(111) and evt.ActorSeesParty(34, 1536) then MM9Cinematic.start("bob_and_doug") end
end
local function poll()
    shopHours()
    banter()
    evt.StartTimer(260, seconds(1))
end
handlers[260] = poll
handlers[1] = function()   -- map load
    for k = 1024, 1033 do if k ~= 1029 and has(k) then MM9.takeKey(k) end end
    MM9.giveKey(1029)
    if var("BankOpen") == 1 then set("BankOpen", 0); bankHatch(false) end
    show(5, has(108) or not (has(104) or has(40)))   -- NPC180.scr :Init
    if not has(377) then show(0, false); show(1, false) end   -- Forad.scr "Hate", NPC309.scr :Main
    local thorolf = has(83) and not has(84)   -- NPC378.scr :Init
    show(2, thorolf); show(3, thorolf); show(4, has(106) and not has(107))
    show(35, not has(460))   -- Retainer.scr (238: key 460): hidden while hired
    cog(403, has(278))   -- HideModel.scr "278 UnHide": the runestone
    cog(404, has(1022) and var("BarrelGone") == 0 and not has(72))   -- NPC215.scr :Init
    maypole()
    if has(72) or has(174) then iceGone() end   -- BreakIce.scr :Init (TELP 1.3)
    if has(104) and not has(377) then battle() end   -- BattleMan.scr :Init
    townPortalAltar()   -- TownPortal.scr :Init (FixCheck): the clean altar once its key is set
    poll()
end
-- MM9's approach talks (dungeon/lua.py approach_talk): an NPC whose script talks when the party comes
-- within 16 LT of his body (OnTargetWithinDist / RunTo 16 -> DoRude). reach: the feet's distance at which
-- he talks; sight > 0: he runs to the party once he sees it within that range. Once per visit.
local APPROACH_TALKS = {
    {actor = 0, reach = 140, sight = 0, armed = function() return has(104) and var("ForadTalked") == 0 end,
        talk = function() MM9.openRude(2, 0) end},   -- ForadDarre: FORAD.scr :OnAppear OnTargetWithinDist 16 :Talk
    {actor = 2, reach = 109, sight = 1536, armed = function() return not has(107) and (not has(84) or has(106)) end,
        talk = function() MM9.removeActor(3); MM9.openRude(378, 2); MM9.playSound("voices/npc/npc_378.wav") end},   -- Thorolf0: NPC378.scr :OnFound RunTo 16 :Talk
    {actor = 3, reach = 109, sight = 1536, armed = function() return not has(107) and (not has(84) or has(106)) end,
        talk = function() MM9.removeActor(2); MM9.openRude(378, 3); MM9.playSound("voices/npc/npc_378.wav") end},   -- Thorolf1: NPC378.scr :OnFound RunTo 16 :Talk
    {actor = 4, reach = 109, sight = 1536, armed = function() return not has(107) and (not has(84) or has(106)) end,
        talk = function() MM9.removeActor(2); MM9.openRude(378, 4); MM9.playSound("voices/npc/npc_378.wav") end},   -- Thorolf2: NPC378.scr :OnFound RunTo 16 :Talk
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
handlers[53069] = function() MM9.playSound("voices/npc/npc_309.wav"); MM9.openRude(309) end   -- TamurLeng0
do local own = handlers[53075]; handlers[53075] = function() MM9.playSound("voices/npc/npc_180.wav"); own() end end   -- TryggvaRavenlocks0
handlers[53552] = function() MM9.playSound("voices/npc/npc_207.wav"); MM9.openRude(207) end   -- Apothecary
do local own = handlers[53553]; handlers[53553] = function() MM9.playSound("voices/npc/npc_206.wav"); own() end end   -- Banker
handlers[53554] = function() MM9.playSound("voices/npc/npc_209.wav"); MM9.openRude(209) end   -- Dockmaster
handlers[53555] = function() MM9.playSound("voices/npc/npc_212.wav"); MM9.openRude(212) end   -- Librarian0
handlers[53556] = function() MM9.playSound("voices/npc/npc_208.wav"); MM9.openRude(208) end   -- Healer
handlers[53557] = function() MM9.playSound("voices/npc/npc_211.wav"); MM9.openRude(211) end   -- Librarian
handlers[53558] = function() MM9.playSound("voices/npc/npc_185.wav"); MM9.openRude(185) end   -- 185
handlers[53559] = function() MM9.playSound("voices/npc/npc_183.wav"); MM9.openRude(183) end   -- 183
handlers[53560] = function() MM9.playSound("voices/npc/npc_184.wav"); MM9.openRude(184) end   -- 184
handlers[53561] = function() MM9.playSound("voices/npc/npc_188.wav"); MM9.openRude(188) end   -- 188
handlers[53562] = function() MM9.playSound("voices/npc/npc_190.wav"); MM9.openRude(190) end   -- 190
handlers[53563] = function() MM9.playSound("voices/npc/npc_191.wav"); MM9.openRude(191) end   -- 191
handlers[53564] = function() MM9.playSound("voices/npc/npc_192.wav"); MM9.openRude(192) end   -- 192
handlers[53565] = function() MM9.playSound("voices/npc/npc_193.wav"); MM9.openRude(193) end   -- 193
handlers[53566] = function() MM9.playSound("voices/npc/npc_194.wav"); MM9.openRude(194) end   -- 194
handlers[53567] = function() MM9.playSound("voices/npc/npc_197.wav"); MM9.openRude(197) end   -- 197
handlers[53568] = function() MM9.playSound("voices/npc/npc_198.wav"); MM9.openRude(198) end   -- 198
handlers[53569] = function() MM9.playSound("voices/npc/npc_199.wav"); MM9.openRude(199) end   -- 199
handlers[53570] = function() MM9.playSound("voices/npc/npc_201.wav"); MM9.openRude(201) end   -- 201
handlers[53581] = function() MM9.playSound("voices/npc/npc_238.wav"); MM9.openRude(238) end   -- 238
handlers[53585] = function() MM9.playSound("voices/npc/npc_195.wav"); MM9.openRude(195) end   -- 195
handlers[53586] = function() MM9.playSound("voices/npc/npc_196.wav"); MM9.openRude(196) end   -- 196
handlers[53588] = function() MM9.playSound("voices/npc/npc_203.wav"); MM9.openRude(203) end   -- 203
handlers[53589] = function() MM9.playSound("voices/npc/npc_200.wav"); MM9.openRude(200) end   -- 200
do local own = handlers[53593]; handlers[53593] = function() MM9.playSound("voices/npc/npc_181.wav"); own() end end   -- 181
handlers[53594] = function() MM9.playSound("voices/npc/npc_182.wav"); MM9.openRude(182) end   -- 182
handlers[53596] = function() MM9.playSound("voices/npc/npc_210.wav"); MM9.openRude(210) end   -- 210

-- MM9's bonus props (dungeon/objects.py bonus_lines; the use of each class, object.lto): wells, cauldrons,
-- cook pots and clovers.
handlers[30716] = function() MM9.useClover(716, "frosgardcity:Clover0") end   -- Clover0 (Clover)
handlers[30717] = function() MM9.useClover(717, "frosgardcity:Clover1") end   -- Clover1 (Clover)

-- MM9's exploding destructibles (Exploding 1): breaking deals ExplodeDamage within DamageRadius of its
-- centre to the party and to the other exploding destructibles there (the next of a chain breaks then).
local EXPLODING = {[45] = {{16302, -2212, 11}, 512, 100}, [607] = {{4260, -11796, -280}, 512, 100}}
local function explode(id)
    local e = EXPLODING[id]
    local c, r = e[1], e[2]
    evt.SpawnWorldEffect("mm9:column_of_fire", c[1], c[2], c[3], 0.6)
    local x, y, z = evt.GetPartyPosition()
    local dz = math.max(0, c[3] - (z + 170), z - c[3])
    if (x - c[1]) ^ 2 + (y - c[2]) ^ 2 + dz ^ 2 <= r * r then
        evt.DamagePlayer(Players.All, const.Damage.Fire, e[3])
    end
    for other, o in pairs(EXPLODING) do
        local q = o[1]
        if other ~= id and (q[1] - c[1]) ^ 2 + (q[2] - c[2]) ^ 2 + (q[3] - c[3]) ^ 2 <= r * r then
            evt.DamageDestructible(other, e[3])
        end
    end
end
-- MM9's breaking destructibles: an urn's SpawnObject TreasureBag drops (evt.SpawnLootContainer).
handlers[30045] = function() explode(45) end   -- DestructableProp1
handlers[30607] = function() explode(607) end   -- DestructableProp0

-- MM9's PerceptionBrushes (dungeon/perception.py): the red glow shows to a party whose Perception reaches the
-- brush's PerceptionValue, checked on load and every 3 s; map Lua turns one off for good with
-- set("HintOff<cog>", 1) (MM9's Off message to the brush).
local HINTS = {[23672] = 0, [23673] = 0, [23674] = 0, [23675] = 0, [23676] = 0, [23677] = 0, [23678] = 0, [23679] = 0, [23680] = 0, [23681] = 0, [23682] = 0}
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

-- MM9's people posed by their scripts' :Init loopanim (dungeon/lua.py init_poses): every load.
handlers[907] = function()
    evt.PlayActorClip(5, "sit", true); evt.FaceActorTo(5, -3512, -1633, 0)   -- Tryygva Ravenlocks: NPC180.scr :Init loopanim
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
RegisterEvent(230, "Locked door", handlers[230], "Door")
RegisterEvent(231, "Bank", handlers[231], "Bank")
RegisterEvent(53553, "Banker", handlers[53553])
RegisterEvent(50553, "Banker", handlers[50553])
RegisterMapTimerEvent(235, seconds(3), handlers[235], "Cannon", "", seconds(3))
RegisterEvent(232, "Powder barrel", handlers[232], "Barrel")
RegisterEvent(50571, "Powder seller", handlers[50571])
RegisterEvent(50554, "Dockmaster", handlers[50554])
RegisterEvent(233, "Well", handlers[233], "Well")
RegisterEvent(53075, "Tryggva", handlers[53075])
RegisterEvent(50075, "Tryggva", handlers[50075])
RegisterEvent(53593, "181", handlers[53593])
RegisterEvent(50593, "181", handlers[50593])
RegisterEvent(50559, "183", handlers[50559])
RegisterEvent(50560, "184", handlers[50560])
RegisterEvent(50561, "188", handlers[50561])
RegisterEvent(50562, "190", handlers[50562])
RegisterEvent(50563, "Pledge 191", handlers[50563])
RegisterEvent(50565, "Pledge 193", handlers[50565])
RegisterEvent(50585, "Pledge 195", handlers[50585])
RegisterEvent(50586, "Pledge 196", handlers[50586])
RegisterEvent(50567, "Pledge 197", handlers[50567])
RegisterEvent(50569, "Pledge 199", handlers[50569])
RegisterEvent(50590, "Pledge 217", handlers[50590])
RegisterEvent(50595, "Pledge 218", handlers[50595])
RegisterEvent(50069, "Tamur Leng", handlers[50069])
RegisterEvent(53048, "Forad Darre", handlers[53048])
RegisterEvent(50048, "Forad", handlers[50048])
RegisterEvent(53071, "Thorolf", handlers[53071])
RegisterEvent(50071, "Thorolf", handlers[50071])
RegisterEvent(53072, "Thorolf", handlers[53072])
RegisterEvent(50072, "Thorolf", handlers[50072])
RegisterEvent(53073, "Thorolf", handlers[53073])
RegisterEvent(50073, "Thorolf", handlers[50073])
RegisterEvent(234, "Trigger0", handlers[234])
RegisterEvent(330, "TownPortal0", handlers[330], "Altar")
RegisterEvent(331, "Book1", handlers[331], "Book")
RegisterEvent(332, "Prop6", handlers[332], "Read")
RegisterEvent(333, "Prop7", handlers[333], "Read")
RegisterEvent(334, "Prop8", handlers[334], "Read")
RegisterEvent(335, "Prop9", handlers[335], "Read")
RegisterMapTimerEvent(260, seconds(3), handlers[260], "Poll", "", seconds(3))
RegisterEvent(1, "Map load", handlers[1])
RegisterMapTimerEvent(906, seconds(3), handlers[906], "Approach talks", "", seconds(3))
RegisterEvent(53069, "Tamur Leng", handlers[53069])
RegisterEvent(53552, "Gotthorm Stonecaster", handlers[53552])
RegisterEvent(53554, "Jozka Atlia", handlers[53554])
RegisterEvent(53555, "Vel Dra'dna", handlers[53555])
RegisterEvent(53556, "Leif the Lucky", handlers[53556])
RegisterEvent(53557, "Halfdan the Rude", handlers[53557])
RegisterEvent(53558, "Ronan A'Dlinn", handlers[53558])
RegisterEvent(53559, "Skulkil the Dark", handlers[53559])
RegisterEvent(53560, "Brewmaster Smith", handlers[53560])
RegisterEvent(53561, "Nath'i A'Mor", handlers[53561])
RegisterEvent(53562, "Soxolf Tryygvassen", handlers[53562])
RegisterEvent(53563, "Gudrun Fyridotir", handlers[53563])
RegisterEvent(53564, "Goti Egilssen", handlers[53564])
RegisterEvent(53565, "Tuathal A'Ghrie", handlers[53565])
RegisterEvent(53566, "Hjalnek the Orc-faced", handlers[53566])
RegisterEvent(53567, "Rannveig the Elvish", handlers[53567])
RegisterEvent(53568, "Fyri the Black-heart", handlers[53568])
RegisterEvent(53569, "Erik the Fish-head", handlers[53569])
RegisterEvent(53570, "Tryygva Ironhands", handlers[53570])
RegisterEvent(53581, "Sowelu Axeldotir", handlers[53581])
RegisterEvent(53585, "Tjorvi the Bold", handlers[53585])
RegisterEvent(53586, "Jozka Dorcan", handlers[53586])
RegisterEvent(53588, "Thora the Skull-toucher", handlers[53588])
RegisterEvent(53589, "Egil Skallagrimsson", handlers[53589])
RegisterEvent(53594, "Menja Ketildotir", handlers[53594])
RegisterEvent(53596, "Trota Atlia", handlers[53596])
RegisterEvent(30716, "Clover", handlers[30716], "Pick")
RegisterEvent(30717, "Clover", handlers[30717], "Pick")
RegisterEvent(30045, "DestructableProp1", handlers[30045])
RegisterEvent(30607, "DestructableProp0", handlers[30607])
RegisterMapTimerEvent(901, seconds(3), handlers[901], "Perception hints", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
RegisterEvent(907, "Script poses", handlers[907])
RegisterMonsterKilledHook(236, "Forad Darre killed", handlers[236])


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

-- Cinematic break_ice (BreakIce.scr :OnStart..:Done, IceCam1.scr): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["break_ice"] = {
    { "shooter1", function()
        evt.FireMissile("Fire", 5571, -8684, 901, 5571, -8684, -348, 0, "Fire", 0); MM9.launchSound("FireBolt", 5571, -8684, 901)
    end },
    { "floe27", function()
        floes({"DestructableBrush27"})
    end },
    { "shooter2", function()
        evt.FireMissile("Fire", 3359, -8028, 901, 3359, -8028, -348, 0, "Fire", 0); MM9.launchSound("FireBolt", 3359, -8028, 901)
    end },
    { "floe17", function()
        floes({"DestructableBrush17"})
    end },
    { "shooter3", function()
        evt.FireMissile("Fire", 2785, -8110, 901, 2785, -8110, -348, 0, "Fire", 0); MM9.launchSound("FireBolt", 2785, -8110, 901)
    end },
    { "floe18", function()
        floes({"DestructableBrush18"})
    end },
    { "shooter4", function()
        evt.FireMissile("Fire", 2376, -7700, 901, 2376, -7700, -348, 0, "Fire", 0); MM9.launchSound("FireBolt", 2376, -7700, 901)
    end },
    { "floe6", function()
        floes({"DestructableBrush6"})
    end },
    { "floe15", function()
        floes({"DestructableBrush15"})
    end },
    { "floe26", function()
        floes({"DestructableBrush26"})
    end },
    { "floe25", function()
        floes({"DestructableBrush25"})
    end },
    { "group1", function()
        floes({"DestructableBrush16", "DestructableBrush14", "DestructableBrush21", "DestructableBrush24", "DestructableBrush30", "DestructableBrush33", "DestructableBrush36", "DestructableBrush39", "DestructableBrush42", "DestructableBrush45", "DestructableBrush9"})
    end },
    { "group2", function()
        floes({"DestructableBrush19", "DestructableBrush22", "DestructableBrush28", "DestructableBrush31", "DestructableBrush34", "DestructableBrush37", "DestructableBrush40", "DestructableBrush43", "DestructableBrush7"})
    end },
    { "group3", function()
        floes({"DestructableBrush20", "DestructableBrush23", "DestructableBrush29", "DestructableBrush32", "DestructableBrush35", "DestructableBrush38", "DestructableBrush41", "DestructableBrush44", "DestructableBrush8"})
    end },
    { "points", function()
        iceReward()
    end },
}
RegisterEvent(36001, "Cinema break_ice: shooter1", function() MM9Cinematic.runStep("break_ice", 1) end)
RegisterEvent(36002, "Cinema break_ice: floe27", function() MM9Cinematic.runStep("break_ice", 2) end)
RegisterEvent(36003, "Cinema break_ice: shooter2", function() MM9Cinematic.runStep("break_ice", 3) end)
RegisterEvent(36004, "Cinema break_ice: floe17", function() MM9Cinematic.runStep("break_ice", 4) end)
RegisterEvent(36005, "Cinema break_ice: shooter3", function() MM9Cinematic.runStep("break_ice", 5) end)
RegisterEvent(36006, "Cinema break_ice: floe18", function() MM9Cinematic.runStep("break_ice", 6) end)
RegisterEvent(36007, "Cinema break_ice: shooter4", function() MM9Cinematic.runStep("break_ice", 7) end)
RegisterEvent(36008, "Cinema break_ice: floe6", function() MM9Cinematic.runStep("break_ice", 8) end)
RegisterEvent(36009, "Cinema break_ice: floe15", function() MM9Cinematic.runStep("break_ice", 9) end)
RegisterEvent(36010, "Cinema break_ice: floe26", function() MM9Cinematic.runStep("break_ice", 10) end)
RegisterEvent(36011, "Cinema break_ice: floe25", function() MM9Cinematic.runStep("break_ice", 11) end)
RegisterEvent(36012, "Cinema break_ice: group1", function() MM9Cinematic.runStep("break_ice", 12) end)
RegisterEvent(36013, "Cinema break_ice: group2", function() MM9Cinematic.runStep("break_ice", 13) end)
RegisterEvent(36014, "Cinema break_ice: group3", function() MM9Cinematic.runStep("break_ice", 14) end)
RegisterEvent(36015, "Cinema break_ice: points", function() MM9Cinematic.runStep("break_ice", 15) end)
RegisterEvent(36000, "Cinema break_ice: done", function() MM9Cinematic.finish("break_ice") end)
MM9Cinematic.play["break_ice"] = function()
    if evt.GetMapVar("Cinema.break_ice.started", 0) == 0 then
        evt.SetMapVar("Cinema.break_ice.started", 1)
        evt.PlayCinematic("break_ice", 36000)
    end
end

-- Cinematic bob_and_doug (NPC214.scr :OnStart..:OnSpeak9, NPC213.scr): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["bob_and_doug"] = {
    { "key", function()
        MM9.giveKey(111)
    end },
}
RegisterEvent(36051, "Cinema bob_and_doug: key", function() MM9Cinematic.runStep("bob_and_doug", 1) end)
RegisterEvent(36050, "Cinema bob_and_doug: done", function() MM9Cinematic.finish("bob_and_doug") end)
MM9Cinematic.play["bob_and_doug"] = function()
    if evt.GetMapVar("Cinema.bob_and_doug.started", 0) == 0 then
        evt.SetMapVar("Cinema.bob_and_doug.started", 1)
        evt.PlayCinematic("bob_and_doug", 36050)
    end
end

-- DestructableProp0's death (DeathTriggerTarget Shooter0 Start): broken, the barrel sets the ice off as its click
-- does (handler 232), after its shared explosion.
do
    local exploded = handlers[30607]
    handlers[30607] = function()
        if exploded ~= nil then exploded() end
        handlers[232]()
    end
    RegisterEvent(30607, "DestructableProp0", handlers[30607])
end
