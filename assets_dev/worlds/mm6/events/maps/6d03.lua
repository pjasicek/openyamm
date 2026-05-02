-- Shadow Guild Hideout
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {25},
    onLeave = {},
    openedChestIds = {
    [17] = {1},
    [18] = {2},
    [19] = {3},
    },
    textureNames = {},
    spriteNames = {"0"},
    castSpellIds = {6},
    timers = {
    },
})

RegisterEvent(2, "Door", function()
    evt.SetDoorState(2, DoorAction.Close)
end, "Door")

RegisterEvent(3, "Switch", function()
    evt.SetDoorState(3, DoorAction.Trigger)
    evt.SetDoorState(1, DoorAction.Trigger)
    evt.SetDoorState(8, DoorAction.Trigger)
end, "Switch")

RegisterEvent(4, "Door", function()
    if not HasItem(2180) then -- Guild Key
        evt.StatusText("The door is locked.")
        return
    end
    RemoveItem(2180) -- Guild Key
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
end, "Door")

RegisterEvent(8, "Switch", function()
    evt.SetDoorState(3, DoorAction.Trigger)
    evt.SetDoorState(1, DoorAction.Trigger)
    evt.SetDoorState(8, DoorAction.Trigger)
end, "Switch")

RegisterEvent(9, "Door", function()
    evt.SetDoorState(9, DoorAction.Close)
end, "Door")

RegisterEvent(10, "Door", function()
    evt.SetDoorState(10, DoorAction.Close)
end, "Door")

RegisterEvent(12, "Switch", function()
    evt.SetDoorState(12, DoorAction.Trigger)
    evt.SetDoorState(13, DoorAction.Trigger)
    evt.SetDoorState(11, DoorAction.Trigger)
end, "Switch")

RegisterEvent(13, "Switch", function()
    evt.SetDoorState(12, DoorAction.Trigger)
    evt.SetDoorState(13, DoorAction.Trigger)
    evt.SetDoorState(11, DoorAction.Trigger)
end, "Switch")

RegisterEvent(14, "Door", function()
    evt.SetDoorState(14, DoorAction.Close)
end, "Door")

RegisterEvent(15, "Legacy event 15", function()
    evt.SetDoorState(15, DoorAction.Close)
end)

RegisterEvent(16, "Door", function()
    evt.SetDoorState(16, DoorAction.Close)
end, "Door")

RegisterEvent(17, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(18, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(19, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(20, "Exit", function()
    evt.MoveToMap(-350, 18784, 256, 1792, 0, 0, 0, 0, "outd3.odm")
end, "Exit")

RegisterEvent(21, "Legacy event 21", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.ForPlayer(Players.All)
        if not HasItem(2180) then -- Guild Key
            evt.CastSpell(6, 3, 1, -52, 1162, 128, 0, 0, 0) -- Fireball
            return
        end
    end
    SetValue(MapVar(2), 1)
end)

RegisterEvent(22, "Legacy event 22", function()
    if IsQBitSet(QBit(1036)) then return end -- 12 D3, given when you save Mom.
    evt.SpeakNPC(978) -- Sharry Carnegie
    SetQBit(QBit(1703)) -- Replacement for NPCs ¹193 ver. 6
    SetQBit(QBit(1036)) -- 12 D3, given when you save Mom.
end)

RegisterEvent(25, "Legacy event 25", function()
    if IsQBitSet(QBit(1036)) then -- 12 D3, given when you save Mom.
        evt.SetSprite(52, 1, "0")
        evt.SetSprite(53, 1, "0")
        evt.SetSprite(54, 1, "0")
        evt.SetSprite(55, 1, "0")
        evt.SetSprite(56, 1, "0")
        evt.SetSprite(57, 1, "0")
    end
end)

RegisterEvent(26, "Legacy event 26", function()
    if IsAtLeast(MapVar(3), 1) then return end
    SetValue(MapVar(3), 1)
    evt.GiveItem(4, ItemType.Ring_)
end)

