-- The Arena, MM9 rework (level_generation/projects/mm9r_thearena/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {RotatingDoor0 = 1, RotatingDoor1 = 2, RotatingDoor2 = 5, RotatingDoor3 = 6, RotatingDoor4 = 3, RotatingDoor5 = 4}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1}, onLeave = {}, timers = {}, openedChestIds = {}})

-- Chests (MM9 TreasureChest objects; loot records in the scene).

local NAMES = {}
local function hasKey(k) return MM9.hasKey(k) == 1 end

-- A scheduler on the 0.25 s poll (MM9's Wait): after(seconds, fn).
local tick, tasks = 0, {}
local function after(s, fn) table.insert(tasks, {at = tick + math.max(1, math.floor(s * 4 + 0.5)), fn = fn}) end

-- Markers (native, on the floor) and the PlayerInTheHouse box.
local P = {Marker0 = {1720, 0, 1}, Marker1 = {-1761, 0, 1}, Marker2 = {0, 0, 1}, Marker3 = {-225, -3318, 124}, Marker4 = {-225, -3564, 124}, Marker5 = {614, -3441, 1}, Marker6 = {0, -2294, 1}, Soldier0 = {-205, 1802, 493}, Soldier1 = {205, 1802, 493}, Sven0 = {0, 1597, 513}}
local HOUSE = {{-118, -1390, 3}, {138, -1134, 259}}
local GATE_EAST, GATE_WEST = {1331, 0, 1}, {-1331, 0, 1}   -- the pens' mouths
local function inBox(b, x, y, z) return x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] and z >= b[1][3] - 40 and z <= b[2][3] + 40 end

-- Doors: MM9's arena double door (RotatingDoor0/1), the west pen (RotatingDoor2/3) and the east pen
-- (RotatingDoor4/5). Arena.scr :LockDoors / :UnLockDoors and ArenaCreature.scr lock them (map variables).
local LEAVES = {ArenaDoor = {"RotatingDoor0", "RotatingDoor1"}, WestPen = {"RotatingDoor2", "RotatingDoor3"}, EastPen = {"RotatingDoor4", "RotatingDoor5"}}
local function door(group, action) for _, leaf in ipairs(LEAVES[group]) do evt.SetDoorState(DOORS[leaf], action) end end
local function lock(group, on) set("Lock" .. group, on and 1 or 0) end
local function lockDoors() door("ArenaDoor", DoorAction.Close); lock("ArenaDoor", true) end   -- Arena.scr :LockDoors
local function unlockDoors() lock("ArenaDoor", false) end                                          -- :UnLockDoors
local svenWalk
local function clickDoor(group)
    if var("Lock" .. group) == 1 then evt.StatusText("The door is locked.") return end
    door(group, DoorAction.Trigger)
    if group == "ArenaDoor" then svenWalk() end            -- RotatingDoor0's OpenTrigger: SvenArena Walk
end
handlers[100] = function() clickDoor("ArenaDoor") end
handlers[101] = function() clickDoor("WestPen") end
handlers[102] = function() clickDoor("EastPen") end

-- MM9's arena table (PICKMON.inc :PickMonster): a level picks a group, the group one of its monsters at random
-- {row, MM9 level, class}; false where the class has no runtime row (the clan soldiers, the poor town guards:
-- such a draw is drawn again, as MM9 draws again a monster outside the level range).
local RANGES = {{1, 4, 1}, {5, 8, 2}, {9, 11, 3}, {12, 14, 4}, {15, 16, 5}, {17, 19, 6}, {20, 21, 7}, {22, 23, 8}, {24, 26, 9}, {27, 29, 10}, {30, 32, 11}, {33, 33, 12}, {34, 37, 13}, {38, 39, 14}, {40, 43, 15}, {44, 47, 16}, {48, 53, 17}, {54, 58, 18}, {59, 64, 19}, {65, 74, 20}, {76, 999, 21}}
local GROUPS = {
    [1] = {{9075, 2, "DragonFlyMite"}, {9078, 4, "Imply"}, {9076, 3, "DragonFly"}, {9183, 4, "Skeletoid"}},
    [2] = {{9077, 5, "FireDragonFly"}, {9081, 6, "NagateHatchling"}, {9079, 6, "Imp"}, {9184, 8, "BoneThrasher"}, {9090, 8, "FieldThrall"}, {9099, 8, "Cutpurse"}},
    [3] = {{9180, 9, "Rotter"}, {9082, 10, "Nagate"}, {9080, 10, "ImpElder"}, {9096, 10, "Troglodyte"}, {9120, 10, "DwarvenGuard"}},
    [4] = {{9096, 12, "Troglodyte"}, {9091, 12, "Thrall"}, {9181, 13, "Dripper"}, {9102, 14, "HalfOrcRecruit"}, {9100, 14, "Burgler"}},
    [5] = {{9171, 15, "Gezzamptling"}, {9150, 15, "Basilisk"}, {9135, 16, "Skeleton"}, {9135, 16, "Skeleton"}},
    [6] = {{9097, 17, "TroglodyteWren"}, {9182, 17, "Zombie"}, {9092, 18, "ThrallMaster"}, {9198, 18, "Bigfoot"}},
    [7] = {false, {9172, 20, "Gezzampt"}, false, {9111, 20, "Guard"}, {9114, 20, "GreyWolf"}, {9121, 20, "DwarvenSoldier"}, {9144, 20, "CanopicMummy"}, {9174, 20, "Ghast"}, {9195, 20, "Bloodsucker"}},
    [8] = {{9165, 22, "Trellborg"}, {9101, 22, "Bandit"}, {9277, 22, "Magreeb"}, {9136, 22, "SkeletonWarrior"}, {9151, 23, "FibraseBasilisk"}},
    [9] = {{9098, 24, "TroglodyteGnoll"}, {9103, 24, "HalfOrcSoldier"}, {9098, 24, "TroglodyteGnoll"}},
    [10] = {{9159, 27, "WingedOddity"}, {9175, 27, "Ghoul"}, {9112, 28, "GuardSegeant"}, {9199, 28, "Sasquatch"}, {9199, 28, "Sasquatch"}, {9173, 28, "GezzamptElder"}},
    [11] = {{9115, 30, "RedWolf"}, {9145, 30, "EmbalmedMummy"}, {9122, 30, "DwarvenCommander"}, {9152, 30, "KingBasilisk"}, {9152, 30, "KingBasilisk"}},
    [12] = {{9137, 33, "SkeletonMaster"}, {9277, 33, "Magreeb2"}, {9196, 33, "Annelid"}, {9113, 33, "GuardCaptain"}, {9113, 33, "GuardCaptain"}, {9277, 33, "Magreeb2"}},
    [13] = {false, {9162, 35, "Fright"}, {9104, 35, "HalfOrcCaptain"}, {9104, 35, "HalfOrcCaptain"}, {9166, 35, "KinTrellborg"}},
    [14] = {{9176, 38, "Revenant"}, {9200, 38, "Yeti"}, {9147, 39, "Dagrell"}, {9160, 39, "WingedMutant"}},
    [15] = {{9189, 40, "LizardOrc"}, {9116, 40, "BlackWolf"}, {9146, 40, "PetrifiedMummy"}, {9189, 40, "LizardOrc"}},
    [16] = {false, {9207, 45, "Lich"}},
    [17] = {{9197, 48, "Vampir"}, {9167, 50, "AncientTrellborg"}, {9161, 51, "WingedAberration"}},
    [18] = {false, {9163, 55, "Dread"}, {9208, 55, "PowerLich"}},
    [19] = {{9148, 59, "VenomousDagrell"}, {9190, 60, "LizardOrcWarrior"}},
    [20] = {{9164, 65, "Terror"}, {9209, 65, "LichKing"}},
    [21] = {{9149, 79, "SpectreDagrell"}, {9191, 80, "LizardOrcMage"}},
}
local function pickMonster(level)
    for _, r in ipairs(RANGES) do
        if level >= r[1] and level <= r[2] then local g = GROUPS[r[3]] return g[math.random(1, #g)] end
    end
    return nil
end

-- ArenaFight.scr :GetCharLevel: the mean level of the party.
local function memberLevel(i)
    evt.ForPlayer(i)
    local lo, hi = 1, 400
    while lo < hi do
        local mid = math.floor((lo + hi + 1) / 2)
        if evt.Cmp(VarTag.BaseLevel, mid) then lo = mid else hi = mid - 1 end
    end
    return lo
end
local function partyLevel()
    local n, sum = math.max(1, evt.GetPartyMemberCount()), 0
    for i = 0, n - 1 do sum = sum + memberLevel(i) end
    evt.ForPlayer(Players.Current)
    return math.max(1, math.floor(sum / n + 0.5))
end

-- Fresh monster groups (fights and bouts); a reload hides what a former visit left standing.
local function newGroup() set("Serial", var("Serial") + 1) return 100 + var("Serial") end
local function spawn(row, at, group, hostile)
    local hp = (70 + math.random(0, 80)) / 100                 -- :Startup / :Init: HitPoints x 0.7-1.5
    return evt.SummonMonstersById({monster = row, x = at[1], y = at[2], z = at[3], radius = 48, count = 1,
        group = group, hostile = hostile, loot = false, hpScale = hp})   -- GaveTreasure TRUE: no treasure
end

local function reset() for _, k in ipairs({1004, 1005, 1006, 1007, 1008, 1010, 1011, 1012, 1013, 1014, 1015, 1016, 1017, 1018, 1019}) do MM9.takeKey(k) end end   -- Arena.scr :Reset

-- ---- Fights against the party (ArenaFight.scr :OnPage, :OnSquire, :OnKnight, :OnLord) -------------------------
local FIGHTS = {[1] = {0.8, 1.3, 2, 20}, [2] = {0.8, 1.5, 3, 30}, [3] = {1.0, 1.7, 4, 50}, [4] = {1.0, 2.5, 5, 100}}
local function prepareFight(difficulty)
    local f, level = FIGHTS[difficulty], partyLevel()
    local low, high = math.floor(level * f[1]), math.floor(level * f[2])
    if level > 89 then high = 89 end
    if level < 4 then high = 4 end
    if high < low then high = low end
    local count = math.random(1, f[3])
    set("Reward", count * level * f[4])
    set("FightCount", count)
    for i = 1, count do
        local pick, best = nil, nil
        for attempt = 1, 400 do                         -- MM9: Goto OnPage until a monster in the range
            local m = pickMonster(math.random(math.max(0, low), math.max(0, high)))
            if m then
                if m[2] >= low and m[2] <= high then pick = m break end
                local miss = math.max(low - m[2], m[2] - high)
                if best == nil or miss < best[1] then best = {miss, m} end
            end
        end
        pick = pick or best[2]                          -- no monster of the range at all: the nearest
        set("FightMonster" .. i, pick[1])
    end
    if difficulty == 4 and hasKey(214) then set("Lord", 1) end   -- ArenaFight :OnLord -> Arena :OnLord
    MM9.giveKey(1011)                                -- ArenaFightPlayer.scr :Main
    set("Waiting", 1)                                     -- SetConsoleNumVar WaitingForPlayer, TRUE
end
-- :OnPlayerInTheHouse: the party past the arena doors shuts them behind it; the opponents come out of the pens
-- (ArenaFightPlayer.scr :Startup: the first at Marker0 in the east pen, the others at Marker1 in the west).
local function startFight()
    set("Waiting", 0)
    lockDoors()
    local group = newGroup()
    set("FightGroup", group)
    for i = 1, var("FightCount") do
        spawn(var("FightMonster" .. i), i == 1 and P.Marker0 or P.Marker1, group, true)
    end
    door("EastPen", DoorAction.Open); door("WestPen", DoorAction.Open)
end
local function fightDead()   -- ArenaFight.scr :OnDead: all down -> key 1020, the arena door unlocked
    local group = var("FightGroup")
    if group == 0 or not evt.CheckMonstersKilled(ActorKillCheck.Group, group, 0, true) then return end
    set("FightGroup", 0)
    MM9.giveKey(1020)
    unlockDoors()
    evt.PlaySoundName("ambient/people/crowdnoise-cheer01.wav", 0, 0, 0)
end
local function fightWin()    -- Arena.scr :FightWin
    if var("Lord") == 1 then
        MM9.giveKey(217)                      -- the third labor: no purse (MM9)
        MM9.playSound("sounds/events/quest.wav")
        set("Lord", 0)
    else
        MM9.giveGold(var("Reward"))
    end
    MM9.giveKey(1009); MM9.takeKey(1020)
end

-- ---- Bouts to watch and bet on (Arena.scr :pick, :Init, :OnWatch, :OnBet, :OnMonsterDead) ------------------
local function pickPair()   -- Arena.scr :pick: monster A at a random level, B within 4 levels of it
    local a, b, la
    repeat la = math.random(1, 89) a = pickMonster(la) until a
    local low = math.max(1, la - 4)
    local high = math.min(89, low + 8)
    low = high - 8
    repeat
        local lb = math.random(low, high)
        if lb == la then lb = la - 1 if lb < 1 then lb = la + 1 end end
        b = pickMonster(lb)
    until b
    set("BoutA", a[1]); set("BoutLevelA", a[2]); set("BoutB", b[1]); set("BoutLevelB", b[2])
    NAMES.A, NAMES.B = a[3], b[3]
end
local function initBout()   -- Arena.scr :Init: three bouts a visit, then 'no more fights today'
    if var("Bouts") >= 3 then MM9.giveKey(1009) return end
    set("Bouts", var("Bouts") + 1)
    pickPair()
end
local function watch()      -- Arena.scr :OnWatch: A from the east pen, B from the west; the crowd cheers
    local ga, gb = newGroup(), newGroup()
    set("BoutGroupA", ga); set("BoutGroupB", gb); set("BoutDead", 0)
    local a, b = var("BoutA"), var("BoutB")
    evt.SetMonsterRelation(a, b, 2); evt.SetMonsterRelation(b, a, 2)   -- :OnArrive HateAll (ArenaCreature :OnHate)
    MM9.giveKey(1011)                                     -- ArenaCreature.scr :Main
    lockDoors()
    evt.PlaySoundName("ambient/people/crowdnoise-cheer01.wav", 0, 0, 0)
    door("WestPen", DoorAction.Open); door("EastPen", DoorAction.Open)   -- :Init: the pens open
    -- MM9 runs both to Marker2 and sets them on each other there. Native actors do not walk to a marker and do
    -- not wake in a pen out of the party's room: each steps out of its open pen (spawned at the gate on the
    -- arena side), where the two see each other across the floor.
    after(3, function()
        spawn(a, GATE_EAST, ga, false)                          -- AddFriend Player: not hostile to the party
        spawn(b, GATE_WEST, gb, false)
    end)
end
local function boutOver()   -- ArenaVictory.scr :RunAway, :Delete: the winner leaves, the next pair is drawn
    MM9.takeKey(1010); MM9.takeKey(1011); MM9.takeKey(1017)
    for _, g in ipairs({var("BoutGroupA"), var("BoutGroupB")}) do
        if g ~= 0 then evt.SetMonGroupBit(g, MonsterBits.Invisible, true) end
    end
    set("BoutGroupA", 0); set("BoutGroupB", 0)
    door("WestPen", DoorAction.Close); door("EastPen", DoorAction.Close)
    unlockDoors()
    initBout()
end
local function boutDead()   -- Arena.scr :OnMonsterDead
    local ga, gb = var("BoutGroupA"), var("BoutGroupB")
    if ga == 0 then return end
    local deadA = evt.CheckMonstersKilled(ActorKillCheck.Group, ga, 0, true)
    local deadB = evt.CheckMonstersKilled(ActorKillCheck.Group, gb, 0, true)
    if deadA and deadB then                                      -- both of them: reset, the next pair
        reset(); set("BoutGroupA", 0); set("BoutGroupB", 0); initBout(); unlockDoors()
        return
    end
    if (deadA or deadB) and var("BoutDead") == 0 then
        set("BoutDead", 1)
        MM9.takeKey(1019)
        local winner = deadA and "B" or "A"
        if hasKey(1017) then                               -- :OnMonsterAWin / :OnMonsterBWin
            if var("BetOn") == (winner == "A" and 1 or 2) then
                MM9.giveKey(1018)
                evt.StatusText("You won your bet! The Arena Master has your winnings.")
            else
                evt.StatusText("You lost your bet.")
            end
        end
        evt.PlaySoundName("ambient/people/crowdnoise-cheer01.wav", 0, 0, 0)
        after(20, boutOver)                                       -- Wait 20 -> :BeVictorious
    end
end
local function bet()        -- Arena.scr :OnBet2: the wager is taken, or 'no gold' and the talk is undone
    lockDoors()
    for key, amount in pairs({[1012] = 50, [1013] = 100, [1014] = 250, [1015] = 500, [1016] = 1000}) do
        if hasKey(key) then
            if MM9.hasGold(amount) == 0 then
                evt.StatusText("You do not have enough gold.")    -- NoGold.inc
                reset(); unlockDoors()
            else
                MM9.takeKey(key); MM9.takeGold(amount); set("BetAmount", amount)
            end
            return
        end
    end
end
local function slip(which)  -- ArenaMini.scr :OnUse, Arena.scr :OnMonsterA / :OnMonsterB
    local mine, other = var("BoutLevel" .. which), var("BoutLevel" .. (which == "A" and "B" or "A"))
    if not hasKey(1017) or hasKey(1019) then
        local name = tr(NAMES[which] or "?")
        if which == "A" then
            evt.StatusText(tr("Contestant from the east gate: {name} (level {level})", {name = name, level = mine}))
        else
            evt.StatusText(tr("Contestant from the west gate: {name} (level {level})", {name = name, level = mine}))
        end
        return
    end
    set("BetOn", which == "A" and 1 or 2)
    local d, amount = other - mine, var("BetAmount")
    if d < 0 then amount = math.floor(amount * 1.5) elseif d > 5 then amount = amount * 2 end   -- MM9's odds
    set("BetAmount", amount)
    MM9.giveKey(1019)
    evt.StatusText(tr("You bet on the {name}.", {name = NAMES[which] and tr(NAMES[which]) or tr("contestant")}))
    after(3, watch)                                               -- wait 1 3 Fight -> Arena :OnWatch
end
handlers[110] = function() slip("A") end
handlers[111] = function() slip("B") end
local function giveWin()    -- Arena.scr :GiveWin
    MM9.takeKey(1018); MM9.takeKey(1019); reset()
    MM9.giveGold(var("BetAmount"))
end

-- The Arena Master (Arena.scr :OnRude, after RUDE 430): the keys his rows gave decide what happens.
handlers[50012] = function()
    if not hasKey(231) and hasKey(230) then reset() return end   -- Sven's day: no fights
    if hasKey(1018) then giveWin() return end
    if hasKey(1009) then return end
    if hasKey(1011) then if hasKey(1020) then fightWin() end return end
    if hasKey(1010) then watch() return end
    if hasKey(1017) then bet() return end
    for difficulty, key in ipairs({1004, 1005, 1006, 1007}) do   -- :FightCheck
        if hasKey(key) then prepareFight(difficulty); unlockDoors() return end
    end
end

-- ---- Jarl Sven's double and the assassin (SvenArena.scr, NPC245.scr) ----------------------------------------
-- With key 230 (Sven's plan) and without 231: opening the arena door brings Sven's double
-- and his two soldiers into the box (:OnWalk; MM9 walks them there), the crowd cheers (:OnWave), the east pen
-- opens and Byri the Scarred comes out to the middle (NPC245 :OnEnter), and the crowd boos (:Boo).
svenWalk = function()
    if hasKey(231) or not hasKey(230) or var("SvenWalked") == 1 then return end
    -- A dead or removed actor takes none of these messages (MM9.receives): the double's Walk, the soldiers' Guard
    -- (sent by his :OnWalk), Byri's enter (sent by their :OnStart waits, which fire even after a death).
    if not MM9.receives("thearena", "SvenArena", "Walk", 1) then return end
    set("SvenWalked", 1)
    evt.SetMapActorPosition(1, P.Sven0[1], P.Sven0[2], P.Sven0[3])
    evt.SetMonsterBit(1, MonsterBits.Invisible, false)
    if MM9.receives("thearena", "ClanSoldier0", "Guard", 2) then evt.SetMapActorPosition(2, P.Soldier0[1], P.Soldier0[2], P.Soldier0[3]); evt.SetMonsterBit(2, MonsterBits.Invisible, false) end
    if MM9.receives("thearena", "ClanSoldier1", "Guard", 3) then evt.SetMapActorPosition(3, P.Soldier1[1], P.Soldier1[2], P.Soldier1[3]); evt.SetMonsterBit(3, MonsterBits.Invisible, false) end
    evt.PlaySoundName("events/trumpets02.wav", 0, 0, 0)
    -- :OnArrive wait 2 :OnWave: the cheer and PlayAnim Bless (the soldiers' bodies, MM9's ClanSoldier too, have
    -- no Bless: only the double's plays)
    after(2, function()
        evt.PlaySoundName("ambient/people/crowdnoise-cheer01.wav", 0, 0, 0)
        if MM9.actorAlive(1) then evt.PlayActorClip(1, "bless", false) end
    end)
    local byriEnters = false
    after(4, function()
        door("EastPen", DoorAction.Open)
        byriEnters = MM9.receives("thearena", "CommonerHuman2MaleB0", "enter", 4)
        if byriEnters then evt.SetMonsterBit(4, MonsterBits.Invisible, false) end
    end)
    after(5, function() if byriEnters then evt.SetMapActorPosition(4, P.Marker2[1], P.Marker2[2], P.Marker2[3]) end end)
    after(6, function() evt.PlaySoundName("ambient/people/crowdnoise-cheer01.wav", 0, 0, 0) end)   -- :Boo
end
-- Byri (NPC245.scr :OnRude, :Run, :OnVanish): once he gave himself away (key 231), he opens the arena
-- door and runs off (Marker6, in the hall) and is gone.
handlers[50025] = function()
    if not hasKey(231) then return end
    after(2, function()
        lock("ArenaDoor", false); door("ArenaDoor", DoorAction.Open)
        evt.SetMapActorPosition(4, P.Marker6[1], P.Marker6[2], P.Marker6[3])
    end)
    after(4, function() evt.SetMonGroupBit(3, MonsterBits.Invisible, true) end)
end
-- Sven's double (SvenArena.scr :OnUse gives key 1034 before his talk, RUDE 428; :OnRude takes it).
handlers[53020] = function() MM9.giveKey(1034); MM9.openRude(428) end
handlers[50020] = function() MM9.takeKey(1034) end

-- A bout creature's DeathTrigger sends the Arena Master IDied (ArenaCreature.scr): a dead master takes none
-- (MM9.receives), so no winner, no bet paid, no next pair.
handlers[130] = function(context)
    fightDead()
    if var("BoutGroupA") ~= 0 and MM9.receives("thearena", "ShopkeeperElfMaleB0", "IDied", 0) then boutDead() end
end

-- The poll: PlayerInTheHouse (a touch box, polled as MM9's fire on any part of the party) and the waits.
local inHouse = false
handlers[120] = function()
    evt.StartTimer(120, seconds(0.25))
    tick = tick + 1
    local x, y, z = evt.GetPartyPosition()
    local now = inBox(HOUSE, x, y, z)
    if now and not inHouse and var("Waiting") == 1 then startFight() end
    inHouse = now
    local due = {}
    for i = #tasks, 1, -1 do if tasks[i].at <= tick then table.insert(due, 1, tasks[i].fn) table.remove(tasks, i) end end
    for _, fn in ipairs(due) do fn() end
end

-- Map load (Arena.scr :Main, :OnPostStartWorld; ArenaFight.scr :Main; SvenArena.scr / NPC245.scr :Init): every
-- visit starts afresh: the day's keys go, three new bouts, Sven's party and Byri hidden, what an earlier visit
-- left standing in the arena is gone, the doors unlocked.
handlers[1] = function()
    MM9.takeKey(1009); reset(); MM9.takeKey(1034)
    for g = 101, 100 + var("Serial") do evt.SetMonGroupBit(g, MonsterBits.Invisible, true) end
    for _, i in ipairs({1, 2, 3, 4}) do evt.SetMonsterBit(i, MonsterBits.Invisible, true) end
    for _, name in ipairs({"Waiting", "FightGroup", "BoutGroupA", "BoutGroupB", "Bouts", "Lord", "SvenWalked", "BetAmount", "BetOn"}) do set(name, 0) end
    for _, g in ipairs({"ArenaDoor", "WestPen", "EastPen"}) do lock(g, false) end
    initBout()
    evt.StartTimer(120, seconds(0.25))
end

-- MM9's greeting voices (dungeon/voices.py): a click on these people plays their GreetingSound or the
-- voice their script's :OnUse plays, then opens their dialogue (or runs the map's own click).
handlers[53025] = function() MM9.playSound("voices/npc/npc_245.wav"); MM9.openRude(245) end   -- CommonerHuman2MaleB0


RegisterEvent(100, "Door", handlers[100], "Door")
RegisterEvent(101, "Door", handlers[101], "Door")
RegisterEvent(102, "Door", handlers[102], "Door")
RegisterEvent(110, "Betting slip", handlers[110], "Betting slip")
RegisterEvent(111, "Betting slip", handlers[111], "Betting slip")
RegisterEvent(50012, "Arena Master", handlers[50012])
RegisterEvent(50025, "Byri the Scarred", handlers[50025])
RegisterEvent(53020, "Sven Forkbeard", handlers[53020])
RegisterEvent(50020, "Sven Forkbeard", handlers[50020])
RegisterEvent(130, "Arena kills", handlers[130])
RegisterMapTimerEvent(120, seconds(3), handlers[120], "Poll", "", seconds(3))
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(53025, "Byri the Scarred", handlers[53025])
RegisterMonsterKilledHook(130, "Arena kills", handlers[130])
