-- MMMerge map supplement: the Crypt of Korbu.

-- The Sarcophagus of Korbu is found once per game (devdocs/maw/MAPS_CONTENT.md §3.3): the base guard, QBit 81, is set
-- only while the party holds items 612 and 627, so a refilled crypt gave a second sarcophagus.
ReplaceMapEvent(131, nil, function()
    if IsQBitSet(QBit(81)) or evt.GetGlobalVar("SarcophagusFound", 0) ~= 0 then return end
    evt.SetFacetBit(10, FacetBits.Invisible, 1)
    evt.SetFacetBit(10, FacetBits.Untouchable, 1)
    AddValue(InventoryItem(612), 612) -- Sarcophagus of Korbu
    SetValue(MapVar(11), 1)
    SetQBit(QBit(211)) -- Sarcophagus of Korbu - I lost it
    evt.SetGlobalVar("SarcophagusFound", 1)
end)
