-- Tomb of Ethric the Mad
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [14] = {0},
    [15] = {1},
    [16] = {2},
    [17] = {3},
    [18] = {4},
    [19] = {5},
    [20] = {6},
    [33] = {7},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {6},
    timers = {
    { eventId = 56, repeating = true, intervalGameMinutes = 1.5, remainingGameMinutes = 1.5 },
    },
})

RegisterEvent(1, "Elevator", function()
    evt.SetDoorState(1, DoorAction.Trigger)
end, "Elevator")

RegisterEvent(2, "Elevator", function()
    evt.SetDoorState(2, DoorAction.Trigger)
end, "Elevator")

RegisterEvent(3, "Elevator", function()
    evt.SetDoorState(3, DoorAction.Trigger)
end, "Elevator")

RegisterEvent(4, "Door.", function()
    evt.SetDoorState(4, DoorAction.Trigger)
end, "Door.")

RegisterEvent(5, "Switch", function()
    evt.SetDoorState(5, DoorAction.Trigger)
    evt.SetDoorState(10, DoorAction.Trigger)
end, "Switch")

RegisterEvent(6, "Switch", function()
    evt.SetDoorState(6, DoorAction.Trigger)
    evt.SetDoorState(11, DoorAction.Trigger)
end, "Switch")

RegisterEvent(7, "Door.", function()
    evt.SetDoorState(7, DoorAction.Close)
end, "Door.")

RegisterEvent(8, "Door.", function()
    evt.SetDoorState(8, DoorAction.Close)
end, "Door.")

RegisterEvent(9, "Door.", function()
    evt.SetDoorState(9, DoorAction.Close)
end, "Door.")

RegisterEvent(10, "Door.", function()
    evt.SetDoorState(10, DoorAction.Close)
end, "Door.")

RegisterEvent(11, "Door.", function()
    evt.SetDoorState(11, DoorAction.Close)
end, "Door.")

RegisterEvent(13, "Switch", function()
    evt.SetDoorState(13, DoorAction.Trigger)
    evt.SetDoorState(12, DoorAction.Trigger)
end, "Switch")

RegisterEvent(14, "Sarcophagus", function()
    evt.OpenChest(0)
end, "Sarcophagus")

RegisterEvent(15, "Sarcophagus", function()
    evt.OpenChest(1)
end, "Sarcophagus")

RegisterEvent(16, "Sarcophagus", function()
    evt.OpenChest(2)
end, "Sarcophagus")

RegisterEvent(17, "Sarcophagus", function()
    evt.OpenChest(3)
end, "Sarcophagus")

RegisterEvent(18, "Sarcophagus", function()
    evt.OpenChest(4)
end, "Sarcophagus")

RegisterEvent(19, "Sarcophagus", function()
    evt.OpenChest(5)
end, "Sarcophagus")

RegisterEvent(20, "Sarcophagus", function()
    evt.OpenChest(6)
end, "Sarcophagus")

RegisterEvent(21, "Burial niche", function()
    evt.StatusText("Fumes make you feel sick.")
    evt.ForPlayer(6)
    AddValue(Unconscious, 2)
end, "Burial niche")

RegisterEvent(22, "Burial niche", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.StatusText("You find something among the bones.")
        AddValue(Gold, 2000)
        AddValue(MapVar(2), 1)
        return
    end
    evt.StatusText("The niche is empty.")
end, "Burial niche")

RegisterEvent(23, "Burial niche", function()
    if not IsAtLeast(MapVar(3), 1) then
        evt.StatusText("You find something among the bones.")
        AddValue(Gold, 2000)
        AddValue(MapVar(3), 1)
        return
    end
    evt.StatusText("The niche is empty.")
end, "Burial niche")

RegisterEvent(24, "Burial niche", function()
    if not IsAtLeast(MapVar(4), 1) then
        evt.StatusText("You find something among the bones.")
        AddValue(Gold, 2000)
        AddValue(MapVar(4), 1)
        return
    end
    evt.StatusText("The niche is empty.")
end, "Burial niche")

RegisterEvent(25, "Burial niche", function()
    if not IsAtLeast(MapVar(5), 1) then
        evt.StatusText("You find something among the bones.")
        AddValue(Gold, 2000)
        AddValue(MapVar(5), 1)
        return
    end
    evt.StatusText("The niche is empty.")
end, "Burial niche")

RegisterEvent(26, "Burial niche", function()
    if not IsAtLeast(MapVar(6), 1) then
        evt.StatusText("You find something among the bones.")
        AddValue(Gold, 2000)
        AddValue(MapVar(6), 1)
        return
    end
    evt.StatusText("The niche is empty.")
end, "Burial niche")

RegisterEvent(27, "Burial niche", function()
    if not IsAtLeast(MapVar(6), 1) then
        evt.StatusText("You find something among the bones.")
        AddValue(Gold, 2000)
        AddValue(MapVar(6), 1)
        return
    end
    evt.StatusText("The niche is empty.")
end, "Burial niche")

RegisterEvent(28, "Burial niche", function()
    if not IsAtLeast(MapVar(6), 1) then
        evt.StatusText("You find something among the bones.")
        AddValue(Gold, 2000)
        AddValue(MapVar(6), 1)
        return
    end
    evt.StatusText("The niche is empty.")
end, "Burial niche")

RegisterEvent(29, "Burial niche", function()
    if not IsAtLeast(MapVar(7), 1) then
        evt.StatusText("You find something among the bones.")
        AddValue(InventoryItem(1766), 1766) -- Cure Wounds
        AddValue(MapVar(7), 1)
        return
    end
    evt.StatusText("The niche is empty.")
end, "Burial niche")

RegisterEvent(30, "Burial niche", function()
    if not IsAtLeast(MapVar(8), 1) then
        evt.StatusText("You find something among the bones.")
        AddValue(InventoryItem(1715), 1715) -- Cavalier Gauntlets
        AddValue(MapVar(8), 1)
        return
    end
    evt.StatusText("The niche is empty.")
end, "Burial niche")

RegisterEvent(31, "Burial niche", function()
    if not IsAtLeast(MapVar(9), 1) then
        evt.StatusText("You find something among the bones.")
        AddValue(InventoryItem(1744), 1744) -- Druid Wand of Lashing
        AddValue(MapVar(9), 1)
        return
    end
    evt.StatusText("The niche is empty.")
end, "Burial niche")

RegisterEvent(32, "Burial niche", function()
    if not IsAtLeast(MapVar(10), 1) then
        evt.StatusText("You find something among the bones.")
        AddValue(InventoryItem(1760), 1760) -- Dragon Wand of Shrinking
        AddValue(MapVar(10), 1)
        return
    end
    evt.StatusText("The niche is empty.")
end, "Burial niche")

RegisterEvent(33, "Sarcophagus", function()
    evt.OpenChest(7)
end, "Sarcophagus")

RegisterEvent(34, "Gate", function()
    evt.StatusText("The door will not budge.")
end, "Gate")

RegisterEvent(35, "Burial niche", function()
    evt.StatusText("The niche is empty.")
end, "Burial niche")

RegisterEvent(36, "Burial niche", function()
    if not IsAtLeast(MapVar(11), 1) then
        evt.StatusText("You find something among the bones.")
        AddValue(Gold, 500)
        AddValue(MapVar(11), 1)
        return
    end
    evt.StatusText("The niche is empty.")
end, "Burial niche")

RegisterEvent(37, "Burial niche", function()
    if not IsAtLeast(MapVar(12), 1) then
        evt.StatusText("You find something among the bones.")
        AddValue(Gold, 500)
        AddValue(MapVar(12), 1)
        return
    end
    evt.StatusText("The niche is empty.")
end, "Burial niche")

RegisterEvent(38, "Burial niche", function()
    if not IsAtLeast(MapVar(13), 1) then
        evt.StatusText("You find something among the bones.")
        AddValue(Gold, 500)
        AddValue(MapVar(13), 1)
        return
    end
    evt.StatusText("The niche is empty.")
end, "Burial niche")

RegisterEvent(39, "Door.", function()
    evt.StatusText("The door will not budge.")
    evt.SetDoorState(2, DoorAction.Close)
end, "Door.")

RegisterEvent(40, "Door.", function()
    evt.StatusText("The door will not budge.")
    evt.SetDoorState(3, DoorAction.Close)
end, "Door.")

RegisterEvent(50, "Exit.", function()
    evt.MoveToMap(-19989, -1020, 159, 256, 0, 0, 0, 0, "outc2.odm")
end, "Exit.")

RegisterEvent(51, "Burial niche", function()
    if IsAtLeast(MapVar(31), 1) then return end
    SetValue(MapVar(31), 1)
    evt.GiveItem(4, 39)
end, "Burial niche")

RegisterEvent(52, "Burial niche", function()
    if IsAtLeast(MapVar(32), 1) then return end
    SetValue(MapVar(32), 1)
    evt.GiveItem(4, 37)
end, "Burial niche")

RegisterEvent(53, "Burial niche", function()
    if IsAtLeast(MapVar(33), 1) then return end
    SetValue(MapVar(33), 1)
    evt.GiveItem(4, 34)
end, "Burial niche")

RegisterEvent(54, "Burial niche", function()
    if IsAtLeast(MapVar(34), 1) then return end
    SetValue(MapVar(34), 1)
    evt.GiveItem(4, 38)
end, "Burial niche")

RegisterEvent(55, "Legacy event 55", function()
    if IsAtLeast(MapVar(35), 1) then return end
    SetValue(MapVar(35), 1)
    AddValue(InventoryItem(1757), 1757) -- Dragon Wand of Implosion
end)

RegisterEvent(56, "Legacy event 56", function()
    evt.CastSpell(6, 7, 1, -1088, 1984, 896, 960, 3456, 896) -- Fireball
    evt.CastSpell(6, 7, 1, -1088, 4160, 896, 960, 2624, 896) -- Fireball
    evt.CastSpell(6, 7, 1, 832, 4160, 896, -1280, 2688, 896) -- Fireball
    evt.CastSpell(6, 7, 1, 832, 1984, 896, -1216, 3584, 896) -- Fireball
end)

