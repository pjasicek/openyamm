-- The Titans' Stronghold
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [176] = {0, 1},
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
    [195] = {0},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(3, "Legacy event 3", function()
    evt.SetDoorState(1, DoorAction.Trigger)
end)

RegisterEvent(4, "Legacy event 4", function()
    evt.SetDoorState(2, DoorAction.Trigger)
end)

RegisterEvent(5, "Legacy event 5", function()
    evt.SetDoorState(3, DoorAction.Trigger)
end)

RegisterEvent(6, "Legacy event 6", function()
    evt.SetDoorState(4, DoorAction.Trigger)
end)

RegisterEvent(176, "Chest", function()
    if not IsQBitSet(QBit(1586)) then -- Promoted to Master Archer
        if IsQBitSet(QBit(1587)) then -- Promoted to Honorary Master Archer
            evt.OpenChest(0)
            return
        elseif IsQBitSet(QBit(1588)) then -- Promoted to Sniper
            evt.OpenChest(0)
            return
        elseif IsQBitSet(QBit(1589)) then -- Promoted to Honorary Sniper
            evt.OpenChest(0)
            return
        elseif IsQBitSet(QBit(542)) then -- Retrieve the Perfect Bow from the Titans' Stronghold in Avlee and return it to Lawrence Mark in Harmondale.
            SetQBit(QBit(675)) -- Got perfect bow out of chest
            evt.OpenChest(1)
        elseif IsQBitSet(QBit(544)) then -- Retrieve the Perfect Bow from the Titans' Stronghold in Avlee and return it to Steagal Snick in Avlee.
            SetQBit(QBit(675)) -- Got perfect bow out of chest
            evt.OpenChest(1)
        else
            evt.OpenChest(0)
            return
        end
    end
    evt.OpenChest(0)
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

RegisterEvent(195, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(501, "Legacy event 501", function()
    evt.MoveToMap(18754, -17550, 929, 768, 0, 0, 0, 0, "out14.odm")
end)

