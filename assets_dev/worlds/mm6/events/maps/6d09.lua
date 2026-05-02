-- Snergle's Iron Mines
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [27] = {1},
    [28] = {2},
    [29] = {3},
    [30] = {4},
    [31] = {5},
    [32] = {6},
    [33] = {7},
    [34] = {8},
    [35] = {9},
    [36] = {10},
    [37] = {11},
    [77] = {12},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Door", function()
    evt.SetDoorState(1, DoorAction.Close)
end, "Door")

RegisterEvent(2, "Door", function()
    if not HasItem(2192) then -- Cell Key
        evt.StatusText("The Door is Locked")
        return
    end
    evt.SetDoorState(2, DoorAction.Close)
    RemoveItem(2192) -- Cell Key
end, "Door")

RegisterEvent(3, "Door", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.StatusText("The Door is Locked")
        return
    end
    evt.SetDoorState(3, DoorAction.Close)
end, "Door")

RegisterEvent(4, "Door", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.StatusText("The Door is Locked")
        return
    end
    evt.SetDoorState(4, DoorAction.Close)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(5, DoorAction.Close)
end, "Door")

RegisterEvent(6, "Double Door", function()
    evt.SetDoorState(6, DoorAction.Close)
    evt.SetDoorState(7, DoorAction.Close)
end, "Double Door")

RegisterEvent(8, "Door", function()
    evt.SetDoorState(8, DoorAction.Close)
end, "Door")

RegisterEvent(9, "Door", function()
    if not IsAtLeast(ActualIntellect, 40) then
        evt.ForPlayer(Players.All)
        evt.DamagePlayer(5, 0, 30)
        evt.StatusText("You are not smart enough!")
        return
    end
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

RegisterEvent(19, "Door", function()
    evt.SetDoorState(19, DoorAction.Close)
end, "Door")

RegisterEvent(20, "Door", function()
    evt.SetDoorState(20, DoorAction.Close)
end, "Door")

RegisterEvent(21, "Door", function()
    evt.SetDoorState(21, DoorAction.Close)
end, "Door")

RegisterEvent(22, "Legacy event 22", function()
    evt.SetDoorState(22, DoorAction.Close)
end)

RegisterEvent(23, "Double Door", function()
    evt.SetDoorState(23, DoorAction.Close)
    evt.SetDoorState(24, DoorAction.Close)
end, "Double Door")

RegisterEvent(25, "Door", function()
    evt.SetDoorState(25, DoorAction.Close)
end, "Door")

RegisterEvent(26, "Door", function()
    evt.SetDoorState(26, DoorAction.Close)
end, "Door")

RegisterEvent(27, "Cabinet", function()
    evt.OpenChest(1)
    SetValue(MapVar(2), 1)
    if IsAtLeast(MapVar(21), 1) then return end
    evt.SummonMonsters(1, 1, 2, -1280, 3200, 0, 0, 0) -- encounter slot 1 "BDwarf" tier A, count 2, pos=(-1280, 3200, 0), actor group 0, no unique actor name
    evt.SummonMonsters(1, 2, 2, -1920, 2688, 0, 0, 0) -- encounter slot 1 "BDwarf" tier B, count 2, pos=(-1920, 2688, 0), actor group 0, no unique actor name
    evt.SummonMonsters(1, 3, 2, -2560, 2944, 0, 0, 0) -- encounter slot 1 "BDwarf" tier C, count 2, pos=(-2560, 2944, 0), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, -1792, 3584, 0, 0, 0) -- encounter slot 3 "Demon" tier A, count 1, pos=(-1792, 3584, 0), actor group 0, no unique actor name
    SetValue(MapVar(21), 1)
end, "Cabinet")

RegisterEvent(28, "Cabinet", function()
    evt.OpenChest(2)
end, "Cabinet")

RegisterEvent(29, "Cabinet", function()
    evt.OpenChest(3)
end, "Cabinet")

RegisterEvent(30, "Cabinet", function()
    evt.OpenChest(4)
end, "Cabinet")

RegisterEvent(31, "Cabinet", function()
    evt.OpenChest(5)
end, "Cabinet")

RegisterEvent(32, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(33, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(34, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(35, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(36, "Cabinet", function()
    evt.OpenChest(10)
end, "Cabinet")

RegisterEvent(37, "Cabinet", function()
    evt.OpenChest(11)
end, "Cabinet")

RegisterNoOpEvent(39, "Bookshelves", "Bookshelves")

RegisterEvent(40, "Bookshelves", function()
    evt.StatusText("\"You thumb through the books, but find nothing of interest.\"")
    evt.FaceExpression(39)
end, "Bookshelves")

RegisterEvent(41, "Legacy event 41", function()
    evt.ForPlayer(Players.All)
    if HasItem(2108) then return end -- Key to Snergle's Chambers
    SetQBit(QBit(1025)) -- 1 D09, key to open D05
    evt.SpeakNPC(851) -- Ghim Hammond
end)

RegisterEvent(50, "Exit", function()
    evt.MoveToMap(20212, 13238, 97, 1408, 0, 0, 0, 0, "outc3.odm")
end, "Exit")

RegisterEvent(60, "Legacy event 60", function()
    SetValue(MapVar(51), 20)
    SetValue(MapVar(52), 20)
end)

RegisterEvent(61, "Pool", function()
    if not IsAtLeast(MapVar(51), 1) then
        evt.StatusText("Refreshing!")
        SetAutonote(457) -- 10 Hit points cured by the right side pool in Snergle's Iron Mines.
        return
    end
    SubtractValue(MapVar(51), 1)
    AddValue(CurrentHealth, 10)
    evt.StatusText("+10 Hit points restored.")
    SetAutonote(457) -- 10 Hit points cured by the right side pool in Snergle's Iron Mines.
end, "Pool")

RegisterEvent(62, "Pool", function()
    if not IsAtLeast(MapVar(52), 1) then
        evt.StatusText("Refreshing!")
        SetAutonote(458) -- 10 Spell points restored by the left side pool in Snergle's Iron Mines.
        return
    end
    SubtractValue(MapVar(52), 1)
    AddValue(CurrentSpellPoints, 10)
    evt.StatusText("+10 Spell points restored.")
    SetAutonote(458) -- 10 Spell points restored by the left side pool in Snergle's Iron Mines.
end, "Pool")

RegisterEvent(63, "Legacy event 63", function()
    evt.SetDoorState(27, DoorAction.Close)
end)

RegisterEvent(64, "Bookshelves", function()
    if IsAtLeast(MapVar(3), 1) then return end
    AddValue(InventoryItem(1902), 1902) -- Torch Light
    SetValue(MapVar(3), 1)
end, "Bookshelves")

RegisterEvent(65, "Bookshelves", function()
    if IsAtLeast(MapVar(4), 1) then return end
    AddValue(InventoryItem(1903), 1903) -- Fire Bolt
    SetValue(MapVar(4), 1)
end, "Bookshelves")

RegisterEvent(66, "Bookshelves", function()
    if IsAtLeast(MapVar(5), 1) then return end
    AddValue(InventoryItem(1905), 1905) -- Fire Resistance
    SetValue(MapVar(5), 1)
end, "Bookshelves")

RegisterEvent(67, "Bookshelves", function()
    if IsAtLeast(MapVar(6), 1) then return end
    AddValue(InventoryItem(1915), 1915) -- Wizard Eye
    SetValue(MapVar(6), 1)
end, "Bookshelves")

RegisterEvent(68, "Bookshelves", function()
    if IsAtLeast(MapVar(7), 1) then return end
    AddValue(InventoryItem(1916), 1916) -- Feather Fall
    SetValue(MapVar(7), 1)
end, "Bookshelves")

RegisterEvent(69, "Bookshelves", function()
    if IsAtLeast(MapVar(8), 1) then return end
    AddValue(InventoryItem(1918), 1918) -- Air Resistance
    SetValue(MapVar(8), 1)
end, "Bookshelves")

RegisterEvent(70, "Bookshelves", function()
    if IsAtLeast(MapVar(9), 1) then return end
    AddValue(InventoryItem(1928), 1928) -- Awaken
    SetValue(MapVar(9), 1)
end, "Bookshelves")

RegisterEvent(71, "Bookshelves", function()
    if IsAtLeast(MapVar(10), 1) then return end
    AddValue(InventoryItem(1929), 1929) -- Poison Spray
    SetValue(MapVar(10), 1)
end, "Bookshelves")

RegisterEvent(72, "Bookshelves", function()
    if IsAtLeast(MapVar(11), 1) then return end
    AddValue(InventoryItem(1930), 1930) -- Water Resistance
    SetValue(MapVar(11), 1)
end, "Bookshelves")

RegisterEvent(73, "Bookshelves", function()
    if IsAtLeast(MapVar(12), 1) then return end
    AddValue(InventoryItem(1980), 1980) -- Cure Weakness
    SetValue(MapVar(12), 1)
end, "Bookshelves")

RegisterEvent(74, "Bookshelves", function()
    if IsAtLeast(MapVar(13), 1) then return end
    AddValue(InventoryItem(1981), 1981) -- Heal
    SetValue(MapVar(13), 1)
end, "Bookshelves")

RegisterEvent(75, "Bookshelves", function()
    if IsAtLeast(MapVar(14), 1) then return end
    AddValue(InventoryItem(1983), 1983) -- Body Resistance
    SetValue(MapVar(14), 1)
end, "Bookshelves")

RegisterEvent(76, "Bookshelves", function()
    if IsAtLeast(MapVar(15), 1) then return end
    AddValue(InventoryItem(1960), 1960) -- Remove Curse
    SetValue(MapVar(15), 1)
end, "Bookshelves")

RegisterEvent(77, "Cabinet", function()
    evt.OpenChest(12)
end, "Cabinet")

