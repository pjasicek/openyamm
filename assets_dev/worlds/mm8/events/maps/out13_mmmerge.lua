-- MMMerge supplement: the cannon can be fired again after the Regnan fleet is already sunk.

ReplaceMapEvent(451, "Fire the cannon !", function()
    evt.ForPlayer(Players.All)

    if HasItem(662) then
        RemoveItem(662)
        evt.ForPlayer(Players.Current)
        evt.StatusText("You hear a low rumbling noise")
        SetValue(MapVar(41), 1)
        evt.PlaySound(473, -12945, 12015)
        ClearQBit(QBit(224)) -- Cannonball of Dominion - I lost it
        return
    end

    evt.ForPlayer(Players.Current)
    evt.StatusText("You do not see the right kind of ammunition anywhere")
end, "Fire the cannon !")

-- QBit 37 records that the Regnan fleet was sunk. Reapply the resulting cannon
-- geometry on load for saves without outdoor facet deltas.
RegisterMapOnLoadEvent(901, "Restore Regnan cannon state", function()
    if not IsQBitSet(QBit(37)) then
        return
    end

    evt.SetFacetBit(31, FacetBits.Invisible, 0)
    evt.SetFacetBit(31, FacetBits.Untouchable, 0)
    evt.SetFacetBit(30, FacetBits.Invisible, 1)
    evt.SetFacetBit(30, FacetBits.Untouchable, 1)
end)

RegisterMapTimerEvent(452, 60, function()
    if not IsAtLeast(MapVar(41), 1) then
        return
    end

    if IsAtLeast(MapVar(41), 3) then
        if not IsQBitSet(QBit(37)) then -- Regnan Pirate Fleet is sunk.
            SetQBit(QBit(37)) -- Regnan Pirate Fleet is sunk.
            evt.MoveNPC(64, 899)
            evt.MoveNPC(20, 900)
            evt.MoveNPC(21, 900)
            AddValue(History(13), 0)
            evt.SetFacetBit(31, FacetBits.Invisible, 0)
            evt.SetFacetBit(31, FacetBits.Untouchable, 0)
            evt.SetFacetBit(30, FacetBits.Invisible, 1)
            evt.SetFacetBit(30, FacetBits.Untouchable, 1)
        end

        SetValue(MapVar(41), 0)
        return
    end

    if IsAtLeast(MapVar(41), 2) then
        AddValue(MapVar(41), 1)
        local meteorTargets = {
            {-19692, 14204},
            {-16984, 15783},
            {-12333, 18364},
            {-13102, 20346},
            {-15489, 18406},
            {-19300, 18374},
            {-17229, 20297},
            {-13235, 20616},
            {-16787, 13839},
            {-12748, 14383},
            {-15107, 13092},
        }

        for _, target in ipairs(meteorTargets) do
            evt.CastSpell(9, 3, 4, target[1], target[2], 4000, target[1], target[2], 0)
        end

        local lightningTargets = {
            {-16984, 15783},
            {-12333, 18364},
            {-13102, 20346},
            {-15489, 18406},
            {-19300, 18374},
            {-17229, 20297},
            {-13235, 20616},
        }

        for _, target in ipairs(lightningTargets) do
            evt.CastSpell(18, 3, 4, target[1], target[2], 4000, target[1], target[2], 0)
        end

        evt.CastSpell(43, 3, 4, -13312, 12864, 2432, -15743, 15989, 2731)
        evt.CastSpell(43, 3, 4, -13312, 12864, 2432, -12022, 19402, 2728)
        evt.CastSpell(43, 3, 4, -13312, 12864, 2432, -13168, 15608, 2725)
        evt.CastSpell(43, 3, 4, -13312, 12864, 2432, -14622, 15778, 2724)
        return
    end

    evt.CastSpell(6, 3, 4, -13312, 12864, 2432, -13371, 13740, 2793)
    evt.CastSpell(6, 3, 4, -13312, 12864, 2432, -13600, 13740, 2793)
    evt.CastSpell(6, 3, 4, -13312, 12864, 2432, -13250, 13740, 2793)
    evt.CastSpell(6, 3, 4, -13312, 12864, 2432, -13371, 13600, 2793)
    evt.CastSpell(6, 3, 4, -13312, 12864, 2432, -13371, 13820, 3000)
    evt.CastSpell(6, 3, 4, -13312, 12864, 2432, -13371, 13740, 2250)
    evt.CastSpell(6, 3, 4, -13312, 12864, 2432, -13371, 13800, 2500)
    evt.CastSpell(6, 3, 4, -13312, 12864, 2432, -13100, 13740, 3000)
    AddValue(MapVar(41), 1)
    evt._SpecialJump(16778952, 208)
    evt.PlaySound(472, -13305, 12958)
end)
