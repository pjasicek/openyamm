-- Mountain Pass, MM9 rework (level_generation/projects/mm9r_mountainpass/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}}})

-- Doors: each MM9 door group opens and closes on a click.

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest0

local function has(k) return MM9.hasKey(k) == 1 end
local function quest() MM9.playSound("sounds/events/quest.wav") end
local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; if gold > 0 then MM9.giveGold(gold) end; quest() end

-- MountainPass.scr :OnStep (Trigger0, Trigger1 send "Use" once each) and :OnAward on the second.
local PASS_TRIGGERS = {{name = "Trigger0", low = {15461, -5163, -328}, high = {17427, -4508, 983}}, {name = "Trigger1", low = {-11900, 12368, 0}, high = {-11245, 14334, 1311}}}
-- A volume grown by the party's radius (its feet may stand 170 below it), and whether the party's path since the
-- last poll (a straight segment) passes through it.
local function passBounds(b)
    return {b.low[1] - 37, b.low[2] - 37, b.low[3] - 170}, {b.high[1] + 37, b.high[2] + 37, b.high[3] + 37}
end
local function crossesPassBox(b, from, to)
    local low, high = passBounds(b)
    local t0, t1 = 0, 1
    for k = 1, 3 do
        local d = to[k] - from[k]
        if d == 0 then
            if from[k] < low[k] or from[k] > high[k] then return false end
        else
            local ta, tb = (low[k] - from[k]) / d, (high[k] - from[k]) / d
            if ta > tb then ta, tb = tb, ta end
            if ta > t0 then t0 = ta end
            if tb < t1 then t1 = tb end
            if t0 > t1 then return false end
        end
    end
    return true
end
local function passAward()
    if has(80) or has(176) then return end   -- once (MM9 paid key 176's branch again after key 80)
    local xp = 12500 -- MM9 GiveExp 14000, mm9_quest_xp_profile.yml
    if has(79) then reward(80, xp, 0) else reward(176, xp, 0) end
end
local lastPartyPos = nil   -- runtime: the party's position at the previous poll (none after a load)
handlers[600] = function()
    if has(80) or has(176) then return end
    local x, y, z = evt.GetPartyPosition()
    local here = {x, y, z}
    local from = lastPartyPos or here
    if (x - from[1]) ^ 2 + (y - from[2]) ^ 2 > 2048 ^ 2 then from = here end   -- a jump, not a run
    lastPartyPos = here
    for _, b in ipairs(PASS_TRIGGERS) do
        if var("Stepped" .. b.name) == 0 and crossesPassBox(b, from, here) then
            set("Stepped" .. b.name, 1)   -- the trigger turns itself off
            set("PassSteps", var("PassSteps") + 1)
            if var("PassSteps") == 2 then passAward() end
        end
    end
    -- cleared: every monster in the pass is dead
    if evt.CheckMonstersKilled(ActorKillCheck.Hostile, 0, 0, false) then passAward() end
end

-- MP_Imp.scr (Imply0, the lookout): :Main waits 1 s, :OnStart walks it to ImpMarker1 and arms OnFoundTarget;
-- :TargetFound (it sees the party) plays wince1 (its Hit clip) and runs it to ImpMarker2, the imps' camp;
-- :StartAttack: help (the camp's imps take the party) and it fights (BaseInit). Map var ImpAlarm: it has seen
-- the party (afterwards it is an ordinary imp), 2 it called; walks are not saved: a load during its wince or
-- run calls the camp at once.
local IMP = 49
local IMP_MARKER1, IMP_MARKER2 = {-19232, 19759, 46}, {-16160, 17611, 105}
local IMP_CAMP = {42, 43, 44, 45, 46, 47, 48, 50}   -- within 1024 of ImpMarker2
local impPhase, impRun = 0, 0   -- runtime: 0 before :OnStart, 1 watching, 2 wincing (held), 3 running (ticks)
local function impHelp()   -- :StartAttack
    set("ImpAlarm", 2)
    if not MM9.actorAlive(IMP) then return end
    evt.SetActorImmobile(IMP, false)
    for _, a in ipairs(IMP_CAMP) do if MM9.actorAlive(a) then evt.SetActorTarget(a, "party") end end
    evt.SetActorTarget(IMP, "party")
end
handlers[601] = function()
    evt.StopTimer(601)
    if var("ImpAlarm") == 2 or not MM9.actorAlive(IMP) then return end
    if var("ImpAlarm") == 1 then
        if impPhase == 2 then   -- the wince is over: RunTo ImpMarker2
            impPhase, impRun = 3, 0
            evt.SetActorImmobile(IMP, false)
            evt.MoveActorTo(IMP, IMP_MARKER2[1], IMP_MARKER2[2], IMP_MARKER2[3], 602, true)
        elseif impPhase == 3 then   -- running: by the camp (its imps crowd the marker), or out of time
            impRun = impRun + 1
            local x, y = evt.GetMapActorPosition(IMP)
            if impRun >= 40 or (x ~= nil and (x - IMP_MARKER2[1]) ^ 2 + (y - IMP_MARKER2[2]) ^ 2 <= 512 ^ 2) then
                evt.StopActorMove(IMP)
                impHelp()
                return
            end
        end
        evt.StartTimer(601, seconds(0.5))
        return
    end
    if impPhase == 0 then   -- :OnStart
        impPhase = 1
        evt.MoveActorTo(IMP, IMP_MARKER1[1], IMP_MARKER1[2], IMP_MARKER1[3])
    elseif evt.ActorSeesParty(IMP, 1536) then   -- :TargetFound
        set("ImpAlarm", 1)
        impPhase = 2
        evt.StopActorMove(IMP)
        evt.SetActorImmobile(IMP, true)
        evt.PlayActorClip(IMP, "hit", false)
        evt.StartTimer(601, seconds(1.0))
        return
    end
    evt.StartTimer(601, seconds(0.5))
end
handlers[602] = function() if var("ImpAlarm") == 1 then impHelp() end end
handlers.regionLoad = function()
    if var("ImpAlarm") == 1 then impHelp() end
end

handlers[1] = function()
    if handlers.regionLoad then handlers.regionLoad() end
end

-- MM9's BonePile objects (dungeon/objects.py): a click searches the pile (evt.SearchLootProp: its
-- TreasureLevel loot once, DiseaseChance; the pile stays).
handlers[30263] = function() evt.SearchLootProp("mm9:mountainpass:object:263") end   -- BonePile0
handlers[30264] = function() evt.SearchLootProp("mm9:mountainpass:object:264") end   -- BonePile1
handlers[30265] = function() evt.SearchLootProp("mm9:mountainpass:object:265") end   -- BonePile2
handlers[30266] = function() evt.SearchLootProp("mm9:mountainpass:object:266") end   -- BonePile3
handlers[30267] = function() evt.SearchLootProp("mm9:mountainpass:object:267") end   -- BonePile4


RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(602, "Lookout imp", handlers[602])
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(30263, "Bone Pile", handlers[30263], "Bone Pile")
RegisterEvent(30264, "Bone Pile", handlers[30264], "Bone Pile")
RegisterEvent(30265, "Bone Pile", handlers[30265], "Bone Pile")
RegisterEvent(30266, "Bone Pile", handlers[30266], "Bone Pile")
RegisterEvent(30267, "Bone Pile", handlers[30267], "Bone Pile")
RegisterMapTimerEvent(600, seconds(0.5), handlers[600], "Mountain Pass triggers", "", seconds(0.5))
RegisterMapTimerEvent(601, seconds(1), handlers[601], "Lookout imp", "", seconds(1))
