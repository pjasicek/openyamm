-- Training Hall, MM9 rework (level_generation/projects/mm9r_traininghall/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {Pusher0 = 16, Pusher1 = 17, Pusher2 = 18, Rank0250d = 19, Rank0500c = 20, Rank0500d = 21, Rank0750b = 22, Rank0750c = 23, Rank0750d = 24, Rank1000a = 25, Rank1000b = 26, Rank1000c = 27, Rank1000d = 28, Rank1000d_INV = 29, Rank2000a = 30, Rank2000b = 31, Rank2000c = 32, Rank2000c_INV = 33, Rank4000a = 34, Rank4000b = 35, Rank4000b_INV = 36, Rank8000a = 37, Rank8000a_INV = 38, RotatingDoor0 = 13, RotatingDoor1 = 15, RotatingDoor2 = 12, RotatingDoor3 = 14, d2lever = 39, d2w1 = 5, d2w2 = 4, d2w3 = 3, d2w4 = 2, d4lever0 = 40, d4w1 = 8, d4w2 = 9, d4w3 = 10, d4w4 = 11, dragonroomdoorL = 42, dragonroomdoorR = 41, drop = 43, drop_GLASS2 = 45, drop_INV = 44, dummy2door = 1, dummy4door = 6, dummy4guide = 7, resetlever1 = 46, resetlever2 = 47, resetlever3 = 48, resetlever4 = 49, target1 = 50, target2 = 51, target3 = 52, target4 = 53, target4_INV = 54}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 902}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}, [44] = {3}, [45] = {4}}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(12, DoorAction.Trigger) evt.SetDoorState(13, DoorAction.Trigger) end   -- LobbyDoorE
handlers[102] = function() evt.SetDoorState(14, DoorAction.Trigger) evt.SetDoorState(15, DoorAction.Trigger) end   -- LobbyDoorW
handlers[103] = function() evt.SetDoorState(41, DoorAction.Trigger) evt.SetDoorState(42, DoorAction.Trigger) end   -- dragonroomdoor

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- Blackbox
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest0
handlers[43] = function() evt.OpenChest(2) end   -- TreasureChest1
handlers[44] = function() evt.OpenChest(3) end   -- TreasureChest3
handlers[45] = function() evt.OpenChest(4) end   -- TreasureChest4

-- Mover groups (each MM9 model's mechanism and its invisible collision part move together).
local GROUPS = {Horse2 = {1}, Horse2Wheels = {2, 3, 4, 5}, Horse4 = {6}, Horse4Guide = {7}, Horse4Wheels = {8, 9, 10, 11}, LobbyDoorE = {12, 13}, LobbyDoorW = {14, 15}, Pusher0 = {16}, Pusher1 = {17}, Pusher2 = {18}, Rank0250d = {19}, Rank0500c = {20}, Rank0500d = {21}, Rank0750b = {22}, Rank0750c = {23}, Rank0750d = {24}, Rank1000a = {25}, Rank1000b = {26}, Rank1000c = {27}, Rank1000d = {28, 29}, Rank2000a = {30}, Rank2000b = {31}, Rank2000c = {32, 33}, Rank4000a = {34}, Rank4000b = {35, 36}, Rank8000a = {37, 38}, d2lever = {39}, d4lever0 = {40}, dragonroomdoor = {41, 42}, drop = {43, 44, 45}, resetlever1 = {46}, resetlever2 = {47}, resetlever3 = {48}, resetlever4 = {49}, target1 = {50}, target2 = {51}, target3 = {52}, target4 = {53, 54}}
local function openG(g) for _, d in ipairs(GROUPS[g]) do evt.SetDoorState(d, DoorAction.Open) end end
local function closeG(g) for _, d in ipairs(GROUPS[g]) do evt.SetDoorState(d, DoorAction.Close) end end
local function arm(timer, delay) set("Armed" .. timer, 1); evt.StartTimer(timer, seconds(delay)) end
local function fired(timer)
    evt.StopTimer(timer)
    if var("Armed" .. timer) ~= 1 then return false end
    set("Armed" .. timer, 0)
    return true
end
local function sound(name) evt.PlaySoundName(name, 0, 0, 0) end
local function inBox(b, x, y, z) return x >= b[1][1] - 37 and x <= b[2][1] + 37 and y >= b[1][2] - 37 and y <= b[2][2] + 37 and z + 170 >= b[1][3] and z <= b[2][3] end
local function hintOff(cog) set("HintOff" .. cog, 1); evt.SetFacetBit(cog, FacetBits.Invisible, true) end

-- The lobby chandelier (dropsequence -> cracktrigger1-5 -> droptrigger destroys DestructableBrush6, whose death
-- opens Door "drop": 432 LT down at 750 LT/s, Sticky). The party standing on it hears each trigger's
-- ActivationSound as it fires (MM9's SendDelays: dropsequence 0, cracktrigger1 0.5, 2-3 0.35, 4 0.25, 5 1.25,
-- droptrigger 1.0 s): the wood creaks and cracks, the bar shatters and the chandelier falls into the pool.
local CRACKS = {{0.5, "events/woodwood02.wav"}, {0.35, "events/woodwood03.wav"}, {0.35, "events/shatterwood01.wav"}, {0.25, "events/shatterwood02.wav"}}
local function creak()
    if var("DropDone") == 1 or var("DropCrack") > 0 then return end
    sound("ambient/woodcreak2.wav")   -- dropsequence
    sound("events/woodwood01.wav")   -- cracktrigger1
    set("DropCrack", 1)
    arm(405, CRACKS[1][1])
end
handlers[405] = function()   -- cracktrigger2-5
    if not fired(405) then return end
    local k = var("DropCrack")
    sound(CRACKS[k][2])
    set("DropCrack", k + 1)
    if CRACKS[k + 1] then arm(405, CRACKS[k + 1][1]) else arm(406, 1.25 + 1.0) end
end
handlers[406] = function()
    if not fired(406) then return end
    evt.DestroyDestructible(2)   -- droptrigger: DestructableBrush6 destroy
end
-- DestructableBrush6's death (droptrigger's destroy, or 100 HP of weapon damage) opens "drop".
handlers[221] = function()
    if var("DropDone") == 1 then return end
    set("DropDone", 1)
    openG("drop")
    hintOff(300)   -- Door drop OpenTrigger: "drop perception" off
end

-- The lobby ghouls (TH_LobbyGhouls.scr): TriggerLobbyGhouls sends them up the stairs into the pole room and
-- onto WO_GhoulPlatform over its entrance (MM9 runs them along Ghoul*Marker0-2 and sets them on the last
-- marker) and uses the dragon door; TriggerGhoulsAttack drops them in front of the party and uses the door;
-- TriggerShutDoor uses it once more. A dead ghoul takes neither Go nor Drop (MM9.receives): it stays where it
-- fell. Drop makes the platform non-solid (DropGhouls: ClearFlag WO_GhoulPlatform), so whatever is perched on
-- it falls once any living ghoul takes it.
local GHOULS = {{name = "GhoulInSauna0", actor = 16, perch = {154, 1874, 1485}, land = {154, 1812, 517}}, {name = "GhoulInSauna1", actor = 17, perch = {-113, 1864, 1485}, land = {-113, 1802, 517}}}
local function ghoulsUp()
    set("GhoulsUp", 1)
    for _, g in ipairs(GHOULS) do
        if MM9.receives("traininghall", g.name, "Go", g.actor) then
            set("Perched" .. g.name, 1)
            evt.SetMapActorPosition(g.actor, g.perch[1], g.perch[2], g.perch[3])
        end
    end
    openG("dragonroomdoor")
end
local function ghoulsDrop()
    if var("GhoulsUp") ~= 1 then return end
    set("GhoulsDropped", 1)
    local drops = false
    for _, g in ipairs(GHOULS) do
        if MM9.receives("traininghall", g.name, "Drop", g.actor) then drops = true end
    end
    for _, g in ipairs(GHOULS) do
        if drops and var("Perched" .. g.name) == 1 then
            set("Perched" .. g.name, 0)
            evt.SetMapActorPosition(g.actor, g.land[1], g.land[2], g.land[3])
        end
    end
    closeG("dragonroomdoor")
end

-- The joust (d2lever, Switch: open -> Trigger2 turns the wheels and opens dummy2door, the horse rides 1190 LT
-- east at 1250 LT/s; close -> Trigger3 and dummy2door back at 200 LT/s). A click on the lever does it, and so
-- does the Mean Trellborg (TH_MeanTrellborg.scr) while the party is down at the lanes (TriggerTrellborgOn0/1
-- 'Go', Off0/1 'Stop'): stand, two fidgets and a taunt (routine "launch": MEAN_LEAD s), pull, he turns to
-- the Trellborg the horse rides at, pulls it back facing the lever (dummy2door 'Switch', routine "reset"), and
-- when it is back ('Throw') he starts again.
-- The horse's wheels (d2w1-4, RotatingBrush: mover spin) turn while it rides: Trigger2 sends them on and
-- reverse, Trigger3 reverse and on; dummy2door's Open/CloseTriggers (TriggerHorseGo) send off on arrival (out
-- 1190 LT at 1250 LT/s, back at 200 LT/s). The second horse's wheels (d4w1-4) never turn in MM9: Trigger7
-- sends them on and Trigger6 off in the same moment.
local WHEELS2 = {DOORS.d2w1, DOORS.d2w2, DOORS.d2w3, DOORS.d2w4}
local function wheels2(...) for _, w in ipairs(WHEELS2) do for _, m in ipairs({...}) do evt.SpinMover(w, m) end end end
local function lever2(pull)
    if pull then openG("d2lever"); openG("Horse2"); openG("Horse2Wheels"); set("Horse2Out", 1)
    else closeG("d2lever"); closeG("Horse2"); closeG("Horse2Wheels"); set("Horse2Out", 0) end
    if pull then wheels2("on", "reverse") else wheels2("reverse", "on") end
    arm(409, pull and 1190 / 1250 or 1190 / 200)
    sound("events/gears01.wav")
end
handlers[409] = function() if fired(409) then wheels2("off") end end   -- TriggerHorseGo
handlers[201] = function() lever2(var("Horse2Out") == 0) end

-- The training scenes (SCENES in convert.py): while the party is in its part of the hall, each actor runs its
-- MM9 script's chain of clips and walks (its scene routine, runtime only: set again on load); the drill, the
-- commanders' orders, the observers' pacing, the gossip, the jousters' and the lookout's watch.
local SCENES = {
    OrcTraining = {routine = "train", actors = {7, 10, 9, 6, 8, 11}},
    Gossip = {routine = "gossip", actors = {13, 12}},
    BoxOrcs = {routine = "train", actors = {14, 15}},
    Jousting = {routine = "joust", actors = {21, 20, 19}},
}
local function scene(name, on)
    set(name, on and 1 or 0)
    for _, a in ipairs(SCENES[name].actors) do evt.SetActorRoutine(a, on and SCENES[name].routine or nil) end
end
local MEAN, MEAN_LEAD = 18, 7
local function meanLaunch() evt.SetActorRoutine(MEAN, "launch"); arm(403, MEAN_LEAD) end
handlers[403] = function()
    if not fired(403) then return end
    if var("Jousting") ~= 1 or var("MeanDead") == 1 then return end
    if var("JoustThrow") == 1 then           -- the horse is back ('Throw'): :CheckStart
        set("JoustThrow", 0); meanLaunch()
    elseif var("Horse2Out") == 0 then        -- :LaunchHorse
        lever2(true); set("Launches", var("Launches") + 1)
        arm(403, 1.5)
    else                                      -- :ResetSwitch
        lever2(false); evt.SetActorRoutine(MEAN, "reset"); set("JoustThrow", 1)
        arm(403, 1190 / 200)
    end
end
local function joust(on)
    scene("Jousting", on)
    set("JoustThrow", 0)
    if on then meanLaunch() else evt.SetActorRoutine(MEAN, nil) end
end
handlers[96] = function(context) if context.actorIndex == MEAN then set("MeanDead", 1) end end

-- The second horse (d4lever0, Switch: open -> dummy4guide and dummy4door open; dummy4door rides 2000 LT east
-- through the wooden wall: woodexplosion, PerceptionBrush1 off, and dummy4guide's upperbreak1 -> Trigger8 ->
-- lowerbreak1, upperbreak2, Trigger9 -> lowerbreak2: the wall is gone and the debris room behind it is open).
-- Close: the guide goes back and dummy4door locks where it stands (MM9).
handlers[202] = function()
    sound("events/gears01.wav")
    if var("Lever4Open") == 1 then
        set("Lever4Open", 0); closeG("d4lever0"); closeG("Horse4Guide")
        return
    end
    set("Lever4Open", 1); openG("d4lever0"); openG("Horse4Guide")
    if var("WallBroken") == 1 then return end
    openG("Horse4"); openG("Horse4Wheels")
    hintOff(301)
    arm(404, 1.1)
end
handlers[404] = function()
    if not fired(404) then return end
    set("WallBroken", 1)
    sound("weapons/eqhammerimpact.wav")
    for _, k in ipairs({242, 243, 244, 245}) do set("AmbientSound" .. k, 1) end   -- upper/lowerbreak1-2 DamageTriggers: exsound0-3 on
    for _, id in ipairs({241, 235, 236, 238, 239}) do evt.DestroyDestructible(id) end   -- the wall's TriggerDestroyOnly pieces
end

-- The reset levers by the range (RotatingDoor, MM9 Locked: nothing in the map unlocks them).
handlers[203] = function() evt.StatusText("The lever is locked.") end
handlers[204] = function() evt.StatusText("The lever is locked.") end
handlers[205] = function() evt.StatusText("The lever is locked.") end
handlers[206] = function() evt.StatusText("The lever is locked.") end

-- The crate round the Blackbox (DestructableBrush0-5, 25 HP, each turns its PerceptionBrush2-7 off; the back
-- board DestructableBrush8, 100 HP: crateopentrigger turns PerceptionBrush8 off): scene destructibles that
-- weapons break (a click on a board: the shared killing blow; a click or missile on its hint: this event).
local function breakBoard(board, id, cog)
    if var("Broken" .. board) == 1 then return end
    set("Broken" .. board, 1)
    evt.DestroyDestructible(id); hintOff(cog)
end
handlers[210] = function() breakBoard("DestructableBrush0", 37, 302) end
handlers[211] = function() breakBoard("DestructableBrush1", 38, 303) end
handlers[212] = function() breakBoard("DestructableBrush2", 39, 304) end
handlers[213] = function() breakBoard("DestructableBrush3", 40, 305) end
handlers[214] = function() breakBoard("DestructableBrush4", 41, 306) end
handlers[215] = function() breakBoard("DestructableBrush5", 42, 307) end
handlers[216] = function() breakBoard("DestructableBrush8", 43, 308) end

-- The hall's end (TrainingEnter.scr "TrainingHall" on TrainingTrigger): breaking the bar on the end door
-- (DestructableBrush12, 1 HP) gives key 301, +5 Might and +5 Intellect (GiveAttribute 0 5 1, 1 5 1: the
-- active member, as the Ruined Temple reads it), 20000 experience and the quest sound, and turns ExitTrigger0
-- on: here the bar's invisible slab across the door's recess goes with it. With the key, the map loads with
-- the bar gone (:Init RemoveObject).
handlers[220] = function()
    if var("BarBroken") == 1 then return end
    set("BarBroken", 1)
    evt.DestroyDestructible(443)
    if MM9.hasKey(301) == 0 then
        MM9.giveKey(301)
        AddValue(BaseMight, 5)
        AddValue(BaseIntellect, 5)
        MM9.giveExperience(18500) -- MM9 GiveExp 20000, mm9_quest_xp_profile.yml
        MM9.playSound("sounds/events/quest.wav")
    end
end

-- The archery range (TH_TargetMgr.scr, TH_TargetRing.scr). The four targets stand at load; passing
-- TriggerTargetsOff (StartOn) lays them flat ('closeall' -> LowerTargets: each target opens), TriggerTargetsOn
-- stands them up again ('openall'); each re-arms the other. A ring hit by a missile (or a click) rings the bell,
-- pays its prize in gold once per target (key 7009 + target) and lays its target flat for good (open, lock).
local TARGETS = {[1] = {"target1", "Rank8000a", "Rank4000a", "Rank2000a", "Rank1000a"}, [2] = {"target2", "Rank4000b", "Rank2000b", "Rank1000b", "Rank0750b"}, [3] = {"target3", "Rank2000c", "Rank1000c", "Rank0750c", "Rank0500c"}, [4] = {"target4", "Rank1000d", "Rank0750d", "Rank0500d", "Rank0250d"}}
local function setTarget(t, down)
    if var("TargetLocked" .. t) == 1 then return end
    for _, g in ipairs(TARGETS[t]) do if down then openG(g) else closeG(g) end end
end
local function hitRing(t, prize)
    if var("TargetLocked" .. t) == 1 or var("TargetsDown") == 1 then return end
    set("RingHits", var("RingHits") + 1)
    if MM9.hasKey(7009 + t) == 0 then
        MM9.giveKey(7009 + t)
        MM9.giveGold(prize)
        set("Prize" .. t, prize)
        sound("events/gold01.wav")
    end
    sound("events/hand bell.wav")
    setTarget(t, true)
    set("TargetLocked" .. t, 1)
end
handlers[230] = function() hitRing(1, 8000) end   -- Rank8000a
handlers[231] = function() hitRing(1, 4000) end   -- Rank4000a
handlers[232] = function() hitRing(1, 2000) end   -- Rank2000a
handlers[233] = function() hitRing(1, 1000) end   -- Rank1000a
handlers[234] = function() hitRing(2, 4000) end   -- Rank4000b
handlers[235] = function() hitRing(2, 2000) end   -- Rank2000b
handlers[236] = function() hitRing(2, 1000) end   -- Rank1000b
handlers[237] = function() hitRing(2, 750) end   -- Rank0750b
handlers[238] = function() hitRing(3, 2000) end   -- Rank2000c
handlers[239] = function() hitRing(3, 1000) end   -- Rank1000c
handlers[240] = function() hitRing(3, 750) end   -- Rank0750c
handlers[241] = function() hitRing(3, 500) end   -- Rank0500c
handlers[242] = function() hitRing(4, 1000) end   -- Rank1000d
handlers[243] = function() hitRing(4, 750) end   -- Rank0750d
handlers[244] = function() hitRing(4, 500) end   -- Rank0500d
handlers[245] = function() hitRing(4, 250) end   -- Rank0250d

-- The pole room's beams (Pusher0-2: MM9 Doors with Looping, 130-150 LT at 40 LT/s, MoveDelay 2, OpenWaitTime 3,
-- CloseWaitTime 2): out, wait, back, wait, for ever, sweeping their beams.
local PUSHERS = {{name = "Pusher0", out = 3.25, back = 9.5, cycle = 11.5, delay = 2}, {name = "Pusher1", out = 3.75, back = 10.5, cycle = 12.5, delay = 2.2}, {name = "Pusher2", out = 3.75, back = 10.5, cycle = 12.5, delay = 2.4}}
handlers[402] = function()
    evt.StartTimer(402, seconds(0.25))
    local tick = var("PushTick") + 1
    set("PushTick", tick)
    for _, p in ipairs(PUSHERS) do
        local t = (tick * 0.25 - p.delay) % p.cycle
        if t < 0.25 then openG(p.name) elseif t >= p.out + (p.back - 2 * p.out) and t < p.out + (p.back - 2 * p.out) + 0.25 then closeG(p.name) end
    end
end

-- MM9's Trigger volumes, polled four times a second. The one-shot ones fire once (MM9 turns them off); the
-- paired on/off ones fire whenever their state allows (MM9's mutual On/Off messages) and the party has left
-- the box since.
local VOLUMES = {
    {name = "dropsequence", box = {{-369, -369, 1188}, {369, 369, 1403}}, again = false, armed = function() return true end, run = function() creak() end},
    {name = "TriggerLobbyGhouls", box = {{-369, -369, 1188}, {369, 369, 1572}}, again = false, armed = function() return true end, run = function() ghoulsUp() end},
    {name = "TriggerGhoulsAttack", box = {{-128, 1756, 568}, {128, 1807, 824}}, again = false, armed = function() return true end, run = function() ghoulsDrop() end},
    {name = "TriggerShutDoor", box = {{-128, 2330, 323}, {128, 2586, 579}}, again = false, armed = function() return var("GhoulsDropped") == 1 end, run = function() closeG("dragonroomdoor") end},
    {name = "TriggerTargetsOn", box = {{1434, -2662, 5}, {4055, -2406, 261}}, again = true, armed = function() return var("TargetsDown") == 1 end, run = function() set("TargetsDown", 0); for t = 1, 4 do setTarget(t, false) end end},
    {name = "TriggerTargetsOff", box = {{1434, -3328, 5}, {4055, -3072, 261}}, again = true, armed = function() return var("TargetsDown") == 0 end, run = function() set("TargetsDown", 1); for t = 1, 4 do setTarget(t, true) end end},
    {name = "TriggerTrellborgOn0", box = {{1766, -1152, -333}, {2022, -896, -77}}, again = true, armed = function() return var("Jousting") == 0 end, run = function() joust(true) end},
    {name = "TriggerTrellborgOn1", box = {{-2012, -1152, -333}, {-1756, -896, -77}}, again = true, armed = function() return var("Jousting") == 0 end, run = function() joust(true) end},
    {name = "TriggerTrellborgOff0", box = {{1756, -712, -46}, {2012, -456, 210}}, again = true, armed = function() return var("Jousting") == 1 end, run = function() joust(false) end},
    {name = "TriggerTrellborgOff1", box = {{-2022, -701, -46}, {-1766, -445, 210}}, again = true, armed = function() return var("Jousting") == 1 end, run = function() joust(false) end},
    {name = "TriggerOrcTraining", box = {{2657, -1705, 36}, {2913, -1449, 292}}, again = true, armed = function() return var("OrcTraining") == 0 end, run = function() scene("OrcTraining", true) end},
    {name = "TriggerOrcsStop", box = {{2657, -1213, 36}, {2913, -957, 292}}, again = true, armed = function() return var("OrcTraining") == 1 end, run = function() scene("OrcTraining", false) end},
    {name = "TriggerGossipOn", box = {{1185, -141, -5}, {1313, 141, 251}}, again = true, armed = function() return var("Gossip") == 0 end, run = function() scene("Gossip", true) end},
    {name = "TriggerGossipOff", box = {{978, -384, -5}, {1029, 384, 251}}, again = true, armed = function() return var("Gossip") == 1 end, run = function() scene("Gossip", false) end},
    {name = "TriggerBoxOrcsOn", box = {{-2790, -128, -46}, {-2534, 128, 210}}, again = true, armed = function() return var("BoxOrcs") == 0 end, run = function() scene("BoxOrcs", true) end},
    {name = "TriggerBoxOrcsOff", box = {{-2360, -128, -46}, {-2104, 128, 210}}, again = true, armed = function() return var("BoxOrcs") == 1 end, run = function() scene("BoxOrcs", false) end}
}
handlers[400] = function()
    evt.StartTimer(400, seconds(0.25))
    local x, y, z = evt.GetPartyPosition()
    for _, v in ipairs(VOLUMES) do
        local inside = inBox(v.box, x, y, z)
        if inside and var("In" .. v.name) == 0 and var("Done" .. v.name) == 0 and v.armed() then
            if not v.again then set("Done" .. v.name, 1) end
            v.run()
        end
        set("In" .. v.name, inside and 1 or 0)
    end
end

-- The PerceptionBrushes: the red glow shows to a party whose Perception reaches the brush's PerceptionValue
-- (12: the chandelier's bar, the wooden wall; 17: the crate's boards) unless MM9's wiring switched it off.
local HINTS = {[300] = 12, [301] = 12, [302] = 17, [303] = 17, [304] = 17, [305] = 17, [306] = 17, [307] = 17, [308] = 17}
local function updateHints()
    for cog, value in pairs(HINTS) do
        local want = evt.CheckSkill(29, 0, value) and 2 or 1
        if var("Hint" .. cog) ~= want or var("HintOff" .. cog) == 1 then
            set("Hint" .. cog, want)
            evt.SetFacetBit(cog, FacetBits.Invisible, want == 1 or var("HintOff" .. cog) == 1)
        end
    end
end
handlers[401] = updateHints
handlers[1] = function()   -- map load: what MM9 saves stays as it was left
    for cog, _ in pairs(HINTS) do set("Hint" .. cog, 0) end
    updateHints()
    if MM9.hasKey(301) == 1 and var("BarBroken") == 0 then set("BarBroken", 1); evt.DestroyDestructible(443) end
    evt.StartTimer(400, seconds(0.25))
    evt.StartTimer(402, seconds(0.25))
    -- the scenes' routines are runtime only: those under way when the game was saved start again
    if var("OrcTraining") == 1 then scene("OrcTraining", true) end
    if var("Gossip") == 1 then scene("Gossip", true) end
    if var("BoxOrcs") == 1 then scene("BoxOrcs", true) end
    if var("Jousting") == 1 then joust(true) end
end

-- MM9's breakable brushes once built as click movers (destructibles.build_breakables): weapons break
-- them; a click still does, as a killing blow (refused while MM9's CanDamage is off).
handlers[38037] = function() evt.DamageDestructible(37, 1000000) end   -- DestructableBrush0
handlers[38038] = function() evt.DamageDestructible(38, 1000000) end   -- DestructableBrush1
handlers[38039] = function() evt.DamageDestructible(39, 1000000) end   -- DestructableBrush2
handlers[38040] = function() evt.DamageDestructible(40, 1000000) end   -- DestructableBrush3
handlers[38041] = function() evt.DamageDestructible(41, 1000000) end   -- DestructableBrush4
handlers[38042] = function() evt.DamageDestructible(42, 1000000) end   -- DestructableBrush5
handlers[38043] = function() evt.DamageDestructible(43, 1000000) end   -- DestructableBrush8
handlers[38443] = function() evt.DamageDestructible(443, 1000000) end   -- DestructableBrush12

-- MM9's touch Triggers switching AmbientSounds (dungeon/objects.py): entering one sends its On / Off / Toggle
-- (the scene sound's map variable AmbientSound<key>: 1 on, 2 off); ActivationCount limits the uses.
local SOUND_TRIGGERS = {
    {name = "dropsequence", box = {{-165, -165, 1212}, {165, 165, 1403}}, uses = 1, switches = {{3, "off", true}}},
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
    handlers[903]()
end

RegisterEvent(101, "Door", handlers[101], "Door")
RegisterEvent(102, "Door", handlers[102], "Door")
RegisterEvent(103, "Door", handlers[103], "Door")
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(43, "Chest", handlers[43], "Chest")
RegisterEvent(44, "Chest", handlers[44], "Chest")
RegisterEvent(45, "Chest", handlers[45], "Chest")
RegisterEvent(201, "Lever", handlers[201], "Lever")
RegisterEvent(202, "Lever", handlers[202], "Lever")
RegisterEvent(203, "Lever", handlers[203], "Lever")
RegisterEvent(204, "Lever", handlers[204], "Lever")
RegisterEvent(205, "Lever", handlers[205], "Lever")
RegisterEvent(206, "Lever", handlers[206], "Lever")
RegisterEvent(210, "Board", handlers[210], "Board")
RegisterEvent(211, "Board", handlers[211], "Board")
RegisterEvent(212, "Board", handlers[212], "Board")
RegisterEvent(213, "Board", handlers[213], "Board")
RegisterEvent(214, "Board", handlers[214], "Board")
RegisterEvent(215, "Board", handlers[215], "Board")
RegisterEvent(216, "Board", handlers[216], "Board")
RegisterEvent(220, "Bar", handlers[220], "Bar")
RegisterEvent(221, "Chandelier bar", handlers[221])
RegisterEvent(230, "Target", handlers[230], "Target")
RegisterEvent(231, "Target", handlers[231], "Target")
RegisterEvent(232, "Target", handlers[232], "Target")
RegisterEvent(233, "Target", handlers[233], "Target")
RegisterEvent(234, "Target", handlers[234], "Target")
RegisterEvent(235, "Target", handlers[235], "Target")
RegisterEvent(236, "Target", handlers[236], "Target")
RegisterEvent(237, "Target", handlers[237], "Target")
RegisterEvent(238, "Target", handlers[238], "Target")
RegisterEvent(239, "Target", handlers[239], "Target")
RegisterEvent(240, "Target", handlers[240], "Target")
RegisterEvent(241, "Target", handlers[241], "Target")
RegisterEvent(242, "Target", handlers[242], "Target")
RegisterEvent(243, "Target", handlers[243], "Target")
RegisterEvent(244, "Target", handlers[244], "Target")
RegisterEvent(245, "Target", handlers[245], "Target")
RegisterMapTimerEvent(400, seconds(3), handlers[400], "Trigger volumes", "", seconds(3))
RegisterMapTimerEvent(401, seconds(3), handlers[401], "Perception hints", "", seconds(3))
RegisterMapTimerEvent(402, seconds(3), handlers[402], "Pole room beams", "", seconds(3))
RegisterMapTimerEvent(403, seconds(3), handlers[403], "Timer", "", seconds(3))
RegisterMapTimerEvent(404, seconds(3), handlers[404], "Timer", "", seconds(3))
RegisterMapTimerEvent(405, seconds(3), handlers[405], "Timer", "", seconds(3))
RegisterMapTimerEvent(406, seconds(3), handlers[406], "Timer", "", seconds(3))
RegisterMapTimerEvent(409, seconds(3), handlers[409], "Timer", "", seconds(3))
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(38037, "DestructableBrush0", handlers[38037], "Boards")
RegisterEvent(38038, "DestructableBrush1", handlers[38038], "Boards")
RegisterEvent(38039, "DestructableBrush2", handlers[38039], "Boards")
RegisterEvent(38040, "DestructableBrush3", handlers[38040], "Boards")
RegisterEvent(38041, "DestructableBrush4", handlers[38041], "Boards")
RegisterEvent(38042, "DestructableBrush5", handlers[38042], "Boards")
RegisterEvent(38043, "DestructableBrush8", handlers[38043], "Boards")
RegisterEvent(38443, "DestructableBrush12", handlers[38443], "Boards")
RegisterMapTimerEvent(903, seconds(3), handlers[903], "Ambient triggers", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
RegisterMonsterKilledHook(96, "Mean Trellborg killed", handlers[96])
