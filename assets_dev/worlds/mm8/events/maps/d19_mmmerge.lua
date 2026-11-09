-- MMMerge supplement: Dyson checks are relaxed for invisibility and transformer completion.

-- OpenYAMM: the guild's Skeleton Archers (faction 58, monsters 172-174) start peaceful toward the party, like the
-- necromancers and vampires beside them, though hostile.txt has them hostile. All of them spawn in actor group 10, so
-- the guild's own hostility events (the transformer room door, forcing the inner doors, QBit 20 or 229 on load) still
-- turn them hostile with the rest of the guild.
SetLocalFactionRelations({
    {58, 0, 0},
})

local function applySkeletonTransformerDestroyedState()
    evt.SetFacetBit(30, FacetBits.Untouchable, 1)
    evt.SetFacetBit(30, FacetBits.Invisible, 1)
end

ReplaceMapEvent(15, "Door", function()
    if IsQBitSet(QBit(20)) -- Allied with Temple of the Sun. Destroy the Skeleton Transformer done.
        or IsQBitSet(QBit(19)) -- Allied with Necromancers Guild. Steal Nightshade Brazier done.
        or HasPlayer(34) then
        evt.SetDoorState(5, DoorAction.Open)
        return
    end

    if IsInvisible() then
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    end

    evt.SetNPCGreeting(45, 107)
    evt.SpeakNPC(45)
end, "Door")

ReplaceMapEvent(131, nil, function()
    if IsQBitSet(QBit(27)) -- Skeleton Transformer Destroyed.
        or not IsQBitSet(QBit(26)) -- Destroy the skeleton transformer and return to Oskar Tyre.
        or not IsAtLeast(MapVar(21), 15) then
        return
    end

    SetQBit(QBit(27)) -- Skeleton Transformer Destroyed.
    evt.ShowMovie("skeltrans", true)
    applySkeletonTransformerDestroyedState()
end)

RegisterMapOnLoadEvent(901, "Restore skeleton transformer state", function()
    if IsQBitSet(QBit(27)) then -- Skeleton Transformer Destroyed.
        applySkeletonTransformerDestroyedState()
    end
end)
