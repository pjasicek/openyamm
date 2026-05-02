-- Free Haven Sewer
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [10] = {0},
    [11] = {1},
    [14] = {2},
    [15] = {3},
    [16] = {4},
    [17] = {5},
    [18] = {6},
    },
    textureNames = {},
    spriteNames = {"0"},
    castSpellIds = {90},
    timers = {
    { eventId = 34, repeating = true, intervalGameMinutes = 5, remainingGameMinutes = 5 },
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

RegisterEvent(6, "Legacy event 6", function()
    evt.SetDoorState(6, DoorAction.Close)
end)

RegisterEvent(7, "Legacy event 7", function()
    evt.SetDoorState(7, DoorAction.Close)
end)

RegisterEvent(8, "Legacy event 8", function()
    if IsQBitSet(QBit(1194)) then -- NPC
        return
    elseif IsQBitSet(QBit(1122)) then -- Capture the Prince of Thieves and bring him to Lord Anthony Stone at Castle Stone. - NPC
        SetQBit(QBit(1701)) -- Replacement for NPCs ¹17 ver. 6
        SetQBit(QBit(1194)) -- NPC
        evt.SpeakNPC(802) -- The Prince of Thieves
        return
    else
        return
    end
end)

RegisterEvent(9, "Torch", function()
    evt.SetSprite(112, 1, "0")
    evt.SetLight(0, 1)
end, "Torch")

RegisterEvent(10, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(11, "Cabinet", function()
    evt.OpenChest(1)
end, "Cabinet")

RegisterEvent(12, "Sewer Grate", function()
    if not IsAtLeast(MapVar(5), 1) then
        AddValue(InventoryItem(2198), 2198) -- Sewer Key
        evt.StatusText("Something's stashed here!")
        SetValue(MapVar(5), 1)
        return
    end
    if IsAtLeast(MapVar(2), 12) then return end
    local randomStep = PickRandomOption(12, 7, {7, 10, 14, 17, 18})
    if randomStep == 7 then
        AddValue(MapVar(2), 1)
        local randomStep = PickRandomOption(12, 9, {19, 23, 19})
        if randomStep == 19 then
            evt.DamagePlayer(5, 2, 30)
            evt.StatusText("Ouch!")
            AddValue(MapVar(2), 1)
            return
        elseif randomStep == 23 then
            AddValue(MapVar(2), 1)
            return
        end
    elseif randomStep == 10 then
        AddValue(MapVar(2), 2)
        AddValue(Gold, 2000)
        evt.StatusText("Something's stashed here!")
        return
    elseif randomStep == 14 then
        AddValue(Gold, 1000)
        evt.StatusText("Something's stashed here!")
        AddValue(MapVar(2), 1)
        return
    elseif randomStep == 17 then
        return
    elseif randomStep == 18 then
        return
    end
end, "Sewer Grate")

RegisterEvent(13, "Door", function()
    if not HasItem(2198) then -- Sewer Key
        evt.StatusText("The door is locked.")
        return
    end
    evt.SetDoorState(8, DoorAction.Close)
    RemoveItem(2198) -- Sewer Key
end, "Door")

RegisterEvent(14, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(15, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(16, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(17, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(18, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(19, "Well", function()
    if not IsAtLeast(MapVar(4), 1) then
        evt.StatusText("Refreshing!")
        SetAutonote(459) -- +10 Hit points restored south west of the main Sewer chamber.
        SetValue(MapVar(4), 20)
        return
    end
    SubtractValue(MapVar(4), 1)
    AddValue(CurrentHealth, 10)
    evt.StatusText("+10 Hit points restored.")
    SetAutonote(459) -- +10 Hit points restored south west of the main Sewer chamber.
    SetValue(MapVar(4), 20)
end, "Well")

RegisterEvent(20, "Exit", function()
    evt.MoveToMap(5322, 16780, 256, 512, 0, 0, 0, 0, "outc2.odm")
end, "Exit")

RegisterEvent(21, "Exit", function()
    evt.MoveToMap(10592, 16625, 161, 1024, 0, 0, 0, 0, "outc2.odm")
end, "Exit")

RegisterEvent(22, "Exit", function()
    evt.MoveToMap(12226, 11741, 1, 1024, 0, 0, 0, 0, "outc2.odm")
end, "Exit")

RegisterEvent(23, "Exit", function()
    evt.MoveToMap(12322, 8748, 256, 512, 0, 0, 0, 0, "outc2.odm")
end, "Exit")

RegisterEvent(24, "Exit", function()
    evt.MoveToMap(9465, 8037, 256, 1024, 0, 0, 0, 0, "outc2.odm")
end, "Exit")

RegisterEvent(25, "Exit", function()
    evt.MoveToMap(12184, 8703, 256, 512, 0, 0, 0, 0, "outc2.odm")
end, "Exit")

RegisterEvent(26, "Door", function()
    evt.SetDoorState(9, DoorAction.Close)
end, "Door")

RegisterEvent(27, "Cylinder", function()
    if IsQBitSet(QBit(1200)) then -- NPC
        evt.SetDoorState(21, DoorAction.Open)
    end
end, "Cylinder")

RegisterEvent(28, "Legacy event 28", function()
    if IsQBitSet(QBit(1200)) then -- NPC
        evt.MoveToMap(-3078, 2819, 2049, 1536, 0, 0, 0, 0, "6t6.blv")
    end
end)

RegisterEvent(30, "Sewer Grate", function()
    if IsAtLeast(MapVar(7), 4) then return end
    AddValue(MapVar(7), 1)
    AddValue(InventoryItem(220), 220) -- Potion Bottle
end, "Sewer Grate")

RegisterEvent(31, "Sewer Grate", function()
    if IsAtLeast(MapVar(8), 4) then return end
    AddValue(MapVar(8), 1)
    AddValue(InventoryItem(221), 221) -- Catalyst
end, "Sewer Grate")

RegisterEvent(32, "Sewer Grate", function()
    if IsAtLeast(MapVar(9), 4) then return end
    AddValue(MapVar(9), 1)
    AddValue(InventoryItem(222), 222) -- Cure Wounds
end, "Sewer Grate")

RegisterEvent(33, "Sewer Grate", function()
    if IsAtLeast(MapVar(10), 4) then return end
    AddValue(MapVar(10), 1)
    AddValue(InventoryItem(223), 223) -- Magic Potion
end, "Sewer Grate")

RegisterEvent(34, "Legacy event 34", function()
    evt.CastSpell(90, 6, 1, -4864, 3904, 200, -4000, 3904, 200) -- Toxic Cloud
    evt.CastSpell(90, 6, 1, -1280, 1152, 142, -1280, 3000, 142) -- Toxic Cloud
    evt.CastSpell(90, 6, 1, 2688, 5760, 142, 2000, 5760, 142) -- Toxic Cloud
    evt.CastSpell(90, 6, 1, 2624, 1216, 142, -2304, 6016, 142) -- Toxic Cloud
    evt.CastSpell(90, 6, 1, 1536, 6144, 142, 1536, 4000, 142) -- Toxic Cloud
    evt.CastSpell(90, 6, 1, 384, 3328, 1700, 384, 3328, 0) -- Toxic Cloud
end)

