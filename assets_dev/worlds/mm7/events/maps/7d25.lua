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
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    SetQBit(QBit(182)) -- Twiling Town Portal
    if IsQBitSet(QBit(611)) then -- Chose the path of Light
        if IsQBitSet(QBit(782)) then -- Your friends are mad at you
            if IsAtLeast(Counter(10), 720) then
                ClearQBit(QBit(782)) -- Your friends are mad at you
                SetValue(MapVar(6), 0)
                evt.SetMonGroupBit(56, MonsterBits.Hostile, 0)
                evt.SetMonGroupBit(55, MonsterBits.Hostile, 0)
            end
            SetValue(MapVar(6), 2)
            evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
            evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
            return
        elseif IsAtLeast(MapVar(6), 2) then
            evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
            evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
            return
        else
            return
        end
    end
    SetValue(MapVar(6), 2)
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
    evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
end)

RegisterEvent(3, "Legacy event 3", function()
    evt.SetDoorState(5, DoorAction.Trigger)
end)

RegisterEvent(4, "Legacy event 4", function()
    evt.SetDoorState(1, DoorAction.Trigger)
    evt.SetDoorState(2, DoorAction.Trigger)
end)

RegisterEvent(5, "Legacy event 5", function()
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
        evt.MoveToMap(0, 3808, 129, 270, 0, 0, 0, 0, "\tmdt15.blv")
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

RegisterEvent(377, "Legacy event 377", function()
    if IsQBitSet(QBit(533)) then -- Go to the Celestial Court in Celeste and kill Lady Eleanor Carmine. Return with proof to Seknit Undershadow in the Deyja Moors.
        evt.SetMonGroupBit(52, MonsterBits.Invisible, 0)
        evt.SetMonGroupBit(52, MonsterBits.Hostile, 1)
        SetValue(MapVar(2), 1)
    end
end)

RegisterEvent(378, "Legacy event 378", function()
    if not IsAtLeast(MapVar(2), 1) then return end
    if evt.CheckMonstersKilled(ActorKillCheck.Group, 52, 0, false) then -- actor group 52; all matching actors defeated
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

RegisterEvent(451, "Legacy event 451", function()
    local randomStep = PickRandomOption(451, 1, {1, 2, 3, 4, 5, 6})
    if randomStep == 1 then
        evt.MoveToMap(8146, 4379, 3700, 0, 0, 0, 0, 0)
        evt.MoveToMap(-2815, 1288, 3700, 0, 0, 0, 0, 0)
        evt.MoveToMap(-11883, 8667, 3700, 0, 0, 0, 0, 0)
        evt.MoveToMap(-22231, 13145, 3700, 0, 0, 0, 0, 0)
        evt.MoveToMap(-12770, 18344, 3700, 0, 0, 0, 0, 0)
    elseif randomStep == 2 then
        evt.MoveToMap(-2815, 1288, 3700, 0, 0, 0, 0, 0)
        evt.MoveToMap(-11883, 8667, 3700, 0, 0, 0, 0, 0)
        evt.MoveToMap(-22231, 13145, 3700, 0, 0, 0, 0, 0)
        evt.MoveToMap(-12770, 18344, 3700, 0, 0, 0, 0, 0)
    elseif randomStep == 3 then
        evt.MoveToMap(-11883, 8667, 3700, 0, 0, 0, 0, 0)
        evt.MoveToMap(-22231, 13145, 3700, 0, 0, 0, 0, 0)
        evt.MoveToMap(-12770, 18344, 3700, 0, 0, 0, 0, 0)
    elseif randomStep == 4 then
        evt.MoveToMap(-22231, 13145, 3700, 0, 0, 0, 0, 0)
        evt.MoveToMap(-12770, 18344, 3700, 0, 0, 0, 0, 0)
    elseif randomStep == 5 then
        evt.MoveToMap(-12770, 18344, 3700, 0, 0, 0, 0, 0)
    end
    evt.MoveToMap(9185, 18564, 3700, 0, 0, 0, 0, 0)
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
    evt.MoveToMap(-9718, 10097, 2449, 1536, 0, 0, 0, 0, "7out06.odm")
end, "Leave Celeste")

RegisterEvent(502, "Enter the Walls of Mist", function()
    evt.MoveToMap(-896, -4717, 161, 512, 0, 0, 144, 1, "\t7d11.blv")
end, "Enter the Walls of Mist")

RegisterEvent(503, "Enter Castle Lambent", function()
    evt.MoveToMap(64, -640, 1, 512, 0, 0, 130, 1, "\t7d30.blv")
end, "Enter Castle Lambent")

RegisterEvent(504, "Enter The Temple of the Light", function()
    evt.EnterHouse(316) -- Temple of Light
end, "Enter The Temple of the Light")

