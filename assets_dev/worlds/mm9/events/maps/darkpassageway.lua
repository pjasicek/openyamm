-- Dark Passageway, MM9 rework (level_generation/projects/mm9r_darkpassageway/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {Bridge0 = 1, Bridge1 = 2, Bridge2 = 3, Bridge3 = 4, Bridge4 = 5, CanyonDoorL0 = 6, CanyonDoorL0_INV = 7, CanyonDoorR0 = 8, CanyonDoorR0_INV = 9, DB_TeleporterCage0 = 10, DesertDoor0 = 11, DesertRoomDoor1 = 12, Door1 = 13, Door2 = 14, Door3 = 15, Door4 = 16, Door5 = 17, Door6 = 18, DoubleDoorL40 = 19, DoubleDoorR40 = 20, ElevatorObj = 21, ExitRamp = 22, ExitRiser = 23, ExitRoomDoor = 24, ExitRoomTempleDoor0 = 25, ExitRoomTempleDoor1 = 26, FlameCage = 27, FlameCage_GLASS1 = 29, FlameCage_INV = 28, ForestDoor0 = 30, MountainForestDoor = 31, Painting = 32, SpikeDoor1 = 33, SpikeDoor2 = 34, SpikeDoor3 = 35, SpikeDoor4 = 36, Switch = 37, TeleportDoor0 = 38, TeleportDoor1 = 39, TrapRoomDoor1 = 40, TrapRoomDoor2 = 41}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 902}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}, [44] = {3}, [45] = {4}, [46] = {5}, [47] = {6}}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(12, DoorAction.Trigger) end   -- DesertRoomDoor1
handlers[102] = function() evt.SetDoorState(24, DoorAction.Trigger) end   -- ExitRoomDoor
handlers[103] = function() evt.SetDoorState(25, DoorAction.Trigger) evt.SetDoorState(26, DoorAction.Trigger) end   -- ExitRoomTempleDoor
handlers[104] = function() evt.SetDoorState(31, DoorAction.Trigger) end   -- MountainForestDoor
handlers[105] = function() evt.SetDoorState(40, DoorAction.Trigger) end   -- TrapRoomDoor1
handlers[106] = function() evt.SetDoorState(41, DoorAction.Trigger) end   -- TrapRoomDoor2

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest0
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest1
handlers[43] = function() evt.OpenChest(2) end   -- TreasureChest2
handlers[44] = function() evt.OpenChest(3) end   -- TreasureChest3
handlers[45] = function() evt.OpenChest(4) end   -- TreasureChest4
handlers[46] = function() evt.OpenChest(5) end   -- TreasureChest5
handlers[47] = function() evt.OpenChest(6) end   -- TreasureChest6

-- Mover groups (each MM9 model's mechanism and its invisible collision part move together).
local GROUPS = {Bridge0 = {1}, Bridge1 = {2}, Bridge2 = {3}, Bridge3 = {4}, Bridge4 = {5}, CanyonDoor = {6, 7, 8, 9}, DB_TeleporterCage0 = {10}, DesertDoor0 = {11}, DesertRoomDoor1 = {12}, Door1 = {13}, Door2 = {14}, Door3 = {15}, Door4 = {16}, Door5 = {17}, Door6 = {18}, DoubleDoor40 = {19, 20}, ElevatorObj = {21}, ExitRamp = {22}, ExitRiser = {23}, ExitRoomDoor = {24}, ExitRoomTempleDoor = {25, 26}, FlameCage = {27, 28, 29}, ForestDoor0 = {30}, MountainForestDoor = {31}, Painting = {32}, SpikeDoor1 = {33}, SpikeDoor2 = {34}, SpikeDoor3 = {35}, SpikeDoor4 = {36}, Switch = {37}, TeleportDoor0 = {38}, TeleportDoor1 = {39}, TrapRoomDoor1 = {40}, TrapRoomDoor2 = {41}}
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
local function inBox(b, x, y, z) return x >= b[1][1] - 37 and x <= b[2][1] + 37 and y >= b[1][2] - 37 and y <= b[2][2] + 37 and z + 170 >= b[1][3] and z <= b[2][3] + 37 end
local function hintOff(cog) set("HintOff" .. cog, 1); evt.SetFacetBit(cog, FacetBits.Invisible, true) end
local function locked() evt.StatusText("The door is locked.") end

-- The bridge puzzle (DarkP_bridgepuzzle.scr, DarkP_initMyStuff.inc: 'Sequence to completion - ADCBDCBA').
-- The state is a 5-bit number, bit (4 - k) set while bridge k is down; each statue (DarkP_RaisingSwitch.scr
-- "PuzzleManager0 Hit<X>") maps the state through its table and the bridges whose bit changed move
-- (DarkP_RaisingBridge.scr: 160 LT between their markers at 180 LT/s). State 0 (every bridge up) solves it:
-- the statues stop and TeleportDoor0 unlocks and opens. The terror statue (DarkP_BridgeReset.scr) resets it.
local PUZZLE = {A = {[0] = 0, [1] = 5, [5] = 14, [9] = 21, [14] = 22, [17] = 0, [19] = 22, [21] = 14, [22] = 14, [23] = 14, [25] = 9, [26] = 5, [29] = 1, [30] = 1, [31] = 9}, B = {[0] = 0, [1] = 9, [5] = 30, [9] = 23, [14] = 5, [17] = 9, [19] = 31, [21] = 5, [22] = 1, [23] = 1, [25] = 17, [26] = 23, [29] = 23, [30] = 9, [31] = 23}, C = {[0] = 0, [1] = 23, [5] = 1, [9] = 22, [14] = 23, [17] = 5, [19] = 23, [21] = 19, [22] = 30, [23] = 9, [25] = 5, [26] = 31, [29] = 25, [30] = 5, [31] = 21}, D = {[0] = 0, [1] = 30, [5] = 22, [9] = 26, [14] = 30, [17] = 23, [19] = 30, [21] = 9, [22] = 21, [23] = 22, [25] = 23, [26] = 9, [29] = 30, [30] = 23, [31] = 29}}
local BUILT_UP = {true, false, false, false, true}
local function puzzleState() if var("PuzzleSet") == 0 then return 14 end return var("Puzzle") end
local function placeBridges(state)
    for k = 0, 4 do
        local down = math.floor(state / 2 ^ (4 - k)) % 2 == 1
        -- bridges 0 and 4 are built up (open = down), 1-3 built down (open = up)
        local moved = down == BUILT_UP[k + 1]
        if moved then openG("Bridge" .. k) else closeG("Bridge" .. k) end
        if k < 4 then evt.SetSprite(410 + 2 * k, not moved); evt.SetSprite(410 + 2 * k + 1, moved) end
    end
end
local function setPuzzle(state)
    local old = puzzleState()
    set("PuzzleSet", 1); set("Puzzle", state)
    if old ~= state then sound("spells/eshield.wav") end
    placeBridges(state)
    if state == 0 and var("PuzzleSolved") == 0 then
        set("PuzzleSolved", 1)
        openG("TeleportDoor0")
        MM9.playSound("sounds/events/quest.wav")
    end
end
-- The statues (animated decorations; each puzzle statue and its moved twin play together): at start
-- PlayAnim fidget1 (the banshee awareAir, which BANSHEE.abc lacks: it stands at rest), its end held; a Use
-- plays fidget1 (the banshee FidgetAir1) with EnchantItem.wav, and only the clip's end (PlayAnim's callback
-- :TriggerScrObj) tells the manager: Hit<X>, or Reset for the terror (DarkP_BridgeReset.scr). A click while
-- the clip plays is ignored (MM9 restarts it, still one trigger). The solved puzzle's Stop removes the Use.
local STATUES = {
    [0] = {cogs = {410, 411}, hit = "A", start = "fidget1", use = "fidget1", seconds = 2.033},   -- SwitchCreature0
    [1] = {cogs = {412, 413}, hit = "B", start = "fidget1", use = "fidget1", seconds = 3.667},   -- SwitchCreature1
    [2] = {cogs = {414, 415}, hit = "C", start = "fidget1", use = "fidget1", seconds = 2.000},   -- SwitchCreature2
    [3] = {cogs = {416, 417}, hit = "D", use = "fidgetair1", seconds = 3.000},   -- SwitchCreature3
    [4] = {cogs = {418}, start = "fidget1", use = "fidget1", seconds = 2.300},   -- SwitchCreature5
}
local function showStatue(k)   -- the pose it holds: the end of the last clip it played
    local s = STATUES[k]
    local clip = var("StatueUsed" .. k) == 1 and s.use or s.start
    if clip then for _, cog in ipairs(s.cogs) do evt.PlayDecorationClip(cog, clip, "end") end end
end
local function useStatue(k)   -- :MoveMe
    if var("PuzzleSolved") == 1 or var("StatueBusy" .. k) == 1 then return end
    local s = STATUES[k]
    set("StatueBusy" .. k, 1); set("StatueUsed" .. k, 1)
    for _, cog in ipairs(s.cogs) do evt.PlayDecorationClip(cog, s.use) end
    sound("spells/EnchantItem.wav")
    arm(430 + k, s.seconds)
end
local function statueDone(k)   -- :TriggerScrObj
    set("StatueBusy" .. k, 0)
    if var("PuzzleSolved") == 1 then return end
    local s = STATUES[k]
    setPuzzle(s.hit and (PUZZLE[s.hit][puzzleState()] or 0) or 14)
end
handlers[201] = function() useStatue(0) end   -- SwitchCreature0
handlers[430] = function() if fired(430) then statueDone(0) end end
handlers[202] = function() useStatue(1) end   -- SwitchCreature1
handlers[431] = function() if fired(431) then statueDone(1) end end
handlers[203] = function() useStatue(2) end   -- SwitchCreature2
handlers[432] = function() if fired(432) then statueDone(2) end end
handlers[204] = function() useStatue(3) end   -- SwitchCreature3
handlers[433] = function() if fired(433) then statueDone(3) end end
handlers[205] = function() useStatue(4) end   -- SwitchCreature5
handlers[434] = function() if fired(434) then statueDone(4) end end
handlers[221] = function()   -- TeleportDoor0: Locked until the puzzle is solved
    if var("PuzzleSolved") == 0 or var("TeleportDoor0Locked") == 1 then locked() return end
    openG("TeleportDoor0")
end

-- The teleporters (MM9 Teleporter objects, TouchNotify: the party walking into the box goes to its
-- TeleportDestination, facing the arrival's way, UseRotation).
local ARRIVALS = {Teleporter0 = {{-7864, -18678, -817}, 512}, LakeTeleporter = {{-19323, -10394, -1309}, 1535}, MountainTeleporter = {{-18801, -22036, -326}, 2044}, DesertTeleporter = {{-5243, -1454, -754}, 512}, ForestTeleporter = {{-15401, -9708, 2}, 512}}
local function teleport(name)
    local a = ARRIVALS[name]
    set("Teleported", var("Teleported") + 1); set("LastTeleport" .. name, var("LastTeleport" .. name) + 1)
    sound("magic/teleport.wav")
    evt.MoveToMap(a[1][1], a[1][2], a[1][3], a[2], 0, 0, 0, 0)
end

-- The canyon (DarkP_CanyonSwitch.scr on the ice statue SwitchCreature4, an animated decoration): a click
-- plays Hattack2, Taunt, Rattack1 and Fidget1 in turn, each with EnchantItem.wav; each clip's end wakes a
-- pair of the banshee statues' eyes (BansheeAEye0/1, 2/3, 6/7, then 4/5: Shooters, KBYellowLine, 5 damage,
-- one shot a second at the party), the last one stops the statue (holding Fidget1's end), removes its Use
-- and unlocks and opens the canyon doors (CanyonDoorL0/R0). At start it plays CastSpell, which
-- SKELETONWARRIOR.abc lacks: it stands at rest. TriggerBansheeOff0 by the mountain teleporter turns every
-- eye off. An eye's shot strikes the party in its path (FireMissile's strikesParty).
local EYES = {{-19446, -17439, 625}, {-19446, -17459, 625}, {-19446, -18749, 453}, {-19446, -18770, 453}, {-21821, -21309, 5}, {-21842, -21309, 5}, {-23276, -18422, 481}, {-23276, -18442, 481}}   -- in the order they wake
local CANYON = {{"hattack2", 0.900}, {"taunt", 0.900}, {"rattack1", 1.100}, {"fidget1", 1.700}}
local function shoot(e)
    local x, y, z = evt.GetPartyPosition()
    z = z + 100
    local dx, dy, dz = x - e[1], y - e[2], z - e[3]
    local length = math.max(1, math.sqrt(dx * dx + dy * dy + dz * dz))
    if length > 6000 then return end
    local k = math.max(64 / length, 0.05)
    local shot = evt.FireMissile("Fire", e[1] + dx * k, e[2] + dy * k, e[3] + dz * k, x, y, z, 5, "Energy", 0, 0, true)
    if shot then MM9.launchSound("KBYellowLine", e[1], e[2], e[3]) end
    set("EyeShots", var("EyeShots") + (shot and 1 or 0))
end
handlers[402] = function()
    evt.StartTimer(402, seconds(1))
    local on = var("EyesOn")
    if var("EyesOff") == 1 or on == 0 then return end
    for k = 1, math.min(on, 8) do shoot(EYES[k]) end
end
local function canyonClip(step)   -- :OnUse, :AnimateA-C
    set("CanyonStep", step)
    sound("spells/EnchantItem.wav")
    evt.PlayDecorationClip(419, CANYON[step][1])
    arm(408, CANYON[step][2])
end
local function canyonOpen()   -- :Stop, :CanyonDoors
    set("EyesOn", 8); set("CanyonOpen", 1); openG("CanyonDoor")
end
handlers[408] = function()   -- a clip's end: a pair of eyes wakes, then the next clip
    if not fired(408) then return end
    set("EyesOn", math.min(8, var("EyesOn") + 2))
    if var("CanyonStep") < #CANYON then canyonClip(var("CanyonStep") + 1) else canyonOpen() end
end
handlers[206] = function()   -- SwitchCreature4 :OnUse
    if var("CanyonUsed") == 1 then return end
    set("CanyonUsed", 1)
    canyonClip(1)
end
handlers[219] = function()   -- CanyonDoorL0/R0: Locked until the statue's call
    if var("CanyonOpen") == 0 then locked() return end
    openG("CanyonDoor")
end

-- The magic carpet (MagicCarpet.scr "0" on ElevatorObj, at the bottom of the canyon's pit): a click lifts it
-- at 500 LT/s; MM9 also drifts it the way the party faces (800 LT/s) and drops it back when it reaches y 0
-- or sticks. Native: a lift straight up to y 0 (README: Deviations); 8 s at the top, then it sinks back.
handlers[207] = function()
    if var("CarpetUp") == 1 then return end
    set("CarpetUp", 1); set("CarpetRides", var("CarpetRides") + 1)
    openG("ElevatorObj")
    arm(403, 2500 / 500 + 8)
end
handlers[403] = function()
    if not fired(403) then return end
    sound("default.wav")
    closeG("ElevatorObj"); set("CarpetUp", 0)
end

-- The forest ambush: TriggerDoor0 unlocks ForestDoor0 (AutoTrigger: it opens as the party comes); in the forest
-- TriggerAttack0 slams and locks it behind the party, and the Colloidal Warrior (DarkP_Warrior.scr :HitNpc)
-- strikes the adventurer down (DarkP_NPCDie.scr) and turns on the party. Its death unlocks TeleportDoor1
-- (DeathTriggerTarget); opening TeleportDoor1 locks TeleportDoor0 (its OpenTrigger).
local WARRIOR, ADVENTURER = 2, 3
handlers[406] = function()
    if not fired(406) then return end
    -- TriggerAttack0's HitNpc: a warrior killed before the ambush takes none (the adventurer lives), and a
    -- dead adventurer takes no Destroy (MM9.receives)
    if not MM9.receives("darkpassageway", "ColloidalWarrior0", "HitNpc", WARRIOR) then return end
    sound("weapons/swordhit01.wav")
    if MM9.receives("darkpassageway", "NPCAdventurer0", "destroy", ADVENTURER) then
        MM9.removeActor(ADVENTURER); set("AdventurerDead", 1)
    end
    evt.WakeActor(WARRIOR)
end
handlers[220] = function()
    if var("ForestUnlocked") == 0 or var("ForestLocked") == 1 then locked() return end
    openG("ForestDoor0")
end
handlers[218] = function()   -- TeleportDoor1: Locked until the warrior dies
    if var("WarriorDead") == 0 then locked() return end
    openG("TeleportDoor1"); set("TeleportDoor0Locked", 1)
end
handlers[96] = function(context)
    if context.monsterId == WARRIOR or context.actorIndex == WARRIOR then set("WarriorDead", 1) end
    if context.monsterId == 4 or context.actorIndex == 4 then
        set("CageBroken", 1); openG("DB_TeleporterCage0"); sound("events/clap01.wav")
    end
end

-- The painting (RotatingDoor, 90 about y; its OpenTriggers open DoubleDoorL40 (and R40 with it), lock it
-- and turn PerceptionBrush1 off): the hidden room with TreasureChest0-2 behind it.
handlers[208] = function()
    if var("PaintingOpen") == 1 then return end
    set("PaintingOpen", 1)
    openG("Painting"); openG("DoubleDoor40")
    hintOff(301)
end

-- The mirror puzzle in the desert (PassageMirror.scr "<angle> <next> <beam>", PassageLaser.scr,
-- PassageGemstone.scr "CageTerror 0 5"): a click on a mirror turns it 10 degrees clockwise (its counter + 1,
-- mod 36). A click on the gemstone shines its light (GemLight0) at Mirror0; a mirror whose counter is its
-- target angle / 10 passes it on to the next, the last to BeamReceiver1, and the gemstone then releases the
-- six cage terrors (their cage doors Door1-6 unlock and open, they come out after the door's open time) and
-- opens
-- DesertDoor0. Each mirror is a decoration (cog MIRROR_COG + k) turned by evt.AimDecoration, 10 degrees a
-- click at MM9's 180 degrees a second: MirrorTurns<k> counts every click (the aim keeps turning the same way
-- past a full turn), and the map's load puts each back at its angle (decoration aims are not saved).
local MIRRORS = {{name = "Mirror0", target = 33, at = {-6548, -13107, -315}, next = {-3113, -11141, -315}, facing = -0.4}, {name = "Mirror1", target = 1, at = {-3113, -11141, -315}, next = {-6881, -10486, -315}, facing = -180.4}, {name = "Mirror2", target = 34, at = {-6881, -10486, -315}, next = {-3031, -9134, -315}, facing = -0.6}, {name = "Mirror3", target = 5, at = {-3031, -9134, -315}, next = {-3277, -13107, -274}, facing = -180.2}}
local GEM_LIGHT = {-3302, -13107, -271}
local CAGES = {{name = "CageTerror0", actor = 6, door = "Door1"}, {name = "CageTerror1", actor = 10, door = "Door2"}, {name = "CageTerror2", actor = 7, door = "Door3"}, {name = "CageTerror3", actor = 9, door = "Door4"}, {name = "CageTerror4", actor = 11, door = "Door5"}, {name = "CageTerror5", actor = 8, door = "Door6"}}
local function mirrorCount(k) return var("Mirror" .. k) end
local function aimMirror(k, speed) evt.AimDecoration(420 + k - 1, -10 * var("MirrorTurns" .. k), speed) end
local function beamFrom(k)
    local m = MIRRORS[k]
    local a = math.rad(m.facing - mirrorCount(k) * 10)
    return {m.at[1] + math.cos(a) * 3000, m.at[2] + math.sin(a) * 3000, m.at[3]}
end
local function release()
    if var("CagesOpen") == 1 then return end
    set("CagesOpen", 1)
    sound("spells/enchantitem.wav"); sound("door/doorslidestone.wav")
    -- each terror's go (DP_CageMonster.scr :OpenCage unlocks and opens its own door): a dead one takes none
    for _, c in ipairs(CAGES) do
        if MM9.receives("darkpassageway", c.name, "go", c.actor) then openG(c.door) end
    end
    openG("DesertDoor0")
    arm(404, 192 / 60)
end
handlers[404] = function()   -- DP_CageMonster.scr :LeaveCage after the door's open time
    if not fired(404) then return end
    for _, c in ipairs(CAGES) do evt.WakeActor(c.actor) end
end
handlers[215] = function()   -- Gemstone :ShineLight
    set("Shines", var("Shines") + 1)
    sound("spells/enchantitem.wav")
    local from = GEM_LIGHT
    for k = 1, 4 do
        local m = MIRRORS[k]
        evt.Beam("PassageBeam" .. k, "openyamm:fx/arc_beam", from[1], from[2], from[3], m.at[1], m.at[2], m.at[3], 1.5)
        -- PassageMirror.scr :GiveFocus: a mirror turned 70-290 degrees from its facing sends no light on
        local count = mirrorCount(k)
        if count > 6 and count < 30 then return end
        if count ~= m.target then
            local to = beamFrom(k)
            evt.Beam("PassageBeamLost", "openyamm:fx/arc_beam", m.at[1], m.at[2], m.at[3], to[1], to[2], to[3], 1.5)
            return
        end
        from = m.at
    end
    local g = {-5734, -6190, -102}   -- Mirror3's light ends at BeamReceiver1
    evt.Beam("PassageBeam5", "openyamm:fx/arc_beam", from[1], from[2], from[3], g[1], g[2], g[3], 1.5)
    release()
end
handlers[210] = function()   -- Mirror0 :Rotate
    set("Mirror1", (var("Mirror1") + 1) % 36)
    set("MirrorTurns1", var("MirrorTurns1") + 1)
    aimMirror(1, 180)
    sound("door/doorslidestone.wav")
    evt.StatusText(tr("The mirror turns ({degrees} degrees).", {degrees = var("Mirror1") * 10}))
end
handlers[211] = function()   -- Mirror1 :Rotate
    set("Mirror2", (var("Mirror2") + 1) % 36)
    set("MirrorTurns2", var("MirrorTurns2") + 1)
    aimMirror(2, 180)
    sound("door/doorslidestone.wav")
    evt.StatusText(tr("The mirror turns ({degrees} degrees).", {degrees = var("Mirror2") * 10}))
end
handlers[212] = function()   -- Mirror2 :Rotate
    set("Mirror3", (var("Mirror3") + 1) % 36)
    set("MirrorTurns3", var("MirrorTurns3") + 1)
    aimMirror(3, 180)
    sound("door/doorslidestone.wav")
    evt.StatusText(tr("The mirror turns ({degrees} degrees).", {degrees = var("Mirror3") * 10}))
end
handlers[213] = function()   -- Mirror3 :Rotate
    set("Mirror4", (var("Mirror4") + 1) % 36)
    set("MirrorTurns4", var("MirrorTurns4") + 1)
    aimMirror(4, 180)
    sound("door/doorslidestone.wav")
    evt.StatusText(tr("The mirror turns ({degrees} degrees).", {degrees = var("Mirror4") * 10}))
end
handlers[222] = function()   -- DesertDoor0: Locked until the gemstone's light
    if var("CagesOpen") == 0 then locked() return end
    openG("DesertDoor0")
end

-- Njam the Meddler's cameo (Trigger1 -> SpawnNjam0 Spawn: SpawnNjamCameo.scr): a second later the effect and
-- Windup10 at the spawner (:Onspawn2), two more and he appears with the town portal sound (:Appear) and walks
-- (NjamCameo.scr: BaseWanderForceStartUp), 10-20 s later he goes (:Vanish2: his behaviour's departure,
-- worlds/mm9/behaviors/njam.lua cameo). A hit sends him away at once (NjamCameo.scr OnDamage: the behaviour).
local NJAM = 43
handlers[405] = function()
    if not fired(405) then return end
    local stage = var("NjamStage")
    if stage == 1 then
        set("NjamStage", 2)
        MM9.clientFx(NJAM, "mm9:GreaterDemon"); sound("magic/windup10.wav")
        arm(405, 2)
    elseif stage == 2 then
        set("NjamStage", 3); set("NjamShown", 1)
        sound("spells/TownPortal.wav")
        evt.SetMonsterBit(NJAM, MonsterBits.Invisible, false)
        evt.SetActorImmobile(NJAM, false)
        arm(405, evt.RandomBetween(10, 20))
    elseif stage == 3 then
        set("NjamStage", 4)
        if MM9.actorAlive(NJAM) then evt.TriggerActor(NJAM, "vanish") end
    end
end

-- The exit room (ExitTrigger0-3, four boxes at the room's corners, each turning the next on: 2 -> 0 -> 1 -> 3;
-- the last, on the riser, unlocks and raises ExitRiser 228 LT and runs out ExitRamp to the upper door; the
-- Switch (StartOpen, -> ExitReset) puts it all back: ExitTrigger2 on, the others off, riser down and locked).
local function exitStep(k)
    if var("ExitOn" .. k) ~= 1 then return end
    if k == 2 then set("ExitOn0", 1); set("ExitOn3", 0)
    elseif k == 0 then set("ExitOn1", 1); set("ExitOn2", 0); set("ExitOn3", 0)
    elseif k == 1 then set("ExitOn3", 1); set("ExitOn2", 0); set("ExitOn1", 0)
    elseif k == 3 then
        set("ExitOn0", 0); set("ExitOn1", 0); set("ExitOn2", 0); set("ExitOn3", 0)
        set("RiserUp", 1); openG("ExitRiser"); openG("ExitRamp")
        set("AmbientSound468", 1)   -- ExitTrigger3: the magic elevator sound on
        sound("magic/windup10.wav")
    end
    sound("spells/enchantitem.wav")
end
local function exitReset()
    set("ExitOn0", 0); set("ExitOn1", 0); set("ExitOn2", 1); set("ExitOn3", 0)
    set("RiserUp", 0); closeG("ExitRiser"); closeG("ExitRamp")
    set("AmbientSound468", 2)   -- ExitRiser's CloseTrigger0: off
end
handlers[217] = function()   -- Switch -> ExitReset
    for _, d in ipairs(GROUPS.Switch) do evt.SetDoorState(d, DoorAction.Trigger) end
    set("Resets", var("Resets") + 1)
    exitReset()
end

-- The Wyrde of the Unknown (NPC338.scr :OnRude on RUDE 338's exit): with key 476 the flame cage opens and the
-- exit is on (:activate); with item 396 and no key 188, key 188 and 146 000 experience; the first talk (no key
-- 187) gives keys 476 and 187, 92 000 experience, the quest sound and :activate. FlameCage sinks 128 LT at 15;
-- its invisible slab ring round ExitPoint goes with it; FlameDamage (PoisonGas, 10) burns until then.
local function activate()
    if var("CageOpen") == 1 then return end
    set("CageOpen", 1); openG("FlameCage")
end
handlers[50284] = function()   -- WyrdeoftheUnknown0
    if MM9.hasKey(476) == 1 then activate() end
    if MM9.hasKey(188) == 0 and MM9.hasItem(396) == 1 then
        MM9.giveKey(188); MM9.giveExperience(18500) -- MM9 GiveExp 146000, mm9_quest_xp_profile.yml
    end
    if MM9.hasKey(187) == 0 then
        MM9.giveKey(476); MM9.giveKey(187); MM9.giveExperience(18500) -- MM9 GiveExp 92000, mm9_quest_xp_profile.yml
        activate()
        MM9.playSound("sounds/events/quest.wav")
    end
end
handlers[407] = function() end

-- MM9's Trigger and Teleporter volumes, polled four times a second (any part of the party in the box). One-shot
-- ones fire once; the others whenever their state allows and the party has left the box since.
local VOLUMES = {
    {name = "SpikeTrigger1", box = {{-5857, -3564, -422}, {-5304, -3011, -279}}, again = false, armed = function() return var("SpikesOpen") == 0 end, run = function() set("SpikesOpen", 1); for k = 1, 4 do openG("SpikeDoor" .. k) end; sound("door/doormetal_open02.wav") end},
    {name = "TriggerDoor0", box = {{-15683, -17516, -333}, {-15119, -17260, -77}}, again = false, armed = function() return true end, run = function() set("ForestUnlocked", 1); openG("ForestDoor0") end},
    {name = "TriggerAttack0", box = {{-16169, -16461, -333}, {-14633, -15437, -77}}, again = false, armed = function() return true end, run = function() closeG("ForestDoor0"); set("ForestLocked", 1); arm(406, 1.5); sound("door/doorslammetal01.wav") end},
    {name = "TriggerBansheeOff0", box = {{-18611, -22287, -333}, {-18355, -21724, -77}}, again = false, armed = function() return true end, run = function() set("EyesOff", 1) end},
    {name = "Trigger1", box = {{-8044, -14761, -851}, {-7685, -14403, -493}}, again = false, armed = function() return true end, run = function() set("NjamStage", 1); arm(405, 1) end},
    {name = "ExitTrigger0", box = {{-5612, 1044, -1198}, {-5448, 1208, -1096}}, again = true, armed = function() return var("ExitOn0") == 1 end, run = function() exitStep(0) end},
    {name = "ExitTrigger1", box = {{-5038, 1044, -1198}, {-4874, 1208, -1096}}, again = true, armed = function() return var("ExitOn1") == 1 end, run = function() exitStep(1) end},
    {name = "ExitTrigger2", box = {{-5038, 1413, -1198}, {-4874, 1577, -1096}}, again = true, armed = function() return var("ExitOn2") == 1 end, run = function() exitStep(2) end},
    {name = "ExitTrigger3", box = {{-5612, 1413, -1198}, {-5448, 1577, -1096}}, again = true, armed = function() return var("ExitOn3") == 1 end, run = function() exitStep(3) end},
    {name = "Teleporter0", box = {{-7665, -21898, -3354}, {-7409, -21642, -3098}}, again = true, armed = function() return true end, run = function() teleport("Teleporter0") end},
    {name = "LakeTeleporter", box = {{-19420, -10038, -1193}, {-19164, -9910, -937}}, again = true, armed = function() return true end, run = function() teleport("LakeTeleporter") end},
    {name = "MountainTeleporter", box = {{-19835, -22226, -292}, {-19732, -21765, -36}}, again = true, armed = function() return true end, run = function() teleport("MountainTeleporter") end},
    {name = "DesertTeleporter", box = {{-4838, -2954, -333}, {-4582, -2698, -77}}, again = true, armed = function() return true end, run = function() teleport("DesertTeleporter") end},
    {name = "ForestTeleporter", box = {{-15631, -11064, -292}, {-15171, -10808, -36}}, again = true, armed = function() return true end, run = function() teleport("ForestTeleporter") end},
    {name = "ShaftExit", box = {{-9708, -21709, -2683}, {-9462, -21422, -2458}}, again = true, armed = function() return true end, run = function() set("ShaftDrops", var("ShaftDrops") + 1); evt.MoveToMap(-9585, -21565, -2688, 0, 0, 0, 0, 0) end}
}
local FLAME = {{123, 5939, -573}, {573, 6758, -266}}
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
    -- FlameDamage (PoisonGas, Damage 10 a second) until the cage is open; the spike pit once (Spikes1, 100)
    if var("CageOpen") == 0 and inBox(FLAME, x, y, z) then
        set("FlameTicks", var("FlameTicks") + 1)
        if var("FlameTicks") % 4 == 0 then evt.DamagePlayer(Players.All, const.Damage.Fire, 10) end
    end
end

-- The PerceptionBrushes: the red glow shows to a party whose Perception reaches the brush's PerceptionValue
-- unless MM9's wiring switched it off (the painting's PerceptionBrush1).
local HINTS = {[300] = 20, [301] = 20, [302] = 20, [303] = 20}
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
    if var("ExitInit") == 0 then set("ExitInit", 1); set("ExitOn2", 1) end
    for k = 0, 4 do
        -- a save taken while a statue's clip played: the manager hears it now
        if var("StatueBusy" .. k) == 1 then set("Armed" .. (430 + k), 0); statueDone(k) end
        showStatue(k)
    end
    placeBridges(puzzleState())
    if var("CanyonUsed") == 1 and var("CanyonOpen") == 0 then set("Armed408", 0); canyonOpen() end
    if var("CanyonOpen") == 1 then evt.PlayDecorationClip(419, CANYON[#CANYON][1], "end") end
    for k = 1, 4 do aimMirror(k, 0) end
    if var("PuzzleSolved") == 1 then openG("TeleportDoor0") end
    if var("NjamShown") == 1 then MM9.removeActor(NJAM)
    elseif var("NjamStage") == 2 then set("NjamStage", 1); arm(405, 1) end   -- saved mid-spawn
    if var("AdventurerDead") == 1 then MM9.removeActor(ADVENTURER) end
    evt.StartTimer(400, seconds(0.25))
    evt.StartTimer(402, seconds(1))
end

-- MM9's greeting voices (dungeon/voices.py): a click on these people plays their GreetingSound or the
-- voice their script's :OnUse plays, then opens their dialogue (or runs the map's own click).
handlers[53284] = function() MM9.playSound("voices/npc/npc_338.wav"); MM9.openRude(338) end   -- WyrdeoftheUnknown0

-- MM9's PerceptionLights (dungeon/lights.py perception_lights): the red hint lights shine for a party whose
-- Perception reaches their PerceptionValue (scene pulsing lights, evt.SetLight), checked on load and every
-- 3 s. MM9's Off message: set("LightOff<key>", 1) and evt.SetLight(key, false); On: set("LightOff<key>", 0).
local PERCEPTION_LIGHTS = {[40469] = 20, [40470] = 20, [40471] = 20, [40472] = 20, [40473] = 20, [40474] = 20, [40475] = 20, [40476] = 20, [40477] = 20, [40478] = 20, [40479] = 20, [40480] = 20, [40481] = 20, [40482] = 20, [40483] = 20, [40484] = 20, [40485] = 20, [40486] = 20, [40487] = 20, [40488] = 20, [40489] = 20, [40490] = 20, [40491] = 20, [40492] = 20, [40493] = 20, [40494] = 20, [40495] = 20, [40496] = 20, [40497] = 20, [40498] = 20, [40499] = 20, [40500] = 20, [40501] = 20, [40502] = 20, [40503] = 20, [40504] = 20, [40505] = 20, [40506] = 20, [40507] = 20, [40508] = 20, [40509] = 20, [40510] = 20, [40511] = 20, [40512] = 20, [40513] = 20, [40514] = 20, [40515] = 20, [40516] = 20, [40517] = 20, [40518] = 20, [40519] = 20, [40520] = 20, [40521] = 20, [40522] = 20, [40523] = 20, [40524] = 20, [40525] = 20, [40526] = 20, [40527] = 20, [40528] = 20, [40529] = 20}
handlers[904] = function()
    for key, value in pairs(PERCEPTION_LIGHTS) do
        local want = (var("LightOff" .. key) == 0 and evt.CheckSkill(29, 0, value)) and 2 or 1
        if var("Light" .. key) ~= want then
            set("Light" .. key, want)
            evt.SetLight(key, want == 2)
        end
    end
end
handlers[902] = function()   -- map load: the shared objects
    for key, _ in pairs(PERCEPTION_LIGHTS) do set("Light" .. key, 0) end
    handlers[904]()
end

RegisterEvent(101, "Door", handlers[101], "Door")
RegisterEvent(102, "Door", handlers[102], "Door")
RegisterEvent(103, "Door", handlers[103], "Door")
RegisterEvent(104, "Door", handlers[104], "Door")
RegisterEvent(105, "Door", handlers[105], "Door")
RegisterEvent(106, "Door", handlers[106], "Door")
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(43, "Chest", handlers[43], "Chest")
RegisterEvent(44, "Chest", handlers[44], "Chest")
RegisterEvent(45, "Chest", handlers[45], "Chest")
RegisterEvent(46, "Chest", handlers[46], "Chest")
RegisterEvent(47, "Chest", handlers[47], "Chest")
RegisterEvent(201, "Statue", handlers[201], "Statue")
RegisterEvent(202, "Statue", handlers[202], "Statue")
RegisterEvent(203, "Statue", handlers[203], "Statue")
RegisterEvent(204, "Statue", handlers[204], "Statue")
RegisterEvent(205, "Statue", handlers[205], "Statue")
RegisterEvent(206, "Statue", handlers[206], "Statue")
RegisterEvent(207, "Magic carpet", handlers[207], "Carpet")
RegisterEvent(208, "Painting", handlers[208], "Painting")
RegisterEvent(210, "Mirror", handlers[210], "Mirror")
RegisterEvent(211, "Mirror", handlers[211], "Mirror")
RegisterEvent(212, "Mirror", handlers[212], "Mirror")
RegisterEvent(213, "Mirror", handlers[213], "Mirror")
RegisterEvent(215, "Gemstone", handlers[215], "Gemstone")
RegisterEvent(217, "Switch", handlers[217], "Switch")
RegisterEvent(218, "Door", handlers[218], "Door")
RegisterEvent(219, "Door", handlers[219], "Door")
RegisterEvent(220, "Door", handlers[220], "Door")
RegisterEvent(221, "Door", handlers[221], "Door")
RegisterEvent(222, "Door", handlers[222], "Door")
RegisterEvent(50284, "Wyrde of the Unknown", handlers[50284])
RegisterMapTimerEvent(400, seconds(3), handlers[400], "Trigger volumes", "", seconds(3))
RegisterMapTimerEvent(401, seconds(3), handlers[401], "Perception hints", "", seconds(3))
RegisterMapTimerEvent(402, seconds(3), handlers[402], "Banshee eyes", "", seconds(3))
RegisterMapTimerEvent(403, seconds(3), handlers[403], "Timer", "", seconds(3))
RegisterMapTimerEvent(404, seconds(3), handlers[404], "Timer", "", seconds(3))
RegisterMapTimerEvent(405, seconds(3), handlers[405], "Timer", "", seconds(3))
RegisterMapTimerEvent(406, seconds(3), handlers[406], "Timer", "", seconds(3))
RegisterMapTimerEvent(407, seconds(3), handlers[407], "Timer", "", seconds(3))
RegisterMapTimerEvent(408, seconds(3), handlers[408], "Timer", "", seconds(3))
RegisterMapTimerEvent(430, seconds(3), handlers[430], "SwitchCreature0's clip ends", "", seconds(3))
RegisterMapTimerEvent(431, seconds(3), handlers[431], "SwitchCreature1's clip ends", "", seconds(3))
RegisterMapTimerEvent(432, seconds(3), handlers[432], "SwitchCreature2's clip ends", "", seconds(3))
RegisterMapTimerEvent(433, seconds(3), handlers[433], "SwitchCreature3's clip ends", "", seconds(3))
RegisterMapTimerEvent(434, seconds(3), handlers[434], "SwitchCreature5's clip ends", "", seconds(3))
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(53284, "Wyrde of the Unknown", handlers[53284])
RegisterMapTimerEvent(904, seconds(3), handlers[904], "Perception lights", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
RegisterMonsterKilledHook(96, "Dark Passageway kills", handlers[96])
