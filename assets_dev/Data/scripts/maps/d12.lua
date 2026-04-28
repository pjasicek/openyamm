-- Ogre Fortress
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 2, 3, 4, 5},
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
    textureNames = {},
    spriteNames = {},
    castSpellIds = {15},
    timers = {
    },
})

RegisterNoOpEvent(1, "Legacy event 1")

RegisterNoOpEvent(2, "Legacy event 2")

RegisterNoOpEvent(3, "Legacy event 3")

RegisterNoOpEvent(4, "Legacy event 4")

RegisterEvent(5, "Legacy event 5", function()
    evt.SetMonGroupBit(10, MonsterBits.Hostile, 1)
    return
end)

RegisterEvent(6, "Legacy event 6", function()
    if IsQBitSet(QBit(130)) then return end
    if not evt.CheckMonstersKilled(2, 30, 0, false) then return end
    if not evt.CheckMonstersKilled(2, 31, 0, false) then return end
    if not evt.CheckMonstersKilled(2, 32, 0, false) then return end
    if not evt.CheckMonstersKilled(2, 105, 0, false) then return end
    if not evt.CheckMonstersKilled(2, 106, 0, false) then return end
    if not evt.CheckMonstersKilled(2, 107, 0, false) then return end
    SetQBit(QBit(131))
    SetQBit(QBit(130))
    SetQBit(QBit(225))
    ClearQBit(QBit(225))
    evt.StatusText("You have Killed all of the Ogres")
    return
end)

RegisterEvent(7, "Legacy event 7", function()
    if not IsQBitSet(QBit(120)) then return end
    evt.SetMonGroupBit(5, MonsterBits.Invisible, 1)
    return
end)

RegisterNoOpEvent(8, "Legacy event 8")

RegisterNoOpEvent(9, "Legacy event 9")

RegisterNoOpEvent(10, "Legacy event 10")

RegisterEvent(11, "Key Hole", function()
    evt.ForPlayer(Players.All)
    if not HasItem(620) then -- Prison Key
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    end
    evt.SetDoorState(1, 1)
    return
end, "Key Hole")

RegisterEvent(12, "Key Hole", function()
    evt.ForPlayer(Players.All)
    if not HasItem(621) then -- Prison Key
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    end
    evt.SetDoorState(2, 1)
    if evt.CheckMonstersKilled(1, 5, 1, false) then return end
    if IsQBitSet(QBit(120)) then return end
    SetQBit(QBit(120))
    evt.SpeakNPC(285) -- Irabelle Hunter
    return
end, "Key Hole")

RegisterEvent(14, "Button", function()
    evt.SetDoorState(4, 2)
    evt.SetDoorState(3, 2)
    return
end, "Button")

RegisterEvent(15, "Door", function()
    evt.SetDoorState(5, 0)
    return
end, "Door")

RegisterEvent(16, "Door", function()
    evt.SetDoorState(6, 0)
    return
end, "Door")

RegisterEvent(17, "Door", function()
    evt.SetDoorState(7, 0)
    return
end, "Door")

RegisterEvent(18, "Door", function()
    evt.SetDoorState(8, 0)
    return
end, "Door")

RegisterEvent(19, "Door", function()
    evt.SetDoorState(9, 0)
    return
end, "Door")

RegisterEvent(20, "Door", function()
    evt.SetDoorState(10, 0)
    return
end, "Door")

RegisterEvent(21, "Door", function()
    evt.SetDoorState(11, 0)
    return
end, "Door")

RegisterEvent(22, "Door", function()
    evt.SetDoorState(12, 0)
    return
end, "Door")

RegisterEvent(23, "Door", function()
    evt.SetDoorState(13, 0)
    return
end, "Door")

RegisterEvent(24, "Door", function()
    evt.SetDoorState(14, 0)
    return
end, "Door")

RegisterEvent(25, "Door", function()
    evt.SetDoorState(15, 0)
    return
end, "Door")

RegisterEvent(26, "Door", function()
    evt.SetDoorState(16, 0)
    return
end, "Door")

RegisterEvent(27, "Door", function()
    evt.SetDoorState(17, 0)
    return
end, "Door")

RegisterEvent(28, "Door", function()
    evt.SetDoorState(18, 0)
    return
end, "Door")

RegisterEvent(29, "Door", function()
    evt.SetDoorState(19, 0)
    return
end, "Door")

RegisterEvent(30, "Door", function()
    evt.SetDoorState(20, 0)
    return
end, "Door")

RegisterEvent(31, "Door", function()
    evt.SetDoorState(21, 0)
    return
end, "Door")

RegisterEvent(32, "Door", function()
    evt.SetDoorState(22, 0)
    return
end, "Door")

RegisterEvent(33, "Door", function()
    evt.SetDoorState(23, 0)
    return
end, "Door")

RegisterEvent(34, "Door", function()
    evt.SetDoorState(24, 0)
    return
end, "Door")

RegisterEvent(35, "Door", function()
    evt.SetDoorState(25, 0)
    return
end, "Door")

RegisterEvent(36, "Door", function()
    evt.SetDoorState(26, 0)
    return
end, "Door")

RegisterEvent(37, "Door", function()
    evt.SetDoorState(27, 0)
    return
end, "Door")

RegisterEvent(38, "Door", function()
    evt.SetDoorState(28, 0)
    return
end, "Door")

RegisterEvent(39, "Door", function()
    evt.SetDoorState(29, 0)
    return
end, "Door")

RegisterEvent(40, "Door", function()
    evt.SetDoorState(30, 0)
    return
end, "Door")

RegisterEvent(41, "Door", function()
    evt.SetDoorState(31, 0)
    return
end, "Door")

RegisterEvent(42, "Door", function()
    evt.SetDoorState(32, 0)
    return
end, "Door")

RegisterEvent(43, "Door", function()
    evt.SetDoorState(33, 0)
    return
end, "Door")

RegisterEvent(44, "Door", function()
    evt.SetDoorState(34, 0)
    return
end, "Door")

RegisterEvent(45, "Door", function()
    evt.SetDoorState(35, 0)
    return
end, "Door")

RegisterEvent(46, "Door", function()
    evt.SetDoorState(36, 0)
    return
end, "Door")

RegisterEvent(47, "Door", function()
    evt.SetDoorState(37, 0)
    return
end, "Door")

RegisterEvent(48, "Door", function()
    evt.SetDoorState(38, 0)
    return
end, "Door")

RegisterEvent(49, "Door", function()
    evt.SetDoorState(39, 0)
    return
end, "Door")

RegisterEvent(50, "Door", function()
    evt.SetDoorState(40, 0)
    return
end, "Door")

RegisterEvent(51, "Door", function()
    evt.SetDoorState(41, 0)
    return
end, "Door")

RegisterEvent(52, "Door", function()
    evt.SetDoorState(42, 0)
    return
end, "Door")

RegisterEvent(53, "Door", function()
    evt.SetDoorState(43, 0)
    return
end, "Door")

RegisterEvent(54, "Door", function()
    evt.SetDoorState(44, 0)
    return
end, "Door")

RegisterEvent(55, "Door", function()
    evt.SetDoorState(45, 0)
    return
end, "Door")

RegisterEvent(56, "Door", function()
    evt.SetDoorState(46, 0)
    return
end, "Door")

RegisterEvent(57, "Door", function()
    evt.SetDoorState(47, 0)
    return
end, "Door")

RegisterEvent(58, "Door", function()
    evt.SetDoorState(48, 0)
    return
end, "Door")

RegisterEvent(59, "Door", function()
    evt.SetDoorState(49, 0)
    return
end, "Door")

RegisterEvent(60, "Door", function()
    evt.SetDoorState(50, 0)
    return
end, "Door")

RegisterEvent(81, "Chest", function()
    evt.OpenChest(0)
    return
end, "Chest")

RegisterEvent(82, "Chest", function()
    evt.OpenChest(1)
    return
end, "Chest")

RegisterEvent(83, "Chest", function()
    evt.OpenChest(2)
    return
end, "Chest")

RegisterEvent(84, "Chest", function()
    evt.OpenChest(3)
    return
end, "Chest")

RegisterEvent(85, "Chest", function()
    evt.OpenChest(4)
    return
end, "Chest")

RegisterEvent(86, "Chest", function()
    evt.OpenChest(5)
    return
end, "Chest")

RegisterEvent(87, "Chest", function()
    evt.OpenChest(6)
    return
end, "Chest")

RegisterEvent(88, "Chest", function()
    evt.OpenChest(7)
    return
end, "Chest")

RegisterEvent(89, "Chest", function()
    evt.OpenChest(8)
    return
end, "Chest")

RegisterEvent(90, "Chest", function()
    evt.OpenChest(9)
    return
end, "Chest")

RegisterEvent(91, "Chest", function()
    evt.OpenChest(10)
    return
end, "Chest")

RegisterEvent(92, "Chest", function()
    evt.OpenChest(11)
    return
end, "Chest")

RegisterEvent(93, "Chest", function()
    evt.OpenChest(12)
    return
end, "Chest")

RegisterEvent(94, "Chest", function()
    evt.OpenChest(13)
    return
end, "Chest")

RegisterEvent(95, "Chest", function()
    evt.OpenChest(14)
    return
end, "Chest")

RegisterEvent(96, "Chest", function()
    evt.OpenChest(15)
    return
end, "Chest")

RegisterEvent(97, "Chest", function()
    evt.OpenChest(16)
    return
end, "Chest")

RegisterEvent(98, "Chest", function()
    evt.OpenChest(17)
    return
end, "Chest")

RegisterEvent(99, "Chest", function()
    evt.OpenChest(18)
    return
end, "Chest")

RegisterEvent(100, "Chest", function()
    evt.OpenChest(19)
    return
end, "Chest")

RegisterEvent(101, "Legacy event 101", function()
    evt.CastSpell(15, 10, 2, -5536, -3216, 1168, -5536, -3216, 544) -- Sparks
    return
end)

RegisterEvent(102, "Legacy event 102", function()
    evt.CastSpell(15, 10, 2, -7472, -1280, 1168, -7472, -1280, 544) -- Sparks
    return
end)

RegisterEvent(103, "Legacy event 103", function()
    evt.CastSpell(15, 10, 2, -6784, -592, 1168, -6784, -592, 352) -- Sparks
    return
end)

RegisterEvent(104, "Legacy event 104", function()
    evt.CastSpell(15, 10, 2, -4848, -2528, 1168, -4848, -2528, 352) -- Sparks
    return
end)

RegisterEvent(105, "Legacy event 105", function()
    evt.CastSpell(15, 10, 2, -7472, 1184, 1168, -7472, 1184, 544) -- Sparks
    return
end)

RegisterEvent(106, "Legacy event 106", function()
    evt.CastSpell(15, 10, 2, -5536, 3120, 1168, -5536, 3120, 544) -- Sparks
    return
end)

RegisterEvent(107, "Legacy event 107", function()
    evt.CastSpell(15, 10, 2, -4848, 2432, 1168, -4848, 2432, 352) -- Sparks
    return
end)

RegisterEvent(108, "Legacy event 108", function()
    evt.CastSpell(15, 10, 2, -6784, 496, 1168, -6784, 496, 352) -- Sparks
    return
end)

RegisterEvent(109, "Legacy event 109", nil)

RegisterEvent(110, "Legacy event 110", nil)

RegisterEvent(111, "Legacy event 111", nil)

RegisterEvent(501, "Leave the Ogre Raiding Fortress", function()
    evt.MoveToMap(-20450, 1451, 1056, 1536, 0, 0, 0, 0, "Out03.odm")
    return
end, "Leave the Ogre Raiding Fortress")
