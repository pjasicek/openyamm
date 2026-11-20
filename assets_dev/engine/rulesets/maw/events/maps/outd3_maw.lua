-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- The stat shrine prays in any month, while The Seer's Pilgrimage has not been paid out (MAPS_CONTENT.md §3.1).
ReplaceMapEvent(261, "Shrine of Electricity", function()
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1239)) then -- NPC
            SetQBit(QBit(1239)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(AirResistance, 10)
            evt.StatusText("+10 Electricity resistance permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(AirResistance, 3)
        evt.StatusText("+3 Electricity resistance permanent")
        return
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Electricity")
