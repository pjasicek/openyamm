-- pending
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [5] = {1},
    [6] = {0},
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

RegisterEvent(3, "Dresser", function()
    evt.SetDoorState(3, DoorAction.Close)
end, "Dresser")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(4, DoorAction.Close)
end, "Door")

RegisterEvent(5, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(6, "Bag", function()
    evt.OpenChest(0)
end, "Bag")

