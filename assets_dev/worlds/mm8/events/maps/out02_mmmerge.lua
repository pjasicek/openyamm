-- MMMerge supplement: Escaton's Crystal can be reused after the Conflux Key opened it once.

-- Ravenshore's fountain: MM8's (out02.evt event 104: Ravenshore's Town Portal, and 200 gold, twice, to a party with
-- less than 100 in hand and in the bank), which also opens the dimensional travel as MMerge's did (without its Verdant
-- quest gate; the user, 2026-11-09).
RegisterEvent(104, "Drink from the fountain", function()
    if not IsQBitSet(QBit(302)) then -- Ravenshore Town Portal
        SetQBit(QBit(302)) -- Ravenshore Town Portal
    end
    if IsAtLeast(MapVar(29), 2) or IsAtLeast(Gold, 199) or IsAtLeast(BankGold, 99) then
        evt.StatusText("Refreshing")
    else
        AddValue(MapVar(29), 1)
        AddValue(Gold, 200)
        SetAutonote(211) -- Fountain in the city of Ravenshore gives 200 gold if the party and bank hold less than 100.
    end
    evt.OpenDimensionDoor()
end, "Drink from the fountain")

ReplaceMapEvent(504, "Enter Escaton's Crystal", function()
    evt.ForPlayer(Players.All)

    if HasItem(610) or MM8.GetMapFlag("CrystalOpened") then
        MM8.SetMapFlag("CrystalOpened", true)
        evt.ForPlayer(Players.Current)
        evt.MoveToMap(-1024, -1626, 0, 520, 0, 0, 355, 1, "d10.blv")
        return
    end

    evt.ForPlayer(Players.Current)
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Enter Escaton's Crystal")

-- The dimensional travel pedestal and its orb (../../maps/out02_dimensional_travel.scene.yml): the four continents'
-- portals.
RegisterEvent(1777, "Dimensional Travel", function()
    evt.OpenDimensionDoor()
end, "Dimensional Travel")
