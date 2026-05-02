-- New World Computing
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {65},
    onLeave = {},
    openedChestIds = {
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {83},
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
    evt.SetDoorState(8, DoorAction.Open)
    evt.SetDoorState(41, DoorAction.Open)
end, "Door")

RegisterEvent(8, "Door", function()
    evt.SetDoorState(8, DoorAction.Close)
    evt.SetDoorState(7, DoorAction.Open)
    evt.SetDoorState(9, DoorAction.Open)
end, "Door")

RegisterEvent(9, "Door", function()
    evt.SetDoorState(9, DoorAction.Close)
    evt.SetDoorState(8, DoorAction.Open)
    evt.SetDoorState(11, DoorAction.Open)
end, "Door")

RegisterEvent(10, "Door", function()
    evt.SetDoorState(10, DoorAction.Close)
end, "Door")

RegisterEvent(11, "Door", function()
    evt.SetDoorState(11, DoorAction.Close)
    evt.SetDoorState(12, DoorAction.Open)
    evt.SetDoorState(9, DoorAction.Open)
    evt.SetDoorState(17, DoorAction.Open)
end, "Door")

RegisterEvent(12, "Door", function()
    evt.SetDoorState(12, DoorAction.Close)
    evt.SetDoorState(17, DoorAction.Open)
    evt.SetDoorState(11, DoorAction.Open)
    evt.SetDoorState(17, DoorAction.Open)
end, "Door")

RegisterEvent(13, "Door", function()
    evt.SetDoorState(13, DoorAction.Close)
    evt.SetDoorState(17, DoorAction.Open)
end, "Door")

RegisterEvent(14, "Door", function()
    evt.SetDoorState(14, DoorAction.Close)
end, "Door")

RegisterEvent(15, "Door", function()
    evt.SetDoorState(15, DoorAction.Close)
end, "Door")

RegisterEvent(17, "Door", function()
    evt.SetDoorState(17, DoorAction.Close)
    evt.SetDoorState(12, DoorAction.Open)
    evt.SetDoorState(18, DoorAction.Open)
end, "Door")

RegisterEvent(18, "Door", function()
    evt.SetDoorState(18, DoorAction.Close)
    evt.SetDoorState(17, DoorAction.Open)
    evt.SetDoorState(19, DoorAction.Open)
end, "Door")

RegisterEvent(19, "Door", function()
    evt.SetDoorState(19, DoorAction.Close)
    evt.SetDoorState(18, DoorAction.Open)
    evt.SetDoorState(20, DoorAction.Open)
    evt.SetDoorState(17, DoorAction.Open)
end, "Door")

RegisterEvent(20, "Door", function()
    evt.SetDoorState(20, DoorAction.Close)
    evt.SetDoorState(19, DoorAction.Open)
    evt.SetDoorState(21, DoorAction.Open)
    evt.SetDoorState(17, DoorAction.Open)
end, "Door")

RegisterEvent(21, "Door", function()
    evt.SetDoorState(21, DoorAction.Close)
    evt.SetDoorState(20, DoorAction.Open)
    evt.SetDoorState(22, DoorAction.Open)
    evt.SetDoorState(17, DoorAction.Open)
end, "Door")

RegisterEvent(22, "Door", function()
    evt.SetDoorState(22, DoorAction.Close)
    evt.SetDoorState(21, DoorAction.Open)
    evt.SetDoorState(23, DoorAction.Open)
    evt.SetDoorState(17, DoorAction.Open)
end, "Door")

RegisterEvent(23, "Door", function()
    evt.SetDoorState(23, DoorAction.Close)
    evt.SetDoorState(22, DoorAction.Open)
    evt.SetDoorState(24, DoorAction.Open)
end, "Door")

RegisterEvent(24, "Door", function()
    evt.SetDoorState(24, DoorAction.Close)
    evt.SetDoorState(23, DoorAction.Open)
    evt.SetDoorState(25, DoorAction.Open)
end, "Door")

RegisterEvent(25, "Door", function()
    evt.SetDoorState(25, DoorAction.Close)
    evt.SetDoorState(24, DoorAction.Open)
    evt.SetDoorState(26, DoorAction.Open)
end, "Door")

RegisterEvent(26, "Door", function()
    evt.SetDoorState(26, DoorAction.Close)
    evt.SetDoorState(25, DoorAction.Open)
    evt.SetDoorState(27, DoorAction.Open)
end, "Door")

RegisterEvent(27, "Door", function()
    evt.SetDoorState(27, DoorAction.Close)
    evt.SetDoorState(28, DoorAction.Open)
    evt.SetDoorState(26, DoorAction.Open)
end, "Door")

RegisterEvent(28, "Door", function()
    evt.SetDoorState(28, DoorAction.Close)
    evt.SetDoorState(27, DoorAction.Open)
    evt.SetDoorState(29, DoorAction.Open)
end, "Door")

RegisterEvent(29, "Door", function()
    evt.SetDoorState(29, DoorAction.Close)
    evt.SetDoorState(28, DoorAction.Open)
    evt.SetDoorState(30, DoorAction.Open)
end, "Door")

RegisterEvent(30, "Door", function()
    evt.SetDoorState(30, DoorAction.Close)
    evt.SetDoorState(31, DoorAction.Open)
    evt.SetDoorState(29, DoorAction.Open)
end, "Door")

RegisterEvent(31, "Door", function()
    evt.SetDoorState(31, DoorAction.Close)
    evt.SetDoorState(30, DoorAction.Open)
    evt.SetDoorState(32, DoorAction.Open)
end, "Door")

RegisterEvent(32, "Door", function()
    evt.SetDoorState(32, DoorAction.Close)
    evt.SetDoorState(31, DoorAction.Open)
    evt.SetDoorState(33, DoorAction.Open)
end, "Door")

RegisterEvent(33, "Door", function()
    evt.SetDoorState(33, DoorAction.Close)
    evt.SetDoorState(34, DoorAction.Open)
    evt.SetDoorState(32, DoorAction.Open)
end, "Door")

RegisterEvent(34, "Door", function()
    evt.SetDoorState(34, DoorAction.Close)
    evt.SetDoorState(38, DoorAction.Open)
    evt.SetDoorState(33, DoorAction.Open)
end, "Door")

RegisterEvent(35, "Door", function()
    evt.SetDoorState(35, DoorAction.Close)
end, "Door")

RegisterEvent(36, "Door", function()
    evt.SetDoorState(36, DoorAction.Close)
end, "Door")

RegisterEvent(37, "Door", function()
    evt.SetDoorState(37, DoorAction.Close)
end, "Door")

RegisterEvent(38, "Door", function()
    evt.SetDoorState(38, DoorAction.Close)
    evt.SetDoorState(39, DoorAction.Open)
    evt.SetDoorState(34, DoorAction.Open)
end, "Door")

RegisterEvent(39, "Door", function()
    evt.SetDoorState(39, DoorAction.Close)
end, "Door")

RegisterEvent(40, "Door", function()
    evt.SetDoorState(40, DoorAction.Close)
    evt.SetDoorState(39, DoorAction.Open)
    evt.SetDoorState(41, DoorAction.Open)
end, "Door")

RegisterEvent(41, "Door", function()
    evt.SetDoorState(41, DoorAction.Close)
    evt.SetDoorState(7, DoorAction.Open)
    evt.SetDoorState(40, DoorAction.Open)
end, "Door")

RegisterEvent(42, "Lever", function()
    evt.SetDoorState(42, DoorAction.Trigger)
    evt.SetDoorState(16, DoorAction.Trigger)
end, "Lever")

RegisterEvent(44, "Door", function()
    evt.SetDoorState(44, DoorAction.Close)
    evt.SetDoorState(43, DoorAction.Close)
end, "Door")

RegisterEvent(45, "Door", function()
    evt.SetDoorState(45, DoorAction.Close)
end, "Door")

RegisterEvent(46, "Door", function()
    evt.SetDoorState(46, DoorAction.Close)
end, "Door")

RegisterEvent(47, "Door", function()
    evt.SetDoorState(47, DoorAction.Close)
end, "Door")

RegisterEvent(48, "Door", function()
    evt.SetDoorState(48, DoorAction.Close)
end, "Door")

RegisterEvent(49, "Door", function()
    evt.SetDoorState(49, DoorAction.Close)
end, "Door")

RegisterEvent(50, "Door", function()
    evt.SetDoorState(50, DoorAction.Close)
end, "Door")

RegisterEvent(51, "Door", function()
    evt.SetDoorState(51, DoorAction.Close)
end, "Door")

RegisterEvent(52, "Door", function()
    evt.SetDoorState(52, DoorAction.Close)
end, "Door")

RegisterEvent(53, "Door", function()
    evt.SetDoorState(53, DoorAction.Close)
end, "Door")

RegisterEvent(54, "Door", function()
    evt.SetDoorState(54, DoorAction.Close)
end, "Door")

RegisterEvent(55, "Door", function()
    evt.SetDoorState(55, DoorAction.Close)
end, "Door")

RegisterEvent(56, "Door", function()
    evt.SetDoorState(56, DoorAction.Close)
end, "Door")

RegisterEvent(57, "Door", function()
    evt.SetDoorState(57, DoorAction.Close)
end, "Door")

RegisterEvent(58, "Door", function()
    evt.SetDoorState(58, DoorAction.Close)
end, "Door")

RegisterEvent(59, "Door", function()
    evt.SetDoorState(59, DoorAction.Close)
end, "Door")

RegisterEvent(60, "Shelves", function()
    if not IsAtLeast(MapVar(2), 4) then
        AddValue(MapVar(2), 1)
        evt.StatusText("You found something!")
        local randomStep = PickRandomOption(60, 4, {4, 6, 8, 10, 12, 14})
        if randomStep == 4 then
            AddValue(InventoryItem(1603), 1603) -- Longsword
            return
        elseif randomStep == 6 then
            AddValue(InventoryItem(1617), 1617) -- Dagger
            return
        elseif randomStep == 8 then
            AddValue(InventoryItem(1660), 1660) -- Root Club
            return
        elseif randomStep == 10 then
            AddValue(InventoryItem(1763), 1763) -- Phirna Root
            return
        elseif randomStep == 12 then
            AddValue(InventoryItem(1913), 1913) -- Inferno
            return
        elseif randomStep == 14 then
            AddValue(InventoryItem(114), 114) -- Citizen Hat
            return
        end
    end
    evt.StatusText("Nothing here")
end, "Shelves")

RegisterEvent(61, "Potions for sale", function()
    if not IsAtLeast(Gold, 100) then
        evt.StatusText("Not enough gold")
        return
    end
    evt.StatusText("You found something!")
    local randomStep = PickRandomOption(61, 5, {5, 8, 11, 14, 17, 20})
    if randomStep == 5 then
        AddValue(InventoryItem(220), 220) -- Potion Bottle
        SubtractValue(Gold, 50)
        return
    elseif randomStep == 8 then
        AddValue(InventoryItem(221), 221) -- Catalyst
        SubtractValue(Gold, 20)
        return
    elseif randomStep == 11 then
        AddValue(InventoryItem(221), 221) -- Catalyst
        SubtractValue(Gold, 100)
        return
    elseif randomStep == 14 then
        AddValue(InventoryItem(222), 222) -- Cure Wounds
        SubtractValue(Gold, 50)
        return
    elseif randomStep == 17 then
        AddValue(InventoryItem(223), 223) -- Magic Potion
        SubtractValue(Gold, 20)
        return
    elseif randomStep == 20 then
        AddValue(InventoryItem(224), 224) -- Cure Weakness
        SubtractValue(Gold, 50)
        return
    end
end, "Potions for sale")

RegisterEvent(62, "Pantry", function()
    local randomStep = PickRandomOption(62, 1, {1, 3, 5, 7, 10, 13})
    if randomStep == 1 then
        AddValue(Food, 1)
        return
    elseif randomStep == 3 then
        AddValue(Food, 2)
        return
    elseif randomStep == 5 then
        AddValue(Food, 1)
        return
    elseif randomStep == 7 then
        evt.StatusText("Bad Food!")
        SetValue(PoisonedYellow, 1)
        return
    elseif randomStep == 10 then
        evt.StatusText("Hic!")
        SetValue(PoisonedGreen, 1)
        return
    elseif randomStep == 13 then
        AddValue(InventoryItem(220), 220) -- Potion Bottle
    end
end, "Pantry")

RegisterEvent(63, "Counter", function()
    AddValue(InventoryItem(220), 220) -- Potion Bottle
end, "Counter")

RegisterEvent(64, "Legacy event 64", function()
    if IsAtLeast(MapVar(3), 16) then return end
    AddValue(MapVar(3), 1)
    evt.StatusText("You found something!")
    local randomStep = PickRandomOption(64, 4, {4, 6, 8})
    if randomStep == 4 then
        AddValue(InventoryItem(1762), 1762) -- Poppysnaps
        return
    elseif randomStep == 6 then
        AddValue(InventoryItem(1763), 1763) -- Phirna Root
        return
    elseif randomStep == 8 then
        AddValue(InventoryItem(1764), 1764) -- Widoweeps Berries
        return
    end
end)

RegisterEvent(65, "Legacy event 65", function()
    evt.SummonObject(36, 2944, 1920, 1, 1000, 5, false) -- Widowsweep Berries
end)

RegisterEvent(66, "Desk", function()
    if IsAtLeast(MapVar(5), 1) then return end
    AddValue(MapVar(5), 1)
    evt.StatusText("You found something!")
    local randomStep = PickRandomOption(66, 4, {4, 6, 8, 10, 12})
    if randomStep == 4 then
        AddValue(InventoryItem(89), 89) -- Rusty Mail Vest
        return
    elseif randomStep == 6 then
        AddValue(InventoryItem(90), 90) -- Steel Chainmail
        return
    elseif randomStep == 8 then
        AddValue(InventoryItem(91), 91) -- Minotaur Chainmail
        return
    elseif randomStep == 10 then
        AddValue(InventoryItem(92), 92) -- Siertal Chainmail
        return
    elseif randomStep == 12 then
        AddValue(InventoryItem(93), 93) -- Erudine Chainmail
    end
end, "Desk")

RegisterEvent(67, "Legacy event 67", function()
    evt.ForPlayer(Players.All)
    AddValue(Insane, 10)
end)

RegisterEvent(68, "Legacy event 68", function()
    evt.ForPlayer(Players.All)
    if IsAtLeast(Insane, 10) then
        SubtractValue(Insane, 10)
    end
end)

RegisterEvent(69, "Desk", function()
    if IsAtLeast(MapVar(4), 1) then return end
    SetValue(MapVar(4), 1)
    evt.StatusText("You found something!")
    AddValue(InventoryItem(133), 133) -- Hardened Leather Boots
end, "Desk")

RegisterEvent(70, "Desk", function()
    if IsAtLeast(MapVar(6), 1) then return end
    SetValue(MapVar(6), 1)
    evt.StatusText("You found something!")
    AddValue(InventoryItem(1660), 1660) -- Root Club
end, "Desk")

RegisterNoOpEvent(71, "Desk", "Desk")

RegisterEvent(72, "Desk", function()
    if IsAtLeast(MapVar(7), 4) then return end
    evt.StatusText("You found something!")
    AddValue(InventoryItem(123), 123) -- Moon Temple Cloak
    AddValue(MapVar(7), 1)
end, "Desk")

RegisterEvent(73, "Desk", function()
    evt.CastSpell(83, 64, 3, 0, 0, 0, 0, 0, 0) -- Day of the Gods
end, "Desk")

RegisterEvent(74, "Desk", function()
    if IsAtLeast(Gold, 10000) then return end
    AddValue(Gold, 500)
    evt.StatusText("You found something!")
end, "Desk")

RegisterEvent(75, "Exit", function()
    evt.MoveToMap(12808, 6832, 64, 512, 0, 0, 0, 0)
end, "Exit")

