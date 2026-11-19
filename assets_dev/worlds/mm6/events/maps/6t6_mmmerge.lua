-- MMMerge map supplement: Supreme Temple of Baa memory crystal pickup and earth shrine reward.

ReplaceMapEvent(32, "Oracle Memory Crystal", function()
    if IsQBitSet(QBit(1077)) then return end -- 53 T6, Given when characters take the Oracle Crystal from the altar.
    SetQBit(QBit(1077)) -- 53 T6, Given when characters take the Oracle Crystal from the altar.
    evt.SetMessage("Exit")
    evt.SetSprite(132, 1, "crysdisc")
    AddValue(InventoryItem(2170), 2170) -- Memory Crystal Alpha
    SetQBit(QBit(1215)) -- Quest item bits for seer
end, "Oracle Memory Crystal")

-- The legacy event grants fire resistance despite this being the earth shrine.
-- Use the merged resistance system rather than the unused MM6 magic resistance stat.
ReplaceMapEvent(46, "Shrine of Earth", function()
    if IsQBitSet(QBit(1345)) then return end
    if not IsQBitSet(QBit(1339)) or not IsQBitSet(QBit(1340)) or not IsQBitSet(QBit(1341)) then
        evt.StatusText("You're not worthy!")
        return
    end

    AddValue(EarthResistance, 10)
    SetQBit(QBit(1345))
    evt.StatusText("+10 Earth resistance permanent.")
end, "Shrine of Earth")
