-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- The wine rack gives MAW's potions (Cure Disease, Heroism, Bless, Cure Weakness, Might Boost) instead of the MM7
-- reagents, with the same odds (§3.2).
ReplaceMapEvent(196, "Wine Rack", function()
    if IsAtLeast(MapVar(6), 2) then return end
    local randomStep = PickRandomOption(196, 2, {2, 2, 12, 12, 13, 14})
    if randomStep == 2 then
        local itemStep = PickRandomOption(196, 3, {3, 5, 7, 9, 11, 12})
        if itemStep == 3 then
            AddValue(InventoryItem(225), 225)
        elseif itemStep == 5 then
            AddValue(InventoryItem(229), 229)
        elseif itemStep == 7 then
            AddValue(InventoryItem(230), 230)
        elseif itemStep == 9 then
            AddValue(InventoryItem(224), 224)
        elseif itemStep == 11 then
            AddValue(InventoryItem(240), 240)
        end
        if PickRandomOption(196, 13, {13, 13, 13, 13, 14, 14}) == 13 then
            AddValue(MapVar(6), 1)
        end
    elseif randomStep == 12 then
        if PickRandomOption(196, 13, {13, 13, 13, 13, 14, 14}) == 13 then
            AddValue(MapVar(6), 1)
        end
    elseif randomStep == 13 then
        AddValue(MapVar(6), 1)
    end
end, "Wine Rack")
