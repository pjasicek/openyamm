-- Ancient Troll Home
-- generated from legacy EVT/STR

SetMapMetadata({
    levitateTrapFaceMask = 0x08000000,
    onLoad = {1, 2, 3, 4, 5},
    onLeave = {6, 7, 8, 9, 10},
    openedChestIds = {
    [81] = {0},
    [82] = {1},
    [83] = {2},
    [84] = {3},
    [85] = {4},
    [86] = {5},
    [87] = {6},
    [88] = {7},
    [89] = {8},
    [90] = {9},
    [91] = {10},
    [92] = {11},
    [93] = {12},
    [94] = {13},
    [95] = {14},
    [96] = {15},
    [97] = {16},
    [98] = {17},
    [99] = {18},
    [100] = {19},
    },
    contextActions = {
    [10] = { kind = "generic_event", source = "opcode" },
    [11] = { kind = "open_door", source = "title" },
    [12] = { kind = "open_door", source = "title" },
    [13] = { kind = "open_door", source = "title" },
    [14] = { kind = "open_door", source = "title" },
    [15] = { kind = "open_door", source = "title" },
    [16] = { kind = "open_door", source = "title" },
    [17] = { kind = "open_door", source = "title" },
    [18] = { kind = "open_door", source = "title" },
    [19] = { kind = "open_door", source = "title" },
    [20] = { kind = "open_door", source = "title" },
    [21] = { kind = "open_door", source = "title" },
    [22] = { kind = "open_door", source = "title" },
    [23] = { kind = "open_door", source = "title" },
    [24] = { kind = "open_door", source = "title" },
    [25] = { kind = "open_door", source = "title" },
    [26] = { kind = "open_door", source = "title" },
    [27] = { kind = "open_door", source = "title" },
    [28] = { kind = "open_door", source = "title" },
    [29] = { kind = "open_door", source = "title" },
    [30] = { kind = "open_door", source = "title" },
    [31] = { kind = "open_door", source = "title" },
    [32] = { kind = "open_door", source = "title" },
    [33] = { kind = "open_door", source = "title" },
    [34] = { kind = "open_door", source = "title" },
    [35] = { kind = "open_door", source = "title" },
    [36] = { kind = "open_door", source = "title" },
    [37] = { kind = "open_door", source = "title" },
    [38] = { kind = "open_door", source = "title" },
    [39] = { kind = "open_door", source = "title" },
    [40] = { kind = "open_door", source = "title" },
    [41] = { kind = "open_door", source = "title" },
    [42] = { kind = "open_door", source = "title" },
    [43] = { kind = "open_door", source = "title" },
    [44] = { kind = "open_door", source = "title" },
    [45] = { kind = "open_door", source = "title" },
    [46] = { kind = "open_door", source = "title" },
    [47] = { kind = "open_door", source = "title" },
    [48] = { kind = "open_door", source = "title" },
    [49] = { kind = "open_door", source = "title" },
    [50] = { kind = "open_door", source = "title" },
    [51] = { kind = "open_door", source = "title" },
    [52] = { kind = "open_door", source = "title" },
    [53] = { kind = "open_door", source = "title" },
    [54] = { kind = "open_door", source = "title" },
    [55] = { kind = "open_door", source = "title" },
    [56] = { kind = "open_door", source = "title" },
    [57] = { kind = "open_door", source = "title" },
    [58] = { kind = "open_door", source = "title" },
    [59] = { kind = "open_door", source = "title" },
    [60] = { kind = "open_door", source = "title" },
    [81] = { kind = "open_chest", source = "opcode", chestIds = {0} },
    [82] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [83] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [84] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [85] = { kind = "open_chest", source = "opcode", chestIds = {4} },
    [86] = { kind = "open_chest", source = "opcode", chestIds = {5} },
    [87] = { kind = "open_chest", source = "opcode", chestIds = {6} },
    [88] = { kind = "open_chest", source = "opcode", chestIds = {7} },
    [89] = { kind = "open_chest", source = "opcode", chestIds = {8} },
    [90] = { kind = "open_chest", source = "opcode", chestIds = {9} },
    [91] = { kind = "open_chest", source = "opcode", chestIds = {10} },
    [92] = { kind = "open_chest", source = "opcode", chestIds = {11} },
    [93] = { kind = "open_chest", source = "opcode", chestIds = {12} },
    [94] = { kind = "open_chest", source = "opcode", chestIds = {13} },
    [95] = { kind = "open_chest", source = "opcode", chestIds = {14} },
    [96] = { kind = "open_chest", source = "opcode", chestIds = {15} },
    [97] = { kind = "open_chest", source = "opcode", chestIds = {16} },
    [98] = { kind = "open_chest", source = "opcode", chestIds = {17} },
    [99] = { kind = "open_chest", source = "opcode", chestIds = {18} },
    [100] = { kind = "open_chest", source = "opcode", chestIds = {19} },
    [501] = { kind = "leave_dungeon", source = "opcode", targetMap = "out07.odm", targetName = "Murmurwoods" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterNoOpEvent(1, nil)

RegisterNoOpEvent(2, nil)

RegisterNoOpEvent(3, nil)

RegisterNoOpEvent(4, nil)

RegisterNoOpEvent(5, nil)

RegisterNoOpEvent(6, nil)

RegisterNoOpEvent(7, nil)

RegisterNoOpEvent(8, nil)

RegisterNoOpEvent(9, nil)

RegisterEvent(10, nil, function()
    if IsQBitSet(QBit(69)) then return end -- Ancient Troll Homeland Found
    if evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 87, 0, true) and evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 88, 0, true) and evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 89, 0, true) then -- monster 87 "Young Basilisk"; all matching actors defeated
        SetQBit(QBit(69)) -- Ancient Troll Homeland Found
        SetQBit(QBit(225)) -- dead questbit for internal use(bling)
        ClearQBit(QBit(225)) -- dead questbit for internal use(bling)
        evt.StatusText("You have Killed all of the Basilisks in this Ancient Troll Home")
    else
    end
end)

RegisterEvent(11, "Door", function()
    evt.SetDoorState(1, DoorAction.Open)
end, "Door")

RegisterEvent(12, "Door", function()
    evt.SetDoorState(2, DoorAction.Open)
end, "Door")

RegisterEvent(13, "Door", function()
    evt.SetDoorState(3, DoorAction.Open)
end, "Door")

RegisterEvent(14, "Door", function()
    evt.SetDoorState(4, DoorAction.Open)
end, "Door")

RegisterEvent(15, "Door", function()
    evt.SetDoorState(5, DoorAction.Open)
end, "Door")

RegisterEvent(16, "Door", function()
    evt.SetDoorState(6, DoorAction.Open)
end, "Door")

RegisterEvent(17, "Door", function()
    evt.SetDoorState(7, DoorAction.Open)
end, "Door")

RegisterEvent(18, "Door", function()
    evt.SetDoorState(8, DoorAction.Open)
end, "Door")

RegisterEvent(19, "Door", function()
    evt.SetDoorState(9, DoorAction.Open)
end, "Door")

RegisterEvent(20, "Door", function()
    evt.SetDoorState(10, DoorAction.Open)
end, "Door")

RegisterEvent(21, "Door", function()
    evt.SetDoorState(11, DoorAction.Open)
end, "Door")

RegisterEvent(22, "Door", function()
    evt.SetDoorState(12, DoorAction.Open)
end, "Door")

RegisterEvent(23, "Door", function()
    evt.SetDoorState(13, DoorAction.Open)
end, "Door")

RegisterEvent(24, "Door", function()
    evt.SetDoorState(14, DoorAction.Open)
end, "Door")

RegisterEvent(25, "Door", function()
    evt.SetDoorState(15, DoorAction.Open)
end, "Door")

RegisterEvent(26, "Door", function()
    evt.SetDoorState(16, DoorAction.Open)
end, "Door")

RegisterEvent(27, "Door", function()
    evt.SetDoorState(17, DoorAction.Open)
end, "Door")

RegisterEvent(28, "Door", function()
    evt.SetDoorState(18, DoorAction.Open)
end, "Door")

RegisterEvent(29, "Door", function()
    evt.SetDoorState(19, DoorAction.Open)
end, "Door")

RegisterEvent(30, "Door", function()
    evt.SetDoorState(20, DoorAction.Open)
end, "Door")

RegisterEvent(31, "Door", function()
    evt.SetDoorState(21, DoorAction.Open)
end, "Door")

RegisterEvent(32, "Door", function()
    evt.SetDoorState(22, DoorAction.Open)
end, "Door")

RegisterEvent(33, "Door", function()
    evt.SetDoorState(23, DoorAction.Open)
end, "Door")

RegisterEvent(34, "Door", function()
    evt.SetDoorState(24, DoorAction.Open)
end, "Door")

RegisterEvent(35, "Door", function()
    evt.SetDoorState(25, DoorAction.Open)
end, "Door")

RegisterEvent(36, "Door", function()
    evt.SetDoorState(26, DoorAction.Open)
end, "Door")

RegisterEvent(37, "Door", function()
    evt.SetDoorState(27, DoorAction.Open)
end, "Door")

RegisterEvent(38, "Door", function()
    evt.SetDoorState(28, DoorAction.Open)
end, "Door")

RegisterEvent(39, "Door", function()
    evt.SetDoorState(29, DoorAction.Open)
end, "Door")

RegisterEvent(40, "Door", function()
    evt.SetDoorState(30, DoorAction.Open)
end, "Door")

RegisterEvent(41, "Door", function()
    evt.SetDoorState(31, DoorAction.Open)
end, "Door")

RegisterEvent(42, "Door", function()
    evt.SetDoorState(32, DoorAction.Open)
end, "Door")

RegisterEvent(43, "Door", function()
    evt.SetDoorState(33, DoorAction.Open)
end, "Door")

RegisterEvent(44, "Door", function()
    evt.SetDoorState(34, DoorAction.Open)
end, "Door")

RegisterEvent(45, "Door", function()
    evt.SetDoorState(35, DoorAction.Open)
end, "Door")

RegisterEvent(46, "Door", function()
    evt.SetDoorState(36, DoorAction.Open)
end, "Door")

RegisterEvent(47, "Door", function()
    evt.SetDoorState(37, DoorAction.Open)
end, "Door")

RegisterEvent(48, "Door", function()
    evt.SetDoorState(38, DoorAction.Open)
end, "Door")

RegisterEvent(49, "Door", function()
    evt.SetDoorState(39, DoorAction.Open)
end, "Door")

RegisterEvent(50, "Door", function()
    evt.SetDoorState(40, DoorAction.Open)
end, "Door")

RegisterEvent(51, "Door", function()
    evt.SetDoorState(41, DoorAction.Open)
end, "Door")

RegisterEvent(52, "Door", function()
    evt.SetDoorState(42, DoorAction.Open)
end, "Door")

RegisterEvent(53, "Door", function()
    evt.SetDoorState(43, DoorAction.Open)
end, "Door")

RegisterEvent(54, "Door", function()
    evt.SetDoorState(44, DoorAction.Open)
end, "Door")

RegisterEvent(55, "Door", function()
    evt.SetDoorState(45, DoorAction.Open)
end, "Door")

RegisterEvent(56, "Door", function()
    evt.SetDoorState(46, DoorAction.Open)
end, "Door")

RegisterEvent(57, "Door", function()
    evt.SetDoorState(47, DoorAction.Open)
end, "Door")

RegisterEvent(58, "Door", function()
    evt.SetDoorState(48, DoorAction.Open)
end, "Door")

RegisterEvent(59, "Door", function()
    evt.SetDoorState(49, DoorAction.Open)
end, "Door")

RegisterEvent(60, "Door", function()
    evt.SetDoorState(50, DoorAction.Open)
end, "Door")

RegisterEvent(81, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(82, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(83, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(84, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(85, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(86, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(87, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(88, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(89, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(90, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(91, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(92, "Chest", function()
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(93, "Chest", function()
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(94, "Chest", function()
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(95, "Chest", function()
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(96, "Chest", function()
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(97, "Chest", function()
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(98, "Chest", function()
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(99, "Chest", function()
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(100, "Chest", function()
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(501, "Leave the Ancient Troll Home", function()
    evt.MoveToMap(-20346, 480, 187, 0, 0, 0, 0, 1, "out07.odm") -- Murmurwoods
end, "Leave the Ancient Troll Home")

