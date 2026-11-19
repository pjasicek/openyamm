-- MMMerge supplement: Erathia transport and scavenger advertisement triggers.

RegisterMapOnLoadEvent(65005, "MMMerge Erathia contest transport", function()
    if IsQBitSet(QBit(519)) then -- Finished Scavenger Hunt
        evt.SetTransportRouteOverride(462, 4, {
            destinationName = "The Bracada Desert",
            mapFileName = "7Out06.odm",
            daysAvailable = {false, false, true, false, false, false, false},
            travelDays = 6,
            x = 19171,
            y = -19722,
            z = 193,
            directionDegrees = 180,
        })
    else
        evt.SetTransportRouteOverride(462, 4, {
            destinationName = "Emerald Island",
            mapFileName = "7Out01.odm",
            daysAvailable = {false, false, true, false, false, false, false},
            travelDays = 6,
            x = 12552,
            y = 800,
            z = 193,
            directionDegrees = 90,
        })
    end
end)

-- QBit 569 records completion of the Erathian obelisk puzzle. Reapply its
-- finished geometry on load for saves without outdoor facet deltas.
RegisterMapOnLoadEvent(65006, "Restore Erathian obelisk state", function()
    if not IsQBitSet(QBit(569)) then
        return
    end

    evt.SetFacetBit(16, FacetBits.Untouchable, 1)
    evt.SetFacetBit(17, FacetBits.Invisible, 0)
    evt.SetFacetBit(16, FacetBits.Invisible, 1)
end)

-- Repair older Erathia snapshots that still hide Quixote after the Crusader quest.
AppendMapEvent(86, function()
    if (IsQBitSet(QBit(1590)) or IsQBitSet(QBit(1591))) and not IsQBitSet(QBit(534)) then
        RemoveFollowerNpc(356)
    end
end)

RegisterMapTimerEvent(65004, 180, function()
    MM7.GiveScavengerAdvertisementIfNear(-10511, 6119, false)
end, "MMMerge Erathia scavenger advertisement")
