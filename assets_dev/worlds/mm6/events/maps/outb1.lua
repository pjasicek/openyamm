-- Kriegspire
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {151},
    onLeave = {},
    openedChestIds = {
    [75] = {1},
    [76] = {2},
    },
    contextActions = {
    [2] = { kind = "enter_house", source = "opcode", houseId = 35, targetName = "Knight's Paradise" },
    [4] = { kind = "enter_house", source = "opcode", houseId = 73, targetName = "Armorworks " },
    [6] = { kind = "enter_house", source = "opcode", houseId = 104, targetName = "Unusual Enchantments" },
    [8] = { kind = "enter_house", source = "opcode", houseId = 477, targetName = "King's Highway" },
    [10] = { kind = "enter_house", source = "opcode", houseId = 1591, targetName = "Lone Tree Training" },
    [12] = { kind = "enter_house", source = "opcode", houseId = 279, targetName = "The Broken Promise" },
    [14] = { kind = "enter_house", source = "opcode", houseId = 1451, targetName = "Hermit's Hut" },
    [40] = { kind = "enter_house", source = "opcode", houseId = 1248, targetName = "House" },
    [41] = { kind = "enter_house", source = "opcode", houseId = 1262, targetName = "House" },
    [42] = { kind = "enter_house", source = "opcode", houseId = 1277, targetName = "House" },
    [43] = { kind = "enter_house", source = "opcode", houseId = 1292, targetName = "House" },
    [50] = { kind = "enter_house", source = "opcode", houseId = 1219, targetName = "House" },
    [51] = { kind = "enter_house", source = "opcode", houseId = 1234, targetName = "House" },
    [52] = { kind = "enter_house", source = "opcode", houseId = 1249, targetName = "House" },
    [53] = { kind = "enter_house", source = "opcode", houseId = 1263, targetName = "House" },
    [54] = { kind = "enter_house", source = "opcode", houseId = 1278, targetName = "House" },
    [55] = { kind = "enter_house", source = "opcode", houseId = 1293, targetName = "House" },
    [56] = { kind = "enter_house", source = "opcode", houseId = 1306, targetName = "House" },
    [57] = { kind = "enter_house", source = "opcode", houseId = 1318, targetName = "House" },
    [58] = { kind = "enter_house", source = "opcode", houseId = 1340, targetName = "House" },
    [59] = { kind = "enter_house", source = "opcode", houseId = 1352, targetName = "House" },
    [60] = { kind = "enter_house", source = "opcode", houseId = 1363, targetName = "House" },
    [61] = { kind = "enter_house", source = "opcode", houseId = 1374, targetName = "House" },
    [62] = { kind = "enter_house", source = "opcode", houseId = 1385, targetName = "House" },
    [63] = { kind = "enter_house", source = "opcode", houseId = 1395, targetName = "House" },
    [64] = { kind = "enter_house", source = "opcode", houseId = 1405, targetName = "House" },
    [65] = { kind = "enter_house", source = "opcode", houseId = 1415, targetName = "House" },
    [75] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [76] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [90] = { kind = "enter_house", source = "opcode", houseId = 435, targetName = "Superior Temple of Baa" },
    [91] = { kind = "enter_house", source = "opcode", houseId = 448, targetName = "Agar's Laboratory" },
    [92] = { kind = "enter_house", source = "opcode", houseId = 449, targetName = "Caves of the Dragon Riders" },
    [93] = { kind = "enter_house", source = "opcode", houseId = 427, targetName = "Castle Kriegspire" },
    [94] = { kind = "enter_dungeon", source = "opcode", targetMap = "zdwj02.blv", targetName = "Devil Outpost" },
    [100] = { kind = "enter_dungeon", source = "opcode", targetMap = "cd3.blv", targetName = "Castle Kriegspire" },
    [101] = { kind = "well", source = "title" },
    [102] = { kind = "well", source = "title" },
    [103] = { kind = "fountain", source = "title" },
    [104] = { kind = "fountain", source = "title" },
    [105] = { kind = "fountain", source = "title" },
    [150] = { kind = "use_pedestal", source = "title" },
    [152] = { kind = "obelisk", source = "title" },
    [261] = { kind = "shrine", source = "title" },
    [262] = { kind = "shrine", source = "title" },
    },
    textureNames = {},
    spriteNames = {"ped01"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(2, "Knight's Paradise", function()
    evt.EnterHouse(35) -- Knight's Paradise
end, "Knight's Paradise")

RegisterEvent(3, "Knight's Paradise", nil, "Knight's Paradise")

RegisterEvent(4, "Armorworks ", function()
    evt.EnterHouse(73) -- Armorworks
end, "Armorworks ")

RegisterEvent(5, "Armorworks ", nil, "Armorworks ")

RegisterEvent(6, "Unusual Enchantments", function()
    evt.EnterHouse(104) -- Unusual Enchantments
end, "Unusual Enchantments")

RegisterEvent(7, "Unusual Enchantments", nil, "Unusual Enchantments")

RegisterEvent(8, "King's Highway", function()
    evt.EnterHouse(477) -- King's Highway
end, "King's Highway")

RegisterEvent(9, "King's Highway", nil, "King's Highway")

RegisterEvent(10, "Lone Tree Training", function()
    evt.EnterHouse(1591) -- Lone Tree Training
end, "Lone Tree Training")

RegisterEvent(11, "Lone Tree Training", nil, "Lone Tree Training")

RegisterEvent(12, "The Broken Promise", function()
    evt.EnterHouse(279) -- The Broken Promise
end, "The Broken Promise")

RegisterEvent(13, "The Broken Promise", nil, "The Broken Promise")

RegisterEvent(14, "Hermit's Hut", function()
    evt.EnterHouse(1451) -- Hermit's Hut
end, "Hermit's Hut")

RegisterEvent(40, "House", function()
    evt.EnterHouse(1248) -- House
end, "House")

RegisterEvent(41, "House", function()
    evt.EnterHouse(1262) -- House
end, "House")

RegisterEvent(42, "House", function()
    evt.EnterHouse(1277) -- House
end, "House")

RegisterEvent(43, "House", function()
    evt.EnterHouse(1292) -- House
end, "House")

RegisterEvent(50, "House", function()
    evt.EnterHouse(1219) -- House
end, "House")

RegisterEvent(51, "House", function()
    evt.EnterHouse(1234) -- House
end, "House")

RegisterEvent(52, "House", function()
    evt.EnterHouse(1249) -- House
end, "House")

RegisterEvent(53, "House", function()
    evt.EnterHouse(1263) -- House
end, "House")

RegisterEvent(54, "House", function()
    evt.EnterHouse(1278) -- House
end, "House")

RegisterEvent(55, "House", function()
    evt.EnterHouse(1293) -- House
end, "House")

RegisterEvent(56, "House", function()
    evt.EnterHouse(1306) -- House
end, "House")

RegisterEvent(57, "House", function()
    evt.EnterHouse(1318) -- House
end, "House")

RegisterEvent(58, "House", function()
    evt.EnterHouse(1340) -- House
end, "House")

RegisterEvent(59, "House", function()
    evt.EnterHouse(1352) -- House
end, "House")

RegisterEvent(60, "House", function()
    evt.EnterHouse(1363) -- House
end, "House")

RegisterEvent(61, "House", function()
    evt.EnterHouse(1374) -- House
end, "House")

RegisterEvent(62, "House", function()
    evt.EnterHouse(1385) -- House
end, "House")

RegisterEvent(63, "House", function()
    evt.EnterHouse(1395) -- House
end, "House")

RegisterEvent(64, "House", function()
    evt.EnterHouse(1405) -- House
end, "House")

RegisterEvent(65, "House", function()
    evt.EnterHouse(1415) -- House
end, "House")

RegisterEvent(75, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(76, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(90, nil, function()
    evt.ForPlayer(Players.All)
    if not HasItem(2105) then -- Cloak of Baa
        evt.StatusText("You are not a follower of Baa.  Begone!")
        return
    end
    evt.MoveToMap(2094, -19, 177, 337, 0, 0, 179, 1, "6t7.blv") -- Superior Temple of Baa
end)

RegisterEvent(91, nil, function()
    evt.MoveToMap(2702, -2926, 1, 1024, 0, 0, 192, 1, "6d19.blv") -- Agar's Laboratory
end)

RegisterEvent(92, nil, function()
    evt.MoveToMap(-49, -42, -2, 512, 0, 0, 193, 1, "6d20.blv") -- Caves of the Dragon Riders
end)

RegisterEvent(93, nil, function()
    evt.MoveToMap(5861, 2720, 169, 0, 0, 0, 171, 1, "cd3.blv") -- Castle Kriegspire
end)

RegisterEvent(94, "Demon Lair", function()
    evt.MoveToMap(1893, 122, 1, 1024, 0, 0, 0, 0, "zdwj02.blv") -- Devil Outpost
end, "Demon Lair")

RegisterEvent(100, "Drink from Well.", function()
    evt.StatusText("You feel Strange.")
    evt.MoveToMap(12768, 4192, 512, 0, 0, 0, 0, 0, "cd3.blv") -- Castle Kriegspire
end, "Drink from Well.")

RegisterEvent(101, "Drink from Well.", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.StatusText("Refreshing!")
        return
    end
    if IsAtLeast(Gold, 5000) then
        if not IsAtLeast(Gold, 5000) then
            return
        end
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
        evt.MoveNPC(826, 1342) -- Twillen -> House
    end
end, "Pedestal")

RegisterEvent(151, nil, function()
    if IsQBitSet(QBit(1247)) then -- NPC
        evt.SetSprite(141, 1, "ped01")
    end
end)

RegisterEvent(152, "Obelisk", function(continueStep)
    if continueStep == 2 then
        SetQBit(QBit(1387)) -- NPC
        SetAutonote(445) -- Obelisk Message # 4: t_haat_lt__en_lc
    end
    if continueStep ~= nil then return end
    evt.SetMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            t_haat_lt__en_lc")
    evt._PressAnyKey(152, 2)
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
        return
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
        return
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Fire")

