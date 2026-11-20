-- Guberland, MM9 rework (level_generation/projects/mm9r_guberland/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {Riser1 = 1, Strikeplate1 = 2, Switch = 3, Switch0 = 4}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 902}, onLeave = {}, timers = {}, openedChestIds = {}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(1, DoorAction.Trigger) end   -- Riser1
handlers[102] = function() evt.SetDoorState(2, DoorAction.Trigger) end   -- Strikeplate1
handlers[103] = function() evt.SetDoorState(3, DoorAction.Trigger) end   -- Switch
handlers[104] = function() evt.SetDoorState(4, DoorAction.Trigger) end   -- Switch0

-- Chests (MM9 TreasureChest objects; loot records in the scene).

local function has(k) return MM9.hasKey(k) == 1 end
local function quest() MM9.playSound("sounds/events/quest.wav") end
local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; if gold > 0 then MM9.giveGold(gold) end; quest() end

-- ForadWorld.scr (ScriptObject0, "guberland"): key 1028 is the party's location while here (keys
-- 1024-1033), and key 5017 closes the shops from 20:00 to 06:00 (MM9's dialogues test it).
local function shopHours()
    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24
    local closed = hour >= 20 or hour < 6
    if closed and not has(5017) then MM9.giveKey(5017) elseif not closed and has(5017) then MM9.takeKey(5017) end
end
handlers[260] = function() shopHours() end

-- StatStone0 (StatStone: Stat 1 Magic, +10 for 3700 s)
handlers[390] = function()
    if evt.CurrentGameMinutes() < var("StatStoneUntil0") then
        evt.StatusText("The stone's power is still with you.") return
    end
    evt.ApplyPartyPrimaryStatBuff(1, 10, 3700) evt.ApplyPartyPrimaryStatBuff(2, 10, 3700)
    set("StatStoneUntil0", evt.CurrentGameMinutes() + 62)
    evt.PlaySoundName("events/dingbell.wav", 0, 0, 0)
    evt.StatusText("+10 Magic for 1.02778 hours")
end
local function show(a, on) evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end

-- NPC133.scr (Thorir Mouth, RUDE 133). :OnUse :ItemCheck: all six Gathering prizes (362-367) in the
-- packs give key 487 (his row 'We've got your set of prizes' gives 488).
handlers[53021] = function()
    local n = 0
    for k = 362, 367 do
        if MM9.hasItem(k, "guberland:Thorir") == 1 then n = n + 1 end
    end
    if n == 6 then MM9.giveKey(487) end
    MM9.openRude(133)
end
-- NPC133.scr :OnRude: the prizes taken (488, not 490: key 490); Nicolai's job (121, not 122: 5 000 gold,
-- 20 000 experience, key 122); the Capstone of Order (488, not 188: item 396, 146 000 experience, key 188).
handlers[50021] = function()
    if has(488) and not has(490) then MM9.takeItem(362, "guberland:Thorir"); MM9.takeItem(363, "guberland:Thorir"); MM9.takeItem(364, "guberland:Thorir"); MM9.takeItem(365, "guberland:Thorir"); MM9.takeItem(366, "guberland:Thorir"); MM9.takeItem(367, "guberland:Thorir"); MM9.giveKey(490) end
    if has(121) and not has(122) then reward(122, 16500, 5000) end -- MM9 GiveExp 20000, mm9_quest_xp_profile.yml
    if has(488) and not has(188) then MM9.giveItem(396, "guberland:Thorir"); reward(188, 18500, 0) end -- MM9 GiveExp 146000, mm9_quest_xp_profile.yml
end
-- NPC130.scr (Ivan the Smart, RUDE 130) :Trivia: beaten (60, not 164): key 164, 5 000 experience, item 400.
handlers[50022] = function()
    if has(60) and not has(164) then reward(164, 5000, 0); MM9.giveItem(400, "guberland:Ivan") end
end

-- The Mercenary promotion. atlipromo.scr (the late guard at the dock, AtliGuard): @m 2:45 key 376,
-- @m 3:15 taken; :OnLeave (OnFoundPlayer): with 376 and Atli's job (125) he gives 197 and walks off to
-- AtliMarker. Here the party standing within 768 LT of his post stands for his sighting.
-- Atliwagon.scr: @M 3:30 three Bandits and three Cutpurses at SpawnMarker (once, with 197); @M 6:00
-- :summonatli: key 126 and Atli's :OnSummon: he, his daughter (NPC187.scr :OnReturn) and the guard
-- (atlipromo.scr :OnReturn) walk to the dock, Atlimarker0.
-- The watch is a night's (the user, 2026-11-08): the relief starts it; the raid comes at 3:30 of that night
-- (the party on the map); Atli comes at 6:00 once every raider is dead (a party that left after the fight
-- finds him come when it is back). Raiders still alive at 5:30, or a raid the party was away for, fail the
-- night: the raiders are gone, key 197 is taken and the guard walks back to his post, to be relieved again
-- the next night. MM9's clock triggers fire during a wait: by the dock, the rest alarm (evt.SetRestAlarm)
-- stops a rest at 2:45 (at the post), 3:30, 5:30 and 6:00. The walks run on after a load (GuardLeaving 1 to
-- AtliMarker, 2 back to the post; AtliComing); the guard stays until Atli is gone (127).
-- BanditAttack.scr (their spawn string's script): :OnAttack runs each to Atlimarker0 (TerrainMode, Runto 256)
-- until OnFoundPlayer, then stops and fights (:OnExit, BaseInit); arriving does the same. Here the watch's
-- poll stops a runner the party is in sight of (evt.ActorSeesParty) and sets it on the party; a load sends
-- the ones still running again (:Main OnPostSaveLoad OnAttack).
local ATLI_MARKER = {17461, 4696, -39}   -- Atlimarker0, the dock
local GUARD_AWAY = {11891, 11496, 120}   -- AtliMarker
local GUARD_POST = {18116, 4860, -123}   -- AtliGuard
local ATLI_WALKERS = {54, 55, 56}   -- Atli, his daughter, the guard
local DOCK_RANGE = 5120   -- the rest alarms stop a rest this near the dock
local function banditsRun(count, made)
    if made == nil then return end
    for _, i in ipairs(made) do
        local n = var("Runners") + 1
        set("Runners", n); set("Runner" .. n, i + 1)
        local b = var("Bandits") + 1
        set("Bandits", b); set("Bandit" .. b, i + 1)
        evt.MoveActorTo(i, ATLI_MARKER[1], ATLI_MARKER[2], ATLI_MARKER[3], 0, true)
    end
end
local function banditsWatch(resend)
    for n = 1, var("Runners") do
        local i = var("Runner" .. n) - 1
        if i >= 0 then
            if evt.GetMapActorPosition(i) == nil or evt.ActorSeesParty(i) then
                evt.StopActorMove(i); evt.SetActorTarget(i, "party"); set("Runner" .. n, 0)   -- :OnExit
            elseif resend then
                evt.MoveActorTo(i, ATLI_MARKER[1], ATLI_MARKER[2], ATLI_MARKER[3], 0, true)
            elseif not evt.IsActorMoving(i) then
                set("Runner" .. n, 0)   -- at Atlimarker0: Runto's Onexit, BaseInit
            end
        end
    end
end
local function banditsLeft()   -- this night's raiders still standing
    local left = 0
    for n = 1, var("Bandits") do
        local i = var("Bandit" .. n) - 1
        if i >= 0 and MM9.actorAlive(i) then left = left + 1 end
    end
    return left
end
local function nextClock(at, minute)   -- the first game minute >= at whose time of day is `minute`
    local t = math.floor(at / 1440) * 1440 + minute
    if t < at then t = t + 1440 end
    return t
end
local function near(i, p)   -- a walker at its walk's end (Walkto's 256 LT)
    local x, y = evt.GetMapActorPosition(i)
    return x == nil or (x - p[1]) ^ 2 + (y - p[2]) ^ 2 <= 655 ^ 2
end
local function walkOn(i, p)   -- a walk a load dropped, or one to start: sent again
    if not near(i, p) and not evt.IsActorMoving(i) then evt.MoveActorTo(i, p[1], p[2], p[3]) end
end
local function walkTo(i, p)   -- a new walk, turning from the last one
    evt.MoveActorTo(i, p[1], p[2], p[3])
end
local function watchFailed()   -- the raid not stopped by 5:30: the raiders make off, the guard is back on duty
    for n = 1, var("Bandits") do
        local i = var("Bandit" .. n) - 1
        if i >= 0 and MM9.actorAlive(i) then evt.StopActorMove(i); MM9.removeActor(i) end
    end
    set("Bandits", 0); set("Runners", 0); set("BanditsSent", 0); set("RelievedAt", 0)
    MM9.takeKey(197)
    set("GuardLeaving", 2); walkTo(56, GUARD_POST)
    evt.StatusText("The raiders got away. Atli's boat needs guarding again tonight.")
end
local function atliWatch()
    banditsWatch(false)
    local now = math.floor(evt.CurrentGameMinutes())
    local minute = now % 1440
    local window = minute >= 165 and minute < 195
    if window and not has(376) then MM9.giveKey(376) elseif not window and has(376) then MM9.takeKey(376) end
    local x, y = evt.GetPartyPosition()
    local dx, dy = x - (18116), y - (4860)
    local atPost = dx * dx + dy * dy <= 1966 * 1966
    local byDock = (x - ATLI_MARKER[1]) ^ 2 + (y - ATLI_MARKER[2]) ^ 2 <= DOCK_RANGE ^ 2
    if has(376) and has(125) and not has(197) and not has(126) and atPost and MM9.actorAlive(56) then
        MM9.giveKey(197); set("RelievedAt", now)
        set("GuardLeaving", 1); walkTo(56, GUARD_AWAY)   -- :OnLeave: walkto AtliMarker
        evt.StatusText("The late guard leaves. Your watch begins.")
    end
    local g = var("GuardLeaving")
    if g ~= 0 and not has(126) then
        local p = g == 1 and GUARD_AWAY or GUARD_POST
        if near(56, p) then set("GuardLeaving", 0) else walkOn(56, p) end
    end
    local alarm = nil
    if has(197) and not has(126) and not has(127) then
        local at = var("RelievedAt")
        local raidAt, giveUpAt, atliAt = nextClock(at, 210), nextClock(at, 330), nextClock(at, 360)
        if var("BanditsSent") == 0 then
            if now >= giveUpAt then watchFailed()
            elseif now >= raidAt then
                set("BanditsSent", 1)
                banditsRun(evt.SummonMonstersById({monster = 9101, x = 10580, y = 8137, z = 120, radius = 128, count = 3}))
                banditsRun(evt.SummonMonstersById({monster = 9099, x = 10580, y = 8137, z = 120, radius = 128, count = 3}))
            else alarm = raidAt end
        elseif banditsLeft() > 0 then
            if now >= giveUpAt then watchFailed() else alarm = giveUpAt end
        elseif now >= atliAt then
            MM9.giveKey(126); set("AtliComing", 1); set("GuardLeaving", 0)   -- :summonatli, :OnSummon
            for _, i in ipairs(ATLI_WALKERS) do walkTo(i, ATLI_MARKER) end
        else alarm = atliAt end
    elseif has(125) and not has(197) and not has(126) and atPost then
        alarm = nextClock(now, 165)   -- to be there when he can be relieved
    end
    evt.SetRestAlarm((byDock or atPost) and alarm or nil)
    if var("AtliComing") == 1 and not has(127) then
        local arrived = true
        for _, i in ipairs(ATLI_WALKERS) do
            if not near(i, ATLI_MARKER) then arrived = false; walkOn(i, ATLI_MARKER) end
        end
        if arrived then set("AtliComing", 0) end
    end
end
handlers[600] = atliWatch

-- NPC186.scr (Atli Sigmundssen, RUDE 186) :Mercpromo: Atli has come (126, not 127): key 127, 1 000 gold,
-- 24 000 experience, the characters holding 401-404 promoted to Mercenary (each key taken).
handlers[50085] = function()
    if not has(126) or has(127) then return end
    reward(127, 16500, 1000) -- MM9 GiveExp 24000, mm9_quest_xp_profile.yml
    MM9.promoteParty("Mercenary")   -- every eligible member (not MM9's per-character keys 401-404)
end

-- THJORGARDGAMESCOMMON.inc: a game takes a ticket (item 557) when it starts; a win (Guberland:
-- HucksterMod.scr "1") gives the game's key, key 7116 and a random prize (362-367). MM9's rollover
-- strings are not extracted: the status lines are our own words.
local function ticket()   -- :CheckGameTicket, :TakeGameTicket
    if MM9.hasItem(557, "guberland:Ticket") ~= 1 then
        evt.StatusText("You need a game ticket. The ticket master sells them.")
        return false
    end
    MM9.takeItem(557, "guberland:Ticket")
    evt.StatusText("A game ticket is used.")
    return true
end
local function gameWon(key)   -- :Record<Game>Win, :CheckGuberlandWins, :GiveGuberlandPrize
    MM9.giveKey(key); MM9.giveKey(7116)
    MM9.giveItem(MM9.random(362, 367), "guberland:Prize")
    evt.StatusText("You win! Here is your prize.")
end
local function might()   -- GetAttribute 0: the active character's Might
    evt.ForPlayer(Players.Current)
    local low, high = 0, 1024
    while low < high do
        local mid = math.floor((low + high + 1) / 2)
        if evt.Cmp(VarTag.ActualMight, mid) then low = mid else high = mid - 1 end
    end
    return low
end
-- HucksterMod.scr (the ticket master, RUDE 429) :OnRudeExit: key 1001: one ticket for 5 gold; key 1010:
-- ten for 40 gold; the rule book (item 594) with the first. Without the gold, NoGold.inc.
local function sellTickets(cost, count)   -- :SellGameTicket, :SellBatchTickets
    if MM9.hasGold(cost) ~= 1 then evt.StatusText("You don't have enough gold."); return end
    evt.PlaySoundName("events/gold01.wav", 0, 0, 0)
    MM9.takeGold(cost)
    for n = 1, count do MM9.giveItem(557, "guberland:Ticket") end
    if MM9.hasItem(594, "guberland:Rulebook") ~= 1 then MM9.giveItem(594, "guberland:Rulebook") end
    evt.StatusText(count == 1 and "You bought a game ticket." or "You bought ten game tickets.")
end
handlers[50324] = function()
    if has(1001) then MM9.takeKey(1001); sellTickets(5, 1)
    elseif has(1010) then MM9.takeKey(1010); sellTickets(40, 10) end
end

-- ArmWrestle.scr (Mata Abyomi, RUDE 148) :OnUse (his dialogue opens too: DoRude 1): with a ticket, his
-- might (no ScriptParams: 0) + 1..40 against the character's Might + 9..50; a tie is the party's.
-- A beaten Mata :StartCower: PlayAnim cowerstart, LoopAnim cower 5, PlayAnim cowerstop, his use (the game,
-- not the dialogue) removed until it ends (:RemoveUse, :RestoreUse: 5.3 s; runtime only).
local MATA = 61
local mataCowers = false
handlers[53330] = function()
    if not mataCowers and ticket() then
        local his = MM9.random(1, 40)
        if might() + MM9.random(9, 50) >= his then
            evt.PlayActorClip(MATA, {"cowerstart", "cower", "cower", "cower", "cower", "cower", "cowerstop"}, false)
            mataCowers = true; evt.StartTimer(605, seconds(5.3))
            gameWon(7115)
        else evt.StatusText("You lose.") end
    end
    MM9.openRude(148)
end
handlers[605] = function()   -- :FinishCower -> :RestoreUse
    evt.StopTimer(605)
    mataCowers = false
end

-- DingTheBell.scr (Strikeplate1) :HitBell, BellWeight.scr (Riser1, "360") :AdjustHeight: with a
-- ticket the plate goes down and the weight rises to 360 LT x timing / ding (timing 40..60 + the
-- character's Might, ding 60..80); :CheckWin: timing > ding rings the bell (the bell's win), else a
-- loss; the plate works again 3 s later, when the weight's close lifts it. Here timer 601 stops the
-- weight at its height, then closes both.
local BELL_RISE = 1.029   -- seconds for the weight's full rise (move length / open speed)
handlers[102] = function()   -- Strikeplate1 (replaces its door toggle)
    if var("BellPhase") ~= 0 then return end   -- :BlockUse
    if not ticket() then return end
    local ding = MM9.random(60, 80)
    local timing = MM9.random(40, 60) + might()
    set("BellWin", timing > ding and 1 or 0)
    set("BellPhase", 1)
    evt.SetDoorState(2, DoorAction.Open) evt.SetDoorState(1, DoorAction.Open)
    evt.StartTimer(601, seconds(BELL_RISE * math.min(1, timing / ding)))
end
handlers[601] = function()
    local phase = var("BellPhase")
    if phase == 1 then
        evt.StopDoor(1)
        if var("BellWin") == 1 then evt.PlaySoundName("events/dingbell.wav", 0, 0, 0); gameWon(7114)
        else evt.StatusText("You lose.") end
        set("BellPhase", 2); evt.StartTimer(601, seconds(3))   -- :AllowUse
    else
        if phase == 2 then evt.SetDoorState(1, DoorAction.Close) evt.SetDoorState(2, DoorAction.Close) end
        set("BellPhase", 0); evt.StopTimer(601)
    end
end
handlers[101] = function() end   -- Riser1: only the plate drives the weight

-- The runes. MastermindColor.scr (ColorButton0-4): the current colour. MastermindSpace.scr
-- (ColorSpace0-3): Mastermind.scr :ColorChosen (the game's first choice takes a ticket) and the stone
-- takes the colour (here its decoration swaps to the button's). The Switch's open: :CompareColors: right
-- runes (MM9 lights FireCorrect fires; here a status line names them), 4 chances, all four right: the
-- runes' win; :GenerateColors: four random colours 0..4. RuneChosen<i> holds colour + 1 (0 = none).
-- MastermindSpace.scr :ChangeColor (skins\gibs\<colour>.dtx)
local function paintRune(cog, colour)
    if colour == 0 then evt.SetSprite(cog, 1, "mm9_stonered_x200")
    elseif colour == 1 then evt.SetSprite(cog, 1, "mm9_stoneblue_x200")
    elseif colour == 2 then evt.SetSprite(cog, 1, "mm9_stoneyellow_x200")
    elseif colour == 3 then evt.SetSprite(cog, 1, "mm9_stoneorange_x200")
    elseif colour == 4 then evt.SetSprite(cog, 1, "mm9_stonegreen_x200")
    else evt.SetSprite(cog, 1, "mm9_stone_x200") end
end
local function newRunes()   -- :GenerateColors
    for i = 1, 4 do set("RuneCode" .. i, MM9.random(0, 4)) end
    set("RuneChances", 4); set("RuneTicket", 1)
end
local function runeTicket()   -- bNeedsTicket
    if var("RuneTicket") == 0 then return true end
    if not ticket() then return false end
    set("RuneTicket", 0)
    return true
end
handlers[330] = function()   -- ColorButton0
    evt.PlaySoundName("door/trapdooropen.wav", 0, 0, 0)
    set("RuneColour", 0); evt.StatusText("The red rune.")
end
handlers[331] = function()   -- ColorButton1
    evt.PlaySoundName("door/trapdooropen.wav", 0, 0, 0)
    set("RuneColour", 1); evt.StatusText("The blue rune.")
end
handlers[332] = function()   -- ColorButton2
    evt.PlaySoundName("door/trapdooropen.wav", 0, 0, 0)
    set("RuneColour", 2); evt.StatusText("The yellow rune.")
end
handlers[333] = function()   -- ColorButton3
    evt.PlaySoundName("door/trapdooropen.wav", 0, 0, 0)
    set("RuneColour", 3); evt.StatusText("The orange rune.")
end
handlers[334] = function()   -- ColorButton4
    evt.PlaySoundName("door/trapdooropen.wav", 0, 0, 0)
    set("RuneColour", 4); evt.StatusText("The green rune.")
end
handlers[335] = function()   -- ColorSpace0 (MastermindSpace.scr :UpdateColor)
    local colour = var("RuneColour")
    if var("RuneChances") > 0 and runeTicket() then set("RuneChosen1", colour + 1) end
    evt.PlaySoundName("door/doorlatch01.wav", 0, 0, 0)
    paintRune(401, colour)
end
handlers[336] = function()   -- ColorSpace1 (MastermindSpace.scr :UpdateColor)
    local colour = var("RuneColour")
    if var("RuneChances") > 0 and runeTicket() then set("RuneChosen2", colour + 1) end
    evt.PlaySoundName("door/doorlatch01.wav", 0, 0, 0)
    paintRune(402, colour)
end
handlers[337] = function()   -- ColorSpace2 (MastermindSpace.scr :UpdateColor)
    local colour = var("RuneColour")
    if var("RuneChances") > 0 and runeTicket() then set("RuneChosen3", colour + 1) end
    evt.PlaySoundName("door/doorlatch01.wav", 0, 0, 0)
    paintRune(403, colour)
end
handlers[338] = function()   -- ColorSpace3 (MastermindSpace.scr :UpdateColor)
    local colour = var("RuneColour")
    if var("RuneChances") > 0 and runeTicket() then set("RuneChosen4", colour + 1) end
    evt.PlaySoundName("door/doorlatch01.wav", 0, 0, 0)
    paintRune(404, colour)
end
handlers[103] = function()   -- Switch (OpenTrigger: Mastermind check; not a door toggle)
    evt.SetDoorState(3, DoorAction.Open)
    evt.StartTimer(602, seconds(1))
    if var("RuneChances") <= 0 or not runeTicket() then return end
    local right = {}
    for i = 1, 4 do
        if var("RuneChosen" .. i) == var("RuneCode" .. i) + 1 then
            right[#right + 1] = tostring(i)
        end
    end
    local chances = var("RuneChances") - 1
    set("RuneChances", chances)
    if #right == 4 then newRunes(); gameWon(7112); return end   -- :Correct (bless.wav is not imported)
    local text = tr("No rune is right.")
    if #right > 0 then text = tr("Right: rune {runes}.", {runes = table.concat(right, ", ")}) end
    if chances == 0 then evt.StatusText(text .. " " .. tr("You lose.")); newRunes()   -- :Incorrect
    else
        local left = ({tr("1 chance left."), tr("2 chances left."), tr("3 chances left.")})[chances]
        evt.StatusText(text .. " " .. left)
    end
end
handlers[602] = function() evt.StopTimer(602); evt.SetDoorState(3, DoorAction.Close) end

local function rnd(a, b)   -- MM9's GetRandomInt a, b (the high bits of the event generator)
    return a + math.floor(MM9.random(0, 1073741823) / 65536) % (b - a + 1)
end

-- StonesGame.scr "Square 6" (TronMgr), StonesSquare.scr (Square0-35), StonesPiece.scr (Piece0-35),
-- StonesPlayer.scr (TronPlayer, the bot). A 6 x 6 board, map vars St0-St35: 0 empty, 1 white (the party),
-- 2 black (the bot). A move goes on an empty square next to (8 ways) a stone of the mover's colour; after
-- each move, the side to move without a legal square loses (MM9's scan skips the last square). The first
-- move of a game takes a ticket; a win is key 7110. The board is set again on every load.
local ST_COGS = {700, 701, 702, 703, 704, 705, 706, 707, 708, 709, 710, 711, 712, 713, 714, 715, 716, 717, 718, 719, 720, 721, 722, 723, 724, 725, 726, 727, 728, 729, 730, 731, 732, 733, 734, 735}
local ST_OFFSETS = {-5, 1, 7, -6, 6, -7, -1, 5}   -- :SetupCheck (BOARDSIZE 6); 1-3 right, 6-8 left
local function stDraw(i, colour)   -- StonesPiece.scr :TurnWhite / :TurnBlack; empty keeps a grey stone
    local key = ST_COGS[i + 1]
    if colour == 1 then evt.SetSprite(key, 1, "mm9_stoneyellow_x200")
    elseif colour == 2 then evt.SetSprite(key, 1, "mm9_stoneblue_x200")
    else evt.SetSprite(key, 1, "mm9_stone") end
end
local function stSet(i, colour) set("St" .. i, colour); stDraw(i, colour) end
local function stLegal(i, colour)   -- :CheckSurrounding
    if var("St" .. i) ~= 0 then return false end
    for n, offset in ipairs(ST_OFFSETS) do
        local j = i + offset
        local edge = ((i + 1) % 6 == 0 and n <= 3) or (i % 6 == 0 and n >= 6) or j < 0 or j > 35
        if not edge and var("St" .. j) == colour then return true end
    end
    return false
end
local function stCanMove(colour)   -- :CheckVictory (while nCurSquare < LISTLAST: squares 0-34)
    for i = 0, 34 do if stLegal(i, colour) then return true end end
    return false
end
local function stReset()   -- :ResetVars, :ResetBoard: one white and the mirrored black at random
    for i = 0, 35 do stSet(i, 0) end
    local r = rnd(0, 35)
    stSet(r, 1); stSet(35 - r, 2); set("StTicket", 0); set("StTurn", 0)
end
-- A slain stones player (TronPlayer) takes no "play" (MM9.receives): the board waits on black, and the
-- party's next click places black (:CheckMove alternates the colours whoever clicks). Map var StTurn 2.
local ST_BOT = 57
local function stMove(i)   -- StonesSquare.scr :RequestMove -> StonesGame.scr :CheckMove
    if var("StTicket") == 0 then
        if not ticket() then return end
        set("StTicket", 1)
    end
    if var("StTurn") == 2 then   -- black's turn (:HandleInvalidMove sends the dead bot "play": nothing)
        if not stLegal(i, 2) then return end
        stSet(i, 2); set("StTurn", 0)
        if not stCanMove(1) then evt.StatusText("Black wins!!!"); stReset(); return end
        evt.StatusText("Your move.")
        return
    end
    if not stLegal(i, 1) then evt.StatusText("Stone must be placed adjacent to another of your stones."); return end   -- :HandleInvalidMove
    stSet(i, 1)
    if not stCanMove(2) then evt.StatusText("White wins!!!"); gameWon(7110); stReset(); return end
    if not MM9.receives("guberland", "TronPlayer", "play", ST_BOT) then set("StTurn", 2); return end
    local legal = {}   -- StonesPlayer.scr :PlacePiece: random squares until a legal one
    for j = 0, 35 do if stLegal(j, 2) then legal[#legal + 1] = j end end
    stSet(legal[rnd(1, #legal)], 2)
    if not stCanMove(1) then evt.StatusText("Black wins!!!"); stReset(); return end
    evt.StatusText("Your move.")
end
handlers[700] = function() stMove(0) end   -- Piece0 (Square0)
handlers[701] = function() stMove(1) end   -- Piece1 (Square1)
handlers[702] = function() stMove(2) end   -- Piece2 (Square2)
handlers[703] = function() stMove(3) end   -- Piece3 (Square3)
handlers[704] = function() stMove(4) end   -- Piece4 (Square4)
handlers[705] = function() stMove(5) end   -- Piece5 (Square5)
handlers[706] = function() stMove(6) end   -- Piece6 (Square6)
handlers[707] = function() stMove(7) end   -- Piece7 (Square7)
handlers[708] = function() stMove(8) end   -- Piece8 (Square8)
handlers[709] = function() stMove(9) end   -- Piece9 (Square9)
handlers[710] = function() stMove(10) end   -- Piece10 (Square10)
handlers[711] = function() stMove(11) end   -- Piece11 (Square11)
handlers[712] = function() stMove(12) end   -- Piece12 (Square12)
handlers[713] = function() stMove(13) end   -- Piece13 (Square13)
handlers[714] = function() stMove(14) end   -- Piece14 (Square14)
handlers[715] = function() stMove(15) end   -- Piece15 (Square15)
handlers[716] = function() stMove(16) end   -- Piece16 (Square16)
handlers[717] = function() stMove(17) end   -- Piece17 (Square17)
handlers[718] = function() stMove(18) end   -- Piece18 (Square18)
handlers[719] = function() stMove(19) end   -- Piece19 (Square19)
handlers[720] = function() stMove(20) end   -- Piece20 (Square20)
handlers[721] = function() stMove(21) end   -- Piece21 (Square21)
handlers[722] = function() stMove(22) end   -- Piece22 (Square22)
handlers[723] = function() stMove(23) end   -- Piece23 (Square23)
handlers[724] = function() stMove(24) end   -- Piece24 (Square24)
handlers[725] = function() stMove(25) end   -- Piece25 (Square25)
handlers[726] = function() stMove(26) end   -- Piece26 (Square26)
handlers[727] = function() stMove(27) end   -- Piece27 (Square27)
handlers[728] = function() stMove(28) end   -- Piece28 (Square28)
handlers[729] = function() stMove(29) end   -- Piece29 (Square29)
handlers[730] = function() stMove(30) end   -- Piece30 (Square30)
handlers[731] = function() stMove(31) end   -- Piece31 (Square31)
handlers[732] = function() stMove(32) end   -- Piece32 (Square32)
handlers[733] = function() stMove(33) end   -- Piece33 (Square33)
handlers[734] = function() stMove(34) end   -- Piece34 (Square34)
handlers[735] = function() stMove(35) end   -- Piece35 (Square35)

-- Whack-a-Honky.scr "<k> Honky 0 3" (Honky0-3) and Switch0 (OpenTrigger0 Honky0 "start"). A pull with a
-- ticket: Countdown5, then ten seconds (Wait 19, 15 EndGame from the pull) of geese, one up at a time: it
-- rises (0.2 s), waits 0.5-1 s, goes down (0.2 s) and another rises (:OnFinishedLower, never the same one); a
-- click on the raised goose counts (WHACK_COUNTER) and sends it down at once. Eight win (WIN_CONDITION):
-- key 7113. MM9 raises the geese 20 units from their holes; here the idle geese all stand, and while
-- the game runs only the raised one shows. Map vars: HonkState (0 idle, 1 countdown, 2 playing), HonkStep,
-- HonkUp (1-4, 0 none), HonkLast, HonkHits.
local HONK_COGS = {736, 737, 738, 739}
local HONK_COUNT = {"Five...", "Four...", "Three...", "Two...", "One..."}
local function honkShowAll(on) for i = 1, 4 do evt.SetSprite(HONK_COGS[i], on and 1 or 0, "0") end end
local function honkRaise()   -- :ReceivePopup
    local k = rnd(1, 4)
    while k == var("HonkLast") do k = rnd(1, 4) end
    set("HonkUp", k); set("HonkLast", k); evt.SetSprite(HONK_COGS[k], 1, "0")
    evt.StartTimer(603, seconds((200 + rnd(500, 1000)) / 1000))
end
local function honkLower()   -- :SendPopup
    local k = var("HonkUp")
    if k > 0 then evt.SetSprite(HONK_COGS[k], 0, "0") end
    set("HonkUp", 0); evt.StartTimer(603, seconds(0.2))
end
local function honkReset()
    evt.StopTimer(603); evt.StopTimer(604)
    set("HonkState", 0); set("HonkUp", 0); honkShowAll(true)
    evt.SetDoorState(4, DoorAction.Close)
end
handlers[104] = function()   -- Switch0 -> Honky0 :StartGame (replaces its door toggle)
    if var("HonkState") ~= 0 or not ticket() then return end
    evt.SetDoorState(4, DoorAction.Open)
    set("HonkState", 1); set("HonkStep", 1); set("HonkHits", 0); set("HonkLast", 0)
    evt.StatusText(HONK_COUNT[1]); evt.StartTimer(603, seconds(1))
    evt.StartTimer(604, seconds(15))
end
handlers[603] = function()
    local state = var("HonkState")
    if state == 1 then
        local step = var("HonkStep")
        if step < 5 then set("HonkStep", step + 1); evt.StatusText(HONK_COUNT[step + 1]); evt.StartTimer(603, seconds(1))
        else set("HonkState", 2); honkShowAll(false); honkRaise() end
    elseif state == 2 then
        if var("HonkUp") > 0 then honkLower() else honkRaise() end
    end
end
handlers[604] = function()   -- :EndGame
    if var("HonkState") ~= 2 then return end
    local hits = var("HonkHits")
    honkReset()
    if hits >= 8 then gameWon(7113) else evt.StatusText("You lose.") end
end
handlers[736] = function()   -- Honky0 :OnDamage
    if var("HonkState") ~= 2 or var("HonkUp") ~= 1 then return end
    set("HonkHits", var("HonkHits") + 1)
    evt.PlaySoundName("ambient/animals/goose honk.wav", 0, 0, 0)   -- MM9: animsounds\hen\fidget01
    honkLower()
end
handlers[737] = function()   -- Honky1 :OnDamage
    if var("HonkState") ~= 2 or var("HonkUp") ~= 2 then return end
    set("HonkHits", var("HonkHits") + 1)
    evt.PlaySoundName("ambient/animals/goose honk.wav", 0, 0, 0)   -- MM9: animsounds\hen\fidget01
    honkLower()
end
handlers[738] = function()   -- Honky2 :OnDamage
    if var("HonkState") ~= 2 or var("HonkUp") ~= 3 then return end
    set("HonkHits", var("HonkHits") + 1)
    evt.PlaySoundName("ambient/animals/goose honk.wav", 0, 0, 0)   -- MM9: animsounds\hen\fidget01
    honkLower()
end
handlers[739] = function()   -- Honky3 :OnDamage
    if var("HonkState") ~= 2 or var("HonkUp") ~= 4 then return end
    set("HonkHits", var("HonkHits") + 1)
    evt.PlaySoundName("ambient/animals/goose honk.wav", 0, 0, 0)   -- MM9: animsounds\hen\fidget01
    honkLower()
end

-- StonesPlayer.scr (TronPlayer) :OnRudeEnter: key 7002, DoRude 428; :OnRudeExit: 7002 taken. Live once
-- the actor carries RUDE 428 (it is placed with none: work/scr_spec.md).
handlers[53267] = function() MM9.giveKey(7002); MM9.openRude(428) end
handlers[50267] = function() MM9.takeKey(7002) end

-- Retainer.scr (Alvar the Clumsy, RUDE 178, key 458): gone while hired (also once his dialogue hires
-- him).
handlers[50345] = function()
    show(63, not has(458))
end

-- NPC150.scr :Init OnFoundPlayer :OnStart: the first time Scandlan perceives the party (without key 5020) he
-- and Broccan (NPC151.scr) talk, the cinematic newgame_talk (its steps at the end of this file).
handlers[56047] = function()
    if not has(5020) then MM9Cinematic.start("newgame_talk") end
end

-- Visibility and the games on every load (the scripts' :Init).
handlers.regionLoad = function()
    show(56, not has(127))   -- gone with Atli (atlipromo.scr :Init: once relieved)
    banditsWatch(true)   -- BanditAttack.scr OnPostSaveLoad OnAttack: the runners run on
    atliWatch()
    show(54, not has(127))   -- NPC186.scr :Init: gone to Thronheim
    show(55, not has(127))   -- NPC187.scr :Init: gone to Thronheim
    evt.SetSprite(400, has(127) and 0 or 1, "0")   -- Atliwagon.scr :Init: the ship is gone
    if var("BellPhase") ~= 0 then set("BellPhase", 0); evt.SetDoorState(1, DoorAction.Close) evt.SetDoorState(2, DoorAction.Close) end
    newRunes()   -- Mastermind.scr :InitMastermind
    for i = 1, 4 do set("RuneChosen" .. i, 0) end
    paintRune(401, -1)
    paintRune(402, -1)
    paintRune(403, -1)
    paintRune(404, -1)
    stReset()   -- StonesGame.scr :InitStonesGame
    honkReset()   -- Whack-a-Honky.scr :Main, :ResetPOS
    show(63, not has(458))   -- Retainer.scr :Init
    show(62, has(121))   -- NPC414.scr :Init: here once he has the circus job
end

handlers[1] = function()
    for k = 1024, 1033 do MM9.takeKey(k) end
    MM9.giveKey(1028)
    shopHours()
    if handlers.regionLoad then handlers.regionLoad() end
end

-- MM9's greeting voices (dungeon/voices.py): a click on these people plays their GreetingSound or the
-- voice their script's :OnUse plays, then opens their dialogue (or runs the map's own click).
handlers[53020] = function() MM9.playSound("voices/npc/npc_132.wav"); MM9.openRude(132) end   -- RUDEProp11
do local own = handlers[53021]; handlers[53021] = function() MM9.playSound("voices/npc/npc_133.wav"); own() end end   -- RUDEProp10
handlers[53022] = function() MM9.playSound("voices/npc/npc_130.wav"); MM9.openRude(130) end   -- RUDEProp9
handlers[53078] = function() MM9.playSound("voices/npc/npc_144.wav"); MM9.openRude(144) end   -- CommonerHumanMaleA0
handlers[53085] = function() MM9.playSound("voices/npc/npc_186.wav"); MM9.openRude(186) end   -- Atli
handlers[53086] = function() MM9.playSound("voices/npc/npc_187a.wav"); MM9.openRude(187) end   -- AtliDaughter
handlers[53344] = function() MM9.playSound("voices/npc/npc_414.wav"); MM9.openRude(414) end   -- Niclolai
handlers[53345] = function() MM9.playSound("voices/npc/npc_178.wav"); MM9.openRude(178) end   -- AlvartheClumsy

-- MM9's PerceptionBrushes (dungeon/perception.py): the red glow shows to a party whose Perception reaches the
-- brush's PerceptionValue, checked on load and every 3 s; map Lua turns one off for good with
-- set("HintOff<cog>", 1) (MM9's Off message to the brush).
local HINTS = {[23074] = 0, [23075] = 0, [23076] = 0, [23077] = 0}
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
RegisterMapTimerEvent(260, seconds(3), handlers[260], "Shop hours", "", seconds(3))
RegisterEvent(390, "Stat stone", handlers[390], "Touch")
RegisterEvent(53021, "Thorir Mouth", handlers[53021])
RegisterEvent(50021, "Thorir Mouth", handlers[50021])
RegisterEvent(50022, "Ivan the Smart", handlers[50022])
RegisterMapTimerEvent(600, seconds(3), handlers[600], "Atli's watch", "", seconds(3))
RegisterEvent(50085, "Atli Sigmundssen", handlers[50085])
RegisterEvent(50324, "Ticket master", handlers[50324])
RegisterEvent(53330, "Mata Abyomi", handlers[53330])
RegisterMapTimerEvent(605, seconds(3), handlers[605], "Mata's cower", "", seconds(3))
RegisterMapTimerEvent(601, seconds(3), handlers[601], "Bell", "", seconds(3))
RegisterEvent(330, "Rune", handlers[330], "Rune")
RegisterEvent(331, "Rune", handlers[331], "Rune")
RegisterEvent(332, "Rune", handlers[332], "Rune")
RegisterEvent(333, "Rune", handlers[333], "Rune")
RegisterEvent(334, "Rune", handlers[334], "Rune")
RegisterEvent(335, "Rune stone", handlers[335], "Rune")
RegisterEvent(336, "Rune stone", handlers[336], "Rune")
RegisterEvent(337, "Rune stone", handlers[337], "Rune")
RegisterEvent(338, "Rune stone", handlers[338], "Rune")
RegisterMapTimerEvent(602, seconds(3), handlers[602], "Rune switch", "", seconds(3))
RegisterEvent(700, "Stone", handlers[700], "Stone")
RegisterEvent(701, "Stone", handlers[701], "Stone")
RegisterEvent(702, "Stone", handlers[702], "Stone")
RegisterEvent(703, "Stone", handlers[703], "Stone")
RegisterEvent(704, "Stone", handlers[704], "Stone")
RegisterEvent(705, "Stone", handlers[705], "Stone")
RegisterEvent(706, "Stone", handlers[706], "Stone")
RegisterEvent(707, "Stone", handlers[707], "Stone")
RegisterEvent(708, "Stone", handlers[708], "Stone")
RegisterEvent(709, "Stone", handlers[709], "Stone")
RegisterEvent(710, "Stone", handlers[710], "Stone")
RegisterEvent(711, "Stone", handlers[711], "Stone")
RegisterEvent(712, "Stone", handlers[712], "Stone")
RegisterEvent(713, "Stone", handlers[713], "Stone")
RegisterEvent(714, "Stone", handlers[714], "Stone")
RegisterEvent(715, "Stone", handlers[715], "Stone")
RegisterEvent(716, "Stone", handlers[716], "Stone")
RegisterEvent(717, "Stone", handlers[717], "Stone")
RegisterEvent(718, "Stone", handlers[718], "Stone")
RegisterEvent(719, "Stone", handlers[719], "Stone")
RegisterEvent(720, "Stone", handlers[720], "Stone")
RegisterEvent(721, "Stone", handlers[721], "Stone")
RegisterEvent(722, "Stone", handlers[722], "Stone")
RegisterEvent(723, "Stone", handlers[723], "Stone")
RegisterEvent(724, "Stone", handlers[724], "Stone")
RegisterEvent(725, "Stone", handlers[725], "Stone")
RegisterEvent(726, "Stone", handlers[726], "Stone")
RegisterEvent(727, "Stone", handlers[727], "Stone")
RegisterEvent(728, "Stone", handlers[728], "Stone")
RegisterEvent(729, "Stone", handlers[729], "Stone")
RegisterEvent(730, "Stone", handlers[730], "Stone")
RegisterEvent(731, "Stone", handlers[731], "Stone")
RegisterEvent(732, "Stone", handlers[732], "Stone")
RegisterEvent(733, "Stone", handlers[733], "Stone")
RegisterEvent(734, "Stone", handlers[734], "Stone")
RegisterEvent(735, "Stone", handlers[735], "Stone")
RegisterEvent(736, "Goose", handlers[736], "Goose")
RegisterEvent(737, "Goose", handlers[737], "Goose")
RegisterEvent(738, "Goose", handlers[738], "Goose")
RegisterEvent(739, "Goose", handlers[739], "Goose")
RegisterEvent(104, "Whack-a-honky lever", handlers[104], "Lever")
RegisterMapTimerEvent(603, seconds(3), handlers[603], "Whack-a-honky", "", seconds(3))
RegisterMapTimerEvent(604, seconds(3), handlers[604], "Whack-a-honky end", "", seconds(3))
RegisterEvent(53267, "Stones player", handlers[53267])
RegisterEvent(50267, "Stones player", handlers[50267])
RegisterEvent(50345, "Alvar the Clumsy", handlers[50345])
RegisterEvent(56047, "Scandlan", handlers[56047])
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(53020, "Hjordisa the Hag", handlers[53020])
RegisterEvent(53022, "Ivan the Smart", handlers[53022])
RegisterEvent(53078, "Olaf Ullson", handlers[53078])
RegisterEvent(53085, "Atli Sigmundssen", handlers[53085])
RegisterEvent(53086, "Hungerda Atlidotir", handlers[53086])
RegisterEvent(53344, "Nicolai Ironfist", handlers[53344])
RegisterEvent(53345, "Alvar the Clumsy", handlers[53345])
RegisterMapTimerEvent(901, seconds(3), handlers[901], "Perception hints", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])


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

-- Cinematic newgame_talk (NPC150.scr :OnStart..:OnSpeak12, NPC151.scr): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["newgame_talk"] = {
    { "key", function()
        MM9.giveKey(5020)
    end },
    { "hears02", function()
        if evt.GetMapVar("NewgameTalkBroken", 0) == 0 and not MM9.receives("guberland", "Broccan", "Speak2", 44) then
            evt.SetMapVar("NewgameTalkBroken", 1)
            evt.SkipCinematic()
        end
    end },
    { "hears03", function()
        if evt.GetMapVar("NewgameTalkBroken", 0) == 0 and not MM9.receives("guberland", "Scandlan", "Speak3", 43) then
            evt.SetMapVar("NewgameTalkBroken", 1)
            evt.SkipCinematic()
        end
    end },
    { "hears04", function()
        if evt.GetMapVar("NewgameTalkBroken", 0) == 0 and not MM9.receives("guberland", "Broccan", "Speak4", 44) then
            evt.SetMapVar("NewgameTalkBroken", 1)
            evt.SkipCinematic()
        end
    end },
    { "hears05", function()
        if evt.GetMapVar("NewgameTalkBroken", 0) == 0 and not MM9.receives("guberland", "Scandlan", "Speak5", 43) then
            evt.SetMapVar("NewgameTalkBroken", 1)
            evt.SkipCinematic()
        end
    end },
    { "hears06", function()
        if evt.GetMapVar("NewgameTalkBroken", 0) == 0 and not MM9.receives("guberland", "Broccan", "Speak6", 44) then
            evt.SetMapVar("NewgameTalkBroken", 1)
            evt.SkipCinematic()
        end
    end },
    { "hears07", function()
        if evt.GetMapVar("NewgameTalkBroken", 0) == 0 and not MM9.receives("guberland", "Scandlan", "Speak7", 43) then
            evt.SetMapVar("NewgameTalkBroken", 1)
            evt.SkipCinematic()
        end
    end },
    { "hears08", function()
        if evt.GetMapVar("NewgameTalkBroken", 0) == 0 and not MM9.receives("guberland", "Broccan", "Speak8", 44) then
            evt.SetMapVar("NewgameTalkBroken", 1)
            evt.SkipCinematic()
        end
    end },
    { "hears09", function()
        if evt.GetMapVar("NewgameTalkBroken", 0) == 0 and not MM9.receives("guberland", "Scandlan", "Speak9", 43) then
            evt.SetMapVar("NewgameTalkBroken", 1)
            evt.SkipCinematic()
        end
    end },
    { "hears10", function()
        if evt.GetMapVar("NewgameTalkBroken", 0) == 0 and not MM9.receives("guberland", "Broccan", "Speak10", 44) then
            evt.SetMapVar("NewgameTalkBroken", 1)
            evt.SkipCinematic()
        end
    end },
    { "hears11", function()
        if evt.GetMapVar("NewgameTalkBroken", 0) == 0 and not MM9.receives("guberland", "Scandlan", "Speak11", 43) then
            evt.SetMapVar("NewgameTalkBroken", 1)
            evt.SkipCinematic()
        end
    end },
    { "walk_away", function()
        if evt.GetMapVar("NewgameTalkBroken", 0) == 0 and MM9.receives("guberland", "Broccan", "Speak12", 44) then
            evt.ClearActorPresentation(44)
            evt.MoveActorTo(44, 15766, 18704, 120)
        end
    end },
}
RegisterEvent(36001, "Cinema newgame_talk: key", function() MM9Cinematic.runStep("newgame_talk", 1) end)
RegisterEvent(36002, "Cinema newgame_talk: hears02", function() MM9Cinematic.runStep("newgame_talk", 2) end)
RegisterEvent(36003, "Cinema newgame_talk: hears03", function() MM9Cinematic.runStep("newgame_talk", 3) end)
RegisterEvent(36004, "Cinema newgame_talk: hears04", function() MM9Cinematic.runStep("newgame_talk", 4) end)
RegisterEvent(36005, "Cinema newgame_talk: hears05", function() MM9Cinematic.runStep("newgame_talk", 5) end)
RegisterEvent(36006, "Cinema newgame_talk: hears06", function() MM9Cinematic.runStep("newgame_talk", 6) end)
RegisterEvent(36007, "Cinema newgame_talk: hears07", function() MM9Cinematic.runStep("newgame_talk", 7) end)
RegisterEvent(36008, "Cinema newgame_talk: hears08", function() MM9Cinematic.runStep("newgame_talk", 8) end)
RegisterEvent(36009, "Cinema newgame_talk: hears09", function() MM9Cinematic.runStep("newgame_talk", 9) end)
RegisterEvent(36010, "Cinema newgame_talk: hears10", function() MM9Cinematic.runStep("newgame_talk", 10) end)
RegisterEvent(36011, "Cinema newgame_talk: hears11", function() MM9Cinematic.runStep("newgame_talk", 11) end)
RegisterEvent(36012, "Cinema newgame_talk: walk_away", function() MM9Cinematic.runStep("newgame_talk", 12) end)
RegisterEvent(36000, "Cinema newgame_talk: done", function() MM9Cinematic.finish("newgame_talk") end)
MM9Cinematic.play["newgame_talk"] = function()
    if evt.GetMapVar("Cinema.newgame_talk.started", 0) == 0 then
        evt.SetMapVar("Cinema.newgame_talk.started", 1)
        evt.PlayCinematic("newgame_talk", 36000)
    end
end

