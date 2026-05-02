-- Temple of Baa
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {70},
    onLeave = {},
    openedChestIds = {
    [23] = {0, 0},
    [27] = {1},
    [28] = {2},
    [29] = {3},
    [30] = {4},
    [31] = {5},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {6, 63},
    timers = {
    { eventId = 51, repeating = true, intervalGameMinutes = 2.5, remainingGameMinutes = 2.5 },
    },
})

RegisterEvent(1, "Door", function()
    evt.ForPlayer(Players.All)
    if not HasItem(2178) then -- Secret Door Key
        evt.StatusText("The door is locked.")
        return
    end
    evt.ForPlayer(Players.All)
    RemoveItem(2178) -- Secret Door Key
    evt.SetDoorState(1, DoorAction.Close)
end, "Door")

RegisterEvent(2, "Door", function()
    evt.ForPlayer(Players.All)
    if not HasItem(2177) then -- Treasure Room Key
        evt.StatusText("The door is locked.")
        return
    end
    evt.SetDoorState(2, DoorAction.Close)
    evt.ForPlayer(Players.All)
    RemoveItem(2177) -- Treasure Room Key
end, "Door")

RegisterEvent(3, "Door", function()
    evt.ForPlayer(Players.All)
    if not HasItem(2183) then -- Treasure Room Key
        evt.StatusText("The door is locked.")
        return
    end
    evt.SetDoorState(3, DoorAction.Close)
    evt.ForPlayer(Players.All)
    RemoveItem(2183) -- Treasure Room Key
end, "Door")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(4, DoorAction.Close)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.ForPlayer(Players.All)
    if not HasItem(2176) then -- Store Room Key
        evt.StatusText("The door is locked.")
        return
    end
    evt.SetDoorState(5, DoorAction.Close)
    evt.ForPlayer(Players.All)
    RemoveItem(2176) -- Store Room Key
    evt.SummonMonsters(3, 3, 2, -9956, -2760, -255, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 2, pos=(-9956, -2760, -255), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 2, -9956, -2908, -255, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 2, pos=(-9956, -2908, -255), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 2, -9956, -3108, -255, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 2, pos=(-9956, -3108, -255), actor group 0, no unique actor name
    evt.SummonMonsters(1, 1, 1, -9866, -2606, -255, 0, 0) -- encounter slot 1 "Cleric" tier A, count 1, pos=(-9866, -2606, -255), actor group 0, no unique actor name
    evt.SummonMonsters(1, 1, 1, -10102, -2606, -255, 0, 0) -- encounter slot 1 "Cleric" tier A, count 1, pos=(-10102, -2606, -255), actor group 0, no unique actor name
end, "Door")

RegisterEvent(6, "Door", function()
    evt.ForPlayer(Players.All)
    if not HasItem(2182) then -- Store Room Key
        evt.StatusText("The door is locked.")
        return
    end
    evt.SetDoorState(6, DoorAction.Close)
    evt.ForPlayer(Players.All)
    RemoveItem(2182) -- Store Room Key
    evt.SummonMonsters(3, 3, 2, -9956, -2760, -255, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 2, pos=(-9956, -2760, -255), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 2, -9956, -2908, -255, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 2, pos=(-9956, -2908, -255), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 2, -9956, -3108, -255, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 2, pos=(-9956, -3108, -255), actor group 0, no unique actor name
    evt.SummonMonsters(1, 1, 1, -9866, -2606, -255, 0, 0) -- encounter slot 1 "Cleric" tier A, count 1, pos=(-9866, -2606, -255), actor group 0, no unique actor name
    evt.SummonMonsters(1, 1, 1, -10102, -2606, -255, 0, 0) -- encounter slot 1 "Cleric" tier A, count 1, pos=(-10102, -2606, -255), actor group 0, no unique actor name
end, "Door")

RegisterEvent(7, "Door", function()
    evt.SetDoorState(7, DoorAction.Close)
end, "Door")

RegisterEvent(8, "Door", function()
    evt.SetDoorState(8, DoorAction.Close)
end, "Door")

RegisterEvent(9, "Door", function()
    evt.ForPlayer(Players.All)
    if not HasItem(2175) then -- Bathhouse Key
        evt.StatusText("The door is locked.")
        return
    end
    evt.SetDoorState(9, DoorAction.Close)
    evt.ForPlayer(Players.All)
    RemoveItem(2175) -- Bathhouse Key
    evt.SummonMonsters(3, 3, 2, -9986, 3669, -255, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 2, pos=(-9986, 3669, -255), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 2, -9986, 3741, -255, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 2, pos=(-9986, 3741, -255), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 2, -9986, 3870, -255, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 2, pos=(-9986, 3870, -255), actor group 0, no unique actor name
    evt.SummonMonsters(1, 1, 1, -9986, 2537, -255, 0, 0) -- encounter slot 1 "Cleric" tier A, count 1, pos=(-9986, 2537, -255), actor group 0, no unique actor name
    evt.SummonMonsters(1, 1, 1, -9986, 3603, -255, 0, 0) -- encounter slot 1 "Cleric" tier A, count 1, pos=(-9986, 3603, -255), actor group 0, no unique actor name
end, "Door")

RegisterEvent(10, "Door", function()
    evt.ForPlayer(Players.All)
    if not HasItem(2181) then -- Bathhouse Key
        evt.StatusText("The door is locked.")
        return
    end
    evt.SetDoorState(10, DoorAction.Close)
    evt.ForPlayer(Players.All)
    RemoveItem(2181) -- Bathhouse Key
    evt.SummonMonsters(3, 3, 2, -9986, 3669, -255, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 2, pos=(-9986, 3669, -255), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 2, -9986, 3741, -255, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 2, pos=(-9986, 3741, -255), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 2, -9986, 3870, -255, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 2, pos=(-9986, 3870, -255), actor group 0, no unique actor name
    evt.SummonMonsters(1, 1, 1, -9986, 2537, -255, 0, 0) -- encounter slot 1 "Cleric" tier A, count 1, pos=(-9986, 2537, -255), actor group 0, no unique actor name
    evt.SummonMonsters(1, 1, 1, -9986, 3603, -255, 0, 0) -- encounter slot 1 "Cleric" tier A, count 1, pos=(-9986, 3603, -255), actor group 0, no unique actor name
end, "Door")

RegisterEvent(11, "Door", function()
    evt.SetDoorState(11, DoorAction.Close)
    evt.SetDoorState(12, DoorAction.Close)
end, "Door")

RegisterEvent(12, "Sign", function()
    evt.SimpleMessage("\"A silver sign reads: As the winds blow, the seasons change, and only at the end of all can the doors be opened.\"")
end, "Sign")

RegisterEvent(14, "Sign", function()
    evt.SimpleMessage("\"A copper sign reads: As the winds blow, the seasons change, and only at the end of all can the doors be opened.\"")
end, "Sign")

RegisterEvent(15, "Door", function()
    evt.SetDoorState(15, DoorAction.Close)
    evt.SetDoorState(16, DoorAction.Close)
end, "Door")

RegisterEvent(16, "Sign", function()
    evt.SimpleMessage("\"A lapis sign reads: As the winds blow, the seasons change, and only at the end of all can the doors be opened.\"")
end, "Sign")

RegisterEvent(17, "Door", function()
    evt.SetDoorState(17, DoorAction.Close)
    evt.SetDoorState(18, DoorAction.Close)
end, "Door")

RegisterEvent(18, "Door", function()
    evt.SetDoorState(18, DoorAction.Close)
end, "Door")

RegisterEvent(19, "Door", function()
    if IsAtLeast(MapVar(4), 1) then
        AddValue(MapVar(5), 1)
        if not IsAtLeast(MapVar(5), 2) then
            evt.StatusText("The door clicks.")
            return
        end
        SetValue(MapVar(5), 1)
    end
    evt.DamagePlayer(5, 0, 10)
    SetValue(MapVar(4), 0)
    SetValue(MapVar(5), 0)
    SetValue(MapVar(6), 0)
    SetValue(MapVar(10), 0)
    evt.StatusText("Zap!")
end, "Door")

RegisterEvent(20, "Door", function()
    if IsAtLeast(MapVar(6), 1) then
        AddValue(MapVar(10), 1)
        if IsAtLeast(MapVar(10), 2) then
            SetValue(MapVar(10), 1)
            evt.DamagePlayer(5, 0, 10)
            evt.StatusText("Zap!")
            return
        elseif IsAtLeast(MapVar(4), 1) then
            if not IsAtLeast(MapVar(5), 1) then return end
            if IsAtLeast(MapVar(6), 1) then
                evt.SetDoorState(20, DoorAction.Close)
                evt.SetDoorState(19, DoorAction.Close)
                evt.SetDoorState(21, DoorAction.Close)
                evt.SetDoorState(22, DoorAction.Close)
                SetValue(MapVar(4), 0)
                SetValue(MapVar(5), 0)
                SetValue(MapVar(6), 0)
                SetValue(MapVar(10), 0)
            end
            return
        else
            return
        end
    end
    evt.DamagePlayer(5, 0, 10)
    evt.StatusText("Zap!")
end, "Door")

RegisterEvent(21, "Door", function()
    if IsAtLeast(MapVar(5), 1) then
        AddValue(MapVar(6), 1)
        if not IsAtLeast(MapVar(6), 2) then
            evt.StatusText("The door clicks.")
            return
        end
        SetValue(MapVar(5), 1)
    end
    evt.DamagePlayer(5, 0, 10)
    SetValue(MapVar(4), 0)
    SetValue(MapVar(5), 0)
    SetValue(MapVar(6), 0)
    SetValue(MapVar(10), 0)
    evt.StatusText("Zap!")
end, "Door")

RegisterEvent(22, "Door", function()
    AddValue(MapVar(4), 1)
    if not IsAtLeast(MapVar(4), 2) then
        evt.StatusText("The door clicks.")
        return
    end
    SetValue(MapVar(4), 1)
    evt.DamagePlayer(5, 0, 10)
    evt.StatusText("Zap!")
end, "Door")

RegisterEvent(23, "Chest", function()
    if not IsAtLeast(MapVar(21), 1) then
        evt.OpenChest(0)
        SetValue(MapVar(21), 1)
        evt.SummonMonsters(3, 3, 2, -9986, 1295, -255, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 2, pos=(-9986, 1295, -255), actor group 0, no unique actor name
        evt.SummonMonsters(3, 2, 2, -10224, 1295, -255, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 2, pos=(-10224, 1295, -255), actor group 0, no unique actor name
        evt.SummonMonsters(3, 1, 2, -9716, 1295, -255, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 2, pos=(-9716, 1295, -255), actor group 0, no unique actor name
        evt.SummonMonsters(1, 1, 1, -9688, 1678, -255, 0, 0) -- encounter slot 1 "Cleric" tier A, count 1, pos=(-9688, 1678, -255), actor group 0, no unique actor name
        evt.SummonMonsters(1, 1, 1, -10273, 1678, -255, 0, 0) -- encounter slot 1 "Cleric" tier A, count 1, pos=(-10273, 1678, -255), actor group 0, no unique actor name
        evt.SummonMonsters(3, 3, 2, -8716, 101, -255, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 2, pos=(-8716, 101, -255), actor group 0, no unique actor name
        evt.SummonMonsters(3, 2, 2, -8716, 405, -255, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 2, pos=(-8716, 405, -255), actor group 0, no unique actor name
        evt.SummonMonsters(3, 1, 2, -8716, -117, -255, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 2, pos=(-8716, -117, -255), actor group 0, no unique actor name
        evt.SummonMonsters(1, 1, 1, -8261, -227, -255, 0, 0) -- encounter slot 1 "Cleric" tier A, count 1, pos=(-8261, -227, -255), actor group 0, no unique actor name
        evt.SummonMonsters(1, 1, 1, -8261, 453, -255, 0, 0) -- encounter slot 1 "Cleric" tier A, count 1, pos=(-8261, 453, -255), actor group 0, no unique actor name
        evt.SummonMonsters(3, 3, 2, -10009, -1039, -255, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 2, pos=(-10009, -1039, -255), actor group 0, no unique actor name
        evt.SummonMonsters(3, 2, 2, -9713, -1039, -255, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 2, pos=(-9713, -1039, -255), actor group 0, no unique actor name
        evt.SummonMonsters(3, 1, 2, -10272, -1039, -255, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 2, pos=(-10272, -1039, -255), actor group 0, no unique actor name
        evt.SummonMonsters(1, 1, 1, -10281, -1402, -255, 0, 0) -- encounter slot 1 "Cleric" tier A, count 1, pos=(-10281, -1402, -255), actor group 0, no unique actor name
        evt.SummonMonsters(1, 1, 1, -9716, -1402, -255, 0, 0) -- encounter slot 1 "Cleric" tier A, count 1, pos=(-9716, -1402, -255), actor group 0, no unique actor name
        evt.SummonMonsters(3, 3, 2, -11291, 138, -255, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 2, pos=(-11291, 138, -255), actor group 0, no unique actor name
        evt.SummonMonsters(3, 2, 2, -11291, -93, -255, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 2, pos=(-11291, -93, -255), actor group 0, no unique actor name
        evt.SummonMonsters(3, 1, 2, -11291, 454, -255, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 2, pos=(-11291, 454, -255), actor group 0, no unique actor name
        evt.SummonMonsters(1, 1, 1, -11675, 454, -255, 0, 0) -- encounter slot 1 "Cleric" tier A, count 1, pos=(-11675, 454, -255), actor group 0, no unique actor name
        evt.SummonMonsters(1, 1, 1, -11675, -139, -255, 0, 0) -- encounter slot 1 "Cleric" tier A, count 1, pos=(-11675, -139, -255), actor group 0, no unique actor name
        return
    end
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(24, "Sign", function()
    evt.SimpleMessage("\"A wooden sign reads: As the winds blow, the seasons change, and only at the end of all can the doors be opened.\"")
end, "Sign")

RegisterEvent(26, "Legacy event 26", function()
    evt.ForPlayer(Players.All)
    if IsAtLeast(ThieverySkill, 1) then
        return
    elseif IsAtLeast(Asleep, 1) then
        return
    else
        evt.CastSpell(63, 10, 1, 0, 0, 0, 0, 0, 0) -- Mass Fear
        evt.StatusText("The haunted sounds of tortured souls assail your ears.")
        return
    end
end)

RegisterEvent(27, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(28, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(29, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(30, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(31, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(32, "Statue", function()
    if IsAtLeast(MapVar(12), 1) then return end
    AddValue(InventoryItem(2176), 2176) -- Store Room Key
    evt.StatusText("Found something!")
    SetValue(MapVar(12), 1)
end, "Statue")

RegisterEvent(34, "Fountain", function()
    if not IsAtLeast(MapVar(16), 1) then
        evt.StatusText("Refreshing.")
        return
    end
    SubtractValue(MapVar(16), 1)
    AddValue(CurrentHealth, 20)
    evt.StatusText(" +20 Hit points restored.")
end, "Fountain")

RegisterEvent(50, "Exit", function()
    evt.MoveToMap(4885, -7698, 96, 1536, 0, 0, 0, 0, "outd3.odm")
end, "Exit")

RegisterEvent(51, "Legacy event 51", function()
    evt.CastSpell(6, 4, 1, -1590, 133, -100, -2200, 133, -100) -- Fireball
end)

RegisterEvent(52, "Legacy event 52", function()
    if IsAtLeast(MapVar(31), 1) then return end
    evt.PlaySound(42682, 0, 0)
    evt.SummonMonsters(3, 3, 1, 3702, 3216, 577, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 1, pos=(3702, 3216, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 3702, 2572, 577, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 1, pos=(3702, 2572, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 3702, 1929, 577, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 1, pos=(3702, 1929, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 3702, 1286, 577, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 1, pos=(3702, 1286, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 3702, 643, 577, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 1, pos=(3702, 643, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 3702, 0, 577, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 1, pos=(3702, 0, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 3702, -643, 577, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 1, pos=(3702, -643, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 3702, -1286, 577, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 1, pos=(3702, -1286, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 3702, -1929, 577, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 1, pos=(3702, -1929, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 3702, -2572, 577, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 1, pos=(3702, -2572, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 3326, 3216, 577, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 1, pos=(3326, 3216, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 3326, 2572, 577, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 1, pos=(3326, 2572, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 3326, 1929, 577, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 1, pos=(3326, 1929, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 3326, 1286, 577, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 1, pos=(3326, 1286, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 3326, 643, 577, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 1, pos=(3326, 643, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 3326, 0, 577, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 1, pos=(3326, 0, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 3326, -643, 577, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 1, pos=(3326, -643, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 3326, -1286, 577, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 1, pos=(3326, -1286, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 3326, -1929, 577, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 1, pos=(3326, -1929, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 3326, -2572, 577, 0, 0) -- encounter slot 3 "Skeleton" tier C, count 1, pos=(3326, -2572, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 2950, 3216, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(2950, 3216, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 2950, 2572, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(2950, 2572, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 2950, 1929, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(2950, 1929, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 2950, 1286, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(2950, 1286, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 2950, 643, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(2950, 643, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 2950, 0, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(2950, 0, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 2950, -643, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(2950, -643, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 2950, -1286, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(2950, -1286, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 2950, -1929, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(2950, -1929, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 2950, -2572, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(2950, -2572, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 2400, 3216, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(2400, 3216, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 2400, 2572, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(2400, 2572, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 2400, 1929, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(2400, 1929, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 2400, 1286, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(2400, 1286, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 2400, 643, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(2400, 643, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 2400, 0, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(2400, 0, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 2400, -643, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(2400, -643, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 2400, -1286, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(2400, -1286, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 2400, -1929, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(2400, -1929, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 2400, -2572, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(2400, -2572, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 1985, 3216, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(1985, 3216, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 1985, 2572, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(1985, 2572, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 1985, 1929, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(1985, 1929, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 1985, 1286, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(1985, 1286, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 1985, 643, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(1985, 643, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 1985, 0, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(1985, 0, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 1985, -643, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(1985, -643, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 1985, -1286, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(1985, -1286, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 1985, -1929, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(1985, -1929, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 1985, -2572, 577, 0, 0) -- encounter slot 3 "Skeleton" tier B, count 1, pos=(1985, -2572, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 1476, 3216, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(1476, 3216, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 1476, 2572, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(1476, 2572, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 1476, 1929, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(1476, 1929, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 1476, 1286, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(1476, 1286, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 1476, 643, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(1476, 643, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 1476, 0, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(1476, 0, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 1476, -643, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(1476, -643, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 1476, -1286, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(1476, -1286, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 1476, -1929, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(1476, -1929, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 1476, -2572, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(1476, -2572, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 810, 3216, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(810, 3216, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 810, 2572, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(810, 2572, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 810, 1929, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(810, 1929, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 810, 1286, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(810, 1286, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 810, 643, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(810, 643, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 810, 0, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(810, 0, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 810, -643, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(810, -643, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 810, -1286, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(810, -1286, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 810, -1929, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(810, -1929, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 810, -2572, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(810, -2572, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 440, 3216, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(440, 3216, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 440, 2572, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(440, 2572, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 440, 1929, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(440, 1929, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 440, 1286, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(440, 1286, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 440, 643, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(440, 643, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 440, 0, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(440, 0, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 440, -643, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(440, -643, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 440, -1286, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(440, -1286, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 440, -1929, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(440, -1929, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 440, -2572, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(440, -2572, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 0, 3216, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(0, 3216, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 0, 2572, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(0, 2572, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 0, 1929, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(0, 1929, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 0, 1286, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(0, 1286, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 0, 643, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(0, 643, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 0, 0, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(0, 0, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 0, -643, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(0, -643, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 0, -1286, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(0, -1286, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 0, -1929, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(0, -1929, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 0, -2572, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(0, -2572, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, -650, 3216, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(-650, 3216, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, -650, 2572, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(-650, 2572, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, -650, 1929, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(-650, 1929, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, -650, 1286, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(-650, 1286, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, -650, 643, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(-650, 643, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, -650, 0, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(-650, 0, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, -650, -643, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(-650, -643, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, -650, -1286, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(-650, -1286, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, -650, -1929, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(-650, -1929, 577), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, -650, -2572, 577, 0, 0) -- encounter slot 3 "Skeleton" tier A, count 1, pos=(-650, -2572, 577), actor group 0, no unique actor name
    SetValue(MapVar(31), 1)
end)

RegisterEvent(53, "Legacy event 53", function()
    if IsAtLeast(MapVar(26), 1) then return end
    AddValue(Gold, 5000)
    SetValue(MapVar(26), 1)
end)

RegisterEvent(70, "Legacy event 70", function()
    SetValue(MapVar(4), 0)
    SetValue(MapVar(5), 0)
    SetValue(MapVar(6), 0)
    SetValue(MapVar(10), 0)
end)

