-- Temple of the Fist
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {11},
    onLeave = {},
    openedChestIds = {
    [5] = {0},
    [6] = {1},
    [7] = {2},
    },
    contextActions = {
    [1] = { kind = "open_door", source = "title" },
    [3] = { kind = "open_door", source = "opcode" },
    [4] = { kind = "use_switch", source = "title" },
    [5] = { kind = "open_chest", source = "opcode", chestIds = {0} },
    [6] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [7] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [8] = { kind = "generic_event", source = "opcode" },
    [9] = { kind = "generic_event", source = "opcode" },
    [10] = { kind = "open_door", source = "title" },
    [50] = { kind = "leave_dungeon", source = "opcode", targetMap = "outd2.odm", targetName = "Bootleg Bay" },
    },
    textureNames = {},
    spriteNames = {"0"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Door", function()
    evt.SetDoorState(1, DoorAction.Close)
end, "Door")

RegisterEvent(2, "Door", nil, "Door")

RegisterEvent(3, "Flickering Torch", function()
    evt.SetDoorState(3, DoorAction.Close)
    evt.StatusText("You pull the torch and it shifts in your hand")
end, "Flickering Torch")

RegisterEvent(4, "Switch", function()
    evt.SetDoorState(4, DoorAction.Close)
    evt.SetDoorState(2, DoorAction.Close)
end, "Switch")

RegisterEvent(5, "Cabinet", function()
    evt.OpenChest(0)
end, "Cabinet")

RegisterEvent(6, "Cabinet", function()
    evt.OpenChest(1)
end, "Cabinet")

RegisterEvent(7, "Full sack", function()
    evt.OpenChest(2)
end, "Full sack")

RegisterEvent(8, nil, function()
    evt.ForPlayer(Players.All)
    SubtractValue(MightBonus, 10)
    evt.StatusText("The skulls seem to sap your might")
end)

RegisterEvent(9, "Evil Crystal", function()
    if IsQBitSet(QBit(1045)) then return end -- 21 T2, Given when evil crystal is destroyed
    evt.SetSprite(25, 0, "0")
    SetQBit(QBit(1045)) -- 21 T2, Given when evil crystal is destroyed
    evt.StatusText("You have destroyed the evil crystal")
end, "Evil Crystal")

RegisterEvent(10, "Door", function()
    evt.StatusText("The door won't budge")
end, "Door")

RegisterEvent(11, nil, function()
    if IsQBitSet(QBit(1045)) then -- 21 T2, Given when evil crystal is destroyed
        evt.SetSprite(25, 0, "0")
    end
end)

RegisterEvent(50, "Exit", function()
    evt.MoveToMap(-21001, -4653, 257, 1536, 0, 0, 0, 6, "outd2.odm") -- Bootleg Bay
end, "Exit")

RegisterEvent(55, nil, function()
    if IsAtLeast(MapVar(2), 1) then return end
    SetValue(MapVar(2), 1)
    AddValue(InventoryItem(1877), 1877) -- Flying Fist
end)

RegisterEvent(56, nil, function()
    if IsAtLeast(MapVar(3), 1) then return end
    SetValue(MapVar(3), 1)
    AddValue(InventoryItem(1877), 1877) -- Flying Fist
end)

RegisterEvent(57, nil, function()
    if IsAtLeast(MapVar(4), 1) then return end
    SetValue(MapVar(4), 1)
    AddValue(InventoryItem(1877), 1877) -- Flying Fist
end)

RegisterEvent(58, nil, function()
    if IsAtLeast(MapVar(5), 1) then return end
    SetValue(MapVar(5), 1)
    AddValue(InventoryItem(1877), 1877) -- Flying Fist
end)

