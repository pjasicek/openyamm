-- Eel Infested Waters
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {226},
    onLeave = {},
    openedChestIds = {
    [58] = {1},
    [59] = {2},
    },
    textureNames = {},
    spriteNames = {"swrdstx"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(2, "Kessel's Kantina", function()
    evt.EnterHouse(108) -- Kessel's Kantina
end, "Kessel's Kantina")

RegisterEvent(3, "Kessel's Kantina", nil, "Kessel's Kantina")

RegisterEvent(4, "Veldon's Cottage", function()
    evt.EnterHouse(328) -- Veldon's Cottage
end, "Veldon's Cottage")

RegisterEvent(5, "Bluesawn Home", function()
    evt.EnterHouse(262) -- Bluesawn Home
end, "Bluesawn Home")

RegisterEvent(6, "Bluesawn Home", nil, "Bluesawn Home")

RegisterEvent(7, "Quicktongue Estate", function()
    evt.EnterHouse(263) -- Quicktongue Estate
end, "Quicktongue Estate")

RegisterEvent(8, "Quicktongue Estate", nil, "Quicktongue Estate")

RegisterEvent(9, "House 504", function()
    evt.EnterHouse(504) -- House 504
end, "House 504")

RegisterEvent(10, "House 503", function()
    evt.EnterHouse(503) -- House 503
end, "House 503")

RegisterEvent(50, "Legacy event 50", function()
    evt.EnterHouse(1226)
end)

RegisterEvent(51, "Legacy event 51", function()
    evt.EnterHouse(1241)
end)

RegisterEvent(52, "Legacy event 52", function()
    evt.EnterHouse(1256)
end)

RegisterEvent(53, "Legacy event 53", function()
    evt.EnterHouse(1271)
end)

RegisterEvent(54, "Legacy event 54", function()
    evt.EnterHouse(1286)
end)

RegisterEvent(55, "Legacy event 55", function()
    evt.EnterHouse(1301)
end)

RegisterEvent(56, "Legacy event 56", function()
    evt.EnterHouse(1314)
end)

RegisterEvent(57, "Legacy event 57", function()
    evt.EnterHouse(1326)
end)

RegisterEvent(58, "Legacy event 58", function()
    evt.OpenChest(1)
end)

RegisterEvent(59, "Legacy event 59", function()
    evt.OpenChest(2)
end)

RegisterEvent(90, "Legacy event 90", function()
    evt.MoveToMap(-2921, 13139, 225, 1536, 0, 0, 163, 1, "cd1.blv")
end)

RegisterEvent(100, "Drink from Fountain.", function()
    if not IsAtLeast(FireResistanceBonus, 20) then
        SetValue(FireResistanceBonus, 20)
        SetValue(AirResistanceBonus, 20)
        SetValue(WaterResistanceBonus, 20)
        SetValue(EarthResistanceBonus, 20)
        evt.StatusText("+20 Elemental resistance temporary.")
        SetAutonote(405) -- 20 Points of temporary fire, electricity, cold, and poison resistance from the southwest fountain in the Eel Infested Waters.
        return
    end
    evt.StatusText("Refreshing")
end, "Drink from Fountain.")

RegisterEvent(101, "Drink from Fountain.", function()
    if not IsAtLeast(WaterResistanceBonus, 20) then
        SetValue(WaterResistanceBonus, 20)
        evt.StatusText("+20 Magic resistance temporary.")
        SetAutonote(406) -- 20 Points of temporary magic resistance from the southeast fountain in the Eel Infested Waters.
        return
    end
    evt.StatusText("Refreshing")
end, "Drink from Fountain.")

RegisterEvent(226, "Legacy event 226", function()
    if IsQBitSet(QBit(1337)) then -- NPC
        return
    end
    if not IsAtLeast(ActualMight, 200) then
        evt.FaceExpression(51)
        evt.StatusText("The Sword won't budge!")
        return
    end
    SetQBit(QBit(1337)) -- NPC
    AddValue(InventoryItem(2023), 2023) -- Excalibur
    evt.SetSprite(99, 1, "swrdstx")
end)

RegisterEvent(227, "Obelisk", function()
    evt.SimpleMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            oon_htfdorstusl_")
    SetQBit(QBit(1396)) -- NPC
    SetAutonote(454) -- Obelisk Message # 13: oon_htfdorstusl_
end, "Obelisk")

RegisterEvent(261, "Shrine of Poison", function()
    if not IsAtLeast(MonthIs, 10) then
        evt.StatusText("You pray at the shrine.")
        return
    end
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1241)) then -- NPC
            SetQBit(QBit(1241)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(EarthResistance, 10)
            evt.StatusText("+10 Poison resistance permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(EarthResistance, 3)
        evt.StatusText("+3 Poison resistance permanent")
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Poison")

