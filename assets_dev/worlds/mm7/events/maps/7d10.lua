-- The Breeding Zone
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [176] = {1},
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
    [195] = {0, 19},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {6, 39},
    timers = {
    },
})

RegisterEvent(3, "Button", function()
    evt.SetDoorState(11, DoorAction.Trigger)
    evt.SetDoorState(14, DoorAction.Trigger)
end, "Button")

RegisterEvent(4, "Button", function()
    evt.SetDoorState(13, DoorAction.Trigger)
    evt.SetDoorState(15, DoorAction.Trigger)
end, "Button")

RegisterEvent(5, "Button", function()
    evt.SetDoorState(12, DoorAction.Trigger)
    evt.SetDoorState(16, DoorAction.Trigger)
end, "Button")

RegisterEvent(6, "Take a Drink", function()
    evt.SetDoorState(31, DoorAction.Trigger)
end, "Take a Drink")

RegisterEvent(7, "Button", function()
    evt.SetDoorState(32, DoorAction.Trigger)
    evt.SetDoorState(33, DoorAction.Trigger)
end, "Button")

RegisterEvent(8, "Door", function()
    evt.SetDoorState(40, DoorAction.Trigger)
end, "Door")

RegisterEvent(9, "Button", function()
    evt.SetDoorState(53, DoorAction.Trigger)
    evt.SetDoorState(50, DoorAction.Trigger)
end, "Button")

RegisterEvent(10, "Button", function()
    evt.SetDoorState(52, DoorAction.Trigger)
    evt.SetDoorState(51, DoorAction.Trigger)
end, "Button")

RegisterEvent(11, "Door", function()
    evt.SetDoorState(2, DoorAction.Trigger)
end, "Door")

RegisterEvent(12, "Door", function()
    evt.SetDoorState(1, DoorAction.Trigger)
end, "Door")

RegisterEvent(176, "Chest", function()
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

RegisterEvent(195, "Chest", function()
    if not IsAtLeast(MapVar(2), 1) then
        if not IsQBitSet(QBit(751)) then -- Got the Divine Intervention
            evt.OpenChest(0)
            SetQBit(QBit(751)) -- Got the Divine Intervention
            SetQBit(QBit(738)) -- Book of Divine Intervention - I lost it
            SetValue(MapVar(2), 1)
            return
        end
        evt.OpenChest(19)
        return
    end
    evt.OpenChest(0)
    SetQBit(QBit(751)) -- Got the Divine Intervention
    SetQBit(QBit(738)) -- Book of Divine Intervention - I lost it
    SetValue(MapVar(2), 1)
end, "Chest")

RegisterEvent(451, "Legacy event 451", function()
    evt.CastSpell(39, 7, 4, -4686, 3674, -447, -4686, 1445, -447) -- Blades
    evt.CastSpell(39, 7, 4, -4686, 1445, -447, -4686, 3674, -447) -- Blades
end)

RegisterEvent(452, "Legacy event 452", function()
    evt.CastSpell(6, 8, 4, -768, 2432, 257, 1664, 2432, 257) -- Fireball
end)

RegisterEvent(501, "Leave the Breeding Zone", function()
    evt.MoveToMap(-5376, 474, -415, 1536, 0, 0, 0, 0, "7d26.blv")
end, "Leave the Breeding Zone")

RegisterEvent(502, "Leave the Breeding Zone", function()
    SetQBit(QBit(641)) -- Completed Breeding Pit.
    evt.MoveToMap(-5376, 474, -415, 1536, 0, 0, 0, 0, "7d26.blv")
end, "Leave the Breeding Zone")

