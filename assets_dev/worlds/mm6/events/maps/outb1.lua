-- Kriegspire
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {151},
    onLeave = {},
    openedChestIds = {
    [75] = {1},
    [76] = {2},
    },
    textureNames = {},
    spriteNames = {"ped01"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(2, "Shrine of Cold", function()
    evt.EnterHouse(35) -- Gifts of Regna
end, "Shrine of Cold")

RegisterEvent(3, "Shrine of Cold", nil, "Shrine of Cold")

RegisterEvent(4, "Placeholder", function()
    evt.EnterHouse(73) -- Placeholder
end, "Placeholder")

RegisterEvent(5, "Placeholder", nil, "Placeholder")

RegisterEvent(6, "Placeholder", function()
    evt.EnterHouse(104) -- Placeholder
end, "Placeholder")

RegisterEvent(7, "Placeholder", nil, "Placeholder")

RegisterEvent(8, "Griven's House", function()
    evt.EnterHouse(477) -- Griven's House
end, "Griven's House")

RegisterEvent(9, "Griven's House", nil, "Griven's House")

RegisterEvent(10, "Legacy event 10", function()
    evt.EnterHouse(1591)
end)

RegisterEvent(11, "Legacy event 11", nil)

RegisterEvent(12, "House Memoria", function()
    evt.EnterHouse(279) -- House Memoria
end, "House Memoria")

RegisterEvent(13, "House Memoria", nil, "House Memoria")

RegisterEvent(14, "Legacy event 14", function()
    evt.EnterHouse(1451)
end)

RegisterEvent(40, "Legacy event 40", function()
    evt.EnterHouse(1248)
end)

RegisterEvent(41, "Legacy event 41", function()
    evt.EnterHouse(1262)
end)

RegisterEvent(42, "Legacy event 42", function()
    evt.EnterHouse(1277)
end)

RegisterEvent(43, "Legacy event 43", function()
    evt.EnterHouse(1292)
end)

RegisterEvent(50, "Legacy event 50", function()
    evt.EnterHouse(1219)
end)

RegisterEvent(51, "Legacy event 51", function()
    evt.EnterHouse(1234)
end)

RegisterEvent(52, "Legacy event 52", function()
    evt.EnterHouse(1249)
end)

RegisterEvent(53, "Legacy event 53", function()
    evt.EnterHouse(1263)
end)

RegisterEvent(54, "Legacy event 54", function()
    evt.EnterHouse(1278)
end)

RegisterEvent(55, "Legacy event 55", function()
    evt.EnterHouse(1293)
end)

RegisterEvent(56, "Legacy event 56", function()
    evt.EnterHouse(1306)
end)

RegisterEvent(57, "Legacy event 57", function()
    evt.EnterHouse(1318)
end)

RegisterEvent(58, "Legacy event 58", function()
    evt.EnterHouse(1340)
end)

RegisterEvent(59, "Legacy event 59", function()
    evt.EnterHouse(1352)
end)

RegisterEvent(60, "Legacy event 60", function()
    evt.EnterHouse(1363)
end)

RegisterEvent(61, "Legacy event 61", function()
    evt.EnterHouse(1374)
end)

RegisterEvent(62, "Legacy event 62", function()
    evt.EnterHouse(1385)
end)

RegisterEvent(63, "Legacy event 63", function()
    evt.EnterHouse(1395)
end)

RegisterEvent(64, "Legacy event 64", function()
    evt.EnterHouse(1405)
end)

RegisterEvent(65, "Legacy event 65", function()
    evt.EnterHouse(1415)
end)

RegisterEvent(75, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(76, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(90, "Legacy event 90", function()
    evt.ForPlayer(Players.All)
    if not HasItem(2105) then -- Cloak of Baa
        evt.StatusText("You are not a follower of Baa.  Begone!")
        return
    end
    evt.MoveToMap(2094, -19, 177, 337, 0, 0, 179, 1, "6t7.blv")
end)

RegisterEvent(91, "Legacy event 91", function()
    evt.MoveToMap(2702, -2926, 1, 1024, 0, 0, 192, 1, "6d19.blv")
end)

RegisterEvent(92, "Legacy event 92", function()
    evt.MoveToMap(-49, -42, -2, 512, 0, 0, 193, 1, "6d20.blv")
end)

RegisterEvent(93, "Legacy event 93", function()
    evt.MoveToMap(5861, 2720, 169, 0, 0, 0, 171, 1, "cd3.blv")
end)

RegisterEvent(94, "Demon Lair", function()
    evt.MoveToMap(1893, 122, 1, 1024, 0, 0, 0, 0, "zdwj02.blv")
end, "Demon Lair")

RegisterEvent(100, "Drink from Well.", function()
    evt.StatusText("You feel Strange.")
    evt.MoveToMap(12768, 4192, 512, 0, 0, 0, 0, 0)
end, "Drink from Well.")

RegisterEvent(101, "Drink from Well.", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.StatusText("Refreshing!")
        return
    end
    if IsAtLeast(Gold, 5000) then
        SubtractValue(Gold, 5000)
        AddValue(Experience, 5000)
        SubtractValue(MapVar(2), 1)
        evt.StatusText("\"+5000 Experience, -5000 Gold.\"")
        SetAutonote(434) -- 5000 Experience and minus 5000 gold from the southern well in the town of Kriegspire.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Well.")

RegisterEvent(102, "Drink from Well.", function()
    if not IsAtLeast(LevelBonus, 30) then
        SetValue(LevelBonus, 30)
        evt.StatusText("+30 Level temporary.  Look Out!")
        SetAutonote(435) -- 30 Temporary levels from the western well in the town of Kriegspire.
        evt.SummonMonsters(3, 3, 2, -13280, 19696, 160, 0, 0) -- encounter slot 3 "BDragonFly" tier C, count 2, pos=(-13280, 19696, 160), actor group 0, no unique actor name
        evt.SummonMonsters(3, 3, 2, -13368, 18096, 160, 0, 0) -- encounter slot 3 "BDragonFly" tier C, count 2, pos=(-13368, 18096, 160), actor group 0, no unique actor name
        evt.SummonMonsters(3, 3, 2, -10976, 18152, 160, 0, 0) -- encounter slot 3 "BDragonFly" tier C, count 2, pos=(-10976, 18152, 160), actor group 0, no unique actor name
        evt.SummonMonsters(3, 3, 2, -9992, 19056, 160, 0, 0) -- encounter slot 3 "BDragonFly" tier C, count 2, pos=(-9992, 19056, 160), actor group 0, no unique actor name
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Well.")

RegisterEvent(103, "Drink from Fountain", function()
    if not IsPlayerBitSet(PlayerBit(68)) then
        SetPlayerBit(PlayerBit(68))
        AddValue(FireResistance, 10)
        SetValue(MapVar(0), 0)
        evt.StatusText("+10 Magic resistance permanent.")
        SetAutonote(436) -- 10 Points of permanent magic resistance from the fountain north of the Dragon Tower in the town of Kriegspire.
        return
    end
    SetValue(MapVar(0), 0)
end, "Drink from Fountain")

RegisterEvent(104, "Drink from Fountain", function()
    if not IsAtLeast(ArmorClassBonus, 40) then
        SetValue(ArmorClassBonus, 40)
        evt.StatusText("+40 Armor class temporary.")
        SetAutonote(437) -- 40 Points of temporary armor class from the fountain outside of Castle Kriegspire.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain")

RegisterEvent(105, "Drink from Fountain", function()
    if not IsPlayerBitSet(PlayerBit(67)) then
        SetPlayerBit(PlayerBit(67))
        AddValue(FireResistance, 5)
        AddValue(AirResistance, 5)
        AddValue(WaterResistance, 5)
        AddValue(EarthResistance, 5)
        SetValue(Eradicated, 0)
        evt.StatusText("+5 Elemental resistance permanent.")
        SetAutonote(438) -- 5 Points of permanent fire, electricity, cold, and poison resistance from the fountain northwest of the Superior Temple of Baa.
        return
    end
    SetValue(Eradicated, 0)
end, "Drink from Fountain")

RegisterEvent(150, "Pedestal", function()
    if not HasItem(2071) then return end -- Bear Statuette
    RemoveItem(2071) -- Bear Statuette
    evt.SetSprite(141, 1, "ped01")
    SetQBit(QBit(1247)) -- NPC
    if not IsQBitSet(QBit(1246)) then return end -- NPC
    if not IsQBitSet(QBit(1248)) then return end -- NPC
    if not IsQBitSet(QBit(1249)) then return end -- NPC
    if IsQBitSet(QBit(1250)) then -- NPC
        evt.MoveNPC(872, 0) -- Twillen -> removed
        evt.MoveNPC(826, 1342) -- Twillen -> house 1342
    end
end, "Pedestal")

RegisterEvent(151, "Legacy event 151", function()
    if IsQBitSet(QBit(1247)) then -- NPC
        evt.SetSprite(141, 1, "ped01")
    end
end)

RegisterEvent(152, "Obelisk", function()
    evt.SimpleMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            t_haat_lt__en_lc")
    SetQBit(QBit(1387)) -- NPC
    SetAutonote(445) -- Obelisk Message # 4: t_haat_lt__en_lc
end, "Obelisk")

RegisterEvent(261, "Shrine of Cold", function()
    if not IsAtLeast(MonthIs, 9) then
        evt.StatusText("You pray at the shrine.")
        return
    end
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1240)) then -- NPC
            SetQBit(QBit(1240)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(WaterResistance, 10)
            evt.StatusText("+10 Cold resistance permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(WaterResistance, 3)
        evt.StatusText("+3 Cold resistance permanent")
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Cold")

RegisterEvent(262, "Shrine of Fire", function()
    if not IsAtLeast(MonthIs, 7) then
        evt.StatusText("You pray at the shrine.")
        return
    end
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1238)) then -- NPC
            SetQBit(QBit(1238)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(FireResistance, 10)
            evt.StatusText("+10 Fire permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(FireResistance, 3)
        evt.StatusText("+3 Fire permanent")
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Fire")

