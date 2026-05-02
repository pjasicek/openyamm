-- Temple of the Moon
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [13] = {1},
    [14] = {2},
    [15] = {3},
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
    evt.SetDoorState(2, DoorAction.Close)
end, "Door")

RegisterEvent(3, "Door", function()
    if not IsAtLeast(MapVar(8), 21) then
        evt.StatusText("The door won't budge")
        return
    end
    evt.SetDoorState(3, DoorAction.Close)
    evt.SetDoorState(4, DoorAction.Close)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(5, DoorAction.Close)
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

RegisterEvent(11, "Switch", function()
    evt.SetDoorState(11, DoorAction.Trigger)
    evt.SetDoorState(12, DoorAction.Trigger)
    evt.SetDoorState(16, DoorAction.Trigger)
end, "Switch")

RegisterEvent(13, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(14, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(15, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(16, "Altar of Might", function()
    if IsAtLeast(MapVar(9), 1) then
        evt.DamagePlayer(5, 4, 10)
        SetValue(MapVar(9), 1)
        SetValue(MapVar(5), 1)
        AddValue(MapVar(8), 3)
        evt.StatusText("Ouch!")
        return
    elseif IsAtLeast(MapVar(5), 1) then
        return
    elseif IsAtLeast(MapVar(2), 1) then
        SetValue(MapVar(5), 1)
        AddValue(MapVar(8), 3)
        evt.ForPlayer(Players.Member0)
        AddValue(BaseMight, 5)
        evt.ForPlayer(Players.Member1)
        AddValue(BaseMight, 5)
        evt.ForPlayer(Players.Member2)
        AddValue(BaseMight, 5)
        evt.ForPlayer(Players.Member3)
        AddValue(BaseMight, 5)
        evt.ForPlayer(Players.Current)
        AddValue(BaseMight, 5)
        evt.StatusText("You kneel at the altar for a moment of silent prayer.")
    else
        evt.DamagePlayer(5, 4, 10)
        SetValue(MapVar(9), 1)
        SetValue(MapVar(5), 1)
        AddValue(MapVar(8), 3)
        evt.StatusText("Ouch!")
    end
end, "Altar of Might")

RegisterEvent(17, "Altar of Life", function()
    if IsAtLeast(MapVar(9), 1) then
        evt.DamagePlayer(5, 4, 10)
        SetValue(MapVar(7), 1)
        AddValue(MapVar(8), 1)
        evt.StatusText("Ouch!")
        return
    elseif IsAtLeast(MapVar(7), 1) then
        evt.StatusText("You kneel at the altar for a moment of silent prayer.")
        return
    else
        SetValue(MapVar(7), 1)
        AddValue(MapVar(8), 1)
        evt.ForPlayer(Players.Member0)
        AddValue(BasePersonality, 5)
        evt.ForPlayer(Players.Member1)
        AddValue(BasePersonality, 5)
        evt.ForPlayer(Players.Member2)
        AddValue(BasePersonality, 5)
        evt.ForPlayer(Players.Member3)
        AddValue(BasePersonality, 5)
        evt.ForPlayer(Players.Current)
        AddValue(BasePersonality, 5)
        evt.StatusText("You kneel at the altar for a moment of silent prayer.")
        return
    end
end, "Altar of Life")

RegisterEvent(18, "Altar of Endurance", function()
    if IsAtLeast(MapVar(9), 1) then
        evt.DamagePlayer(5, 4, 10)
        SetValue(MapVar(9), 1)
        SetValue(MapVar(3), 1)
        AddValue(MapVar(8), 4)
        evt.StatusText("Ouch!")
        return
    elseif IsAtLeast(MapVar(3), 1) then
        evt.StatusText("You kneel at the altar for a moment of silent prayer.")
        return
    elseif IsAtLeast(MapVar(5), 1) then
        SetValue(MapVar(3), 1)
        AddValue(MapVar(8), 4)
        evt.ForPlayer(Players.Member0)
        AddValue(BaseEndurance, 5)
        evt.ForPlayer(Players.Member1)
        AddValue(BaseEndurance, 5)
        evt.ForPlayer(Players.Member2)
        AddValue(BaseEndurance, 5)
        evt.ForPlayer(Players.Member3)
        AddValue(BaseEndurance, 5)
        evt.ForPlayer(Players.Current)
        AddValue(BaseEndurance, 5)
        evt.StatusText("You kneel at the altar for a moment of silent prayer.")
    else
        evt.DamagePlayer(5, 4, 10)
        SetValue(MapVar(9), 1)
        SetValue(MapVar(3), 1)
        AddValue(MapVar(8), 4)
        evt.StatusText("Ouch!")
    end
end, "Altar of Endurance")

RegisterEvent(19, "Altar of Accuracy", function()
    if IsAtLeast(MapVar(9), 1) then
        evt.DamagePlayer(5, 4, 10)
        SetValue(MapVar(9), 1)
        AddValue(MapVar(8), 2)
        SetValue(MapVar(2), 1)
        evt.StatusText("Ouch!")
        return
    elseif IsAtLeast(MapVar(2), 1) then
        evt.StatusText("You kneel at the altar for a moment of silent prayer.")
        return
    elseif IsAtLeast(MapVar(7), 1) then
        SetValue(MapVar(2), 1)
        AddValue(MapVar(8), 2)
        evt.ForPlayer(Players.Member0)
        AddValue(BaseAccuracy, 5)
        evt.ForPlayer(Players.Member1)
        AddValue(BaseAccuracy, 5)
        evt.ForPlayer(Players.Member2)
        AddValue(BaseAccuracy, 5)
        evt.ForPlayer(Players.Member3)
        AddValue(BaseAccuracy, 5)
        evt.ForPlayer(Players.Current)
        AddValue(BaseAccuracy, 5)
        evt.StatusText("You kneel at the altar for a moment of silent prayer.")
    else
        evt.DamagePlayer(5, 4, 10)
        SetValue(MapVar(9), 1)
        AddValue(MapVar(8), 2)
        SetValue(MapVar(2), 1)
        evt.StatusText("Ouch!")
    end
end, "Altar of Accuracy")

RegisterEvent(20, "Altar of Speed", function()
    if IsAtLeast(MapVar(9), 1) then
        SetValue(MapVar(6), 1)
        SetValue(MapVar(9), 1)
        evt.DamagePlayer(5, 4, 10)
        AddValue(MapVar(8), 5)
        evt.StatusText("Ouch!")
        return
    elseif IsAtLeast(MapVar(6), 1) then
        evt.StatusText("You kneel at the altar for a moment of silent prayer.")
        return
    elseif IsAtLeast(MapVar(3), 1) then
        SetValue(MapVar(6), 1)
        AddValue(MapVar(8), 5)
        evt.ForPlayer(Players.Member0)
        AddValue(BaseSpeed, 5)
        evt.ForPlayer(Players.Member1)
        AddValue(BaseSpeed, 5)
        evt.ForPlayer(Players.Member2)
        AddValue(BaseSpeed, 5)
        evt.ForPlayer(Players.Member3)
        AddValue(BaseSpeed, 5)
        evt.ForPlayer(Players.Current)
        AddValue(BaseSpeed, 5)
        evt.StatusText("You kneel at the altar for a moment of silent prayer.")
    else
        SetValue(MapVar(6), 1)
        SetValue(MapVar(9), 1)
        evt.DamagePlayer(5, 4, 10)
        AddValue(MapVar(8), 5)
        evt.StatusText("Ouch!")
    end
end, "Altar of Speed")

RegisterEvent(21, "Altar of Luck", function()
    if IsAtLeast(MapVar(9), 1) then
        evt.DamagePlayer(5, 4, 10)
        SetValue(MapVar(9), 1)
        SetValue(MapVar(4), 1)
        AddValue(MapVar(8), 6)
        evt.StatusText("Ouch!")
        return
    elseif IsAtLeast(MapVar(4), 1) then
        evt.StatusText("You kneel at the altar for a moment of silent prayer.")
        return
    elseif IsAtLeast(MapVar(6), 1) then
        evt.ForPlayer(Players.Member0)
        AddValue(BaseLuck, 2)
        evt.ForPlayer(Players.Member1)
        AddValue(BaseLuck, 5)
        evt.ForPlayer(Players.Member2)
        AddValue(BaseLuck, 5)
        evt.ForPlayer(Players.Member3)
        AddValue(BaseLuck, 5)
        evt.ForPlayer(Players.Current)
        AddValue(BaseLuck, 5)
        SetValue(MapVar(4), 1)
        AddValue(MapVar(8), 6)
        evt.StatusText("You kneel at the altar for a moment of silent prayer.")
    else
        evt.DamagePlayer(5, 4, 10)
        SetValue(MapVar(9), 1)
        SetValue(MapVar(4), 1)
        AddValue(MapVar(8), 6)
        evt.StatusText("Ouch!")
    end
end, "Altar of Luck")

RegisterEvent(22, "Plaque", function()
    evt.SimpleMessage("\"Life above all, Accuracy before Might, Endurance before Speed, and finally, Luck.\"")
end, "Plaque")

RegisterEvent(23, "Door", function()
    evt.SetDoorState(13, DoorAction.Close)
end, "Door")

RegisterEvent(24, "Door", function()
    evt.SetDoorState(14, DoorAction.Close)
end, "Door")

RegisterEvent(25, "Door", function()
    evt.SetDoorState(15, DoorAction.Close)
end, "Door")

RegisterEvent(27, "Altar of the Moon", function()
    if IsQBitSet(QBit(1198)) then return end -- NPC
    if not IsQBitSet(QBit(1143)) then return end -- Visit the Altar of the Moon in the Temple of the Moon at midnight of a full moon. - NPC
    if IsAtLeast(Hour, 1) then
        return
    elseif IsAtLeast(Hour, 0) then
        evt.SpeakNPC(1091) -- Loretta Fleise
    else
        return
    end
end, "Altar of the Moon")

RegisterEvent(50, "Exit", function()
    evt.MoveToMap(-18178, 19695, 161, 512, 0, 0, 0, 0, "outc2.odm")
end, "Exit")

RegisterEvent(51, "Legacy event 51", function()
    if IsAtLeast(MapVar(21), 1) then return end
    SetValue(MapVar(21), 1)
    evt.GiveItem(6, 37)
end)

RegisterEvent(52, "Legacy event 52", function()
    if IsAtLeast(MapVar(22), 1) then return end
    SetValue(MapVar(22), 1)
    AddValue(InventoryItem(1841), 1841) -- Stone to Flesh
end)

RegisterEvent(53, "Legacy event 53", function()
    if IsAtLeast(MapVar(23), 1) then return end
    SetValue(MapVar(23), 1)
    AddValue(InventoryItem(1841), 1841) -- Stone to Flesh
end)

RegisterEvent(54, "Legacy event 54", function()
    if IsAtLeast(MapVar(24), 1) then return end
    SetValue(MapVar(24), 1)
    AddValue(InventoryItem(1841), 1841) -- Stone to Flesh
end)

RegisterEvent(55, "Legacy event 55", function()
    if IsAtLeast(MapVar(25), 1) then return end
    SetValue(MapVar(25), 1)
    AddValue(InventoryItem(1841), 1841) -- Stone to Flesh
end)

RegisterEvent(56, "Legacy event 56", function()
    if IsAtLeast(MapVar(26), 1) then return end
    SetValue(MapVar(26), 1)
    AddValue(InventoryItem(1841), 1841) -- Stone to Flesh
end)

