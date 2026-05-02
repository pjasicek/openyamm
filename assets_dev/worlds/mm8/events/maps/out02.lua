-- Ravenshore
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 2, 3, 4},
    onLeave = {6, 7, 8, 9, 10},
    openedChestIds = {
    [81] = {0},
    [82] = {1},
    [83] = {2},
    [84] = {3},
    [85] = {4},
    [86] = {5},
    [87] = {6},
    [88] = {7},
    [89] = {8},
    [90] = {9},
    [91] = {10},
    [92] = {11},
    [93] = {12},
    [94] = {13},
    [95] = {14},
    [96] = {15},
    [97] = {16},
    [98] = {17},
    [99] = {18},
    [100] = {19},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 131, repeating = true, intervalGameMinutes = 7.5, remainingGameMinutes = 7.5 },
    { eventId = 132, repeating = true, intervalGameMinutes = 10, remainingGameMinutes = 10 },
    { eventId = 478, repeating = true, intervalGameMinutes = 7.5, remainingGameMinutes = 7.5 },
    { eventId = 479, repeating = true, intervalGameMinutes = 10, remainingGameMinutes = 10 },
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsQBitSet(QBit(93)) then return end -- You have entered out02.odm, this is your new starting place
    SetQBit(QBit(93)) -- You have entered out02.odm, this is your new starting place
    ClearQBit(QBit(212)) -- Power Stone - I lost it
    ClearQBit(QBit(213)) -- Power Stone - I lost it
end)

RegisterEvent(2, "Legacy event 2", function()
    if not IsQBitSet(QBit(10)) then -- Letter from Q Bit 9 delivered.
        evt.SetFacetBit(10, FacetBits.Invisible, 1)
        evt.SetFacetBit(10, FacetBits.Untouchable, 1)
        evt.SetFacetBit(12, FacetBits.Untouchable, 1)
        return
    end
    evt.SetFacetBit(10, FacetBits.Invisible, 0)
    evt.SetFacetBit(10, FacetBits.Untouchable, 0)
    evt.SetFacetBit(12, FacetBits.Untouchable, 0)
end)

RegisterEvent(3, "Legacy event 3", function()
    if IsQBitSet(QBit(228)) then -- You have seen the Endgame movie
        evt.SetFacetBit(30, FacetBits.Untouchable, 1)
        evt.SetFacetBit(30, FacetBits.Invisible, 1)
        return
    elseif IsQBitSet(QBit(56)) then -- All Lords from quests 48, 50, 52, 54 rescued.
        SetQBit(QBit(228)) -- You have seen the Endgame movie
        AddValue(History(20), 0)
        evt.ShowMovie("wingame", true)
        evt.SetNPCTopic(40, 1, 115) -- Elgar Fellmoon topic 1: Merchant House
        evt.SetNPCGreeting(40, 38) -- Elgar Fellmoon greeting: Hail, heroes of Jadame! I'm glad you’ve returned. I want to make it clear that the merchant guild has made this guildhouse permanently open to you. Now that the crisis is over, the other council members have returned home. Though they are gone, good will prevails between us. The beginning of a new era of peace? We will see. Certainly it is a time of prosperity! Our caravans are already back in operation.
        evt.SetNPCTopic(55, 0, 143) -- Masul topic 0: Keys to the City
        evt.MoveNPC(55, 755) -- Masul -> Minotaur Leader's Room
        evt.SetNPCGreeting(55, 42) -- Masul greeting: How good of you to grace us with your presence. Heroes of Jadame. Saviors of Balthazar Lair. Both fitting titles for you who have done so much for me herd and for all of Jadame!
        if not IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
            evt.SetNPCTopic(52, 0, 122) -- Sir Charles Quixote topic 0: Dragon Hunting
            evt.SetNPCGreeting(52, 39) -- Sir Charles Quixote greeting: Ah well, very good to see you. Quite a lot of trouble is behind us, no? What brings the "Heroes of Jadame" to my camp?
            evt.MoveNPC(52, 753) -- Sir Charles Quixote -> Charles Quixote's House
            evt.MoveNPC(51, 0) -- Garret Deverro -> removed
            if not IsQBitSet(QBit(19)) then -- Allied with Necromancers Guild. Steal Nightshade Brazier done.
                evt.SetNPCTopic(54, 0, 136) -- Oskar Tyre topic 0: Servants of the Light
                evt.SetNPCGreeting(54, 41) -- Oskar Tyre greeting: The Light has shined upon us indeed. Our temple is always open to the "Heroes of Jadame." How may I help you?
                evt.MoveNPC(54, 214) -- Oskar Tyre -> Temple of the Sun Leader Room
                evt.SetNPCTopic(19, 0, 0) -- Xanthor topic 0 cleared
                evt.SetNPCTopic(19, 1, 157) -- Xanthor topic 1: Leaving
                evt.SetNPCGreeting(19, 47) -- Xanthor greeting: You have conducted yourselves greatly. I must say I had my doubts about your abilities, but no longer. You are truly worthy of the praise that all lavish upon you.
                evt.SetNPCGroupNews(1, 10) -- NPC group 1 "Peasants on Main Island of Dagger Wound" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(3, 10) -- NPC group 3 "Peasants on smaller islands of Dagger Wound" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(5, 10) -- NPC group 5 "Peasants in Ravenshore city" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(6, 10) -- NPC group 6 "Peasants in Ravenshore city" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(7, 10) -- NPC group 7 "Peasants in Ravenshore city" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(16, 10) -- NPC group 16 "Peasants in Alvar" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(17, 10) -- NPC group 17 "Peasants in Alvar" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(18, 10) -- NPC group 18 "Peasants in Alvar" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(19, 10) -- NPC group 19 "Trolls in Ironsand/Rust" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(20, 10) -- NPC group 20 "Trolls in Ironsand/Rust" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(21, 10) -- NPC group 21 "Trolls in Ironsand/Rust" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(25, 10) -- NPC group 25 "Peasants in Shadowspire" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(26, 10) -- NPC group 26 "Peasants in Shadowspire" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(27, 10) -- NPC group 27 "Peasants in Shadowspire" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(28, 10) -- NPC group 28 "Peasants in Murmurwoods" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(29, 10) -- NPC group 29 "Peasants in Murmurwoods" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(30, 10) -- NPC group 30 "Ogres in Ravage Roaming by Zog's fort" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(31, 10) -- NPC group 31 "Ogres in Ravage Roaming by boat dock" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(32, 10) -- NPC group 32 "Peasant Pirates of Regna" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(33, 10) -- NPC group 33 "Peasant Pirates of Regna" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(34, 10) -- NPC group 34 "Peasant Pirates of Regna" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.SetNPCGroupNews(35, 10) -- NPC group 35 "Peasant Minotaurs in Balzathar Lair" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
                evt.ForPlayer(Players.All)
                AddValue(Experience, 100000)
                ClearQBit(QBit(220)) -- Ring of Keys - I lost it
                evt.MoveNPC(20, 0) -- Queen Catherine -> removed
                evt.MoveNPC(21, 0) -- King Roland -> removed
                evt.SetFacetBit(30, FacetBits.Untouchable, 1)
                evt.SetFacetBit(30, FacetBits.Invisible, 1)
                return
            end
            evt.SetNPCTopic(56, 0, 150) -- Sandro topic 0: Safety
            evt.SetNPCGreeting(56, 43) -- Sandro greeting: Hail! In the name of the guild, I welcome you. Know that we consider you our friends, Heroes of Jadame. What would you have of us today?
            evt.MoveNPC(56, 213) -- Sandro -> Sandro/Thant's Throne Room
            evt.MoveNPC(63, 0) -- Thant -> removed
            evt.SetNPCTopic(19, 0, 0) -- Xanthor topic 0 cleared
            evt.SetNPCTopic(19, 1, 157) -- Xanthor topic 1: Leaving
            evt.SetNPCGreeting(19, 47) -- Xanthor greeting: You have conducted yourselves greatly. I must say I had my doubts about your abilities, but no longer. You are truly worthy of the praise that all lavish upon you.
            evt.SetNPCGroupNews(1, 10) -- NPC group 1 "Peasants on Main Island of Dagger Wound" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(3, 10) -- NPC group 3 "Peasants on smaller islands of Dagger Wound" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(5, 10) -- NPC group 5 "Peasants in Ravenshore city" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(6, 10) -- NPC group 6 "Peasants in Ravenshore city" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(7, 10) -- NPC group 7 "Peasants in Ravenshore city" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(16, 10) -- NPC group 16 "Peasants in Alvar" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(17, 10) -- NPC group 17 "Peasants in Alvar" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(18, 10) -- NPC group 18 "Peasants in Alvar" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(19, 10) -- NPC group 19 "Trolls in Ironsand/Rust" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(20, 10) -- NPC group 20 "Trolls in Ironsand/Rust" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(21, 10) -- NPC group 21 "Trolls in Ironsand/Rust" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(25, 10) -- NPC group 25 "Peasants in Shadowspire" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(26, 10) -- NPC group 26 "Peasants in Shadowspire" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(27, 10) -- NPC group 27 "Peasants in Shadowspire" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(28, 10) -- NPC group 28 "Peasants in Murmurwoods" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(29, 10) -- NPC group 29 "Peasants in Murmurwoods" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(30, 10) -- NPC group 30 "Ogres in Ravage Roaming by Zog's fort" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(31, 10) -- NPC group 31 "Ogres in Ravage Roaming by boat dock" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(32, 10) -- NPC group 32 "Peasant Pirates of Regna" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(33, 10) -- NPC group 33 "Peasant Pirates of Regna" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(34, 10) -- NPC group 34 "Peasant Pirates of Regna" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(35, 10) -- NPC group 35 "Peasant Minotaurs in Balzathar Lair" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.ForPlayer(Players.All)
            AddValue(Experience, 100000)
            ClearQBit(QBit(220)) -- Ring of Keys - I lost it
            evt.MoveNPC(20, 0) -- Queen Catherine -> removed
            evt.MoveNPC(21, 0) -- King Roland -> removed
            evt.SetFacetBit(30, FacetBits.Untouchable, 1)
            evt.SetFacetBit(30, FacetBits.Invisible, 1)
            return
        end
        evt.SetNPCTopic(53, 0, 129) -- Deftclaw Redreaver topic 0: Great Deeds
        evt.SetNPCGreeting(53, 40) -- Deftclaw Redreaver greeting: Together we have done a great deed. I look forward to telling my heir the tale. How can I help you, heroes?
        evt.MoveNPC(53, 774) -- Deftclaw Redreaver -> Dragon Leader's Cavern
        if not IsQBitSet(QBit(19)) then -- Allied with Necromancers Guild. Steal Nightshade Brazier done.
            evt.SetNPCTopic(54, 0, 136) -- Oskar Tyre topic 0: Servants of the Light
            evt.SetNPCGreeting(54, 41) -- Oskar Tyre greeting: The Light has shined upon us indeed. Our temple is always open to the "Heroes of Jadame." How may I help you?
            evt.MoveNPC(54, 214) -- Oskar Tyre -> Temple of the Sun Leader Room
            evt.SetNPCTopic(19, 0, 0) -- Xanthor topic 0 cleared
            evt.SetNPCTopic(19, 1, 157) -- Xanthor topic 1: Leaving
            evt.SetNPCGreeting(19, 47) -- Xanthor greeting: You have conducted yourselves greatly. I must say I had my doubts about your abilities, but no longer. You are truly worthy of the praise that all lavish upon you.
            evt.SetNPCGroupNews(1, 10) -- NPC group 1 "Peasants on Main Island of Dagger Wound" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(3, 10) -- NPC group 3 "Peasants on smaller islands of Dagger Wound" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(5, 10) -- NPC group 5 "Peasants in Ravenshore city" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(6, 10) -- NPC group 6 "Peasants in Ravenshore city" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(7, 10) -- NPC group 7 "Peasants in Ravenshore city" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(16, 10) -- NPC group 16 "Peasants in Alvar" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(17, 10) -- NPC group 17 "Peasants in Alvar" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(18, 10) -- NPC group 18 "Peasants in Alvar" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(19, 10) -- NPC group 19 "Trolls in Ironsand/Rust" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(20, 10) -- NPC group 20 "Trolls in Ironsand/Rust" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(21, 10) -- NPC group 21 "Trolls in Ironsand/Rust" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(25, 10) -- NPC group 25 "Peasants in Shadowspire" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(26, 10) -- NPC group 26 "Peasants in Shadowspire" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(27, 10) -- NPC group 27 "Peasants in Shadowspire" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(28, 10) -- NPC group 28 "Peasants in Murmurwoods" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(29, 10) -- NPC group 29 "Peasants in Murmurwoods" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(30, 10) -- NPC group 30 "Ogres in Ravage Roaming by Zog's fort" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(31, 10) -- NPC group 31 "Ogres in Ravage Roaming by boat dock" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(32, 10) -- NPC group 32 "Peasant Pirates of Regna" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(33, 10) -- NPC group 33 "Peasant Pirates of Regna" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(34, 10) -- NPC group 34 "Peasant Pirates of Regna" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.SetNPCGroupNews(35, 10) -- NPC group 35 "Peasant Minotaurs in Balzathar Lair" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
            evt.ForPlayer(Players.All)
            AddValue(Experience, 100000)
            ClearQBit(QBit(220)) -- Ring of Keys - I lost it
            evt.MoveNPC(20, 0) -- Queen Catherine -> removed
            evt.MoveNPC(21, 0) -- King Roland -> removed
            evt.SetFacetBit(30, FacetBits.Untouchable, 1)
            evt.SetFacetBit(30, FacetBits.Invisible, 1)
            return
        end
        evt.SetNPCTopic(56, 0, 150) -- Sandro topic 0: Safety
        evt.SetNPCGreeting(56, 43) -- Sandro greeting: Hail! In the name of the guild, I welcome you. Know that we consider you our friends, Heroes of Jadame. What would you have of us today?
        evt.MoveNPC(56, 213) -- Sandro -> Sandro/Thant's Throne Room
        evt.MoveNPC(63, 0) -- Thant -> removed
        evt.SetNPCTopic(19, 0, 0) -- Xanthor topic 0 cleared
        evt.SetNPCTopic(19, 1, 157) -- Xanthor topic 1: Leaving
        evt.SetNPCGreeting(19, 47) -- Xanthor greeting: You have conducted yourselves greatly. I must say I had my doubts about your abilities, but no longer. You are truly worthy of the praise that all lavish upon you.
        evt.SetNPCGroupNews(1, 10) -- NPC group 1 "Peasants on Main Island of Dagger Wound" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(3, 10) -- NPC group 3 "Peasants on smaller islands of Dagger Wound" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(5, 10) -- NPC group 5 "Peasants in Ravenshore city" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(6, 10) -- NPC group 6 "Peasants in Ravenshore city" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(7, 10) -- NPC group 7 "Peasants in Ravenshore city" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(16, 10) -- NPC group 16 "Peasants in Alvar" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(17, 10) -- NPC group 17 "Peasants in Alvar" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(18, 10) -- NPC group 18 "Peasants in Alvar" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(19, 10) -- NPC group 19 "Trolls in Ironsand/Rust" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(20, 10) -- NPC group 20 "Trolls in Ironsand/Rust" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(21, 10) -- NPC group 21 "Trolls in Ironsand/Rust" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(25, 10) -- NPC group 25 "Peasants in Shadowspire" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(26, 10) -- NPC group 26 "Peasants in Shadowspire" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(27, 10) -- NPC group 27 "Peasants in Shadowspire" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(28, 10) -- NPC group 28 "Peasants in Murmurwoods" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(29, 10) -- NPC group 29 "Peasants in Murmurwoods" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(30, 10) -- NPC group 30 "Ogres in Ravage Roaming by Zog's fort" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(31, 10) -- NPC group 31 "Ogres in Ravage Roaming by boat dock" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(32, 10) -- NPC group 32 "Peasant Pirates of Regna" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(33, 10) -- NPC group 33 "Peasant Pirates of Regna" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(34, 10) -- NPC group 34 "Peasant Pirates of Regna" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.SetNPCGroupNews(35, 10) -- NPC group 35 "Peasant Minotaurs in Balzathar Lair" -> news 10: "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
        evt.ForPlayer(Players.All)
        AddValue(Experience, 100000)
        ClearQBit(QBit(220)) -- Ring of Keys - I lost it
        evt.MoveNPC(20, 0) -- Queen Catherine -> removed
        evt.MoveNPC(21, 0) -- King Roland -> removed
        evt.SetFacetBit(30, FacetBits.Untouchable, 1)
        evt.SetFacetBit(30, FacetBits.Invisible, 1)
        return
    else
        return
    end
end)

RegisterEvent(4, "Legacy event 4", function()
    if not IsQBitSet(QBit(58)) then -- The Pirates that invaded Ravenshore are all dead now )
        if IsQBitSet(QBit(6)) then -- Pirate Leader in Dagger Wound Pirate Outpost killed (quest given at Q Bit 5). Ends pirate/lizardman war on Dagger Wound. Shuts off pirate timer.
            if IsQBitSet(QBit(37)) then -- Regnan Pirate Fleet is sunk.
                evt.SetMonGroupBit(10, MonsterBits.Invisible, 1) -- actor group 10: Regnan Bandit, Regnan Brigadier, Regnan Pirate
                return
            elseif IsAtLeast(Counter(1), 1344) then
                evt.SetMonGroupBit(10, MonsterBits.Invisible, 0) -- actor group 10: Regnan Bandit, Regnan Brigadier, Regnan Pirate
                SetQBit(QBit(57)) -- The Pirates invaded Ravenshore
                SetValue(BankGold, 0)
            else
                evt.SetMonGroupBit(10, MonsterBits.Invisible, 1) -- actor group 10: Regnan Bandit, Regnan Brigadier, Regnan Pirate
            end
        return
        end
    end
    evt.SetMonGroupBit(10, MonsterBits.Invisible, 1) -- actor group 10: Regnan Bandit, Regnan Brigadier, Regnan Pirate
end)

RegisterNoOpEvent(6, "Legacy event 6")

RegisterNoOpEvent(7, "Legacy event 7")

RegisterNoOpEvent(8, "Legacy event 8")

RegisterNoOpEvent(9, "Legacy event 9")

RegisterNoOpEvent(10, "Legacy event 10")

RegisterEvent(11, "Wilburt's Hovel", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(508) -- Wilburt's Hovel
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Wilburt's Hovel")

RegisterEvent(12, "Wilburt's Hovel", nil, "Wilburt's Hovel")

RegisterEvent(13, "Jack's Hovel", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(762) -- Jack's Hovel
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Jack's Hovel")

RegisterEvent(14, "Jack's Hovel", nil, "Jack's Hovel")

RegisterEvent(15, "Iver's Estate", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(777) -- Iver's Estate
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Iver's Estate")

RegisterEvent(16, "Iver's Estate", nil, "Iver's Estate")

RegisterEvent(17, "Pederton Place", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(785) -- Pederton Place
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Pederton Place")

RegisterEvent(18, "Pederton Place", nil, "Pederton Place")

RegisterEvent(19, "Puddle's Hovel", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(793) -- Puddle's Hovel
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Puddle's Hovel")

RegisterEvent(20, "Puddle's Hovel", nil, "Puddle's Hovel")

RegisterEvent(21, "Forgewright Estate", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(796) -- Forgewright Estate
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Forgewright Estate")

RegisterEvent(22, "Forgewright Estate", nil, "Forgewright Estate")

RegisterEvent(23, "Apple Home", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(799) -- Apple Home
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Apple Home")

RegisterEvent(24, "Apple Home", nil, "Apple Home")

RegisterEvent(25, "Treblid's Home", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(805) -- Treblid's Home
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Treblid's Home")

RegisterEvent(26, "Treblid's Home", nil, "Treblid's Home")

RegisterEvent(27, "Holden's Hovel", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(814) -- Holden's Hovel
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Holden's Hovel")

RegisterEvent(28, "Holden's Hovel", nil, "Holden's Hovel")

RegisterEvent(29, "Aznog's Hovel", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(824) -- Aznog's Hovel
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Aznog's Hovel")

RegisterEvent(30, "Aznog's Hovel", nil, "Aznog's Hovel")

RegisterEvent(31, "Luodrin House", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(834) -- Luodrin House
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Luodrin House")

RegisterEvent(32, "Luodrin House", nil, "Luodrin House")

RegisterEvent(33, "Applebee Estate", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(844) -- Applebee Estate
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Applebee Estate")

RegisterEvent(34, "Applebee Estate", nil, "Applebee Estate")

RegisterEvent(35, "Archibald's Home", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(853) -- Archibald's Home
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Archibald's Home")

RegisterEvent(36, "Archibald's Home", nil, "Archibald's Home")

RegisterEvent(37, "Arius' House", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(861) -- Arius' House
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Arius' House")

RegisterEvent(38, "Arius' House", nil, "Arius' House")

RegisterEvent(39, "Deerhunter's House", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(867) -- Deerhunter's House
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Deerhunter's House")

RegisterEvent(40, "Deerhunter's House", nil, "Deerhunter's House")

RegisterEvent(41, "Townsaver Hall", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(871) -- Townsaver Hall
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Townsaver Hall")

RegisterEvent(42, "Townsaver Hall", nil, "Townsaver Hall")

RegisterEvent(43, "Jobber's Home", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(874) -- Jobber's Home
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Jobber's Home")

RegisterEvent(44, "Jobber's Home", nil, "Jobber's Home")

RegisterEvent(45, "Maylander's House", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(877) -- Maylander's House
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Maylander's House")

RegisterEvent(46, "Maylander's House", nil, "Maylander's House")

RegisterEvent(47, "Bluesawn Home", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(880) -- Bluesawn Home
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Bluesawn Home")

RegisterEvent(48, "Bluesawn Home", nil, "Bluesawn Home")

RegisterEvent(49, "Quicktongue Estate", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(883) -- Quicktongue Estate
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Quicktongue Estate")

RegisterEvent(50, "Quicktongue Estate", nil, "Quicktongue Estate")

RegisterEvent(51, "Laraselle Estate", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(886) -- Laraselle Estate
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Laraselle Estate")

RegisterEvent(52, "Laraselle Estate", nil, "Laraselle Estate")

RegisterEvent(53, "Hillsman Cottage", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(888) -- Hillsman Cottage
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Hillsman Cottage")

RegisterEvent(54, "Hillsman Cottage", nil, "Hillsman Cottage")

RegisterEvent(55, "Caverhill Estate", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(889) -- Caverhill Estate
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Caverhill Estate")

RegisterEvent(56, "Caverhill Estate", nil, "Caverhill Estate")

RegisterEvent(57, "Reaver's Home", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(890) -- Reaver's Home
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Reaver's Home")

RegisterEvent(58, "Reaver's Home", nil, "Reaver's Home")

RegisterEvent(59, "Temper Hall", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(891) -- Temper Hall
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Temper Hall")

RegisterEvent(60, "Temper Hall", nil, "Temper Hall")

RegisterEvent(61, "Putnam's Home", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(892) -- Putnam's Home
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Putnam's Home")

RegisterEvent(62, "Putnam's Home", nil, "Putnam's Home")

RegisterEvent(63, "Karrand's Cottage", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(893) -- Karrand's Cottage
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Karrand's Cottage")

RegisterEvent(64, "Karrand's Cottage", nil, "Karrand's Cottage")

RegisterEvent(65, "Lathius' Home", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(894) -- Lathius' Home
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Lathius' Home")

RegisterEvent(66, "Lathius' Home", nil, "Lathius' Home")

RegisterEvent(67, "Guild of Bounty Hunters", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(895) -- Guild of Bounty Hunters
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Guild of Bounty Hunters")

RegisterEvent(68, "Guild of Bounty Hunters", nil, "Guild of Bounty Hunters")

RegisterEvent(69, "Botham Hall", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(896) -- Botham Hall
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Botham Hall")

RegisterEvent(70, "Botham Hall", nil, "Botham Hall")

RegisterEvent(71, "Neblick's House", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(897) -- Neblick's House
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Neblick's House")

RegisterEvent(72, "Neblick's House", nil, "Neblick's House")

RegisterEvent(73, "Stonecleaver Hall", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(898) -- Stonecleaver Hall
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Stonecleaver Hall")

RegisterEvent(74, "Stonecleaver Hall", nil, "Stonecleaver Hall")

RegisterEvent(75, "Hostel", function()
    if IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    elseif IsQBitSet(QBit(286)) then -- Did the conflux key quest
        evt.EnterHouse(899) -- Hostel
        return
    else
        evt.ForPlayer(Players.All)
        if HasItem(606) and HasItem(607) and HasItem(608) and HasItem(609) then -- Heart of Fire
            evt.ShowMovie("\"confluxkey\"", true)
            evt.ForPlayer(Players.Current)
            RemoveItem(606) -- Heart of Fire
            RemoveItem(607) -- Heart of Water
            RemoveItem(608) -- Heart of Air
            RemoveItem(609) -- Heart of Earth
            AddValue(InventoryItem(610), 610) -- Conflux Key
            SetQBit(QBit(46)) -- Find the cause of the cataclysm through the Crystal Gateway. - Given by XANTHOR. Taken by Eschaton.
            ClearQBit(QBit(41)) -- Bring the Heart of Water from the Plane of Water to Xanthor. - Given by XANTHOR. Taken when 41-44 done simultaneously.
            ClearQBit(QBit(42)) -- Bring the Heart of Air from the Plane of Air to Xanthor. - Given by XANTHOR. Taken when 41-44 done simultaneously.
            ClearQBit(QBit(43)) -- Bring the Heart of Earth from the Plane of Earth to Xanthor. - Given by XANTHOR. Taken when 41-44 done simultaneously.
            ClearQBit(QBit(44)) -- Bring the Heart of Fire from the Plane of Fire to Xanthor. - Given by XANTHOR. Taken when 41-44 done simultaneously.
            SetQBit(QBit(45)) -- Quests 41-44 done. Items from 41-44 given to XANTHOR.
            evt.ForPlayer(Players.All)
            AddValue(Experience, 250000)
            SetAward(Award(13)) -- Built the Conflux Key.
            evt.SetNPCTopic(19, 0, 0) -- Xanthor topic 0 cleared
            evt.SetNPCTopic(19, 1, 0) -- Xanthor topic 1 cleared
            evt.SetNPCGreeting(19, 46) -- Xanthor greeting: There. It is built. Take this Conflux Key. As I have explained, it will allow you to use the crystal in the town square as a gateway--much as you've used the elemental gateways to reach the elemental planes. The crystal gateway will take you to the place between the planes.On this "Plane Between Planes" you must find the source of the cataclysm. What it is, I don't know, but whatever it is, it is there. Go now! The fate of the land, I'm afraid, lies on your shoulders. Be worthy of the task!
            evt.SetNPCTopic(40, 1, 113) -- Elgar Fellmoon topic 1: Plane Between Planes
            evt.SetNPCTopic(52, 0, 120) -- Sir Charles Quixote topic 0: Plane Between Planes
            evt.SetNPCTopic(53, 0, 127) -- Deftclaw Redreaver topic 0: Crystal Dragons
            evt.SetNPCTopic(54, 0, 134) -- Oskar Tyre topic 0: Source of the Crisis
            evt.SetNPCTopic(55, 0, 141) -- Masul topic 0: Iron Rations
            evt.SetNPCTopic(56, 0, 148) -- Sandro topic 0: Nightmares
            AddValue(History(17), 0)
            SetQBit(QBit(209)) -- Conflux Key - I lost it
            ClearQBit(QBit(205)) -- Heart of Fire - I lost it
            ClearQBit(QBit(206)) -- Heart of Water - I lost it
            ClearQBit(QBit(207)) -- Heart of Air - I lost it
            ClearQBit(QBit(208)) -- Heart of Earth - I lost it
            SetQBit(QBit(286)) -- Did the conflux key quest
        else
        end
        evt.EnterHouse(899) -- Hostel
        return
    end
end, "Hostel")

RegisterEvent(76, "Hostel", nil, "Hostel")

RegisterEvent(77, "Hostel", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(900) -- Hostel
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Hostel")

RegisterEvent(78, "Hostel", nil, "Hostel")

RegisterEvent(79, "Brigham's Home", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(901) -- Brigham's Home
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Brigham's Home")

RegisterEvent(80, "Brigham's Home", nil, "Brigham's Home")

RegisterEvent(81, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(82, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(83, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(84, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(85, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(86, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(87, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(88, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(89, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(90, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(91, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(92, "Tree", function()
    evt.OpenChest(11)
end, "Tree")

RegisterEvent(93, "Chest", function()
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(94, "Chest", function()
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(95, "Chest", function()
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(96, "Chest", function()
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(97, "Chest", function()
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(98, "Chest", function()
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(99, "Chest", function()
    evt.ForPlayer(Players.All)
    if not HasAward(Award(41)) then -- Arcomage Champion.
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    end
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(100, "The Vault of Time", function()
    evt.ForPlayer(Players.All)
    if HasItem(661) then -- Emperor Thorn's Key
        evt.OpenChest(19)
        RemoveItem(661) -- Emperor Thorn's Key
        SetValue(MapVar(3), 1)
        return
    elseif IsAtLeast(MapVar(3), 1) then
        evt.OpenChest(19)
        RemoveItem(661) -- Emperor Thorn's Key
        SetValue(MapVar(3), 1)
    else
        evt.FaceAnimation(FaceAnimation.DoorLocked)
    end
return
end, "The Vault of Time")

RegisterEvent(101, "Drink from the well", function()
    if not IsAtLeast(MightBonus, 25) then
        AddValue(MightBonus, 25)
        evt.StatusText("Might +25 (Temporary)")
        SetAutonote(210) -- Well in the city of Ravenshore gives a temporary Strength bonus of 25.
        return
    end
    evt.StatusText("Refreshing")
end, "Drink from the well")

RegisterEvent(102, "Drink from the well", function()
    evt.StatusText("That was not so refreshing")
    SetValue(PoisonedRed, 0)
end, "Drink from the well")

RegisterEvent(103, "Drink from the well", function()
    evt.StatusText("Refreshing")
end, "Drink from the well")

RegisterEvent(104, "Drink from the fountain", function()
    if not IsQBitSet(QBit(180)) then -- Ravenshore Town Portal
        SetQBit(QBit(180)) -- Ravenshore Town Portal
    end
    if IsAtLeast(MapVar(31), 2) then
        evt.StatusText("Refreshing")
        return
    elseif IsAtLeast(Gold, 199) then
        evt.StatusText("Refreshing")
        return
    elseif IsAtLeast(BankGold, 99) then
        evt.StatusText("Refreshing")
    else
        AddValue(MapVar(31), 1)
        AddValue(Gold, 200)
        SetAutonote(211) -- Fountain in the city of Ravenshore gives 200 gold if the total gold on party and in the bank is less than 100.
    end
return
end, "Drink from the fountain")

RegisterEvent(131, "Legacy event 131", function()
    if IsQBitSet(QBit(58)) then -- The Pirates that invaded Ravenshore are all dead now )
        return
    elseif IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        if evt.CheckMonstersKilled(ActorKillCheck.Group, 10, 0, true) then -- actor group 10: Regnan Bandit, Regnan Brigadier, Regnan Pirate; all matching actors defeated
            SetQBit(QBit(58)) -- The Pirates that invaded Ravenshore are all dead now )
            SetQBit(QBit(225)) -- dead questbit for internal use(bling)
            SetQBit(QBit(225)) -- dead questbit for internal use(bling)
            evt.StatusText("The Invaders have been defeated!")
            ClearQBit(QBit(57)) -- The Pirates invaded Ravenshore
        end
        return
    else
        return
    end
end)

RegisterEvent(132, "Legacy event 132", function()
    if IsQBitSet(QBit(140)) then return end -- Killed all Dire Wolves in Ravenshore
    if not evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 84, 0, false) then return end -- monster 84 "Dire Wolf Yearling"; all matching actors defeated
    if not evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 85, 0, false) then return end -- monster 85 "Dire Wolf"; all matching actors defeated
    if not evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 86, 0, false) then return end -- monster 86 "Pack Leader"; all matching actors defeated
    if not IsQBitSet(QBit(141)) then -- Dire Wolf Questbit for Riki
        SetQBit(QBit(141)) -- Dire Wolf Questbit for Riki
        evt.SummonMonsters(3, 1, 1, -18208, 16256, 8, 1, 0) -- encounter slot 3 "Dire Wolf" tier A, count 1, pos=(-18208, 16256, 8), actor group 1, no unique actor name
        evt.SetMonGroupBit(1, MonsterBits.Invisible, 1)
        return
    end
    SetQBit(QBit(140)) -- Killed all Dire Wolves in Ravenshore
    evt.StatusText("You have killed all of the Dire Wolves")
    SetQBit(QBit(225)) -- dead questbit for internal use(bling)
    ClearQBit(QBit(225)) -- dead questbit for internal use(bling)
end)

RegisterEvent(150, "Obelisk", function()
    if IsQBitSet(QBit(187)) then return end -- Obelisk Area 2
    evt.StatusText("ethesunsh")
    SetAutonote(14) -- Obelisk message #7: ethesunsh
    SetQBit(QBit(187)) -- Obelisk Area 2
end, "Obelisk")

RegisterEvent(171, "Keen Edge", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(2) -- Keen Edge
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Keen Edge")

RegisterEvent(172, "Keen Edge", nil, "Keen Edge")

RegisterEvent(173, "The Polished Shield", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(37) -- The Polished Shield
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "The Polished Shield")

RegisterEvent(174, "The Polished Shield", nil, "The Polished Shield")

RegisterEvent(175, "Needful Things", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(77) -- Needful Things
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Needful Things")

RegisterEvent(176, "Needful Things", nil, "Needful Things")

RegisterEvent(177, "Apothecary", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(111) -- Apothecary
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Apothecary")

RegisterEvent(178, "Apothecary", nil, "Apothecary")

RegisterEvent(179, "Vexation's Hexes", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(184) -- Vexation's Hexes
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Vexation's Hexes")

RegisterEvent(180, "Vexation's Hexes", nil, "Vexation's Hexes")

RegisterEvent(181, "Guild Caravans", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(452) -- Guild Caravans
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Guild Caravans")

RegisterEvent(182, "Guild Caravans", nil, "Guild Caravans")

RegisterEvent(183, "The Dauntless", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(480) -- The Dauntless
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "The Dauntless")

RegisterEvent(184, "The Dauntless", nil, "The Dauntless")

RegisterEvent(185, "Sanctum", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(304) -- Sanctum
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Sanctum")

RegisterEvent(186, "Sanctum", nil, "Sanctum")

RegisterEvent(187, "Gymnasium", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(1565) -- Gymnasium
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Gymnasium")

RegisterEvent(188, "Gymnasium", nil, "Gymnasium")

RegisterEvent(191, "Kessel's Kantina", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(229) -- Kessel's Kantina
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Kessel's Kantina")

RegisterEvent(192, "Kessel's Kantina", nil, "Kessel's Kantina")

RegisterEvent(193, "Steele's Vault", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(282) -- Steele's Vault
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Steele's Vault")

RegisterEvent(194, "Steele's Vault", nil, "Steele's Vault")

RegisterEvent(195, "Caori's Curios", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(83) -- Caori's Curios
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Caori's Curios")

RegisterEvent(196, "Caori's Curios", nil, "Caori's Curios")

RegisterEvent(197, "The Dancing Ogre", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(237) -- The Dancing Ogre
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "The Dancing Ogre")

RegisterEvent(198, "The Dancing Ogre", nil, "The Dancing Ogre")

RegisterEvent(199, "Wind", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(483) -- Wind
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Wind")

RegisterEvent(200, "Wind", nil, "Wind")

RegisterEvent(201, "Self Guild", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(186) -- Self Guild
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Self Guild")

RegisterEvent(202, "Self Guild", nil, "Self Guild")

RegisterEvent(203, "Oracle", function()
    evt.EnterHouse(757) -- Oracle
end, "Oracle")

RegisterEvent(204, "Oracle", nil, "Oracle")

RegisterEvent(209, "The Adventurer's Inn", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(1607) -- The Adventurer's Inn
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "The Adventurer's Inn")

RegisterEvent(210, "The Adventurer's Inn", nil, "The Adventurer's Inn")

RegisterEvent(401, "Smuggler's Cove", nil, "Smuggler's Cove")

RegisterEvent(402, "Dire Wolf Den", nil, "Dire Wolf Den")

RegisterEvent(403, "Merchant House of Alvar", nil, "Merchant House of Alvar")

RegisterEvent(404, "Escaton's Crystal", nil, "Escaton's Crystal")

RegisterEvent(405, "The Tomb of Lord Brinne", nil, "The Tomb of Lord Brinne")

RegisterEvent(406, "Chapel of Eep", nil, "Chapel of Eep")

RegisterEvent(407, "Sealed Crate", nil, "Sealed Crate")

RegisterEvent(408, "The Vault of Time", nil, "The Vault of Time")

RegisterEvent(449, "Fountain", nil, "Fountain")

RegisterEvent(450, "Well", nil, "Well")

RegisterEvent(451, "House Memoria", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(902) -- House Memoria
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "House Memoria")

RegisterEvent(452, "House Memoria", nil, "House Memoria")

RegisterEvent(453, "House of Hawthorne ", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(903) -- House of Hawthorne
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "House of Hawthorne ")

RegisterEvent(454, "House of Hawthorne ", nil, "House of Hawthorne ")

RegisterEvent(455, "Lott's Family Home", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(904) -- Lott's Family Home
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Lott's Family Home")

RegisterEvent(456, "Lott's Family Home", nil, "Lott's Family Home")

RegisterEvent(457, "House of Nosewort", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(905) -- House of Nosewort
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "House of Nosewort")

RegisterEvent(458, "House of Nosewort", nil, "House of Nosewort")

RegisterEvent(459, "Dotes Family Hovel", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(909) -- Dotes Family Hovel
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Dotes Family Hovel")

RegisterEvent(460, "Dotes Family Hovel", nil, "Dotes Family Hovel")

RegisterEvent(461, "Hall of the Tracker", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(906) -- Hall of the Tracker
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Hall of the Tracker")

RegisterEvent(462, "Hall of the Tracker", nil, "Hall of the Tracker")

RegisterEvent(463, "Hunter's Hovel", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(907) -- Hunter's Hovel
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Hunter's Hovel")

RegisterEvent(464, "Hunter's Hovel", nil, "Hunter's Hovel")

RegisterEvent(465, "Dervish's Cottage", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(908) -- Dervish's Cottage
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Dervish's Cottage")

RegisterEvent(466, "Dervish's Cottage", nil, "Dervish's Cottage")

RegisterEvent(467, "House Understone", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.EnterHouse(697) -- House Understone
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "House Understone")

RegisterEvent(468, "House Understone", nil, "House Understone")

RegisterEvent(478, "Legacy event 478", function()
    local randomStep = PickRandomOption(478, 2, {2, 2, 3, 3, 3, 3})
    if randomStep == 2 then
        evt.PlaySound(325, 17056, -12512)
    end
end)

RegisterEvent(479, "Legacy event 479", function()
    PickRandomOption(479, 2, {2, 4, 6, 8, 10, 12})
end)

RegisterEvent(490, "Tree", function()
    if evt.CheckItemsCount(DecorVar(23), 1) then
        evt.RemoveItems(DecorVar(23))
        AddValue(InventoryItem(220), 220) -- Potion Bottle
    end
end, "Tree")

RegisterEvent(491, "Legacy event 491", function()
    evt._SpecialJump(19661824, 220)
end)

RegisterEvent(492, "Legacy event 492", function()
    evt._SpecialJump(19662336, 220)
end)

RegisterEvent(493, "Legacy event 493", function()
    evt._SpecialJump(19660800, 220)
end)

RegisterEvent(494, "Door", function()
    evt.FaceAnimation(FaceAnimation.DoorLocked)
    evt.StatusText("The door is locked")
end, "Door")

RegisterEvent(495, "Tree", function()
    if IsQBitSet(QBit(272)) then -- Reagant spout area 2
        return
    elseif IsAtLeast(DisarmTrapSkill, 3) then
        local randomStep = PickRandomOption(495, 4, {5, 7, 9, 11, 13})
        if randomStep == 5 then
            evt.SummonItem(200, 1376, 5312, 126, 1000, 1, true) -- Fae dust
        elseif randomStep == 7 then
            evt.SummonItem(205, 1376, 5312, 126, 1000, 1, true) -- Vial of Ooze endoplasm
        elseif randomStep == 9 then
            evt.SummonItem(210, 1376, 5312, 126, 1000, 1, true) -- Yellow Potion
        elseif randomStep == 11 then
            evt.SummonItem(215, 1376, 5312, 126, 1000, 1, true) -- Green Potion
        elseif randomStep == 13 then
            evt.SummonItem(220, 1376, 5312, 126, 1000, 1, true) -- Blue and Orange Potion
        end
        SetQBit(QBit(272)) -- Reagant spout area 2
        return
    else
        return
    end
end, "Tree")

RegisterEvent(497, "Rock", function()
    if IsQBitSet(QBit(273)) then -- Reagant spout area 2
        return
    elseif IsAtLeast(DisarmTrapSkill, 7) then
        local randomStep = PickRandomOption(497, 4, {5, 7, 9, 11, 13, 15})
        if randomStep == 5 then
            evt.SummonItem(240, 11520, 14320, 992, 1000, 1, true) -- Sealed Letter
        elseif randomStep == 7 then
            evt.SummonItem(241, 11520, 14320, 992, 1000, 1, true) -- Sealed Letter
        elseif randomStep == 9 then
            evt.SummonItem(242, 11520, 14320, 992, 1000, 1, true) -- Sealed Letter
        elseif randomStep == 11 then
            evt.SummonItem(243, 11520, 14320, 992, 1000, 1, true) -- Sealed Letter
        elseif randomStep == 13 then
            evt.SummonItem(244, 11520, 14320, 992, 1000, 1, true) -- Sealed Letter
        elseif randomStep == 15 then
            evt.SummonItem(245, 11520, 14320, 992, 1000, 1, true) -- Lich Jar
        end
        SetQBit(QBit(273)) -- Reagant spout area 2
        return
    else
        return
    end
end, "Rock")

RegisterEvent(499, "Buoy", function()
    if IsQBitSet(QBit(274)) then return end -- Area 2 buoy
    if IsAtLeast(BaseLuck, 20) then
        SetQBit(QBit(274)) -- Area 2 buoy
        AddValue(SkillPoints, 5)
    end
end, "Buoy")

RegisterEvent(501, "Enter Smuggler's Cove", function()
    evt.MoveToMap(-3800, 623, 1, 2000, 0, 0, 351, 1, "d07.blv") -- Smuggler's Cove
end, "Enter Smuggler's Cove")

RegisterEvent(502, "Enter the Dire Wolf Den", function()
    evt.MoveToMap(2157, 1003, 1, 1024, 0, 0, 353, 1, "d08.blv") -- Dire Wolf Den
end, "Enter the Dire Wolf Den")

RegisterEvent(503, "Enter the Merchant House of Alvar", function()
    if not IsQBitSet(QBit(59)) then -- Returned to the Merchant guild in Alvar with overdune. Quest 25 done.
        evt.SpeakNPC(3) -- Elgar Fellmoon
        return
    end
    evt.MoveToMap(320, -1290, 513, 512, 0, 0, 354, 1, "d09.blv") -- Merchant House of Alvar
end, "Enter the Merchant House of Alvar")

RegisterEvent(504, "Enter Escaton's Crystal", function()
    evt.ForPlayer(Players.All)
    if not HasItem(610) then -- Conflux Key
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    end
    evt.MoveToMap(-1024, -1626, 0, 520, 0, 0, 355, 1, "d10.blv") -- Escaton's Crystal
end, "Enter Escaton's Crystal")

RegisterEvent(505, "Enter the Merchant House of Alvar", function()
    evt.MoveToMap(-1752, 1370, 449, 0, 0, 0, 354, 1, "d09.blv") -- Merchant House of Alvar
end, "Enter the Merchant House of Alvar")

RegisterEvent(506, "Enter the Tomb of Lord Brinne", function()
    evt.MoveToMap(0, -448, 0, 0, 0, 0, 0, 1, "d28.blv") -- Tomb of Lord Brinne
end, "Enter the Tomb of Lord Brinne")

RegisterEvent(507, "Enter the Chapel of Eep", function()
    evt.MoveToMap(-481, -2824, 321, 512, 0, 0, 0, 1, "d45.blv") -- Chapel of Eep
end, "Enter the Chapel of Eep")

