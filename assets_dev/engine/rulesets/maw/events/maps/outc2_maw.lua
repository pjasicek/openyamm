-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- The stat shrine prays in any month, while The Seer's Pilgrimage has not been paid out (MAPS_CONTENT.md §3.1).
ReplaceMapEvent(261, "Shrine of Accuracy", function()
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1235)) then -- NPC
            SetQBit(QBit(1235)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(BaseAccuracy, 10)
            evt.StatusText("+10 Accuracy permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(BaseAccuracy, 3)
        evt.StatusText("+3 Accuracy permanent")
        return
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Accuracy")
