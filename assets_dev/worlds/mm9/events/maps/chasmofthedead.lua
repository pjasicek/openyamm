-- Chasm of the Dead, MM9 rework (level_generation/projects/mm9r_chasmofthedead/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {CWL1 = 1, CWL2 = 2, CWPlate1 = 3, CWR1 = 4, CWR2 = 5, CeilingCrush3 = 6, CeilingCrush4 = 7, CeilingCrushPlate3 = 8, CeilingCrushPlate4 = 9, Door1 = 10, Door10 = 11, Door11 = 12, Door12 = 13, Door14 = 14, Door15 = 15, Door16 = 16, Door17 = 17, Door18 = 18, Door19 = 19, Door2 = 20, Door20 = 21, Door21 = 22, Door22 = 23, Door23 = 24, Door24 = 25, Door25 = 26, Door26 = 27, Door27 = 28, Door28 = 29, Door29 = 30, Door3 = 31, Door30 = 32, Door31 = 33, Door32 = 34, Door33 = 35, Door34 = 36, Door35 = 37, Door4 = 38, Door5 = 39, Door6 = 40, Door8 = 41, Door9 = 42, Gratetrap0 = 43, Gratetrap0_INV = 44, HSP1 = 45, HSP2 = 46, HSP6 = 47, HSP7 = 48, Pendulum1 = 49, Pendulum1_INV = 50, Pendulum2 = 51, Pendulum2_INV = 52, PivotButton1 = 53, PivotTreasurePanel1 = 54, PivotWallTrap1 = 55, SDL1 = 56, SDL2 = 58, SDL3 = 60, SDL4 = 62, SDL6 = 64, SDL7 = 66, SDU1 = 57, SDU2 = 59, SDU3 = 61, SDU4 = 63, SDU6 = 65, SDU7 = 67, ShooterPlate1 = 68, ShooterPlate10 = 69, ShooterPlate2 = 70, ShooterPlate3 = 71, ShooterPlate4 = 72, ShooterPlate5 = 73, ShooterPlate6 = 74, ShooterPlate7 = 75, ShooterPlate8 = 76, ShooterPlate9 = 77, SpikeRow1 = 78, SpikeRow10 = 79, SpikeRow11 = 80, SpikeRow12 = 81, SpikeRow13 = 82, SpikeRow14 = 83, SpikeRow2 = 84, SpikeRow3 = 85, SpikeRow4 = 86, SpikeRow5 = 87, SpikeRow6 = 88, SpikeRow7 = 89, SpikeRow8 = 90, SpikeRow9 = 91, SpikeRowPlate1 = 92, TrapExitDoor1 = 93}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 902}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}, [44] = {3}, [45] = {4}, [46] = {5}, [47] = {6}, [48] = {7}, [49] = {8}, [50] = {9}, [51] = {10}, [52] = {11}, [53] = {12}, [54] = {13}, [55] = {14}, [56] = {15}}})

local GROUPS = {CWL1 = {1}, CWL2 = {2}, CWPlate1 = {3}, CWR1 = {4}, CWR2 = {5}, CeilingCrush3 = {6}, CeilingCrush4 = {7}, CeilingCrushPlate3 = {8}, CeilingCrushPlate4 = {9}, Door1 = {10}, Door10 = {11}, Door11 = {12}, Door12 = {13}, Door14 = {14}, Door15 = {15}, Door16 = {16}, Door17 = {17}, Door18 = {18}, Door19 = {19}, Door2 = {20}, Door20 = {21}, Door21 = {22}, Door22 = {23}, Door23 = {24}, Door24 = {25}, Door25 = {26}, Door26 = {27}, Door27 = {28}, Door28 = {29}, Door29 = {30}, Door3 = {31}, Door30 = {32}, Door31 = {33}, Door32 = {34}, Door33 = {35}, Door34 = {36}, Door35 = {37}, Door4 = {38}, Door5 = {39}, Door6 = {40}, Door8 = {41}, Door9 = {42}, Gratetrap0 = {43, 44}, HSP1 = {45}, HSP2 = {46}, HSP6 = {47}, HSP7 = {48}, Pendulum1 = {49, 50}, Pendulum2 = {51, 52}, PivotButton1 = {53}, PivotTreasurePanel1 = {54}, PivotWallTrap1 = {55}, SD1 = {56, 57}, SD2 = {58, 59}, SD3 = {60, 61}, SD4 = {62, 63}, SD6 = {64, 65}, SD7 = {66, 67}, ShooterPlate1 = {68}, ShooterPlate10 = {69}, ShooterPlate2 = {70}, ShooterPlate3 = {71}, ShooterPlate4 = {72}, ShooterPlate5 = {73}, ShooterPlate6 = {74}, ShooterPlate7 = {75}, ShooterPlate8 = {76}, ShooterPlate9 = {77}, SpikeRow1 = {78}, SpikeRow10 = {79}, SpikeRow11 = {80}, SpikeRow12 = {81}, SpikeRow13 = {82}, SpikeRow14 = {83}, SpikeRow2 = {84}, SpikeRow3 = {85}, SpikeRow4 = {86}, SpikeRow5 = {87}, SpikeRow6 = {88}, SpikeRow7 = {89}, SpikeRow8 = {90}, SpikeRow9 = {91}, SpikeRowPlate1 = {92}, TrapExitDoor1 = {93}}
local function openGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Open) end end
local function closeGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Close) end end
local function arm(timer, delay) set("Armed" .. timer, 1); evt.StartTimer(timer, seconds(delay)) end
local function fired(timer)
    evt.StopTimer(timer)
    if var("Armed" .. timer) ~= 1 then return false end
    set("Armed" .. timer, 0)
    return true
end
local function inBox(b, x, y, z) return x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] and z + 170 >= b[1][3] and z <= b[2][3] end
local function near(b)
    local x, y, z = evt.GetPartyPosition()
    return inBox(b, x, y, z)
end
-- A Shooter sits in its wall or ceiling: the bolt starts a third of the way to the party's chest and
-- strikes the party in its path (FireMissile's strikesParty); `projectile` is its MM9 ProjectileName (the
-- launch sound).
local function shoot(sx, sy, sz, damage, kind, projectile)
    local x, y, z = evt.GetPartyPosition()
    z = z + 100
    local dx, dy, dz = x - sx, y - sy, z - sz
    local length = math.max(1, math.sqrt(dx * dx + dy * dy + dz * dz))
    local k = math.max(64 / length, 0.33)
    local shot = evt.FireMissile("Fire", sx + dx * k, sy + dy * k, sz + dz * k, x, y, z, damage, kind, 0, 0, true)
    if shot then MM9.launchSound(projectile, sx, sy, sz) end
    set("ShotsFired", var("ShotsFired") + (shot and 1 or 0))
end
local function hurt(amount) evt.DamagePlayer(Players.All, const.Damage.Physical, amount) end

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(10, DoorAction.Trigger) end   -- Door1
handlers[102] = function() evt.SetDoorState(11, DoorAction.Trigger) end   -- Door10
handlers[103] = function() evt.SetDoorState(12, DoorAction.Trigger) end   -- Door11
handlers[104] = function() evt.SetDoorState(13, DoorAction.Trigger) end   -- Door12
handlers[105] = function() evt.SetDoorState(14, DoorAction.Trigger) end   -- Door14
handlers[106] = function() evt.SetDoorState(15, DoorAction.Trigger) end   -- Door15
handlers[107] = function() evt.SetDoorState(16, DoorAction.Trigger) end   -- Door16
handlers[108] = function() evt.SetDoorState(17, DoorAction.Trigger) end   -- Door17
handlers[109] = function() evt.SetDoorState(18, DoorAction.Trigger) end   -- Door18
handlers[110] = function() evt.SetDoorState(19, DoorAction.Trigger) end   -- Door19
handlers[111] = function() evt.SetDoorState(20, DoorAction.Trigger) end   -- Door2
handlers[112] = function() evt.SetDoorState(21, DoorAction.Trigger) end   -- Door20
handlers[113] = function() evt.SetDoorState(22, DoorAction.Trigger) end   -- Door21
handlers[114] = function() evt.SetDoorState(23, DoorAction.Trigger) end   -- Door22
handlers[115] = function() evt.SetDoorState(24, DoorAction.Trigger) end   -- Door23
handlers[116] = function() evt.SetDoorState(25, DoorAction.Trigger) end   -- Door24
handlers[117] = function() evt.SetDoorState(26, DoorAction.Trigger) end   -- Door25
handlers[118] = function() evt.SetDoorState(27, DoorAction.Trigger) end   -- Door26
handlers[119] = function() evt.SetDoorState(28, DoorAction.Trigger) end   -- Door27
handlers[120] = function() evt.SetDoorState(29, DoorAction.Trigger) end   -- Door28
handlers[121] = function() evt.SetDoorState(30, DoorAction.Trigger) end   -- Door29
handlers[122] = function() evt.SetDoorState(31, DoorAction.Trigger) end   -- Door3
handlers[123] = function() evt.SetDoorState(32, DoorAction.Trigger) end   -- Door30
handlers[124] = function() evt.SetDoorState(33, DoorAction.Trigger) end   -- Door31
handlers[125] = function() evt.SetDoorState(34, DoorAction.Trigger) end   -- Door32
handlers[126] = function() evt.SetDoorState(35, DoorAction.Trigger) end   -- Door33
handlers[127] = function() evt.SetDoorState(36, DoorAction.Trigger) end   -- Door34
handlers[128] = function() evt.SetDoorState(37, DoorAction.Trigger) end   -- Door35
handlers[129] = function() evt.SetDoorState(38, DoorAction.Trigger) end   -- Door4
handlers[130] = function() evt.SetDoorState(39, DoorAction.Trigger) end   -- Door5
handlers[131] = function() evt.SetDoorState(40, DoorAction.Trigger) end   -- Door6
handlers[132] = function() evt.SetDoorState(41, DoorAction.Trigger) end   -- Door8
handlers[133] = function() evt.SetDoorState(42, DoorAction.Trigger) end   -- Door9

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest1
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest23
handlers[43] = function() evt.OpenChest(2) end   -- TreasureChest21
handlers[44] = function() evt.OpenChest(3) end   -- TreasureChest20
handlers[45] = function() evt.OpenChest(4) end   -- TreasureChest19
handlers[46] = function() evt.OpenChest(5) end   -- TreasureChest17
handlers[47] = function() evt.OpenChest(6) end   -- TreasureChest16
handlers[48] = function() evt.OpenChest(7) end   -- TreasureChest15
handlers[49] = function() evt.OpenChest(8) end   -- TreasureChest12
handlers[50] = function() evt.OpenChest(9) end   -- TreasureChest11
handlers[51] = function() evt.OpenChest(10) end   -- TreasureChest10
handlers[52] = function() evt.OpenChest(11) end   -- TreasureChest7
handlers[53] = function() evt.OpenChest(12) end   -- TreasureChest8
handlers[54] = function() evt.OpenChest(13) end   -- TreasureChest3
handlers[55] = function() evt.OpenChest(14) end   -- TreasureChest4
handlers[56] = function() evt.OpenChest(15) end   -- TreasureChest5

-- Shooter plates (MM9 Door + Trigger): the plate sinks, its Shooter fires one FireBolt (DamageAmt 20) and the plate rises after 1 s (CloseWaitTime).
handlers[200] = function()   -- ShooterPlate1 -> Shooter1
    if var("ShooterPlate1") == 1 then return end
    set("ShooterPlate1", 1)
    openGroup("ShooterPlate1")
    shoot(-15524, 22036, 1741, 20, "Fire", "FireBolt")
    arm(301, 1.1)
end
handlers[301] = function()
    if not fired(301) then return end
    closeGroup("ShooterPlate1")
    set("ShooterPlate1", 0)
end
handlers[201] = function()   -- ShooterPlate2 -> CeilingShooter1
    if var("ShooterPlate2") == 1 then return end
    set("ShooterPlate2", 1)
    openGroup("ShooterPlate2")
    shoot(-11223, 21668, 1925, 20, "Fire", "FireBolt")
    arm(302, 1.1)
end
handlers[302] = function()
    if not fired(302) then return end
    closeGroup("ShooterPlate2")
    set("ShooterPlate2", 0)
end
handlers[202] = function()   -- ShooterPlate3 -> CeilingShooter3
    if var("ShooterPlate3") == 1 then return end
    set("ShooterPlate3", 1)
    openGroup("ShooterPlate3")
    shoot(-9585, 12411, 676, 20, "Fire", "FireBolt")
    arm(303, 1.1)
end
handlers[303] = function()
    if not fired(303) then return end
    closeGroup("ShooterPlate3")
    set("ShooterPlate3", 0)
end
handlers[203] = function()   -- ShooterPlate4 -> CeilingShooter2
    if var("ShooterPlate4") == 1 then return end
    set("ShooterPlate4", 1)
    openGroup("ShooterPlate4")
    shoot(-9585, 12820, 676, 20, "Fire", "FireBolt")
    arm(304, 1.1)
end
handlers[304] = function()
    if not fired(304) then return end
    closeGroup("ShooterPlate4")
    set("ShooterPlate4", 0)
end
handlers[204] = function()   -- ShooterPlate5 -> Shooter2
    if var("ShooterPlate5") == 1 then return end
    set("ShooterPlate5", 1)
    openGroup("ShooterPlate5")
    shoot(5079, -3318, -4280, 20, "Fire", "FireBolt")
    arm(305, 1.1)
end
handlers[305] = function()
    if not fired(305) then return end
    closeGroup("ShooterPlate5")
    set("ShooterPlate5", 0)
end
handlers[205] = function()   -- ShooterPlate6 -> Shooter2
    if var("ShooterPlate6") == 1 then return end
    set("ShooterPlate6", 1)
    openGroup("ShooterPlate6")
    shoot(5079, -3318, -4280, 20, "Fire", "FireBolt")
    arm(306, 1.1)
end
handlers[306] = function()
    if not fired(306) then return end
    closeGroup("ShooterPlate6")
    set("ShooterPlate6", 0)
end
handlers[206] = function()   -- ShooterPlate7 -> Shooter2
    if var("ShooterPlate7") == 1 then return end
    set("ShooterPlate7", 1)
    openGroup("ShooterPlate7")
    shoot(5079, -3318, -4280, 20, "Fire", "FireBolt")
    arm(307, 1.1)
end
handlers[307] = function()
    if not fired(307) then return end
    closeGroup("ShooterPlate7")
    set("ShooterPlate7", 0)
end
handlers[207] = function()   -- ShooterPlate8 -> Shooter3
    if var("ShooterPlate8") == 1 then return end
    set("ShooterPlate8", 1)
    openGroup("ShooterPlate8")
    shoot(6062, -3318, -4280, 20, "Fire", "FireBolt")
    arm(308, 1.1)
end
handlers[308] = function()
    if not fired(308) then return end
    closeGroup("ShooterPlate8")
    set("ShooterPlate8", 0)
end
handlers[208] = function()   -- ShooterPlate9 -> Shooter3
    if var("ShooterPlate9") == 1 then return end
    set("ShooterPlate9", 1)
    openGroup("ShooterPlate9")
    shoot(6062, -3318, -4280, 20, "Fire", "FireBolt")
    arm(309, 1.1)
end
handlers[309] = function()
    if not fired(309) then return end
    closeGroup("ShooterPlate9")
    set("ShooterPlate9", 0)
end
handlers[209] = function()   -- ShooterPlate10 -> Shooter3
    if var("ShooterPlate10") == 1 then return end
    set("ShooterPlate10", 1)
    openGroup("ShooterPlate10")
    shoot(6062, -3318, -4280, 20, "Fire", "FireBolt")
    arm(310, 1.1)
end
handlers[310] = function()
    if not fired(310) then return end
    closeGroup("ShooterPlate10")
    set("ShooterPlate10", 0)
end

-- Hidden shooters (HSP plates, SDU/SDL shutters, HS shooters): the plate sinks, the shutters open, a bolt comes out, and they shut after 1 s (CloseWaitTime; MM9's flaps swing apart: here they slide).
handlers[220] = function()   -- HSP1
    if var("HSP1") == 1 then return end
    set("HSP1", 1)
    openGroup("HSP1")
    openGroup("SD1"); shoot(-860, -4956, -4280, 20, "Fire", "FireBolt")
    openGroup("SD2"); shoot(860, -6062, -4280, 20, "Fire", "FireBolt")
    arm(320, 1.3)
end
handlers[320] = function()
    if not fired(320) then return end
    closeGroup("SD1")
    closeGroup("SD2")
    closeGroup("HSP1")
    set("HSP1", 0)
end
handlers[221] = function()   -- HSP2
    if var("HSP2") == 1 then return end
    set("HSP2", 1)
    openGroup("HSP2")
    openGroup("SD3"); shoot(-860, -8806, -4280, 20, "Fire", "FireBolt")
    openGroup("SD4"); shoot(881, -7700, -4280, 20, "Fire", "FireBolt")
    arm(321, 1.3)
end
handlers[321] = function()
    if not fired(321) then return end
    closeGroup("SD3")
    closeGroup("SD4")
    closeGroup("HSP2")
    set("HSP2", 0)
end
handlers[222] = function()   -- HSP6
    if var("HSP6") == 1 then return end
    set("HSP6", 1)
    openGroup("HSP6")
    openGroup("SD6"); shoot(-12692, 8028, -3215, 20, "Fire", "FireBolt")
    arm(322, 1.3)
end
handlers[322] = function()
    if not fired(322) then return end
    closeGroup("SD6")
    closeGroup("HSP6")
    set("HSP6", 0)
end
handlers[223] = function()   -- HSP7
    if var("HSP7") == 1 then return end
    set("HSP7", 1)
    openGroup("HSP7")
    openGroup("SD7"); shoot(-6308, -737, -3215, 20, "Fire", "FireBolt")
    arm(323, 1.3)
end
handlers[323] = function()
    if not fired(323) then return end
    closeGroup("SD7")
    closeGroup("HSP7")
    set("HSP7", 0)
end

-- The closing walls (TriggerCWPlate1, CWR1/L1, CWR2/L2: Door 80 LT at 300, DoDamage; Spikes3-8 on them): the plate sinks, both pairs slam in, whoever stands between is hurt; 3 s later they draw back.
local WALL_BOX = {{-13148, 18760, 1577}, {-12247, 19251, 1946}}
handlers[230] = function()   -- CWPlate1
    if var("ClosingWalls") == 1 then return end
    set("ClosingWalls", 1)
    openGroup("CWPlate1")
    openGroup("CWR1"); openGroup("CWL1"); openGroup("CWR2"); openGroup("CWL2")
    arm(330, 0.3)
end
handlers[330] = function()
    if not fired(330) then return end
    if near(WALL_BOX) then hurt(20); set("WallHits", var("WallHits") + 1) end
    arm(331, 3)
end
handlers[331] = function()
    if not fired(331) then return end
    closeGroup("CWR1"); closeGroup("CWL1"); closeGroup("CWR2"); closeGroup("CWL2")
    closeGroup("CWPlate1")
    set("ClosingWalls", 0)
end

-- The spike wave (SpikeRowTrigger1, SpikeRowPlate1, SpikeRow1-14: Door, Solid 0, 96 LT up at 600, back at 100; each row's open toggles the next and the last): a wave runs the length of the stair.
local ROW_X = {-5663, -5765, -5868, -5969, -6072, -6174, -6277, -6380, -6482, -6584, -6686, -6789, -6892, -6994}
handlers[231] = function()   -- SpikeRowPlate1
    if var("SpikeWave") ~= 0 then return end
    set("SpikeWave", 1)
    openGroup("SpikeRowPlate1")
    evt.StartTimer(332, seconds(0.16))
end
handlers[332] = function()
    local k = var("SpikeWave")
    evt.StopTimer(332)
    if k == 0 then return end
    if k > 1 then closeGroup("SpikeRow" .. (k - 1)) end
    if k > 14 then
        closeGroup("SpikeRowPlate1")
        set("SpikeWave", 0)
        return
    end
    openGroup("SpikeRow" .. k)
    local x, y = evt.GetPartyPosition()
    if math.abs(x - ROW_X[k]) <= 70 and y >= 9815 and y <= 10172 then
        hurt(10); set("SpikeHits", var("SpikeHits") + 1)
    end
    set("SpikeWave", k + 1)
    evt.StartTimer(332, seconds(0.16))
end

-- Ceiling crushers (CeilingCrushPlate, CeilingCrush: Lift 160 LT down at 500, back at 100 after 3 s; Spikes5/6 20 a second): the plate sinks, the ceiling drops, a party under it takes 20.
handlers[236] = function()   -- CeilingCrushPlate3 -> CeilingCrush3
    if var("CeilingCrush3") == 1 then return end
    set("CeilingCrush3", 1)
    openGroup("CeilingCrushPlate3"); openGroup("CeilingCrush3")
    arm(336, 0.35)
end
handlers[336] = function()
    if not fired(336) then return end
    local x, y = evt.GetPartyPosition()
    if x >= -1781 and x <= -841 and y >= 3667 and y <= 4607 then
        hurt(20); set("CrushHits", var("CrushHits") + 1)
    end
    arm(337, 3)
end
handlers[337] = function()
    if not fired(337) then return end
    closeGroup("CeilingCrush3"); closeGroup("CeilingCrushPlate3")
    set("CeilingCrush3", 0)
end
handlers[237] = function()   -- CeilingCrushPlate4 -> CeilingCrush4
    if var("CeilingCrush4") == 1 then return end
    set("CeilingCrush4", 1)
    openGroup("CeilingCrushPlate4"); openGroup("CeilingCrush4")
    arm(338, 0.35)
end
handlers[338] = function()
    if not fired(338) then return end
    local x, y = evt.GetPartyPosition()
    if x >= 2336 and x <= 2825 and y >= -15728 and y <= -15197 then
        hurt(20); set("CrushHits", var("CrushHits") + 1)
    end
    arm(339, 3)
end
handlers[339] = function()
    if not fired(339) then return end
    closeGroup("CeilingCrush4"); closeGroup("CeilingCrushPlate4")
    set("CeilingCrush4", 0)
end

-- The pendulums (PendulumTrigger1/2, Pendulum1/2: RotatingDoor, 210 degrees at 100, 30 a second): a touch swings both blades through the corridor; the next touch swings them back (Sticky).
local PENDULUM_BOX = {{-5376, 3922, -1966}, {-4147, 4332, -1802}}
local function swing()
    if var("Pendulum") == 1 then return end
    set("Pendulum", 1)
    for _, name in ipairs({"Pendulum1", "Pendulum2"}) do
        for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Trigger) end
    end
    arm(333, 1.0)
end
handlers[333] = function()
    if not fired(333) then return end
    if near(PENDULUM_BOX) then hurt(30); set("PendulumHits", var("PendulumHits") + 1) end
    arm(334, 1.2)
end
handlers[334] = function()
    if not fired(334) then return end
    set("Pendulum", 0)
end
handlers[233] = function() swing() end

-- PivotTreasurePanel1 (PushOpen, Sticky): a click slides it up and shows TreasureChest1.
handlers[232] = function() openGroup("PivotTreasurePanel1") end

-- The pivot trap (PivotWallTrap1, its trigger on the corridor half, PivotButton1 in the alcove): the cross turns 90 degrees and tips the party into the spike pit; it turns back itself (the mover's auto-close) and arms again. The ladder climbs to TrapExitDoor1, a hatch opened by a click.
handlers[239] = function()
    if var("PivotTrap") == 1 then return end
    set("PivotTrap", 1)
    openGroup("PivotWallTrap1"); openGroup("PivotButton1")
    arm(340, 8)
end
handlers[340] = function()
    if not fired(340) then return end
    closeGroup("PivotButton1")
    set("PivotTrap", 0)
end
-- MM9's cross is a revolving wall: its quarter turn would carry a party from the pit's west half up into the alcove and from the alcove out to the corridor, but its trigger stands on the corridor half and the button in the alcove, so no party could ever get in. The pit's west half springs the trap and the turn carries the party up; the button in the alcove turns it back out.
local CARRY_ALCOVE = {2125, -4547, -4419}
local CARRY_CORRIDOR = {2560, -4547, -4419}
local function carry(to)
    set("CarryTo", to)
    arm(341, 0.9)
end
handlers[341] = function()
    if not fired(341) then return end
    local p = var("CarryTo") == 1 and CARRY_ALCOVE or CARRY_CORRIDOR
    set("Carried", var("Carried") + 1)
    evt.MoveToMap(p[1], p[2], p[3], 0, 0, 0, 0, 0)
end
handlers[242] = function()
    if var("PivotTrap") == 1 then return end
    handlers[239]()
    carry(1)
end
handlers[241] = function()   -- PivotButton1
    if var("PivotTrap") == 1 then return end
    handlers[239]()
    carry(2)
end
handlers[240] = function() openGroup("TrapExitDoor1") end   -- TrapExitDoor1

-- The mummies (MummyAwaken.scr): they stand in their coffins (dormant) until an awaken message or a hit; each then wakes the next, at once or at its death (ScriptParams p0). A dead mummy takes no
-- awaken (MM9.receives) and its OnDamage does not fire: a blow that kills a dormant one wakes
-- nothing, so a hit wakes at the next poll, if the mummy lived through it; its OnDeath sends the
-- next one's awaken with p0 1 only (OnDeath DoNothing with p0 0).
local MUMMIES = {[0] = {name = "PetrifiedMummy8", next = 5, onDeath = true}, [1] = {name = "PetrifiedMummy7", next = nil, onDeath = false}, [2] = {name = "PetrifiedMummy13", next = 28, onDeath = true}, [3] = {name = "PetrifiedMummy9", next = 31, onDeath = true}, [4] = {name = "PetrifiedMummy11", next = 29, onDeath = true}, [5] = {name = "PetrifiedMummy14", next = nil, onDeath = false}, [6] = {name = "PetrifiedMummy3", next = nil, onDeath = false}, [7] = {name = "PetrifiedMummy30", next = nil, onDeath = true}, [8] = {name = "PetrifiedMummy31", next = 11, onDeath = true}, [9] = {name = "PetrifiedMummy32", next = nil, onDeath = true}, [10] = {name = "PetrifiedMummy33", next = 7, onDeath = true}, [11] = {name = "PetrifiedMummy34", next = nil, onDeath = true}, [12] = {name = "PetrifiedMummy35", next = 9, onDeath = true}, [13] = {name = "PetrifiedMummy16", next = 14, onDeath = false}, [14] = {name = "PetrifiedMummy17", next = 15, onDeath = false}, [15] = {name = "PetrifiedMummy18", next = 16, onDeath = false}, [16] = {name = "PetrifiedMummy19", next = 17, onDeath = false}, [17] = {name = "PetrifiedMummy20", next = 18, onDeath = false}, [18] = {name = "PetrifiedMummy21", next = 19, onDeath = false}, [19] = {name = "PetrifiedMummy22", next = 20, onDeath = false}, [20] = {name = "PetrifiedMummy23", next = 21, onDeath = false}, [21] = {name = "PetrifiedMummy24", next = 22, onDeath = false}, [22] = {name = "PetrifiedMummy25", next = 23, onDeath = false}, [23] = {name = "PetrifiedMummy26", next = 24, onDeath = false}, [24] = {name = "PetrifiedMummy27", next = 25, onDeath = false}, [25] = {name = "PetrifiedMummy28", next = 26, onDeath = false}, [26] = {name = "PetrifiedMummy29", next = nil, onDeath = false}, [27] = {name = "PetrifiedMummy4", next = 4, onDeath = true}, [28] = {name = "PetrifiedMummy6", next = 32, onDeath = true}, [29] = {name = "PetrifiedMummy5", next = 1, onDeath = true}, [30] = {name = "PetrifiedMummy10", next = 3, onDeath = true}, [31] = {name = "PetrifiedMummy12", next = 0, onDeath = true}, [32] = {name = "PetrifiedMummy15", next = 6, onDeath = true}, [33] = {name = "PetrifiedMummy37", next = nil, onDeath = true}, [34] = {name = "PetrifiedMummy36", next = 33, onDeath = true}, [35] = {name = "PetrifiedMummy2", next = nil, onDeath = false}, [36] = {name = "PetrifiedMummy1", next = nil, onDeath = false}, [37] = {name = "EmbalmedMummy2", next = nil, onDeath = false}, [38] = {name = "EmbalmedMummy1", next = nil, onDeath = false}}
local function wake(index)
    if var("Mummy" .. index) == 1 then return end
    if not MM9.receives("chasmofthedead", MUMMIES[index].name, "awaken", index) then return end
    set("Mummy" .. index, 1)
    set("MummiesAwake", var("MummiesAwake") + 1)
    evt.WakeActor(index)
    local m = MUMMIES[index]
    if m.next ~= nil and not m.onDeath then wake(m.next) end
end
local mummiesHit = {}
handlers[96] = function(context)
    if MUMMIES[context.actorIndex] then mummiesHit[context.actorIndex] = true end
end
handlers[97] = function(context)
    local m = MUMMIES[context.actorIndex]
    if m ~= nil and m.next ~= nil and m.onDeath then wake(m.next) end
end

-- MM9's Trigger volumes: awaken lists, the buried zombies (AutoResurrect.Scr: hidden under the floor until their RESURRECT), the apparitions (Chasm_GhostSpawner.scr: each touched trigger makes the next of the thirteen markers spawn an Apparition, ghost.scr; then the spawner stops), the acid grate.
local function wakeAll(list) for _, index in ipairs(list) do wake(index) end end
local function rise(group)
    evt.SetMonGroupBit(group, MonsterBits.Invisible, false)
    set("ZombiesRisen", var("ZombiesRisen") + 1)
end
local MARKERS = {{2376, 14787, 1720}, {7086, 14950, 901}, {7455, 14623, 1065}, {7086, 12001, 410}, {5366, 9830, 410}, {5038, 7209, 164}, {4260, 2499, -492}, {3932, 2089, -492}, {2908, -1229, -819}, {2253, -1106, -1147}, {1556, 8192, -1802}, {1720, 8602, -2130}, {1434, 13681, -2458}}
local function spawnGhost()
    local k = var("GhostsSpawned") + 1
    if k > #MARKERS then return end
    set("GhostsSpawned", k)
    local p = MARKERS[k]
    evt.SummonMonstersById({monster = 9139, x = p[1], y = p[2], z = p[3], radius = 32, group = 90, count = 1, effect = "mm9:fireblue"})   -- :SpawnCreature: DoClientFX hDummy, SPELL_BLUEFIRE
end
local function grate()
    if var("GrateOpen") == 1 then return end
    set("GrateOpen", 1)
    openGroup("Gratetrap0")
    arm(335, 5.5)
end
handlers[335] = function()
    if not fired(335) then return end
    closeGroup("Gratetrap0")
    set("GrateOpen", 0)
end
local ACID_BOX = {{6943, 16323, -6001}, {7311, 16691, -5427}}
local RIM = {6707, 16507, -5324}
local VOLUMES = {
    {name = "Trigger0", box = {{-8765, 3318, -2867}, {-8110, 3973, -2540}}, rearm = false, run = function() wakeAll({30, 2, 27}) end},
    {name = "Trigger1", box = {{10035, 11141, -5325}, {10691, 11796, -4997}}, rearm = false, run = function() wakeAll({34, 12, 8, 10}) end},
    {name = "Trigger7", box = {{-3400, 7823, -2376}, {-2744, 8479, -2048}}, rearm = false, run = function() wakeAll({36, 35, 38, 37}) end},
    {name = "Trigger2", box = {{1966, 13107, -3932}, {3277, 14418, -3686}}, rearm = false, run = function() rise(60) end},
    {name = "Trigger3", box = {{7127, 13312, -3932}, {7782, 14623, -3686}}, rearm = false, run = function() rise(61) end},
    {name = "Trigger4", box = {{3400, 8315, -3932}, {4710, 9626, -3686}}, rearm = false, run = function() rise(62) end},
    {name = "Trigger5", box = {{1966, -737, -3932}, {3277, 573, -3686}}, rearm = false, run = function() rise(63); set("Trigger6On", 1) end},
    {name = "Trigger6", box = {{573, 3021, -3932}, {3195, 4024, -3686}}, rearm = false, run = function() rise(64) end},
    {name = "Apparition13", box = {{2575, 14822, 934}, {2831, 15078, 1190}}, rearm = false, run = function() spawnGhost() end},
    {name = "Apparition14", box = {{7286, 14495, 356}, {7542, 14751, 612}}, rearm = false, run = function() spawnGhost() end},
    {name = "Apparition15", box = {{1674, 8392, -2355}, {1930, 8648, -2099}}, rearm = false, run = function() spawnGhost() end},
    {name = "Apparition16", box = {{1838, 8965, -2463}, {2094, 9221, -2207}}, rearm = false, run = function() spawnGhost() end},
    {name = "Apparition17", box = {{1797, 13880, -3250}, {2053, 14136, -2994}}, rearm = false, run = function() spawnGhost() end},
    {name = "Apparition18", box = {{7327, 14003, 371}, {7583, 14259, 627}}, rearm = false, run = function() spawnGhost() end},
    {name = "Apparition19", box = {{6630, 11873, 81}, {6886, 12129, 337}}, rearm = false, run = function() spawnGhost() end},
    {name = "Apparition20", box = {{4910, 9375, -205}, {5166, 9631, 51}}, rearm = false, run = function() spawnGhost() end},
    {name = "Apparition21", box = {{4664, 6671, -524}, {4920, 6927, -268}}, rearm = false, run = function() spawnGhost() end},
    {name = "Apparition22", box = {{3886, 1961, -855}, {4142, 2217, -599}}, rearm = false, run = function() spawnGhost() end},
    {name = "Apparition23", box = {{3804, 1715, -928}, {4060, 1971, -672}}, rearm = false, run = function() spawnGhost() end},
    {name = "Apparition24", box = {{2452, -1193, -1423}, {2708, -937, -1167}}, rearm = false, run = function() spawnGhost() end},
    {name = "Apparition25", box = {{1961, -1070, -1485}, {2217, -814, -1229}}, rearm = false, run = function() spawnGhost() end},
    {name = "GratetrapTrigger0", box = {{7004, 16384, -5386}, {7250, 16630, -5304}}, rearm = true, run = function() grate() end},
    {name = "PendulumTrigger1", box = {{-5130, 3922, -1966}, {-4147, 4086, -1802}}, rearm = true, run = function() swing() end},
    {name = "PendulumTrigger2", box = {{-5376, 4168, -1966}, {-4393, 4332, -1802}}, rearm = true, run = function() swing() end}
}
local SPIKE_BOX = {{2340, -4726, -5197}, {2698, -4367, -4915}}
local inside, polls = {}, 0
handlers[300] = function()
    evt.StartTimer(300, seconds(0.25))
    for index in pairs(mummiesHit) do   -- OnDamage WakeUp, for a mummy that lived through the blow
        mummiesHit[index] = nil
        if MM9.actorAlive(index) then wake(index) end
    end
    local x, y, z = evt.GetPartyPosition()
    polls = polls + 1
    for _, v in ipairs(VOLUMES) do
        local armed = var("Done" .. v.name) == 0
        if v.name == "Trigger6" and var("Trigger6On") == 0 then armed = false end
        local now = inBox(v.box, x, y, z)
        if armed and now and not inside[v.name] then
            if not v.rearm then set("Done" .. v.name, 1) end
            v.run()
        end
        inside[v.name] = now
    end
    if polls % 4 == 0 and inBox(SPIKE_BOX, x, y, z) then
        hurt(20); set("PitSpikeHits", var("PitSpikeHits") + 1)
    end
    if inBox(ACID_BOX, x, y, z) and z < -5487 then
        if polls % 4 == 0 then
            evt.DamagePlayer(Players.All, const.Damage.Water, 10)
            set("AcidSeconds", var("AcidSeconds") + 1)
            if var("AcidSeconds") % 3 == 0 then
                evt.StatusText("You claw your way out of the acid.")
                set("AcidLifts", var("AcidLifts") + 1)
                evt.MoveToMap(RIM[1], RIM[2], RIM[3], 0, 0, 0, 0, 0)
            end
        end
    end
end

-- The quest objects are world items (dungeon/pickups.py): the Lich Instructions (447) give key 296;
-- the Crona Kiga's (390) pickup runs CronaKiga.scr's use.
local CK = {13}
handlers[235] = function()   -- CronaKiga.scr, picked up (its CKTrigger awakens PetrifiedMummy16)
    wakeAll(CK)
    if MM9.hasKey(48) == 1 or MM9.hasKey(169) == 1 then return end
    if MM9.hasKey(46) == 1 then MM9.giveKey(48) else MM9.giveKey(169) end
    MM9.giveExperience(10000)
    MM9.playSound("sounds/events/quest.wav")
end

-- Shooter0 (OffRailTrigger.scr, PurpleThingy, DamageAmt 35): fires once at a party that leaves MM9's AI rails; the map's only off-rail footing is the dais under it, a one-shot pad here.
handlers[238] = function()
    if var("DaisShot") == 1 then return end
    set("DaisShot", 1)
    shoot(-9503, 3645, -2294, 35, "Dark", "PurpleThingy")
end

handlers[1] = function()   -- map load: taken objects stay gone, the volumes start polling
    evt.StartTimer(300, seconds(0.25))
end
-- MM9's PerceptionBrushes (dungeon/perception.py): the red glow shows to a party whose Perception reaches the
-- brush's PerceptionValue, checked on load and every 3 s; map Lua turns one off for good with
-- set("HintOff<cog>", 1) (MM9's Off message to the brush).
local HINTS = {[24644] = 8, [24645] = 8, [24646] = 8, [24647] = 8, [24648] = 8, [24649] = 8, [24650] = 8, [24651] = 8, [24652] = 8, [24653] = 8, [24654] = 8, [24655] = 8, [24656] = 8, [24657] = 8, [24658] = 8, [24659] = 8, [24660] = 8, [24663] = 10}
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
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(43, "Chest", handlers[43], "Chest")
RegisterEvent(44, "Chest", handlers[44], "Chest")
RegisterEvent(45, "Chest", handlers[45], "Chest")
RegisterEvent(46, "Chest", handlers[46], "Chest")
RegisterEvent(47, "Chest", handlers[47], "Chest")
RegisterEvent(48, "Chest", handlers[48], "Chest")
RegisterEvent(49, "Chest", handlers[49], "Chest")
RegisterEvent(50, "Chest", handlers[50], "Chest")
RegisterEvent(51, "Chest", handlers[51], "Chest")
RegisterEvent(52, "Chest", handlers[52], "Chest")
RegisterEvent(53, "Chest", handlers[53], "Chest")
RegisterEvent(54, "Chest", handlers[54], "Chest")
RegisterEvent(55, "Chest", handlers[55], "Chest")
RegisterEvent(56, "Chest", handlers[56], "Chest")
RegisterEvent(200, "ShooterPlate1", handlers[200])
RegisterMapTimerEvent(301, seconds(3), handlers[301], "ShooterPlate1 reset", "", seconds(3))
RegisterEvent(201, "ShooterPlate2", handlers[201])
RegisterMapTimerEvent(302, seconds(3), handlers[302], "ShooterPlate2 reset", "", seconds(3))
RegisterEvent(202, "ShooterPlate3", handlers[202])
RegisterMapTimerEvent(303, seconds(3), handlers[303], "ShooterPlate3 reset", "", seconds(3))
RegisterEvent(203, "ShooterPlate4", handlers[203])
RegisterMapTimerEvent(304, seconds(3), handlers[304], "ShooterPlate4 reset", "", seconds(3))
RegisterEvent(204, "ShooterPlate5", handlers[204])
RegisterMapTimerEvent(305, seconds(3), handlers[305], "ShooterPlate5 reset", "", seconds(3))
RegisterEvent(205, "ShooterPlate6", handlers[205])
RegisterMapTimerEvent(306, seconds(3), handlers[306], "ShooterPlate6 reset", "", seconds(3))
RegisterEvent(206, "ShooterPlate7", handlers[206])
RegisterMapTimerEvent(307, seconds(3), handlers[307], "ShooterPlate7 reset", "", seconds(3))
RegisterEvent(207, "ShooterPlate8", handlers[207])
RegisterMapTimerEvent(308, seconds(3), handlers[308], "ShooterPlate8 reset", "", seconds(3))
RegisterEvent(208, "ShooterPlate9", handlers[208])
RegisterMapTimerEvent(309, seconds(3), handlers[309], "ShooterPlate9 reset", "", seconds(3))
RegisterEvent(209, "ShooterPlate10", handlers[209])
RegisterMapTimerEvent(310, seconds(3), handlers[310], "ShooterPlate10 reset", "", seconds(3))
RegisterEvent(220, "HSP1", handlers[220])
RegisterMapTimerEvent(320, seconds(3), handlers[320], "HSP1 reset", "", seconds(3))
RegisterEvent(221, "HSP2", handlers[221])
RegisterMapTimerEvent(321, seconds(3), handlers[321], "HSP2 reset", "", seconds(3))
RegisterEvent(222, "HSP6", handlers[222])
RegisterMapTimerEvent(322, seconds(3), handlers[322], "HSP6 reset", "", seconds(3))
RegisterEvent(223, "HSP7", handlers[223])
RegisterMapTimerEvent(323, seconds(3), handlers[323], "HSP7 reset", "", seconds(3))
RegisterEvent(230, "CWPlate1", handlers[230])
RegisterMapTimerEvent(330, seconds(3), handlers[330], "Walls strike", "", seconds(3))
RegisterMapTimerEvent(331, seconds(3), handlers[331], "Walls open", "", seconds(3))
RegisterEvent(231, "SpikeRowPlate1", handlers[231])
RegisterMapTimerEvent(332, seconds(3), handlers[332], "Spike wave", "", seconds(3))
RegisterEvent(236, "CeilingCrushPlate3", handlers[236])
RegisterMapTimerEvent(336, seconds(3), handlers[336], "CeilingCrush3 strike", "", seconds(3))
RegisterMapTimerEvent(337, seconds(3), handlers[337], "CeilingCrush3 rise", "", seconds(3))
RegisterEvent(237, "CeilingCrushPlate4", handlers[237])
RegisterMapTimerEvent(338, seconds(3), handlers[338], "CeilingCrush4 strike", "", seconds(3))
RegisterMapTimerEvent(339, seconds(3), handlers[339], "CeilingCrush4 rise", "", seconds(3))
RegisterEvent(233, "Pendulum", handlers[233])
RegisterMapTimerEvent(333, seconds(3), handlers[333], "Pendulum strike", "", seconds(3))
RegisterMapTimerEvent(334, seconds(3), handlers[334], "Pendulum rises", "", seconds(3))
RegisterEvent(232, "Panel", handlers[232], "Panel")
RegisterEvent(239, "Pivot trap", handlers[239])
RegisterMapTimerEvent(340, seconds(3), handlers[340], "Pivot trap reset", "", seconds(3))
RegisterMapTimerEvent(341, seconds(3), handlers[341], "Pivot carry", "", seconds(3))
RegisterEvent(242, "Pit west", handlers[242])
RegisterEvent(241, "PivotButton1", handlers[241], "Button")
RegisterEvent(240, "TrapExitDoor1", handlers[240], "Hatch")
RegisterMapTimerEvent(300, seconds(3), handlers[300], "Trigger volumes", "", seconds(3))
RegisterMapTimerEvent(335, seconds(3), handlers[335], "Grate shuts", "", seconds(3))
RegisterEvent(235, "Crona Kiga", handlers[235])
RegisterEvent(238, "Dais shooter", handlers[238])
RegisterEvent(1, "Map load", handlers[1])
RegisterMapTimerEvent(901, seconds(3), handlers[901], "Perception hints", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
RegisterMonsterDamageHook(96, "Mummy wakes", handlers[96])
RegisterMonsterKilledHook(97, "Mummy chain", handlers[97])
