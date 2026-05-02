-- Misty Islands
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {101, 102, 103, 104, 105, 106, 107, 108, 213},
    onLeave = {},
    openedChestIds = {
    [75] = {1},
    [76] = {2},
    [77] = {3},
    [78] = {4},
    [79] = {5},
    },
    textureNames = {},
    spriteNames = {"6tree06"},
    castSpellIds = {6},
    timers = {
    { eventId = 210, repeating = true, intervalGameMinutes = 5, remainingGameMinutes = 5 },
    },
})

RegisterNoOpEvent(1, "Tree", "Tree")

RegisterEvent(2, "Drink from Fountain.", function()
    evt.EnterHouse(26) -- Placeholder
end, "Drink from Fountain.")

RegisterEvent(3, "Drink from Fountain.", nil, "Drink from Fountain.")

RegisterEvent(4, "You pray at the shrine.", function()
    evt.EnterHouse(63) -- The Windling
end, "You pray at the shrine.")

RegisterEvent(5, "You pray at the shrine.", nil, "You pray at the shrine.")

RegisterEvent(6, "Placeholder", function()
    evt.EnterHouse(98) -- Placeholder
end, "Placeholder")

RegisterEvent(7, "Legacy event 7", nil)

RegisterEvent(8, "Legacy event 8", function()
    evt.EnterHouse(1229)
end)

RegisterEvent(9, "Legacy event 9", nil)

RegisterEvent(10, "Balthazar Lair", function()
    evt.EnterHouse(499) -- Balthazar Lair
end, "Balthazar Lair")

RegisterEvent(11, "Legacy event 11", function()
    evt.EnterHouse(1590)
end)

RegisterEvent(12, "Legacy event 12", nil)

RegisterEvent(13, "Abandoned Pirate Keep", function()
    evt.EnterHouse(210) -- Abandoned Pirate Keep
end, "Abandoned Pirate Keep")

RegisterEvent(14, "Featherwind's House", function()
    evt.EnterHouse(330) -- Featherwind's House
end, "Featherwind's House")

RegisterEvent(15, "Maylander's House", function()
    evt.EnterHouse(261) -- Maylander's House
end, "Maylander's House")

RegisterEvent(16, "Maylander's House", nil, "Maylander's House")

RegisterEvent(17, "Sparkman Home", function()
    evt.EnterHouse(298) -- Sparkman Home
end, "Sparkman Home")

RegisterEvent(18, "Sparkman Home", nil, "Sparkman Home")

RegisterEvent(19, "Bank of Balthazar", function()
    evt.EnterHouse(132) -- Bank of Balthazar
end, "Bank of Balthazar")

RegisterEvent(20, "Bank of Balthazar", nil, "Bank of Balthazar")

RegisterEvent(21, "Placeholder", function()
    evt.EnterHouse(138) -- Placeholder
end, "Placeholder")

RegisterEvent(22, "Placeholder", nil, "Placeholder")

RegisterEvent(23, "Placeholder", function()
    evt.EnterHouse(144) -- Placeholder
end, "Placeholder")

RegisterEvent(24, "Placeholder", nil, "Placeholder")

RegisterEvent(25, "Ogre Raiding Fort", function()
    evt.EnterHouse(198) -- Ogre Raiding Fort
end, "Ogre Raiding Fort")

RegisterEvent(26, "Ogre Raiding Fort", nil, "Ogre Raiding Fort")

RegisterEvent(27, "Pirate Outpost", function()
    evt.EnterHouse(192) -- Pirate Outpost
end, "Pirate Outpost")

RegisterEvent(28, "Pirate Outpost", nil, "Pirate Outpost")

RegisterEvent(29, "Abandoned Pirate Keep", nil, "Abandoned Pirate Keep")

RegisterEvent(30, "Gateway to the Plane of Water", function()
    evt.MoveToMap(0, 0, 0, 0, 0, 0, 80, 1, "0.")
    evt.EnterHouse(223) -- Gateway to the Plane of Water
end, "Gateway to the Plane of Water")

RegisterEvent(31, "Welcome to Misty Islands", nil, "Welcome to Misty Islands")

RegisterEvent(50, "Legacy event 50", function()
    evt.EnterHouse(1227)
end)

RegisterEvent(51, "Legacy event 51", function()
    evt.EnterHouse(1242)
end)

RegisterEvent(52, "Legacy event 52", function()
    evt.EnterHouse(1257)
end)

RegisterEvent(53, "Legacy event 53", function()
    evt.EnterHouse(1272)
end)

RegisterEvent(54, "Legacy event 54", function()
    evt.EnterHouse(1287)
end)

RegisterEvent(55, "Legacy event 55", function()
    evt.EnterHouse(1302)
end)

RegisterEvent(56, "Legacy event 56", function()
    evt.EnterHouse(1315)
end)

RegisterEvent(57, "Legacy event 57", function()
    evt.EnterHouse(1327)
end)

RegisterEvent(58, "Legacy event 58", function()
    evt.EnterHouse(1338)
end)

RegisterEvent(59, "Legacy event 59", function()
    evt.EnterHouse(1350)
end)

RegisterEvent(60, "Legacy event 60", function()
    evt.EnterHouse(1362)
end)

RegisterEvent(61, "Legacy event 61", function()
    evt.EnterHouse(1373)
    if IsQBitSet(QBit(1325)) then return end -- NPC
    SetQBit(QBit(1325)) -- NPC
end)

RegisterEvent(62, "Legacy event 62", function()
    evt.EnterHouse(1384)
end)

RegisterEvent(75, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(76, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(77, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(78, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(79, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(90, "Legacy event 90", function()
    evt.MoveToMap(4427, 3061, 769, 1024, 0, 0, 178, 1, "6d07.blv")
end)

RegisterEvent(91, "Legacy event 91", function()
    if IsQBitSet(QBit(1325)) then -- NPC
        evt.MoveToMap(-18176, -1072, 96, 512, 0, 0, 0, 0)
    end
end)

RegisterEvent(92, "Legacy event 92", function()
    evt.MoveToMap(4688, -2944, 96, 1400, 0, 0, 0, 0)
end)

RegisterEvent(101, "Tree", function()
    if not IsAtLeast(MapVar(2), 1) then
        SetValue(MapVar(2), 1)
        AddValue(Food, 1)
        evt.StatusText("Tree")
        evt.SetSprite(134, 1, "6tree06")
        return
    end
    evt.StatusText("There doesn't seem to be anymore apples.")
    if not IsAtLeast(MapVar(2), 1) then return end
    evt.SetSprite(134, 1, "6tree06")
end, "Tree")

RegisterEvent(102, "Tree", function()
    if not IsAtLeast(MapVar(3), 1) then
        SetValue(MapVar(3), 1)
        AddValue(Food, 1)
        evt.StatusText("Tree")
        evt.SetSprite(135, 1, "6tree06")
        return
    end
    evt.StatusText("There doesn't seem to be anymore apples.")
    if not IsAtLeast(MapVar(3), 1) then return end
    evt.SetSprite(135, 1, "6tree06")
end, "Tree")

RegisterEvent(103, "Tree", function()
    if not IsAtLeast(MapVar(4), 1) then
        SetValue(MapVar(4), 1)
        AddValue(Food, 1)
        evt.StatusText("Tree")
        evt.SetSprite(136, 1, "6tree06")
        return
    end
    evt.StatusText("There doesn't seem to be anymore apples.")
    if not IsAtLeast(MapVar(4), 1) then return end
    evt.SetSprite(136, 1, "6tree06")
end, "Tree")

RegisterEvent(104, "Tree", function()
    if not IsAtLeast(MapVar(5), 1) then
        SetValue(MapVar(5), 1)
        AddValue(Food, 1)
        evt.StatusText("Tree")
        evt.SetSprite(137, 1, "6tree06")
        return
    end
    evt.StatusText("There doesn't seem to be anymore apples.")
    if not IsAtLeast(MapVar(5), 1) then return end
    evt.SetSprite(137, 1, "6tree06")
end, "Tree")

RegisterEvent(105, "Tree", function()
    if not IsAtLeast(MapVar(6), 1) then
        SetValue(MapVar(6), 1)
        AddValue(Food, 1)
        evt.StatusText("Tree")
        evt.SetSprite(138, 1, "6tree06")
        return
    end
    evt.StatusText("There doesn't seem to be anymore apples.")
    if not IsAtLeast(MapVar(6), 1) then return end
    evt.SetSprite(138, 1, "6tree06")
end, "Tree")

RegisterEvent(106, "Tree", function()
    if not IsAtLeast(MapVar(7), 1) then
        SetValue(MapVar(7), 1)
        AddValue(Food, 1)
        evt.StatusText("Tree")
        evt.SetSprite(139, 1, "6tree06")
        return
    end
    evt.StatusText("There doesn't seem to be anymore apples.")
    if not IsAtLeast(MapVar(7), 1) then return end
    evt.SetSprite(139, 1, "6tree06")
end, "Tree")

RegisterEvent(107, "Tree", function()
    if not IsAtLeast(MapVar(8), 1) then
        SetValue(MapVar(8), 1)
        AddValue(Food, 1)
        evt.StatusText("Tree")
        evt.SetSprite(140, 1, "6tree06")
        return
    end
    evt.StatusText("There doesn't seem to be anymore apples.")
    if not IsAtLeast(MapVar(8), 1) then return end
    evt.SetSprite(140, 1, "6tree06")
end, "Tree")

RegisterEvent(108, "Tree", function()
    if not IsAtLeast(MapVar(9), 1) then
        SetValue(MapVar(9), 1)
        AddValue(Food, 1)
        evt.StatusText("Tree")
        evt.SetSprite(141, 1, "6tree06")
        return
    end
    evt.StatusText("There doesn't seem to be anymore apples.")
    if not IsAtLeast(MapVar(9), 1) then return end
    evt.SetSprite(141, 1, "6tree06")
end, "Tree")

RegisterEvent(109, "Drink from Fountain.", function()
    if not IsAtLeast(MapVar(11), 1) then
        evt.StatusText("Refreshing!")
        return
    end
    SubtractValue(MapVar(11), 1)
    AddValue(CurrentSpellPoints, 10)
    evt.StatusText("+10 Spell points restored.")
    SetAutonote(401) -- 10 Spell points restored by the central fountain in Mist.
end, "Drink from Fountain.")

RegisterEvent(110, "Drink from Fountain.", function()
    if not IsAtLeast(IntellectBonus, 10) then
        SetValue(IntellectBonus, 10)
        SetValue(PersonalityBonus, 10)
        evt.StatusText("+10 Intellect and Personality temporary.")
        SetAutonote(403) -- 10 Points of temporary intellect and personality from the west fountain at Castle Newton.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain.")

RegisterEvent(111, "Drink from Fountain.", function()
    if not IsAtLeast(FireResistanceBonus, 5) then
        SetValue(FireResistanceBonus, 5)
        SetValue(AirResistanceBonus, 5)
        SetValue(WaterResistanceBonus, 5)
        SetValue(EarthResistanceBonus, 5)
        evt.StatusText("+5 Elemental resistance temporary.")
        SetAutonote(404) -- 5 Points of temporary fire, electricity, cold, and poison resistance from the east fountain at Castle Newton.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain.")

RegisterEvent(112, "Drink from Well.", function()
    if not IsAtLeast(LuckBonus, 20) then
        SetValue(LuckBonus, 20)
        evt.StatusText("+20 Luck temporary.")
        SetAutonote(402) -- 20 Points of temporary luck from the fountain west of the Imp Slapper in Mist.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Well.")

RegisterEvent(113, "Drink from Trough.", function()
    evt.DamagePlayer(7, 2, 20)
    SetValue(PoisonedYellow, 1)
    evt.StatusText("Poison!")
end, "Drink from Trough.")

RegisterEvent(114, "Drink from Trough.", function()
    evt.StatusText("Refreshing!")
end, "Drink from Trough.")

RegisterEvent(210, "Legacy event 210", function()
    if IsQBitSet(QBit(1181)) then -- NPC
        return
    elseif IsAtLeast(IsFlying, 0) then
        evt.CastSpell(6, 5, 3, 3039, -9201, 2818, 0, 0, 0) -- Fireball
    else
        return
    end
end)

RegisterEvent(211, "Legacy event 211", function()
    evt.ForPlayer(Players.All)
    if IsQBitSet(QBit(1181)) then -- NPC
        return
    elseif HasItem(2106) then -- Dragon Tower Keys
        SetQBit(QBit(1181)) -- NPC
        return
    else
        return
    end
end)

RegisterEvent(212, "Obelisk", function()
    evt.SimpleMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            f_oteh__fe_h__e_")
    SetQBit(QBit(1397)) -- NPC
    SetAutonote(455) -- Obelisk Message # 14: f_oteh__fe_h__e_
end, "Obelisk")

RegisterEvent(213, "Legacy event 213", function()
    if IsQBitSet(QBit(1181)) then -- NPC
    end
end)

RegisterEvent(261, "Shrine of Intellect", function()
    if not IsAtLeast(MonthIs, 1) then
        evt.StatusText("You pray at the shrine.")
        return
    end
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1232)) then -- NPC
            SetQBit(QBit(1232)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(BaseIntellect, 10)
            evt.StatusText("+10 Intellect permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(BaseIntellect, 3)
        evt.StatusText("+3 Intellect permanent")
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Intellect")

