-- Castle Kriegspire
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {63},
    onLeave = {},
    openedChestIds = {
    [41] = {1},
    [42] = {2, 9},
    [43] = {3},
    [44] = {4},
    [45] = {5},
    [49] = {6},
    [50] = {7},
    },
    textureNames = {},
    spriteNames = {"crysdisc"},
    castSpellIds = {},
    timers = {
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

RegisterEvent(6, "Door", function()
    evt.SetDoorState(6, DoorAction.Close)
end, "Door")

RegisterEvent(7, "Door", function()
    evt.SetDoorState(7, DoorAction.Close)
end, "Door")

RegisterEvent(8, "Door", function()
    evt.SetDoorState(8, DoorAction.Close)
end, "Door")

RegisterEvent(9, "Door", function()
    evt.SetDoorState(9, DoorAction.Close)
end, "Door")

RegisterEvent(10, "Door", function()
    evt.SetDoorState(10, DoorAction.Close)
end, "Door")

RegisterEvent(11, "Door", function()
    evt.SetDoorState(11, DoorAction.Close)
end, "Door")

RegisterEvent(12, "Door", function()
    evt.SetDoorState(12, DoorAction.Close)
end, "Door")

RegisterEvent(13, "Guardian of Kriegspire", function(continueStep)
    if continueStep == 3 then
        evt.StatusText("Get Lost!")
        return
    end
    if continueStep == 5 then
        if not IsAtLeast(Gold, 50000) then
            evt.StatusText("Get Lost!")
            return
        end
        SubtractValue(Gold, 50000)
        evt.MoveToMap(13487, 3117, 673, 0, 0, 0, 0, 0)
    end
    if continueStep ~= nil then return end
    if not IsQBitSet(QBit(1364)) then -- NPC
        evt.SimpleMessage("\"The Guardian of Kriegspire proclaims, 'For 50,000 gold, the secret will be revealed!'\"")
        evt.AskQuestion(13, 3, 10, 5, 11, 12, "Accept (Yes/No)?", {"Yes", "Y"})
        return nil
    end
    evt.MoveToMap(13487, 3117, 673, 0, 0, 0, 0, 0)
end, "Guardian of Kriegspire")

RegisterEvent(15, "Legacy event 15", function()
    evt.MoveToMap(5773, 5678, -848, 0, 0, 0, 0, 0)
end)

RegisterEvent(17, "Door", function()
    evt.SetDoorState(17, DoorAction.Close)
end, "Door")

RegisterEvent(18, "Legacy event 18", function()
    evt.SetDoorState(18, DoorAction.Close)
end)

RegisterEvent(19, "Legacy event 19", function()
    evt.MoveToMap(-11534, -9562, 97, 1536, 0, 0, 0, 0, "outb1.odm")
end)

RegisterEvent(20, "Legacy event 20", function()
    if IsAtLeast(MapVar(3), 1) then return end
    evt.SummonMonsters(1, 1, 1, 13458, 3830, 673, 0, 0) -- encounter slot 1 "BMinotaur" tier A, count 1, pos=(13458, 3830, 673), actor group 0, no unique actor name
    evt.SummonMonsters(1, 1, 1, 13458, 4084, 673, 0, 0) -- encounter slot 1 "BMinotaur" tier A, count 1, pos=(13458, 4084, 673), actor group 0, no unique actor name
    evt.SummonMonsters(1, 1, 1, 13458, 4518, 673, 0, 0) -- encounter slot 1 "BMinotaur" tier A, count 1, pos=(13458, 4518, 673), actor group 0, no unique actor name
    evt.SummonMonsters(1, 1, 1, 13054, 4878, 673, 0, 0) -- encounter slot 1 "BMinotaur" tier A, count 1, pos=(13054, 4878, 673), actor group 0, no unique actor name
    evt.SummonMonsters(1, 2, 1, 12677, 4878, 673, 0, 0) -- encounter slot 1 "BMinotaur" tier B, count 1, pos=(12677, 4878, 673), actor group 0, no unique actor name
    evt.SummonMonsters(1, 2, 1, 12364, 4878, 673, 0, 0) -- encounter slot 1 "BMinotaur" tier B, count 1, pos=(12364, 4878, 673), actor group 0, no unique actor name
    evt.SummonMonsters(1, 2, 1, 11991, 4505, 673, 0, 0) -- encounter slot 1 "BMinotaur" tier B, count 1, pos=(11991, 4505, 673), actor group 0, no unique actor name
    evt.SummonMonsters(1, 2, 1, 11991, 4122, 673, 0, 0) -- encounter slot 1 "BMinotaur" tier B, count 1, pos=(11991, 4122, 673), actor group 0, no unique actor name
    evt.SummonMonsters(1, 3, 1, 11991, 3688, 673, 0, 0) -- encounter slot 1 "BMinotaur" tier C, count 1, pos=(11991, 3688, 673), actor group 0, no unique actor name
    evt.SummonMonsters(1, 3, 1, 12424, 3368, 673, 0, 0) -- encounter slot 1 "BMinotaur" tier C, count 1, pos=(12424, 3368, 673), actor group 0, no unique actor name
    evt.SummonMonsters(1, 3, 1, 12776, 3368, 673, 0, 0) -- encounter slot 1 "BMinotaur" tier C, count 1, pos=(12776, 3368, 673), actor group 0, no unique actor name
    evt.SummonMonsters(1, 3, 1, 13182, 3368, 673, 0, 0) -- encounter slot 1 "BMinotaur" tier C, count 1, pos=(13182, 3368, 673), actor group 0, no unique actor name
    SetValue(MapVar(3), 1)
end)

RegisterEvent(21, "Legacy event 21", function()
    if IsAtLeast(MapVar(4), 1) then return end
    evt.SummonMonsters(2, 1, 1, 14033, 4539, 673, 0, 0) -- encounter slot 2 "Cockatrice" tier A, count 1, pos=(14033, 4539, 673), actor group 0, no unique actor name
    evt.SummonMonsters(2, 1, 1, 14033, 4131, 673, 0, 0) -- encounter slot 2 "Cockatrice" tier A, count 1, pos=(14033, 4131, 673), actor group 0, no unique actor name
    evt.SummonMonsters(2, 1, 1, 14033, 3720, 673, 0, 0) -- encounter slot 2 "Cockatrice" tier A, count 1, pos=(14033, 3720, 673), actor group 0, no unique actor name
    evt.SummonMonsters(2, 1, 1, 14444, 3362, 673, 0, 0) -- encounter slot 2 "Cockatrice" tier A, count 1, pos=(14444, 3362, 673), actor group 0, no unique actor name
    evt.SummonMonsters(2, 2, 1, 14779, 3362, 673, 0, 0) -- encounter slot 2 "Cockatrice" tier B, count 1, pos=(14779, 3362, 673), actor group 0, no unique actor name
    evt.SummonMonsters(2, 2, 1, 15195, 3362, 673, 0, 0) -- encounter slot 2 "Cockatrice" tier B, count 1, pos=(15195, 3362, 673), actor group 0, no unique actor name
    evt.SummonMonsters(2, 2, 1, 15548, 3749, 673, 0, 0) -- encounter slot 2 "Cockatrice" tier B, count 1, pos=(15548, 3749, 673), actor group 0, no unique actor name
    evt.SummonMonsters(2, 2, 1, 15548, 4100, 673, 0, 0) -- encounter slot 2 "Cockatrice" tier B, count 1, pos=(15548, 4100, 673), actor group 0, no unique actor name
    evt.SummonMonsters(2, 3, 1, 15548, 4460, 673, 0, 0) -- encounter slot 2 "Cockatrice" tier C, count 1, pos=(15548, 4460, 673), actor group 0, no unique actor name
    evt.SummonMonsters(2, 3, 1, 15142, 4872, 673, 0, 0) -- encounter slot 2 "Cockatrice" tier C, count 1, pos=(15142, 4872, 673), actor group 0, no unique actor name
    evt.SummonMonsters(2, 3, 1, 14765, 4872, 673, 0, 0) -- encounter slot 2 "Cockatrice" tier C, count 1, pos=(14765, 4872, 673), actor group 0, no unique actor name
    evt.SummonMonsters(2, 3, 1, 14361, 4872, 673, 0, 0) -- encounter slot 2 "Cockatrice" tier C, count 1, pos=(14361, 4872, 673), actor group 0, no unique actor name
    SetValue(MapVar(4), 1)
end)

RegisterEvent(22, "Legacy event 22", function()
    if IsAtLeast(MapVar(5), 1) then return end
    evt.SummonMonsters(1, 1, 1, 12990, 1356, 673, 0, 0) -- encounter slot 1 "BMinotaur" tier A, count 1, pos=(12990, 1356, 673), actor group 0, no unique actor name
    evt.SummonMonsters(1, 1, 1, 12454, 1356, 673, 0, 0) -- encounter slot 1 "BMinotaur" tier A, count 1, pos=(12454, 1356, 673), actor group 0, no unique actor name
    evt.SummonMonsters(1, 2, 1, 13482, 1741, 673, 0, 0) -- encounter slot 1 "BMinotaur" tier B, count 1, pos=(13482, 1741, 673), actor group 0, no unique actor name
    evt.SummonMonsters(1, 2, 1, 13482, 2360, 673, 0, 0) -- encounter slot 1 "BMinotaur" tier B, count 1, pos=(13482, 2360, 673), actor group 0, no unique actor name
    evt.SummonMonsters(1, 3, 1, 13000, 2830, 673, 0, 0) -- encounter slot 1 "BMinotaur" tier C, count 1, pos=(13000, 2830, 673), actor group 0, no unique actor name
    evt.SummonMonsters(1, 3, 1, 12414, 2830, 673, 0, 0) -- encounter slot 1 "BMinotaur" tier C, count 1, pos=(12414, 2830, 673), actor group 0, no unique actor name
    evt.SummonMonsters(2, 1, 1, 13147, 2142, 673, 0, 0) -- encounter slot 2 "Cockatrice" tier A, count 1, pos=(13147, 2142, 673), actor group 0, no unique actor name
    evt.SummonMonsters(2, 1, 1, 12388, 2142, 673, 0, 0) -- encounter slot 2 "Cockatrice" tier A, count 1, pos=(12388, 2142, 673), actor group 0, no unique actor name
    evt.SummonMonsters(2, 2, 1, 12750, 2501, 673, 0, 0) -- encounter slot 2 "Cockatrice" tier B, count 1, pos=(12750, 2501, 673), actor group 0, no unique actor name
    evt.SummonMonsters(2, 2, 1, 12750, 1703, 673, 0, 0) -- encounter slot 2 "Cockatrice" tier B, count 1, pos=(12750, 1703, 673), actor group 0, no unique actor name
    evt.SummonMonsters(2, 3, 1, 12441, 1760, 673, 0, 0) -- encounter slot 2 "Cockatrice" tier C, count 1, pos=(12441, 1760, 673), actor group 0, no unique actor name
    evt.SummonMonsters(2, 3, 1, 13115, 2297, 673, 0, 0) -- encounter slot 2 "Cockatrice" tier C, count 1, pos=(13115, 2297, 673), actor group 0, no unique actor name
    SetValue(MapVar(5), 1)
end)

RegisterEvent(23, "Legacy event 23", function()
    if IsAtLeast(MapVar(6), 1) then return end
    evt.SummonMonsters(3, 1, 1, 14373, 2407, 256, 0, 0) -- encounter slot 3 "BDragonFly" tier A, count 1, pos=(14373, 2407, 256), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 14373, 1670, 256, 0, 0) -- encounter slot 3 "BDragonFly" tier A, count 1, pos=(14373, 1670, 256), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 15056, 1670, 256, 0, 0) -- encounter slot 3 "BDragonFly" tier B, count 1, pos=(15056, 1670, 256), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 15056, 2407, 256, 0, 0) -- encounter slot 3 "BDragonFly" tier C, count 1, pos=(15056, 2407, 256), actor group 0, no unique actor name
    SetValue(MapVar(6), 1)
end)

RegisterEvent(24, "Legacy event 24", function()
    if IsAtLeast(MapVar(7), 1) then return end
    SetValue(MapVar(7), 1)
    AddValue(Gold, 15000)
end)

RegisterEvent(25, "Legacy event 25", function()
    if IsAtLeast(MapVar(8), 1) then return end
    SetValue(MapVar(8), 1)
    AddValue(Gold, 15000)
end)

RegisterEvent(26, "Cage", function()
    if IsAtLeast(MapVar(10), 1) then return end
    AddValue(InventoryItem(2165), 2165) -- Roland's Journal
    SetValue(MapVar(10), 1)
end, "Cage")

RegisterEvent(27, "Curator of Kriegspire", function(continueStep)
    if continueStep == 2 then
        evt.StatusText("Get Lost!")
        return
    end
    if continueStep == 4 then
        if not IsAtLeast(Gold, 10000) then
            evt.StatusText("Get Lost!")
            return
        end
        SubtractValue(Gold, 10000)
        evt.ForPlayer(Players.All)
        SetValue(MapVar(1), 0)
        AddValue(MaxHealth, 0)
        AddValue(MaxSpellPoints, 0)
        SubtractValue(1638635, 25)
    end
    if continueStep ~= nil then return end
    evt.SimpleMessage("\"The Curator of Kriegspire proclaims, 'For 10,000 gold you shall be healed.'\"")
    evt.AskQuestion(27, 2, 10, 4, 11, 12, "Accept (Yes/No)?", {"Yes", "Y"})
    return nil
end, "Curator of Kriegspire")

RegisterEvent(31, "Door", function()
    evt.SetDoorState(31, DoorAction.Close)
    evt.SetDoorState(32, DoorAction.Close)
end, "Door")

RegisterEvent(41, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(42, "Chest", function()
    if not IsAtLeast(MapVar(2), 1) then
        if not IsQBitSet(QBit(1323)) then -- NPC
            evt.OpenChest(2)
            SetQBit(QBit(1323)) -- NPC
            SetValue(MapVar(2), 1)
            return
        end
        evt.OpenChest(9)
    end
    evt.OpenChest(2)
    SetQBit(QBit(1323)) -- NPC
    SetValue(MapVar(2), 1)
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

RegisterEvent(46, "Legacy event 46", function()
    evt.MoveToMap(6383, 4644, 222, 315, 0, 0, 0, 0)
end)

RegisterEvent(49, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(50, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(58, "Door", function()
    evt.StatusText("The door won't budge")
end, "Door")

RegisterEvent(59, "Legacy event 59", function()
    SetValue(MapVar(9), 1)
    evt.SetDoorState(19, DoorAction.Close)
end)

RegisterEvent(60, "Legacy event 60", function()
    if IsAtLeast(MapVar(9), 1) then
        evt.SetDoorState(33, DoorAction.Close)
        evt.SetDoorState(34, DoorAction.Close)
    end
end)

RegisterEvent(61, "Legacy event 61", function()
    evt.MoveToMap(9111, 2540, 121, 512, 0, 0, 0, 0)
end)

RegisterEvent(62, "Legacy event 62", function()
    evt.ForPlayer(Players.All)
    if IsQBitSet(QBit(1128)) then -- CD3
        return
    elseif HasItem(2173) then -- Memory Crystal Epsilon
        return
    else
        evt.SetSprite(290, 1, "crysdisc")
        evt.ForPlayer(Players.Current)
        AddValue(InventoryItem(2173), 2173) -- Memory Crystal Epsilon
        SetQBit(QBit(1128)) -- CD3
        SetQBit(QBit(1218)) -- Quest item bits for seer
        return
    end
end)

RegisterEvent(63, "Legacy event 63", function()
    evt.ForPlayer(Players.All)
    if IsQBitSet(QBit(1128)) or HasItem(2173) then -- CD3
        evt.SetSprite(290, 1, "crysdisc")
    end
end)

