-- Thjorgard, MM9 rework (level_generation/projects/mm9r_thjorgard/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {Riser1 = 1, Strikeplate1 = 2, Switch = 3, Switch0 = 4, ["cottage door"] = 5, ["mine cart door left"] = 6, ["mine cart door right"] = 7}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 902}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(1, DoorAction.Trigger) end   -- Riser1
handlers[102] = function() evt.SetDoorState(2, DoorAction.Trigger) end   -- Strikeplate1
handlers[103] = function() evt.SetDoorState(3, DoorAction.Trigger) end   -- Switch
handlers[104] = function() evt.SetDoorState(4, DoorAction.Trigger) end   -- Switch0
handlers[105] = function() evt.SetDoorState(5, DoorAction.Trigger) end   -- cottage_door

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest0
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest

local function has(k) return MM9.hasKey(k) == 1 end
local function quest() MM9.playSound("sounds/events/quest.wav") end
local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; if gold > 0 then MM9.giveGold(gold) end; quest() end

-- Doors MM9 never opens (mine_cart_door_left): a click says so (doorlock01.wav).
local function lockedDoor() evt.PlaySoundName("door/doorlock01.wav", 0, 0, 0); evt.StatusText("The door is locked.") end
handlers[106] = lockedDoor
-- ForadWorld.scr (ScriptObject0, "thjorgard"): key 1025 is the party's location while here (keys
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
local function say(text) evt.StatusText(text) end
local function rnd(a, b)   -- MM9's GetRandomInt a, b (the high bits of the event generator)
    return a + math.floor(MM9.random(0, 1073741823) / 65536) % (b - a + 1)
end

-- ThjorgardGamesCommon.inc: :CheckGameTicket + :TakeGameTicket (item 557), :Record*Win -> :CheckThjorgardWins
-- -> :GiveThjorgardPrize (all six games won while on Yrsa's quest, key 93; MM9 waits two seconds first).
local function ticket()
    if MM9.hasItem(557, "thjorgard:games") ~= 1 then say("Sorry, you need a ticket to play..."); return false end
    MM9.takeItem(557, "thjorgard:games"); say("You used a ticket.")
    return true
end
local function gameWon(key)
    say("You Win!"); MM9.giveKey(key)
    if has(7106) then return end
    for k = 7100, 7105 do if not has(k) then return end end
    if not has(93) then return end
    MM9.giveKey(7106); MM9.giveExperience(10000); MM9.giveItem(395, "thjorgard:games"); MM9.giveKey(94); quest()
    say("You received the Stuffed Dragon for completing all the games!")
end
local function gameLost() say("You Lost.") end
local function currentMight()   -- GetAttribute 0: the active character's Might
    evt.ForPlayer(Players.Current)
    local low, high = 0, 1023
    while low < high do
        local mid = math.floor((low + high + 1) / 2)
        if IsAtLeast(ActualMight, mid) then low = mid else high = mid - 1 end
    end
    return low
end

-- HucksterMod.scr :OnRudeExit (TicketMaster, RUDE 429): his row "We'd love to play" gives key 1001 (one
-- ticket, 5 gold), "a batch" key 1010 (ten, 40 gold); the rule book (item 594) comes with the first.
-- Without the gold MM9 plays a character's grumble (NoGold.inc): its text 229 here.
local function sellTickets(count, cost)   -- :SellGameTicket, :SellBatchTickets
    if MM9.hasGold(cost) ~= 1 then say("You do not have enough gold to purchase a ticket."); return end
    evt.PlaySoundName("events/gold01.wav", 0, 0, 0)
    MM9.takeGold(cost); if MM9.hasItem(594, "thjorgard:games") ~= 1 then MM9.giveItem(594, "thjorgard:games") end
    for _ = 1, count do MM9.giveItem(557, "thjorgard:games") end
    say(count == 1 and "You bought a ticket." or "You bought 10 tickets.")
end
handlers[50673] = function()
    if has(1001) then MM9.takeKey(1001); sellTickets(1, 5)
    elseif has(1010) then MM9.takeKey(1010); sellTickets(10, 40) end
end

-- StonesGame.scr "Square 6" (TronMgr), StonesSquare.scr (Square0-35), StonesPiece.scr (Piece0-35),
-- StonesPlayer.scr (TronPlayer, the bot). A 6 x 6 board, map vars St0-St35: 0 empty, 1 white (the party),
-- 2 black (the bot). A move goes on an empty square next to (8 ways) a stone of the mover's colour; after
-- each move, the side to move without a legal square loses (MM9's scan skips the last square). The first
-- move of a game takes a ticket. The board is set again on every load (:InitStonesGame).
local ST_COGS = {400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435}
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
local ST_BOT = 39
local function stMove(i)   -- StonesSquare.scr :RequestMove -> StonesGame.scr :CheckMove
    if var("StTicket") == 0 then
        if not ticket() then return end
        set("StTicket", 1)
    end
    if var("StTurn") == 2 then   -- black's turn (:HandleInvalidMove sends the dead bot "play": nothing)
        if not stLegal(i, 2) then return end
        stSet(i, 2); set("StTurn", 0)
        if not stCanMove(1) then say("Black wins!!!"); stReset(); return end
        say("Your move.")
        return
    end
    if not stLegal(i, 1) then say("Stone must be placed adjacent to another of your stones."); return end   -- :HandleInvalidMove
    stSet(i, 1)
    if not stCanMove(2) then say("White wins!!!"); gameWon(7100); stReset(); return end
    if not MM9.receives("thjorgard", "TronPlayer", "play", ST_BOT) then set("StTurn", 2); return end
    local legal = {}   -- StonesPlayer.scr :PlacePiece: random squares until a legal one
    for j = 0, 35 do if stLegal(j, 2) then legal[#legal + 1] = j end end
    stSet(legal[rnd(1, #legal)], 2)
    if not stCanMove(1) then say("Black wins!!!"); stReset(); return end
    say("Your move.")
end
handlers[600] = function() stMove(0) end   -- Piece0 (Square0)
handlers[601] = function() stMove(1) end   -- Piece1 (Square1)
handlers[602] = function() stMove(2) end   -- Piece2 (Square2)
handlers[603] = function() stMove(3) end   -- Piece3 (Square3)
handlers[604] = function() stMove(4) end   -- Piece4 (Square4)
handlers[605] = function() stMove(5) end   -- Piece5 (Square5)
handlers[606] = function() stMove(6) end   -- Piece6 (Square6)
handlers[607] = function() stMove(7) end   -- Piece7 (Square7)
handlers[608] = function() stMove(8) end   -- Piece8 (Square8)
handlers[609] = function() stMove(9) end   -- Piece9 (Square9)
handlers[610] = function() stMove(10) end   -- Piece10 (Square10)
handlers[611] = function() stMove(11) end   -- Piece11 (Square11)
handlers[612] = function() stMove(12) end   -- Piece12 (Square12)
handlers[613] = function() stMove(13) end   -- Piece13 (Square13)
handlers[614] = function() stMove(14) end   -- Piece14 (Square14)
handlers[615] = function() stMove(15) end   -- Piece15 (Square15)
handlers[616] = function() stMove(16) end   -- Piece16 (Square16)
handlers[617] = function() stMove(17) end   -- Piece17 (Square17)
handlers[618] = function() stMove(18) end   -- Piece18 (Square18)
handlers[619] = function() stMove(19) end   -- Piece19 (Square19)
handlers[620] = function() stMove(20) end   -- Piece20 (Square20)
handlers[621] = function() stMove(21) end   -- Piece21 (Square21)
handlers[622] = function() stMove(22) end   -- Piece22 (Square22)
handlers[623] = function() stMove(23) end   -- Piece23 (Square23)
handlers[624] = function() stMove(24) end   -- Piece24 (Square24)
handlers[625] = function() stMove(25) end   -- Piece25 (Square25)
handlers[626] = function() stMove(26) end   -- Piece26 (Square26)
handlers[627] = function() stMove(27) end   -- Piece27 (Square27)
handlers[628] = function() stMove(28) end   -- Piece28 (Square28)
handlers[629] = function() stMove(29) end   -- Piece29 (Square29)
handlers[630] = function() stMove(30) end   -- Piece30 (Square30)
handlers[631] = function() stMove(31) end   -- Piece31 (Square31)
handlers[632] = function() stMove(32) end   -- Piece32 (Square32)
handlers[633] = function() stMove(33) end   -- Piece33 (Square33)
handlers[634] = function() stMove(34) end   -- Piece34 (Square34)
handlers[635] = function() stMove(35) end   -- Piece35 (Square35)

-- StonesPlayer.scr :OnRudeEnter / :OnRudeExit (TronPlayer): key 7002 opens his row of RUDE 428.
handlers[53593] = function() MM9.giveKey(7002); MM9.openRude(428) end
handlers[50593] = function() MM9.takeKey(7002) end

-- Mastermind.scr "FireCorrect", MastermindColor.scr (ColorButton0-4), MastermindSpace.scr (ColorSpace0-3)
-- and the Switch door (OpenTrigger "check"). Map vars: MMCode1-4 the hidden colours (0-4), MMPick1-4 the
-- chosen ones (colour + 1), MMColor the button last pressed, MMChances, MMTicket (paid this round). A new
-- code on every load, after a win and after the fourth miss (:GenerateColors keeps the chosen stones).
local MM_COGS = {436, 437, 438, 439}
local MM_PLACE = {1, 2, 3, 4}   -- each stone's place from the left
local function mmPaint(slot, colour)   -- MastermindSpace.scr :ChangeColor (SetModelFilenames)
    local key = MM_COGS[slot]
    if colour == 0 then evt.SetSprite(key, 1, "mm9_stonered_x200")
    elseif colour == 1 then evt.SetSprite(key, 1, "mm9_stoneblue_x200")
    elseif colour == 2 then evt.SetSprite(key, 1, "mm9_stoneyellow_x200")
    elseif colour == 3 then evt.SetSprite(key, 1, "mm9_stoneorange_x200")
    elseif colour == 4 then evt.SetSprite(key, 1, "mm9_stonegreen_x200")
    else evt.SetSprite(key, 1, "mm9_stone_x200") end
end
local function mmNew()   -- :GenerateColors
    for i = 1, 4 do set("MMCode" .. i, rnd(0, 4)) end
    set("MMChances", 4); set("MMTicket", 0)
end
local function mmPaid()   -- bNeedsTicket: the first pick or check of a round takes a ticket
    if var("MMTicket") == 1 then return true end
    if not ticket() then return false end
    set("MMTicket", 1)
    return true
end
handlers[636] = function() evt.PlaySoundName("door/trapdooropen.wav", 0, 0, 0); set("MMColor", 0) end   -- ColorButton0 (MastermindColor.scr :ChangeColor)
handlers[637] = function() evt.PlaySoundName("door/trapdooropen.wav", 0, 0, 0); set("MMColor", 1) end   -- ColorButton1 (MastermindColor.scr :ChangeColor)
handlers[638] = function() evt.PlaySoundName("door/trapdooropen.wav", 0, 0, 0); set("MMColor", 2) end   -- ColorButton2 (MastermindColor.scr :ChangeColor)
handlers[639] = function() evt.PlaySoundName("door/trapdooropen.wav", 0, 0, 0); set("MMColor", 3) end   -- ColorButton3 (MastermindColor.scr :ChangeColor)
handlers[640] = function() evt.PlaySoundName("door/trapdooropen.wav", 0, 0, 0); set("MMColor", 4) end   -- ColorButton4 (MastermindColor.scr :ChangeColor)
handlers[641] = function()   -- ColorSpace0 (MastermindSpace.scr :UpdateColor; Mastermind.scr :ColorChosen)
    local colour = var("MMColor")
    if var("MMChances") > 0 and mmPaid() then set("MMPick1", colour + 1) end
    evt.PlaySoundName("door/doorlatch01.wav", 0, 0, 0); mmPaint(1, colour)
end
handlers[642] = function()   -- ColorSpace1 (MastermindSpace.scr :UpdateColor; Mastermind.scr :ColorChosen)
    local colour = var("MMColor")
    if var("MMChances") > 0 and mmPaid() then set("MMPick2", colour + 1) end
    evt.PlaySoundName("door/doorlatch01.wav", 0, 0, 0); mmPaint(2, colour)
end
handlers[643] = function()   -- ColorSpace2 (MastermindSpace.scr :UpdateColor; Mastermind.scr :ColorChosen)
    local colour = var("MMColor")
    if var("MMChances") > 0 and mmPaid() then set("MMPick3", colour + 1) end
    evt.PlaySoundName("door/doorlatch01.wav", 0, 0, 0); mmPaint(3, colour)
end
handlers[644] = function()   -- ColorSpace3 (MastermindSpace.scr :UpdateColor; Mastermind.scr :ColorChosen)
    local colour = var("MMColor")
    if var("MMChances") > 0 and mmPaid() then set("MMPick4", colour + 1) end
    evt.PlaySoundName("door/doorlatch01.wav", 0, 0, 0); mmPaint(4, colour)
end
-- The Switch (a push door: its open sends "check"): it goes down on a click and back up on the next tick.
-- Mastermind.scr :CompareColors lights a flame by each right stone (told here), then :Correct (MM9 plays
-- spells\bless.wav, not among the imported sounds: the quest sound) or :Incorrect.
handlers[103] = function()
    evt.SetDoorState(3, DoorAction.Open); set("MMSwitch", 1)
    if var("MMChances") <= 0 or not mmPaid() then return end
    local right = {}
    for i = 1, 4 do
        if var("MMPick" .. i) == var("MMCode" .. i) + 1 then right[#right + 1] = MM_PLACE[i] end
    end
    local chances = var("MMChances") - 1
    set("MMChances", chances)
    if #right == 4 then quest(); mmNew(); gameWon(7102); return end
    table.sort(right)
    local flames = #right == 0 and tr("No flame burns.")
        or tr("Flames burn by stone {stones} (from the left).", {stones = table.concat(right, ", ")})
    local left = {"Only 1 chance left!!!", "Only 2 chances left!!!", "Only 3 chances left!!!"}
    if chances == 0 then say(flames .. " " .. tr("You Lost.")); mmNew() else say(flames .. " " .. tr(left[chances])) end
end

-- BoatJudge.scr "RacingBoat 0 3" (RUDE 429) and RacingBoat.scr. A click gives key 7003 (his rows about
-- the race); leaving with key 7004 ("Sure!") and a ticket starts the countdown (Countdown5: Five... One...,
-- the bell), then the race. The party's boat moves one length (a tenth of the way, one second) per hit;
-- here per click, not again while it moves. The three rival boats move a length in two to four seconds
-- each (here a random share every half second). Map vars: BoatState (0 idle, 1 countdown, 2 racing),
-- BoatCount (countdown ticks), BoatPushes, BoatMoving (ticks), BoatAI1-3 (hundredths of a length).
local BOAT_COUNT = {"One...", "Two...", "Three...", "Four..."}
handlers[53669] = function() MM9.giveKey(7003); MM9.openRude(429) end   -- :OnUse
handlers[50669] = function()   -- :StartRace
    MM9.takeKey(7003)
    if not has(7004) then return end
    MM9.takeKey(7004)
    if var("BoatState") ~= 0 or not ticket() then return end
    set("BoatState", 1); set("BoatCount", 10); set("BoatPushes", 0); set("BoatMoving", 0)
    for b = 1, 3 do set("BoatAI" .. b, 0) end
    evt.PlaySoundName("door/doorlock01.wav", 0, 0, 0); say("Five...")
end
handlers[645] = function()   -- RacingBoat0 (RacingBoat.scr :Ready -> :MoveForward)
    if var("BoatState") ~= 2 or var("BoatMoving") > 0 then return end
    set("BoatPushes", var("BoatPushes") + 1); set("BoatMoving", 2)
    say(tr("Your boat: {pushes} of 10 lengths.", {pushes = var("BoatPushes")}))
end
local function boatEnd(won)   -- BoatJudge.scr :PlayerWon / :AIWon, then the boats submerge and reset
    set("BoatState", 0)
    -- RacingBoat.scr :Arrived sends the judge PlayerArrival / CPUArrival: a slain judge takes neither (no
    -- result; the race is over, and no new one starts without his dialogue)
    if not MM9.receives("thjorgard", "BoatJudge", won and "PlayerArrival" or "CPUArrival", 51) then return end
    if won then evt.PlaySoundName("events/trumpets02.wav", 0, 0, 0); gameWon(7101) else gameLost() end
end
local function boatTick(tick)
    local state = var("BoatState")
    if state == 1 then
        local count = var("BoatCount") - 1
        set("BoatCount", count)
        if count % 2 ~= 0 then return end
        if count > 0 then evt.PlaySoundName("door/doorlock01.wav", 0, 0, 0); say(BOAT_COUNT[math.floor(count / 2)])
        else evt.PlaySoundName("events/dingbell.wav", 0, 0, 0); set("BoatState", 2) end   -- :Countdown0
    elseif state == 2 then
        local moving = var("BoatMoving")
        if moving > 0 then
            set("BoatMoving", moving - 1)
            if moving == 1 and var("BoatPushes") >= 10 then boatEnd(true); return end
        end
        local best = 0
        for b = 1, 3 do
            local p = var("BoatAI" .. b) + rnd(12, 25)
            set("BoatAI" .. b, p)
            if p > best then best = p end
        end
        if best >= 1000 then boatEnd(false); return end
        if tick % 4 == 0 then
            say(tr("Your boat: {pushes} of 10 lengths; the leading rival: {rival}.",
                {pushes = var("BoatPushes"), rival = math.floor(best / 100)}))
        end
    end
end

-- DingTheBell.scr (Strikeplate1) and BellWeight.scr "360" (Riser1). A click with a ticket: ding 60-80,
-- timing 40-60 + the character's Might (GetAttribute 0; the active character here); the weight climbs to
-- timing / ding of its full height (BellWeight :AdjustHeight); it rings and wins when timing > ding
-- (:CheckWin, when the weight stops). The plate takes no click for three seconds after (:BlockUse).
-- Map vars: BellStage (0 idle, 1 rising, 2 waiting), BellWin. The weight's way up takes 1.03 s.
handlers[102] = function()   -- :HitBell
    if var("BellStage") ~= 0 or not ticket() then return end
    local ding, timing = rnd(60, 80), rnd(40, 60) + currentMight()
    set("BellWin", timing > ding and 1 or 0); set("BellStage", 1)
    evt.SetDoorState(2, DoorAction.Open) evt.SetDoorState(1, DoorAction.Open)
    evt.StartTimer(301, seconds(math.min(1, timing / ding) * 1.029))
end
handlers[301] = function()
    local stage = var("BellStage")
    if stage == 1 then   -- the weight at its height: Strikeplate1 "ring" -> :CheckWin
        evt.SetDoorState(1, DoorAction.Close)
        if var("BellWin") == 1 then evt.PlaySoundName("events/dingbell.wav", 0, 0, 0); gameWon(7104)
        else gameLost() end
        set("BellStage", 2); evt.StartTimer(301, seconds(3))
    else   -- :AllowUse
        if stage == 2 then evt.SetDoorState(2, DoorAction.Close) end
        set("BellStage", 0); evt.StopTimer(301)
    end
end

-- Riser1 is the bell's weight (PushOpen 0 in MM9): a click does nothing.
handlers[101] = function() end

-- Whack-a-Honky.scr "<k> Honky 0 3" (Honky0-3) and Switch0 (OpenTrigger0 Honky0 "start"). A pull with a
-- ticket: Countdown5, then ten seconds (Wait 19, 15 EndGame from the pull) of geese, one up at a time: it
-- rises (0.2 s), waits 0.5-1 s, goes down (0.2 s) and another rises (:OnFinishedLower, never the same one); a
-- click on the raised goose counts (WHACK_COUNTER) and sends it down at once. Eight win (WIN_CONDITION).
-- MM9 raises the geese 20 units from their holes; here the idle geese all stand, and while the game runs
-- only the raised one shows. Map vars: HonkState (0 idle, 1 countdown, 2 playing), HonkStep, HonkUp (1-4,
-- 0 none), HonkLast, HonkHits.
local HONK_COGS = {440, 441, 442, 443}
local HONK_COUNT = {"Five...", "Four...", "Three...", "Two...", "One..."}
local function honkShowAll(on) for i = 1, 4 do evt.SetSprite(HONK_COGS[i], on and 1 or 0, "0") end end
local function honkRaise()   -- :ReceivePopup
    local k = rnd(1, 4)
    while k == var("HonkLast") do k = rnd(1, 4) end
    set("HonkUp", k); set("HonkLast", k); evt.SetSprite(HONK_COGS[k], 1, "0")
    evt.StartTimer(302, seconds((200 + rnd(500, 1000)) / 1000))
end
local function honkLower()   -- :SendPopup
    local k = var("HonkUp")
    if k > 0 then evt.SetSprite(HONK_COGS[k], 0, "0") end
    set("HonkUp", 0); evt.StartTimer(302, seconds(0.2))
end
local function honkReset()
    evt.StopTimer(302); evt.StopTimer(303)
    set("HonkState", 0); set("HonkUp", 0); honkShowAll(true)
    evt.SetDoorState(4, DoorAction.Close)
end
handlers[104] = function()   -- Switch0 -> Honky0 :StartGame
    if var("HonkState") ~= 0 or not ticket() then return end
    evt.SetDoorState(4, DoorAction.Open)
    set("HonkState", 1); set("HonkStep", 1); set("HonkHits", 0); set("HonkLast", 0)
    say(HONK_COUNT[1]); evt.StartTimer(302, seconds(1))
    evt.StartTimer(303, seconds(15))
end
handlers[302] = function()
    local state = var("HonkState")
    if state == 1 then
        local step = var("HonkStep")
        if step < 5 then set("HonkStep", step + 1); say(HONK_COUNT[step + 1]); evt.StartTimer(302, seconds(1))
        else set("HonkState", 2); honkShowAll(false); honkRaise() end
    elseif state == 2 then
        if var("HonkUp") > 0 then honkLower() else honkRaise() end
    end
end
handlers[303] = function()   -- :EndGame
    if var("HonkState") ~= 2 then return end
    local hits = var("HonkHits")
    honkReset()
    if hits >= 8 then gameWon(7103) else gameLost() end
end
handlers[646] = function()   -- Honky0 :OnDamage
    if var("HonkState") ~= 2 or var("HonkUp") ~= 1 then return end
    set("HonkHits", var("HonkHits") + 1)
    evt.PlaySoundName("ambient/animals/goose honk.wav", 0, 0, 0)   -- MM9: animsounds\hen\fidget01
    honkLower()
end
handlers[647] = function()   -- Honky1 :OnDamage
    if var("HonkState") ~= 2 or var("HonkUp") ~= 2 then return end
    set("HonkHits", var("HonkHits") + 1)
    evt.PlaySoundName("ambient/animals/goose honk.wav", 0, 0, 0)   -- MM9: animsounds\hen\fidget01
    honkLower()
end
handlers[648] = function()   -- Honky2 :OnDamage
    if var("HonkState") ~= 2 or var("HonkUp") ~= 3 then return end
    set("HonkHits", var("HonkHits") + 1)
    evt.PlaySoundName("ambient/animals/goose honk.wav", 0, 0, 0)   -- MM9: animsounds\hen\fidget01
    honkLower()
end
handlers[649] = function()   -- Honky3 :OnDamage
    if var("HonkState") ~= 2 or var("HonkUp") ~= 4 then return end
    set("HonkHits", var("HonkHits") + 1)
    evt.PlaySoundName("ambient/animals/goose honk.wav", 0, 0, 0)   -- MM9: animsounds\hen\fidget01
    honkLower()
end

-- Armwrestle.scr "2" (HalfOrcCaptain0) :OnUse -> :StartMightGame: with a ticket, his 2 + 1-40 against the
-- active character's Might (GetAttribute 0) + 9-50; a tie wins. A win: :StartCower (PlayAnim cowerstart,
-- LoopAnim cower 5, PlayAnim cowerstop), his use removed until it ends (:RemoveUse, :RestoreUse). His body
-- (the Half Orc's) has only the loop, cower: five of it (MM9's DookMilitia.abc has no cowerstop either).
local WRESTLER = 38
handlers[53117] = function()
    if var("Tick") < var("WrestlerCowerUntil") then return end   -- :RemoveUse while he cowers
    if not ticket() then return end
    local mine, theirs = 2 + rnd(1, 40), currentMight() + rnd(9, 50)
    if theirs >= mine then
        evt.PlayActorClip(WRESTLER, {"cower", "cower", "cower", "cower", "cower"}, false)
        set("WrestlerCowerUntil", var("Tick") + 30)
        gameWon(7105)
    else gameLost() end
end

-- Thorgard_actor.scr :SetupKen (Ken1-3): hidden, not solid, until RobPlayerTrigger sends RobPlayer; at
-- night (18:00-05:00, :IsNightTime) they appear and come for the party (:OnRobPlayer; the walk to their
-- markers and the taunt are the monster AI's). Map var KensOut: they have appeared.
local KENS = {0, 1, 2}
local KEN_NAMES = {"Ken1", "Ken2", "Ken3"}
local function robberTick()
    if var("KensOut") == 1 then return end
    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24
    if hour < 18 and hour >= 5 then return end
    local x, y, z = evt.GetPartyPosition()
    if x < -7113 or x > -6729 or y < 11475 or y > 11859 or z < 1648 or z > 1968 then return end
    set("KensOut", 1)
    for k, a in ipairs(KENS) do   -- a slain Ken takes no RobPlayer (MM9.receives)
        if MM9.receives("thjorgard", KEN_NAMES[k], "RobPlayer", a) then show(a, true) end
    end
end

-- Thorgard_actor.scr / Jumper.inc (Jumper0-3, the bandits on the cliff): hidden, not solid, until
-- JumperTrigger (once): Jumper0 GetPlayer at once, Jumper1-3 WaitGetPlayer (Jumper.inc 1-2.5 s; Jumper2
-- 10-25 s, Jumper3 30-45 s, Thorgard_actor.scr :JumperWaitGetPlayer); then they appear and come for the party
-- (the leap's clips below; the monster AI takes them on sight). Their DeathTriggerTarget: Jumper0's death sends
-- Jumper2 BuddyDead, Jumper1's Jumper3 (:SetupJumper AddTrigger BuddyDead, JumperGetPlayer: at once).
-- Map vars JumpersSprung, JumperDue<k> (the tick it appears), JumperOut<k>.
local JUMPERS = {7, 8, 14, 15}   -- Jumper0, Jumper1, Jumper2, Jumper3
local JUMPER_WAIT = {{0, 0}, {2, 5}, {20, 50}, {60, 90}}   -- half-second ticks
local JUMPER_NAMES = {"Jumper0", "Jumper1", "Jumper2", "Jumper3"}
-- A slain jumper takes no GetPlayer, WaitGetPlayer or BuddyDead (MM9.receives); a wait it took still ends.
-- Jumper.inc :JumperGetPlayer (LoopAnim LyingDown while it rises, then :JumpAtTarget LoopAnim JumpingDown
-- until it lands): the two clips in turn, held in place meanwhile (the leap's arc is not carried);
-- map var JumperLands<k>: the tick it is free (a load frees it at once). Freed, it goes for the party
-- (JumpAtTarget's GetPlayer): on the cliff top it seldom sees the party below, and one left waiting there
-- stood on it for good (Jumper3 in the user's save, 2026-11-11); a load sets the free ones on it again.
local JUMP_TICKS = 5
local function jumpNow(k)
    if var("JumperOut" .. k) == 1 then return end
    set("JumperOut" .. k, 1); set("JumperDue" .. k, 0)
    show(JUMPERS[k], true)
    evt.SetActorImmobile(JUMPERS[k], true)
    evt.PlayActorClip(JUMPERS[k], {"lying_down", "jumping_down"}, false)
    set("JumperLands" .. k, var("Tick") + JUMP_TICKS)
end
local function jumperLands(k)
    set("JumperLands" .. k, 0)
    evt.SetActorImmobile(JUMPERS[k], false)
    if MM9.actorAlive(JUMPERS[k]) then evt.SetActorTarget(JUMPERS[k], "party") end
end
local function jumperTick(tick)
    if var("JumpersSprung") == 0 then
        local x, y, z = evt.GetPartyPosition()
        if x < 356 or x > 1252 or y < -736 or y > -352 or z < 3054 or z > 3374 then return end
        set("JumpersSprung", 1)
        for k = 1, #JUMPERS do
            if var("JumperOut" .. k) == 0 and MM9.receives("thjorgard", JUMPER_NAMES[k], k == 1 and "GetPlayer" or "WaitGetPlayer", JUMPERS[k]) then
                set("JumperDue" .. k, tick + rnd(JUMPER_WAIT[k][1], JUMPER_WAIT[k][2]))
            end
        end
    end
    for k = 1, #JUMPERS do
        local due = var("JumperDue" .. k)
        if due > 0 and tick >= due then jumpNow(k) end
        local lands = var("JumperLands" .. k)
        if lands > 0 and tick >= lands then jumperLands(k) end
    end
end
handlers[304] = function(context)   -- a jumper's DeathTriggerTarget: BuddyDead
    local buddy = context.actorIndex == JUMPERS[1] and 3 or context.actorIndex == JUMPERS[2] and 4 or nil
    if buddy ~= nil and MM9.receives("thjorgard", JUMPER_NAMES[buddy], "BuddyDead", JUMPERS[buddy]) then jumpNow(buddy) end
end

-- JumperWarningTrigger0 (a plain touch Trigger, ActivationCount 1, no targets): its ActivationSound
-- (Sounds\Events\rubble.wav, SoundRadius 600: the party is inside it) once, when the party walks in.
local function warningTick()
    if var("RubbleWarned") == 1 then return end
    local x, y, z = evt.GetPartyPosition()
    if x < 1002 or x > 2356 or y < 2695 or y > 3025 or z + 170 < 2521 or z > 2777 then return end
    set("RubbleWarned", 1)
    evt.PlaySoundName("events/rubble.wav", 0, 0, 0)
end

-- Thorgard_actor.scr :CheckDisable: MagreebBaby0, Jim, Dean, Walter and the Dummies are hidden while the
-- Scholar promotion waits for its Magreeb (key 201 without 202); the adult Magreeb (Scholarpromo.scr) is the
-- one to find then. :MagreebAttackCheck: once a load, the baby within 1 800 units of the party gives key 202
-- (its leap from the water and the bandits' chase are the monster AI's). Scholarpromo.scr :RunAway: the
-- adult on sighting the party (its SightDistance) or hurt (OnDamage; here slain) gives key 202 with the quest
-- sound during the quest and leaves for good (map var MagreebGone). Only once the quest is taken (201): MM9's
-- ran off before it too, and the journal's Thjorgard Magreeb was then gone (2026-11-08).
local function magreebWaits() return has(201) and not has(202) end
local AMBUSH = {4, 9, 10, 11, 12, 13}
local function magreebTick()
    if var("MagreebSeen") == 0 and not magreebWaits() and evt.IsMapActorWithinPartyDistance(4, 4608) then
        set("MagreebSeen", 1); MM9.giveKey(202)
    end
    -- :RunAway is its OnFoundPlayer / OnDamage
    if var("MagreebGone") == 0 and has(201) then
        if not MM9.actorAlive(16) then
            if magreebWaits() then MM9.giveKey(202); quest() end
            set("MagreebGone", 1)
        elseif evt.IsMapActorWithinPartyDistance(16, 1536) then
            if magreebWaits() then MM9.giveKey(202); quest() end
            set("MagreebGone", 1); MM9.removeActor(16)
        end
    end
end

-- The games' half-second tick (countdowns, the rival boats, the switch's release) and the polls.
handlers[300] = function()
    local tick = var("Tick") % 1000000 + 1
    set("Tick", tick)
    if var("MMSwitch") == 1 then set("MMSwitch", 0); evt.SetDoorState(3, DoorAction.Close) end
    boatTick(tick)
    robberTick()
    jumperTick(tick)
    warningTick()
    if tick % 2 == 0 then magreebTick() end
    evt.StartTimer(300, seconds(0.5))
end

-- TrainingEnter.scr (ScriptObject1) :OnBreak: breaking the training hall's wall (DestructableBrush7) gives
-- key 301, +5 Might and +5 Intellect (GiveAttribute 0 5 1, 1 5 1: the active member), 20000
-- experience and the quest sound, once (the Training Hall's own end gives the same).
handlers[370] = function()
    set("Mm9ExitDisabled486", 0)   -- ExitTrigger3 on (tomneededatrigger1 "on", :Init)
    set("Mm9ExitDisabled114", 0)   -- ExitTrigger6 on (tomneededatrigger1 "on", :Init)
    set("HintOff23056", 1)   -- PerceptionBrush6 off (tomneededatrigger1, dungeon/perception.py)
    if MM9.hasKey(301) == 1 then return end
    MM9.giveKey(301)
    AddValue(BaseMight, 5)
    AddValue(BaseIntellect, 5)
    MM9.giveExperience(18500) -- MM9 GiveExp 20000, mm9_quest_xp_profile.yml
    MM9.playSound("sounds/events/quest.wav")
end

handlers.regionLoad = function()
    stReset()   -- StonesGame.scr :InitStonesGame
    mmNew()   -- Mastermind.scr :InitMastermind
    for i = 1, 4 do set("MMPick" .. i, 0); mmPaint(i, -1) end
    set("MMColor", 0); if var("MMSwitch") == 1 then set("MMSwitch", 0); evt.SetDoorState(3, DoorAction.Close) end
    set("BoatState", 0)   -- RacingBoat.scr :InitRacingBoat (a race does not survive a load)
    set("BellStage", 0)   -- DingTheBell.scr :Main
    honkReset()   -- Whack-a-Honky.scr :Main, :ResetPOS
    set("WrestlerCowerUntil", 0)   -- the cower is not saved
    if var("KensOut") == 0 then for _, a in ipairs(KENS) do show(a, false) end end   -- :SetupKen
    for k = 1, #JUMPERS do if var("JumperOut" .. k) == 0 then show(JUMPERS[k], false) end end   -- :SetupJumper
    for k = 1, #JUMPERS do if var("JumperOut" .. k) == 1 then jumperLands(k) end end
    for _, a in ipairs(AMBUSH) do show(a, not magreebWaits()) end   -- :CheckDisable
    set("MagreebSeen", 0)
    if var("MagreebGone") == 1 then MM9.removeActor(16) end
    evt.StartTimer(300, seconds(0.5))
    set("Mm9ExitDisabled486", has(301) and 0 or 1)   -- ExitTrigger3 (StartOn 0)
    set("Mm9ExitDisabled114", has(301) and 0 or 1)   -- ExitTrigger6 (StartOn 0)
end

handlers[1] = function()
    for k = 1024, 1033 do MM9.takeKey(k) end
    MM9.giveKey(1025)
    shopHours()
    if handlers.regionLoad then handlers.regionLoad() end
end

-- MM9's greeting voices (dungeon/voices.py): a click on these people plays their GreetingSound or the
-- voice their script's :OnUse plays, then opens their dialogue (or runs the map's own click).
handlers[53001] = function() MM9.playSound("voices/npc/npc_018.wav"); MM9.openRude(18) end   -- JohnGoodman

-- MM9's bonus props (dungeon/objects.py bonus_lines; the use of each class, object.lto): wells, cauldrons,
-- cook pots and clovers.
handlers[30699] = function() MM9.useCauldron(699, 0, 5) end   -- obj_Cauldron0 (Cauldron)

-- MM9's breaking destructibles: an urn's SpawnObject TreasureBag drops (evt.SpawnLootContainer).
handlers[30480] = function() set("HintOff23058", 1); evt.SetFacetBit(23058, FacetBits.Invisible, true) end   -- DestructableBrush8
handlers[30481] = function() set("HintOff23060", 1); evt.SetFacetBit(23060, FacetBits.Invisible, true) end   -- DestructableBrush9
handlers[30482] = function() set("HintOff23061", 1); evt.SetFacetBit(23061, FacetBits.Invisible, true) end   -- DestructableBrush10
handlers[30483] = function() set("HintOff23057", 1); evt.SetFacetBit(23057, FacetBits.Invisible, true) end   -- DestructableBrush11
handlers[30484] = function() set("HintOff23059", 1); evt.SetFacetBit(23059, FacetBits.Invisible, true) end   -- DestructableBrush12
handlers[30485] = function() set("HintOff23055", 1); evt.SetFacetBit(23055, FacetBits.Invisible, true) end   -- DestructableBrush13

-- MM9's PerceptionBrushes (dungeon/perception.py): the red glow shows to a party whose Perception reaches the
-- brush's PerceptionValue, checked on load and every 3 s; map Lua turns one off for good with
-- set("HintOff<cog>", 1) (MM9's Off message to the brush).
local HINTS = {[23050] = 1, [23051] = 1, [23052] = 1, [23053] = 1, [23054] = 1, [23055] = 1, [23056] = 1, [23057] = 1, [23058] = 1, [23059] = 1, [23060] = 1, [23061] = 1}
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
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(106, "Locked door", handlers[106], "Door")
RegisterMapTimerEvent(260, seconds(3), handlers[260], "Shop hours", "", seconds(3))
RegisterEvent(390, "Stat stone", handlers[390], "Touch")
RegisterEvent(50673, "The Huckster", handlers[50673])
RegisterEvent(600, "Stone", handlers[600], "Stone")
RegisterEvent(601, "Stone", handlers[601], "Stone")
RegisterEvent(602, "Stone", handlers[602], "Stone")
RegisterEvent(603, "Stone", handlers[603], "Stone")
RegisterEvent(604, "Stone", handlers[604], "Stone")
RegisterEvent(605, "Stone", handlers[605], "Stone")
RegisterEvent(606, "Stone", handlers[606], "Stone")
RegisterEvent(607, "Stone", handlers[607], "Stone")
RegisterEvent(608, "Stone", handlers[608], "Stone")
RegisterEvent(609, "Stone", handlers[609], "Stone")
RegisterEvent(610, "Stone", handlers[610], "Stone")
RegisterEvent(611, "Stone", handlers[611], "Stone")
RegisterEvent(612, "Stone", handlers[612], "Stone")
RegisterEvent(613, "Stone", handlers[613], "Stone")
RegisterEvent(614, "Stone", handlers[614], "Stone")
RegisterEvent(615, "Stone", handlers[615], "Stone")
RegisterEvent(616, "Stone", handlers[616], "Stone")
RegisterEvent(617, "Stone", handlers[617], "Stone")
RegisterEvent(618, "Stone", handlers[618], "Stone")
RegisterEvent(619, "Stone", handlers[619], "Stone")
RegisterEvent(620, "Stone", handlers[620], "Stone")
RegisterEvent(621, "Stone", handlers[621], "Stone")
RegisterEvent(622, "Stone", handlers[622], "Stone")
RegisterEvent(623, "Stone", handlers[623], "Stone")
RegisterEvent(624, "Stone", handlers[624], "Stone")
RegisterEvent(625, "Stone", handlers[625], "Stone")
RegisterEvent(626, "Stone", handlers[626], "Stone")
RegisterEvent(627, "Stone", handlers[627], "Stone")
RegisterEvent(628, "Stone", handlers[628], "Stone")
RegisterEvent(629, "Stone", handlers[629], "Stone")
RegisterEvent(630, "Stone", handlers[630], "Stone")
RegisterEvent(631, "Stone", handlers[631], "Stone")
RegisterEvent(632, "Stone", handlers[632], "Stone")
RegisterEvent(633, "Stone", handlers[633], "Stone")
RegisterEvent(634, "Stone", handlers[634], "Stone")
RegisterEvent(635, "Stone", handlers[635], "Stone")
RegisterEvent(53593, "Stones player", handlers[53593])
RegisterEvent(50593, "Stones player", handlers[50593])
RegisterEvent(636, "Rune stone", handlers[636], "Stone")
RegisterEvent(637, "Rune stone", handlers[637], "Stone")
RegisterEvent(638, "Rune stone", handlers[638], "Stone")
RegisterEvent(639, "Rune stone", handlers[639], "Stone")
RegisterEvent(640, "Rune stone", handlers[640], "Stone")
RegisterEvent(641, "Rune stone", handlers[641], "Stone")
RegisterEvent(642, "Rune stone", handlers[642], "Stone")
RegisterEvent(643, "Rune stone", handlers[643], "Stone")
RegisterEvent(644, "Rune stone", handlers[644], "Stone")
RegisterEvent(103, "Switch", handlers[103], "Switch")
RegisterEvent(53669, "Boat judge", handlers[53669])
RegisterEvent(50669, "Boat race", handlers[50669])
RegisterEvent(645, "Toy boat", handlers[645], "Boat")
RegisterEvent(102, "Bell strike plate", handlers[102], "Strike")
RegisterMapTimerEvent(301, seconds(3), handlers[301], "Bell", "", seconds(3))
RegisterEvent(101, "Bell weight", handlers[101])
RegisterEvent(646, "Goose", handlers[646], "Goose")
RegisterEvent(647, "Goose", handlers[647], "Goose")
RegisterEvent(648, "Goose", handlers[648], "Goose")
RegisterEvent(649, "Goose", handlers[649], "Goose")
RegisterEvent(104, "Whack-a-honky lever", handlers[104], "Lever")
RegisterMapTimerEvent(302, seconds(3), handlers[302], "Whack-a-honky", "", seconds(3))
RegisterMapTimerEvent(303, seconds(3), handlers[303], "Whack-a-honky end", "", seconds(3))
RegisterEvent(53117, "Arm wrestler", handlers[53117])
RegisterMapTimerEvent(300, seconds(3), handlers[300], "Fair games", "", seconds(3))
RegisterEvent(370, "Training hall wall broken", handlers[370])
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(53001, "Trollfin the Sailcutter", handlers[53001])
RegisterEvent(30699, "Cauldron", handlers[30699], "Drink")
RegisterEvent(30480, "DestructableBrush8", handlers[30480])
RegisterEvent(30481, "DestructableBrush9", handlers[30481])
RegisterEvent(30482, "DestructableBrush10", handlers[30482])
RegisterEvent(30483, "DestructableBrush11", handlers[30483])
RegisterEvent(30484, "DestructableBrush12", handlers[30484])
RegisterEvent(30485, "DestructableBrush13", handlers[30485])
RegisterMapTimerEvent(901, seconds(3), handlers[901], "Perception hints", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
RegisterMonsterKilledHook(304, "Jumper killed", handlers[304])
