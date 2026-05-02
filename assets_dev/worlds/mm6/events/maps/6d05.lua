-- Snergle's Caverns
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {35},
    onLeave = {},
    openedChestIds = {
    [8] = {0},
    },
    textureNames = {"t3ll6"},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(3, "Switch", function()
    evt.SetDoorState(3, DoorAction.Trigger)
    evt.SetDoorState(2, DoorAction.Trigger)
end, "Switch")

RegisterEvent(4, "Glowing dinosaur bones", function()
    evt.MoveToMap(1576, -1921, 1, 44, 0, 0, 0, 0)
end, "Glowing dinosaur bones")

RegisterEvent(6, "Lever", function()
    evt.SetDoorState(6, DoorAction.Trigger)
    evt.SetDoorState(5, DoorAction.Trigger)
end, "Lever")

RegisterEvent(7, "Legacy event 7", function()
    evt.SetDoorState(7, DoorAction.Trigger)
end)

RegisterEvent(8, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(9, "Door", function()
    if not IsQBitSet(QBit(1051)) then -- 27 D05, Given when axe is returned (so door can't be opened)
        if not HasItem(2108) then -- Key to Snergle's Chambers
            evt.StatusText("The door is locked")
            return
        end
        evt.SetDoorState(9, DoorAction.Close)
        RemoveItem(2108) -- Key to Snergle's Chambers
        evt.SummonMonsters(1, 2, 3, 387, 8721, 257, 0, 0) -- encounter slot 1 "BDwarf" tier B, count 3, pos=(387, 8721, 257), actor group 0, no unique actor name
        evt.SummonMonsters(1, 3, 3, 420, 8538, 257, 0, 0) -- encounter slot 1 "BDwarf" tier C, count 3, pos=(420, 8538, 257), actor group 0, no unique actor name
        evt.SummonMonsters(1, 2, 3, 44, 8517, 247, 0, 0) -- encounter slot 1 "BDwarf" tier B, count 3, pos=(44, 8517, 247), actor group 0, no unique actor name
        evt.SummonMonsters(1, 3, 3, -208, 8507, 257, 0, 0) -- encounter slot 1 "BDwarf" tier C, count 3, pos=(-208, 8507, 257), actor group 0, no unique actor name
        evt.SummonMonsters(1, 2, 3, -455, 8588, 247, 0, 0) -- encounter slot 1 "BDwarf" tier B, count 3, pos=(-455, 8588, 247), actor group 0, no unique actor name
        evt.SummonMonsters(1, 3, 3, -556, 8573, 257, 0, 0) -- encounter slot 1 "BDwarf" tier C, count 3, pos=(-556, 8573, 257), actor group 0, no unique actor name
        return
    end
    evt.StatusText("The door is locked")
end, "Door")

RegisterEvent(10, "Gold vein", function()
    if IsAtLeast(MapVar(13), 1) then return end
    local randomStep = PickRandomOption(10, 2, {15, 20, 15, 11, 7, 3})
    if randomStep == 15 then
        evt.DamagePlayer(5, 4, 20)
        evt.StatusText("Cave-in!")
        evt.SetTexture(204, "t3ll6")
        SetValue(MapVar(13), 1)
        return
    elseif randomStep == 20 then
        evt.DamagePlayer(5, 4, 20)
        AddValue(Gold, 1000)
        evt.StatusText("Cave-in!")
        evt.SetTexture(204, "t3ll6")
        SetValue(MapVar(13), 1)
        return
    elseif randomStep == 11 then
        AddValue(Gold, 800)
        evt.SetTexture(204, "t3ll6")
        SetValue(MapVar(13), 1)
        return
    elseif randomStep == 7 then
        AddValue(Gold, 600)
        evt.SetTexture(204, "t3ll6")
        SetValue(MapVar(13), 1)
        return
    elseif randomStep == 3 then
        AddValue(Gold, 400)
        evt.SetTexture(204, "t3ll6")
        SetValue(MapVar(13), 1)
        return
    end
end, "Gold vein")

RegisterEvent(11, "Gold vein", function()
    if IsAtLeast(MapVar(14), 1) then return end
    local randomStep = PickRandomOption(11, 2, {15, 20, 15, 11, 7, 3})
    if randomStep == 15 then
        evt.DamagePlayer(5, 4, 20)
        evt.StatusText("Cave-in!")
        evt.SetTexture(207, "t3ll6")
        SetValue(MapVar(14), 1)
        return
    elseif randomStep == 20 then
        evt.DamagePlayer(5, 4, 20)
        AddValue(Gold, 1000)
        evt.StatusText("Cave-in!")
        evt.SetTexture(207, "t3ll6")
        SetValue(MapVar(14), 1)
        return
    elseif randomStep == 11 then
        AddValue(Gold, 800)
        evt.SetTexture(207, "t3ll6")
        SetValue(MapVar(14), 1)
        return
    elseif randomStep == 7 then
        AddValue(Gold, 600)
        evt.SetTexture(207, "t3ll6")
        SetValue(MapVar(14), 1)
        return
    elseif randomStep == 3 then
        AddValue(Gold, 400)
        evt.SetTexture(207, "t3ll6")
        SetValue(MapVar(14), 1)
        return
    end
end, "Gold vein")

RegisterEvent(12, "Gold vein", function()
    if IsAtLeast(MapVar(15), 1) then return end
    local randomStep = PickRandomOption(12, 2, {15, 20, 15, 11, 7, 3})
    if randomStep == 15 then
        evt.DamagePlayer(5, 4, 20)
        evt.StatusText("Cave-in!")
        evt.SetTexture(12, "t3ll6")
        SetValue(MapVar(15), 1)
        return
    elseif randomStep == 20 then
        evt.DamagePlayer(5, 4, 20)
        AddValue(Gold, 1000)
        evt.StatusText("Cave-in!")
        evt.SetTexture(12, "t3ll6")
        SetValue(MapVar(15), 1)
        return
    elseif randomStep == 11 then
        AddValue(Gold, 800)
        evt.SetTexture(12, "t3ll6")
        SetValue(MapVar(15), 1)
        return
    elseif randomStep == 7 then
        AddValue(Gold, 600)
        evt.SetTexture(12, "t3ll6")
        SetValue(MapVar(15), 1)
        return
    elseif randomStep == 3 then
        AddValue(Gold, 400)
        evt.SetTexture(12, "t3ll6")
        SetValue(MapVar(15), 1)
        return
    end
end, "Gold vein")

RegisterEvent(13, "Gold vein", function()
    if IsAtLeast(MapVar(16), 1) then return end
    local randomStep = PickRandomOption(13, 2, {15, 20, 15, 11, 7, 3})
    if randomStep == 15 then
        evt.DamagePlayer(5, 4, 20)
        evt.StatusText("Cave-in!")
        evt.SetTexture(624, "t3ll6")
        SetValue(MapVar(16), 1)
        return
    elseif randomStep == 20 then
        evt.DamagePlayer(5, 4, 20)
        AddValue(Gold, 1000)
        evt.StatusText("Cave-in!")
        evt.SetTexture(624, "t3ll6")
        SetValue(MapVar(16), 1)
        return
    elseif randomStep == 11 then
        AddValue(Gold, 800)
        evt.SetTexture(624, "t3ll6")
        SetValue(MapVar(16), 1)
        return
    elseif randomStep == 7 then
        AddValue(Gold, 600)
        evt.SetTexture(624, "t3ll6")
        SetValue(MapVar(16), 1)
        return
    elseif randomStep == 3 then
        AddValue(Gold, 400)
        evt.SetTexture(624, "t3ll6")
        SetValue(MapVar(16), 1)
        return
    end
end, "Gold vein")

RegisterEvent(14, "Gold vein", function()
    if IsAtLeast(MapVar(17), 1) then return end
    local randomStep = PickRandomOption(14, 2, {15, 20, 15, 11, 7, 3})
    if randomStep == 15 then
        evt.DamagePlayer(5, 4, 20)
        evt.StatusText("Cave-in!")
        evt.SetTexture(612, "t3ll6")
        SetValue(MapVar(17), 1)
        return
    elseif randomStep == 20 then
        evt.DamagePlayer(5, 4, 20)
        AddValue(Gold, 1000)
        evt.StatusText("Cave-in!")
        evt.SetTexture(612, "t3ll6")
        SetValue(MapVar(17), 1)
        return
    elseif randomStep == 11 then
        AddValue(Gold, 800)
        evt.SetTexture(612, "t3ll6")
        SetValue(MapVar(17), 1)
        return
    elseif randomStep == 7 then
        AddValue(Gold, 600)
        evt.SetTexture(612, "t3ll6")
        SetValue(MapVar(17), 1)
        return
    elseif randomStep == 3 then
        AddValue(Gold, 400)
        evt.SetTexture(612, "t3ll6")
        SetValue(MapVar(17), 1)
        return
    end
end, "Gold vein")

RegisterEvent(21, "Black liquid filled barrel", function()
    AddValue(Paralyzed, 3)
end, "Black liquid filled barrel")

RegisterEvent(22, "Black liquid filled barrel", function()
    AddValue(Paralyzed, 3)
end, "Black liquid filled barrel")

RegisterEvent(23, "Black liquid filled barrel", function()
    AddValue(PoisonedRed, 3)
end, "Black liquid filled barrel")

RegisterEvent(25, "Glowing dinosaur bones", function()
    if not IsAtLeast(MapVar(9), 1) then
        if not IsAtLeast(BaseMight, 40) then
            AddValue(MapVar(9), 1)
            AddValue(BaseMight, 5)
            evt.StatusText("The bones feel weird (+5 Might permanent)")
            evt.FaceExpression(52)
            return
        end
    end
    evt.StatusText("No effect")
end, "Glowing dinosaur bones")

RegisterEvent(26, "Gold vein", function()
    if IsAtLeast(MapVar(21), 1) then return end
    local randomStep = PickRandomOption(26, 2, {15, 20, 15, 11, 7, 3})
    if randomStep == 15 then
        evt.DamagePlayer(5, 4, 20)
        evt.StatusText("Cave-in!")
        evt.SetTexture(143, "t3ll6")
        SetValue(MapVar(21), 1)
        return
    elseif randomStep == 20 then
        evt.DamagePlayer(5, 4, 20)
        AddValue(Gold, 1000)
        evt.StatusText("Cave-in!")
        evt.SetTexture(143, "t3ll6")
        SetValue(MapVar(21), 1)
        return
    elseif randomStep == 11 then
        AddValue(Gold, 800)
        evt.SetTexture(143, "t3ll6")
        SetValue(MapVar(21), 1)
        return
    elseif randomStep == 7 then
        AddValue(Gold, 600)
        evt.SetTexture(143, "t3ll6")
        SetValue(MapVar(21), 1)
        return
    elseif randomStep == 3 then
        AddValue(Gold, 400)
        evt.SetTexture(143, "t3ll6")
        SetValue(MapVar(21), 1)
        return
    end
end, "Gold vein")

RegisterEvent(28, "Gems", function()
    if IsAtLeast(MapVar(18), 1) then return end
    local randomStep = PickRandomOption(28, 2, {15, 20, 15, 11, 7, 3})
    if randomStep == 15 then
        evt.DamagePlayer(5, 4, 20)
        evt.StatusText("Cave-in!")
        evt.SetTexture(124, "t3ll6")
        SetValue(MapVar(18), 1)
        return
    elseif randomStep == 20 then
        evt.DamagePlayer(5, 4, 20)
        AddValue(Gold, 2000)
        evt.StatusText("Cave-in!")
        evt.SetTexture(124, "t3ll6")
        SetValue(MapVar(18), 1)
        return
    elseif randomStep == 11 then
        AddValue(Gold, 1200)
        evt.SetTexture(124, "t3ll6")
        SetValue(MapVar(18), 1)
        return
    elseif randomStep == 7 then
        AddValue(Gold, 800)
        evt.SetTexture(124, "t3ll6")
        SetValue(MapVar(18), 1)
        return
    elseif randomStep == 3 then
        AddValue(Gold, 600)
        evt.SetTexture(124, "t3ll6")
        SetValue(MapVar(18), 1)
        return
    end
end, "Gems")

RegisterEvent(29, "Gems", function()
    if IsAtLeast(MapVar(19), 1) then return end
    local randomStep = PickRandomOption(29, 2, {15, 20, 15, 11, 7, 3})
    if randomStep == 15 then
        evt.DamagePlayer(5, 4, 20)
        evt.StatusText("Cave-in!")
        evt.SetTexture(132, "t3ll6")
        SetValue(MapVar(19), 1)
        return
    elseif randomStep == 20 then
        evt.DamagePlayer(5, 4, 20)
        AddValue(Gold, 2000)
        evt.StatusText("Cave-in!")
        evt.SetTexture(132, "t3ll6")
        SetValue(MapVar(19), 1)
        return
    elseif randomStep == 11 then
        AddValue(Gold, 1200)
        evt.SetTexture(132, "t3ll6")
        SetValue(MapVar(19), 1)
        return
    elseif randomStep == 7 then
        AddValue(Gold, 800)
        evt.SetTexture(132, "t3ll6")
        SetValue(MapVar(19), 1)
        return
    elseif randomStep == 3 then
        AddValue(Gold, 600)
        evt.SetTexture(132, "t3ll6")
        SetValue(MapVar(19), 1)
        return
    end
end, "Gems")

RegisterEvent(30, "Gems", function()
    if IsAtLeast(MapVar(20), 1) then return end
    local randomStep = PickRandomOption(30, 2, {15, 20, 15, 11, 7, 3})
    if randomStep == 15 then
        evt.DamagePlayer(5, 4, 20)
        evt.StatusText("Cave-in!")
        evt.SetTexture(135, "t3ll6")
        SetValue(MapVar(20), 1)
        return
    elseif randomStep == 20 then
        evt.DamagePlayer(5, 4, 20)
        AddValue(Gold, 2000)
        evt.StatusText("Cave-in!")
        evt.SetTexture(135, "t3ll6")
        SetValue(MapVar(20), 1)
        return
    elseif randomStep == 11 then
        AddValue(Gold, 1200)
        evt.SetTexture(135, "t3ll6")
        SetValue(MapVar(20), 1)
        return
    elseif randomStep == 7 then
        AddValue(Gold, 800)
        evt.SetTexture(135, "t3ll6")
        SetValue(MapVar(20), 1)
        return
    elseif randomStep == 3 then
        AddValue(Gold, 600)
        evt.SetTexture(135, "t3ll6")
        SetValue(MapVar(20), 1)
        return
    end
end, "Gems")

RegisterEvent(31, "The door will not budge", function()
    evt.StatusText("The door will not budge")
end, "The door will not budge")

RegisterEvent(32, "Bones", function()
    if not IsAtLeast(MapVar(11), 1) then
        AddValue(MapVar(11), 1)
        AddValue(EarthResistance, 5)
        evt.StatusText("The bones feel weird (+5 Poison resistance permanent)")
        return
    end
    evt.StatusText("No effect")
end, "Bones")

RegisterEvent(33, "Bones", function()
    if not IsAtLeast(MapVar(12), 1) then
        AddValue(MapVar(12), 1)
        AddValue(FireResistance, 5)
        evt.StatusText("The bones feel weird (+5 Magic resistance permanent)")
        return
    end
    evt.StatusText("No effect")
end, "Bones")

RegisterEvent(35, "Legacy event 35", function()
    if IsAtLeast(MapVar(13), 1) then
        evt.SetTexture(204, "t3ll6")
    end
    if IsAtLeast(MapVar(14), 1) then
        evt.SetTexture(207, "t3ll6")
    end
    if IsAtLeast(MapVar(15), 1) then
        if IsAtLeast(MapVar(16), 1) then
            evt.SetTexture(624, "t3ll6")
        end
        if IsAtLeast(MapVar(17), 1) then
            evt.SetTexture(612, "t3ll6")
        end
        if IsAtLeast(MapVar(21), 1) then
            evt.SetTexture(143, "t3ll6")
        end
        if IsAtLeast(MapVar(18), 1) then
            evt.SetTexture(124, "t3ll6")
        end
        if IsAtLeast(MapVar(19), 1) then
            evt.SetTexture(132, "t3ll6")
        end
        if IsAtLeast(MapVar(20), 1) then
            evt.SetTexture(135, "t3ll6")
        end
        return
    elseif IsAtLeast(MapVar(16), 1) then
        evt.SetTexture(624, "t3ll6")
        if IsAtLeast(MapVar(17), 1) then
            evt.SetTexture(612, "t3ll6")
        end
        if IsAtLeast(MapVar(21), 1) then
            evt.SetTexture(143, "t3ll6")
        end
        if IsAtLeast(MapVar(18), 1) then
            evt.SetTexture(124, "t3ll6")
        end
        if IsAtLeast(MapVar(19), 1) then
            evt.SetTexture(132, "t3ll6")
        end
        if IsAtLeast(MapVar(20), 1) then
            evt.SetTexture(135, "t3ll6")
        end
        return
    elseif IsAtLeast(MapVar(17), 1) then
        evt.SetTexture(612, "t3ll6")
        if IsAtLeast(MapVar(21), 1) then
            evt.SetTexture(143, "t3ll6")
        end
        if IsAtLeast(MapVar(18), 1) then
            evt.SetTexture(124, "t3ll6")
        end
        if IsAtLeast(MapVar(19), 1) then
            evt.SetTexture(132, "t3ll6")
        end
        if IsAtLeast(MapVar(20), 1) then
            evt.SetTexture(135, "t3ll6")
        end
        return
    elseif IsAtLeast(MapVar(21), 1) then
        evt.SetTexture(143, "t3ll6")
        if IsAtLeast(MapVar(18), 1) then
            evt.SetTexture(124, "t3ll6")
        end
        if IsAtLeast(MapVar(19), 1) then
            evt.SetTexture(132, "t3ll6")
        end
        if IsAtLeast(MapVar(20), 1) then
            evt.SetTexture(135, "t3ll6")
        end
        return
    elseif IsAtLeast(MapVar(18), 1) then
        evt.SetTexture(124, "t3ll6")
        if IsAtLeast(MapVar(19), 1) then
            evt.SetTexture(132, "t3ll6")
        end
        if IsAtLeast(MapVar(20), 1) then
            evt.SetTexture(135, "t3ll6")
        end
        return
    elseif IsAtLeast(MapVar(19), 1) then
        evt.SetTexture(132, "t3ll6")
        if IsAtLeast(MapVar(20), 1) then
            evt.SetTexture(135, "t3ll6")
        end
        return
    elseif IsAtLeast(MapVar(20), 1) then
        evt.SetTexture(135, "t3ll6")
    else
        return
    end
end)

RegisterEvent(50, "Exit", function()
    evt.MoveToMap(-19604, 20019, 161, 1024, 0, 0, 0, 0, "outd3.odm")
end, "Exit")

RegisterEvent(51, "Legacy event 51", function()
    if IsAtLeast(MapVar(26), 1) then return end
    SetValue(MapVar(26), 1)
    local randomStep = PickRandomOption(51, 3, {3, 5, 7})
    if randomStep == 3 then
        evt.GiveItem(5, ItemType.Ring_)
        return
    elseif randomStep == 5 then
        evt.GiveItem(5, ItemType.Weapon_)
        return
    elseif randomStep == 7 then
        evt.GiveItem(5, ItemType.Armor_)
        return
    end
end)

