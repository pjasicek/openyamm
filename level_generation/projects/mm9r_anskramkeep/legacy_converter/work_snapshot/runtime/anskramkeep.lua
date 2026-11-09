-- Anskram Keep, MM9 rework (level_generation/projects/mm9r_anskramkeep/convert.py writes this file).
-- MM9's doors, plates, crushers, levers, gate, cages, Imp gates and Giant Imp as native events; every
-- door, pad and decoration is named by its DAT object (see work/content.json and README.md).
local handlers = {}
local DOORS = {CeilingCrush1 = 1, CeilingCrush2 = 2, CeilingCrush3 = 3, CeilingCrushPlate1 = 4, CeilingCrushPlate2 = 5, CeilingCrushPlate3 = 6, CritterBreakOut0 = 7, CritterBreakOut1 = 8, DoubleDoorL1 = 9, DoubleDoorL10 = 11, DoubleDoorL11 = 13, DoubleDoorL12 = 15, DoubleDoorL13 = 17, DoubleDoorL14 = 19, DoubleDoorL15 = 21, DoubleDoorL16 = 23, DoubleDoorL17 = 25, DoubleDoorL18 = 27, DoubleDoorL19 = 29, DoubleDoorL2 = 31, DoubleDoorL20 = 33, DoubleDoorL21 = 35, DoubleDoorL22 = 37, DoubleDoorL23 = 39, DoubleDoorL24 = 41, DoubleDoorL25 = 43, DoubleDoorL26 = 45, DoubleDoorL27 = 47, DoubleDoorL28 = 49, DoubleDoorL3 = 51, DoubleDoorL4 = 53, DoubleDoorL5 = 55, DoubleDoorL6 = 57, DoubleDoorL7 = 59, DoubleDoorL8 = 61, DoubleDoorL9 = 63, DoubleDoorR1 = 10, DoubleDoorR10 = 12, DoubleDoorR11 = 14, DoubleDoorR12 = 16, DoubleDoorR13 = 18, DoubleDoorR14 = 20, DoubleDoorR15 = 22, DoubleDoorR16 = 24, DoubleDoorR17 = 26, DoubleDoorR18 = 28, DoubleDoorR19 = 30, DoubleDoorR2 = 32, DoubleDoorR20 = 34, DoubleDoorR21 = 36, DoubleDoorR22 = 38, DoubleDoorR23 = 40, DoubleDoorR24 = 42, DoubleDoorR25 = 44, DoubleDoorR26 = 46, DoubleDoorR27 = 48, DoubleDoorR28 = 50, DoubleDoorR3 = 52, DoubleDoorR4 = 54, DoubleDoorR5 = 56, DoubleDoorR6 = 58, DoubleDoorR7 = 60, DoubleDoorR8 = 62, DoubleDoorR9 = 64, ExitStairs = 65, Innerdoor0 = 66, Innerdoor1 = 67, LeverPanel = 68, LeverPanel0 = 69, Outerdoor0 = 70, Outerdoor1 = 71, PanelLever = 72, PivotButton1 = 73, PivotButton2 = 74, PivotButton3 = 75, PivotTreasurePanel1 = 76, PivotWallTrap1 = 77, PivotWallTrap2 = 78, PivotWallTrap3 = 79, RoundDoorLeft0 = 81, RoundDoorLeft1 = 83, RoundDoorLeft2 = 85, RoundDoorLeft3 = 87, RoundDoorRight0 = 80, RoundDoorRight1 = 82, RoundDoorRight2 = 84, RoundDoorRight3 = 86, ShooterPlate10 = 88, ShooterPlate5 = 89, ShooterPlate6 = 90, ShooterPlate7 = 91, ShooterPlate8 = 92, ShooterPlate9 = 93, Switch0 = 94, Switch1 = 95, SwitchLever0 = 96, TrapExitDoor1 = 97, TrapExitDoor2 = 98, TrapExitDoor3 = 99}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function hidden(group, state) evt.SetMonGroupBit(group, MonsterBits.Invisible, state) end
local function seconds(n) return n * 30 end
-- A Shooter sits inside its wall or ceiling: the bolt starts a third of the way from it to the party's
-- chest (at least 64 units out), inside the room.
local function shoot(sx, sy, sz, damage)
    local x, y, z = evt.GetPartyPosition()
    z = z + 100
    local dx, dy, dz = x - sx, y - sy, z - sz
    local length = math.max(1, math.sqrt(dx * dx + dy * dy + dz * dz))
    local k = math.max(64 / length, 0.33)
    local fired = evt.FireMissile("Fire", sx + dx * k, sy + dy * k, sz + dz * k, x, y, z, damage, "Fire", 0)
    set("ShotsFired", var("ShotsFired") + (fired and 1 or 0))
end

SetMapMetadata({onLoad = {1}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}, [44] = {3}, [45] = {4}, [46] = {5}, [47] = {6}}})

-- Doors: each MM9 door group opens and closes on a click (the gate's leaves open only by its switches).
handlers[101] = function() evt.SetDoorState(9, DoorAction.Trigger) evt.SetDoorState(10, DoorAction.Trigger) end   -- DoubleDoor1
handlers[102] = function() evt.SetDoorState(11, DoorAction.Trigger) evt.SetDoorState(12, DoorAction.Trigger) end   -- DoubleDoor10
handlers[103] = function() evt.SetDoorState(13, DoorAction.Trigger) evt.SetDoorState(14, DoorAction.Trigger) end   -- DoubleDoor11
handlers[104] = function() evt.SetDoorState(15, DoorAction.Trigger) evt.SetDoorState(16, DoorAction.Trigger) end   -- DoubleDoor12
handlers[105] = function() evt.SetDoorState(17, DoorAction.Trigger) evt.SetDoorState(18, DoorAction.Trigger) end   -- DoubleDoor13
handlers[106] = function() evt.SetDoorState(19, DoorAction.Trigger) evt.SetDoorState(20, DoorAction.Trigger) end   -- DoubleDoor14
handlers[107] = function() evt.SetDoorState(21, DoorAction.Trigger) evt.SetDoorState(22, DoorAction.Trigger) end   -- DoubleDoor15
handlers[108] = function() evt.SetDoorState(23, DoorAction.Trigger) evt.SetDoorState(24, DoorAction.Trigger) end   -- DoubleDoor16
handlers[109] = function() evt.SetDoorState(25, DoorAction.Trigger) evt.SetDoorState(26, DoorAction.Trigger) end   -- DoubleDoor17
handlers[110] = function() evt.SetDoorState(27, DoorAction.Trigger) evt.SetDoorState(28, DoorAction.Trigger) end   -- DoubleDoor18
handlers[111] = function() evt.SetDoorState(29, DoorAction.Trigger) evt.SetDoorState(30, DoorAction.Trigger) end   -- DoubleDoor19
handlers[112] = function() evt.SetDoorState(31, DoorAction.Trigger) evt.SetDoorState(32, DoorAction.Trigger) end   -- DoubleDoor2
handlers[113] = function() evt.SetDoorState(33, DoorAction.Trigger) evt.SetDoorState(34, DoorAction.Trigger) end   -- DoubleDoor20
handlers[114] = function() evt.SetDoorState(35, DoorAction.Trigger) evt.SetDoorState(36, DoorAction.Trigger) end   -- DoubleDoor21
handlers[115] = function() evt.SetDoorState(37, DoorAction.Trigger) evt.SetDoorState(38, DoorAction.Trigger) end   -- DoubleDoor22
handlers[116] = function() evt.SetDoorState(39, DoorAction.Trigger) evt.SetDoorState(40, DoorAction.Trigger) end   -- DoubleDoor23
handlers[117] = function() evt.SetDoorState(41, DoorAction.Trigger) evt.SetDoorState(42, DoorAction.Trigger) end   -- DoubleDoor24
handlers[118] = function() evt.SetDoorState(43, DoorAction.Trigger) evt.SetDoorState(44, DoorAction.Trigger) end   -- DoubleDoor25
handlers[119] = function() evt.SetDoorState(45, DoorAction.Trigger) evt.SetDoorState(46, DoorAction.Trigger) end   -- DoubleDoor26
handlers[120] = function() evt.SetDoorState(47, DoorAction.Trigger) evt.SetDoorState(48, DoorAction.Trigger) end   -- DoubleDoor27
handlers[121] = function() evt.SetDoorState(49, DoorAction.Trigger) evt.SetDoorState(50, DoorAction.Trigger) end   -- DoubleDoor28
handlers[122] = function() evt.SetDoorState(51, DoorAction.Trigger) evt.SetDoorState(52, DoorAction.Trigger) end   -- DoubleDoor3
handlers[123] = function() evt.SetDoorState(53, DoorAction.Trigger) evt.SetDoorState(54, DoorAction.Trigger) end   -- DoubleDoor4
handlers[124] = function() evt.SetDoorState(55, DoorAction.Trigger) evt.SetDoorState(56, DoorAction.Trigger) end   -- DoubleDoor5
handlers[125] = function() evt.SetDoorState(57, DoorAction.Trigger) evt.SetDoorState(58, DoorAction.Trigger) end   -- DoubleDoor6
handlers[126] = function() evt.SetDoorState(59, DoorAction.Trigger) evt.SetDoorState(60, DoorAction.Trigger) end   -- DoubleDoor7
handlers[127] = function() evt.SetDoorState(61, DoorAction.Trigger) evt.SetDoorState(62, DoorAction.Trigger) end   -- DoubleDoor8
handlers[128] = function() evt.SetDoorState(63, DoorAction.Trigger) evt.SetDoorState(64, DoorAction.Trigger) end   -- DoubleDoor9
handlers[129] = function() evt.SetDoorState(80, DoorAction.Trigger) evt.SetDoorState(81, DoorAction.Trigger) end   -- RoundDoor0
handlers[130] = function() evt.SetDoorState(82, DoorAction.Trigger) evt.SetDoorState(83, DoorAction.Trigger) end   -- RoundDoor1
handlers[131] = function() evt.SetDoorState(84, DoorAction.Trigger) evt.SetDoorState(85, DoorAction.Trigger) end   -- RoundDoor2
handlers[132] = function() evt.SetDoorState(86, DoorAction.Trigger) evt.SetDoorState(87, DoorAction.Trigger) end   -- RoundDoor3

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest1
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest0
handlers[43] = function() evt.OpenChest(2) end   -- TreasureChest2
handlers[44] = function() evt.OpenChest(3) end   -- TreasureChest3
handlers[45] = function() evt.OpenChest(4) end   -- TreasureChest4
handlers[46] = function() evt.OpenChest(5) end   -- TreasureChest5
handlers[47] = function() evt.OpenChest(6) end   -- TreasureChest6

-- Shooter plates: the plate sinks and its Shooter fires a fire bolt at the party (MM9 FireBolt, DamageAmt); the plate rises after 3 s (CloseWaitTime).
handlers[60] = function()   -- ShooterPlate5 -> Shooter5
    if var("ShooterPlate5") == 1 then return end
    set("ShooterPlate5", 1)
    open("ShooterPlate5")
    shoot(-2790, 5875, -317, 5)
    evt.StartTimer(150, seconds(3))
end
handlers[150] = function() evt.StopTimer(150); close("ShooterPlate5"); set("ShooterPlate5", 0) end
handlers[61] = function()   -- ShooterPlate6 -> Shooter6
    if var("ShooterPlate6") == 1 then return end
    set("ShooterPlate6", 1)
    open("ShooterPlate6")
    shoot(-3909, 4756, -317, 5)
    evt.StartTimer(151, seconds(3))
end
handlers[151] = function() evt.StopTimer(151); close("ShooterPlate6"); set("ShooterPlate6", 0) end
handlers[62] = function()   -- ShooterPlate7 -> Shooter7
    if var("ShooterPlate7") == 1 then return end
    set("ShooterPlate7", 1)
    open("ShooterPlate7")
    shoot(-1899, 5340, -317, 5)
    evt.StartTimer(152, seconds(3))
end
handlers[152] = function() evt.StopTimer(152); close("ShooterPlate7"); set("ShooterPlate7", 0) end
handlers[63] = function()   -- ShooterPlate8 -> Shooter8
    if var("ShooterPlate8") == 1 then return end
    set("ShooterPlate8", 1)
    open("ShooterPlate8")
    shoot(-3374, 3865, -317, 5)
    evt.StartTimer(153, seconds(3))
end
handlers[153] = function() evt.StopTimer(153); close("ShooterPlate8"); set("ShooterPlate8", 0) end
handlers[64] = function()   -- ShooterPlate9 -> CeilingShooter1
    if var("ShooterPlate9") == 1 then return end
    set("ShooterPlate9", 1)
    open("ShooterPlate9")
    shoot(-1597, 9011, 59, 10)
    evt.StartTimer(154, seconds(3))
end
handlers[154] = function() evt.StopTimer(154); close("ShooterPlate9"); set("ShooterPlate9", 0) end
handlers[65] = function()   -- ShooterPlate10 -> CeilingShooter0
    if var("ShooterPlate10") == 1 then return end
    set("ShooterPlate10", 1)
    open("ShooterPlate10")
    shoot(1597, 9011, 59, 10)
    evt.StartTimer(155, seconds(3))
end
handlers[155] = function() evt.StopTimer(155); close("ShooterPlate10"); set("ShooterPlate10", 0) end

-- Ceiling crushers: the plate sinks, the crusher drops (MM9 Speed 300, MoveDist 176), its spikes hurt a party under it (20, MM9 Spikes18-20), and it rises after 3 s.
handlers[66] = function()   -- CeilingCrushPlate1 -> CeilingCrush1
    if var("CeilingCrush1") == 1 then return end
    set("CeilingCrush1", 1)
    open("CeilingCrushPlate1")
    open("CeilingCrush1")
    evt.StartTimer(156, seconds(0.7))
end
handlers[156] = function()
    evt.StopTimer(156)
    if var("CeilingCrush1") ~= 1 then return end
    local x, y = evt.GetPartyPosition()
    if x >= 4219 and x <= 4627 and y >= 2991 and y <= 3562 then evt.DamagePlayer(Players.All, const.Damage.Physical, 20); set("CrushHits", var("CrushHits") + 1) end
    evt.StartTimer(157, seconds(2.3))
end
handlers[157] = function() evt.StopTimer(157); close("CeilingCrush1"); close("CeilingCrushPlate1"); set("CeilingCrush1", 0) end
handlers[67] = function()   -- CeilingCrushPlate2 -> CeilingCrush2
    if var("CeilingCrush2") == 1 then return end
    set("CeilingCrush2", 1)
    open("CeilingCrushPlate2")
    open("CeilingCrush2")
    evt.StartTimer(158, seconds(0.7))
end
handlers[158] = function()
    evt.StopTimer(158)
    if var("CeilingCrush2") ~= 1 then return end
    local x, y = evt.GetPartyPosition()
    if x >= -4084 and x <= -3185 and y >= 2468 and y <= 3368 then evt.DamagePlayer(Players.All, const.Damage.Physical, 20); set("CrushHits", var("CrushHits") + 1) end
    evt.StartTimer(159, seconds(2.3))
end
handlers[159] = function() evt.StopTimer(159); close("CeilingCrush2"); close("CeilingCrushPlate2"); set("CeilingCrush2", 0) end
handlers[68] = function()   -- CeilingCrushPlate3 -> CeilingCrush3
    if var("CeilingCrush3") == 1 then return end
    set("CeilingCrush3", 1)
    open("CeilingCrushPlate3")
    open("CeilingCrush3")
    evt.StartTimer(160, seconds(0.7))
end
handlers[160] = function()
    evt.StopTimer(160)
    if var("CeilingCrush3") ~= 1 then return end
    local x, y = evt.GetPartyPosition()
    if x >= -1734 and x <= -835 and y >= 180 and y <= 1079 then evt.DamagePlayer(Players.All, const.Damage.Physical, 20); set("CrushHits", var("CrushHits") + 1) end
    evt.StartTimer(161, seconds(2.3))
end
handlers[161] = function() evt.StopTimer(161); close("CeilingCrush3"); close("CeilingCrushPlate3"); set("CeilingCrush3", 0) end

-- The treasure panel beside PivotWallTrap1 slides up (MM9 Sticky, PushOpen) to show TreasureChest1.
handlers[70] = function() open("PivotTreasurePanel1") end

-- Pivot traps: the cross turns 90 degrees and tips the party into the pit; MM9's CloseWaitTime turns it back
-- (the mover's auto-close), then it is armed again. A ladder climbs to the hatch beside it.
handlers[77] = function()   -- PivotWallTrap1
    if var("PivotWallTrap1") == 1 then return end
    set("PivotWallTrap1", 1)
    open("PivotWallTrap1")
    open("PivotButton1")
    evt.StartTimer(162, seconds(8))
end
handlers[162] = function() evt.StopTimer(162); close("PivotButton1"); set("PivotWallTrap1", 0) end
handlers[83] = function() handlers[77]() end   -- PivotButton1
handlers[80] = function() open("TrapExitDoor1") end   -- TrapExitDoor1
handlers[78] = function()   -- PivotWallTrap2
    if var("PivotWallTrap2") == 1 then return end
    set("PivotWallTrap2", 1)
    open("PivotWallTrap2")
    open("PivotButton2")
    evt.StartTimer(163, seconds(8))
end
handlers[163] = function() evt.StopTimer(163); close("PivotButton2"); set("PivotWallTrap2", 0) end
handlers[84] = function() handlers[78]() end   -- PivotButton2
handlers[81] = function() open("TrapExitDoor2") end   -- TrapExitDoor2
handlers[79] = function()   -- PivotWallTrap3
    if var("PivotWallTrap3") == 1 then return end
    set("PivotWallTrap3", 1)
    open("PivotWallTrap3")
    open("PivotButton3")
    evt.StartTimer(164, seconds(8))
end
handlers[164] = function() evt.StopTimer(164); close("PivotButton3"); set("PivotWallTrap3", 0) end
handlers[85] = function() handlers[79]() end   -- PivotButton3
handlers[82] = function() open("TrapExitDoor3") end   -- TrapExitDoor3
handlers[86] = function() evt.DamagePlayer(Players.All, const.Damage.Physical, 20); set("SpikeHits", var("SpikeHits") + 1) end   -- Spikes14
handlers[87] = function() evt.DamagePlayer(Players.All, const.Damage.Physical, 20); set("SpikeHits", var("SpikeHits") + 1) end   -- Spikes16
handlers[88] = function() evt.DamagePlayer(Players.All, const.Damage.Physical, 20); set("SpikeHits", var("SpikeHits") + 1) end   -- Spikes17

-- The gate is an airlock: the outer leaves stand apart (built shut, starting open) and the inner ones shut.
-- SwitchLever0 slides LeverPanel and LeverPanel0 aside, PanelLever unlocks Switch0 and Switch1, and either
-- switch shuts the outer gate and opens the inner one (MM9: one after the other), or the reverse.
handlers[71] = function()
    if var("SwitchLever0") == 1 then return end
    set("SwitchLever0", 1)
    open("SwitchLever0"); open("LeverPanel"); open("LeverPanel0")
end
handlers[72] = function()
    if var("PanelLever") == 1 then return end
    set("PanelLever", 1)
    open("PanelLever")
end
local function gateSwitch(name)
    if var("PanelLever") == 0 then evt.StatusText("The switch is locked.") return end
    if var("Gate") == 0 then
        set("Gate", 1)
        open("Switch0"); open("Switch1")
        close("Outerdoor0"); close("Outerdoor1"); open("Innerdoor0"); open("Innerdoor1")
    else
        set("Gate", 0)
        close("Switch0"); close("Switch1")
        open("Outerdoor0"); open("Outerdoor1"); close("Innerdoor0"); close("Innerdoor1")
    end
end
handlers[73] = function() gateSwitch("Switch0") end
handlers[74] = function() gateSwitch("Switch1") end

-- The cages: stepping near them breaks the walls (CritterBreakOut0/1 sink into the floor and wall) and the
-- caged Nagate Hatchlings and Airborne Ickies (KingKong.scr) come out.
handlers[75] = function() if var("TriggerNagateBust") == 0 then set("TriggerNagateBust", 1); open("CritterBreakOut0") end end
handlers[76] = function() if var("TriggerIckyBust") == 0 then set("TriggerIckyBust", 1); open("CritterBreakOut1") end end

-- The Imp gates (AK_ImpGate.scr on ImpGateSpawner0-7): a touch trigger starts its gate; it sends 5 Imps one
-- after another, each when the last is dead; then its fire goes out. When all eight are out, the Giant Imp
-- (AK_GiantImp.scr) and its two guards (AK_GiantImpGuard.scr, friends of the party) appear when the party
-- crosses TriggerGiantImp in the north hall. Gate states: 0 waiting, 1 sending, 2 done.
local GATES = {
    [0] = {position = {2565, 11315, -492}, count = 5},   -- ImpGateSpawner0, ImpGateFire0
    [1] = {position = {1444, 9446, -492}, count = 5},   -- ImpGateSpawner1, ImpGateFire1
    [2] = {position = {-1464, 9446, -492}, count = 5},   -- ImpGateSpawner2, ImpGateFire2
    [3] = {position = {-2565, 11131, -492}, count = 5},   -- ImpGateSpawner3, ImpGateFire3
    [4] = {position = {5842, 8591, -492}, count = 5},   -- ImpGateSpawner4, ImpGateFire4
    [5] = {position = {5842, 4147, -492}, count = 5},   -- ImpGateSpawner5, ImpGateFire5
    [6] = {position = {-5842, 2161, -492}, count = 5},   -- ImpGateSpawner6, ImpGateFire6
    [7] = {position = {-5842, 7404, -492}, count = 5},   -- ImpGateSpawner7, ImpGateFire7
}
local function sendImp(k)
    local gate = GATES[k]
    local sent = evt.SummonMonstersById({monster = 9079, x = gate.position[1], y = gate.position[2], z = gate.position[3], radius = 64, group = 60 + k, count = 1})
    set("ImpsSummoned", var("ImpsSummoned") + sent)
    set("ImpGateSent" .. k, var("ImpGateSent" .. k) + 1)
end
local function startGate(k)
    if var("ImpGate" .. k) ~= 0 then return end
    set("ImpGate" .. k, 1)
    sendImp(k)
end
handlers[170] = function() startGate(4) end   -- TriggerBarrackGate0 -> ImpGateSpawner4
handlers[171] = function() startGate(4) end   -- TriggerBarrackGate1 -> ImpGateSpawner4
handlers[172] = function() startGate(5) end   -- TriggerBarrackGate2 -> ImpGateSpawner5
handlers[173] = function() startGate(5) end   -- TriggerBarrackGate3 -> ImpGateSpawner5
handlers[174] = function() startGate(6) end   -- TriggerBarrackGate4 -> ImpGateSpawner6
handlers[175] = function() startGate(6) end   -- TriggerBarrackGate5 -> ImpGateSpawner6
handlers[176] = function() startGate(7) end   -- TriggerBarrackGate6 -> ImpGateSpawner7
handlers[177] = function() startGate(7) end   -- TriggerBarrackGate7 -> ImpGateSpawner7
handlers[178] = function() startGate(0) end   -- TriggerClosetGate0 -> ImpGateSpawner0
handlers[179] = function() startGate(2) end   -- TriggerClosetGate2 -> ImpGateSpawner2
handlers[180] = function() startGate(3) end   -- TriggerClosetGate3 -> ImpGateSpawner3
handlers[181] = function() startGate(1) end   -- TriggerClosetGate1 -> ImpGateSpawner1
handlers[182] = function() startGate(5) end   -- TriggerBarrackGate8 -> ImpGateSpawner5
handlers[183] = function() startGate(4) end   -- TriggerBarrackGate9 -> ImpGateSpawner4
handlers[95] = function()   -- any monster killed
    for k = 0, 7 do
        if var("ImpGate" .. k) == 1 and evt.CheckMonstersKilled(ActorKillCheck.Group, 60 + k, 0, false) then
            if var("ImpGateSent" .. k) < GATES[k].count then
                sendImp(k)
            else
                set("ImpGate" .. k, 2)
                evt.SetSprite(200 + k, false)
                set("ImpGatesDone", var("ImpGatesDone") + 1)
            end
        end
    end
end
handlers[90] = function()   -- TriggerGiantImp
    if var("GiantImp") == 1 or var("ImpGatesDone") < 8 then return end
    set("GiantImp", 1)
    hidden(51, false)
    hidden(52, false)
end
handlers[1] = function()   -- map load: fires of the finished gates stay out
    for k = 0, 7 do
        if var("ImpGate" .. k) == 2 then evt.SetSprite(200 + k, false) end
    end
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
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(43, "Chest", handlers[43], "Chest")
RegisterEvent(44, "Chest", handlers[44], "Chest")
RegisterEvent(45, "Chest", handlers[45], "Chest")
RegisterEvent(46, "Chest", handlers[46], "Chest")
RegisterEvent(47, "Chest", handlers[47], "Chest")
RegisterEvent(60, "ShooterPlate5", handlers[60], "ShooterPlate5")
RegisterMapTimerEvent(150, seconds(3), handlers[150], "ShooterPlate5 reset", "", seconds(3))
RegisterEvent(61, "ShooterPlate6", handlers[61], "ShooterPlate6")
RegisterMapTimerEvent(151, seconds(3), handlers[151], "ShooterPlate6 reset", "", seconds(3))
RegisterEvent(62, "ShooterPlate7", handlers[62], "ShooterPlate7")
RegisterMapTimerEvent(152, seconds(3), handlers[152], "ShooterPlate7 reset", "", seconds(3))
RegisterEvent(63, "ShooterPlate8", handlers[63], "ShooterPlate8")
RegisterMapTimerEvent(153, seconds(3), handlers[153], "ShooterPlate8 reset", "", seconds(3))
RegisterEvent(64, "ShooterPlate9", handlers[64], "ShooterPlate9")
RegisterMapTimerEvent(154, seconds(3), handlers[154], "ShooterPlate9 reset", "", seconds(3))
RegisterEvent(65, "ShooterPlate10", handlers[65], "ShooterPlate10")
RegisterMapTimerEvent(155, seconds(3), handlers[155], "ShooterPlate10 reset", "", seconds(3))
RegisterEvent(66, "CeilingCrushPlate1", handlers[66], "CeilingCrushPlate1")
RegisterMapTimerEvent(156, seconds(3), handlers[156], "CeilingCrush1 strike", "", seconds(3))
RegisterMapTimerEvent(157, seconds(3), handlers[157], "CeilingCrush1 rise", "", seconds(3))
RegisterEvent(67, "CeilingCrushPlate2", handlers[67], "CeilingCrushPlate2")
RegisterMapTimerEvent(158, seconds(3), handlers[158], "CeilingCrush2 strike", "", seconds(3))
RegisterMapTimerEvent(159, seconds(3), handlers[159], "CeilingCrush2 rise", "", seconds(3))
RegisterEvent(68, "CeilingCrushPlate3", handlers[68], "CeilingCrushPlate3")
RegisterMapTimerEvent(160, seconds(3), handlers[160], "CeilingCrush3 strike", "", seconds(3))
RegisterMapTimerEvent(161, seconds(3), handlers[161], "CeilingCrush3 rise", "", seconds(3))
RegisterEvent(77, "PivotWallTrap1", handlers[77])
RegisterMapTimerEvent(162, seconds(3), handlers[162], "PivotWallTrap1 reset", "", seconds(3))
RegisterEvent(83, "PivotButton1", handlers[83], "PivotButton1")
RegisterEvent(80, "TrapExitDoor1", handlers[80], "Hatch")
RegisterEvent(78, "PivotWallTrap2", handlers[78])
RegisterMapTimerEvent(163, seconds(3), handlers[163], "PivotWallTrap2 reset", "", seconds(3))
RegisterEvent(84, "PivotButton2", handlers[84], "PivotButton2")
RegisterEvent(81, "TrapExitDoor2", handlers[81], "Hatch")
RegisterEvent(79, "PivotWallTrap3", handlers[79])
RegisterMapTimerEvent(164, seconds(3), handlers[164], "PivotWallTrap3 reset", "", seconds(3))
RegisterEvent(85, "PivotButton3", handlers[85], "PivotButton3")
RegisterEvent(82, "TrapExitDoor3", handlers[82], "Hatch")
RegisterEvent(86, "Spikes14", handlers[86])
RegisterEvent(87, "Spikes16", handlers[87])
RegisterEvent(88, "Spikes17", handlers[88])
RegisterEvent(70, "Panel", handlers[70], "Panel")
RegisterEvent(71, "Lever", handlers[71], "Lever")
RegisterEvent(72, "Lever", handlers[72], "Lever")
RegisterEvent(73, "Switch", handlers[73], "Switch")
RegisterEvent(74, "Switch", handlers[74], "Switch")
RegisterEvent(75, "TriggerNagateBust", handlers[75])
RegisterEvent(76, "TriggerIckyBust", handlers[76])
RegisterEvent(170, "TriggerBarrackGate0", handlers[170])
RegisterEvent(171, "TriggerBarrackGate1", handlers[171])
RegisterEvent(172, "TriggerBarrackGate2", handlers[172])
RegisterEvent(173, "TriggerBarrackGate3", handlers[173])
RegisterEvent(174, "TriggerBarrackGate4", handlers[174])
RegisterEvent(175, "TriggerBarrackGate5", handlers[175])
RegisterEvent(176, "TriggerBarrackGate6", handlers[176])
RegisterEvent(177, "TriggerBarrackGate7", handlers[177])
RegisterEvent(178, "TriggerClosetGate0", handlers[178])
RegisterEvent(179, "TriggerClosetGate2", handlers[179])
RegisterEvent(180, "TriggerClosetGate3", handlers[180])
RegisterEvent(181, "TriggerClosetGate1", handlers[181])
RegisterEvent(182, "TriggerBarrackGate8", handlers[182])
RegisterEvent(183, "TriggerBarrackGate9", handlers[183])
RegisterEvent(90, "TriggerGiantImp", handlers[90])
RegisterMonsterKilledHook(95, "Imp gates", handlers[95])
RegisterEvent(1, "Map load", handlers[1])
