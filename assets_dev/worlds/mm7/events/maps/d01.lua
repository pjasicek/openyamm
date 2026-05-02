-- The Erathian Sewers
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
    [194] = {19},
    [195] = {0},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {24, 39},
    timers = {
    },
})

RegisterEvent(3, "Door", function()
    evt.SetDoorState(22, DoorAction.Close)
    SetValue(MapVar(3), 1)
end, "Door")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(23, DoorAction.Close)
    SetValue(MapVar(3), 1)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(5, DoorAction.Trigger)
    evt.SetDoorState(6, DoorAction.Trigger)
end, "Door")

RegisterEvent(7, "Door", function()
    evt.SetDoorState(7, DoorAction.Trigger)
end, "Door")

RegisterEvent(8, "Door", function()
    evt.SetDoorState(8, DoorAction.Trigger)
end, "Door")

RegisterEvent(10, "Door", function()
    evt.SetDoorState(10, DoorAction.Trigger)
end, "Door")

RegisterEvent(13, "Door", function()
    evt.SetDoorState(13, DoorAction.Trigger)
end, "Door")

RegisterEvent(14, "Door", function()
    evt.SetDoorState(14, DoorAction.Trigger)
end, "Door")

RegisterEvent(15, "Door", function()
    evt.SetDoorState(15, DoorAction.Trigger)
end, "Door")

RegisterEvent(16, "Door", function()
    evt.SetDoorState(16, DoorAction.Trigger)
end, "Door")

RegisterEvent(17, "Door", function()
    evt.SetDoorState(17, DoorAction.Trigger)
end, "Door")

RegisterEvent(18, "Door", function()
    evt.SetDoorState(18, DoorAction.Close)
    SetValue(MapVar(3), 0)
end, "Door")

RegisterEvent(19, "Door", function()
    evt.SetDoorState(19, DoorAction.Trigger)
end, "Door")

RegisterEvent(20, "Door", function()
    evt.SetDoorState(20, DoorAction.Trigger)
end, "Door")

RegisterEvent(21, "Door", function()
    evt.SetDoorState(21, DoorAction.Close)
    SetValue(MapVar(3), 0)
end, "Door")

RegisterEvent(151, "Legacy event 151", function()
    evt.SetFacetBit(2, FacetBits.Invisible, 0)
    evt.SetFacetBit(2, FacetBits.Untouchable, 0)
    evt.SetDoorState(1, DoorAction.Open)
    evt.SetDoorState(2, DoorAction.Trigger)
end)

RegisterEvent(152, "Legacy event 152", function()
    evt.SetFacetBit(1, FacetBits.Invisible, 0)
    evt.SetFacetBit(1, FacetBits.Untouchable, 0)
    evt.SetDoorState(3, DoorAction.Trigger)
    evt.SetDoorState(4, DoorAction.Open)
end)

RegisterEvent(153, "Legacy event 153", function()
    evt.MoveToMap(768, 10880, 1, -1, 0, 0, 0, 0)
end)

RegisterEvent(154, "Legacy event 154", function()
    evt.MoveToMap(768, 10400, 0, -1, 0, 0, 0, 0)
end)

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

RegisterEvent(376, "Door", function()
    evt.EnterHouse(1162) -- Master Thief
end, "Door")

RegisterEvent(451, "Legacy event 451", function()
    evt.SetDoorState(24, DoorAction.Trigger)
    evt.SetDoorState(30, DoorAction.Trigger)
    evt.SetDoorState(31, DoorAction.Trigger)
    evt.SetDoorState(34, DoorAction.Trigger)
end)

RegisterEvent(452, "Legacy event 452", function()
    evt.SetDoorState(25, DoorAction.Trigger)
    evt.SetDoorState(34, DoorAction.Trigger)
    evt.SetDoorState(31, DoorAction.Trigger)
end)

RegisterEvent(453, "Legacy event 453", function()
    evt.SetDoorState(26, DoorAction.Trigger)
    evt.SetDoorState(30, DoorAction.Open)
    evt.SetDoorState(31, DoorAction.Open)
    evt.SetDoorState(32, DoorAction.Open)
    evt.SetDoorState(33, DoorAction.Open)
    evt.SetDoorState(34, DoorAction.Open)
    evt.SetDoorState(24, DoorAction.Open)
    evt.SetDoorState(25, DoorAction.Open)
    evt.SetDoorState(27, DoorAction.Open)
    evt.SetDoorState(28, DoorAction.Open)
    evt.SetDoorState(29, DoorAction.Open)
end)

RegisterEvent(454, "Legacy event 454", function()
    evt.SetDoorState(27, DoorAction.Trigger)
    evt.SetDoorState(32, DoorAction.Trigger)
    evt.SetDoorState(33, DoorAction.Trigger)
end)

RegisterEvent(455, "Legacy event 455", function()
    evt.SetDoorState(28, DoorAction.Trigger)
    evt.SetDoorState(34, DoorAction.Trigger)
end)

RegisterEvent(456, "Legacy event 456", function()
    evt.SetDoorState(29, DoorAction.Trigger)
    evt.SetDoorState(32, DoorAction.Trigger)
end)

RegisterEvent(457, "Legacy event 457", function()
    if IsAtLeast(MapVar(3), 1) then
        evt.CastSpell(39, 10, 4, 5632, 4736, 542, 5632, 12352, 542) -- Blades
    end
end)

RegisterEvent(458, "Legacy event 458", function()
    if IsAtLeast(MapVar(3), 1) then
        evt.CastSpell(39, 10, 4, -5632, 4736, 542, -5632, 12352, 542) -- Blades
    end
end)

RegisterEvent(459, "Legacy event 459", function()
    evt.CastSpell(24, 10, 4, 0, 4736, 368, 0, 5632, 64) -- Poison Spray
    evt.CastSpell(24, 10, 4, 0, 6528, 368, 0, 5632, 64) -- Poison Spray
end)

RegisterEvent(501, "Leave the Erathian Sewer", function()
    evt.MoveToMap(2727, -9254, 164, 1536, 0, 0, 0, 0, "7out03.odm")
end, "Leave the Erathian Sewer")

RegisterEvent(502, "Leave the Erathian Sewer", function()
    evt.MoveToMap(-2184, 14886, 25, 512, 0, 0, 0, 0, "7out03.odm")
end, "Leave the Erathian Sewer")

RegisterEvent(503, "Leave the Erathian Sewer", function()
    evt.MoveToMap(-18356, 15481, 158, 1, 0, 0, 0, 0, "7out03.odm")
end, "Leave the Erathian Sewer")

