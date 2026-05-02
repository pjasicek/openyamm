-- Bootleg Bay
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {122},
    onLeave = {},
    openedChestIds = {
    [60] = {1},
    [61] = {2},
    [62] = {3},
    [63] = {4},
    [64] = {5},
    },
    textureNames = {},
    spriteNames = {"ped05"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(2, "Refreshing!", function()
    evt.EnterHouse(23) -- Placeholder
end, "Refreshing!")

RegisterEvent(3, "Refreshing!", nil, "Refreshing!")

RegisterEvent(4, "Pedestal", function()
    evt.EnterHouse(65) -- Smoke
end, "Pedestal")

RegisterEvent(5, "Pedestal", nil, "Pedestal")

RegisterEvent(6, "Placeholder", function()
    evt.EnterHouse(99) -- Placeholder
end, "Placeholder")

RegisterEvent(7, "Placeholder", nil, "Placeholder")

RegisterEvent(8, "Legacy event 8", function()
    evt.EnterHouse(1587)
end)

RegisterEvent(9, "Legacy event 9", nil)

RegisterEvent(10, "Caverhill Estate", function()
    evt.EnterHouse(266) -- Caverhill Estate
end, "Caverhill Estate")

RegisterEvent(11, "Caverhill Estate", nil, "Caverhill Estate")

RegisterEvent(12, "Reaver's Home", function()
    evt.EnterHouse(267) -- Reaver's Home
end, "Reaver's Home")

RegisterEvent(13, "Reaver's Home", nil, "Reaver's Home")

RegisterEvent(14, "Legacy event 14", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1595)
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end)

RegisterEvent(15, "Talion's Hovel", function()
    evt.EnterHouse(333) -- Talion's Hovel
end, "Talion's Hovel")

RegisterEvent(16, "House 506", function()
    evt.EnterHouse(506) -- House 506
end, "House 506")

RegisterEvent(17, "House 505", function()
    evt.EnterHouse(505) -- House 505
end, "House 505")

RegisterEvent(18, "Obelisk", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1596)
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Obelisk")

RegisterEvent(19, "Freehaven", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1598)
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Freehaven")

RegisterEvent(20, "Legacy event 20", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1601)
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end)

RegisterEvent(21, "Ironfist Castle", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1597)
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Ironfist Castle")

RegisterEvent(22, "Circus (Winter)", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1599)
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Circus (Winter)")

RegisterEvent(23, "Drink from Fountain", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1600)
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Drink from Fountain")

RegisterEvent(24, "Ironfist Castle", function()
    evt.StatusText("Ironfist Castle")
end, "Ironfist Castle")

RegisterEvent(25, "Freehaven", function()
    evt.StatusText("Freehaven")
end, "Freehaven")

RegisterEvent(26, "Circus (Winter)", function()
    evt.StatusText("Circus (Winter)")
end, "Circus (Winter)")

RegisterEvent(50, "Legacy event 50", function()
    evt.EnterHouse(1224)
end)

RegisterEvent(51, "Legacy event 51", function()
    evt.EnterHouse(1239)
end)

RegisterEvent(52, "Legacy event 52", function()
    evt.EnterHouse(1254)
end)

RegisterEvent(53, "Legacy event 53", function()
    evt.EnterHouse(1269)
end)

RegisterEvent(54, "Legacy event 54", function()
    evt.EnterHouse(1284)
end)

RegisterEvent(55, "Legacy event 55", function()
    evt.EnterHouse(1299)
end)

RegisterEvent(56, "Legacy event 56", function()
    evt.EnterHouse(1312)
end)

RegisterEvent(57, "Legacy event 57", function()
    evt.EnterHouse(1324)
end)

RegisterEvent(58, "Legacy event 58", function()
    evt.EnterHouse(1335)
end)

RegisterEvent(59, "Legacy event 59", function()
    evt.EnterHouse(1347)
end)

RegisterEvent(60, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(61, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(62, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(63, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(64, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(90, "Legacy event 90", function()
    evt.MoveToMap(-1792, -19, 1, 0, 0, 0, 172, 1, "6d04.blv")
end)

RegisterEvent(91, "Drink from Well.", function()
    evt.MoveToMap(0, -2231, 513, 512, 0, 0, 167, 1, "6t2.blv")
end, "Drink from Well.")

RegisterEvent(92, "Drink from Well.", function()
    evt.MoveToMap(-3258, 483, 49, 0, 0, 0, 173, 1, "6t4.blv")
end, "Drink from Well.")

RegisterEvent(93, "Drink from Well.", function()
    evt.MoveToMap(2817, -4748, -639, 512, 0, 0, 170, 1, "6t3.blv")
end, "Drink from Well.")

RegisterEvent(94, "Hovel of Mist", function()
    evt.EnterHouse(334) -- Hovel of Mist
end, "Hovel of Mist")

RegisterEvent(100, "Drink from Well.", function()
    if IsAtLeast(MightBonus, 20) then return end
    SetValue(MightBonus, 20)
    evt.StatusText("+20 Might temporary.")
    SetAutonote(410) -- 20 Points of temporary might from the well near the Goblin's Tooth in Bootleg Bay.
end, "Drink from Well.")

RegisterEvent(101, "Drink from Well.", function()
    evt.DamagePlayer(7, 2, 40)
    SetValue(PoisonedYellow, 1)
    evt.StatusText("Poison!")
end, "Drink from Well.")

RegisterEvent(102, "Drink from Fountain", function()
    if not IsAtLeast(BaseIntellect, 15) then
        if not IsAtLeast(MapVar(3), 1) then
            evt.StatusText("Refreshing!")
            return
        end
        SubtractValue(MapVar(3), 1)
        AddValue(BaseIntellect, 2)
        evt.StatusText("+2 Intellect permanent.")
        SetAutonote(411) -- 2 Points of permanent intellect from the north fountain in Bootleg Bay.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain")

RegisterEvent(103, "Drink from Fountain", function()
    if not IsAtLeast(BasePersonality, 15) then
        if not IsAtLeast(MapVar(4), 1) then
            evt.StatusText("Refreshing!")
            return
        end
        SubtractValue(MapVar(4), 1)
        AddValue(BasePersonality, 2)
        evt.StatusText("+2 Personality permanent.")
        SetAutonote(412) -- 2 Points of permanent personality from the south fountain in Bootleg Bay.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain")

RegisterEvent(104, "Legacy event 104", function()
    SetValue(MapVar(3), 8)
    SetValue(MapVar(4), 8)
end)

RegisterEvent(122, "Legacy event 122", function()
    if IsQBitSet(QBit(1250)) then -- NPC
        evt.SetSprite(347, 1, "ped05")
    end
end)

RegisterEvent(219, "Legacy event 219", function()
    SetValue(MapVar(11), 0)
end)

RegisterEvent(220, "Drink from Fountain of Magic", function()
    if IsQBitSet(QBit(1135)) then -- Drink from the Fountain of Magic and return to Lord Albert Newton in Mist. - NPC
        evt.SetNPCTopic(790, 1, 1371) -- Albert Newton topic 1: Wizards
        SetQBit(QBit(1260)) -- NPC
    end
    if not IsAtLeast(MaxSpellPoints, 0) then
        AddValue(CurrentSpellPoints, 20)
        evt.StatusText("+20 Spell points restored.")
        SetAutonote(400)
        return
    end
    evt.StatusText("Refreshing!")
    SetAutonote(400)
end, "Drink from Fountain of Magic")

RegisterEvent(221, "Pedestal", function()
    if not HasItem(2074) then return end -- Dragon Statuette
    RemoveItem(2074) -- Dragon Statuette
    evt.SetSprite(347, 1, "ped05")
    SetQBit(QBit(1250)) -- NPC
    if not IsQBitSet(QBit(1247)) then return end -- NPC
    if not IsQBitSet(QBit(1248)) then return end -- NPC
    if not IsQBitSet(QBit(1249)) then return end -- NPC
    if IsQBitSet(QBit(1246)) then -- NPC
        evt.MoveNPC(872, 0) -- Twillen -> removed
        evt.MoveNPC(826, 1342) -- Twillen -> house 1342
    end
end, "Pedestal")

RegisterEvent(223, "Obelisk", function()
    evt.SimpleMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            d_re_e_Hpfotyhz_")
    SetQBit(QBit(1394)) -- NPC
    SetAutonote(452) -- Obelisk Message # 11: d_re_e_Hpfotyhz_
end, "Obelisk")

RegisterEvent(261, "Shrine of Might", function()
    if not IsAtLeast(MonthIs, 0) then
        evt.StatusText("You pray at the shrine.")
        return
    end
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1231)) then -- NPC
            SetQBit(QBit(1231)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(BaseMight, 10)
            evt.StatusText("+10 Might permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(BaseMight, 3)
        evt.StatusText("+3 Might permanent")
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Might")

