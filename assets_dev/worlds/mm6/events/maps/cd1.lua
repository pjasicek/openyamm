-- Castle Alamos
-- generated from legacy EVT/STR

SetMapMetadata({
    levitateTrapEvents = {70},
    onLoad = {60},
    onLeave = {},
    openedChestIds = {
    [30] = {0},
    [41] = {1},
    [42] = {2},
    [43] = {3},
    [44] = {4},
    [45] = {5},
    [51] = {6},
    [52] = {7},
    [53] = {8},
    [54] = {9},
    [55] = {10},
    [56] = {11},
    [57] = {12},
    [58] = {13},
    },
    contextActions = {
    [1] = { kind = "open_door", source = "title" },
    [4] = { kind = "open_door", source = "title" },
    [5] = { kind = "open_door", source = "title" },
    [6] = { kind = "open_door", source = "title" },
    [7] = { kind = "open_door", source = "title" },
    [8] = { kind = "open_door", source = "title" },
    [9] = { kind = "open_door", source = "title" },
    [10] = { kind = "open_door", source = "title" },
    [11] = { kind = "open_door", source = "title" },
    [12] = { kind = "open_door", source = "title" },
    [13] = { kind = "teleport", source = "heuristic" },
    [14] = { kind = "teleport", source = "heuristic" },
    [18] = { kind = "secret_event", source = "heuristic", hidden = true },
    [30] = { kind = "open_chest", source = "opcode", chestIds = {0} },
    [31] = { kind = "use_switch", source = "title" },
    [33] = { kind = "open_door", source = "title" },
    [35] = { kind = "open_door", source = "opcode" },
    [41] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [42] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [43] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [44] = { kind = "open_chest", source = "opcode", chestIds = {4} },
    [45] = { kind = "open_chest", source = "opcode", chestIds = {5} },
    [47] = { kind = "leave_dungeon", source = "opcode", targetMap = "outd1.odm", targetName = "Silver Cove" },
    [51] = { kind = "open_chest", source = "opcode", chestIds = {6} },
    [52] = { kind = "open_chest", source = "opcode", chestIds = {7} },
    [53] = { kind = "open_chest", source = "opcode", chestIds = {8} },
    [54] = { kind = "open_chest", source = "opcode", chestIds = {9} },
    [55] = { kind = "open_chest", source = "opcode", chestIds = {10} },
    [56] = { kind = "open_chest", source = "opcode", chestIds = {11} },
    [57] = { kind = "open_chest", source = "opcode", chestIds = {12} },
    [58] = { kind = "open_chest", source = "opcode", chestIds = {13} },
    [61] = { kind = "leave_dungeon", source = "opcode", targetMap = "oute1.odm", targetName = "Eel Infested Waters" },
    [62] = { kind = "open_door", source = "title" },
    [63] = { kind = "open_door", source = "title" },
    [64] = { kind = "generic_event", source = "opcode" },
    [65] = { kind = "generic_event", source = "opcode" },
    [66] = { kind = "generic_event", source = "opcode" },
    [67] = { kind = "generic_event", source = "opcode" },
    [68] = { kind = "generic_event", source = "opcode" },
    [69] = { kind = "teleport", source = "heuristic" },
    },
    textureNames = {},
    spriteNames = {"crysdisc"},
    castSpellIds = {6},
    timers = {
    { eventId = 70, sourceEventId = 70, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "interval", intervalHalfMinutes = 20 },
    },
})

RegisterEvent(1, "Door", function()
    evt.SetDoorState(1, DoorAction.Close)
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
end, "Door")

RegisterEvent(8, "Door", function()
    if not HasItem(2189) then -- Teleporter Key
        evt.StatusText("The door is locked.")
        return
    end
    RemoveItem(2189) -- Teleporter Key
    evt.SetDoorState(8, DoorAction.Close)
end, "Door")

RegisterEvent(9, "Door", function()
    evt.SetDoorState(9, DoorAction.Close)
end, "Door")

RegisterEvent(10, "Door", function()
    if not HasItem(2188) then -- Treasure Room Key
        evt.StatusText("The door is locked.")
        return
    end
    RemoveItem(2188) -- Treasure Room Key
    evt.SetDoorState(10, DoorAction.Close)
end, "Door")

RegisterEvent(11, "Door", function()
    evt.SetDoorState(11, DoorAction.Close)
end, "Door")

RegisterEvent(12, "Door", function()
    evt.SetDoorState(12, DoorAction.Close)
end, "Door")

RegisterEvent(13, nil, function()
    evt.MoveToMap(-2112, 14240, 40, 0, 0, 0, 0, 0)
end)

RegisterEvent(14, nil, function()
    evt.MoveToMap(4480, 8064, -340, 512, 0, 0, 0, 0)
end)

RegisterEvent(18, nil, function()
    if IsAtLeast(MapVar(2), 5) then return end
    evt.SummonMonsters(3, 3, 5, -2194, 4048, 225, 0, 0) -- encounter slot 3 "ElemAir" tier C, count 5, pos=(-2194, 4048, 225), actor group 0, no unique actor name
    AddValue(MapVar(2), 1)
end)

RegisterEvent(30, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(31, "Switch", function()
    evt.SetDoorState(31, DoorAction.Close)
    evt.SetDoorState(32, DoorAction.Close)
end, "Switch")

RegisterEvent(33, "Door", function()
    evt.StatusText("The door won't budge.")
end, "Door")

RegisterEvent(35, nil, function()
    evt.SetDoorState(35, DoorAction.Trigger)
end)

RegisterEvent(41, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(42, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(43, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(44, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(45, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(47, "Teleporter", function()
    if IsQBitSet(QBit(1078)) then -- Chris
        evt.MoveToMap(7829, -7173, 224, 568, 0, 0, 0, 0, "outd1.odm") -- Silver Cove
    end
end, "Teleporter")

RegisterEvent(51, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(52, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(53, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(54, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(55, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(56, "Chest", function()
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(57, "Chest", function()
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(58, "Chest", function()
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(59, "Exit", function()
    if IsQBitSet(QBit(1078)) then return end -- Chris
    SetQBit(QBit(1078)) -- Chris
    evt.SetSprite(394, 1, "crysdisc")
    AddValue(InventoryItem(2171), 2171) -- Memory Crystal Beta
    SetQBit(QBit(1216)) -- Quest item bits for seer
end, "Exit")

RegisterEvent(60, nil, function()
    if IsQBitSet(QBit(1078)) then -- Chris
        evt.SetSprite(394, 1, "crysdisc")
    end
end)

RegisterEvent(61, "Exit", function()
    evt.MoveToMap(13830, 7687, 673, 512, 0, 0, 0, 0, "oute1.odm") -- Eel Infested Waters
end, "Exit")

RegisterEvent(62, "Door", function()
    evt.SetDoorState(2, DoorAction.Close)
end, "Door")

RegisterEvent(63, "Door", function()
    evt.SetDoorState(3, DoorAction.Close)
end, "Door")

RegisterEvent(64, "Tree", function(continueStep)
    if continueStep == 3 then
    end
    if continueStep ~= nil then return end
    SetValue(MapVar(3), 1)
    evt.SetMessage("\"Etched into the tree a message reads:                                                                                                                                                                                                                              The first is half the forth plus one, better hurry or you'll be done!\"")
    evt._PressAnyKey(64, 3)
end, "Tree")

RegisterEvent(65, "Tree", function(continueStep)
    if continueStep == 3 then
    end
    if continueStep ~= nil then return end
    SetValue(MapVar(4), 1)
    evt.SetMessage("\"Etched into the tree a message reads:                                                                                                                                                                                                                              The second is next to the third, oh so pretty like a bird!\"")
    evt._PressAnyKey(65, 3)
end, "Tree")

RegisterEvent(66, "Tree", function(continueStep)
    if continueStep == 3 then
    end
    if continueStep ~= nil then return end
    SetValue(MapVar(5), 1)
    evt.SetMessage("\"Etched into the tree a message reads:                                                                                                                                                                                                                              The third is the first of twenty six, A through Z you'll have to mix!\"")
    evt._PressAnyKey(66, 3)
end, "Tree")

RegisterEvent(67, "Tree", function(continueStep)
    if continueStep == 3 then
    end
    if continueStep ~= nil then return end
    SetValue(MapVar(6), 1)
    evt.SetMessage("\"Etched into the tree a message reads:                                                                                                                                                                                                                              The fifth is twice the second, five letters in all I reckon!\"")
    evt._PressAnyKey(67, 3)
end, "Tree")

RegisterEvent(68, "Tree", function(continueStep)
    if continueStep == 3 then
    end
    if continueStep ~= nil then return end
    SetValue(MapVar(7), 1)
    evt.SetMessage("\"Etched into the tree a message reads:                                                                                                                                                                                                                              The forth is eight from the end, Archibald really is your friend!\"")
    evt._PressAnyKey(68, 3)
end, "Tree")

RegisterEvent(69, nil, function(continueStep)
    if continueStep == 4 then
        evt.StatusText("Wrong!")
        evt.MoveToMap(-3136, 2240, 224, 1024, 0, 0, 0, 0)
        return
    end
    if continueStep == 23 then
        evt.StatusText("\"Who told you!  Alright, you may pass!\"")
        SetValue(MapVar(8), 1)
    end
    if continueStep == 17 then
        evt.StatusText("Wrong!")
        evt.MoveToMap(-3136, 2240, 224, 1024, 0, 0, 0, 0)
        return
    end
    if continueStep == 20 then
        evt.StatusText("Ok!")
        SetValue(MapVar(8), 1)
        return
    end
    if continueStep ~= nil then return end
    if IsAtLeast(MapVar(8), 1) then
        return
    elseif IsAtLeast(MapVar(3), 1) then
        if IsAtLeast(MapVar(4), 1) then
            if IsAtLeast(MapVar(5), 1) then
                if IsAtLeast(MapVar(6), 1) then
                    if IsAtLeast(MapVar(7), 1) then
                        evt.SetMessage("Restricted area - Keep out.")
                        evt.AskQuestion(69, 17, 14, 20, 15, 16, "What's the password?", {"JBARD", "jbard"})
                        return nil
                    end
                end
            end
        end
        evt.SetMessage("Restricted area - Keep out.")
        evt.AskQuestion(69, 4, 14, 23, 15, 16, "What's the password?", {"JBARD", "jbard"})
        return nil
    else
        evt.SetMessage("Restricted area - Keep out.")
        evt.AskQuestion(69, 4, 14, 23, 15, 16, "What's the password?", {"JBARD", "jbard"})
        return nil
    end
end)

RegisterEvent(70, nil, function()
    evt.CastSpell(6, 10, 1, 2995, 9373, -840, 2000, 9373, -840) -- Fireball
end)

