-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- Merchant Guildhouse: once Overdune's own quest is done (QBit 63), entering reports the witness to Bastian Loudrin
-- and starts the alliance quests without Overdune in the party (Maps/out03.lua:1-25).
ReplaceMapEvent(197, "Merchant Guildhouse", function()
    if not IsQBitSet(QBit(59)) and IsQBitSet(QBit(63)) then -- witness reported; Overdune's quest done
        evt.ShowMovie("\"overrept\"", true)
        evt.SetNPCTopic(5, 0, 43) -- Bastian Loudrin topic 0: Quest
        evt.SetNPCGreeting(5, 15) -- Bastian Loudrin greeting: We have identified those we believe would join...
        evt.ForPlayer(Players.All)
        AddValue(Experience, 10000)
        SetAward(Award(5)) -- Found a witness to the cataclysm in the Ironsand Desert.
        AddValue(History(6), 0)
        evt.ForPlayer(Players.Current)
        ClearQBit(QBit(25)) -- Find a witness to the lake of fire's formation.
        SetQBit(QBit(13)) -- Form an alliance among the major factions of Jadame.
        SetQBit(QBit(14)) -- Form an alliance with the Necromancers' Guild in Shadowspire.
        SetQBit(QBit(15)) -- Form an alliance with the Temple of the Sun in Murmurwoods.
        SetQBit(QBit(16)) -- Form an alliance with the Dragon hunters of Garrote Gorge.
        SetQBit(QBit(17)) -- Form an alliance with the Dragons of Garrote Gorge.
        SetQBit(QBit(18)) -- Form an alliance with the Minotaurs of Ravage Roaming.
        SetQBit(QBit(59)) -- Returned to the Merchant guild in Alvar with overdune. Quest 25 done.
        AddValue(Gold, 4000)
        evt.SetNPCTopic(13, 0, 65) -- Masul topic 0: Alliance
    end
    evt.EnterHouse(773) -- Merchant Guildhouse
end, "Merchant Guildhouse")
