-- Superior Temple of Baa
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [27] = {1},
    [28] = {5},
    [29] = {6},
    [38] = {2},
    [39] = {3},
    [40] = {7, 8},
    [45] = {4},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {6, 15},
    timers = {
    },
})

RegisterEvent(1, "Door", function()
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(31, 0, 8) then
        evt.DamagePlayer(7, 0, 50)
        return
    end
    evt.SetDoorState(1, DoorAction.Close)
end, "Door")

RegisterEvent(2, "Door", function()
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(31, 0, 4) then
        evt.DamagePlayer(7, 0, 50)
        return
    end
    evt.SetDoorState(2, DoorAction.Close)
end, "Door")

RegisterEvent(3, "Door", function()
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(31, 0, 4) then
        evt.DamagePlayer(7, 0, 50)
        return
    end
    evt.SetDoorState(3, DoorAction.Close)
end, "Door")

RegisterEvent(4, "Door", function()
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(31, 0, 4) then
        evt.DamagePlayer(7, 0, 50)
        return
    end
    evt.SetDoorState(4, DoorAction.Close)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(31, 0, 4) then
        evt.DamagePlayer(7, 0, 50)
        return
    end
    evt.SetDoorState(5, DoorAction.Close)
end, "Door")

RegisterEvent(6, "Door", function()
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(31, 0, 4) then
        evt.DamagePlayer(7, 0, 50)
        return
    end
    evt.SetDoorState(6, DoorAction.Close)
end, "Door")

RegisterEvent(7, "Door", function()
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(31, 0, 4) then
        evt.DamagePlayer(7, 0, 50)
        return
    end
    evt.SetDoorState(7, DoorAction.Close)
end, "Door")

RegisterEvent(8, "Door", function()
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(31, 0, 4) then
        evt.DamagePlayer(7, 0, 50)
        return
    end
    evt.SetDoorState(8, DoorAction.Close)
end, "Door")

RegisterEvent(9, "Door", function()
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(31, 0, 4) then
        evt.DamagePlayer(7, 0, 50)
        return
    end
    evt.SetDoorState(9, DoorAction.Close)
end, "Door")

RegisterEvent(10, "Door", function()
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(31, 0, 4) then
        evt.DamagePlayer(7, 0, 50)
        return
    end
    evt.SetDoorState(10, DoorAction.Close)
end, "Door")

RegisterEvent(11, "Door", function()
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(31, 0, 4) then
        evt.DamagePlayer(7, 0, 50)
        return
    end
    evt.SetDoorState(11, DoorAction.Close)
end, "Door")

RegisterEvent(12, "Door", function()
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(31, 0, 4) then
        evt.DamagePlayer(7, 0, 50)
        return
    end
    evt.SetDoorState(12, DoorAction.Close)
end, "Door")

RegisterEvent(13, "Door", function()
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(31, 0, 4) then
        evt.DamagePlayer(7, 0, 50)
        return
    end
    evt.SetDoorState(13, DoorAction.Close)
end, "Door")

RegisterEvent(14, "Door", function()
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(31, 0, 4) then
        evt.DamagePlayer(7, 0, 50)
        return
    end
    evt.SetDoorState(14, DoorAction.Close)
end, "Door")

RegisterEvent(15, "Door", function()
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(31, 0, 4) then
        evt.DamagePlayer(7, 0, 50)
        return
    end
    evt.SetDoorState(15, DoorAction.Close)
end, "Door")

RegisterEvent(16, "Door", function()
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(31, 0, 4) then
        evt.DamagePlayer(7, 0, 50)
        return
    end
    evt.SetDoorState(16, DoorAction.Close)
end, "Door")

RegisterEvent(17, "Door", function()
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(31, 0, 4) then
        evt.DamagePlayer(7, 0, 50)
        return
    end
    evt.SetDoorState(17, DoorAction.Close)
end, "Door")

RegisterEvent(18, "Door", function()
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(31, 0, 4) then
        evt.DamagePlayer(7, 0, 50)
        return
    end
    evt.SetDoorState(18, DoorAction.Close)
end, "Door")

RegisterEvent(19, "Door", function()
    evt.SetDoorState(19, DoorAction.Close)
    if not IsAtLeast(MapVar(14), 1) then
        SetValue(MapVar(10), 1)
        return
    end
    SetValue(MapVar(16), 1)
end, "Door")

RegisterEvent(20, "Door", function()
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(31, 0, 4) then
        evt.DamagePlayer(7, 0, 50)
        return
    end
    evt.SetDoorState(20, DoorAction.Close)
end, "Door")

RegisterEvent(21, "Door", function()
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(31, 0, 4) then
        evt.DamagePlayer(7, 0, 50)
        return
    end
    evt.SetDoorState(21, DoorAction.Close)
end, "Door")

RegisterEvent(27, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(28, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(29, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(34, "Baa Head Two", nil, "Baa Head Two")

RegisterEvent(36, "Podium", function()
    evt.SimpleMessage("\"Expert Perception is the key and the doors of Baa will let you be.                                                                                                                                                                                                                  The Spiral then each head, talk to Baa or you'll be dead.\"")
end, "Podium")

RegisterEvent(38, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(39, "Chest", function()
    if not evt.CheckSkill(31, 0, 2) then
        evt.DamagePlayer(7, 0, 200)
        return
    end
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(40, "Chest", function()
    if not IsAtLeast(MapVar(21), 1) then
        evt.ForPlayer(Players.All)
        if not HasItem(2187) then -- High Cleric's Key
            evt.StatusText("Chest Is locked.")
            if IsAtLeast(MapVar(12), 1) then return end
            SetValue(MapVar(12), 1)
            evt.SummonMonsters(2, 2, 2, -2240, -3168, 0, 0, 0) -- encounter slot 2 "Druidess" tier B, count 2, pos=(-2240, -3168, 0), actor group 0, no unique actor name
            evt.SummonMonsters(2, 2, 2, -320, -3232, 0, 0, 0) -- encounter slot 2 "Druidess" tier B, count 2, pos=(-320, -3232, 0), actor group 0, no unique actor name
            return
        end
        if not HasItem(2112) then -- High Sorcerer's Key
            evt.StatusText("Chest Is locked.")
            if IsAtLeast(MapVar(12), 1) then return end
            SetValue(MapVar(12), 1)
            evt.SummonMonsters(2, 2, 2, -2240, -3168, 0, 0, 0) -- encounter slot 2 "Druidess" tier B, count 2, pos=(-2240, -3168, 0), actor group 0, no unique actor name
            evt.SummonMonsters(2, 2, 2, -320, -3232, 0, 0, 0) -- encounter slot 2 "Druidess" tier B, count 2, pos=(-320, -3232, 0), actor group 0, no unique actor name
            return
        end
        if not IsQBitSet(QBit(1032)) then -- 8 T7, given when you find the smoking gun
            SetValue(MapVar(21), 1)
            evt.OpenChest(7)
            RemoveItem(2187) -- High Cleric's Key
            RemoveItem(2112) -- High Sorcerer's Key
            SetQBit(QBit(1032)) -- 8 T7, given when you find the smoking gun
            SetQBit(QBit(1214)) -- Quest item bits for seer
            return
        end
        evt.OpenChest(8)
    end
    evt.OpenChest(7)
    RemoveItem(2187) -- High Cleric's Key
    RemoveItem(2112) -- High Sorcerer's Key
    SetQBit(QBit(1032)) -- 8 T7, given when you find the smoking gun
    SetQBit(QBit(1214)) -- Quest item bits for seer
end, "Chest")

RegisterEvent(42, "Book Case", function()
    if IsAtLeast(MapVar(6), 1) then return end
    SetValue(MapVar(6), 1)
    AddValue(InventoryItem(2006), 2006) -- Reanimate
end, "Book Case")

RegisterEvent(45, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(60, "Legacy event 60", function()
    evt.MoveToMap(17078, -6601, 161, 1280, 0, 0, 0, 0, "outb1.odm")
end)

RegisterEvent(61, "Legacy event 61", function()
    evt.CastSpell(15, 3, 3, -6272, 6272, 250, -6272, 6272, 100) -- Sparks
end)

RegisterEvent(62, "Legacy event 62", function()
    evt.CastSpell(15, 3, 3, -6272, 6272, 250, -6272, 6272, 100) -- Sparks
    evt.CastSpell(15, 3, 3, -9984, 5792, -50, 0, 0, 0) -- Sparks
end)

RegisterEvent(63, "Legacy event 63", function()
    evt.CastSpell(15, 3, 3, -8768, 6176, -50, 0, 0, 0) -- Sparks
    evt.CastSpell(15, 3, 3, -11552, 3904, -50, 0, 0, 0) -- Sparks
end)

RegisterEvent(64, "Legacy event 64", function()
    evt.CastSpell(6, 5, 3, -11552, -3648, -125, -11712, 2656, -126) -- Fireball
end)

RegisterEvent(65, "Legacy event 65", function()
    evt.CastSpell(15, 3, 3, -11488, -3616, -50, 0, 0, 0) -- Sparks
    evt.CastSpell(15, 3, 3, -11904, -7360, -50, 0, 0, 0) -- Sparks
end)

RegisterEvent(66, "Legacy event 66", function()
    evt.CastSpell(15, 3, 3, -11680, -6140, -20, 0, 0, 0) -- Sparks
    evt.CastSpell(15, 3, 3, -11776, -9824, -400, 0, 0, 0) -- Sparks
end)

RegisterEvent(67, "Legacy event 67", function()
    evt.CastSpell(15, 3, 3, -10560, -11872, -520, 0, 0, 0) -- Sparks
    evt.CastSpell(15, 3, 3, -8160, -11424, -540, 0, 0, 0) -- Sparks
end)

RegisterEvent(68, "Legacy event 68", function()
    evt.CastSpell(15, 3, 3, -7744, -8320, -100, 0, 0, 0) -- Sparks
    evt.CastSpell(15, 3, 3, -10496, -9760, 200, 0, 0, 0) -- Sparks
end)

RegisterEvent(69, "Legacy event 69", function()
    evt.CastSpell(15, 3, 3, -8800, -12864, 250, 0, 0, 0) -- Sparks
    evt.CastSpell(15, 3, 3, -5504, -11520, 220, 0, 0, 0) -- Sparks
end)

RegisterEvent(70, "Legacy event 70", function()
    evt.CastSpell(15, 3, 3, -5344, -10240, 250, 0, 0, 0) -- Sparks
    evt.CastSpell(15, 3, 3, -7232, -7008, 230, 0, 0, 0) -- Sparks
end)

RegisterEvent(71, "Baa Head One", function()
    evt.StatusText("Baa One here.")
    if IsAtLeast(MapVar(11), 1) then return end
    SetValue(MapVar(11), 1)
end, "Baa Head One")

RegisterEvent(72, "Baa Head Two", function()
    if not IsAtLeast(MapVar(11), 1) then
        evt.DamagePlayer(7, 0, 20)
        evt.StatusText("Baa!  Baa!")
        return
    end
    evt.StatusText("Baa Two ready.")
    SetValue(MapVar(12), 1)
end, "Baa Head Two")

RegisterEvent(73, "Baa Head Three", function()
    if not IsAtLeast(MapVar(12), 1) then
        evt.DamagePlayer(7, 0, 20)
        evt.StatusText("Baa!  Baa!")
        return
    end
    evt.StatusText("Baa Three standing by.")
    SetValue(MapVar(13), 1)
end, "Baa Head Three")

RegisterEvent(74, "Baa Head Four", function()
    if not IsAtLeast(MapVar(13), 1) then
        evt.DamagePlayer(7, 0, 20)
        evt.StatusText("Baa!  Baa!")
        return
    end
    evt.StatusText("Baa Four is a go.")
    SetValue(MapVar(14), 1)
    if IsAtLeast(MapVar(10), 1) then
        SetValue(MapVar(16), 1)
    end
end, "Baa Head Four")

RegisterEvent(75, "Almighty Head of Baa.", function()
    if not IsAtLeast(MapVar(16), 1) then
        evt.StatusText("You're not worthy of Baa!")
        evt.DamagePlayer(7, 0, 100)
        return
    end
    if not IsPlayerBitSet(PlayerBit(69)) then
        evt.StatusText("\"Follow Baa!  +50,000 Experience.\"")
        AddValue(Experience, 50000)
        SubtractValue(1638635, 25)
        SetPlayerBit(PlayerBit(69))
        return
    end
    evt.StatusText("Go forth and spread the word of Baa!")
end, "Almighty Head of Baa.")

RegisterEvent(76, "Lava pool", function()
    evt.DamagePlayer(5, 5, 30)
end, "Lava pool")

