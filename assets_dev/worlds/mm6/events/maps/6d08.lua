-- Shadow Guild
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {2},
    onLeave = {},
    openedChestIds = {
    [31] = {1},
    [54] = {2},
    [55] = {3},
    [56] = {4},
    [57] = {5},
    [58] = {6},
    [74] = {7},
    [75] = {8},
    [76] = {9},
    [77] = {10},
    [78] = {11},
    [79] = {12},
    },
    textureNames = {"mystryb", "t3s1off", "t3s1on"},
    spriteNames = {},
    castSpellIds = {2, 15, 26, 34, 41},
    timers = {
    { eventId = 43, repeating = true, intervalGameMinutes = 4.5, remainingGameMinutes = 4.5 },
    { eventId = 44, repeating = true, intervalGameMinutes = 4, remainingGameMinutes = 4 },
    { eventId = 45, repeating = true, intervalGameMinutes = 3.5, remainingGameMinutes = 3.5 },
    { eventId = 46, repeating = true, intervalGameMinutes = 3, remainingGameMinutes = 3 },
    },
})

RegisterEvent(1, "Door", function()
    evt.SetDoorState(1, DoorAction.Close)
    evt.SetDoorState(2, DoorAction.Close)
end, "Door")

RegisterEvent(2, "Legacy event 2", function()
    SetValue(MapVar(2), 0)
    SetValue(MapVar(3), 0)
    SetValue(MapVar(4), 0)
    SetValue(MapVar(5), 0)
    SetValue(MapVar(6), 0)
    SetValue(MapVar(7), 0)
    SetValue(MapVar(8), 0)
    SetValue(MapVar(9), 0)
    SetValue(MapVar(10), 0)
    SetValue(MapVar(11), 0)
    SetValue(MapVar(12), 0)
    SetValue(MapVar(13), 0)
    SetValue(MapVar(14), 0)
    SetValue(MapVar(15), 0)
    SetValue(MapVar(16), 0)
    SetValue(MapVar(17), 0)
    SetValue(MapVar(18), 0)
    evt.SetDoorState(3, DoorAction.Close)
    evt.SetDoorState(4, DoorAction.Open)
    evt.SetDoorState(8, DoorAction.Open)
    evt.SetDoorState(1, DoorAction.Open)
    evt.SetDoorState(2, DoorAction.Open)
    evt.SetDoorState(11, DoorAction.Open)
    evt.SetDoorState(9, DoorAction.Open)
    evt.SetDoorState(5, DoorAction.Open)
    evt.SetDoorState(61, DoorAction.Open)
    evt.SetDoorState(62, DoorAction.Open)
    evt.SetDoorState(63, DoorAction.Open)
    evt.SetDoorState(64, DoorAction.Open)
    if IsAtLeast(MapVar(2), 1) then
        evt.SetTexture(833, "t3s1on")
    end
    if IsAtLeast(MapVar(17), 1) then
        evt.SetTexture(1079, "mystryb")
    end
end)

RegisterEvent(3, "Switch", function()
    evt.SetDoorState(3, DoorAction.Open)
    evt.SetDoorState(4, DoorAction.Close)
end, "Switch")

RegisterEvent(5, "Legacy event 5", function()
    evt.SetDoorState(5, DoorAction.Close)
end)

RegisterEvent(6, "Door", function()
    evt.SetDoorState(6, DoorAction.Close)
end, "Door")

RegisterEvent(7, "Door", function()
    evt.SetDoorState(7, DoorAction.Close)
end, "Door")

RegisterEvent(8, "Door", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.DamagePlayer(7, 0, 15)
        evt.SetDoorState(8, DoorAction.Close)
        return
    end
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

RegisterEvent(12, "Legacy event 12", function()
    evt.SetDoorState(12, DoorAction.Close)
end)

RegisterEvent(13, "Suspicious Floor", function()
    if not IsAtLeast(MapVar(2), 1) then
        SetValue(MapVar(2), 1)
        evt.SetTexture(833, "t3s1on")
        return
    end
    SetValue(MapVar(2), 0)
    evt.SetTexture(833, "t3s1off")
end, "Suspicious Floor")

RegisterEvent(14, "Suspicious Floor", function()
    if IsAtLeast(MapVar(5), 1) then return end
    SetValue(MapVar(3), 1)
    if IsAtLeast(MapVar(4), 1) then
        SetValue(MapVar(5), 1)
        evt.StatusText("Click!")
    end
end, "Suspicious Floor")

RegisterEvent(15, "Suspicious Floor", function()
    if IsAtLeast(MapVar(5), 1) then return end
    SetValue(MapVar(4), 1)
    if IsAtLeast(MapVar(3), 1) then
        SetValue(MapVar(5), 1)
        evt.StatusText("Click!")
    end
end, "Suspicious Floor")

RegisterEvent(16, "Suspicious Floor", function()
    if IsAtLeast(MapVar(8), 1) then return end
    SetValue(MapVar(6), 1)
    if IsAtLeast(MapVar(7), 1) then
        SetValue(MapVar(8), 1)
        evt.StatusText("Ca-Click!")
    end
end, "Suspicious Floor")

RegisterEvent(17, "Suspicious Floor", function()
    if IsAtLeast(MapVar(8), 1) then return end
    SetValue(MapVar(7), 1)
    if IsAtLeast(MapVar(6), 1) then
        SetValue(MapVar(8), 1)
        evt.StatusText("Ca-Click!")
    end
end, "Suspicious Floor")

RegisterEvent(18, "Suspicious Floor", function()
    if IsAtLeast(MapVar(11), 1) then return end
    SetValue(MapVar(9), 1)
    if IsAtLeast(MapVar(10), 1) then
        SetValue(MapVar(11), 1)
        evt.StatusText("Snick!")
    end
end, "Suspicious Floor")

RegisterEvent(19, "Suspicious Floor", function()
    if IsAtLeast(MapVar(11), 1) then return end
    SetValue(MapVar(10), 1)
    if IsAtLeast(MapVar(9), 1) then
        SetValue(MapVar(11), 1)
        evt.StatusText("Snick!")
    end
end, "Suspicious Floor")

RegisterEvent(20, "Suspicious Floor", function()
    if IsAtLeast(MapVar(14), 1) then return end
    SetValue(MapVar(12), 1)
    if IsAtLeast(MapVar(13), 1) then
        SetValue(MapVar(14), 1)
        evt.StatusText("Click!")
    end
end, "Suspicious Floor")

RegisterEvent(21, "Suspicious Floor", function()
    if IsAtLeast(MapVar(14), 1) then return end
    SetValue(MapVar(13), 1)
    if IsAtLeast(MapVar(12), 1) then
        SetValue(MapVar(14), 1)
        evt.StatusText("Click!")
    end
end, "Suspicious Floor")

RegisterEvent(22, "Suspicious Floor", function()
    if IsAtLeast(MapVar(17), 1) then return end
    evt.CastSpell(2, 2, 1, -400, 3072, 190, -1664, 4416, 120) -- Fire Bolt
    evt.CastSpell(15, 2, 1, -8, 3456, 120, -1664, 4416, 120) -- Sparks
    SetValue(MapVar(15), 1)
    if IsAtLeast(MapVar(16), 1) then
        SetValue(MapVar(17), 1)
        evt.StatusText("Ca-Click!")
    end
end, "Suspicious Floor")

RegisterEvent(23, "Suspicious Floor", function()
    if IsAtLeast(MapVar(17), 1) then return end
    evt.CastSpell(2, 2, 1, -1776, 3072, 120, -384, 4416, 120) -- Fire Bolt
    evt.CastSpell(15, 2, 1, -2040, 3456, 120, -384, 4416, 120) -- Sparks
    SetValue(MapVar(16), 1)
    if IsAtLeast(MapVar(15), 1) then
        SetValue(MapVar(17), 1)
        evt.StatusText("Ca-Click!")
    end
end, "Suspicious Floor")

RegisterEvent(24, "Suspicious Floor", function()
    if not IsAtLeast(MapVar(5), 1) then return end
    if not IsAtLeast(MapVar(8), 1) then return end
    if not IsAtLeast(MapVar(11), 1) then return end
    if not IsAtLeast(MapVar(14), 1) then return end
    if not IsAtLeast(MapVar(17), 1) then return end
    evt.StatusText("Snick!")
    evt.FaceExpression(5)
    SetValue(WaterResistanceBonus, 15)
    if IsAtLeast(MapVar(18), 1) then return end
    evt.StatusText("Magic Gate Open")
    SetValue(MapVar(18), 1)
    evt.SetTexture(1079, "mystryb")
    evt.SummonMonsters(3, 1, 1, 2688, 3968, 1, 0, 0) -- encounter slot 3 "BGenie" tier A, count 1, pos=(2688, 3968, 1), actor group 0, no unique actor name
    evt.MoveToMap(2179, 4314, 1, 1, 0, 0, 0, 0)
end, "Suspicious Floor")

RegisterEvent(25, "Suspicious Floor", function()
    evt.StatusText("Trap!")
    evt.CastSpell(15, 3, 1, -1024, 3840, 120, -1024, 2816, 120) -- Sparks
    evt.CastSpell(15, 3, 1, -1024, 3840, 120, -1024, 4864, 120) -- Sparks
    evt.CastSpell(15, 3, 1, -1024, 3840, 120, 0, 3480, 120) -- Sparks
    evt.CastSpell(15, 3, 1, -1024, 3840, 120, -2048, 3480, 120) -- Sparks
    evt.CastSpell(15, 3, 1, -1024, 3840, 120, -256, 4608, 120) -- Sparks
    evt.CastSpell(15, 3, 1, -1024, 3840, 120, -256, 3072, 120) -- Sparks
    evt.CastSpell(15, 3, 1, -1024, 3840, 120, -1792, 3072, 120) -- Sparks
    evt.CastSpell(15, 3, 1, -1024, 3840, 120, -1792, 4608, 120) -- Sparks
    SetValue(MapVar(5), 0)
    SetValue(MapVar(8), 0)
    SetValue(MapVar(11), 0)
    SetValue(MapVar(14), 0)
    SetValue(MapVar(17), 0)
end, "Suspicious Floor")

RegisterEvent(26, "Legacy event 26", function()
    if IsAtLeast(MapVar(18), 1) then
        evt.MoveToMap(8832, -4992, 87, 1, 0, 0, 0, 0)
    end
end)

RegisterEvent(31, "Bag", function()
    evt.OpenChest(1)
end, "Bag")

RegisterEvent(32, "Poisoned Spike", function()
    evt.DamagePlayer(6, 4, 16)
    evt.DamagePlayer(6, 4, 11)
end, "Poisoned Spike")

RegisterEvent(34, "Suspicious Floor", function()
    evt.CastSpell(34, 2, 1, -1632, 2544, 120, -1632, 768, 120) -- Stun
    evt.StatusText("Trap!")
end, "Suspicious Floor")

RegisterEvent(35, "Suspicious Floor", function()
    evt.CastSpell(34, 3, 1, 768, -1528, 120, 768, -1280, 120) -- Stun
    evt.StatusText("Trap!")
end, "Suspicious Floor")

RegisterEvent(36, "Unstable rock", function()
    evt.CastSpell(41, 8, 1, 1728, 1152, 240, 2176, 1152, 32) -- Rock Blast
    evt.StatusText("Trap!")
end, "Unstable rock")

RegisterEvent(39, "Suspicious Floor", function()
    evt.CastSpell(15, 13, 1, 2432, 3576, 120, 2432, 2824, 120) -- Sparks
    evt.StatusText("Trap!")
end, "Suspicious Floor")

RegisterEvent(40, "Suspicious Floor", function()
    evt.CastSpell(15, 10, 2, 2056, 3200, 120, 2800, 3200, 120) -- Sparks
    evt.StatusText("Trap!")
end, "Suspicious Floor")

RegisterEvent(41, "Suspicious Floor", function()
    evt.CastSpell(15, 13, 1, 2432, 2824, 120, 2432, 3576, 120) -- Sparks
    evt.StatusText("Trap!")
end, "Suspicious Floor")

RegisterEvent(42, "Suspicious Floor", function()
    evt.CastSpell(15, 10, 2, 2800, 3200, 120, 2056, 3200, 120) -- Sparks
    evt.StatusText("Trap!")
end, "Suspicious Floor")

RegisterEvent(43, "Legacy event 43", function()
    if IsAtLeast(MapVar(5), 1) then return end
    evt.CastSpell(2, 2, 1, -1776, 3072, 190, -400, 3072, 120) -- Fire Bolt
    evt.CastSpell(2, 2, 1, -400, 3072, 190, -1648, 3072, 120) -- Fire Bolt
end)

RegisterEvent(44, "Legacy event 44", function()
    if IsAtLeast(MapVar(8), 1) then return end
    evt.CastSpell(15, 2, 1, -2040, 3456, 120, -8, 3456, 120) -- Sparks
    evt.CastSpell(15, 2, 1, -8, 3456, 120, -2040, 3456, 120) -- Sparks
end)

RegisterEvent(45, "Legacy event 45", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.CastSpell(26, 2, 1, -2040, 3840, 120, -8, 3840, 120) -- Ice Bolt
    evt.CastSpell(26, 2, 1, -8, 3840, 120, -2040, 3840, 120) -- Ice Bolt
end)

RegisterEvent(46, "Legacy event 46", function()
    if IsAtLeast(MapVar(14), 1) then return end
    evt.CastSpell(34, 2, 1, -2040, 4096, 120, -8, 4096, 120) -- Stun
    evt.CastSpell(34, 2, 1, -8, 4096, 120, -2040, 4096, 120) -- Stun
end)

RegisterEvent(53, "Exit", function()
    evt.MoveToMap(15218, -14862, 161, 0, 0, 0, 0, 0, "outc1.odm")
end, "Exit")

RegisterEvent(54, "Bag", function()
    evt.OpenChest(2)
end, "Bag")

RegisterEvent(55, "Bag", function()
    evt.OpenChest(3)
end, "Bag")

RegisterEvent(56, "Bag", function()
    evt.OpenChest(4)
end, "Bag")

RegisterEvent(57, "Bag", function()
    evt.OpenChest(5)
end, "Bag")

RegisterEvent(58, "Bag", function()
    evt.OpenChest(6)
end, "Bag")

RegisterEvent(61, "Magic Door", function(continueStep)
    if continueStep == 2 then
        evt.StatusText("Incorrect")
        return
    end
    if continueStep == 4 then
        evt.SetDoorState(61, DoorAction.Close)
    end
    if continueStep ~= nil then return end
    evt.SimpleMessage("\"You cannot see me, hear me or touch me.  I lie behind the stars and alter what is real, I am what you really fear, Close your eyes and come I near. What am I?\"")
    evt.AskQuestion(61, 2, 21, 4, 19, 20, "Answer?  ", {"dark", "darkness"})
    return nil
end, "Magic Door")

RegisterEvent(62, "Magic Door", function(continueStep)
    if continueStep == 2 then
        evt.StatusText("Incorrect")
        return
    end
    if continueStep == 4 then
        evt.SetDoorState(62, DoorAction.Close)
    end
    if continueStep ~= nil then return end
    evt.SimpleMessage("\"I go through an apple, or point out your way, I fit in a bow, then a target, to stay. What am I?\"")
    evt.AskQuestion(62, 2, 21, 4, 24, 25, "Answer?  ", {"arrow", "an arrow"})
    return nil
end, "Magic Door")

RegisterEvent(63, "Magic Door", function(continueStep)
    if continueStep == 2 then
        evt.StatusText("Incorrect")
        return
    end
    if continueStep == 4 then
        evt.SetDoorState(63, DoorAction.Close)
    end
    if continueStep ~= nil then return end
    evt.SimpleMessage("\"What consumes rocks, levels mountains, destroys wood, pushes the clouds across the sky, and can make a young one old?\"")
    evt.AskQuestion(63, 2, 21, 4, 27, 27, "Answer?  ", {"time", "time"})
    return nil
end, "Magic Door")

RegisterEvent(64, "Magic Door", function(continueStep)
    if continueStep == 2 then
        evt.StatusText("Incorrect")
        return
    end
    if continueStep == 4 then
        evt.SetDoorState(64, DoorAction.Close)
    end
    if continueStep ~= nil then return end
    evt.SimpleMessage("\"Alive without breath, as cold as death, never thirsty ever drinking, all in mail never clinking, ever travelling, never walking, mouth ever moving, never talking.  What am I? \"")
    evt.AskQuestion(64, 2, 21, 4, 29, 30, "Answer?  ", {"fish", "a fish"})
    return nil
end, "Magic Door")

RegisterEvent(65, "Legacy event 65", function()
    evt.MoveToMap(0, 0, 0, 0, 0, 0, 0, 0)
    SubtractValue(Food, 5)
end)

RegisterEvent(66, "Legacy event 66", function()
    evt.MoveToMap(1408, -1664, 1, 0, 0, 0, 0, 0)
end)

RegisterEvent(67, "Legacy event 67", function()
    evt.MoveToMap(0, 0, 0, 0, 0, 0, 0, 0)
    SubtractValue(Food, 5)
end)

RegisterEvent(68, "Legacy event 68", function()
    evt.MoveToMap(11407, 18074, 1, 0, 0, 0, 0, 0)
    SubtractValue(Food, 5)
end)

RegisterEvent(69, "Magical Wall", nil, "Magical Wall")

RegisterEvent(70, "Sack", function()
    if not IsAtLeast(MapVar(52), 1) then
        SetValue(MapVar(52), 1)
        AddValue(Food, 4)
        return
    end
    evt.StatusText("Empty")
end, "Sack")

RegisterEvent(71, "Sack", function()
    if not IsAtLeast(MapVar(53), 1) then
        SetValue(MapVar(53), 1)
        AddValue(Food, 4)
        return
    end
    evt.StatusText("Empty")
end, "Sack")

RegisterEvent(72, "Sack", function()
    if not IsAtLeast(MapVar(54), 1) then
        SetValue(MapVar(54), 1)
        AddValue(Food, 4)
        return
    end
    evt.StatusText("Empty")
end, "Sack")

RegisterEvent(73, "Sack", function()
    if IsAtLeast(MapVar(55), 1) then return end
    SetValue(MapVar(55), 1)
    AddValue(Food, 3)
end, "Sack")

RegisterEvent(74, "Bag", function()
    evt.OpenChest(7)
end, "Bag")

RegisterEvent(75, "Bag", function()
    evt.OpenChest(8)
end, "Bag")

RegisterEvent(76, "Bag", function()
    evt.OpenChest(9)
end, "Bag")

RegisterEvent(77, "Bag", function()
    evt.OpenChest(10)
end, "Bag")

RegisterEvent(78, "Bag", function()
    evt.OpenChest(11)
end, "Bag")

RegisterEvent(79, "Bag", function()
    evt.OpenChest(12)
end, "Bag")

RegisterEvent(80, "Bag", function()
    evt.StatusText("Empty")
end, "Bag")

