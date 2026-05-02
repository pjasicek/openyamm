-- Colony Zod
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {2},
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
    spriteNames = {"0"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(2, "Legacy event 2", function()
    if not evt.CheckMonstersKilled(ActorKillCheck.ActorIdOe, 0, 0, false) then return end -- OE actor 0; all matching actors defeated
    if IsQBitSet(QBit(617)) then return end -- Slayed Xenofex
    SetQBit(QBit(617)) -- Slayed Xenofex
    evt.ShowMovie("\"family reunion\"", true)
    AddValue(History(27), 0)
end)

RegisterEvent(3, "Legacy event 3", function()
    evt.SetDoorState(5, DoorAction.Trigger)
    evt.SetDoorState(6, DoorAction.Trigger)
end)

RegisterEvent(4, "Legacy event 4", function()
    evt.SetFacetBit(1, FacetBits.Untouchable, 1)
    evt.SetFacetBit(1, FacetBits.Invisible, 1)
    evt.SetFacetBit(2, FacetBits.Untouchable, 0)
    evt.SetFacetBit(2, FacetBits.Invisible, 0)
end)

RegisterEvent(5, "Legacy event 5", function()
    evt.SetDoorState(7, DoorAction.Trigger)
    evt.SetDoorState(8, DoorAction.Trigger)
end)

RegisterEvent(6, "Legacy event 6", function()
    evt.SetDoorState(9, DoorAction.Trigger)
    evt.SetDoorState(10, DoorAction.Trigger)
    evt.SetDoorState(11, DoorAction.Trigger)
end)

RegisterEvent(7, "Legacy event 7", function()
    evt.SetDoorState(12, DoorAction.Trigger)
    evt.SetDoorState(13, DoorAction.Trigger)
end)

RegisterEvent(8, "Legacy event 8", function()
    if not IsAtLeast(MapVar(2), 3) then
        evt.SetDoorState(14, DoorAction.Trigger)
        AddValue(MapVar(2), 1)
        return
    end
    evt.SetDoorState(14, DoorAction.Trigger)
    evt.SetLight(1, 0)
    evt.SetFacetBit(3, FacetBits.Untouchable, 1)
end)

RegisterEvent(9, "Legacy event 9", function()
    if IsAtLeast(MapVar(2), 3) then return end
    evt.SetDoorState(15, DoorAction.Trigger)
    AddValue(MapVar(2), 1)
end)

RegisterEvent(10, "Legacy event 10", function()
    if not IsAtLeast(MapVar(2), 3) then
        evt.SetDoorState(16, DoorAction.Trigger)
        AddValue(MapVar(2), 1)
        return
    end
    evt.SetDoorState(16, DoorAction.Trigger)
    evt.SetLight(1, 0)
    evt.SetFacetBit(3, FacetBits.Untouchable, 1)
end)

RegisterEvent(11, "Legacy event 11", function()
    if not IsAtLeast(MapVar(2), 3) then
        evt.SetDoorState(17, DoorAction.Trigger)
        AddValue(MapVar(2), 1)
        return
    end
    evt.SetDoorState(17, DoorAction.Trigger)
    evt.SetLight(1, 0)
    evt.SetFacetBit(3, FacetBits.Untouchable, 1)
end)

RegisterEvent(12, "Legacy event 12", function()
    evt.SetDoorState(18, DoorAction.Trigger)
    evt.SetDoorState(19, DoorAction.Trigger)
end)

RegisterEvent(13, "Legacy event 13", function()
    evt.SetDoorState(20, DoorAction.Trigger)
    evt.SetDoorState(21, DoorAction.Trigger)
end)

RegisterEvent(14, "Legacy event 14", function()
    evt.SetDoorState(22, DoorAction.Trigger)
    evt.SetDoorState(23, DoorAction.Trigger)
end)

RegisterEvent(15, "Legacy event 15", function()
    evt.SetDoorState(24, DoorAction.Open)
    evt.SetDoorState(25, DoorAction.Open)
end)

RegisterEvent(16, "Legacy event 16", function()
    evt.SetDoorState(26, DoorAction.Trigger)
    evt.SetDoorState(27, DoorAction.Trigger)
end)

RegisterEvent(17, "Legacy event 17", function()
    evt.SetDoorState(28, DoorAction.Trigger)
    evt.SetDoorState(29, DoorAction.Trigger)
end)

RegisterEvent(18, "Legacy event 18", function()
    if IsAtLeast(MapVar(3), 2) then
        evt.SetDoorState(30, DoorAction.Trigger)
        evt.SetDoorState(31, DoorAction.Trigger)
    end
end)

RegisterEvent(19, "Legacy event 19", function()
    evt.SetDoorState(34, DoorAction.Trigger)
    evt.SetDoorState(35, DoorAction.Trigger)
    evt.SetDoorState(36, DoorAction.Trigger)
    evt.SetDoorState(26, DoorAction.Close)
    evt.SetDoorState(27, DoorAction.Close)
end)

RegisterEvent(20, "Legacy event 20", function()
    evt.SetDoorState(37, DoorAction.Trigger)
    evt.SetDoorState(38, DoorAction.Trigger)
    evt.SetDoorState(39, DoorAction.Trigger)
    evt.SetDoorState(30, DoorAction.Close)
    evt.SetDoorState(31, DoorAction.Close)
end)

RegisterEvent(21, "Legacy event 21", function()
    if HasItem(1089) then -- _potion/reagent
        evt.SetDoorState(32, DoorAction.Trigger)
        evt.SetDoorState(33, DoorAction.Trigger)
    end
end)

RegisterEvent(23, "Legacy event 23", function()
    if IsAtLeast(MapVar(4), 1) then return end
    evt.SetDoorState(40, DoorAction.Trigger)
    AddValue(MapVar(3), 1)
    AddValue(MapVar(4), 1)
end)

RegisterEvent(24, "Legacy event 24", function()
    if IsAtLeast(MapVar(5), 1) then return end
    evt.SetDoorState(41, DoorAction.Trigger)
    AddValue(MapVar(3), 1)
    AddValue(MapVar(5), 1)
end)

RegisterEvent(25, "Legacy event 25", function()
    evt.SetDoorState(1, DoorAction.Trigger)
    evt.SetDoorState(2, DoorAction.Trigger)
end)

RegisterEvent(26, "Legacy event 26", function()
    evt.SetDoorState(3, DoorAction.Trigger)
    evt.SetDoorState(4, DoorAction.Trigger)
end)

RegisterEvent(27, "Legacy event 27", function()
    evt.SetDoorState(42, DoorAction.Trigger)
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

RegisterEvent(376, "Legacy event 376", function()
    evt.SpeakNPC(626) -- Roland Ironfist
    evt.SetSprite(20, 1, "0")
    AddValue(InventoryItem(1463), 1463) -- Colony Zod Key
    SetQBit(QBit(752)) -- Talked to Roland
    AddValue(History(26), 0)
    evt.SetFacetBit(1, FacetBits.Untouchable, 1)
    evt.SetFacetBit(1, FacetBits.Invisible, 1)
end)

RegisterEvent(377, "Door", function()
    if not HasItem(1463) then -- Colony Zod Key
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        evt.StatusText("The Door is Locked")
        return
    end
    RemoveItem(1463) -- Colony Zod Key
    evt.SetDoorState(32, DoorAction.Open)
    evt.SetDoorState(33, DoorAction.Open)
end, "Door")

RegisterEvent(501, "Leave the Hive", function()
    evt.MoveToMap(-18246, -11910, 3201, 128, 0, 0, 0, 0, "out12.odm")
end, "Leave the Hive")

