-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- The stat shrine prays in any month, while The Seer's Pilgrimage has not been paid out (MAPS_CONTENT.md §3.1).
ReplaceMapEvent(261, "Shrine of Cold", function()
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

ReplaceMapEvent(262, "Shrine of Fire", function()
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

-- The southern well trades 5000 gold for 5000 experience that MAW does not scale, and fills again each game month
-- although the town no longer refills (§3.1).
ReplaceMapEvent(101, "Drink from Well.", function()
    if not IsAtLeast(MapVar(2), 1) or not IsAtLeast(Gold, 5000) then
        evt.StatusText("Refreshing!")
        return
    end
    SubtractValue(Gold, 5000)
    evt.SetUnscaledExperience(true)
    AddValue(Experience, 5000)
    evt.SetUnscaledExperience(false)
    SubtractValue(MapVar(2), 1)
    evt.StatusText("\"+5000 Experience, -5000 Gold.\"")
    SetAutonote(434) -- 5000 Experience and minus 5000 gold from the southern well in the town of Kriegspire.
end, "Drink from Well.")

RegisterMapOnLoadEvent(60001, "MAW well refill", function()
    local month = math.floor(CurrentGameMinutes() / (60 * 24 * 28))
    if evt.GetMapVar("MawWellMonth", -1) ~= month then
        evt.SetMapVar("MawWellMonth", month)
        SetValue(MapVar(2), 10)
    end
end)
