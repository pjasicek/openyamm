-- The Monolith
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {26},
    onLeave = {},
    openedChestIds = {
    [13] = {0},
    [14] = {1},
    },
    contextActions = {
    [1] = { kind = "open_door", source = "opcode" },
    [2] = { kind = "open_door", source = "opcode" },
    [3] = { kind = "open_door", source = "opcode" },
    [4] = { kind = "open_door", source = "opcode" },
    [5] = { kind = "open_door", source = "opcode" },
    [6] = { kind = "open_door", source = "opcode" },
    [7] = { kind = "open_door", source = "opcode" },
    [8] = { kind = "open_door", source = "opcode" },
    [9] = { kind = "open_door", source = "opcode" },
    [10] = { kind = "open_door", source = "title" },
    [11] = { kind = "open_door", source = "opcode" },
    [12] = { kind = "open_door", source = "opcode" },
    [13] = { kind = "open_chest", source = "opcode", chestIds = {0} },
    [14] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [15] = { kind = "open_door", source = "opcode" },
    [16] = { kind = "generic_event", source = "opcode" },
    [17] = { kind = "generic_event", source = "opcode" },
    [18] = { kind = "generic_event", source = "opcode" },
    [19] = { kind = "generic_event", source = "opcode" },
    [20] = { kind = "generic_event", source = "opcode" },
    [21] = { kind = "generic_event", source = "opcode" },
    [22] = { kind = "generic_event", source = "opcode" },
    [23] = { kind = "generic_event", source = "opcode" },
    [24] = { kind = "shrine", source = "title" },
    [25] = { kind = "open_door", source = "title" },
    [50] = { kind = "leave_dungeon", source = "opcode", targetMap = "outd1.odm", targetName = "Silver Cove" },
    },
    textureNames = {"d6flora"},
    spriteNames = {},
    castSpellIds = {63},
    timers = {
    },
})

RegisterEvent(1, "Strange rock", function()
    evt.StatusText("The rock shifts at your touch.")
    evt.SetDoorState(1, DoorAction.Close)
end, "Strange rock")

RegisterEvent(2, "Strange rock", function()
    evt.StatusText("The rock shifts at your touch.")
    evt.SetDoorState(2, DoorAction.Close)
end, "Strange rock")

RegisterEvent(3, "Monolith", function()
    evt.StatusText("The monolith feels strange to the touch.")
    evt.SetDoorState(3, DoorAction.Close)
end, "Monolith")

RegisterEvent(4, "Strange tree", function()
    evt.StatusText("The tree shakes at your touch.")
    evt.SetDoorState(4, DoorAction.Close)
end, "Strange tree")

RegisterEvent(5, nil, function()
    evt.SetDoorState(5, DoorAction.Close)
end)

RegisterEvent(6, "Strange rock", function()
    evt.StatusText("The rock shifts at your touch.")
    evt.SetDoorState(6, DoorAction.Close)
end, "Strange rock")

RegisterEvent(7, "Monolith", function()
    evt.StatusText("The monolith feels strange to the touch.")
    evt.SetDoorState(7, DoorAction.Trigger)
end, "Monolith")

RegisterEvent(8, "Nice Flower", function()
    evt.StatusText("The flowers smell nice.")
    evt.SetDoorState(8, DoorAction.Close)
end, "Nice Flower")

RegisterEvent(9, "Druid statue", function()
    evt.StatusText("The statue shifts as your touch it.")
    evt.SetDoorState(9, DoorAction.Close)
end, "Druid statue")

RegisterEvent(10, "Door", function()
    evt.SetDoorState(10, DoorAction.Close)
end, "Door")

RegisterEvent(11, nil, function()
    evt.SetDoorState(7, DoorAction.Open)
end)

RegisterEvent(12, "Sacred Pool", function()
    evt.StatusText("The pool shimmers as you touch it.")
    evt.SetDoorState(12, DoorAction.Trigger)
end, "Sacred Pool")

RegisterEvent(13, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(14, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(15, "Strange tree", function()
    evt.StatusText("The tree shakes at your touch.")
    evt.SetDoorState(15, DoorAction.Close)
end, "Strange tree")

RegisterEvent(16, "Strange tree", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.StatusText("You search the tree and find something.")
        AddValue(Gold, 1000)
        AddValue(MapVar(2), 1)
        return
    end
    evt.StatusText("You find nothing.")
end, "Strange tree")

RegisterEvent(17, "Strange tree", function()
    if not IsAtLeast(MapVar(3), 1) then
        evt.StatusText("You search the tree and find something.")
        AddValue(Gold, 1500)
        AddValue(MapVar(3), 1)
        return
    end
    evt.StatusText("You find nothing.")
end, "Strange tree")

RegisterEvent(18, "Strange tree", function()
    if not IsAtLeast(MapVar(4), 1) then
        evt.StatusText("You search the tree and find something.")
        AddValue(Gold, 2000)
        AddValue(MapVar(4), 1)
        return
    end
    evt.StatusText("You find nothing.")
end, "Strange tree")

RegisterEvent(19, "Strange tree", function()
    if not IsAtLeast(MapVar(5), 1) then
        evt.StatusText("You search the tree and find something.")
        AddValue(Gold, 2500)
        AddValue(MapVar(5), 1)
        return
    end
    evt.StatusText("You find nothing.")
end, "Strange tree")

RegisterEvent(20, "Strange tree", function()
    if not IsAtLeast(MapVar(6), 1) then
        evt.StatusText("You search the tree and find something.")
        AddValue(Gold, 3000)
        AddValue(MapVar(6), 1)
        return
    end
    evt.StatusText("You find nothing.")
end, "Strange tree")

RegisterEvent(21, "Strange tree", function()
    if not IsAtLeast(MapVar(7), 1) then
        evt.StatusText("You search the tree and find something.")
        AddValue(Gold, 3500)
        AddValue(MapVar(7), 1)
        return
    end
    evt.StatusText("You find nothing.")
end, "Strange tree")

RegisterEvent(22, "Monolith", function()
    evt.StatusText("The monolith feels strange to the touch.")
    evt.CastSpell(63, 3, 2, 0, 0, 0, 0, 0, 0) -- Mass Fear
end, "Monolith")

RegisterEvent(23, "Strange tree", function()
    if not IsAtLeast(MapVar(8), 1) then
        evt.StatusText("You search the tree and find something.")
        AddValue(Gold, 5000)
        AddValue(MapVar(8), 1)
        return
    end
    evt.StatusText("You find nothing.")
end, "Strange tree")

RegisterEvent(24, "Evil Altar", function()
    if IsQBitSet(QBit(1047)) then -- 23 D13, Given when Altar is desecrated
        return
    end
    evt.SetTexture(-949, "d6flora")
    evt.SetTexture(-947, "d6flora")
    evt.SetTexture(-927, "d6flora")
    evt.SetTexture(-928, "d6flora")
    evt.SetTexture(-929, "d6flora")
    evt.SetTexture(-948, "d6flora")
    evt.SetTexture(-945, "d6flora")
    evt.SetTexture(-946, "d6flora")
    evt.SetTexture(-944, "d6flora")
    evt.SetTexture(-943, "d6flora")
    evt.SetTexture(-942, "d6flora")
    evt.StatusText("+5 Personality permanent to Druids and Clerics.")
    for _, player in ipairs(PartyMembers()) do
        evt.ForPlayer(player)
        if IsAtLeast(ClassId, 4) then
            AddValue(BasePersonality, 5)
        end
    end
    for _, player in ipairs(PartyMembers()) do
        evt.ForPlayer(player)
        if IsAtLeast(ClassId, 12) then
            AddValue(BasePersonality, 5)
        end
    end
    evt.ForPlayer(Players.All)
    SetQBit(QBit(1047)) -- 23 D13, Given when Altar is desecrated
end, "Evil Altar")

RegisterEvent(25, "Door", function()
    evt.StatusText("The door will not budge.")
end, "Door")

RegisterEvent(26, nil, function()
    if IsQBitSet(QBit(1047)) then -- 23 D13, Given when Altar is desecrated
        evt.SetTexture(-949, "d6flora")
        evt.SetTexture(-947, "d6flora")
        evt.SetTexture(-927, "d6flora")
        evt.SetTexture(-928, "d6flora")
        evt.SetTexture(-929, "d6flora")
        evt.SetTexture(-948, "d6flora")
        evt.SetTexture(-945, "d6flora")
        evt.SetTexture(-946, "d6flora")
        evt.SetTexture(-944, "d6flora")
        evt.SetTexture(-943, "d6flora")
        evt.SetTexture(-942, "d6flora")
    end
end)

RegisterEvent(50, "Exit", function()
    evt.MoveToMap(-17658, -12361, 257, 1024, 0, 0, 0, 0, "outd1.odm") -- Silver Cove
end, "Exit")

RegisterEvent(51, "Strange rock", function()
    if IsAtLeast(MapVar(22), 1) then
        return
    elseif IsAtLeast(MapVar(21), 1) then
        evt.GiveItem(6, 34)
        evt.GiveItem(6, 39)
        AddValue(InventoryItem(1991), 1991) -- Flying Fist
        SetValue(MapVar(22), 1)
    elseif IsAtLeast(MapVar(19), 1) then
        SetValue(MapVar(20), 1)
        return
    elseif IsAtLeast(MapVar(17), 1) then
        SetValue(MapVar(18), 1)
        return
    elseif IsAtLeast(MapVar(15), 1) then
        SetValue(MapVar(16), 1)
        return
    elseif IsAtLeast(MapVar(13), 1) then
        SetValue(MapVar(14), 1)
        return
    elseif IsAtLeast(MapVar(11), 1) then
        SetValue(MapVar(12), 1)
        return
    else
        return
    end
end, "Strange rock")

RegisterEvent(52, "Strange rock", function()
    if IsAtLeast(MapVar(20), 1) then
        SetValue(MapVar(21), 1)
        return
    elseif IsAtLeast(MapVar(18), 1) then
        SetValue(MapVar(19), 1)
        return
    elseif IsAtLeast(MapVar(16), 1) then
        SetValue(MapVar(17), 1)
        return
    elseif IsAtLeast(MapVar(14), 1) then
        SetValue(MapVar(15), 1)
        return
    elseif IsAtLeast(MapVar(12), 1) then
        SetValue(MapVar(13), 1)
    else
        SetValue(MapVar(11), 1)
    end
end, "Strange rock")

