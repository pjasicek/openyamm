-- The Hall of the Pit
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
    onLeave = {},
    openedChestIds = {
    [176] = {1, 0},
    [177] = {2},
    [178] = {3},
    [179] = {4},
    [180] = {5},
    [181] = {6},
    [182] = {7},
    [183] = {8},
    [184] = {9},
    [185] = {10},
    [186] = {11},
    [187] = {12},
    [188] = {13},
    [189] = {14},
    [190] = {15},
    [191] = {16},
    [192] = {17},
    [193] = {18},
    [194] = {19},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsQBitSet(QBit(612)) then return end -- Chose the path of Dark
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
end)

RegisterEvent(3, "Door", function()
    evt.SetDoorState(1, DoorAction.Trigger)
    evt.SetDoorState(2, DoorAction.Trigger)
end, "Door")

RegisterEvent(151, "Legacy event 151", function()
    evt.SetDoorState(3, DoorAction.Trigger)
end)

RegisterEvent(176, "Chest", function()
    if not IsQBitSet(QBit(707)) then -- Retrieve the Seasons' Stole from the Hall of the Pit and return it to Gary Zimm in the Bracada Desert.
        evt.OpenChest(1)
        return
    end
    if not HasAward(Award(52)) then -- Retrieved the Seasons' Stole
        evt.OpenChest(0)
        return
    end
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(177, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(178, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(179, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(180, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(181, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(182, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(183, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(184, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(185, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(186, "Chest", function()
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(187, "Chest", function()
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(188, "Chest", function()
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(189, "Chest", function()
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(190, "Chest", function()
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(191, "Chest", function()
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(192, "Chest", function()
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(193, "Chest", function()
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(194, "Chest", function()
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(451, "Legacy event 451", function()
    evt.MoveToMap(2304, 1152, 1, 0, 0, 0, 0, 0)
end)

RegisterEvent(452, "Legacy event 452", function()
    evt.MoveToMap(576, 11200, 64, 0, 0, 0, 0, 0)
end)

RegisterEvent(453, "Legacy event 453", function()
    evt.MoveToMap(512, 7680, -1488, 0, 0, 0, 0, 0)
end)

RegisterEvent(501, "Leave the Hall of the Pit", function()
    evt.MoveToMap(18294, 6145, 1825, 1152, 0, 0, 0, 0, "7out05.odm")
end, "Leave the Hall of the Pit")

RegisterEvent(502, "Enter the Pit", function()
    if IsQBitSet(QBit(611)) or IsQBitSet(QBit(612)) then -- Chose the path of Light
        evt.MoveToMap(-256, 1024, 65, 1536, 0, 0, 0, 0, "7d26.blv")
    end
end, "Enter the Pit")

