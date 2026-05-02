-- Castle Darkmoor
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {58},
    onLeave = {},
    openedChestIds = {
    [10] = {0},
    },
    textureNames = {"deskside", "lavatyl", "orwtrtyl"},
    spriteNames = {"crysdisc"},
    castSpellIds = {6, 26, 32, 90},
    timers = {
    },
})

RegisterEvent(1, "Door", function()
    evt.SetDoorState(1, DoorAction.Close)
end, "Door")

RegisterEvent(2, "Legacy event 2", function()
    evt.CastSpell(90, 10, 1, 13819, -866, -180, 0, 0, 0) -- Toxic Cloud
end)

RegisterEvent(3, "Legacy event 3", function()
    evt.CastSpell(32, 8, 1, 11136, 3712, -80, 0, 0, 0) -- Ice Blast
end)

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

RegisterEvent(10, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(19, "Legacy event 19", function()
    evt.CastSpell(6, 10, 1, 10417, 4800, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 10, 1, 10706, 2258, 150, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 10, 1, 10706, 1628, 150, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 10, 1, 9978, 1914, 150, 0, 0, 0) -- Fireball
end)

RegisterEvent(20, "Door ", function()
    evt.CastSpell(90, 1, 1, 14925, 2518, -689, 0, 0, 0) -- Toxic Cloud
end, "Door ")

RegisterEvent(21, "Legacy event 21", function()
    evt.CastSpell(26, 1, 1, 15217, 576, 528, 0, 0, 0) -- Ice Bolt
    evt.CastSpell(26, 1, 1, 15112, 171, 529, 0, 0, 0) -- Ice Bolt
    evt.CastSpell(26, 1, 1, 15123, 405, 529, 0, 0, 0) -- Ice Bolt
end)

RegisterEvent(22, "Legacy event 22", function()
    evt.CastSpell(26, 1, 1, 15217, 576, 528, 0, 0, 0) -- Ice Bolt
    evt.CastSpell(26, 1, 1, 15112, 171, 529, 0, 0, 0) -- Ice Bolt
    evt.CastSpell(26, 1, 1, 15123, 405, 529, 0, 0, 0) -- Ice Bolt
end)

RegisterEvent(23, "Legacy event 23", function()
    evt.CastSpell(6, 1, 1, 14718, 2456, 541, 0, 0, 0) -- Fireball
end)

RegisterEvent(24, "Legacy event 24", function()
    evt.CastSpell(6, 1, 1, 18915, 2035, 541, 0, 0, 0) -- Fireball
end)

RegisterEvent(25, "Legacy event 25", function()
    evt.CastSpell(6, 1, 1, 18111, 10127, 386, 18111, 4782, 386) -- Fireball
    evt.CastSpell(6, 1, 1, 18131, 10127, 386, 18131, 4782, 386) -- Fireball
    evt.CastSpell(6, 1, 1, 18151, 10127, 386, 18151, 4782, 386) -- Fireball
    evt.CastSpell(6, 1, 1, 18171, 10127, 386, 18171, 4782, 386) -- Fireball
    evt.CastSpell(6, 1, 1, 18191, 10127, 386, 18191, 4782, 386) -- Fireball
    evt.CastSpell(6, 1, 1, 18201, 10127, 386, 18201, 4782, 386) -- Fireball
end)

RegisterEvent(26, "Legacy event 26", function()
    if IsQBitSet(QBit(1033)) then return end -- 9, CD2, given when you destroy Lich book
    evt.SummonMonsters(1, 2, 3, -7522, 14848, -240, 0, 0) -- encounter slot 1 "BLich" tier B, count 3, pos=(-7522, 14848, -240), actor group 0, no unique actor name
end)

RegisterEvent(27, "Legacy event 27", function()
    evt.CastSpell(6, 1, 1, -2904, 16512, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, -2432, 16512, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, -1960, 16512, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, -1606, 16512, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, -1134, 16512, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, -426, 16512, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, -72, 16512, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, 400, 16512, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, 1108, 16512, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, 1462, 16512, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, 1934, 16512, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, 2642, 16512, 100, 0, 0, 0) -- Fireball
end)

RegisterEvent(28, "Legacy event 28", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.MoveToMap(22768, 7504, 1170, 0, 0, 0, 0, 0)
        return
    end
    evt.SetDoorState(10, DoorAction.Close)
    evt.StatusText("The way has been cleared")
end)

RegisterEvent(29, "Legacy event 29", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.MoveToMap(10384, 2224, 0, 0, 0, 0, 0, 0)
        return
    end
    evt.SetDoorState(10, DoorAction.Close)
    evt.StatusText("The way has been cleared")
end)

RegisterEvent(30, "Legacy event 30", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.MoveToMap(22768, 7504, 1170, 0, 0, 0, 0, 0)
        return
    end
    evt.SetDoorState(10, DoorAction.Close)
    evt.StatusText("The way has been cleared")
end)

RegisterEvent(31, "Legacy event 31", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.MoveToMap(8608, 128, 630, 0, 0, 0, 0, 0)
        return
    end
    evt.SetDoorState(10, DoorAction.Close)
    evt.StatusText("The way has been cleared")
end)

RegisterEvent(32, "Legacy event 32", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.MoveToMap(22768, 7504, 1170, 0, 0, 0, 0, 0)
        return
    end
    evt.SetDoorState(10, DoorAction.Close)
    evt.StatusText("The way has been cleared")
end)

RegisterEvent(33, "Legacy event 33", function()
    if not IsAtLeast(MapVar(3), 1) then
        evt.MoveToMap(2560, 3856, -636, 0, 0, 0, 0, 0)
        return
    end
    if not IsAtLeast(MapVar(3), 2) then
        AddValue(MapVar(3), 1)
        evt.SetFacetBit(4522, FacetBits.Untouchable, 1)
        evt.SetFacetBit(4575, FacetBits.Untouchable, 1)
        evt.StatusText("The way has been cleared")
        return
    end
    evt.MoveToMap(2560, 3856, -636, 0, 0, 0, 0, 0)
end)

RegisterEvent(34, "Podium", function()
    if not IsQBitSet(QBit(1033)) then -- 9, CD2, given when you destroy Lich book
        evt.StatusText("The Book of Liches is destroyed")
        SetQBit(QBit(1033)) -- 9, CD2, given when you destroy Lich book
        evt.SetTexture(4560, "deskside")
        return
    end
    evt.StatusText("The Book is destroyed")
end, "Podium")

RegisterEvent(35, "Legacy event 35", function()
    if not IsAtLeast(MapVar(3), 1) then
        evt.SummonObject(2081, 317, 14144, 191, 1000, 1, false) -- explosion
        evt.SummonObject(1, 317, 14144, 320, 10, 1, false) -- longsword
        return
    end
    if IsAtLeast(MapVar(3), 2) then return end
    AddValue(MapVar(3), 1)
    evt.SetFacetBit(4522, FacetBits.Untouchable, 1)
    evt.SetFacetBit(4575, FacetBits.Untouchable, 1)
    evt.StatusText("The way has been cleared")
end)

RegisterEvent(36, "Legacy event 36", function()
    if not IsAtLeast(MapVar(3), 1) then
        evt.SummonObject(2081, 551, 14144, 191, 1000, 1, false) -- explosion
        evt.SummonObject(1, 551, 14144, 320, 10, 1, false) -- longsword
        return
    end
    if IsAtLeast(MapVar(3), 2) then return end
    AddValue(MapVar(3), 1)
    evt.SetFacetBit(4522, FacetBits.Untouchable, 1)
    evt.SetFacetBit(4575, FacetBits.Untouchable, 1)
    evt.StatusText("The way has been cleared")
end)

RegisterEvent(37, "Legacy event 37", function()
    if not IsAtLeast(MapVar(3), 1) then
        evt.MoveToMap(16080, 9072, -180, 0, 0, 0, 0, 0)
        return
    end
    if not IsAtLeast(MapVar(3), 2) then
        AddValue(MapVar(3), 1)
        evt.SetFacetBit(4522, FacetBits.Untouchable, 1)
        evt.SetFacetBit(4575, FacetBits.Untouchable, 1)
        evt.StatusText("The way has been cleared")
        return
    end
    evt.MoveToMap(16080, 9072, -180, 0, 0, 0, 0, 0)
end)

RegisterEvent(38, "Legacy event 38", function()
    if not IsAtLeast(MapVar(4), 1) then
        evt.MoveToMap(-10240, 12144, -240, 0, 0, 0, 0, 0)
        return
    end
    evt.MoveToMap(22080, -2192, 1, 0, 0, 0, 0, 0)
end)

RegisterEvent(39, "Legacy event 39", function()
    if not IsAtLeast(MapVar(4), 1) then
        evt.MoveToMap(-7328, 10496, 600, 0, 0, 0, 0, 0)
        return
    end
    evt.MoveToMap(22080, -2192, 1, 0, 0, 0, 0, 0)
end)

RegisterEvent(40, "Legacy event 40", function()
    if not IsAtLeast(MapVar(4), 1) then
        evt.MoveToMap(-6112, 10912, 600, 0, 0, 0, 0, 0)
        return
    end
    evt.MoveToMap(22080, -2192, 1, 0, 0, 0, 0, 0)
end)

RegisterEvent(41, "Legacy event 41", function()
    if not IsAtLeast(MapVar(4), 1) then
        evt.MoveToMap(-10240, 12144, -240, 0, 0, 0, 0, 0)
        return
    end
    evt.MoveToMap(22080, -2192, 1, 0, 0, 0, 0, 0)
end)

RegisterEvent(42, "Legacy event 42", function()
    if not IsAtLeast(MapVar(4), 1) then
        evt.MoveToMap(-10240, 12144, -240, 0, 0, 0, 0, 0)
        return
    end
    evt.MoveToMap(22080, -2192, 1, 0, 0, 0, 0, 0)
end)

RegisterEvent(43, "Legacy event 43", function()
    evt.MoveToMap(13744, 640, -180, 0, 0, 0, 0, 0)
end)

RegisterEvent(44, "Legacy event 44", function()
    evt.MoveToMap(2528, 3568, -635, 0, 0, 0, 0, 0)
end)

RegisterEvent(45, "Sign", function()
    if not IsAtLeast(MapVar(4), 1) then
        SetValue(MapVar(4), 1)
        evt.SimpleMessage("The fires of the dead shall burn forever")
        evt.SetTexture(4298, "lavatyl")
        evt.SetTexture(4299, "lavatyl")
        evt.SetTexture(4300, "lavatyl")
        evt.SetTexture(4301, "lavatyl")
        evt.SetTexture(4302, "lavatyl")
        evt.SetFacetBit(4298, FacetBits.Fluid, 1)
        evt.SetFacetBit(4299, FacetBits.Fluid, 1)
        evt.SetFacetBit(4300, FacetBits.Fluid, 1)
        evt.SetFacetBit(4301, FacetBits.Fluid, 1)
        evt.SetFacetBit(4302, FacetBits.Fluid, 1)
        return
    end
    SetValue(MapVar(4), 0)
    evt.SetTexture(4298, "orwtrtyl")
    evt.SetTexture(4299, "orwtrtyl")
    evt.SetTexture(4300, "orwtrtyl")
    evt.SetTexture(4301, "orwtrtyl")
    evt.SetTexture(4302, "orwtrtyl")
end, "Sign")

RegisterEvent(46, "Legacy event 46", function()
    evt.CastSpell(6, 1, 1, -2904, 11904, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, -2432, 11904, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, -1960, 11904, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, -1606, 11904, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, -1134, 11904, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, -426, 11904, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, -72, 11904, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, 400, 11904, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, 1108, 11904, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, 1462, 11904, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, 1934, 11904, 100, 0, 0, 0) -- Fireball
    evt.CastSpell(6, 1, 1, 2642, 11904, 100, 0, 0, 0) -- Fireball
end)

RegisterEvent(47, "Legacy event 47", function()
    if IsQBitSet(QBit(1033)) then return end -- 9, CD2, given when you destroy Lich book
    evt.SummonMonsters(1, 2, 3, -6144, 14720, -240, 0, 0) -- encounter slot 1 "BLich" tier B, count 3, pos=(-6144, 14720, -240), actor group 0, no unique actor name
end)

RegisterEvent(48, "Legacy event 48", function()
    if IsQBitSet(QBit(1033)) then return end -- 9, CD2, given when you destroy Lich book
    evt.SummonMonsters(1, 2, 3, -5120, 14208, -240, 0, 0) -- encounter slot 1 "BLich" tier B, count 3, pos=(-5120, 14208, -240), actor group 0, no unique actor name
end)

RegisterEvent(49, "Legacy event 49", function()
    if IsQBitSet(QBit(1033)) then return end -- 9, CD2, given when you destroy Lich book
    evt.SummonMonsters(1, 2, 3, -5760, 12800, -240, 0, 0) -- encounter slot 1 "BLich" tier B, count 3, pos=(-5760, 12800, -240), actor group 0, no unique actor name
end)

RegisterEvent(50, "Legacy event 50", function()
    if IsQBitSet(QBit(1033)) then return end -- 9, CD2, given when you destroy Lich book
    evt.SummonMonsters(1, 2, 3, -7552, 12800, -240, 0, 0) -- encounter slot 1 "BLich" tier B, count 3, pos=(-7552, 12800, -240), actor group 0, no unique actor name
end)

RegisterEvent(51, "Legacy event 51", function()
    if IsQBitSet(QBit(1033)) then return end -- 9, CD2, given when you destroy Lich book
    evt.SummonMonsters(1, 2, 3, -7808, 13056, -240, 0, 0) -- encounter slot 1 "BLich" tier B, count 3, pos=(-7808, 13056, -240), actor group 0, no unique actor name
end)

RegisterEvent(52, "Legacy event 52", function()
    if IsQBitSet(QBit(1033)) then return end -- 9, CD2, given when you destroy Lich book
    evt.SummonMonsters(1, 2, 3, -5376, 11904, -240, 0, 0) -- encounter slot 1 "BLich" tier B, count 3, pos=(-5376, 11904, -240), actor group 0, no unique actor name
end)

RegisterEvent(53, "Sign", function()
    evt.SimpleMessage("The crimson embers will lead the way")
    evt.SetDoorState(13, DoorAction.Trigger)
end, "Sign")

RegisterEvent(54, "Lever", function()
    if not IsAtLeast(MapVar(2), 1) then
        SetValue(MapVar(2), 1)
        evt.SetDoorState(14, DoorAction.Trigger)
        evt.SetTexture(4219, "lavatyl")
        evt.SetTexture(4220, "lavatyl")
        evt.SetTexture(4221, "lavatyl")
        evt.SetTexture(4222, "lavatyl")
        evt.SetTexture(4223, "lavatyl")
        evt.SetFacetBit(4219, FacetBits.Fluid, 1)
        evt.SetFacetBit(4220, FacetBits.Fluid, 1)
        evt.SetFacetBit(4221, FacetBits.Fluid, 1)
        evt.SetFacetBit(4222, FacetBits.Fluid, 1)
        evt.SetFacetBit(4223, FacetBits.Fluid, 1)
        return
    end
    evt.SetDoorState(14, DoorAction.Trigger)
    SetValue(MapVar(2), 0)
    evt.SetTexture(4219, "orwtrtyl")
    evt.SetTexture(4220, "orwtrtyl")
    evt.SetTexture(4221, "orwtrtyl")
    evt.SetTexture(4222, "orwtrtyl")
    evt.SetTexture(4223, "orwtrtyl")
end, "Lever")

RegisterEvent(55, "Sign", function()
    evt.SimpleMessage("The crimson embers will lead the way")
    evt.SetDoorState(11, DoorAction.Trigger)
end, "Sign")

RegisterEvent(56, "Sign", function()
    if not IsAtLeast(MapVar(3), 1) then
        evt.SetDoorState(12, DoorAction.Trigger)
        SetValue(MapVar(3), 1)
        evt.SetTexture(4265, "lavatyl")
        evt.SetTexture(4266, "lavatyl")
        evt.SetTexture(4267, "lavatyl")
        evt.SetTexture(4268, "lavatyl")
        evt.SetTexture(4269, "lavatyl")
        evt.SetFacetBit(4265, FacetBits.Fluid, 1)
        evt.SetFacetBit(4266, FacetBits.Fluid, 1)
        evt.SetFacetBit(4267, FacetBits.Fluid, 1)
        evt.SetFacetBit(4268, FacetBits.Fluid, 1)
        evt.SetFacetBit(4269, FacetBits.Fluid, 1)
        return
    end
    evt.SetDoorState(14, DoorAction.Trigger)
    SetValue(MapVar(3), 0)
    evt.SetTexture(4265, "orwtrtyl")
    evt.SetTexture(4266, "orwtrtyl")
    evt.SetTexture(4267, "orwtrtyl")
    evt.SetTexture(4269, "orwtrtyl")
    evt.SetTexture(4269, "orwtrtyl")
end, "Sign")

RegisterEvent(57, "Crystal", function()
    evt.ForPlayer(Players.All)
    if IsQBitSet(QBit(1126)) then -- Oracle
        return
    elseif HasItem(2172) then -- Memory Crystal Delta
        return
    else
        evt.SetSprite(329, 1, "crysdisc")
        evt.ForPlayer(6)
        AddValue(InventoryItem(2172), 2172) -- Memory Crystal Delta
        SetQBit(QBit(1217)) -- Quest item bits for seer
        return
    end
end, "Crystal")

RegisterEvent(58, "Legacy event 58", function()
    evt.ForPlayer(Players.All)
    if IsQBitSet(QBit(1126)) or HasItem(2172) then -- Oracle
        evt.SetSprite(329, 1, "crysdisc")
    end
    if IsAtLeast(MapVar(4), 1) then
        evt.SetTexture(4298, "lavatyl")
        evt.SetTexture(4299, "lavatyl")
        evt.SetTexture(4300, "lavatyl")
        evt.SetTexture(4301, "lavatyl")
        evt.SetTexture(4302, "lavatyl")
    end
    if IsAtLeast(MapVar(2), 1) then
        evt.SetTexture(4219, "lavatyl")
        evt.SetTexture(4220, "lavatyl")
        evt.SetTexture(4221, "lavatyl")
        evt.SetTexture(4222, "lavatyl")
        evt.SetTexture(4223, "lavatyl")
    end
    if IsAtLeast(MapVar(3), 1) then
        evt.SetTexture(4265, "lavatyl")
        evt.SetTexture(4266, "lavatyl")
        evt.SetTexture(4267, "lavatyl")
        evt.SetTexture(4268, "lavatyl")
        evt.SetTexture(4269, "lavatyl")
    end
    if IsQBitSet(QBit(1033)) then -- 9, CD2, given when you destroy Lich book
        evt.SetTexture(4560, "deskside")
    end
    if IsAtLeast(MapVar(3), 1) then
        evt.SetFacetBit(4522, FacetBits.Untouchable, 1)
        evt.SetFacetBit(4575, FacetBits.Untouchable, 1)
    end
end)

RegisterEvent(59, "Forcefield", function()
    evt.StatusText("Your way is blocked.")
end, "Forcefield")

RegisterEvent(60, "Legacy event 60", function()
    evt.MoveToMap(-17281, 17465, 2081, 0, 0, 0, 0, 0, "outc3.odm")
end)

RegisterEvent(61, "Sarcophagus", function(continueStep)
    if continueStep == 3 then
        return
    end
    if continueStep == 4 then
        SetValue(MapVar(11), 1)
        evt.GiveItem(6, 35)
        SubtractValue(655595, 10)
    end
    if continueStep ~= nil then return end
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SimpleMessage("Steal from the dead?")
    evt.AskQuestion(61, 3, 21, 4, 22, 23, "Steal (Yes/No)?", {"Yes", "Y"})
    return nil
end, "Sarcophagus")

RegisterEvent(62, "Sarcophagus", function(continueStep)
    if continueStep == 3 then
        return
    end
    if continueStep == 4 then
        SetValue(MapVar(12), 1)
        evt.GiveItem(6, 39)
        SubtractValue(655595, 10)
    end
    if continueStep ~= nil then return end
    if IsAtLeast(MapVar(12), 1) then return end
    evt.SimpleMessage("Steal from the dead?")
    evt.AskQuestion(62, 3, 21, 4, 22, 23, "Steal (Yes/No)?", {"Yes", "Y"})
    return nil
end, "Sarcophagus")

RegisterEvent(63, "Sarcophagus", function(continueStep)
    if continueStep == 3 then
        return
    end
    if continueStep == 4 then
        SetValue(MapVar(13), 1)
        evt.GiveItem(6, 36)
        SubtractValue(655595, 10)
    end
    if continueStep ~= nil then return end
    if IsAtLeast(MapVar(13), 1) then return end
    evt.SimpleMessage("Steal from the dead?")
    evt.AskQuestion(63, 3, 21, 4, 22, 23, "Steal (Yes/No)?", {"Yes", "Y"})
    return nil
end, "Sarcophagus")

RegisterEvent(64, "Legacy event 64", function()
    if IsAtLeast(MapVar(14), 1) then return end
    evt.ForPlayer(Players.Current)
    SetValue(MapVar(14), 1)
    AddValue(SkillPoints, 20)
    evt.StatusText("How Clever!  +20 Skill points")
end)

