-- Celeste
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 377},
    onLeave = {378},
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
    [3] = { kind = "open_door", source = "opcode" },
    [4] = { kind = "open_door", source = "opcode" },
    [5] = { kind = "open_door", source = "opcode" },
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
    [376] = { kind = "enter_house", source = "opcode", houseId = 1065, targetName = "Hostel" },
    [415] = { kind = "obelisk", source = "title" },
    [417] = { kind = "enter_house", source = "opcode", houseId = 1059, targetName = "House Devine" },
    [418] = { kind = "enter_house", source = "opcode", houseId = 1060, targetName = "Morningstar Residence" },
    [419] = { kind = "enter_house", source = "opcode", houseId = 1061, targetName = "House Winterbright" },
    [420] = { kind = "enter_house", source = "opcode", houseId = 1062, targetName = "Hostel" },
    [421] = { kind = "enter_house", source = "opcode", houseId = 1063, targetName = "Hostel" },
    [422] = { kind = "enter_house", source = "opcode", houseId = 1064, targetName = "Hostel" },
    [423] = { kind = "enter_house", source = "opcode", houseId = 1067, targetName = "Ramiez Residence" },
    [424] = { kind = "enter_house", source = "opcode", houseId = 1066, targetName = "Tarent Residence" },
    [426] = { kind = "enter_house", source = "opcode", houseId = 1068, targetName = "Hostel" },
    [427] = { kind = "enter_house", source = "opcode", houseId = 1069, targetName = "Hostel" },
    [429] = { kind = "enter_house", source = "opcode", houseId = 12, targetName = "The Hallowed Sword" },
    [431] = { kind = "enter_house", source = "opcode", houseId = 52, targetName = "Armor of Honor" },
    [433] = { kind = "enter_house", source = "opcode", houseId = 1574, targetName = "Trial of Honor" },
    [435] = { kind = "enter_house", source = "opcode", houseId = 245, targetName = "The Blessed Brew" },
    [437] = { kind = "enter_house", source = "opcode", houseId = 289, targetName = "Material Wealth" },
    [439] = { kind = "enter_house", source = "opcode", houseId = 122, targetName = "Phials of Faith" },
    [441] = { kind = "enter_house", source = "opcode", houseId = 137, targetName = "Paramount Guild of Air" },
    [443] = { kind = "enter_house", source = "opcode", houseId = 172, targetName = "Guild of Enlightenment" },
    [445] = { kind = "enter_house", source = "opcode", houseId = 90, targetName = "Esoteric Indulgences" },
    [447] = { kind = "enter_house", source = "opcode", houseId = 206, targetName = "Hall of Dawn" },
    [451] = { kind = "teleport", source = "heuristic" },
    [452] = { kind = "generic_event", source = "opcode" },
    [501] = { kind = "leave_dungeon", source = "opcode", targetMap = "7out06.odm", targetName = "The Bracada Desert" },
    [502] = { kind = "passage", source = "opcode", targetMap = "7d11.blv", targetName = "The Walls of Mist" },
    [503] = { kind = "passage", source = "opcode", targetMap = "7d30.blv", targetName = "Castle Lambent" },
    [504] = { kind = "enter_house", source = "opcode", houseId = 316, targetName = "Temple of Light" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 65535, sourceEventId = 452, triggerStep = 11, origin = "legacy", triggerKind = "long", scheduleKind = "daily", startHour = 1, startMinute = 0, startSecond = 0 },
    },
})

RegisterEvent(1, nil, function()
    SetQBit(QBit(722)) -- TP Buff Celeste
    if IsQBitSet(QBit(611)) then -- Chose the path of Light
        if IsQBitSet(QBit(782)) then -- Your friends are mad at you
            if IsAtLeast(Counter(10), 720) then
                ClearQBit(QBit(782)) -- Your friends are mad at you
                SetValue(MapVar(6), 0)
                evt.SetMonGroupBit(56, MonsterBits.Hostile, 0)
                evt.SetMonGroupBit(55, MonsterBits.Hostile, 0) -- actor group 55: Angel Lord, Wizard
                return
            end
            SetValue(MapVar(6), 2)
            evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
            evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Angel Lord, Wizard
            return
        elseif IsAtLeast(MapVar(6), 2) then
            evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
            evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Angel Lord, Wizard
            return
        else
            return
        end
        return
    end
    SetValue(MapVar(6), 2)
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
    evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Angel Lord, Wizard
end)

RegisterEvent(3, nil, function()
    evt.SetDoorState(5, DoorAction.Trigger)
end)

RegisterEvent(4, nil, function()
    evt.SetDoorState(1, DoorAction.Trigger)
    evt.SetDoorState(2, DoorAction.Trigger)
end)

RegisterEvent(5, nil, function()
    evt.SetDoorState(3, DoorAction.Trigger)
    evt.SetDoorState(4, DoorAction.Trigger)
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
    if IsQBitSet(QBit(639)) then -- Assassinate Robert the Wise in his house in Celeste and return to Tolberti in the Pit.
        evt.MoveToMap(0, 3808, 129, 270, 0, 0, 0, 9, "mdt15.blv") -- The Small House
    elseif IsQBitSet(QBit(626)) then -- Finished Wizard Proving Grounds
        if IsQBitSet(QBit(627)) then -- Finished Wizard Task 2 - Temple of Dark
            if IsQBitSet(QBit(628)) then -- Finished Wizard Task 3 - Wine Cellar
                if IsQBitSet(QBit(629)) then -- Finished Wizard Task 4 - Soul Jars
                    if IsQBitSet(QBit(631)) then -- Killed Evil MM3 Person
                        evt.MoveNPC(419, 220) -- Resurectra -> Throne Room
                        evt.EnterHouse(1065) -- Hostel
                        return
                    elseif IsQBitSet(QBit(710)) then -- Archibald in Clankers Lab now
                        evt.EnterHouse(1065) -- Hostel
                        return
                    else
                        evt.SetNPCGreeting(422, 236) -- Robert the Wise greeting: You've finished their missions. Good. Our conflict with the Necromancers is rapidly coming to a conclusion. I have a dangerous, but critical mission for you. The future of your…er, our world depends on your success.
                        SetQBit(QBit(710)) -- Archibald in Clankers Lab now
                        evt.EnterHouse(1065) -- Hostel
                        return
                    end
                    return
                end
            end
        end
        evt.EnterHouse(1065) -- Hostel
        return
    else
        evt.EnterHouse(1065) -- Hostel
        return
    end
end, "Hostel")

RegisterEvent(377, nil, function()
    if IsQBitSet(QBit(533)) then -- Go to the Celestial Court in Celeste and kill Lady Eleanor Carmine. Return with proof to Seknit Undershadow in the Deyja Moors.
        evt.SetMonGroupBit(52, MonsterBits.Invisible, 0)
        evt.SetMonGroupBit(52, MonsterBits.Hostile, 1)
        SetValue(MapVar(2), 1)
    end
end)

RegisterEvent(378, nil, function()
    if not IsAtLeast(MapVar(2), 1) then return end
    if evt.CheckMonstersKilled(ActorKillCheck.Group, 52, 0, true) then -- actor group 52; all matching actors defeated
        SetQBit(QBit(725)) -- Dagger - I lost it
    end
end)

RegisterEvent(415, "Obelisk", function()
    if IsQBitSet(QBit(681)) then return end -- Visited Obelisk in Area 7
    evt.StatusText("eut__i_n")
    SetAutonote(314) -- Obelisk message #6: eut__i_n
    SetQBit(QBit(681)) -- Visited Obelisk in Area 7
end, "Obelisk")

RegisterEvent(416, "House", nil, "House")

RegisterEvent(417, "House Devine", function()
    evt.EnterHouse(1059) -- House Devine
end, "House Devine")

RegisterEvent(418, "Morningstar Residence", function()
    evt.EnterHouse(1060) -- Morningstar Residence
end, "Morningstar Residence")

RegisterEvent(419, "House Winterbright", function()
    evt.EnterHouse(1061) -- House Winterbright
end, "House Winterbright")

RegisterEvent(420, "Hostel", function()
    if not IsQBitSet(QBit(631)) then -- Killed Evil MM3 Person
        evt.EnterHouse(1062) -- Hostel
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Hostel")

RegisterEvent(421, "Hostel", function()
    evt.EnterHouse(1063) -- Hostel
end, "Hostel")

RegisterEvent(422, "Hostel", function()
    evt.EnterHouse(1064) -- Hostel
end, "Hostel")

RegisterEvent(423, "Ramiez Residence", function()
    evt.EnterHouse(1067) -- Ramiez Residence
end, "Ramiez Residence")

RegisterEvent(424, "Tarent Residence", function()
    evt.EnterHouse(1066) -- Tarent Residence
end, "Tarent Residence")

RegisterEvent(426, "Hostel", function()
    evt.EnterHouse(1068) -- Hostel
end, "Hostel")

RegisterEvent(427, "Hostel", function()
    evt.EnterHouse(1069) -- Hostel
end, "Hostel")

RegisterEvent(428, "The Hallowed Sword", nil, "The Hallowed Sword")

RegisterEvent(429, "The Hallowed Sword", function()
    evt.EnterHouse(12) -- The Hallowed Sword
end, "The Hallowed Sword")

RegisterEvent(430, "Armor of Honor", nil, "Armor of Honor")

RegisterEvent(431, "Armor of Honor", function()
    evt.EnterHouse(52) -- Armor of Honor
end, "Armor of Honor")

RegisterEvent(432, "Trial of Honor", nil, "Trial of Honor")

RegisterEvent(433, "Trial of Honor", function()
    evt.EnterHouse(1574) -- Trial of Honor
end, "Trial of Honor")

RegisterEvent(434, "The Blessed Brew", nil, "The Blessed Brew")

RegisterEvent(435, "The Blessed Brew", function()
    evt.EnterHouse(245) -- The Blessed Brew
end, "The Blessed Brew")

RegisterEvent(436, "Material Wealth", nil, "Material Wealth")

RegisterEvent(437, "Material Wealth", function()
    evt.EnterHouse(289) -- Material Wealth
end, "Material Wealth")

RegisterEvent(438, "Phials of Faith", nil, "Phials of Faith")

RegisterEvent(439, "Phials of Faith", function()
    evt.EnterHouse(122) -- Phials of Faith
end, "Phials of Faith")

RegisterEvent(440, "Paramount Guild of Air", nil, "Paramount Guild of Air")

RegisterEvent(441, "Paramount Guild of Air", function()
    evt.EnterHouse(137) -- Paramount Guild of Air
end, "Paramount Guild of Air")

RegisterEvent(442, "Guild of Enlightenment", nil, "Guild of Enlightenment")

RegisterEvent(443, "Guild of Enlightenment", function()
    evt.EnterHouse(172) -- Guild of Enlightenment
end, "Guild of Enlightenment")

RegisterEvent(444, "Esoteric Indulgences", nil, "Esoteric Indulgences")

RegisterEvent(445, "Esoteric Indulgences", function()
    evt.EnterHouse(90) -- Esoteric Indulgences
end, "Esoteric Indulgences")

RegisterEvent(446, "Hall of Dawn", nil, "Hall of Dawn")

RegisterEvent(447, "Hall of Dawn", function()
    evt.EnterHouse(206) -- Hall of Dawn
end, "Hall of Dawn")

RegisterEvent(451, nil, function()
    local randomStep = PickRandomOption(451, 1, {1, 2, 3, 4, 5, 6})
    if randomStep == 1 then
        evt.MoveToMap(8146, 4379, 3700, 0, 0, 0, 0, 0)
        evt.MoveToMap(-2815, 1288, 3700, 0, 0, 0, 0, 0, "7out06.odm") -- The Bracada Desert
        evt.MoveToMap(-11883, 8667, 3700, 0, 0, 0, 0, 0, "7out06.odm") -- The Bracada Desert
        evt.MoveToMap(-22231, 13145, 3700, 0, 0, 0, 0, 0, "7out06.odm") -- The Bracada Desert
        evt.MoveToMap(-12770, 18344, 3700, 0, 0, 0, 0, 0, "7out06.odm") -- The Bracada Desert
    elseif randomStep == 2 then
        evt.MoveToMap(-2815, 1288, 3700, 0, 0, 0, 0, 0, "7out06.odm") -- The Bracada Desert
        evt.MoveToMap(-11883, 8667, 3700, 0, 0, 0, 0, 0, "7out06.odm") -- The Bracada Desert
        evt.MoveToMap(-22231, 13145, 3700, 0, 0, 0, 0, 0, "7out06.odm") -- The Bracada Desert
        evt.MoveToMap(-12770, 18344, 3700, 0, 0, 0, 0, 0, "7out06.odm") -- The Bracada Desert
    elseif randomStep == 3 then
        evt.MoveToMap(-11883, 8667, 3700, 0, 0, 0, 0, 0, "7out06.odm") -- The Bracada Desert
        evt.MoveToMap(-22231, 13145, 3700, 0, 0, 0, 0, 0, "7out06.odm") -- The Bracada Desert
        evt.MoveToMap(-12770, 18344, 3700, 0, 0, 0, 0, 0, "7out06.odm") -- The Bracada Desert
    elseif randomStep == 4 then
        evt.MoveToMap(-22231, 13145, 3700, 0, 0, 0, 0, 0, "7out06.odm") -- The Bracada Desert
        evt.MoveToMap(-12770, 18344, 3700, 0, 0, 0, 0, 0, "7out06.odm") -- The Bracada Desert
    elseif randomStep == 5 then
        evt.MoveToMap(-12770, 18344, 3700, 0, 0, 0, 0, 0, "7out06.odm") -- The Bracada Desert
    end
    evt.MoveToMap(9185, 18564, 3700, 0, 0, 0, 0, 0, "7out06.odm") -- The Bracada Desert
end)

RegisterEvent(452, "Take a Drink", function()
    if IsPlayerBitSet(PlayerBit(30)) then return end
    AddValue(MightBonus, 25)
    AddValue(IntellectBonus, 25)
    AddValue(PersonalityBonus, 25)
    AddValue(EnduranceBonus, 25)
    AddValue(AccuracyBonus, 25)
    AddValue(SpeedBonus, 25)
    AddValue(LuckBonus, 25)
    evt.StatusText("+25 to all Stats(Temporary)")
    SetPlayerBit(PlayerBit(30))
end, "Take a Drink")

RegisterEvent(501, "Leave Celeste", function()
    evt.MoveToMap(-9718, 10097, 2449, 1536, 0, 0, 0, 8, "7out06.odm") -- The Bracada Desert
end, "Leave Celeste")

RegisterEvent(502, "Enter the Walls of Mist", function()
    evt.MoveToMap(-896, -4717, 161, 512, 0, 0, 400, 9, "7d11.blv") -- The Walls of Mist
end, "Enter the Walls of Mist")

RegisterEvent(503, "Enter Castle Lambent", function()
    evt.MoveToMap(64, -640, 1, 512, 0, 0, 386, 9, "7d30.blv") -- Castle Lambent
end, "Enter Castle Lambent")

RegisterEvent(504, "Temple of Light", function()
    evt.EnterHouse(316) -- Temple of Light
end, "Temple of Light")

RegisterEvent(65535, "", function()
    evt.ForPlayer(Players.All)
    ClearPlayerBit(PlayerBit(30))
end)

