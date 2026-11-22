-- Castle Harmondale
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 376, 377, 451},
    onLeave = {2},
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
    [3] = { kind = "open_door", source = "title" },
    [4] = { kind = "open_door", source = "title" },
    [5] = { kind = "open_door", source = "title" },
    [6] = { kind = "open_door", source = "title" },
    [7] = { kind = "open_door", source = "title" },
    [8] = { kind = "open_door", source = "title" },
    [9] = { kind = "open_door", source = "title" },
    [10] = { kind = "open_door", source = "opcode" },
    [11] = { kind = "open_door", source = "title" },
    [12] = { kind = "open_door", source = "title" },
    [13] = { kind = "open_door", source = "title" },
    [14] = { kind = "open_door", source = "title" },
    [15] = { kind = "open_door", source = "opcode" },
    [16] = { kind = "open_door", source = "opcode" },
    [17] = { kind = "open_door", source = "opcode" },
    [18] = { kind = "open_door", source = "title" },
    [19] = { kind = "open_door", source = "title" },
    [20] = { kind = "open_door", source = "title" },
    [21] = { kind = "open_door", source = "title" },
    [22] = { kind = "open_door", source = "title" },
    [23] = { kind = "open_door", source = "title" },
    [24] = { kind = "open_door", source = "title" },
    [25] = { kind = "open_door", source = "title" },
    [26] = { kind = "open_door", source = "opcode" },
    [27] = { kind = "open_door", source = "title" },
    [28] = { kind = "open_door", source = "title" },
    [29] = { kind = "open_door", source = "title" },
    [30] = { kind = "open_door", source = "title" },
    [31] = { kind = "open_door", source = "title" },
    [32] = { kind = "open_door", source = "opcode" },
    [33] = { kind = "open_door", source = "title" },
    [34] = { kind = "open_door", source = "title" },
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
    [416] = { kind = "enter_house", source = "opcode", houseId = 380 },
    [417] = { kind = "enter_house", source = "opcode", houseId = 380 },
    [418] = { kind = "enter_house", source = "opcode", houseId = 380 },
    [419] = { kind = "enter_house", source = "opcode", houseId = 380 },
    [420] = { kind = "enter_house", source = "opcode", houseId = 1169, targetName = "Throne Room" },
    [501] = { kind = "leave_dungeon", source = "opcode", targetMap = "7out02.odm", targetName = "Harmondale" },
    },
    textureNames = {"bannwc-a", "bannwc-b", "ch1b1", "ch1b1el", "ch1b1er", "chb1p6", "chb1p7", "elfhuma", "elfhumb", "nechuma", "nechumb", "tfb09r1a", "tfb09r1b", "tfb09r1c", "tfb09r1d", "tfb09r1e", "tfb09r1f", "tfb09r1g", "tfb09r1h", "tfb09r1i", "tfb09r1j", "wizh-a", "wizh-b"},
    spriteNames = {"0"},
    castSpellIds = {},
    timers = {
    { eventId = 378, sourceEventId = 378, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "interval", intervalHalfMinutes = 20 },
    },
})

RegisterEvent(1, nil, function()
    if not IsQBitSet(QBit(718)) then -- TP Buff Castle Harmondale
        SetQBit(QBit(718)) -- TP Buff Castle Harmondale
    end
    if not IsQBitSet(QBit(610)) then -- Built Castle to Level 2 (rescued dwarf guy)
        evt.SetTexture(1, "ch1b1")
        evt.SetTexture(3, "ch1b1")
        evt.SetTexture(14, "ch1b1el")
        evt.SetTexture(15, "ch1b1er")
        evt.SetTexture(16, "ch1b1")
        evt.SetTexture(17, "ch1b1")
        evt.SetTexture(19, "ch1b1")
        evt.SetTexture(20, "ch1b1")
        if IsQBitSet(QBit(611)) then -- Chose the path of Light
            if IsQBitSet(QBit(614)) then -- Completed Proving Grounds without killing a single creature
                evt.SetTexture(19, "wizh-a")
                evt.SetTexture(20, "wizh-b")
                evt.SetDoorState(36, DoorAction.Open)
                evt.SetFacetBit(3, FacetBits.Invisible, 0)
            end
            return
        elseif IsQBitSet(QBit(612)) then -- Chose the path of Dark
            if IsQBitSet(QBit(641)) then -- Completed Breeding Pit.
                evt.SetTexture(19, "nechuma")
                evt.SetTexture(20, "nechumb")
                evt.SetDoorState(36, DoorAction.Open)
                evt.SetFacetBit(3, FacetBits.Invisible, 0)
            end
            return
        else
            return
        end
        return
    end
    evt.SetDoorState(35, DoorAction.Open)
    evt.SetSprite(10, 0, "0")
    evt.SetTexture(4, "tfb09r1a")
    evt.SetTexture(5, "tfb09r1b")
    evt.SetTexture(6, "tfb09r1c")
    evt.SetTexture(7, "tfb09r1d")
    evt.SetTexture(8, "tfb09r1e")
    evt.SetTexture(9, "tfb09r1f")
    evt.SetTexture(10, "tfb09r1g")
    evt.SetTexture(11, "tfb09r1h")
    evt.SetTexture(12, "tfb09r1i")
    evt.SetTexture(13, "tfb09r1j")
    if IsQBitSet(QBit(611)) then -- Chose the path of Light
        if IsQBitSet(QBit(614)) then -- Completed Proving Grounds without killing a single creature
            evt.SetTexture(19, "wizh-a")
            evt.SetTexture(20, "wizh-b")
            evt.SetDoorState(36, DoorAction.Open)
            evt.SetFacetBit(3, FacetBits.Invisible, 0)
        end
        return
    elseif IsQBitSet(QBit(612)) then -- Chose the path of Dark
        if IsQBitSet(QBit(641)) then -- Completed Breeding Pit.
            evt.SetTexture(19, "nechuma")
            evt.SetTexture(20, "nechumb")
            evt.SetDoorState(36, DoorAction.Open)
            evt.SetFacetBit(3, FacetBits.Invisible, 0)
        end
        return
    else
        return
    end
end)

RegisterEvent(2, nil, function()
    if IsQBitSet(QBit(647)) then return end -- Player castle goblins are all dead
    if evt.CheckMonstersKilled(ActorKillCheck.Group, 56, 0, false) then -- actor group 56: spawn Bat A, spawn Goblin A, spawn Rat A; all matching actors defeated
        evt.ForPlayer(Players.All)
        SetQBit(QBit(647)) -- Player castle goblins are all dead
    end
end)

RegisterEvent(3, "Door", function()
    evt.SetDoorState(3, DoorAction.Open)
end, "Door")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(4, DoorAction.Open)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(5, DoorAction.Open)
end, "Door")

RegisterEvent(6, "Door", function()
    evt.SetDoorState(6, DoorAction.Open)
end, "Door")

RegisterEvent(7, "Door", function()
    evt.SetDoorState(7, DoorAction.Open)
end, "Door")

RegisterEvent(8, "Door", function()
    evt.SetDoorState(8, DoorAction.Open)
end, "Door")

RegisterEvent(9, "Door", function()
    evt.SetDoorState(9, DoorAction.Open)
end, "Door")

RegisterEvent(10, nil, function()
    evt.SetDoorState(10, DoorAction.Close)
end)

RegisterEvent(11, "Door", function()
    evt.SetDoorState(11, DoorAction.Open)
end, "Door")

RegisterEvent(12, "Door", function()
    evt.SetDoorState(12, DoorAction.Open)
end, "Door")

RegisterEvent(13, "Door", function()
    evt.SetDoorState(13, DoorAction.Open)
end, "Door")

RegisterEvent(14, "Door", function()
    evt.SetDoorState(14, DoorAction.Open)
end, "Door")

RegisterEvent(15, nil, function()
    if IsQBitSet(QBit(614)) or IsQBitSet(QBit(641)) then -- Completed Proving Grounds without killing a single creature
        evt.SetDoorState(15, DoorAction.Open)
    end
end)

RegisterEvent(16, nil, function()
    if IsQBitSet(QBit(614)) or IsQBitSet(QBit(641)) then -- Completed Proving Grounds without killing a single creature
        evt.SetDoorState(16, DoorAction.Open)
    end
end)

RegisterEvent(17, nil, function()
    evt.SetDoorState(17, DoorAction.Open)
end)

RegisterEvent(18, "Door", function()
    evt.SetDoorState(18, DoorAction.Open)
    evt.SetDoorState(19, DoorAction.Open)
end, "Door")

RegisterEvent(19, "Door", function()
    evt.SetDoorState(20, DoorAction.Open)
    evt.SetDoorState(21, DoorAction.Open)
end, "Door")

RegisterEvent(20, "Door", function()
    evt.SetDoorState(22, DoorAction.Open)
end, "Door")

RegisterEvent(21, "Door", function()
    evt.SetDoorState(23, DoorAction.Open)
end, "Door")

RegisterEvent(22, "Door", function()
    evt.SetDoorState(24, DoorAction.Open)
end, "Door")

RegisterEvent(23, "Door", function()
    evt.SetDoorState(25, DoorAction.Open)
end, "Door")

RegisterEvent(24, "Door", function()
    evt.SetDoorState(26, DoorAction.Open)
end, "Door")

RegisterEvent(25, "Door", function()
    evt.SetDoorState(27, DoorAction.Open)
end, "Door")

RegisterEvent(26, nil, function()
    evt.SetDoorState(28, DoorAction.Open)
end)

RegisterEvent(27, "Door", function()
    evt.SetDoorState(29, DoorAction.Open)
end, "Door")

RegisterEvent(28, "Door", function()
    evt.SetDoorState(30, DoorAction.Open)
end, "Door")

RegisterEvent(29, "Door", function()
    evt.SetDoorState(31, DoorAction.Open)
end, "Door")

RegisterEvent(30, "Door", function()
    evt.SetDoorState(32, DoorAction.Open)
end, "Door")

RegisterEvent(31, "Door", function()
    evt.SetDoorState(33, DoorAction.Open)
end, "Door")

RegisterEvent(32, "Bookcase", function()
    evt.SetDoorState(34, DoorAction.Open)
end, "Bookcase")

RegisterEvent(33, "Door", function()
    evt.SetDoorState(1, DoorAction.Open)
end, "Door")

RegisterEvent(34, "Door", function()
    evt.SetDoorState(2, DoorAction.Open)
end, "Door")

RegisterEvent(176, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(177, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(178, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(179, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(180, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(181, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(182, "Cabinet", function()
    evt.OpenChest(7)
end, "Cabinet")

RegisterEvent(183, "Cabinet", function()
    evt.OpenChest(8)
end, "Cabinet")

RegisterEvent(184, "Cabinet", function()
    evt.OpenChest(9)
end, "Cabinet")

RegisterEvent(185, "Cabinet", function()
    evt.OpenChest(10)
end, "Cabinet")

RegisterEvent(186, "Chest", function()
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(187, "Chest", function()
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(188, "Chest", function()
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(189, "Chest", function()
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(190, "Chest", function()
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(191, "Chest", function()
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(192, "Chest", function()
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(193, "Chest", function()
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(194, "Chest", function()
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(195, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(196, "Bookcase", function()
    if not IsQBitSet(QBit(657)) then return end -- Membership to the School of Sorcery Scroll Shop
    if IsAtLeast(MapVar(4), 3) then return end
    local randomStep = PickRandomOption(196, 4, {4, 4, 4, 6, 17, 18})
    if randomStep == 4 then
        evt.GiveItem(5, ItemType.Scroll_)
        local randomStep = PickRandomOption(196, 17, {17, 17, 17, 17, 18, 18})
        if randomStep == 17 then
            AddValue(MapVar(4), 1)
        end
    elseif randomStep == 6 then
        local randomStep = PickRandomOption(196, 7, {7, 9, 11, 13, 15, 16})
        if randomStep == 7 then
            AddValue(InventoryItem(1203), 1203) -- Fire Bolt
        elseif randomStep == 9 then
            AddValue(InventoryItem(1214), 1214) -- Feather Fall
        elseif randomStep == 11 then
            AddValue(InventoryItem(1216), 1216) -- Sparks
        elseif randomStep == 13 then
            AddValue(InventoryItem(1281), 1281) -- Dispel Magic
        elseif randomStep == 15 then
            AddValue(InventoryItem(1269), 1269) -- Heal
        end
        local randomStep = PickRandomOption(196, 17, {17, 17, 17, 17, 18, 18})
        if randomStep == 17 then
            AddValue(MapVar(4), 1)
        end
    elseif randomStep == 17 then
        AddValue(MapVar(4), 1)
    end
end, "Bookcase")

RegisterEvent(197, "Bookcase", function()
    if IsAtLeast(MapVar(3), 1) then return end
    AddValue(InventoryItem(1505), 1505) -- Basic Cryptography
    SetValue(MapVar(3), 1)
end, "Bookcase")

RegisterEvent(376, nil, function()
    evt.SetMonGroupBit(57, MonsterBits.Hostile, 0) -- actor group 57: Gold Golem
    evt.SetMonGroupBit(57, MonsterBits.Invisible, 1) -- actor group 57: Gold Golem
    if IsQBitSet(QBit(585)) then -- Finished constructing Golem with Abbey normal head
        evt.SetMonGroupBit(57, MonsterBits.Hostile, 1) -- actor group 57: Gold Golem
        ClearQBit(QBit(1686)) -- Replacement for NPCs ¹56 ver. 7
        evt.SetMonGroupBit(57, MonsterBits.Invisible, 0) -- actor group 57: Gold Golem
        return
    elseif IsQBitSet(QBit(586)) then -- Finished constructing Golem with normal head
        ClearQBit(QBit(1686)) -- Replacement for NPCs ¹56 ver. 7
        evt.SetMonGroupBit(57, MonsterBits.Invisible, 0) -- actor group 57: Gold Golem
        return
    else
        return
    end
end)

RegisterEvent(377, nil, function()
    evt.SetMonGroupBit(60, MonsterBits.Hostile, 0) -- actor group 60: Adventurer, Goblin, Goblin Lord, Guard, +1 more
    evt.SetMonGroupBit(60, MonsterBits.Invisible, 1) -- actor group 60: Adventurer, Goblin, Goblin Lord, Guard, +1 more
    if IsQBitSet(QBit(526)) then -- Accepted Fireball wand from Malwick
        if IsQBitSet(QBit(702)) then -- Finished with Malwick & Assc.
            return
        elseif IsQBitSet(QBit(696)) then -- Killed all castle monsters
            return
        elseif IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
            evt.SetMonGroupBit(60, MonsterBits.Hostile, 1) -- actor group 60: Adventurer, Goblin, Goblin Lord, Guard, +1 more
            evt.SetMonGroupBit(60, MonsterBits.Invisible, 0) -- actor group 60: Adventurer, Goblin, Goblin Lord, Guard, +1 more
            SetValue(BankGold, 0)
            ClearQBit(QBit(693)) -- Go to the Mercenary Guild in Tatalia and talk to Niles Stantley within two weeks. - Goto Merc Guild
            ClearQBit(QBit(694)) -- Steal the Tapestry from your associate's Castle and return it to Niles Stantley in the Mercenary Guild in Tatalia. - Do the Merc Guild Quest
            return
        elseif IsQBitSet(QBit(694)) then -- Steal the Tapestry from your associate's Castle and return it to Niles Stantley in the Mercenary Guild in Tatalia. - Do the Merc Guild Quest
            if IsAtLeast(Counter(5), 672) then
                evt.ForPlayer(Players.All)
                SetQBit(QBit(695)) -- Failed either goto or do guild quest
                evt.SetMonGroupBit(60, MonsterBits.Hostile, 1) -- actor group 60: Adventurer, Goblin, Goblin Lord, Guard, +1 more
                evt.SetMonGroupBit(60, MonsterBits.Invisible, 0) -- actor group 60: Adventurer, Goblin, Goblin Lord, Guard, +1 more
                SetValue(BankGold, 0)
                ClearQBit(QBit(693)) -- Go to the Mercenary Guild in Tatalia and talk to Niles Stantley within two weeks. - Goto Merc Guild
                ClearQBit(QBit(694)) -- Steal the Tapestry from your associate's Castle and return it to Niles Stantley in the Mercenary Guild in Tatalia. - Do the Merc Guild Quest
            end
            return
        elseif IsQBitSet(QBit(693)) then -- Go to the Mercenary Guild in Tatalia and talk to Niles Stantley within two weeks. - Goto Merc Guild
            if IsAtLeast(Counter(5), 336) then
                evt.ForPlayer(Players.All)
                SetQBit(QBit(695)) -- Failed either goto or do guild quest
                evt.SetMonGroupBit(60, MonsterBits.Hostile, 1) -- actor group 60: Adventurer, Goblin, Goblin Lord, Guard, +1 more
                evt.SetMonGroupBit(60, MonsterBits.Invisible, 0) -- actor group 60: Adventurer, Goblin, Goblin Lord, Guard, +1 more
                SetValue(BankGold, 0)
                ClearQBit(QBit(693)) -- Go to the Mercenary Guild in Tatalia and talk to Niles Stantley within two weeks. - Goto Merc Guild
                ClearQBit(QBit(694)) -- Steal the Tapestry from your associate's Castle and return it to Niles Stantley in the Mercenary Guild in Tatalia. - Do the Merc Guild Quest
            end
            return
        else
            return
        end
        return
    end
    SetValue(BankGold, 0)
    ClearQBit(QBit(693)) -- Go to the Mercenary Guild in Tatalia and talk to Niles Stantley within two weeks. - Goto Merc Guild
    ClearQBit(QBit(694)) -- Steal the Tapestry from your associate's Castle and return it to Niles Stantley in the Mercenary Guild in Tatalia. - Do the Merc Guild Quest
end)

RegisterEvent(378, nil, function()
    if not IsQBitSet(QBit(695)) then return end -- Failed either goto or do guild quest
    if IsQBitSet(QBit(696)) then return end -- Killed all castle monsters
    if not evt.CheckMonstersKilled(ActorKillCheck.Group, 60, 0, false) then return end -- actor group 60: Adventurer, Goblin, Goblin Lord, Guard, +1 more; all matching actors defeated
    evt.ForPlayer(Players.All)
    SetQBit(QBit(696)) -- Killed all castle monsters
    if IsQBitSet(QBit(697)) then -- Killed all outdoor monsters
        evt.ForPlayer(Players.All)
        SetQBit(QBit(702)) -- Finished with Malwick & Assc.
        ClearQBit(QBit(695)) -- Failed either goto or do guild quest
    end
end)

RegisterEvent(416, "Sanctuary", function()
    if not IsQBitSet(QBit(610)) then -- Built Castle to Level 2 (rescued dwarf guy)
        evt.EnterHouse(380)
        return
    end
    if IsQBitSet(QBit(614)) then -- Completed Proving Grounds without killing a single creature
        evt.EnterHouse(322) -- Sanctuary
    elseif IsQBitSet(QBit(641)) then -- Completed Breeding Pit.
        evt.EnterHouse(322) -- Sanctuary
    else
        evt.EnterHouse(381)
        return
    end
end, "Sanctuary")

RegisterEvent(417, "Beakers and Bottles", function()
    if not IsQBitSet(QBit(610)) then -- Built Castle to Level 2 (rescued dwarf guy)
        evt.EnterHouse(380)
        return
    end
    if IsQBitSet(QBit(614)) then -- Completed Proving Grounds without killing a single creature
        evt.EnterHouse(125) -- Beakers and Bottles
    elseif IsQBitSet(QBit(641)) then -- Completed Breeding Pit.
        evt.EnterHouse(125) -- Beakers and Bottles
    else
        evt.EnterHouse(381)
        return
    end
end, "Beakers and Bottles")

RegisterEvent(418, "Thel's Armor and Shields", function()
    if not IsQBitSet(QBit(610)) then -- Built Castle to Level 2 (rescued dwarf guy)
        evt.EnterHouse(380)
        return
    end
    if IsQBitSet(QBit(614)) then -- Completed Proving Grounds without killing a single creature
        evt.EnterHouse(58) -- Thel's Armor and Shields
    elseif IsQBitSet(QBit(641)) then -- Completed Breeding Pit.
        evt.EnterHouse(58) -- Thel's Armor and Shields
    else
        evt.EnterHouse(381)
        return
    end
end, "Thel's Armor and Shields")

RegisterEvent(419, "Swords Inc.", function()
    if not IsQBitSet(QBit(610)) then -- Built Castle to Level 2 (rescued dwarf guy)
        evt.EnterHouse(380)
        return
    end
    if IsQBitSet(QBit(614)) then -- Completed Proving Grounds without killing a single creature
        evt.EnterHouse(18) -- Swords Inc.
    elseif IsQBitSet(QBit(641)) then -- Completed Breeding Pit.
        evt.EnterHouse(18) -- Swords Inc.
    else
        evt.EnterHouse(381)
        return
    end
end, "Swords Inc.")

RegisterEvent(420, "Throne Room", function()
    if not IsQBitSet(QBit(610)) then -- Built Castle to Level 2 (rescued dwarf guy)
        evt.StatusText("The door is blocked")
        return
    end
    evt.EnterHouse(1169) -- Throne Room
end, "Throne Room")

RegisterEvent(451, nil, function()
    SetValue(MapVar(5), 10)
    SetValue(MapVar(6), 10)
    if IsQBitSet(QBit(596)) then -- Gave artifact to humans
        goto step_8
    end
    if IsQBitSet(QBit(597)) then -- Gave artifact to elves
        goto step_10
    end
    if not IsQBitSet(QBit(659)) then -- Gave artifact to arbiter
        SetValue(MapVar(6), 13)
    end
    ::step_8::
    SubtractValue(MapVar(5), 1)
    goto step_11
    ::step_10::
    AddValue(MapVar(5), 1)
    ::step_11::
    if IsQBitSet(QBit(592)) then -- Gave plans to elfking
        goto step_14
    end
    if IsQBitSet(QBit(594)) then -- Gave false plans to elfking (betray)
        goto step_16
    end
    goto step_18
    ::step_14::
    AddValue(MapVar(5), 1)
    goto step_17
    ::step_16::
    SubtractValue(MapVar(5), 1)
    ::step_17::
    SubtractValue(MapVar(6), 1)
    ::step_18::
    if IsQBitSet(QBit(593)) then -- Gave Loren to Catherine
        goto step_21
    end
    if IsQBitSet(QBit(595)) then -- Gave false Loren to Catherine (betray)
        goto step_23
    end
    goto step_25
    ::step_21::
    SubtractValue(MapVar(5), 1)
    goto step_24
    ::step_23::
    AddValue(MapVar(5), 1)
    ::step_24::
    SubtractValue(MapVar(6), 1)
    ::step_25::
    if IsAtLeast(MapVar(6), 12) then
        goto step_37
    end
    if IsAtLeast(MapVar(5), 11) then
        evt.SetTexture(16, "elfhuma")
        evt.SetTexture(17, "elfhumb")
        return
    end
    if not IsAtLeast(MapVar(5), 10) then
        evt.SetTexture(16, "chb1p6")
        evt.SetTexture(17, "chb1p7")
        return
    end
    if IsAtLeast(MapVar(6), 11) then
        goto step_37
    end
    evt.SetTexture(16, "bannwc-a")
    evt.SetTexture(17, "bannwc-b")
    ::step_37::
    do return end
end)

RegisterEvent(501, "Leave Castle Harmondale", function()
    evt.MoveToMap(-18325, 12564, 480, 0, 0, 0, 0, 8, "7out02.odm") -- Harmondale
end, "Leave Castle Harmondale")

