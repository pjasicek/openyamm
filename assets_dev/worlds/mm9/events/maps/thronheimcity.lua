-- Thronheim City, MM9 rework (level_generation/projects/mm9r_thronheimcity/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {CounselDoor0 = 1, CounselDoor1 = 2, Door1 = 3, Door2 = 4, Door3 = 5, Door4 = 6, InnDoor1 = 7, InnDoor2 = 8, KiraDoor1 = 9, KiraDoor2 = 10, LibraryDoor1 = 11, LibraryDoor2 = 12, Magic0 = 13, Prisondoor0 = 14, Prisondoor1 = 15, RotatingDoor11 = 16, RotatingDoor12 = 17, RotatingDoor13 = 18, RotatingDoor14 = 19, RotatingDoor15 = 20, RotatingDoor16 = 21, RotatingDoor17 = 22, RotatingDoor3 = 23, RotatingDoor4 = 24, RotatingDoor6 = 25, RotatingDoor7 = 26, RotatingDoor8 = 27, RotatingDoor9 = 28, Secretdoor0 = 29, Secretdoor0_INV = 30, TempleRatDoor1 = 31, TempleRatDoor2 = 32, TempleThronDoor1 = 34, TempleThronDoor2 = 33, TownHallDoor1 = 35, TownHallDoor2 = 36, WeaponDoor1 = 38, WeaponDoor2 = 37, vaultdoor = 39}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 906, 902, 907}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(1, DoorAction.Trigger) evt.SetDoorState(2, DoorAction.Trigger) end   -- CounselDoor0
handlers[102] = function() evt.SetDoorState(11, DoorAction.Trigger) evt.SetDoorState(12, DoorAction.Trigger) end   -- LibraryDoor1
handlers[103] = function() evt.SetDoorState(13, DoorAction.Trigger) end   -- Magic0
handlers[104] = function() evt.SetDoorState(16, DoorAction.Trigger) evt.SetDoorState(17, DoorAction.Trigger) end   -- RotatingDoor11
handlers[105] = function() evt.SetDoorState(20, DoorAction.Trigger) evt.SetDoorState(21, DoorAction.Trigger) end   -- RotatingDoor15
handlers[106] = function() evt.SetDoorState(22, DoorAction.Trigger) end   -- RotatingDoor17
handlers[107] = function() evt.SetDoorState(24, DoorAction.Trigger) end   -- RotatingDoor4
handlers[108] = function() evt.SetDoorState(25, DoorAction.Trigger) evt.SetDoorState(26, DoorAction.Trigger) end   -- RotatingDoor6
handlers[109] = function() evt.SetDoorState(27, DoorAction.Trigger) evt.SetDoorState(28, DoorAction.Trigger) end   -- RotatingDoor8
handlers[110] = function() evt.SetDoorState(31, DoorAction.Trigger) evt.SetDoorState(32, DoorAction.Trigger) end   -- TempleRatDoor1
handlers[111] = function() evt.SetDoorState(33, DoorAction.Trigger) evt.SetDoorState(34, DoorAction.Trigger) end   -- TempleThronDoor1
handlers[112] = function() evt.SetDoorState(35, DoorAction.Trigger) evt.SetDoorState(36, DoorAction.Trigger) end   -- TownHallDoor1
handlers[113] = function() evt.SetDoorState(37, DoorAction.Trigger) evt.SetDoorState(38, DoorAction.Trigger) end   -- WeaponDoor1
handlers[114] = function() evt.SetDoorState(29, DoorAction.Trigger) evt.SetDoorState(30, DoorAction.Trigger) end   -- Secretdoor0

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest0

local function has(k) return MM9.hasKey(k) == 1 end
local function quest() MM9.playSound("sounds/events/quest.wav") end
local function show(a, on) evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end
local function sprite(cog, on) if cog then evt.SetSprite(cog, on and 1 or 0, "0") end end
local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; if gold > 0 then MM9.giveGold(gold) end; quest() end
local COG = {TreatyProp = 406, BookProp = 407, MarkeProp0 = 408}

-- MM9's locked doors (Locked 1, no key): facade doors, the safe, the guard house, the second inn, the cells,
-- the bank vault.
handlers[230] = function()
    evt.PlaySoundName("door/doorlock01.wav", 0, 0, 0)
    evt.StatusText("The door is locked.")
end

-- ForadWorld.scr (ScriptObject0, "Thronheim"): key 1030 is the party's location while here (keys 1024-1033
-- are the towns'); key 5017 closes the shops and the bank from 20:00 to 06:00.
local function shopHours()
    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24
    local closed = hour >= 20 or hour < 6
    if closed and not has(5017) then MM9.giveKey(5017) elseif not closed and has(5017) then MM9.takeKey(5017) end
end

-- ARG_Unhide.scr: the six Jarls, the book and the treaty sit in Kira's council room from both signatures (keys 90,
-- 91) until Bikki's prize is won (94); Markel alive until the council (40). NPC239.scr removes the dead Markel
-- (MarkeProp0) on every load after it. The Jarls are actors on their HD models looping Sit (rude_props.py).
local function councilProps()
    local council = has(90) and has(91) and not has(94)
    show(44, council)   -- SvenProp
    show(45, council)   -- TryygvaProp
    show(46, council and not has(40))   -- MarkeProp
    show(47, council)   -- ForadProp
    show(48, council)   -- SigmundProp
    show(49, council)   -- BjarniProp
    sprite(COG.TreatyProp, council)
    sprite(COG.BookProp, council)
    sprite(COG.MarkeProp0, false)
end

-- ARGUMENT.scr (Argueman; KiraDoor2 sends it "start" when it opens): with both Jarls' signatures (keys 90, 91)
-- and no council yet (40), the war council: the cinematic council_argument (council.py; its steps are the
-- cinematic block at the end of this file). :War, the reward: keys 184, 40, 85 and 93, 26 500 experience, the
-- Peace Treaty (401) taken. Forad leaves the party at :Cam2b (RemoveNPC 2: the MM9 hireling; key 29 stays).
local function war()
    if has(184) then return end
    MM9.giveKey(184); MM9.giveKey(40); MM9.giveKey(85); MM9.giveExperience(12500); quest() -- MM9 GiveExp 26500, mm9_quest_xp_profile.yml
    MM9.takeItem(401, "thronheimcity:Kira")
    MM9.giveKey(93)
end
handlers[232] = function()   -- KiraDoor1/2
    evt.SetDoorState(DOORS["KiraDoor1"], DoorAction.Trigger) evt.SetDoorState(DOORS["KiraDoor2"], DoorAction.Trigger)
    if has(90) and has(91) and not has(40) then MM9Cinematic.start("council_argument") end
end

-- ARG_Yrsa.scr (Yrsa the Troll, RUDE 1): she appears after the council; talking gives key 93 (her errand: the
-- prize at the Thing in Thjorgard), the exit gives 185 and she vanishes. MM9 shows her only during that
-- session; here she also waits on later visits until 185 (README).
handlers[53230] = function()
    MM9.giveKey(93)
    MM9.openRude(1)
end
handlers[50230] = function()
    if not has(185) and has(93) then
        quest(); MM9.giveKey(185)
        MM9.clientFx(42, "mm9:GreaterDemon")   -- :Vanish: DoClientFX g_hMyObject, GreaterDemon
        MM9.removeActor(42)
    end
end

-- NPC239.scr (Kira the Cold, RUDE 239): a click with all five clan keys (34, 38, 51, 63, 74) gives 178; the
-- exit pays the love letter (147, item 247 taken), the Honkies gone (146), the Mountain Pass (152), the clans
-- united (179) and the treaty written (181, item 401 given).
handlers[53228] = function()
    if not has(178) and has(34) and has(38) and has(51) and has(63) and has(74) then MM9.giveKey(178) end
    MM9.openRude(239)
end
handlers[50228] = function()
    if not has(147) and has(23) then
        MM9.takeItem(247, "thronheimcity:Kira"); reward(147, 12000, 0)
    end
    if not has(146) and has(78) then reward(146, 12500, 7000) end -- MM9 GiveExp 40000, mm9_quest_xp_profile.yml
    if not has(152) and has(81) then reward(152, 12500, 12000) end -- MM9 GiveExp 120000, mm9_quest_xp_profile.yml
    if not has(179) and has(83) then MM9.giveKey(179); MM9.giveExperience(12500); MM9.giveGold(6000) end -- MM9 GiveExp 26500, mm9_quest_xp_profile.yml
    if not has(181) and has(89) then
        reward(181, 12000, 0); MM9.giveItem(401, "thronheimcity:Kira")
    end
end
-- NPC239.scr's clock (@M 6:00): agreed to write the treaty (88) -> 180 at the next 06:00. MM9 fires it only
-- with the map loaded; here the poll gives it once a 06:00 has passed since the poll first saw key 88.
local function kiraClock()
    if has(180) or not has(88) then return end
    local mark = math.floor((evt.CurrentGameMinutes() - 360) / 1440) + 2
    if var("Kira88") == 0 then set("Kira88", mark) elseif mark > var("Kira88") then MM9.giveKey(180) end
end

-- ARG_Yrsa.scr :OnAppear (the council's :End2 sends appear): wait 5 :Appear2 (the summoning glow's windup),
-- wait 2 :Appear2b (Town Portal's sound, she shows, fidget1), then :DoRude: key 93 (TELP 1.3), her greeting
-- and RUDE 1 (council.py).
local function soundAt(actorIndex, name)   -- a sound where the actor stands
    local x, y, z = evt.GetMapActorPosition(actorIndex)
    if x ~= nil then evt.PlaySoundName(name, math.floor(x), math.floor(y), math.floor(z)) end
end
handlers[36040] = function()
    local stage = var("YrsaAppear")
    if stage == 1 then
        set("YrsaAppear", 2); evt.StartTimer(36040, seconds(2))
        soundAt(42, "magic/windup10.wav"); MM9.clientFx(42, "mm9:GreaterDemon")   -- :Appear2: DoClientFX g_hMyObject, GreaterDemon
    elseif stage == 2 then
        set("YrsaAppear", 3); evt.StartTimer(36040, seconds(3))
        soundAt(42, "spells/townportal.wav")
        if not has(185) then show(42, true); evt.PlayActorClip(42, "Fidget") end
    elseif stage == 3 then
        set("YrsaAppear", 4)
        if not has(185) then
            MM9.giveKey(93); MM9.playSound("voices/npc/npc_001.wav"); MM9.openRude(1, 42)
        end
    end
end

-- KnutSpeech.scr (Knut Fastmouth, "Ake") and Ake.scr: when Knut first finds the party (OnFoundPlayer:
-- within his sight, 1536) he rants (Conv; a second later :Speak: key 114 and his 91 s speech at
-- him); Ake heckles (ake01-05.wav at Ake, facing Knut) on Ake.scr's waits until :shutup, 5 s before its end.
-- Ambient as in MM9 (the party keeps control); once (key 114). MM9's four-place cycle is not carried.
local KNUT_HECKLES = {[8] = "01", [17] = "02", [27] = "03", [36] = "04", [45] = "05", [55] = "01", [64] = "02", [74] = "03", [83] = "04"}
handlers[36050] = function()
    evt.StartTimer(36050, seconds(1))
    local clock = var("KnutClock")
    local kx, ky, kz = evt.GetMapActorPosition(28)
    if clock < 0 or kx == nil then return end
    if clock == 0 then
        if has(114) then set("KnutClock", -1) return end
        if not MM9.actorAlive(28) then return end   -- a dead Knut's OnFoundPlayer does not fire
        local x, y, z = evt.GetPartyPosition()
        if (x - kx) ^ 2 + (y - ky) ^ 2 > 1536 ^ 2 or math.abs(z - kz) > 512 then return end
        evt.PlayActorClip(28, "talk", true)   -- :OnBlabber: Conv
        set("KnutClock", 1) return
    end
    clock = clock + 1
    set("KnutClock", clock)
    local t = clock - 2   -- seconds after :Speak
    if t == 0 then
        MM9.giveKey(114); soundAt(28, "voices/cinema/socialism/knutfastmouth01.wav")
        -- :Speak sends Ake blabber; his heckles run on his own waits from there: a dead Ake takes no message
        set("AkeHeckles", MM9.receives("thronheimcity", "Ake", "blabber", 16) and 1 or 0)
    elseif KNUT_HECKLES[t] ~= nil and var("AkeHeckles") == 1 then
        evt.FaceActorTo(16, kx, ky, 0.4); evt.PlayActorClip(16, "talk")
        soundAt(16, "voices/cinema/socialism/ake" .. KNUT_HECKLES[t] .. ".wav")
    elseif t == 86 then
        evt.ClearActorPresentation(28); evt.ClearActorPresentation(16)   -- :shutup
    elseif t >= 91 then
        set("KnutClock", -1)
    end
end

-- HONKIES.scr (the three Honk missionaries, RUDE 271, 272, 279): with the dock captain's plan (key 145), each one
-- persuaded (142, 143, 144) leaves for the docks (:Walk: runs to HonkyMarker, gone there: :OnShanghai);
-- the third gives key 77 and 8 000 experience. Gone on 77 (a load removes the persuaded ones at once).
-- (MM9 sends every Honk whose dialogue closes with 145 and any of the three keys; here only the persuaded one.)
local HONKY_MARKER = {14664, 82, 3092}
local function honkLeaves(actor, arrival)
    local m = HONKY_MARKER
    if not evt.MoveActorTo(actor, m[1], m[2], m[3], arrival, true) then MM9.removeActor(actor) end
end
local function honksDone()
    local n = 0
    for _, k in ipairs({142, 143, 144}) do if has(k) then n = n + 1 end end
    if n == 3 and not has(77) then reward(77, 8000, 0) end
end
handlers[50056] = function()
    if has(145) and has(142) then honkLeaves(1, 265); honksDone() end
end
handlers[265] = function() MM9.removeActor(1) end
handlers[50058] = function()
    if has(145) and has(143) then honkLeaves(3, 266); honksDone() end
end
handlers[266] = function() MM9.removeActor(3) end
handlers[50057] = function()
    if has(145) and has(144) then honkLeaves(2, 267); honksDone() end
end
handlers[267] = function() MM9.removeActor(2) end

-- BANKORB.scr (Brynhildr the Money-wise, RUDE 243, "Thronheim"): the Orb of Linking. A click with the orb
-- (item 252) after the quest (322) unlocks the row that installs it (330); the exit places it (331 -> 328) and
-- the sixth bank's orb pays 20 000 experience and 15 000 gold (337; banks' keys 331-336).
handlers[53059] = function()
    if not has(328) and has(322) and MM9.hasItem(252, "thronheimcity:Bank") == 1 then MM9.giveKey(330) end
    MM9.openRude(243)
end
handlers[50059] = function()
    if has(330) then MM9.takeKey(330) end
    if not has(331) or has(328) then return end
    quest(); MM9.takeItem(252, "thronheimcity:Bank"); MM9.giveKey(328)
    if has(337) then return end
    for k = 331, 336 do if not has(k) then return end end
    reward(337, 12500, 15000) -- MM9 GiveExp 20000, mm9_quest_xp_profile.yml
end

-- NPC241.scr (Ealusaid A'Norta a'thrakan, RUDE 241): the Black Orb's inventor found (314): 50 000 experience,
-- 10 000 gold, the Black Orb (item 250) taken (315).
handlers[50054] = function()
    if not has(315) and has(314) then reward(315, 18500, 10000); MM9.takeItem(250, "thronheimcity:Ealusaid") end -- MM9 GiveExp 50000, mm9_quest_xp_profile.yml
end
-- NPC242.scr (Dagfari the Peevish, RUDE 242) and NPC246.scr (Erlend the Nay-sayer, RUDE 246): the Scroll of
-- Bad News (item 251). Dagfari hands it over (316 -> 317), Erlend takes it (318 -> 319), Dagfari pays (320 ->
-- 321, 5 000 experience, 5 000 gold).
handlers[50060] = function()
    if not has(317) and has(316) then MM9.giveItem(251, "thronheimcity:Dagfari"); MM9.giveKey(317) end
    if not has(321) and has(320) then reward(321, 5000, 5000) end
end
handlers[50098] = function()
    if not has(319) and has(318) then MM9.giveKey(319); MM9.takeItem(251, "thronheimcity:Erlend") end
end

-- NPC378.scr (Thorolf Ratatoskssen, two copies, RUDE 378): the messenger. Talking to one removes the other; after
-- the message (key 84) or the summons (key 107) he vanishes by town portal; with 83 or 106 alone the dialogue
-- reopens (it cannot be skipped).
handlers[53063] = function() MM9.removeActor(9); MM9.openRude(378) end
handlers[50063] = function()
    if has(107) or has(84) then MM9.clientFx(8, "mm9:town_portal"); MM9.removeActor(8); MM9.removeActor(9)
    elseif has(106) or has(83) then MM9.openRude(378) end
end
handlers[53064] = function() MM9.removeActor(8); MM9.openRude(378) end
handlers[50064] = function()
    if has(107) or has(84) then MM9.clientFx(9, "mm9:town_portal"); MM9.removeActor(9); MM9.removeActor(8)
    elseif has(106) or has(83) then MM9.openRude(378) end
end

-- Thronheimcity_BadAss.scr: the Desert Terror in the prison cell breaks out when the party walks across one
-- of the two trigger planes by the prison (BadAssTrigger, BadAssTrigger0; no key gate in MM9). :OnBreakOut: it
-- walks to BadAssWander1 by the cell's back wall and breaks the wall (:AttackWall, :DestroyWall: the scene
-- destructible's crumble and dust); :WallBroken sends Shmoe and Ben its HereComesBadAss (Ben runs to BenMarker);
-- it runs to Shmoe and kills him (:KillShmoe), then turns on the town (:Taunt3Done: Ben runs to Guard1 for help,
-- and 6 s later :GetExtraGuard brings the guard at GuardSpawn1). The guards become MM9's town guards again (their
-- peasant relations dropped, still the party's friends), whom relations.yml sets against MM9's monsters, the
-- Terror. MM9's taunts, the townsfolk's flight (SendRunAway) and its HitPoints 250 / AC 20 are not carried. A
-- walk not done in 12 s, and a load mid-breakout (walks are not saved), finish it at once.
local PLANES = {{x = 11039, y0 = -522, y1 = 1014}, {x = 8571, y0 = -1341, y1 = 553}}
local TERROR, SHMOE, EXTRA_GUARD, WALL = 10, 14, 43, 65
local WALL_MARKER, GUARD_SPAWN = {9452, 758, 3123}, {7665, 1531, 3123}
local SCRIPT_GUARDS = {[11] = true, [12] = true, [43] = true}
local function loose()
    evt.ChangeGroupAlly(2, 0); evt.ChangeGroupAlly(4, 0)
    evt.SetMonGroupBit(2, MonsterBits.Hostile, false)
    evt.SetMonGroupBit(4, MonsterBits.Hostile, false)
    evt.SetMonGroupBit(3, MonsterBits.Hostile, true)
    -- :Taunt3Done's BaseInit: MM9's own monster AI from here (the placement held it still in its cell)
    evt.SetActorImmobile(TERROR, false)
end
local function alive() return var("BadAssDead") == 0 end
-- Thronheimcity_Guard.scr :GetBadAss: the guard takes the Terror as its target (g_hTarget = hBadAss,
-- SetupTarget, AggressiveStart) and fights it on its own AI.
local function hunt(index)
    if var("BadAssStage") ~= 3 or not alive() then return end
    evt.SetActorTarget(index, TERROR)
end
local function hunters()
    local list = var("GuardOut") == 1 and {EXTRA_GUARD} or {}
    for k = 1, var("GuardsSent") do list[#list + 1] = var("GuardSent" .. k) - 1 end
    return list
end
-- Thronheimcity_Guard.scr :OpenEyes (GetExtraGuard sends it to Guard1 only): Guard1 wakes from its sleep at
-- its post (DisableWandering, GotoSleep) and finds its target again (OnFoundTarget): the Terror loose in the
-- town, given it here (far from the party the guard would not look).
local function openEyes()
    evt.WakeActor(11)
    hunt(11)
end
local function freed()   -- :Taunt3Done
    if var("BadAssStage") == 3 then return end
    -- the Terror's own walks, attacks and taunts (callbacks and waits it set while alive): a Terror that died
    -- on the way does none of it (a dead AI's callbacks do not fire): the wall and Shmoe stay as they are
    if not MM9.actorAlive(TERROR) then return end
    evt.StopActorMove(TERROR)
    evt.DestroyDestructible(WALL)
    evt.KillMapActor(SHMOE)
    set("BadAssStage", 3)
    loose()
    if MM9.actorAlive(13) then evt.SetActorTarget(TERROR, 13) end
    local gx, gy, gz = evt.GetMapActorPosition(11)
    if gx ~= nil and MM9.receives("thronheimcity", "Ben", "RunAwayFromMe", 13) then
        evt.MoveActorTo(13, gx, gy, gz, 0, true)   -- Ben: RunAwayFromBadAss
    end
    if var("GuardOut") ~= 1 then set("GuardArm", 1); evt.StartTimer(261, seconds(6)) end
end
handlers[262] = function()   -- :AtWallMarker, :AttackWall, :DestroyWall, :WallBroken
    if not MM9.actorAlive(TERROR) then return end   -- its walk's arrival: no callback once dead
    if var("BadAssStage") ~= 1 then return end
    set("BadAssStage", 2)
    evt.DestroyDestructible(WALL)
    if MM9.receives("thronheimcity", "Ben", "HereComesBadAss", 13) then
        evt.MoveActorTo(13, 9101, -202, 3092, 0, true)   -- Ben: OnHereComesBadAssBen
    end
    local x, y, z = evt.GetMapActorPosition(SHMOE)
    if x == nil or not evt.MoveActorTo(TERROR, x, y, z, 263, true) then freed() end
end
handlers[263] = function() if var("BadAssStage") == 2 then freed() end end   -- :KillShmoe
local function breakout()
    set("BadAssOut", 1); set("BadAssStage", 1); set("BadAssClock", 0)
    if not evt.MoveActorTo(TERROR, WALL_MARKER[1], WALL_MARKER[2], WALL_MARKER[3], 262) then freed() end
end
local function breakoutClock()
    if var("BadAssOut") ~= 1 or var("BadAssStage") == 3 then return end
    set("BadAssClock", var("BadAssClock") + 1)
    if var("BadAssClock") > 12 then freed() end
end
handlers[261] = function()   -- :GetExtraGuard
    if var("GuardArm") ~= 1 then return end
    set("GuardArm", 0); set("GuardOut", 1)
    show(EXTRA_GUARD, true)
    hunt(EXTRA_GUARD)
    openEyes()
end
-- Thronheimcity_Guard.scr :OnDeath: a dead guard of the script (and every one it sends) sends a new PoorTownGuard1
-- from GuardSpawn0 (the dying guard's OnDeath fires and the spawner is no AI: MM9 sends it whether or not the
-- Terror lives), hunting the Terror while it lives (hunt), at most 12 in all (GUARDS_SENT_CAP).
-- No loot (GaveTreasure); the party's friend, as the town's guards.
handlers[264] = function(context)
    local i = context.actorIndex
    if i == nil then return end
    if i == TERROR then set("BadAssDead", 1) return end
    local ours = SCRIPT_GUARDS[i] == true
    for k = 1, var("GuardsSent") do if var("GuardSent" .. k) == i + 1 then ours = true end end
    if not ours or var("GuardsSent") >= 12 then return end
    local _, made = evt.SummonMonstersById({monster = 9107, x = GUARD_SPAWN[1], y = GUARD_SPAWN[2], z = GUARD_SPAWN[3], radius = 32, count = 1, group = 4, hostile = false, loot = false})
    if made == nil or made[1] == nil then return end
    set("GuardsSent", var("GuardsSent") + 1)
    set("GuardSent" .. var("GuardsSent"), made[1] + 1)
    evt.SetMonGroupBit(4, MonsterBits.Hostile, false)
    hunt(made[1])
end
local function crossings()
    local x, y, z = evt.GetPartyPosition()
    local px, py = var("PrevX"), var("PrevY")
    set("PrevX", math.floor(x)); set("PrevY", math.floor(y))
    if var("BadAssOut") == 1 or var("Polled") == 0 then set("Polled", 1) return end
    if math.abs(x - px) + math.abs(y - py) > 1500 then return end   -- a teleport, not a walk
    for _, p in ipairs(PLANES) do
        -- the walk from the last poll crosses the plane's line within its span (where it crosses, not where
        -- the party stands now: a diagonal walk can leave the span within a poll)
        local cy = (px - p.x) * (x - p.x) <= 0 and px ~= x and py + (y - py) * (p.x - px) / (x - px) or nil
        if cy ~= nil and cy >= p.y0 - 64 and cy <= p.y1 + 64 then
            -- the plane's Breakout is a message to the Terror: a dead one takes none (MM9.receives)
            if MM9.receives("thronheimcity", "BadAss", "Breakout", TERROR) then breakout() end
            return
        end
    end
end

-- The council's RUDEProps (PropAnim "Sit"): a click opens the Jarl's dialogue.

-- BookLetter.scr letters (BOOK AND SCROLL TEXT.csv rows), Book.scr books (no text in MM9),
-- KiraShield.scr, TownPortal.scr.
-- TownPortal0: TownPortal.scr "Thronheim": cleansing the altar gives key 5016 and MM9 swaps its dirty skin for
-- the clean one: TownPortal0 (SetSprite 490) hides and TownPortal0Clean (491, the clean
-- altar at its place) shows; the map load does the same once the key is set (:Init FixCheck).
local function townPortalAltar()
    local clean = has(5016)
    evt.SetSprite(490, clean and 0 or 1, "0"); evt.SetSprite(491, clean and 1 or 0, "0")
end
handlers[330] = function()
    if has(5016) then return end
    MM9.giveKey(5016); quest()
    townPortalAltar()
    evt.StatusText("The altar is cleansed.")
end
handlers[331] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0) end   -- BookProp (Book.scr: pages turn, no text)
handlers[332] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0) end   -- Book1 (Book.scr: pages turn, no text)
handlers[333] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Letter to Lariee\n\nLariee, I've found it!\nI found some sort of storage facility from the Old Ursanian Empire!  It must have untold treasures inside!  The words scratched on the door named the place Inventa Storca.  I eagerly await your arrival so that we can excavate it together.  I am certain this place will answer all our questions about the days of the Ursanian Emperors.\nSee you soon\n\nJerhildr") end   -- Prop18 (467)
handlers[334] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Letter to Henree\n\nHenree,\nI've had enough with this Temple of Honk!  I've decided that I will use my petition this month to implore Kira to do something about them.  Last night they spent an hour in my tavern preaching their nonsense to anyone who would listen.  I finally forced them to take their mouths elsewhere, but I suspect they'll be returning tonight.  We'll see what Kira will be able to do about them.\n\nJofridr") end   -- Prop19 (466)
handlers[335] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Invoice\n\n30 lbs flour                       10 gold\n90 Gallons Ale                  40 gold\n35 Gallons Black Whisky  20 gold\n10 lbs Assorted Nuts        10 gold\nTotal                               80 gold\nMoney due upon receipt.") end   -- Prop20 (468)
handlers[336] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Letter to Wahng\n\nWahng,\nI am certain the Temple of Honk has a plot to take over Thronheim.  Why else would they be here?  I've heard them preach to the nobles, and give money to the beggars.  They are up to something, and I intend to find out what.  If you don't hear from me in two day's time, call the Jarl.\n\nJack") end   -- Prop21 (469)

local function poll()
    shopHours()
    kiraClock()
    crossings()
    breakoutClock()
    evt.StartTimer(260, seconds(1))
end
handlers[260] = poll
handlers[1] = function()   -- map load
    for k = 1024, 1033 do if k ~= 1030 and has(k) then MM9.takeKey(k) end end
    MM9.giveKey(1030)
    councilProps()
    show(41, not has(40) or has(108))   -- NPC239.scr :Init
    if has(185) then MM9.removeActor(42) else show(42, has(40)) end
    local thorolf = has(83) and not has(84)   -- NPC378.scr :Init (only Frosgard's third copy comes on 106)
    show(8, thorolf); show(9, thorolf)
    townPortalAltar()   -- TownPortal.scr :Init (FixCheck): the clean altar once its key is set
    evt.PlayActorClip(44, "sit", true); evt.FaceActorTo(44, -11254, 16669, 0)   -- Sven Forkbeard: LoopAnim sit
    evt.PlayActorClip(45, "sit", true); evt.FaceActorTo(45, -11244, 16546, 0)   -- Tryygva Ravenlocks: LoopAnim sit
    evt.PlayActorClip(46, "sit", true); evt.FaceActorTo(46, -11233, 16423, 0)   -- Markel the Great: LoopAnim sit
    evt.PlayActorClip(47, "sit", true); evt.FaceActorTo(47, -11274, 16426, 0)   -- Forad Darre: LoopAnim sit
    evt.PlayActorClip(48, "sit", true); evt.FaceActorTo(48, -11295, 16549, 0)   -- Sigmund the Stressed: LoopAnim sit
    evt.PlayActorClip(49, "sit", true); evt.FaceActorTo(49, -11284, 16692, 0)   -- Bjarni Thorvaldssen: LoopAnim sit
    if has(83) then evt.SetMapActorPosition(8, -7183, 12902, 3092) end
    show(27, not has(461))   -- Retainer.scr: Cleirach A'Lyrae, hidden while hired
    if has(77) then   -- Honkies.scr :Init
        MM9.removeActor(1)
        MM9.removeActor(3)
        MM9.removeActor(2)
    else
        if has(145) and has(142) then MM9.removeActor(1) end
        if has(145) and has(143) then MM9.removeActor(3) end
        if has(145) and has(144) then MM9.removeActor(2) end
    end
    if var("GuardOut") == 1 then show(43, true); openEyes() end
    if var("BadAssOut") == 1 and var("BadAssStage") ~= 3 then freed()   -- walks are not saved
    elseif var("BadAssOut") == 1 then loose(); for _, h in ipairs(hunters()) do hunt(h) end end
    set("Polled", 0)
    poll()
end
-- MM9's approach talks (dungeon/lua.py approach_talk): an NPC whose script talks when the party comes
-- within 16 LT of his body (OnTargetWithinDist / RunTo 16 -> DoRude). reach: the feet's distance at which
-- he talks; sight > 0: he runs to the party once he sees it within that range. Once per visit.
local APPROACH_TALKS = {
    {actor = 8, reach = 109, sight = 1536, armed = function() return not has(107) and (not has(84) or has(106)) end,
        talk = function() MM9.removeActor(9); MM9.openRude(378, 8); MM9.playSound("voices/npc/npc_378.wav") end},   -- Thorolf0: NPC378.scr :OnFound RunTo 16 :Talk
    {actor = 9, reach = 109, sight = 1536, armed = function() return not has(107) and (not has(84) or has(106)) end,
        talk = function() MM9.removeActor(8); MM9.openRude(378, 9); MM9.playSound("voices/npc/npc_378.wav") end},   -- Thorolf1: NPC378.scr :OnFound RunTo 16 :Talk
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
handlers[53054] = function() MM9.playSound("voices/npc/npc_241.wav"); MM9.openRude(241) end   -- Ealusaid
do local own = handlers[53059]; handlers[53059] = function() MM9.playSound("voices/npc/npc_243.wav"); own() end end   -- brynhildr
handlers[53060] = function() MM9.playSound("voices/npc/npc_242.wav"); MM9.openRude(242) end   -- dagfaripeevish
handlers[53061] = function() MM9.playSound("voices/npc/npc_240.wav"); MM9.openRude(240) end   -- Thorfinnskullsplitter
handlers[53098] = function() MM9.playSound("voices/npc/npc_246.wav"); MM9.openRude(246) end   -- CommonerHuman2MaleA8
handlers[53133] = function() MM9.playSound("voices/npc/npc_281.wav"); MM9.openRude(281) end   -- CommonerHuman2MaleA7
handlers[53140] = function() MM9.playSound("voices/npc/npc_247.wav"); MM9.openRude(247) end   -- ShopkeeperHuman2MaleA0
handlers[53141] = function() MM9.playSound("voices/npc/npc_248.wav"); MM9.openRude(248) end   -- ShopkeeperHuman2MaleA1
handlers[53142] = function() MM9.playSound("voices/npc/npc_249.wav"); MM9.openRude(249) end   -- ShopkeeperHuman2MaleA2
handlers[53143] = function() MM9.playSound("voices/npc/npc_254.wav"); MM9.openRude(254) end   -- ShopkeeperHuman2MaleA3
handlers[53144] = function() MM9.playSound("voices/npc/npc_255.wav"); MM9.openRude(255) end   -- ShopkeeperHuman2MaleA4
handlers[53145] = function() MM9.playSound("voices/npc/npc_256.wav"); MM9.openRude(256) end   -- ShopkeeperHuman2MaleA5
handlers[53146] = function() MM9.playSound("voices/npc/npc_258.wav"); MM9.openRude(258) end   -- ShopkeeperHuman2MaleA6
handlers[53147] = function() MM9.playSound("voices/npc/npc_259.wav"); MM9.openRude(259) end   -- ShopkeeperHuman2MaleA7
handlers[53148] = function() MM9.playSound("voices/npc/npc_260.wav"); MM9.openRude(260) end   -- ShopkeeperHuman2MaleA8
do local own = handlers[53228]; handlers[53228] = function() MM9.playSound("voices/npc/npc_239.wav"); own() end end   -- KiraCold

-- MM9's bonus props (dungeon/objects.py bonus_lines; the use of each class, object.lto): wells, cauldrons,
-- cook pots and clovers.
handlers[30950] = function() MM9.useWell(950, 2, 0, 5, 0, 1) end   -- WellMMIX0 (WellMMIX)
handlers[30951] = function() MM9.useClover(951, "thronheimcity:Clover0") end   -- Clover0 (Clover)
handlers[30952] = function() MM9.useClover(952, "thronheimcity:Clover1") end   -- Clover1 (Clover)

-- MM9's PerceptionBrushes (dungeon/perception.py): the red glow shows to a party whose Perception reaches the
-- brush's PerceptionValue, checked on load and every 3 s; map Lua turns one off for good with
-- set("HintOff<cog>", 1) (MM9's Off message to the brush).
local HINTS = {[23051] = 1, [23155] = 1, [23156] = 1, [23157] = 1, [23158] = 1, [23159] = 1, [23160] = 1, [23161] = 1, [23162] = 1, [23163] = 1, [23164] = 1, [23165] = 1}
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
    evt.PlayActorClip(50, "sit", true); evt.FaceActorTo(50, -11265, 16620, 0)   -- Kira the Cold: ARG_Kira.scr :Init loopanim
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
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(230, "Locked door", handlers[230], "Door")
RegisterEvent(232, "Door", handlers[232], "Door")
RegisterEvent(53230, "Yrsa", handlers[53230])
RegisterEvent(50230, "Yrsa", handlers[50230])
RegisterEvent(53228, "Kira", handlers[53228])
RegisterEvent(50228, "Kira", handlers[50228])
RegisterMapTimerEvent(36040, seconds(3), handlers[36040], "Yrsa", "", seconds(3))
RegisterMapTimerEvent(36050, seconds(3), handlers[36050], "Knut", "", seconds(3))
RegisterEvent(50056, "Honk", handlers[50056])
RegisterEvent(50058, "Honk", handlers[50058])
RegisterEvent(50057, "Honk", handlers[50057])
RegisterEvent(265, "Honk", handlers[265])
RegisterEvent(266, "Honk", handlers[266])
RegisterEvent(267, "Honk", handlers[267])
RegisterEvent(53059, "Bank", handlers[53059])
RegisterEvent(50059, "Bank", handlers[50059])
RegisterEvent(50054, "Ealusaid", handlers[50054])
RegisterEvent(50060, "Dagfari", handlers[50060])
RegisterEvent(50098, "Erlend", handlers[50098])
RegisterEvent(53063, "Thorolf", handlers[53063])
RegisterEvent(50063, "Thorolf", handlers[50063])
RegisterEvent(53064, "Thorolf", handlers[53064])
RegisterEvent(50064, "Thorolf", handlers[50064])
RegisterMapTimerEvent(261, seconds(3), handlers[261], "Guard", "", seconds(3))
RegisterEvent(262, "Breakout", handlers[262])
RegisterEvent(263, "Breakout", handlers[263])
RegisterEvent(330, "TownPortal0", handlers[330], "Altar")
RegisterEvent(331, "BookProp", handlers[331], "Book")
RegisterEvent(332, "Book1", handlers[332], "Book")
RegisterEvent(333, "Prop18", handlers[333], "Read")
RegisterEvent(334, "Prop19", handlers[334], "Read")
RegisterEvent(335, "Prop20", handlers[335], "Read")
RegisterEvent(336, "Prop21", handlers[336], "Read")
RegisterMapTimerEvent(260, seconds(3), handlers[260], "Poll", "", seconds(3))
RegisterEvent(1, "Map load", handlers[1])
RegisterMapTimerEvent(906, seconds(3), handlers[906], "Approach talks", "", seconds(3))
RegisterEvent(53054, "Ealusaid A'Norta a'thrakan", handlers[53054])
RegisterEvent(53060, "Dagfari the Peevish", handlers[53060])
RegisterEvent(53061, "Thorfinn Skullsplitter", handlers[53061])
RegisterEvent(53098, "Erlend the Nay-sayer", handlers[53098])
RegisterEvent(53133, "Cleirach A'Lyrae", handlers[53133])
RegisterEvent(53140, "William the Framish", handlers[53140])
RegisterEvent(53141, "Rustavius", handlers[53141])
RegisterEvent(53142, "Bones the Pale", handlers[53142])
RegisterEvent(53143, "Jofridr The Swillbowl", handlers[53143])
RegisterEvent(53144, "Thakkrad Kjarssen", handlers[53144])
RegisterEvent(53145, "Robert Bloodstopper", handlers[53145])
RegisterEvent(53146, "Erpr the Ankle-heavy", handlers[53146])
RegisterEvent(53147, "Jormunrek Jonakrssen", handlers[53147])
RegisterEvent(53148, "Magnus ver Magnussen", handlers[53148])
RegisterEvent(30950, "Well", handlers[30950], "Drink")
RegisterEvent(30951, "Clover", handlers[30951], "Pick")
RegisterEvent(30952, "Clover", handlers[30952], "Pick")
RegisterMapTimerEvent(901, seconds(3), handlers[901], "Perception hints", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
RegisterEvent(907, "Script poses", handlers[907])
RegisterMonsterKilledHook(264, "Breakout guards", handlers[264])


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

-- Cinematic council_argument (ARGUMENT.scr (Argueman) :OnStart..:End2 with ARG_*.scr, ARGUECAM1): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["council_argument"] = {
    { "stage", function()
        -- the seated Jarls play their parts, Kira's stage actor at her place (Kira the Cold hidden meanwhile)
        show(41, false)
        show(50, true); show(49, true); show(48, true); show(47, true); show(45, true); show(46, true)
    end },
    { "forad", function()
        MM9.removeHireling(2)   -- ARGUMENT.scr :Cam2b RemoveNPC 2: Forad leaves the party
    end },
    { "war", function()
        war()   -- ARGUMENT.scr :Cam3 gosub War
    end },
    { "kira_sheath", function()
        evt.AttachActorItem(50, "worlds/mm9/models/mm9_item_kirasword.glb", "Socket_Sheath")
    end },
    { "kira_draw", function()
        evt.DetachActorItem(50, "Socket_Sheath")
        evt.AttachActorItem(50, "worlds/mm9/models/mm9_item_kirasword.glb", "Socket_RHand1")
    end },
    { "end", function()
        -- :End gosub War; the hall as the scene left it: the posed Jarls back, Markel dead (NPC239.scr
        -- :OnKillMarkel), Kira the Cold at her place; ARG_Yrsa.scr :OnAppear: Yrsa 5 + 2 s later
        war()
        evt.DetachActorItem(50)   -- her sword goes with her stage actor (MM9 drops props on a load)
        show(50, false)
        -- the Jarls back in their chairs, looping Sit (the scene's presentation ends with it)
        evt.PlayActorClip(49, "sit", true); evt.FaceActorTo(49, -11284, 16692, 0)   -- Bjarni Thorvaldssen: LoopAnim sit
        evt.PlayActorClip(48, "sit", true); evt.FaceActorTo(48, -11295, 16549, 0)   -- Sigmund the Stressed: LoopAnim sit
        evt.PlayActorClip(47, "sit", true); evt.FaceActorTo(47, -11274, 16426, 0)   -- Forad Darre: LoopAnim sit
        evt.PlayActorClip(45, "sit", true); evt.FaceActorTo(45, -11244, 16546, 0)   -- Tryygva Ravenlocks: LoopAnim sit
        -- :Cam2b's KillMarkel is a message to Kira the Cold: a dead one takes none (MM9.receives): Markel stays
        if MM9.receives("thronheimcity", "KiraCold", "KillMarkel", 41) then
            show(46, false); sprite(COG.MarkeProp0, true)
        else
            evt.SetMapActorPosition(46, -11489, 16425, 3351)
            evt.PlayActorClip(46, "sit", true); evt.FaceActorTo(46, -11233, 16423, 0)   -- Markel the Great: LoopAnim sit
        end
        show(41, true)
        set("YrsaAppear", 1); evt.StartTimer(36040, seconds(5))
    end },
}
RegisterEvent(36001, "Cinema council_argument: stage", function() MM9Cinematic.runStep("council_argument", 1) end)
RegisterEvent(36002, "Cinema council_argument: forad", function() MM9Cinematic.runStep("council_argument", 2) end)
RegisterEvent(36003, "Cinema council_argument: war", function() MM9Cinematic.runStep("council_argument", 3) end)
RegisterEvent(36004, "Cinema council_argument: kira_sheath", function() MM9Cinematic.runStep("council_argument", 4) end)
RegisterEvent(36005, "Cinema council_argument: kira_draw", function() MM9Cinematic.runStep("council_argument", 5) end)
RegisterEvent(36006, "Cinema council_argument: end", function() MM9Cinematic.runStep("council_argument", 6) end)
RegisterEvent(36000, "Cinema council_argument: done", function() MM9Cinematic.finish("council_argument") end)
MM9Cinematic.play["council_argument"] = function()
    if evt.GetMapVar("Cinema.council_argument.started", 0) == 0 then
        evt.SetMapVar("Cinema.council_argument.started", 1)
        evt.PlayCinematic("council_argument", 36000)
    end
end
