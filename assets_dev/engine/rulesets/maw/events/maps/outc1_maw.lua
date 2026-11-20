-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- The stat shrine prays in any month, while The Seer's Pilgrimage has not been paid out (MAPS_CONTENT.md §3.1).
ReplaceMapEvent(261, "Shrine of Endurance", function()
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1234)) then -- NPC
            SetQBit(QBit(1234)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(BaseEndurance, 10)
            evt.StatusText("+10 Endurance permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(BaseEndurance, 3)
        evt.StatusText("+3 Endurance permanent")
        return
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Endurance")
