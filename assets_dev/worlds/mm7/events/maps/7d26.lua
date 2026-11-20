-- The Pit
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
    [376] = { kind = "enter_house", source = "opcode", houseId = 1070, targetName = "Hostel" },
    [415] = { kind = "obelisk", source = "title" },
    [417] = { kind = "enter_house", source = "opcode", houseId = 53, targetName = "Shields of Malice" },
    [419] = { kind = "enter_house", source = "opcode", houseId = 13, targetName = "Blades of Spite" },
    [421] = { kind = "enter_house", source = "opcode", houseId = 290, targetName = "Frozen Assets" },
    [423] = { kind = "enter_house", source = "opcode", houseId = 91, targetName = "Eldritch Influences" },
    [425] = { kind = "enter_house", source = "opcode", houseId = 149, targetName = "Paramount Guild of Earth" },
    [427] = { kind = "enter_house", source = "opcode", houseId = 178, targetName = "Guild of Night" },
    [429] = { kind = "enter_house", source = "opcode", houseId = 123, targetName = "Infernal Temptations" },
    [431] = { kind = "enter_house", source = "opcode", houseId = 207, targetName = "Hall of Midnight" },
    [433] = { kind = "enter_house", source = "opcode", houseId = 1575, targetName = "Perdition's Flame" },
    [435] = { kind = "enter_house", source = "opcode", houseId = 246, targetName = "The Vampyre Lounge" },
    [438] = { kind = "enter_house", source = "opcode", houseId = 1080, targetName = "Hostel" },
    [439] = { kind = "enter_house", source = "opcode", houseId = 1078, targetName = "Hostel" },
    [440] = { kind = "enter_house", source = "opcode", houseId = 1071, targetName = "Hostel" },
    [441] = { kind = "enter_house", source = "opcode", houseId = 1079, targetName = "Hostel" },
    [442] = { kind = "enter_house", source = "opcode", houseId = 1072, targetName = "House Umberpool" },
    [443] = { kind = "enter_house", source = "opcode", houseId = 1074, targetName = "Sand Residence" },
    [444] = { kind = "enter_house", source = "opcode", houseId = 1073, targetName = "Darkenmore Residence" },
    [445] = { kind = "enter_house", source = "opcode", houseId = 1075, targetName = "Hostel" },
    [446] = { kind = "enter_house", source = "opcode", houseId = 1081, targetName = "Hostel" },
    [447] = { kind = "enter_house", source = "opcode", houseId = 1076, targetName = "Hostel" },
    [448] = { kind = "enter_house", source = "opcode", houseId = 1077 },
    [452] = { kind = "teleport", source = "heuristic" },
    [453] = { kind = "teleport", source = "heuristic" },
    [454] = { kind = "teleport", source = "heuristic" },
    [455] = { kind = "teleport", source = "heuristic" },
    [456] = { kind = "teleport", source = "heuristic" },
    [457] = { kind = "teleport", source = "heuristic" },
    [501] = { kind = "passage", source = "opcode", targetMap = "t04.blv", targetName = "The Hall of the Pit" },
    [502] = { kind = "enter_house", source = "opcode", houseId = 317, targetName = "Temple of Dark" },
    [503] = { kind = "passage", source = "opcode", targetMap = "7d10.blv", targetName = "The Breeding Zone" },
    [504] = { kind = "passage", source = "opcode", targetMap = "d03.blv", targetName = "Castle Gloaming" },
    [505] = { kind = "passage", source = "opcode", targetMap = "d03.blv", targetName = "Castle Gloaming" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, nil, function()
    if not IsQBitSet(QBit(723)) then -- TP Buff The Pit
        SetQBit(QBit(723)) -- TP Buff The Pit
    end
    if IsQBitSet(QBit(612)) then -- Chose the path of Dark
        if IsQBitSet(QBit(782)) then -- Your friends are mad at you
            if IsAtLeast(Counter(10), 720) then
                ClearQBit(QBit(782)) -- Your friends are mad at you
                SetValue(MapVar(6), 0)
                evt.SetMonGroupBit(56, MonsterBits.Hostile, 0) -- actor group 56: peasant, spawn Lich A, spawn Necromancer A, spawn Vampire A
                evt.SetMonGroupBit(55, MonsterBits.Hostile, 0)
                return
            end
            SetValue(MapVar(6), 2)
            evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: peasant, spawn Lich A, spawn Necromancer A, spawn Vampire A
            evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
            return
        elseif IsAtLeast(MapVar(6), 2) then
            evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: peasant, spawn Lich A, spawn Necromancer A, spawn Vampire A
            evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
            return
        else
            return
        end
        return
    end
    SetValue(MapVar(6), 2)
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: peasant, spawn Lich A, spawn Necromancer A, spawn Vampire A
    evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
end)

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

RegisterEvent(182, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(183, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(184, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(185, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

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

RegisterEvent(376, "Hostel", function()
    if IsQBitSet(QBit(621)) then -- Assassinate Tolberti in his house in the Pit and return his control cube to Robert the Wise in Celeste.
        evt.MoveToMap(-15360, 3808, 129, 270, 0, 0, 0, 0, "mdt15.blv") -- The Small House
    elseif IsQBitSet(QBit(622)) then -- Finished Necro Proving Grounds
        if IsQBitSet(QBit(623)) then -- Finished Necro Task 2 - Temple of Light
            if IsQBitSet(QBit(624)) then -- Finished Necro Task 3 - Soul Jars
                if IsQBitSet(QBit(625)) then -- Finished Necro Task 4 - Clanker's Lab
                    if IsQBitSet(QBit(630)) then -- Killed Good MM3 Person
                        evt.EnterHouse(1070) -- Hostel
                        return
                    elseif IsQBitSet(QBit(710)) then -- Archibald in Clankers Lab now
                        evt.EnterHouse(1070) -- Hostel
                        return
                    else
                        evt.SetNPCGreeting(426, 248) -- Tolberti greeting: Now that you've finished my associate's tasks, I am ready to give you a much more dangerous, but very critical mission. Our plans hinge on your success. I know I can count on you.Oh, I almost forgot to mention! Archibald is no longer in charge. He left in a huff after we disagreed with how we should proceed with our plans. He's moved into Clanker's laboratory now, and taken some of the less...motivated necromancers with him. No loss there. Kastore is King of the Pit, now.
                        SetQBit(QBit(710)) -- Archibald in Clankers Lab now
                        evt.SetNPCGreeting(427, 250) -- Archibald Ironfist greeting: Hello, my friends…you are still my friends, aren't you? My "advisors", my "lieutenants" [Archibald spits out the words], have the Pit, and their dreams of conquest. I have come to realize they did not need me, nor did they want to study our art. They want a world where there are no Kings, no loyalty, and no honor. Just them and their slaves. Well, they can have it! After the soul jars were stolen, my lieutenants just shrugged, as though it was wagon wheels, or chickens that went missing, not the keys to immortality! We were so close to devising a way to keep the body from decay after the Ritual was performed! Now this--a setback that will cost decades.So, we have moved here--thanks to you--to continue our studies. For what it's worth, I have renounced my claim to the throne of Enroth. I don't think anyone believes me, but that shouldn't matter. This island is quite secure, and we have fixed the breech that let you infiltrate it in the first place.
                        evt.MoveNPC(427, 0) -- Archibald Ironfist -> removed
                        evt.MoveNPC(423, 221) -- Kastore -> Throne Room
                        evt.SetNPCTopic(423, 4, 1012) -- Kastore topic 4: Dark Magic Grandmaster
                        evt.SetNPCTopic(427, 1, 0) -- Archibald Ironfist topic 1 cleared
                        evt.EnterHouse(1070) -- Hostel
                        return
                    end
                    return
                end
            end
        end
        evt.EnterHouse(1070) -- Hostel
        return
    else
        evt.EnterHouse(1070) -- Hostel
        return
    end
end, "Hostel")

RegisterEvent(415, "Obelisk", function()
    if IsQBitSet(QBit(682)) then return end -- Visited Obelisk in Area 8
    evt.StatusText("srhtfnut")
    SetAutonote(315) -- Obelisk message #7: srhtfnut
    evt.ForPlayer(Players.All)
    SetQBit(QBit(682)) -- Visited Obelisk in Area 8
end, "Obelisk")

RegisterEvent(416, "House", nil, "House")

RegisterEvent(417, "Shields of Malice", function()
    evt.EnterHouse(53) -- Shields of Malice
end, "Shields of Malice")

RegisterEvent(418, "Shields of Malice", nil, "Shields of Malice")

RegisterEvent(419, "Blades of Spite", function()
    evt.EnterHouse(13) -- Blades of Spite
end, "Blades of Spite")

RegisterEvent(420, "Blades of Spite", nil, "Blades of Spite")

RegisterEvent(421, "Frozen Assets", function()
    evt.EnterHouse(290) -- Frozen Assets
end, "Frozen Assets")

RegisterEvent(422, "Frozen Assets", nil, "Frozen Assets")

RegisterEvent(423, "Eldritch Influences", function()
    evt.EnterHouse(91) -- Eldritch Influences
end, "Eldritch Influences")

RegisterEvent(424, "Eldritch Influences", nil, "Eldritch Influences")

RegisterEvent(425, "Paramount Guild of Earth", function()
    evt.EnterHouse(149) -- Paramount Guild of Earth
end, "Paramount Guild of Earth")

RegisterEvent(426, "Paramount Guild of Earth", nil, "Paramount Guild of Earth")

RegisterEvent(427, "Guild of Night", function()
    evt.EnterHouse(178) -- Guild of Night
end, "Guild of Night")

RegisterEvent(428, "Guild of Night", nil, "Guild of Night")

RegisterEvent(429, "Infernal Temptations", function()
    evt.EnterHouse(123) -- Infernal Temptations
end, "Infernal Temptations")

RegisterEvent(430, "Infernal Temptations", nil, "Infernal Temptations")

RegisterEvent(431, "Hall of Midnight", function()
    evt.EnterHouse(207) -- Hall of Midnight
end, "Hall of Midnight")

RegisterEvent(432, "Hall of Midnight", nil, "Hall of Midnight")

RegisterEvent(433, "Perdition's Flame", function()
    evt.EnterHouse(1575) -- Perdition's Flame
end, "Perdition's Flame")

RegisterEvent(434, "Perdition's Flame", nil, "Perdition's Flame")

RegisterEvent(435, "The Vampyre Lounge", function()
    evt.EnterHouse(246) -- The Vampyre Lounge
end, "The Vampyre Lounge")

RegisterEvent(436, "The Vampyre Lounge", nil, "The Vampyre Lounge")

RegisterEvent(438, "Hostel", function()
    evt.EnterHouse(1080) -- Hostel
end, "Hostel")

RegisterEvent(439, "Hostel", function()
    evt.EnterHouse(1078) -- Hostel
end, "Hostel")

RegisterEvent(440, "Hostel", function()
    evt.EnterHouse(1071) -- Hostel
end, "Hostel")

RegisterEvent(441, "Hostel", function()
    if not IsQBitSet(QBit(710)) then -- Archibald in Clankers Lab now
        evt.EnterHouse(1079) -- Hostel
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Hostel")

RegisterEvent(442, "House Umberpool", function()
    evt.EnterHouse(1072) -- House Umberpool
end, "House Umberpool")

RegisterEvent(443, "Sand Residence", function()
    evt.EnterHouse(1074) -- Sand Residence
end, "Sand Residence")

RegisterEvent(444, "Darkenmore Residence", function()
    evt.EnterHouse(1073) -- Darkenmore Residence
end, "Darkenmore Residence")

RegisterEvent(445, "Hostel", function()
    evt.EnterHouse(1075) -- Hostel
end, "Hostel")

RegisterEvent(446, "Hostel", function()
    evt.EnterHouse(1081) -- Hostel
end, "Hostel")

RegisterEvent(447, "Hostel", function()
    evt.EnterHouse(1076) -- Hostel
end, "Hostel")

RegisterEvent(448, nil, function()
    evt.EnterHouse(1077)
end)

RegisterEvent(452, nil, function()
    evt.MoveToMap(-1873, -8516, 64, 1536, 0, 0, 0, 0)
end)

RegisterEvent(453, nil, function()
    evt.MoveToMap(-1824, -7136, 33, 512, 0, 0, 0, 0)
end)

RegisterEvent(454, nil, function()
    evt.MoveToMap(-26354, -10440, 689, 1664, 0, 0, 0, 0)
end)

RegisterEvent(455, nil, function()
    evt.MoveToMap(-2854, -23128, 625, 541, 0, 0, 0, 0)
end)

RegisterEvent(456, nil, function()
    evt.MoveToMap(6196, -10401, -362, 832, 0, 0, 0, 0)
end)

RegisterEvent(457, nil, function()
    evt.MoveToMap(9683, -5602, -19, 1600, 0, 0, 0, 0)
end)

RegisterEvent(501, "Leave the Pit", function()
    evt.MoveToMap(498, 16198, 161, 1536, 0, 0, 0, 0, "t04.blv") -- The Hall of the Pit
end, "Leave the Pit")

RegisterEvent(502, "Temple of Dark", function()
    evt.EnterHouse(317) -- Temple of Dark
end, "Temple of Dark")

RegisterEvent(503, "Enter the Breeding Zone", function()
    evt.MoveToMap(-320, -1216, 1, 0, 0, 0, 146, 1, "7d10.blv") -- The Breeding Zone
end, "Enter the Breeding Zone")

RegisterEvent(504, "Enter Castle Gloaming", function()
    evt.MoveToMap(96, 3424, 1, 1088, 0, 0, 129, 1, "d03.blv") -- Castle Gloaming
end, "Enter Castle Gloaming")

RegisterEvent(505, "Enter Castle Gloaming", function()
    evt.MoveToMap(874, -261, -377, 1024, 0, 0, 129, 1, "d03.blv") -- Castle Gloaming
end, "Enter Castle Gloaming")

