-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- The stat shrine prays in any month, while The Seer's Pilgrimage has not been paid out (MAPS_CONTENT.md §3.1).
ReplaceMapEvent(261, "Shrine of Magic", function()
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1242)) then -- NPC
            SetQBit(QBit(1242)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(FireResistance, 10)
            evt.StatusText("+10 Magic permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(FireResistance, 3)
        evt.StatusText("+3 Magic permanent")
        return
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Magic")
