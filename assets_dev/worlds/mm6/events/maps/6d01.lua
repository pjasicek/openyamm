-- Goblinwatch
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {66},
    onLeave = {},
    openedChestIds = {
    [41] = {1},
    [42] = {2},
    [43] = {3},
    [44] = {4},
    [45] = {5},
    [46] = {6},
    [47] = {7},
    [48] = {8},
    [49] = {9},
    [50] = {10},
    },
    textureNames = {"t1swdd", "t1swdu"},
    spriteNames = {},
    castSpellIds = {6, 12},
    timers = {
    },
})

RegisterEvent(1, "Door", function()
    evt.SetDoorState(1, DoorAction.Close)
end, "Door")

RegisterEvent(2, "Door", function()
    evt.SetDoorState(2, DoorAction.Close)
end, "Door")

RegisterEvent(3, "Door", function()
    evt.SetDoorState(3, DoorAction.Close)
end, "Door")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(4, DoorAction.Close)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(5, DoorAction.Close)
end, "Door")

RegisterEvent(6, "Door", function()
    evt.SetDoorState(6, DoorAction.Close)
end, "Door")

RegisterEvent(7, "Door", function()
    evt.SetDoorState(7, DoorAction.Close)
end, "Door")

RegisterEvent(8, "Door", function()
    evt.SetDoorState(8, DoorAction.Close)
end, "Door")

RegisterEvent(9, "Door", function()
    evt.SetDoorState(9, DoorAction.Close)
end, "Door")

RegisterEvent(10, "Door", function()
    evt.SetDoorState(10, DoorAction.Close)
end, "Door")

RegisterEvent(11, "Door", function()
    evt.SetDoorState(11, DoorAction.Close)
end, "Door")

RegisterEvent(12, "Door", function()
    evt.SetDoorState(12, DoorAction.Close)
end, "Door")

RegisterEvent(13, "Door", function()
    evt.SetDoorState(13, DoorAction.Close)
end, "Door")

RegisterEvent(14, "Door", function()
    evt.SetDoorState(14, DoorAction.Close)
end, "Door")

RegisterEvent(15, "Door", function()
    evt.SetDoorState(15, DoorAction.Close)
end, "Door")

RegisterEvent(16, "Door", function()
    evt.SetDoorState(16, DoorAction.Close)
end, "Door")

RegisterEvent(17, "Door", function()
    evt.SetDoorState(17, DoorAction.Close)
end, "Door")

RegisterEvent(18, "Door", function()
    evt.SetDoorState(18, DoorAction.Close)
end, "Door")

RegisterEvent(19, "A", function()
    evt.CastSpell(6, 3, 1, 2496, 4864, 360, 0, 0, 0) -- Fireball
end, "A")

RegisterEvent(20, "B", function()
    if IsAtLeast(MapVar(2), 1) then return end
    SetValue(MapVar(2), 1)
    evt.SetDoorState(55, DoorAction.Close)
    evt.SetDoorState(56, DoorAction.Close)
    evt.SetDoorState(57, DoorAction.Open)
    evt.SetDoorState(58, DoorAction.Open)
    evt.SetTexture(2011, "t1swdu")
end, "B")

RegisterEvent(21, "C", function()
    if IsAtLeast(MapVar(3), 1) then return end
    SetValue(MapVar(3), 1)
    evt.SetDoorState(57, DoorAction.Close)
    evt.SetDoorState(58, DoorAction.Close)
    evt.SetDoorState(55, DoorAction.Open)
    evt.SetDoorState(56, DoorAction.Open)
    evt.SetTexture(2012, "t1swdu")
end, "C")

RegisterEvent(22, "D", function()
    if IsAtLeast(MapVar(4), 1) then return end
    SetValue(MapVar(4), 1)
    evt.SetDoorState(40, DoorAction.Close)
    evt.SetDoorState(52, DoorAction.Close)
    evt.SetDoorState(51, DoorAction.Close)
    evt.SetDoorState(57, DoorAction.Open)
    evt.SetDoorState(58, DoorAction.Open)
    evt.SetTexture(2013, "t1swdu")
end, "D")

RegisterEvent(23, "E", function()
    if IsAtLeast(MapVar(5), 1) then return end
    SetValue(MapVar(5), 1)
    evt.SetDoorState(57, DoorAction.Close)
    evt.SetDoorState(58, DoorAction.Close)
    evt.SetDoorState(40, DoorAction.Open)
    evt.SetDoorState(52, DoorAction.Open)
    evt.SetDoorState(51, DoorAction.Open)
    evt.SetTexture(2009, "t1swdu")
end, "E")

RegisterEvent(24, "F", function()
    if IsAtLeast(MapVar(6), 1) then return end
    SetValue(MapVar(6), 1)
    evt.SetDoorState(36, DoorAction.Close)
    evt.SetDoorState(47, DoorAction.Close)
    evt.SetDoorState(48, DoorAction.Close)
    evt.SetDoorState(55, DoorAction.Open)
    evt.SetDoorState(56, DoorAction.Open)
    evt.SetTexture(2008, "t1swdu")
end, "F")

RegisterEvent(25, "G", function()
    if IsAtLeast(MapVar(7), 1) then return end
    SetValue(MapVar(7), 1)
    evt.SetDoorState(59, DoorAction.Close)
    evt.SetDoorState(60, DoorAction.Close)
    evt.SetTexture(2007, "t1swdu")
end, "G")

RegisterEvent(26, "H", function()
    if IsAtLeast(MapVar(8), 1) then return end
    SetValue(MapVar(8), 1)
    evt.SetDoorState(38, DoorAction.Close)
    evt.SetDoorState(44, DoorAction.Close)
    evt.SetDoorState(36, DoorAction.Open)
    evt.SetDoorState(47, DoorAction.Open)
    evt.SetDoorState(48, DoorAction.Open)
    evt.SetTexture(2006, "t1swdu")
end, "H")

RegisterEvent(27, "I", function()
    if IsAtLeast(MapVar(9), 1) then return end
    SetValue(MapVar(9), 1)
    evt.SetDoorState(36, DoorAction.Close)
    evt.SetDoorState(47, DoorAction.Close)
    evt.SetDoorState(48, DoorAction.Close)
    evt.SetDoorState(38, DoorAction.Open)
    evt.SetDoorState(44, DoorAction.Open)
    evt.SetTexture(2002, "t1swdu")
end, "I")

RegisterEvent(28, "J", function()
    if IsAtLeast(MapVar(10), 1) then return end
    SetValue(MapVar(10), 1)
    evt.SetDoorState(36, DoorAction.Close)
    evt.SetDoorState(47, DoorAction.Close)
    evt.SetDoorState(48, DoorAction.Close)
    evt.SetDoorState(40, DoorAction.Open)
    evt.SetDoorState(52, DoorAction.Open)
    evt.SetDoorState(51, DoorAction.Open)
    evt.SetTexture(2003, "t1swdu")
end, "J")

RegisterEvent(29, "K", function()
    if IsAtLeast(MapVar(11), 1) then return end
    SetValue(MapVar(11), 1)
    evt.SetDoorState(59, DoorAction.Close)
    evt.SetDoorState(60, DoorAction.Close)
    evt.SetDoorState(57, DoorAction.Open)
    evt.SetDoorState(58, DoorAction.Open)
    evt.SetTexture(2004, "t1swdu")
end, "K")

RegisterEvent(30, "L", function()
    if IsAtLeast(MapVar(12), 1) then return end
    SetValue(MapVar(12), 1)
    evt.SetDoorState(38, DoorAction.Close)
    evt.SetDoorState(44, DoorAction.Close)
    evt.SetDoorState(55, DoorAction.Open)
    evt.SetDoorState(56, DoorAction.Open)
    evt.SetTexture(2005, "t1swdu")
end, "L")

RegisterEvent(31, "M", function()
    evt.MoveToMap(9000, 1916, -767, 128, 0, 0, 0, 0)
end, "M")

RegisterEvent(32, "N", function()
    if IsAtLeast(MapVar(13), 1) then return end
    SetValue(MapVar(13), 1)
    evt.SetDoorState(40, DoorAction.Close)
    evt.SetDoorState(51, DoorAction.Close)
    evt.SetDoorState(52, DoorAction.Close)
    evt.SetDoorState(36, DoorAction.Open)
    evt.SetDoorState(47, DoorAction.Open)
    evt.SetDoorState(48, DoorAction.Open)
    evt.SetTexture(2000, "t1swdu")
end, "N")

RegisterEvent(33, "O", function()
    if IsAtLeast(MapVar(14), 1) then return end
    SetValue(MapVar(14), 1)
    evt.SetDoorState(57, DoorAction.Close)
    evt.SetDoorState(58, DoorAction.Close)
    evt.SetDoorState(59, DoorAction.Open)
    evt.SetDoorState(60, DoorAction.Open)
    evt.SetTexture(1999, "t1swdu")
end, "O")

RegisterEvent(34, "P", function()
    SetValue(MapVar(2), 0)
    SetValue(MapVar(3), 0)
    SetValue(MapVar(4), 0)
    SetValue(MapVar(5), 0)
    SetValue(MapVar(6), 0)
    SetValue(MapVar(7), 0)
    SetValue(MapVar(8), 0)
    SetValue(MapVar(9), 0)
    SetValue(MapVar(10), 0)
    SetValue(MapVar(11), 0)
    SetValue(MapVar(12), 0)
    SetValue(MapVar(13), 0)
    SetValue(MapVar(14), 0)
    evt.SetTexture(2011, "t1swdd")
    evt.SetTexture(2012, "t1swdd")
    evt.SetTexture(2013, "t1swdd")
    evt.SetTexture(2009, "t1swdd")
    evt.SetTexture(2008, "t1swdd")
    evt.SetTexture(2007, "t1swdd")
    evt.SetTexture(2006, "t1swdd")
    evt.SetTexture(2002, "t1swdd")
    evt.SetTexture(2003, "t1swdd")
    evt.SetTexture(2004, "t1swdd")
    evt.SetTexture(2005, "t1swdd")
    evt.SetTexture(2000, "t1swdd")
    evt.SetTexture(1999, "t1swdd")
    evt.SetDoorState(40, DoorAction.Open)
    evt.SetDoorState(51, DoorAction.Open)
    evt.SetDoorState(52, DoorAction.Open)
    evt.SetDoorState(36, DoorAction.Open)
    evt.SetDoorState(47, DoorAction.Open)
    evt.SetDoorState(48, DoorAction.Open)
    evt.SetDoorState(38, DoorAction.Open)
    evt.SetDoorState(44, DoorAction.Open)
    evt.SetDoorState(55, DoorAction.Open)
    evt.SetDoorState(56, DoorAction.Open)
    evt.SetDoorState(57, DoorAction.Open)
    evt.SetDoorState(58, DoorAction.Open)
    evt.SetDoorState(59, DoorAction.Open)
    evt.SetDoorState(60, DoorAction.Open)
end, "P")

RegisterEvent(41, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(42, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(43, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(44, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(45, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(46, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(47, "Chest", function()
    evt.OpenChest(7)
    if IsAtLeast(MapVar(21), 1) then return end
    SetValue(MapVar(21), 1)
    evt.SummonObject(2100, 9856, 4992, -1024, 512, 3, false) -- Starburst
    evt.SummonMonsters(2, 2, 3, 9856, 4992, -1024, 0, 0) -- encounter slot 2 "BGoblin" tier B, count 3, pos=(9856, 4992, -1024), actor group 0, no unique actor name
end, "Chest")

RegisterEvent(48, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(49, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(50, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(51, "Exit Door", function()
    evt.MoveToMap(-18400, -14982, 1600, 512, 0, 0, 0, 0, "oute3.odm")
end, "Exit Door")

RegisterEvent(55, "Legacy event 55", function()
    if IsAtLeast(MapVar(26), 1) then return end
    SetValue(MapVar(26), 1)
    evt.GiveItem(4, ItemType.Armor_)
end)

RegisterEvent(60, "Door", function()
    evt.SetDoorState(45, DoorAction.Close)
    evt.SetDoorState(46, DoorAction.Close)
end, "Door")

RegisterEvent(61, "Door", function()
    evt.SetDoorState(23, DoorAction.Close)
end, "Door")

RegisterEvent(62, "Switch", function()
    evt.SetDoorState(31, DoorAction.Close)
    evt.SetDoorState(32, DoorAction.Close)
end, "Switch")

RegisterEvent(63, "Legacy event 63", function()
    evt.SetDoorState(30, DoorAction.Close)
end)

RegisterEvent(64, "Legacy event 64", function()
    if IsAtLeast(MapVar(15), 1) then return end
    evt.CastSpell(12, 15, 1, 0, 0, 0, 0, 0, 0) -- Wizard Eye
    SetValue(MapVar(15), 1)
end)

RegisterEvent(65, "Legacy event 65", function()
    SetValue(MapVar(15), 0)
end)

RegisterEvent(66, "Legacy event 66", function()
    if IsAtLeast(MapVar(2), 1) then
        evt.SetTexture(2011, "t1swdu")
    end
    if IsAtLeast(MapVar(3), 1) then
        evt.SetTexture(2012, "t1swdu")
    end
    if IsAtLeast(MapVar(4), 1) then
        evt.SetTexture(2013, "t1swdu")
    end
    if IsAtLeast(MapVar(4), 1) then
        evt.SetTexture(2009, "t1swdu")
    end
    if IsAtLeast(MapVar(6), 1) then
        evt.SetTexture(2008, "t1swdu")
    end
    if IsAtLeast(MapVar(7), 1) then
        evt.SetTexture(2007, "t1swdu")
    end
    if IsAtLeast(MapVar(8), 1) then
        evt.SetTexture(2006, "t1swdu")
    end
    if IsAtLeast(MapVar(9), 1) then
        evt.SetTexture(2002, "t1swdu")
    end
    if IsAtLeast(MapVar(10), 1) then
        evt.SetTexture(2003, "t1swdu")
    end
    if IsAtLeast(MapVar(11), 1) then
        evt.SetTexture(2004, "t1swdu")
    end
    if IsAtLeast(MapVar(12), 1) then
        evt.SetTexture(2005, "t1swdu")
    end
    if IsAtLeast(MapVar(13), 1) then
        evt.SetTexture(2000, "t1swdu")
    end
    if IsAtLeast(MapVar(14), 1) then
        evt.SetTexture(1999, "t1swdu")
    end
end)

