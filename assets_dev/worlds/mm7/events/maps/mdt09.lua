-- Wromthrax's Cave
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
    onLeave = {},
    openedChestIds = {
    [176] = {1},
    [177] = {2},
    [178] = {3},
    [179] = {4},
    [180] = {5},
    [181] = {6},
    [182] = {7},
    [183] = {8},
    [184] = {9},
    [185] = {10},
    [186] = {11},
    [187] = {12},
    [188] = {13},
    [189] = {14},
    [190] = {15},
    [191] = {16},
    [192] = {17},
    [193] = {18},
    [194] = {19},
    [195] = {0},
    },
    contextActions = {
    [176] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [177] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [178] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [179] = { kind = "open_chest", source = "opcode", chestIds = {4} },
    [180] = { kind = "open_chest", source = "opcode", chestIds = {5} },
    [181] = { kind = "open_chest", source = "opcode", chestIds = {6} },
    [182] = { kind = "open_chest", source = "opcode", chestIds = {7} },
    [183] = { kind = "open_chest", source = "opcode", chestIds = {8} },
    [184] = { kind = "open_chest", source = "opcode", chestIds = {9} },
    [185] = { kind = "open_chest", source = "opcode", chestIds = {10} },
    [186] = { kind = "open_chest", source = "opcode", chestIds = {11} },
    [187] = { kind = "open_chest", source = "opcode", chestIds = {12} },
    [188] = { kind = "open_chest", source = "opcode", chestIds = {13} },
    [189] = { kind = "open_chest", source = "opcode", chestIds = {14} },
    [190] = { kind = "open_chest", source = "opcode", chestIds = {15} },
    [191] = { kind = "open_chest", source = "opcode", chestIds = {16} },
    [192] = { kind = "open_chest", source = "opcode", chestIds = {17} },
    [193] = { kind = "open_chest", source = "opcode", chestIds = {18} },
    [194] = { kind = "open_chest", source = "opcode", chestIds = {19} },
    [195] = { kind = "open_chest", source = "opcode", chestIds = {0} },
    [501] = { kind = "leave_dungeon", source = "opcode", targetMap = "7out13.odm", targetName = "Tatalia" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 376, sourceEventId = 376, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "interval", intervalHalfMinutes = 7 },
    },
})

RegisterEvent(1, nil, function()
    if IsQBitSet(QBit(535)) then -- Killed dragon when on Crusader quest
        return
    elseif IsQBitSet(QBit(1684)) then -- Replacement for NPCs ¹17 ver. 7
        evt.SetMonGroupBit(56, MonsterBits.Invisible, 0) -- actor group 56: Blue Dragon
        return
    else
        return
    end
end)

RegisterEvent(176, "Door", function()
    evt.OpenChest(1)
end, "Door")

RegisterEvent(177, "Door", function()
    evt.OpenChest(2)
end, "Door")

RegisterEvent(178, "Door", function()
    evt.OpenChest(3)
end, "Door")

RegisterEvent(179, "Door", function()
    evt.OpenChest(4)
end, "Door")

RegisterEvent(180, "Door", function()
    evt.OpenChest(5)
end, "Door")

RegisterEvent(181, "Door", function()
    evt.OpenChest(6)
end, "Door")

RegisterEvent(182, "Door", function()
    evt.OpenChest(7)
end, "Door")

RegisterEvent(183, "Door", function()
    evt.OpenChest(8)
end, "Door")

RegisterEvent(184, "Door", function()
    evt.OpenChest(9)
end, "Door")

RegisterEvent(185, "Door", function()
    evt.OpenChest(10)
end, "Door")

RegisterEvent(186, "Door", function()
    evt.OpenChest(11)
end, "Door")

RegisterEvent(187, "Door", function()
    evt.OpenChest(12)
end, "Door")

RegisterEvent(188, "Door", function()
    evt.OpenChest(13)
end, "Door")

RegisterEvent(189, "Door", function()
    evt.OpenChest(14)
end, "Door")

RegisterEvent(190, "Door", function()
    evt.OpenChest(15)
end, "Door")

RegisterEvent(191, "Door", function()
    evt.OpenChest(16)
end, "Door")

RegisterEvent(192, "Door", function()
    evt.OpenChest(17)
end, "Door")

RegisterEvent(193, "Door", function()
    evt.OpenChest(18)
end, "Door")

RegisterEvent(194, "Door", function()
    evt.OpenChest(19)
end, "Door")

RegisterEvent(195, "Door", function()
    evt.OpenChest(0)
end, "Door")

RegisterEvent(376, nil, function()
    if not IsQBitSet(QBit(534)) then return end -- Kill Wromthrax the Heartless in his cave in Tatalia, then talk to Sir Charles Quixote.
    if IsQBitSet(QBit(535)) then return end -- Killed dragon when on Crusader quest
    if evt.CheckMonstersKilled(ActorKillCheck.Group, 56, 1, false) then -- actor group 56: Blue Dragon; at least 1 matching actor defeated
        evt.ForPlayer(Players.All)
        SetQBit(QBit(535)) -- Killed dragon when on Crusader quest
        evt.SetNPCGreeting(356, 0) -- Sir Charles Quixote greeting cleared
        evt.SpeakNPC(356) -- Sir Charles Quixote
    end
end)

RegisterEvent(501, "Leave the Cave", function()
    evt.MoveToMap(-1037, 21058, 2656, 1536, 0, 0, 0, 4, "7out13.odm") -- Tatalia
end, "Leave the Cave")

