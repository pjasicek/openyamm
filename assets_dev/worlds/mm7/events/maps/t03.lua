-- Grand Temple of the Sun
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
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
    [194] = {19},
    [195] = {0},
    },
    textureNames = {"cfb1"},
    spriteNames = {},
    castSpellIds = {6},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
end)

RegisterEvent(3, "Door", function()
    evt.SetDoorState(3, DoorAction.Trigger)
end, "Door")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(4, DoorAction.Trigger)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(5, DoorAction.Trigger)
end, "Door")

RegisterEvent(6, "Door", function()
    evt.SetDoorState(6, DoorAction.Trigger)
end, "Door")

RegisterEvent(7, "Door", function()
    evt.SetDoorState(7, DoorAction.Trigger)
end, "Door")

RegisterEvent(8, "Door", function()
    evt.SetDoorState(8, DoorAction.Trigger)
end, "Door")

RegisterEvent(10, "Button", function()
    evt.SetDoorState(10, DoorAction.Trigger)
    SubtractValue(MapVar(2), 1)
    evt.SetDoorState(14, DoorAction.Close)
end, "Button")

RegisterEvent(11, "Button", function()
    evt.SetDoorState(11, DoorAction.Trigger)
    SubtractValue(MapVar(2), 1)
    evt.SetDoorState(14, DoorAction.Close)
end, "Button")

RegisterEvent(12, "Button", function()
    evt.SetDoorState(12, DoorAction.Trigger)
    SubtractValue(MapVar(2), 1)
    evt.SetDoorState(14, DoorAction.Close)
end, "Button")

RegisterEvent(13, "Button", function()
    evt.SetDoorState(13, DoorAction.Trigger)
    SubtractValue(MapVar(2), 1)
    evt.SetDoorState(14, DoorAction.Close)
end, "Button")

RegisterEvent(14, "Button", function()
    evt.SetDoorState(14, DoorAction.Trigger)
    SetValue(MapVar(2), 1)
end, "Button")

RegisterEvent(15, "Button", function()
    evt.SetDoorState(15, DoorAction.Trigger)
    SubtractValue(MapVar(2), 1)
    evt.SetDoorState(14, DoorAction.Close)
end, "Button")

RegisterEvent(16, "Button", function()
    if IsAtLeast(MapVar(2), 1) then
        evt.SetDoorState(16, DoorAction.Trigger)
        evt.SetDoorState(9, DoorAction.Trigger)
    end
end, "Button")

RegisterEvent(17, "Door", function()
    evt.SetDoorState(1, DoorAction.Trigger)
end, "Door")

RegisterEvent(18, "Door", function()
    evt.SetDoorState(2, DoorAction.Trigger)
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

RegisterEvent(194, "Chest", function()
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(195, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(376, "Altar", function()
    if IsQBitSet(QBit(575)) then return end -- Defaced the Altar of Good. Priest of Dark promo quest.
    if IsQBitSet(QBit(556)) then -- Deface the Altar of Good in the Temple of the Sun on Evenmorn Isle then return to Daedalus Falk in the Deyja Moors.
        evt.SetTexture(20, "cfb1")
        SetQBit(QBit(575)) -- Defaced the Altar of Good. Priest of Dark promo quest.
        evt.ForPlayer(Players.All)
        SetQBit(QBit(757)) -- Congratulations - For Blinging
        ClearQBit(QBit(757)) -- Congratulations - For Blinging
        evt.StatusText("You have Desecrated the altar")
    end
end, "Altar")

RegisterEvent(451, "Legacy event 451", function()
    evt.CastSpell(6, 10, 4, -5, 3919, 288, 0, 1044, 289) -- Fireball
end)

RegisterEvent(501, "Leave the Grand Temple of the Sun", function()
    evt.MoveToMap(-7166, 11033, 185, 1536, 0, 0, 0, 0, "\tout09.odm")
end, "Leave the Grand Temple of the Sun")

