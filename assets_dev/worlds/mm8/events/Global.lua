-- generated from legacy EVT/STR

SetGlobalMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {3, 5, 8, 14, 17, 25, 36, 38, 51, 58, 69, 83},
    timers = {
    },
})

RegisterGlobalEvent(1, "Cataclysm", function()
    evt.SimpleMessage("My fellow Journeyman, we face grave times.  Hopefully our Master will find a way for us to leave this troubled region and return safely to Alvar.  I would not wish to end my life here, even though it is the place of my birth.")
    SetQBit(QBit(232)) -- Set when you talk to S'ton
    return
end)

RegisterGlobalEvent(2, "Caravan Master", function()
    evt.SimpleMessage("Dadeross led us here to trade with the Lizardman Clan of Onefang for their tobersk fruit.  He has gone to talk with Brekish Onefang, the village leader.  Perhaps you should look for him?")
    SetQBit(QBit(232)) -- Set when you talk to S'ton
    return
end)

RegisterGlobalEvent(3, "Pirates of Regna", function()
    evt.SimpleMessage("The Regnan Pirates are a threat to the economy and free travel in Jadame.  Very few boats ply the sea, for fear of being sunk…or worse!  When in Ravenshore, I did hear rumors of a small band of smugglers who have been working beneath the notice of the pirates.  I wonder how they do that!")
    SetQBit(QBit(232)) -- Set when you talk to S'ton
    return
end)

RegisterGlobalEvent(4, "Cataclysm", function()
    evt.SimpleMessage("It is as I have read in the prophecy of the Unmaking! \"...and a Mountain of Fire shall rise from the sea, like a wound drawn by the quick stroke of a dagger…\".\n\nYou must find a way off of these islands, if not for the caravan, at least for yourself!  Someone must take news of what has happened here to the Merchant Council in Alvar!  They must know of the cataclysm and of the Regnan raid!")
    evt.SetNPCTopic(2, 0, 20) -- Dadeross topic 0: Quest
    return
end)

RegisterGlobalEvent(5, "Pirates", function()
    if not IsQBitSet(QBit(6)) then -- Pirate Leader in Dagger Wound Pirate Outpost killed (quest given at Q Bit 5). Ends pirate/lizardman war on Dagger Wound. Shuts off pirate timer.
        evt.SimpleMessage("The pirates from the dread Island of Regna are using the cataclysm and the confusion created by it to aid them in overrunning the islands.  If they conquer Dagger Wound, they can use it as an outpost for direct raids on Ravenshore!  The Merchant Council in Alvar must be notified!  You must find a way to the boats and tell them!")
        return
    end
    evt.SimpleMessage("Good work dealing with those pirates. Now that they're gone, maybe Chief Onefang and his people can rebuild their lives. It really is a travesty what has happened here.")
    return
end)

RegisterGlobalEvent(6, "Caravan", function()
    if not IsQBitSet(QBit(6)) then -- Pirate Leader in Dagger Wound Pirate Outpost killed (quest given at Q Bit 5). Ends pirate/lizardman war on Dagger Wound. Shuts off pirate timer.
        evt.SimpleMessage("It will take several boats to ferry the entire caravan back to Ravenshore, or many trips by one boat.  This cannot be done until the waters around the Dagger Wound Islands are free from Regnan Pirates.  It is best that you return to Alvar and tell the Council of the Regnan attack.  They will send help to rescue us!")
        return
    end
    evt.SimpleMessage("Sadly, the caravan was one of the first things the pirates looted in their raids. I have no idea what they're going to do with three-hundred cases of tobersk fruit! Naturally, I miss the fruit, but the worst of it is the damage they did to the carts. It looks like I'll be here for at least the next season overseeing their repair. I just hope the task is done before the next tobersk harvest so I can see some return out of this profitless venture.")
    return
end)

RegisterGlobalEvent(7, "Cataclysm", function()
    if not IsQBitSet(QBit(6)) then -- Pirate Leader in Dagger Wound Pirate Outpost killed (quest given at Q Bit 5). Ends pirate/lizardman war on Dagger Wound. Shuts off pirate timer.
        evt.SimpleMessage("In the middle of the night the ground shook!  Flaming rocks dropped from the sky!  Many of my people were hurt or killed!  Great damage was done to the village.  The bridges that allowed travel between the smaller islands and the main island were destroyed.  We found ourselves stuck on the main island, unable to reach those on the smaller islands who may be injured.  Many family members and friends are missing.  We cannot reach the islands with the boat docks, and thus we are unable to send to Ravenshore for help. I do not even know if any boats survived!")
        return
    end
    evt.SimpleMessage("What with the damage caused by giant waves, falling rocks and the pirate raid, I don't know if our village will ever be the same. I know you have done great things for us, but not everything can be fixed once broken. I'm not sure what we'll do. Perhaps we will rebuild, or maybe we'll leave. Time and circumstance will decide.")
    return
end)

RegisterGlobalEvent(8, "Portals of Stone", function()
    evt.SimpleMessage("In time long past, my people used the Portals of Stone to travel quickly from island to island, but we have lost the knowledge of their operation. Only the pair connecting the village to the southwestern fields still functions. Now that the bridges are gone, we're trapped on the island!")
    evt.SetNPCTopic(1, 1, 21) -- Brekish Onefang topic 1: Quest
    return
end)

RegisterGlobalEvent(9, "Fredrick Talimere", function()
    evt.SimpleMessage("A Cleric, by the name of Fredrick Talimere, has been living with us for the last few years.  He has been studying the Portals of Stone and the outer ruins of the Abandoned Temple.  Maybe he has the knowledge to get the Portals working again!  Find him and see if he will help!")
end)

RegisterGlobalEvent(10, "Portals of Stone", function()
    evt.SimpleMessage("Ah yes…\"the portals.\" I have been studying them and the lost culture that built them for years.\n\nThey were built by the civilization that had its day long before the Lizardmen came to inhabit these islands. They were a means of instantaneous travel between the islands. Sadly, the power stones needed to operate them are in short supply.")
end)

RegisterGlobalEvent(11, "Cataclysm", function()
    evt.SimpleMessage("The first night of the mountain of fire, I went to the beach to see if I could see anything of its eruption.  I cannot be certain, but as the volcano continued to erupt, I thought I saw Earth Elementals roaming the lava encrusted base of the mountain.")
end)

RegisterGlobalEvent(12, "Power Stone", function()
    evt.SimpleMessage("So Clanleader Onefang gave you that power stone he was holding onto! It will power the portal on the southwestern tip of the island. To use it, hold an image of the stone in your mind as you step onto the portal.")
    evt.ForPlayer(Players.All)
    SetAward(Award(2)) -- Brought Power Stone to Fredrick Talimere.
    AddValue(Experience, 1500)
    ClearQBit(QBit(7)) -- Bring Brekish Onefang's portal crystal to Fredrick Talimere. - Brekish Onefang asks player to bring a power crystal to Fredrick Talimere
    SetQBit(QBit(8)) -- Fredrick Talimere visited by player with crystal in their possesion.
    evt.SetNPCTopic(32, 2, 602) -- Fredrick Talimere topic 2: Roster Join Event
    evt.SetNPCTopic(1, 2, 0) -- Brekish Onefang topic 2 cleared
    return
end)
RegisterCanShowTopic(12, function()
    evt._BeginCanShowTopic(12)
    local visible = true
    if HasItem(617) then -- Power Stone
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(13, "Abandoned Temple", function()
    evt.SimpleMessage("The ruins of a temple built by the lost civilization lies on the island just northwest of the main island. I have not explored it however, for dangerous reptiles have made it their lair. I do suspect that the temple leads to an underwater tunnel which surfaces near the boat docks on the northwest island.\n\nWith the bridges out, that tunnel may be the only way to reach the docks and a boat to safety!")
    return
end)

RegisterGlobalEvent(14, "Quest", function()
    if not IsQBitSet(QBit(138)) then -- Found Isthric the Tongue
        evt.SimpleMessage("My brother, Isthric the Tongue, went to check on the tobersk plants on one of the lesser islands.  He has not returned!  I am afraid that he is one of those stranded by the cataclysm. He may even be hurt!  If you were to fix the Portals of Stone, he would surely be able to return, and we could get help to those who need it!  Find him for me!")
        SetQBit(QBit(137)) -- Find Isthric the Tongue, brother of Rohtnax. Return to Rohtnax in the village of Blood Drop on Dagger Wound Island.
        return
    end
    evt.SimpleMessage("You found Isthric and told him how to return home?  We are indeed in debt to you, Merchant of Alvar!  I will speak well of you to Clan Leader Brekish Onefang.  Please take these potions of Cure Wounds as a reward.")
    evt.ForPlayer(Players.All)
    AddValue(Experience, 750)
    evt.ForPlayer(Players.Member0)
    AddValue(InventoryItem(222), 222) -- Cure Wounds
    AddValue(InventoryItem(222), 222) -- Cure Wounds
    ClearQBit(QBit(137)) -- Find Isthric the Tongue, brother of Rohtnax. Return to Rohtnax in the village of Blood Drop on Dagger Wound Island.
    evt.ForPlayer(Players.All)
    SetAward(Award(54)) -- Rescued Isthric the Tongue, brother of Rohtnax, on the Dagger Wound Islands.
    evt.SetNPCTopic(33, 0, 0) -- Rohtnax topic 0 cleared
    return
end)

RegisterGlobalEvent(15, "Portals of Stone", function()
    if not IsQBitSet(QBit(1)) then -- Activate Area 1 teleporters 3 and 4.
        evt.SimpleMessage("My Granda used to tell us of the times past, when the Portals of Stone were the main travel route between the islands.  She told us that the keys to the Portals disappeared during one of the first raids committed by the Regnan Pirates.  If the Portals of Stone were working my brother Isthric could return back to the main island!")
        return
    end
    evt.SimpleMessage("You have repaired the Portals of Stone?  That is tremendous news!  Quickly, find my brother, Isthric and tell him to return home!")
    return
end)

RegisterGlobalEvent(16, "Fredrick Talimere", function()
    evt.SimpleMessage("That rude man?  He's more concerned with that Abandoned Temple than he is with the life that goes on around him!  My Granda warned him that the Temple is a place of great Evil.  He never listened.  Now Granda isn't with us anymore and we have no one but Brekish Onefang to remind us of the past.")
    return
end)

RegisterGlobalEvent(17, "Mountain of Fire", function()
    evt.SimpleMessage("We have offended the Ancients!  Why else would they call up the Mountain of Fire!  The Prophecies tell of a time when the oceans would boil!  This is the beginning of the end!")
    return
end)

RegisterGlobalEvent(18, "Prophecies", function()
    evt.SimpleMessage("There are many Prophecies that tell of the destruction of Jadame and the entire world!   Most tell of a time when the world will be consumed by that which created it.  Perhaps the Ancients have decided to wipe us all out!")
    return
end)

RegisterGlobalEvent(19, "Quest", function()
    evt.ForPlayer(Players.All)
    if not HasItem(652) then -- Prophecies of the Snake
        evt.SimpleMessage("There is one Prophecy, the Prophecy of the Snake, that I have been unable to find a copy of.  I think it may be most revealing about the future of Jadame.\n\nFredrick Talimere, the Cleric, has told me of the snake ruins, and of the Abandoned Temple.  He is in agreement with me, that there may be a copy of this prophecy, somewhere in the temple.  Could you find it for me?")
        SetQBit(QBit(135)) -- Find the Prophecies of the Snake for Pascella Tisk.
        return
    end
    evt.SimpleMessage("You have found the Prophecies of the Snake!  Perhaps the details of our future can be found in its writings!  Please take this reward for your assistance!")
    RemoveItem(652) -- Prophecies of the Snake
    ClearQBit(QBit(135)) -- Find the Prophecies of the Snake for Pascella Tisk.
    evt.ForPlayer(Players.Member0)
    AddValue(Gold, 500)
    evt.ForPlayer(Players.All)
    AddValue(Experience, 750)
    evt.SetNPCTopic(34, 1, 0) -- Pascella Tisk topic 1 cleared
    return
end)

RegisterGlobalEvent(20, "Quest", function()
    if not IsQBitSet(QBit(3)) then -- Deliver Dadeross' Letter to Elgar Fellmoon at the Merchant House in Ravenshore. - Given by Dadeross in Dagger Wound. Taken by Fellmoon in Ravenshore.
        evt.SimpleMessage("You must find a way off of these islands. Someone must take news of what has happened here to our masters, the Merchants of Alvar!  They must know of the cataclysm and of the Regnan raid! \n\nI've written a letter to the Merchants of Alvar representative in Ravenshore, Elgar Fellmoon. In it I explain our situation here. If anyone can advise us on what to do here, it is Fellmoon. Take this to him now.")
        evt.SetNPCGreeting(2, 8) -- Dadeross greeting: What are you doing here? Get my letter to Fellmoon!
        AddValue(InventoryItem(741), 741) -- Dadeross' Letter to Fellmoon
        SetQBit(QBit(221)) -- Dadeross' Letter to Fellmoon - I lost it, taken event g 28
        SetQBit(QBit(3)) -- Deliver Dadeross' Letter to Elgar Fellmoon at the Merchant House in Ravenshore. - Given by Dadeross in Dagger Wound. Taken by Fellmoon in Ravenshore.
        ClearQBit(QBit(85)) -- Find Dadeross, the Minotaur in charge of your merchant caravan. When you saw him last, he was going to talk to the village clan leader. - Given at the start of the game, taken by dadeross when he gives you the deliver letter quest.
        return
    end
    evt.SimpleMessage("You must bring my letter to Elgar Fellmoon in Ravenshore!")
    return
end)
RegisterCanShowTopic(20, function()
    evt._BeginCanShowTopic(20)
    local visible = true
    if IsQBitSet(QBit(4)) then -- Letter from Q Bit 3 delivered.
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(21, "Quest", function()
    if not IsQBitSet(QBit(7)) then -- Bring Brekish Onefang's portal crystal to Fredrick Talimere. - Brekish Onefang asks player to bring a power crystal to Fredrick Talimere
        evt.SimpleMessage("Take this crystal to Fredrick Talimere. I know that it has something to do with the portals of stone. Perhaps he can tell you how it functions.")
        AddValue(InventoryItem(617), 617) -- Power Stone
        SetQBit(QBit(212)) -- Power Stone - I lost it
        SetQBit(QBit(7)) -- Bring Brekish Onefang's portal crystal to Fredrick Talimere. - Brekish Onefang asks player to bring a power crystal to Fredrick Talimere
        evt.SetNPCTopic(32, 2, 12) -- Fredrick Talimere topic 2: Power Stone
        evt.SetNPCTopic(32, 3, 13) -- Fredrick Talimere topic 3: Abandoned Temple
        return
    end
    evt.SimpleMessage("Bring the portal crystal to Fredrick Talimere. He will know what it does.")
    return
end)
RegisterCanShowTopic(21, function()
    evt._BeginCanShowTopic(21)
    local visible = true
    if IsQBitSet(QBit(8)) then -- Fredrick Talimere visited by player with crystal in their possesion.
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(22, "Promotion to Dark Elf Patriarch", function()
    evt.SimpleMessage("The Merchant Council had sent our greatest warrior, Cauri Blackthorne, to consult with the Sun Temple priests about the disasters that have struck all of Jadame.\n\nCauri left for the Temple of the Sun in Murmurwoods shortly after rumors of the cataclysms were heard here in Alvar.  She was to return after consulting the priests.  We are very concerned that she has not returned.\n\nAs for your promotion, only Cauri can accurately test your skills and assess your worthiness for promotion.  If you find her, provide her with any assistance she may need and return here with news of her status and location.")
    SetQBit(QBit(39)) -- Find Cauri Blackthorne then return to Dantillion in Murmurwoods with information of her location. - Dark Elf Promotion to Patriarch
    evt.SetNPCTopic(52, 0, 31) -- Relburn Jeebes topic 0: Where is Cauri?
    return
end)

RegisterGlobalEvent(23, "Cauri Blackthorne", function()
    if HasAward(Award(19)) then -- Promoted to Elf Patriarch.
        evt.SimpleMessage("Cauri returned and informed us of this assistance you provided her.  She also notified us of your promotion.  Congratulations, may your profits bring you much joy!")
        evt.ForPlayer(Players.Member0)
        AddValue(Gold, 15000)
        evt.SetNPCTopic(52, 1, 0) -- Relburn Jeebes topic 1 cleared
        return
    elseif HasAward(Award(20)) then -- Rescued Cauri Blackthorne.
        evt.SimpleMessage("Cauri returned and informed us of this assistance you provided her.  She also notified us of your promotion.  Congratulations, may your profits bring you much joy!")
        evt.ForPlayer(Players.Member0)
        AddValue(Gold, 15000)
        evt.SetNPCTopic(52, 1, 0) -- Relburn Jeebes topic 1 cleared
    else
        evt.SimpleMessage("This is the home of Cauri Blackthorne, greatest Dark Elf warrior.  She is currently out, working for the Merchant Council of Alvar.  Perhaps you should consult them as to her whereabouts.")
    end
    return
end)

RegisterGlobalEvent(24, "Thank you!", function()
    evt.SimpleMessage("Thank you for your assistance with the Basilisk Curse.  Usually I am prepared to handle the vile lizards, but this time there were just too many of them.\n\nThe Temple of the Sun asked me to check on a few pilgrims that were looking for the Druid Circle of Stone in this area.  When I found the first statue, I realized what had happened to the pilgrims.  \n\nI myself did not know of the increase in the number of Basilisks in this area.  They seem to be agitated by something.  I was going to investigate the Druid Circle of Stone when the Basilisks attacked me.")
    return
end)

RegisterGlobalEvent(25, "Patriarch", function()
    evt.SimpleMessage("::Cauri looks over the Dark Elf(s) in your party::\n\nTo rescue me, you must have researched my path, and investigated the places I had been.  This demonstrates the intelligence needed to succeed in dealing with the world and business.\n\nTo get to where I was attacked, you must have the skills needed to fight the Basilisks and other threats, demonstrating your prowess as a warrior.  Skill in battle is needed when proper negotiations break down.\n\nTo ask me for promotion demonstrates desire, and without desire success will always escape your grasp.\n\nYou have all of the traits necessary to hold the title of Patriarch.  I will notify to Council upon my return.  It would be my pleasure to travel with you again.  You can find me in the Inn in Ravenshore.")
    for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
        evt.ForPlayer(player)
        if IsAtLeast(ClassId, 10) then
            SetValue(ClassId, 11)
            AddValue(Experience, 35000)
            SetAward(Award(19)) -- Promoted to Elf Patriarch.
        else
            AddValue(Experience, 25000)
            SetAward(Award(20)) -- Rescued Cauri Blackthorne.
        end
    end
    ClearQBit(QBit(39)) -- Find Cauri Blackthorne then return to Dantillion in Murmurwoods with information of her location. - Dark Elf Promotion to Patriarch
    SetQBit(QBit(40)) -- Found and Rescued Cauri Blackthorne
    SetQBit(QBit(430)) -- Roster Character In Party 31
    evt.SetNPCTopic(55, 1, 38) -- Cauri Blackthorne topic 1: Thanks for your help!
    return
end)

RegisterGlobalEvent(26, "Circle of Stone", function()
    evt.SimpleMessage("I need to investigate the Circle of Stone further for the Temple of the Sun.  Hopefully not all of the pilgrims met the fate of these. Hopefully there are survivors!\n\nSomething has agitated the creatures in this area, and I think the source can be found in the Circle.")
    return
end)

RegisterGlobalEvent(27, "Cauri Blackthorne", function()
    if IsQBitSet(QBit(39)) then -- Find Cauri Blackthorne then return to Dantillion in Murmurwoods with information of her location. - Dark Elf Promotion to Patriarch
        evt.SimpleMessage("Cauri Blackthorne was here well over a week ago, maybe longer.  She had asked us many questions about the elemental incursions.  We provided her with what information we had here.  She said she would return to Alvar with the information.  Before she left, we asked her if she could do a favor for us.  We asked her if she could check on a group of pilgrims that were traveling to the old Druid Circle of Stone to the northeast of here.  She assured us that she would check in on them on her way back to Alvar.")
        evt.ForPlayer(Players.Member0)
        AddValue(InventoryItem(339), 339) -- Stone to Flesh
        evt.ForPlayer(Players.Member1)
        AddValue(InventoryItem(339), 339) -- Stone to Flesh
        evt.ForPlayer(Players.Member2)
        AddValue(InventoryItem(339), 339) -- Stone to Flesh
        evt.ForPlayer(Players.Member3)
        AddValue(InventoryItem(339), 339) -- Stone to Flesh
        evt.ForPlayer(Players.Member4)
        AddValue(InventoryItem(339), 339) -- Stone to Flesh
        evt.SetNPCTopic(54, 0, 26) -- Dantillion  topic 0: Circle of Stone
        return
    elseif IsQBitSet(QBit(40)) then -- Found and Rescued Cauri Blackthorne
        ClearQBit(QBit(39)) -- Find Cauri Blackthorne then return to Dantillion in Murmurwoods with information of her location. - Dark Elf Promotion to Patriarch
    else
        evt.SimpleMessage("Cauri Blackthorne was here well over a week ago, maybe longer.  She had asked us many questions about the elemental incursions.  We provided her with what information we had here.  She said she would return to Alvar with the information.  Before she left, we asked her if she could do a favor for us.  We asked her if she could check on a group of pilgrims that were traveling to the old Druid Circle of Stone to the northeast of here.  She assured us that she would check in on them on her way back to Alvar.")
        evt.ForPlayer(Players.Member0)
        AddValue(InventoryItem(339), 339) -- Stone to Flesh
        evt.ForPlayer(Players.Member1)
        AddValue(InventoryItem(339), 339) -- Stone to Flesh
        evt.ForPlayer(Players.Member2)
        AddValue(InventoryItem(339), 339) -- Stone to Flesh
        evt.ForPlayer(Players.Member3)
        AddValue(InventoryItem(339), 339) -- Stone to Flesh
        evt.ForPlayer(Players.Member4)
        AddValue(InventoryItem(339), 339) -- Stone to Flesh
    end
evt.SetNPCTopic(54, 0, 26) -- Dantillion  topic 0: Circle of Stone
return
end)

RegisterGlobalEvent(28, "Letter", function()
    evt.ForPlayer(Players.All)
    if not HasItem(741) then -- Dadeross' Letter to Fellmoon
        evt.SimpleMessage("You come to me claiming to have a message from one of my caravan masters. Well, where is it then? If it was so important, perhaps you should have been better about not losing it along the way!")
        return
    end
    evt.SimpleMessage("What is this? A letter from caravan master, Dadeross? Let's see…hmmm…\n\nWell, it seems that serious events are afoot. It is a pity--what has happened on Dagger Wound. Serious action may need to be taken, but I require more information…\n\n…and I think I know how to get it! Perhaps you would be interested in helping me? I will compensate you, of course. And, here. Take this as payment for delivering Dadeross' letter.")
    evt.SetNPCTopic(3, 0, 29) -- Elgar Fellmoon topic 0: Quest
    evt.SetNPCGreeting(2, 58) -- Dadeross greeting: Hail, adventurer!
    evt.ForPlayer(Players.All)
    ClearQBit(QBit(3)) -- Deliver Dadeross' Letter to Elgar Fellmoon at the Merchant House in Ravenshore. - Given by Dadeross in Dagger Wound. Taken by Fellmoon in Ravenshore.
    SetQBit(QBit(4)) -- Letter from Q Bit 3 delivered.
    RemoveItem(741) -- Dadeross' Letter to Fellmoon
    ClearQBit(QBit(221)) -- Dadeross' Letter to Fellmoon - I lost it, taken event g 28
    evt.ForPlayer(Players.Member0)
    AddValue(Gold, 2500)
    evt.ForPlayer(Players.All)
    AddValue(Experience, 7500)
    SetAward(Award(4)) -- Delivered Dadeross' Letter to Elgar Fellmoon.
    return
end)

RegisterGlobalEvent(29, "Quest", function()
    if IsQBitSet(QBit(12)) then -- Quest 11 is done.
        evt.SimpleMessage("You must reach Bastian Loudrin in Alvar. Go! He must be informed of recent events!")
        return
    elseif IsQBitSet(QBit(24)) then -- Received Reward from Elgar Fellmoon for completing quest 9.
        evt.SimpleMessage("As you may be aware, our guild headquarters is located in the city of Alvar. If you've never been there, the easiest way to reach it is to follow the river up through the canyon to the north.\n\nGo to the guild house and find Bastian Loudrin. Tell him about the crystal, and the rumors. Lourdrin will know what to do.")
        SetQBit(QBit(11)) -- Report to Bastian Loudrin, the merchant guildmaster in Alvar. - Given By Elgar Fellmoon (w503, area 2). Taken by Bastian Loudrin (area 3).
        return
    elseif IsQBitSet(QBit(10)) then -- Letter from Q Bit 9 delivered.
        evt.SimpleMessage("Very good, and here is the payment we agreed upon. Hunter's boats will be useful to us through the crisis.\n\nYes, \"crisis,\" I say! Since your initial visit, several other caravans have missed their scheduled stops. There are also the rumors. Twice I've heard of the appearance of a burning lake of fire rising out of the desert.\n\nVolcanoes! Lakes of fire! I fear the mysterious crystal has something to do with it. In any event, the guildmasters in Alvar must be informed!")
        evt.ForPlayer(Players.All)
        SetAward(Award(3)) -- Blackmailed the Wererat Smugglers.
        AddValue(Experience, 12000)
        SetQBit(QBit(24)) -- Received Reward from Elgar Fellmoon for completing quest 9.
        ClearQBit(QBit(284)) -- Return to Fellmoon in Ravenshore and report your success in blackmailing the wererat smuggler, Arion Hunter.
        return
    elseif IsQBitSet(QBit(9)) then -- Deliver Fellmoon's blackmail letter to Arion Hunter, leader of the wererat smugglers. Report back to Fellmoon. - Given and taken by Elgar Fellmoon (w503, area 2).
        evt.SimpleMessage("Listen. We need those boats! Deliver my letter to Arion Hunter. Did you forget? His lair is to the west, up the coast!")
    else
        evt.SimpleMessage("The local smugglers have the fastest boats in Ravenshore. If these were available to my agents, they could make quick scouting missions up and down the coast so we could see the extent of the cataclysm mentioned in Dadeross' letter.\n\nHere. Bring this letter to the smuggler leader, Arion Hunter. I'm sure it will \"persuade\" him to lend his services. You'll find his hideout westward up the coast.\n\nOh, I almost forgot. The smugglers--they're wererats--and you know how they can be. Hunter can be reasoned with, but don't be surprised if his crew is less than civil.")
        SetQBit(QBit(9)) -- Deliver Fellmoon's blackmail letter to Arion Hunter, leader of the wererat smugglers. Report back to Fellmoon. - Given and taken by Elgar Fellmoon (w503, area 2).
        AddValue(InventoryItem(742), 742) -- Blackmail Letter
        SetQBit(QBit(222)) -- Blackmail Letter - I lost it, taken event g 32
        evt.SetNPCGreeting(3, 11) -- Elgar Fellmoon greeting: Have you done as I've asked of you?
    end
return
end)

RegisterGlobalEvent(30, "Blackthorne Residence", function()
    if not IsQBitSet(QBit(40)) then -- Found and Rescued Cauri Blackthorne
        evt.SimpleMessage("This is the home of Cauri Blackthorne, greatest Dark Elf warrior.  She is currently out, working for the Merchant Council of Alvar.  Perhaps you should consult them as to her whereabouts.")
        return
    end
    evt.SimpleMessage("Cauri returned and informed us of this assistance you provided her.  She also notified us of your promotion.  Congratulations, may your profits bring you much joy!")
    return
end)

RegisterGlobalEvent(31, "Where is Cauri?", function()
    evt.SimpleMessage("Have you found Cauri?  We really need to know what happened to her!  Without her, we are all diminished!")
    return
end)
RegisterCanShowTopic(31, function()
    evt._BeginCanShowTopic(31)
    local visible = true
    if IsQBitSet(QBit(40)) then -- Found and Rescued Cauri Blackthorne
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(32, "Blackmail", function()
    evt.SimpleMessage("You did all that to my guards just to deliver a letter! Let me see that…\n\n…hmmm…Fellmoon wants my boats? Never! I…what!…he threatens my Irabelle…I…I…sigh…\n\nV-very well. You can tell Fellmoon he can have my boats. I guess there's no refusing the Merchants of Alvar what they want.")
    evt.ForPlayer(Players.All)
    SetQBit(QBit(10)) -- Letter from Q Bit 9 delivered.
    ClearQBit(QBit(9)) -- Deliver Fellmoon's blackmail letter to Arion Hunter, leader of the wererat smugglers. Report back to Fellmoon. - Given and taken by Elgar Fellmoon (w503, area 2).
    SetQBit(QBit(284)) -- Return to Fellmoon in Ravenshore and report your success in blackmailing the wererat smuggler, Arion Hunter.
    RemoveItem(742) -- Blackmail Letter
    ClearQBit(QBit(222)) -- Blackmail Letter - I lost it, taken event g 32
    evt.SetNPCTopic(4, 0, 33) -- Arion Hunter topic 0: Smuggler Boats
    AddValue(History(5), 0)
    return
end)
RegisterCanShowTopic(32, function()
    evt._BeginCanShowTopic(32)
    local visible = true
    if HasItem(742) then -- Blackmail Letter
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(33, "Smuggler Boats", function()
    evt.SimpleMessage("My cargoes are not the kind that want inspecting by harbor officials so my boats have to be, and are, the fastest on the coast of Jadame. They can even outrun a Regnan galley! From here they run west to Ravage Roaming and east to Shadowspire.")
    return
end)

RegisterGlobalEvent(34, "Ancient Troll Home", function()
    evt.SimpleMessage("Ancient Troll legends tell of a time when we did not live here in this desolate region.  They tell of a place that was quiet and tranquil.  We were driven from this place by the Curse of the Stone.  So for many hundred years we have dwelt here upon the Sand of Iron.  Now it seems we will be forced from this place as well.  The growing sea of fire has destroyed most of my village.  Many friends and family have perished.  This may indeed be the end of my Clan.\n\nThere is a saying amongst my people, \"a thing lives only as long as it is remembered.\"  As long as I remember our homeland, then it will always be there for us to return too.  It just needs to be found.")
    return
end)

RegisterGlobalEvent(35, "Quest", function()
    evt.SimpleMessage("Perhaps if you could locate our previous homeland, and check to see if the Curse of the Stone still exists.  If it does perhaps there is a way to remove it.  Any Troll in your party who completes this task would be promoted to War Troll of our Clan. Many honors are bestowed with this title, and you would be forever known to us as a legendary hero.\n\nOne of our warriors, Dartin Dunewalker, set out to find this place.  He left thinking he would find clues among the stone fields of Ravage Roaming.  Perhaps you can find him there and work together--or at the least, find clues that will lead you to our goal.")
    SetQBit(QBit(68)) -- Find the Ancient Troll Homeland and return to Volog Sandwind in the Ironsand Desert. - Given By ? In area 4
    evt.SetNPCTopic(56, 0, 40) -- Volog Sandwind topic 0: Ancient Home
    return
end)

RegisterGlobalEvent(36, "Ancient Home Found!", function()
    evt.SimpleMessage("You have found our Ancient Home?  Its located in the western area of the Murmurwoods?  This is wonderful news.  Perhaps there is still time to move my people.  Unfortunately the Elemental threat must be dealt with first, or no people will be safe! \n\nAll Trolls among you have been promoted to War Troll, and their names will be forever remembered in our songs.  I will teach the rest of you what skills I can, perhaps it will be enough to help you save all of Jadame.")
    for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
        evt.ForPlayer(player)
        if IsAtLeast(ClassId, 6) then
            SetValue(ClassId, 7)
            AddValue(Experience, 35000)
            SetAward(Award(21)) -- Promoted to War Troll.
        else
            AddValue(Experience, 25000)
            SetAward(Award(22)) -- Found Troll Homeland.
        end
    end
    ClearQBit(QBit(68)) -- Find the Ancient Troll Homeland and return to Volog Sandwind in the Ironsand Desert. - Given By ? In area 4
    evt.SetNPCTopic(56, 1, 612) -- Volog Sandwind topic 1: Roster Join Event
    return
end)
RegisterCanShowTopic(36, function()
    evt._BeginCanShowTopic(36)
    local visible = true
    if IsQBitSet(QBit(69)) then -- Ancient Troll Homeland Found
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(37, "Curse of Stone", function()
    evt.SimpleMessage("You were sent to find the Ancient Troll Home?  Your assistance is welcomed!  I am at a loss; the clues I followed to this region have lead to a dead end.  No one here knows about the Curse of the Stone mentioned in our legends.  The Ogre Mage, Zog was less than helpful.  I was lucky to escape his fortress with my life. \n\nAlthough, he may have provided assistance with out meaning too!  When I mentioned the Curse of the Stone, he said if I bothered him further, he would be sure to cage me with his pet Basilisk!  Basilisks roam the Murmurwoods!")
    return
end)

RegisterGlobalEvent(38, "Thanks for your help!", function()
    evt.SimpleMessage("Thanks again for your assistance with the Basilisk curse!  Hurry back to Alvar!  We must do what we can to save Jadame.")
    return
end)

RegisterGlobalEvent(39, "Thanks for your help!", function()
    evt.SimpleMessage("Thanks for finding our Ancient Home, once the treat to Jadame has been handled we can begin to move there!")
    return
end)

RegisterGlobalEvent(40, "Ancient Home", function()
    evt.SimpleMessage("Have you found the Ancient Home for our Clan?  Without its location, my people will surely perish!")
    return
end)
RegisterCanShowTopic(40, function()
    evt._BeginCanShowTopic(40)
    local visible = true
    if IsQBitSet(QBit(68)) then -- Find the Ancient Troll Homeland and return to Volog Sandwind in the Ironsand Desert. - Given By ? In area 4
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(41, "Deliver Report", function()
    evt.SimpleMessage("Disaster in Dagger Wound, too? This is indeed disturbing. If one were to believe all the rumors, one would think that all of Jadame is in upheaval and chaos.\n\nI wish I knew more. I rely on our caravan masters for news, but all who were supposed to arrive here this month have not. What I do hear, troubles me. Hurricanes, floods, and now a volcano! The worst I've heard is that a sea of fire has appeared in the Ironsand Desert--and this from many sources.\n\nI wonder if this crystal in Ravenshore has something to do with it. Its appearance at the onset of the calamity seems to be more than a coincidence.")
    ClearQBit(QBit(11)) -- Report to Bastian Loudrin, the merchant guildmaster in Alvar. - Given By Elgar Fellmoon (w503, area 2). Taken by Bastian Loudrin (area 3).
    SetQBit(QBit(12)) -- Quest 11 is done.
    evt.SetNPCTopic(5, 0, 42) -- Bastian Loudrin topic 0: Quest
    evt.ForPlayer(Players.All)
    AddValue(Experience, 15000)
    evt.ForPlayer(Players.Member0)
    AddValue(Gold, 2000)
    return
end)
RegisterCanShowTopic(41, function()
    evt._BeginCanShowTopic(41)
    local visible = true
    if IsQBitSet(QBit(11)) then -- Report to Bastian Loudrin, the merchant guildmaster in Alvar. - Given By Elgar Fellmoon (w503, area 2). Taken by Bastian Loudrin (area 3).
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(42, "Quest", function()
    if not IsQBitSet(QBit(25)) then -- Find a witness to the lake of fire's formation. Bring him back to the merchant guild in Alvar. - Given and taken by Bastian Lourdrin (area 3).
        evt.SimpleMessage("All of this upheaval is seriously impacting our guild's business. I need more information, but I'm being buried in gossip and rumor.\n\nMany tell me of this sea of fire in the Ironsand Desert. I've heard the tale enough that I almost believe it. Confirmation or denial of the lake's existence would be of great help to me.\n\nIf you would serve me, go to the Ironsand Desert and seek this lake. If it is indeed there, find me someone who saw it appear. Bring him back here so I can hear his story myself.")
        SetQBit(QBit(25)) -- Find a witness to the lake of fire's formation. Bring him back to the merchant guild in Alvar. - Given and taken by Bastian Lourdrin (area 3).
        AddValue(History(6), 0)
        evt.MoveNPC(7, 177) -- Overdune Snapfinger -> Overdune's House
        evt.MoveNPC(60, 177) -- Farhill Snapfinger -> Overdune's House
        return
    end
    if HasPlayer(4) then -- Overdune Snapfinger
        evt.SimpleMessage("Oh, what a mess you've made of things! When I asked you to find me a witness of events in the Ironsand Desert, I thought it would be obvious that you'd have to return him to me in good condition! I mean look at the poor Troll! Take him to the temple and get him fixed up.\n\nAnd please...try to remember you're working for the guild. We do have a reputation for conducting ourselves with at least passing competence.")
        return
    elseif IsQBitSet(QBit(60)) then -- Party visits Ironsand After QuestBit 25 set.
        evt.SimpleMessage("Well, so it is true. Imagine…a lake of fire. But where is my eyewitness? I need to speak with someone who saw its formation. This is important…for reasons I'm unwilling to discuss with you now.\n\nFind me someone who saw the birth of the lake of fire! Try searching the Troll village, Rust.")
    else
        evt.SimpleMessage("I must know more about what is going on in the Ironsand Desert. I can't use more rumors. I have enough of those already.\n\nI need you to actually go there. The desert is several days travel to the east.")
    end
    return
end)

RegisterGlobalEvent(43, "Quest", function()
    if IsQBitSet(QBit(19)) then -- Allied with Necromancers Guild. Steal Nightshade Brazier done.
        if IsQBitSet(QBit(21)) then -- Allied with Charles Quioxte's Dragon Hunters. Return Dragon Egg to Quixote done.
            if IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
                evt.SimpleMessage("Very good…or at least, as good as can be expected. You managed to bring three partners into the alliance--the minimum number my advisors told me would be sufficient to fulfill the \"…Jadame, must stand together…\" part of the prophecy. A pity it could not be more, but events of the cataclysm are clearly coming to a head. It is time to move onward.\n\nYou must travel to Ravenshore and meet with the alliance council gathered there. With them, decide what must be the next step we take in meeting the elemental crisis.")
                return
            end
            evt.SimpleMessage("You must form an alliance to stand against our threatened oblivion! Seek support from the Necromancers' Guild, Temple of the Sun, Minotaurs of Ravage Roaming, Dragons of Garrote Gorge, and the Dragon hunting party of Charles Quixote in Garrote Gorge. I'm sure that you will find it impossible to get all of them to agree to work together, but still, you must make your best effort.\n\nIf we are to survive in this time of prophecy, my sages tell me that at least three of the groups I mentioned must agree to work together. Go and do this thing. If you value this world and your lives, go!")
            return
        elseif IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
            if IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
                evt.SimpleMessage("Very good…or at least, as good as can be expected. You managed to bring three partners into the alliance--the minimum number my advisors told me would be sufficient to fulfill the \"…Jadame, must stand together…\" part of the prophecy. A pity it could not be more, but events of the cataclysm are clearly coming to a head. It is time to move onward.\n\nYou must travel to Ravenshore and meet with the alliance council gathered there. With them, decide what must be the next step we take in meeting the elemental crisis.")
                return
            end
            evt.SimpleMessage("You must form an alliance to stand against our threatened oblivion! Seek support from the Necromancers' Guild, Temple of the Sun, Minotaurs of Ravage Roaming, Dragons of Garrote Gorge, and the Dragon hunting party of Charles Quixote in Garrote Gorge. I'm sure that you will find it impossible to get all of them to agree to work together, but still, you must make your best effort.\n\nIf we are to survive in this time of prophecy, my sages tell me that at least three of the groups I mentioned must agree to work together. Go and do this thing. If you value this world and your lives, go!")
            return
        else
            evt.SimpleMessage("You must form an alliance to stand against our threatened oblivion! Seek support from the Necromancers' Guild, Temple of the Sun, Minotaurs of Ravage Roaming, Dragons of Garrote Gorge, and the Dragon hunting party of Charles Quixote in Garrote Gorge. I'm sure that you will find it impossible to get all of them to agree to work together, but still, you must make your best effort.\n\nIf we are to survive in this time of prophecy, my sages tell me that at least three of the groups I mentioned must agree to work together. Go and do this thing. If you value this world and your lives, go!")
            return
        end
    elseif IsQBitSet(QBit(20)) then -- Allied with Temple of the Sun. Destroy the Skeleton Transformer done.
        if IsQBitSet(QBit(21)) then -- Allied with Charles Quioxte's Dragon Hunters. Return Dragon Egg to Quixote done.
            if IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
                evt.SimpleMessage("Very good…or at least, as good as can be expected. You managed to bring three partners into the alliance--the minimum number my advisors told me would be sufficient to fulfill the \"…Jadame, must stand together…\" part of the prophecy. A pity it could not be more, but events of the cataclysm are clearly coming to a head. It is time to move onward.\n\nYou must travel to Ravenshore and meet with the alliance council gathered there. With them, decide what must be the next step we take in meeting the elemental crisis.")
                return
            end
            evt.SimpleMessage("You must form an alliance to stand against our threatened oblivion! Seek support from the Necromancers' Guild, Temple of the Sun, Minotaurs of Ravage Roaming, Dragons of Garrote Gorge, and the Dragon hunting party of Charles Quixote in Garrote Gorge. I'm sure that you will find it impossible to get all of them to agree to work together, but still, you must make your best effort.\n\nIf we are to survive in this time of prophecy, my sages tell me that at least three of the groups I mentioned must agree to work together. Go and do this thing. If you value this world and your lives, go!")
            return
        elseif IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
            if IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
                evt.SimpleMessage("Very good…or at least, as good as can be expected. You managed to bring three partners into the alliance--the minimum number my advisors told me would be sufficient to fulfill the \"…Jadame, must stand together…\" part of the prophecy. A pity it could not be more, but events of the cataclysm are clearly coming to a head. It is time to move onward.\n\nYou must travel to Ravenshore and meet with the alliance council gathered there. With them, decide what must be the next step we take in meeting the elemental crisis.")
                return
            end
            evt.SimpleMessage("You must form an alliance to stand against our threatened oblivion! Seek support from the Necromancers' Guild, Temple of the Sun, Minotaurs of Ravage Roaming, Dragons of Garrote Gorge, and the Dragon hunting party of Charles Quixote in Garrote Gorge. I'm sure that you will find it impossible to get all of them to agree to work together, but still, you must make your best effort.\n\nIf we are to survive in this time of prophecy, my sages tell me that at least three of the groups I mentioned must agree to work together. Go and do this thing. If you value this world and your lives, go!")
            return
        else
            evt.SimpleMessage("You must form an alliance to stand against our threatened oblivion! Seek support from the Necromancers' Guild, Temple of the Sun, Minotaurs of Ravage Roaming, Dragons of Garrote Gorge, and the Dragon hunting party of Charles Quixote in Garrote Gorge. I'm sure that you will find it impossible to get all of them to agree to work together, but still, you must make your best effort.\n\nIf we are to survive in this time of prophecy, my sages tell me that at least three of the groups I mentioned must agree to work together. Go and do this thing. If you value this world and your lives, go!")
            return
        end
    else
        evt.SimpleMessage("You must form an alliance to stand against our threatened oblivion! Seek support from the Necromancers' Guild, Temple of the Sun, Minotaurs of Ravage Roaming, Dragons of Garrote Gorge, and the Dragon hunting party of Charles Quixote in Garrote Gorge. I'm sure that you will find it impossible to get all of them to agree to work together, but still, you must make your best effort.\n\nIf we are to survive in this time of prophecy, my sages tell me that at least three of the groups I mentioned must agree to work together. Go and do this thing. If you value this world and your lives, go!")
        return
    end
end)

RegisterGlobalEvent(44, "Well Done", function()
    evt.SimpleMessage("You have done what I feared was impossible. Though these times are fraught with uncertainties, that you have united key factions of Jadame goes a long way towards securing our continued existence.\n\nWell, I have done what I can. I leave the defense of the land to the alliance council. I hope they find the accommodations I have provided them in Ravenshore to be adequate--the guild house there is not our most luxurious. Still, I though it would be best if the council was located near the crystal.\n\nI wish them, and you, good luck!")
    return
end)

RegisterGlobalEvent(45, "Lake of Fire", function()
    evt.SimpleMessage("Yes, I was here when the lake of fire first appeared. A strange gateway appeared on the desert plain outside the village. The fire you see spilled forth from it. The fire spread like water poured on the ground.\n\nA wave of flames rushed over the edge of the village. Most of my people were lost instantly. What remains of this village is as you see it.\n\nI was in the hills overlooking the village when this all happened. I saw it all, but I can hardly believe it.")
    evt.SetNPCTopic(7, 0, 46) -- Overdune Snapfinger topic 0: Come to Alvar
    return
end)

RegisterGlobalEvent(46, "Come to Alvar", function()
    if IsQBitSet(QBit(62)) then -- Vilebites Ashes (item603) placed in troll tomb.
        evt.SimpleMessage("You have done my family a great service. With his ashes safe in the holy sanctuary of the village tomb, Vilebite can lie in peace. My father, too is greatly improved. We have talked and I believe that he can now take care of himself while I accompany you to Alvar.")
        SetQBit(QBit(63)) -- Quest 61 done.
        ClearQBit(QBit(61)) -- Put Vilebite's ashes in the Dust village tomb then return to Overdune. - Given and taken by Overdune, NPC 7, w177.
        evt.ForPlayer(Players.All)
        SetAward(Award(6)) -- Placed Vilebite's ashes in the Troll Tomb.
        evt.ForPlayer(Players.Member0)
        AddValue(Gold, 7500)
        evt.ForPlayer(Players.All)
        AddValue(Experience, 20000)
        evt.SetNPCTopic(7, 0, 604) -- Overdune Snapfinger topic 0: Roster Join Event
        evt.SetNPCGreeting(60, 18) -- Farhill Snapfinger greeting: Th-thank you for giving my son Vilebite his rest.
        evt.SetNPCTopic(60, 0, 47) -- Farhill Snapfinger topic 0: Vilebite
        return
    elseif IsQBitSet(QBit(61)) then -- Put Vilebite's ashes in the Dust village tomb then return to Overdune. - Given and taken by Overdune, NPC 7, w177.
        evt.SimpleMessage("I will go with you only after my brother's ashes are safely in the village tomb.")
    else
        evt.SimpleMessage("I would come with you, If it were not for my father. So deep is his mourning for my brother, Vilebite, that he cannot care for himself.\n\nMy father believes that Vilebite's soul cannot rest until his remains are at rest in the village tomb. Unfortunately, Gogs infested the tomb when the lake of fire appeared.\n\nHere! Take my brother's ashes. I'm sure my father's grief will lessen if they are placed in the tomb. Do this for me and I will travel with you to Alvar.")
        SetQBit(QBit(61)) -- Put Vilebite's ashes in the Dust village tomb then return to Overdune. - Given and taken by Overdune, NPC 7, w177.
        AddValue(InventoryItem(603), 603) -- Urn of Ashes
        SetQBit(QBit(202)) -- Urn of Ashes - I lost it
    end
return
end)

RegisterGlobalEvent(47, "Vilebite", function()
    evt.SimpleMessage("Vilebite was a good son. I will miss him. But at least I can take comfort knowing that he is at peace. Thank you for your kind and heroic deed.")
    return
end)

RegisterGlobalEvent(48, "Alliance", function()
    evt.SimpleMessage("\"An alliance to unite Jadame,\" you say. If it wasn't Lordrin who was proposing it, I would normally have slain you for my supper.\n\nWhile intriguing, I cannot consider the idea now. We are under daily attack by the accursed knights of Charles Quixote. If he were not a problem, I could do as Lordrin asks.\n\nPerhaps you could help me with Quixote?")
    evt.SetNPCTopic(21, 0, 49) -- Deftclaw Redreaver topic 0: Quest
    return
end)
RegisterCanShowTopic(48, function()
    evt._BeginCanShowTopic(48)
    local visible = true
    if IsQBitSet(QBit(17)) then -- Form an alliance with the Dragons of Garrote Gorge. - Given by Bastian Lourdrin (area 3). Activates Merchanthouse in Alvar. Taken when Dragon Egg (item 605) delivered to Charles Quixote or dragon leader.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(49, "Quest", function()
    if IsQBitSet(QBit(21)) then -- Allied with Charles Quioxte's Dragon Hunters. Return Dragon Egg to Quixote done.
        return
    elseif IsQBitSet(QBit(33)) then -- Find the Dragon Egg and return it to the dragon leader, Deftclaw Redreaver. - Given and taken by DRAGON LEADER (area 5)
        evt.ForPlayer(Players.All)
        if not HasItem(605) then -- Dragon Leader's Egg
            evt.SimpleMessage("If you want me to join your alliance, you will have to help me against Charles Quixote. Bring me the Dragon egg he stole from me!")
            return
        end
        evt.ShowMovie("\"dragonsrevenge\" ", true)
        evt.SimpleMessage("Now that I need not fear my heir's destruction. I will visit my revenge on Quixote. His camp will face the assault of fire and claw. Those who have hunted us are now our prey animals.\n\nAs for your alliance…you have done me a great service. I will honor my debt. As soon as I've set my enemies to flight or the beyond, I will join the alliance council in Ravenshore.")
        SetQBit(QBit(22)) -- Allied with Dragons. Return Dragon Egg to Dragons done.
        SetQBit(QBit(35)) -- Quest 33 is done.
        ClearQBit(QBit(16)) -- Form an alliance with the Dragon hunters of Garrote Gorge. - Given by Bastian Lourdrin (area 3). Activates Merchanthouse in Alvar. Taken when Dragon Egg (item 605) delivered to Charles Quixote or dragon leader.
        ClearQBit(QBit(17)) -- Form an alliance with the Dragons of Garrote Gorge. - Given by Bastian Lourdrin (area 3). Activates Merchanthouse in Alvar. Taken when Dragon Egg (item 605) delivered to Charles Quixote or dragon leader.
        ClearQBit(QBit(31)) -- Recover the Dragon Egg from Zog's fortress in Ravage Roaming and return it to Charles Quixote in Garrote Gorge. - Given and taken by Quixote (area 5)
        ClearQBit(QBit(33)) -- Find the Dragon Egg and return it to the dragon leader, Deftclaw Redreaver. - Given and taken by DRAGON LEADER (area 5)
        evt.SetNPCTopic(19, 0, 0) -- Sir Charles Quixote topic 0 cleared
        evt.SetNPCGreeting(21, 20) -- Deftclaw Redreaver greeting: What do you want?
        evt.SetNPCTopic(21, 0, 0) -- Deftclaw Redreaver topic 0 cleared
        evt.ForPlayer(Players.All)
        AddValue(Experience, 20000)
        evt.ForPlayer(Players.All)
        RemoveItem(605) -- Dragon Leader's Egg
        ClearQBit(QBit(204)) -- Dragon Leader's Egg - I lost it, taken event g49, g64
        evt.ForPlayer(Players.Member0)
        AddValue(Gold, 10000)
        evt.ForPlayer(Players.All)
        SetAward(Award(7)) -- Formed an alliance with the Garrote Gorge Dragons.
        AddValue(History(9), 0)
    else
        evt.SimpleMessage("Last month one of Quixote's raiding parties invaded our caves. They slew many and took with them the egg containing my unborn heir. While those foul slayers hold the egg, we cannot attack their encampment.\n\nIf you were to return the egg to me, I could destroy Quixote. Do this for me and I will join your alliance.")
        SetQBit(QBit(33)) -- Find the Dragon Egg and return it to the dragon leader, Deftclaw Redreaver. - Given and taken by DRAGON LEADER (area 5)
    end
    return
end)

RegisterGlobalEvent(50, "Cure for Blazen Stormlance", function()
    evt.SimpleMessage("The Gem of Restoration may cure the knight, Blazen Stormlance, of what you say has befallen him.  There is no love lost between the Temple of the Sun and the Guild of Necromancers; any opponent of theirs is definitely a friend of ours.  Restore Stormlance to life so that he may rejoin Charles Quixote.\n")
    evt.SetNPCTopic(63, 0, 743) -- Dervish Chevron topic 0: Travel with you!
    AddValue(InventoryItem(623), 623) -- Gem of Restoration
    SetQBit(QBit(73)) -- Received Cure for Blazen Stormlance
    SetQBit(QBit(217)) -- Gem of Restoration - I lost it
    ClearQBit(QBit(72)) -- Inquire about a cure for Blazen Stormlance from Dervish Chevron in Ravenshore.
    return
end)
RegisterCanShowTopic(50, function()
    evt._BeginCanShowTopic(50)
    local visible = true
    if IsQBitSet(QBit(72)) then -- Inquire about a cure for Blazen Stormlance from Dervish Chevron in Ravenshore.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(51, "Skeletal Dragons", function()
    evt.SimpleMessage("My father believed that the Necromancers of Shadowspire were attempting to create an undead Dragon.  This would be a truly horrid beast. He believed is was his personal duty to stop them.")
    return
end)

RegisterGlobalEvent(52, "Promotion to Champion", function()
    evt.SimpleMessage("My father Blazen, left here years ago to slay the Skeletal Dragons in the Shadowspire Region. Unfortunately, he has never returned.  He took with him, Ebonest, the greatest Dragon slaying spear ever forged. Charles Quixote has never forgiven my father for taking Ebonest with him.  Unfortunately we have no idea what befell my father.  Because my father was Charles’ second in command and responsible for the loss of Ebonest, Charles is unwilling to promote me to Champion, regardless of the merit of my skills. Perhaps if you find Ebonest, Charles with promote your knights and myself to Champions!")
    SetQBit(QBit(70)) -- Find Blazen Stormlance and recover the spear Ebonest. Return to Leane Stormlance in Garrote Gorge and deliver Ebonest to Charles Quixote.
    evt.SetNPCTopic(62, 0, 59) -- Leane Stormlance topic 0: My Father
    return
end)

RegisterGlobalEvent(53, "Ebonest", function()
    evt.SimpleMessage("I was captured in the center of the Mad Necromancer’s lab.  There I was tortured and many curses were placed upon me.   Ebonest must have been taken from me when I fell, and perhaps is still in the central chamber.  If you were to recover it and return it to Quixote, at least my family name will be cleared, and my daughter can continue her life without my failure haunting her.")
    return
end)

RegisterGlobalEvent(54, "Cure", function()
    evt.ForPlayer(Players.All)
    if not HasItem(623) then -- Gem of Restoration
        evt.SimpleMessage("Perhaps the Clerics of the Sun have a way to cure me, for they would be the only ones who would know how to counter the dark magics that afflict me. There is a friend of mine in Ravenshore named Dervish Chevron. He left the Temple of the Sun years ago to pursue his own research into the mysteries of Jadame.  Perhaps he would know of a cure, or even have it in his possession.  If he cannot help, promise you will return here and kill me so I may at last be at rest!")
        SetQBit(QBit(72)) -- Inquire about a cure for Blazen Stormlance from Dervish Chevron in Ravenshore.
        return
    end
    evt.ForPlayer(Players.All)
    evt.SimpleMessage("The Cleric sent you back with the Gem of Restoration?  I am free of this place!  Search me out if you wish for me to ever travel with you!  It would be my pleasure to join you in your journeys!  I will wait for you at the Adventurer's Inn in Ravenshore.")
    RemoveItem(623) -- Gem of Restoration
    ClearQBit(QBit(217)) -- Gem of Restoration - I lost it
    AddValue(Experience, 15000)
    SetQBit(QBit(134)) -- Gave Gem of Restoration to Blazen Stormlance
    SetQBit(QBit(435)) -- Roster Character In Party 36
    evt.ForPlayer(Players.All)
    SetAward(Award(25)) -- Rescued Blazen Stormlance.
    evt.SetNPCTopic(295, 1, 0) -- Blazen Stormlance topic 1 cleared
    return
end)

RegisterGlobalEvent(55, "Mad Necromancer", function()
    evt.SimpleMessage("Zanthora moved here from the Shadowspire to continue experiments she began at the Necromancers' Guild.  She desired to create the ultimate horror, the Skeletal Dragon.  Her fellow Necromancers feared the end result. If the created Dragons where ever to escape Zanthora’s control, there would be no stopping them.")
    return
end)

RegisterGlobalEvent(56, "Stormlance", function()
    evt.SimpleMessage("Blazen Stormlance was my lieutenant and my friend.  I never understood his personal quest--this need to find these rumored Skeletal Dragons.  He took my greatest tool with him.  With Ebonest in my hand, I would have the Dragon problem well in hand.  ")
    return
end)

RegisterGlobalEvent(57, "Ebonest", function()
    evt.SimpleMessage("The Clerics of the Sun imbued this spear with their blessings, making it the strongest spear forged.  Its power is said to be able to slay any Dragon with one blow.  If this were so, I could end my conflict quickly, cleanly and efficiently.")
    return
end)

RegisterGlobalEvent(58, "Promotion to Champion", function()
    evt.ForPlayer(Players.All)
    if not HasItem(539) then -- Ebonest
        evt.SimpleMessage("You have found Blazen Stormlance? But where is Ebonest?  Return to me when you have the spear and you will be promoted!")
        return
    end
    if not IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
        evt.SimpleMessage("You found Blazen Stormlance?  What about MY spear Ebonest?  You have that as well?\n\nFANTASTIC!\n\nI thank you for this and find myself in your debt!  I will promote all knights in your party to Champion and teach what skills I can to the rest of your party. ")
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if IsAtLeast(ClassId, 4) then
                SetValue(ClassId, 5)
                AddValue(Experience, 50000)
                SetAward(Award(23)) -- Promoted to Champion.
                RemoveItem(539) -- Ebonest
            else
                AddValue(Experience, 35000)
                SetAward(Award(24)) -- Returned Ebonest to Charles Quixote.
            end
        end
        ClearQBit(QBit(70)) -- Find Blazen Stormlance and recover the spear Ebonest. Return to Leane Stormlance in Garrote Gorge and deliver Ebonest to Charles Quixote.
        evt.SetNPCTopic(19, 2, 735) -- Sir Charles Quixote topic 2: Promote Knights
        evt.SetNPCTopic(65, 2, 735) -- Sir Charles Quixote topic 2: Promote Knights
        return
    end
    evt.SimpleMessage("What is this?  You ally with my mortal enemies and then seek to do me a favor?\n\nI wonder what the Dragons think of this. But so be it.  I am in your debt for returning Ebonest to me.  I will promote any Knights in your party to Champion, however they will never be accepted in my service.  The rest I will teach what I can. \n\nI do not wish to see you again!")
    for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
        evt.ForPlayer(player)
        if IsAtLeast(ClassId, 4) then
            SetValue(ClassId, 5)
            AddValue(Experience, 50000)
            SetAward(Award(23)) -- Promoted to Champion.
            RemoveItem(539) -- Ebonest
        else
            AddValue(Experience, 35000)
            SetAward(Award(24)) -- Returned Ebonest to Charles Quixote.
        end
    end
    ClearQBit(QBit(70)) -- Find Blazen Stormlance and recover the spear Ebonest. Return to Leane Stormlance in Garrote Gorge and deliver Ebonest to Charles Quixote.
    evt.SetNPCTopic(19, 2, 735) -- Sir Charles Quixote topic 2: Promote Knights
    evt.SetNPCTopic(65, 2, 735) -- Sir Charles Quixote topic 2: Promote Knights
    return
end)
RegisterCanShowTopic(58, function()
    evt._BeginCanShowTopic(58)
    local visible = true
    if IsQBitSet(QBit(73)) then -- Received Cure for Blazen Stormlance
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(59, "My Father", function()
    if IsQBitSet(QBit(435)) then -- Roster Character In Party 36
        if HasItem(539) then -- Ebonest
            evt.SimpleMessage("You found my father and Ebonest?  I will be forever in your debt!  We should take the spear to Charles Quixote, and if he is agreeable, he will promote me and any knights in your party!")
            evt.ForPlayer(Players.All)
            AddValue(Experience, 5000)
            evt.SetNPCTopic(62, 0, 611) -- Leane Stormlance topic 0: Roster Join Event
            return
        elseif HasAward(Award(24)) then -- Returned Ebonest to Charles Quixote.
            evt.SimpleMessage("You found my father and Ebonest?  I will be forever in your debt!  We should take the spear to Charles Quixote, and if he is agreeable, he will promote me and any knights in your party!")
            evt.ForPlayer(Players.All)
            AddValue(Experience, 5000)
            evt.SetNPCTopic(62, 0, 611) -- Leane Stormlance topic 0: Roster Join Event
        else
            evt.SimpleMessage("You found Ebonest?  What of my father?  Where is he?  I thought you were going to return when you had found both my father and the spear.")
        end
        return
    elseif HasItem(539) then -- Ebonest
        evt.SimpleMessage("You found Ebonest?  What of my father?  Where is he?  I thought you were going to return when you had found both my father and the spear.")
    else
        evt.SimpleMessage("Have you found my father?  Or the spear Ebonest?  We must get it back to Charles Quixote!")
    end
    return
end)

RegisterGlobalEvent(60, "Promotion to Great Wyrm", function()
    if IsQBitSet(QBit(21)) then -- Allied with Charles Quioxte's Dragon Hunters. Return Dragon Egg to Quixote done.
        evt.SimpleMessage("You think I would promote a Dragon that serves those who have allied themselves with our Mortal enemy, Charles Quixote.  What arrogance!  What outrageousness!  You will have to prove yourselves to me! And in the proving you will deal a serious blow to your allies!  To the southwest of here, Quixote has established an encampment of his puny “Dragon Slayers.”  This camp is lead by Jeric Whistlebone, the second in command of Quixote’s army.  Destroy this camp!  Kill all of those who serve Quixote in that region and return to me.  Return to me with the sword of  Whistlebone the Slayer.")
        SetQBit(QBit(74)) -- Kill all Dragon Slayers and return the Sword of Whistlebone the Slayer to Deftclaw Redreaver in Garrote Gorge.
        evt.SetNPCTopic(21, 1, 61) -- Deftclaw Redreaver topic 1: Dragon Slayers
        evt.SetNPCTopic(21, 1, 61) -- Deftclaw Redreaver topic 1: Dragon Slayers
        return
    elseif IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
        evt.SimpleMessage("To attain the status of Great Wyrm, a Dragon must prove that he can handle himself against a great number of foes.  He must face down the vermin that Charles Quixote would send against us.  To the southwest of here, Quixote has established an encampment of his puny “Dragon Slayers.”  This camp is lead by Jeric Whistlebone, the second in command of Quixote’s army.  Destroy this camp!  Kill all of those who serve Quixote in that region and return to me.  Return to me with the sword of  Whistlebone the Slayer.  In doing this, you will prove to me your worthiness.  ")
        SetQBit(QBit(74)) -- Kill all Dragon Slayers and return the Sword of Whistlebone the Slayer to Deftclaw Redreaver in Garrote Gorge.
        evt.SetNPCTopic(21, 1, 61) -- Deftclaw Redreaver topic 1: Dragon Slayers
        evt.SetNPCTopic(66, 1, 61) -- Deftclaw Redreaver topic 1: Dragon Slayers
        return
    else
        evt.SimpleMessage("To attain the status of Great Wyrm, a Dragon must prove that he can handle himself against a great number of foes.  He must face down the vermin that Charles Quixote would send against us.  To the southwest of here, Quixote has established an encampment of his puny “Dragon Slayers.”  This camp is lead by Jeric Whistlebone, the second in command of Quixote’s army.  Destroy this camp!  Kill all of those who serve Quixote in that region and return to me.  Return to me with the sword of  Whistlebone the Slayer.  In doing this, you will prove to me your worthiness.  ")
        SetQBit(QBit(74)) -- Kill all Dragon Slayers and return the Sword of Whistlebone the Slayer to Deftclaw Redreaver in Garrote Gorge.
        evt.SetNPCTopic(21, 1, 61) -- Deftclaw Redreaver topic 1: Dragon Slayers
        evt.SetNPCTopic(66, 1, 61) -- Deftclaw Redreaver topic 1: Dragon Slayers
        return
    end
end)

RegisterGlobalEvent(61, "Dragon Slayers", function()
    if IsQBitSet(QBit(21)) then -- Allied with Charles Quioxte's Dragon Hunters. Return Dragon Egg to Quixote done.
        return
    elseif IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
        evt.SimpleMessage("Have you slain the “Dragon Slayers?\"  Where is the sword of Whistlebone the Slayer?!?")
    else
        evt.SimpleMessage("That cursed knight, Charles Quixote is assembling his best Dragon Slayers at an encampment to the southwest of here.  He must be planning another assault upon the Dragon Caves!")
    end
    return
end)
RegisterCanShowTopic(61, function()
    evt._BeginCanShowTopic(61)
    local visible = true
    if IsQBitSet(QBit(75)) then -- Killed all Dragon Slayers in southwest encampment in Area 5
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(62, "Sword of the Slayer", function()
    evt.ForPlayer(Players.All)
    if not HasItem(540) then -- Sword of Whistlebone
        evt.SimpleMessage("You have killed the Dragon Slayers, but where is the Sword of Whistlebone?  Return to me when you have it!")
        return
    end
    if IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
        evt.SimpleMessage("You return to me with the sword of the Slayer, Whistlebone!  You are indeed worthy of my notice!  The Dragons in your group are promoted to Great Wyrm!  I will teach the others of your group what skills I can as a reward for their assistance!")
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if IsAtLeast(ClassId, 14) then
                SetValue(ClassId, 15)
                AddValue(Experience, 35000)
                SetAward(Award(26)) -- Promoted to Great Wyrm.
                RemoveItem(540) -- Sword of Whistlebone
            else
                AddValue(Experience, 25000)
                SetAward(Award(27)) -- Gave the Sword of Whistlebone the Slayer to the Deftclaw Redreaver.
            end
        end
        evt.ForPlayer(Players.All)
        ClearQBit(QBit(74)) -- Kill all Dragon Slayers and return the Sword of Whistlebone the Slayer to Deftclaw Redreaver in Garrote Gorge.
        evt.SetNPCTopic(21, 2, 736) -- Deftclaw Redreaver topic 2: Promote Dragons
        evt.SetNPCTopic(66, 2, 736) -- Deftclaw Redreaver topic 2: Promote Dragons
        return
    elseif IsQBitSet(QBit(21)) then -- Allied with Charles Quioxte's Dragon Hunters. Return Dragon Egg to Quixote done.
        evt.SimpleMessage("You return to me with the sword of the Slayer, Whistlebone!  Is there no end to the treachery that you will commit? Is there no one that you owe allegiance to?  I will promote those Dragons who travel with you to Great Wyrm, however they will never fly underneath me!  There rest of your traitorous group will be instructed in those skills which can be taught to them!  Go now!  Never show your face here again, unless you want it eaten!")
    else
        evt.SimpleMessage("You return to me with the sword of the Slayer, Whistlebone!  You are indeed worthy of my notice!  The Dragons in your group are promoted to Great Wyrm!  I will teach the others of your group what skills I can as a reward for their assistance!")
    end
for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
    evt.ForPlayer(player)
    if IsAtLeast(ClassId, 14) then
        SetValue(ClassId, 15)
        AddValue(Experience, 35000)
        SetAward(Award(26)) -- Promoted to Great Wyrm.
        RemoveItem(540) -- Sword of Whistlebone
    else
        AddValue(Experience, 25000)
        SetAward(Award(27)) -- Gave the Sword of Whistlebone the Slayer to the Deftclaw Redreaver.
    end
end
evt.ForPlayer(Players.All)
ClearQBit(QBit(74)) -- Kill all Dragon Slayers and return the Sword of Whistlebone the Slayer to Deftclaw Redreaver in Garrote Gorge.
evt.SetNPCTopic(21, 2, 736) -- Deftclaw Redreaver topic 2: Promote Dragons
evt.SetNPCTopic(66, 2, 736) -- Deftclaw Redreaver topic 2: Promote Dragons
return
end)
RegisterCanShowTopic(62, function()
    evt._BeginCanShowTopic(62)
    local visible = true
    if IsQBitSet(QBit(75)) then -- Killed all Dragon Slayers in southwest encampment in Area 5
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(63, "Alliance", function()
    evt.SimpleMessage("Hmmm…things must be serious if trader Loudrin is involving himself in matters other than his own fortunes...and I must say that there is a taint of doom in the air.\n\nIf only for continued good business between my operation and his, I would normally entertain this notion of Loudrin's. Unfortunately, matters here are tying up all of my resources. I have none to spare for support of this alliance you speak of.\n\nSay, perhaps we can help each other? If you were to take care of a little matter for me, I could consider honoring your request.")
    evt.SetNPCTopic(19, 0, 64) -- Sir Charles Quixote topic 0: Quest
    return
end)
RegisterCanShowTopic(63, function()
    evt._BeginCanShowTopic(63)
    local visible = true
    if IsQBitSet(QBit(16)) then -- Form an alliance with the Dragon hunters of Garrote Gorge. - Given by Bastian Lourdrin (area 3). Activates Merchanthouse in Alvar. Taken when Dragon Egg (item 605) delivered to Charles Quixote or dragon leader.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(64, "Quest", function()
    if IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
        return
    elseif IsQBitSet(QBit(31)) then -- Recover the Dragon Egg from Zog's fortress in Ravage Roaming and return it to Charles Quixote in Garrote Gorge. - Given and taken by Quixote (area 5)
        evt.ForPlayer(Players.All)
        if not HasItem(605) then -- Dragon Leader's Egg
            evt.SimpleMessage("Have you recovered the Dragon egg from Zog's Ravage Roaming fortress? Oh, never mind. I can see from your abashed expression that you have not.\n\nI stand firm on our deal. Bring me that egg, or I'll have nothing to do with your alliance!")
            return
        end
        evt.ShowMovie("\"dragonhunters\" ", true)
        evt.SimpleMessage("Well, that matter's done. I will make arrangements to travel to Ravenshore so I myself may sit on your council. Frankly, I could use a bit of change. I will leave my second in command, Reginald Dorray, in charge.\n\nAgain, good job.")
        SetQBit(QBit(21)) -- Allied with Charles Quioxte's Dragon Hunters. Return Dragon Egg to Quixote done.
        SetQBit(QBit(35)) -- Quest 33 is done.
        ClearQBit(QBit(16)) -- Form an alliance with the Dragon hunters of Garrote Gorge. - Given by Bastian Lourdrin (area 3). Activates Merchanthouse in Alvar. Taken when Dragon Egg (item 605) delivered to Charles Quixote or dragon leader.
        ClearQBit(QBit(17)) -- Form an alliance with the Dragons of Garrote Gorge. - Given by Bastian Lourdrin (area 3). Activates Merchanthouse in Alvar. Taken when Dragon Egg (item 605) delivered to Charles Quixote or dragon leader.
        ClearQBit(QBit(31)) -- Recover the Dragon Egg from Zog's fortress in Ravage Roaming and return it to Charles Quixote in Garrote Gorge. - Given and taken by Quixote (area 5)
        ClearQBit(QBit(33)) -- Find the Dragon Egg and return it to the dragon leader, Deftclaw Redreaver. - Given and taken by DRAGON LEADER (area 5)
        evt.SetNPCTopic(19, 0, 0) -- Sir Charles Quixote topic 0 cleared
        evt.SetNPCGreeting(19, 22) -- Sir Charles Quixote greeting: You just caught me. I'm almost ready to leave for Ravenshore, but how may I help you?
        evt.SetNPCTopic(21, 0, 0) -- Deftclaw Redreaver topic 0 cleared
        evt.MoveNPC(443, 0) -- Bazalath -> removed
        evt.ForPlayer(Players.All)
        AddValue(Experience, 20000)
        evt.ForPlayer(Players.All)
        RemoveItem(605) -- Dragon Leader's Egg
        ClearQBit(QBit(204)) -- Dragon Leader's Egg - I lost it, taken event g49, g64
        evt.ForPlayer(Players.Member0)
        AddValue(Gold, 10000)
        evt.ForPlayer(Players.All)
        SetAward(Award(8)) -- Formed an alliance with Charles Quixote and his Dragon Hunters.
        AddValue(History(10), 0)
    else
        evt.SimpleMessage("One of my customers, an Ogre that goes by the charming moniker of \"Zog the Jackal,\" has seriously betrayed my trust. I gave him an item of great value on promise of future payment. This rather large payment never arrived. I sent a messenger to demand return of the item--a Dragon's egg of great potential. This messenger was slain!\n\nNeedless to say, this matter concerns me greatly. I have allotted both money and men for the purpose of revenge. If, however, you were to recover the egg for me from Zog's fortress in Ravage Roaming, I would be glad to pledge service to your alliance.")
        SetQBit(QBit(31)) -- Recover the Dragon Egg from Zog's fortress in Ravage Roaming and return it to Charles Quixote in Garrote Gorge. - Given and taken by Quixote (area 5)
    end
    return
end)

RegisterGlobalEvent(65, "Alliance", function()
    evt.SimpleMessage("You would like my herd to join into an alliance? How could I refuse you? Not only have you saved us from certain death, we have suffered directly from the cataclysm the alliance is being created to fight!\n\nYou have my pledge. With the greatest haste I myself will travel to Ravenshore to take a seat on the alliance council.")
    evt.ForPlayer(Players.All)
    SetAward(Award(9)) -- Formed an alliance with the Minotaurs of Ravage Roaming.
    AddValue(Experience, 20000)
    SetQBit(QBit(23)) -- Allied with Minotaurs. Rescue the Minotaurs done.
    ClearQBit(QBit(18)) -- Form an alliance with the Minotaurs of Ravage Roaming. - Given by Bastian Lourdrin (area 3). Activates Merchanthouse in Alvar. Taken when minotaurs rescued.
    ClearQBit(QBit(30)) -- Rescue the Minotaurs trapped in their lair in Ravage Roaming. - Given by MINOTAUR CLUE GUY (area 8). Turned off when minotaur leader is reached in Minotaur lair dungeon.
    AddValue(History(13), 0)
    evt.SetNPCTopic(13, 0, 0) -- Masul topic 0 cleared
    evt.SetNPCTopic(70, 0, 613) -- Thanys topic 0: Roster Join Event
    evt.SetNPCTopic(70, 1, 0) -- Thanys topic 1 cleared
    evt.SetNPCTopic(70, 2, 0) -- Thanys topic 2 cleared
    return
end)

RegisterGlobalEvent(66, "Flood", function()
    evt.SimpleMessage("It was the worst of horrors! I was on guard in the main labyrinth just north of here when the waters came. A great wave as high as my head flooded through the passages. I managed to reach this high chamber. I waited for others, but there were none. I fear that many of the herd are dead or trapped inside the lair.")
    evt.SetNPCTopic(70, 0, 67) -- Thanys topic 0: Quest
    return
end)

RegisterGlobalEvent(67, "Quest", function()
    if not IsQBitSet(QBit(30)) then -- Rescue the Minotaurs trapped in their lair in Ravage Roaming. - Given by MINOTAUR CLUE GUY (area 8). Turned off when minotaur leader is reached in Minotaur lair dungeon.
        evt.SimpleMessage("Balthazar Lair has many levels. There are other chambers as high as this one., so there may be others who have survived.\n\nI have thought long on this. Though many of the tunnels are flooded, it may be possible to drain them using the doors and air vents as valves. In fact, the whole lair could be drained through the lower level escape tunnel. Help my herd! You would have our eternal gratitude.")
        SetQBit(QBit(30)) -- Rescue the Minotaurs trapped in their lair in Ravage Roaming. - Given by MINOTAUR CLUE GUY (area 8). Turned off when minotaur leader is reached in Minotaur lair dungeon.
        return
    end
    evt.SimpleMessage("I just feel it. There are still survivors of my herd trapped in the lair. If you can figure out how to drain the water from flooded passages, you may be able to reach them. Help them, I beg of you!")
    return
end)

RegisterGlobalEvent(68, "Axe of Balthazar", function()
    evt.SimpleMessage("Balthazar, the greatest leader in the history of our herd, led our warriors in a mighty battle against the Dark Dwarf vermin that erupt from the earth and spread like a plague. It was not a battle that went well for us. Though Balthazar and some warriors escaped, many were lost along with Balthazar's Axe--his regalia of office, and a powerful artifact as well.")
    return
end)

RegisterGlobalEvent(69, "Promotion to Minotaur Lord", function()
    evt.SimpleMessage("Only Masul, our herd leader, can deem an individual worthy of the title of Minotaur Lord.  One way to prove your worth, would be to recover his father’s axe, the Axe of Balthazar from the bowels of the Mines of the Dark Dwarfs.  Set your feet upon the path of this quest, and great is you future!  But we must be sure that the axe you find is indeed the Axe of Balthazar.  Take the Axe to Dadeross, a Minotaur in the service of the Merchants of Alvar, on the island of Dagger Wound.  He will be able to verify the truth of what you find.")
    SetQBit(QBit(76)) -- Find the Axe of Balthazar, in the Dark Dwarf Mines. Have the Axe authenticated by Dadeross. Return the axe to Tessalar, heir to the leadership of the Minotaur Herd.
    evt.SetNPCTopic(71, 0, 71) -- Tessalar topic 0: Quest
end)

RegisterGlobalEvent(70, "Dark Dwarves", function()
    evt.SimpleMessage("These little vermin work with or for the Elements of the Earth.  No one can tell which.  They burrow up from the earth in search of wealth, food, and slaves.  Nothing is left behind where these scavengers have been.")
    return
end)

RegisterGlobalEvent(71, "Quest", function()
    evt.ForPlayer(Players.All)
    if not HasItem(541) then -- Axe of Balthazar
        evt.SimpleMessage("Where is Balthazar's Axe?  You waste my time!  Find the axe, find Dadeross and return to me!")
        return
    end
    if not HasItem(732) then -- Certificate of Authentication
        evt.SimpleMessage("You have found the Axe of Balthazar!  Have you presented it to Dadeross?  Without his authentication, we can not proceed with the Rite’s of Purity!  Find him and return to us once you have presented him with the axe!")
        return
    end
    evt.SimpleMessage("You have found the Axe of Balthazar!  Have you presented it to Dadeross? Ah, you have authentication from Dadeross!  The Rite’s of Purity will begin immediately! You proven yourselves worthy, and our now members of our herd!  The Minotaurs who travel with you are promoted to Minotaur Lord.  The others in your group will be taught what skills we have that maybe useful to them.")
        evt.ForPlayer(player)
        if IsAtLeast(ClassId, 8) then
            SetValue(ClassId, 9)
            AddValue(Experience, 35000)
            SetAward(Award(28)) -- Promoted to Minotaur Lord.
            RemoveItem(541) -- Axe of Balthazar
            RemoveItem(732) -- Certificate of Authentication
        else
            AddValue(Experience, 25000)
            SetAward(Award(29)) -- Recovered Axe of Balthazar.
        end
        evt.ForPlayer(player)
        if IsAtLeast(ClassId, 8) then
            SetValue(ClassId, 9)
            AddValue(Experience, 35000)
            SetAward(Award(28)) -- Promoted to Minotaur Lord.
            RemoveItem(541) -- Axe of Balthazar
            RemoveItem(732) -- Certificate of Authentication
        else
            AddValue(Experience, 25000)
            SetAward(Award(29)) -- Recovered Axe of Balthazar.
        end
        evt.ForPlayer(player)
        if IsAtLeast(ClassId, 8) then
            SetValue(ClassId, 9)
            AddValue(Experience, 35000)
            SetAward(Award(28)) -- Promoted to Minotaur Lord.
            RemoveItem(541) -- Axe of Balthazar
            RemoveItem(732) -- Certificate of Authentication
        else
            AddValue(Experience, 25000)
            SetAward(Award(29)) -- Recovered Axe of Balthazar.
        end
        evt.ForPlayer(player)
        if IsAtLeast(ClassId, 8) then
            SetValue(ClassId, 9)
            AddValue(Experience, 35000)
            SetAward(Award(28)) -- Promoted to Minotaur Lord.
            RemoveItem(541) -- Axe of Balthazar
            RemoveItem(732) -- Certificate of Authentication
        else
            AddValue(Experience, 25000)
            SetAward(Award(29)) -- Recovered Axe of Balthazar.
        end
        evt.ForPlayer(player)
        if IsAtLeast(ClassId, 8) then
            SetValue(ClassId, 9)
            AddValue(Experience, 35000)
            SetAward(Award(28)) -- Promoted to Minotaur Lord.
            RemoveItem(541) -- Axe of Balthazar
            RemoveItem(732) -- Certificate of Authentication
            evt.ForPlayer(Players.All)
        else
            AddValue(Experience, 25000)
            SetAward(Award(29)) -- Recovered Axe of Balthazar.
        end
    ClearQBit(QBit(76)) -- Find the Axe of Balthazar, in the Dark Dwarf Mines. Have the Axe authenticated by Dadeross. Return the axe to Tessalar, heir to the leadership of the Minotaur Herd.
    SetQBit(QBit(87))
    RemoveItem(541) -- Axe of Balthazar
    RemoveItem(732) -- Certificate of Authentication
    evt.SetNPCTopic(71, 0, 740) -- Tessalar topic 0: Promote Minotuars
    return
end)
RegisterCanShowTopic(71, function()
    evt._BeginCanShowTopic(71)
    local visible = true
    if HasItem(732) then -- Certificate of Authentication
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(72, "Balthazar of Ravage Roaming", function()
    if not IsQBitSet(QBit(76)) then -- Find the Axe of Balthazar, in the Dark Dwarf Mines. Have the Axe authenticated by Dadeross. Return the axe to Tessalar, heir to the leadership of the Minotaur Herd.
        evt.SimpleMessage("It was my pleasure to serve under Lord Balthazar, he was the finest herd leader in my tribe’s history.  Unfortunately, my services were pledged to the Merchants of Alvar, or I may have been in the battle where Balthazar fell.  Perhaps my ability and my axe could have saved my lord.  We’ll never know now.")
        return
    end
    evt.SetNPCTopic(2, 3, 73) -- Dadeross topic 3: The Axe of Balthazar
    return
end)

RegisterGlobalEvent(73, "The Axe of Balthazar", function()
    evt.ForPlayer(Players.All)
    if not HasItem(541) then -- Axe of Balthazar
        evt.SimpleMessage("Of course I would know Balthazar's Axe if I saw it!  Do you have it with you?  If you find it, return to me so that I may certify that it is indeed the axe of my late lord, Balthazar.")
        return
    end
    evt.SimpleMessage("Of course I would know Balthazar's Axe if I saw it!  Do you have it with you? This IS the axe!  You must take this back to Tessalar, so the Rite’s of Purity may be performed upon the axe, so it be made ready for the son of Balthazar, Masul.  Take this letter with you, it carries my personal seal, and statement that this is indeed the Axe of Balthazar!")
    evt.ForPlayer(Players.Member0)
    AddValue(InventoryItem(732), 732) -- Certificate of Authentication
    evt.SetNPCTopic(2, 3, 75) -- Dadeross topic 3: Hurry!
end)
RegisterCanShowTopic(73, function()
    evt._BeginCanShowTopic(73)
    local visible = true
    if HasItem(541) then -- Axe of Balthazar
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(74, "Thanks for your help!", function()
    evt.SimpleMessage("Thank you for returning the Axe of Balthazar to us!  When we complete the Rites of Purity, we will present the axe to Masul. It will then be known as the Axe of Masul and surely Masul will be a wise and just herd leader.")
    return
end)

RegisterGlobalEvent(75, "Hurry!", function()
    if not IsQBitSet(QBit(87)) then
        evt.SimpleMessage("You have found Balthazar's Axe and I have authenticated it!  Hurry back to Tessalar so that the Rites of Purity may begin!")
        return
    end
    evt.SimpleMessage("Ah, you returned Balthazar's Axe with my certificate to Tessalar!  The Rites of Purity have begun.  Soon Lord Masul will wield his father's axe as his own!  Greatness will return to my herd!")
    return
end)

RegisterGlobalEvent(76, "Prophecies of the Sun", function()
    evt.ForPlayer(Players.All)
    evt.SimpleMessage("Of the many Prophecies of Jadame, the only ones that I have not be studied are the Prophecies of the Sun.  This temple was established by Tesius Dawnglow, who traveled here from Erathia many years ago to find these Prophecies.  Unfortunately, they were not found.  It is our hope that these Prophecies hold the solution to the events that are destroying Jadame.")
    return
end)
RegisterCanShowTopic(76, function()
    evt._BeginCanShowTopic(76)
    local visible = true
    evt.ForPlayer(Players.All)
    if HasAward(Award(30)) then -- Promoted to Cleric of the Sun.
        visible = true
        return visible
    else
        if HasAward(Award(31)) then -- Found the lost Prophecies of the Sun and returned them to the Temple of the Sun.
            visible = true
            return visible
        else
            visible = false
            return visible
        end
    end
end)

RegisterGlobalEvent(77, "Clues", function()
    evt.ForPlayer(Players.All)
    evt.SimpleMessage("I know that the Prophecies can be found in the Lair of the Feathered Serpent.  However, I have no idea what that means, thus the clue is no help to me. ")
    return
end)
RegisterCanShowTopic(77, function()
    evt._BeginCanShowTopic(77)
    local visible = true
    evt.ForPlayer(Players.All)
    if HasAward(Award(30)) then -- Promoted to Cleric of the Sun.
        visible = false
        return visible
    else
        if HasAward(Award(31)) then -- Found the lost Prophecies of the Sun and returned them to the Temple of the Sun.
            visible = false
            return visible
        else
            visible = true
            return visible
        end
    end
end)

RegisterGlobalEvent(78, "Promtion to Cleric of the Sun", function()
    evt.SimpleMessage("You seek promotion for the clerics of our faith who travel with you.?  I can promote you, but I do not place much trust or faith in strangers these days.  If you were to do something for me, such as finding the lost Prophecies of the Sun, and returning them to me, then I would be agreeable to promoting you.")
    SetQBit(QBit(78)) -- Find the Prophecies of the Sun in the Abandoned Temple and take them to Stephen.
    evt.SetNPCTopic(72, 2, 81) -- Stephen topic 2: Quest
end)

RegisterGlobalEvent(79, "Lair of the Feathered Serpent", function()
    evt.SimpleMessage("Lair of the Feathered Serpent?  That could possibly refer to the poisonous couatl, but they have not been seen for centuries.")
    return
end)

RegisterGlobalEvent(80, "Prophecies of the Sun", function()
    evt.ForPlayer(Players.All)
    evt.SimpleMessage("The Prophecies of the Sun have never been found.  They may not event exist. The Prophecies were written by our greatest prophet.  If they are found it is our hope they will be returned to us!")
    return
end)
RegisterCanShowTopic(80, function()
    evt._BeginCanShowTopic(80)
    local visible = true
    evt.ForPlayer(Players.All)
    if HasAward(Award(30)) then -- Promoted to Cleric of the Sun.
        visible = false
        return visible
    else
        if HasAward(Award(31)) then -- Found the lost Prophecies of the Sun and returned them to the Temple of the Sun.
            visible = false
            return visible
        else
            visible = true
            return visible
        end
    end
end)

RegisterGlobalEvent(81, "Quest", function()
    evt.ForPlayer(Players.All)
    if not HasItem(626) then -- Prophecies of the Sun
        evt.SimpleMessage("Have you found this Lair of the Feathered Serpent and the Prophecies of the Sun?  Do not waste my time!  The world is ending and you waste time with useless conversation!  Return to me when you have found the Prophecies and have taken them to the Temple of the Sun.")
        return
    end
    evt.SimpleMessage("You have found the lost Prophecies of the Sun?  May the Light forever shine upon you and may the Prophet guide your steps.  With these we may be able to find the answer to what has befallen Jadame! ")
    for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
        evt.ForPlayer(player)
        if IsAtLeast(ClassId, 2) then
            SetValue(ClassId, 3)
            AddValue(Experience, 35000)
            SetAward(Award(30)) -- Promoted to Cleric of the Sun.
            RemoveItem(626) -- Prophecies of the Sun
        else
            AddValue(Experience, 25000)
            SetAward(Award(31)) -- Found the lost Prophecies of the Sun and returned them to the Temple of the Sun.
        end
    end
    ClearQBit(QBit(78)) -- Find the Prophecies of the Sun in the Abandoned Temple and take them to Stephen.
    evt.SetNPCTopic(72, 2, 737) -- Stephen topic 2: Promote Clerics
    return
end)
RegisterCanShowTopic(81, function()
    evt._BeginCanShowTopic(81)
    local visible = true
    if HasItem(626) then -- Prophecies of the Sun
        visible = true
        evt.ForPlayer(Players.All)
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(82, "Korbu", function()
    evt.SimpleMessage("Korbu was the most powerful of the Vampire race.  Over one hundred years ago, he sought something that our kind cannot accept.  Absolution.  Somehow, Korbu began to experience guilt over the need to feed.  Or perhaps over the act of feeding itself.  He could no longer bear the thought of killing in order to survive.  Many of our elders argued with him.  He decided to find a place where he could ponder his existence.  Thus the Crypt of Korbu was constructed with slave labor in the Ravage Roaming region.   Korbu has not been heard from since he left.  ")
    return
end)

RegisterGlobalEvent(83, "Quest", function()
    evt.SimpleMessage("In this time of chaos, we need the minds of all our elders.  Return to us with Korbu, or his remains, if he has perished.  If he has indeed perished, you must return his Sarcophagus with him.  We will attempt to reanimate him so that we may consult his wisdom.")
    SetQBit(QBit(80)) -- Find the Sarcophagus of Korbu and Korbu's Remains and return them to Lathean in Shadowspire.
    evt.SetNPCTopic(75, 1, 90) -- Lathean topic 1: Return of Korbu
    return
end)

RegisterGlobalEvent(84, "Korbu", function()
    evt.SimpleMessage("Korbu?  He was the greatest of our kind, and yet he always seemed troubled.  There are some of us that remember the times before he left. He always seemed disturbed to me.")
    return
end)

RegisterGlobalEvent(85, "Korbu", function()
    evt.SimpleMessage("Korbu left us after making the \"Arrangement\" with the necromancers here in Shadowspire.  We aid them in any research they are working on, and assist with the defense of their guild.  In return we are allowed to feed on the local population without hindrance.")
    return
end)

RegisterGlobalEvent(86, "Lich", function()
    evt.SimpleMessage("Ah, you seek to achieve the ultimate in the darker arts.  The necromancer’s among you seek to turn themselves into Liches, the most potent of necromancers.  Very well, I can perform this transformation for you, but you must do something for me...and get something for yourselves.  I require the Lost Book of Khel.  It contains secrets of necromancy that had been hidden since Khel’s tower sank beneath the waves.  The Lizardmen of Dagger Wound celebrated when the sea took Khel and his knowledge from us.  With the volcanic upheaval in that region, I believe the Tower of Khel can be found.  Retrieve the book from the library and bring it to me!  Now, for yourselves, you will need a Lich Jar for every necromancer that wishes to become a Lich.  Zanthora, the Mad Necromancer keeps a large supply of these jars, perhaps she will sell you one!  If not you must take them from her!")
    SetQBit(QBit(82)) -- Find the Lost Book of Khel and return it to Vertrinus in Shadowspire.
    evt.SetNPCTopic(74, 0, 89) -- Vetrinus Taleshire topic 0: Promotion to Lich
    return
end)

RegisterGlobalEvent(87, "Lich Jars", function()
    evt.ForPlayer(Players.All)
    evt.SimpleMessage("The Guild of Necromancers is very stingy when it comes to parting with Lich Jars.  You may be better off seeking out Zanthora, and obtaining one from her.")
    return
end)
RegisterCanShowTopic(87, function()
    evt._BeginCanShowTopic(87)
    local visible = true
    evt.ForPlayer(Players.All)
    if HasAward(Award(34)) then -- Promoted to Lich.
        visible = true
        return visible
    else
        if HasAward(Award(35)) then -- Found the Lost Book of Khel.
            visible = true
            return visible
        else
            visible = false
            return visible
        end
    end
end)

RegisterGlobalEvent(88, "The Lost Book of Khel", function()
    evt.ForPlayer(Players.All)
    evt.SimpleMessage("the Lost Book of Khel is rumored to hold the secrets to the ultimate powers of the dark art of necromancy.  It may be good that no one knows where it is!")
    return
end)
RegisterCanShowTopic(88, function()
    evt._BeginCanShowTopic(88)
    local visible = true
    evt.ForPlayer(Players.All)
    if HasAward(Award(34)) then -- Promoted to Lich.
        visible = true
        return visible
    else
        if HasAward(Award(35)) then -- Found the Lost Book of Khel.
            visible = true
            return visible
        else
            visible = false
            return visible
        end
    end
end)

RegisterGlobalEvent(89, "Promotion to Lich", function()
    evt.ForPlayer(Players.All)
    if not HasItem(611) then -- Lost Book of Kehl
        evt.SimpleMessage("You do not have the Lost Book of Khel!  I cannot help you, if you do not help me!  Return here with the Book and a Lich Jar for each necromancer in your party that wishes to become a Lich!")
        return
    end
    for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
        evt.ForPlayer(player)
        if not IsAtLeast(ClassId, 0) then
            if not HasItem(628) then -- Lich Jar
                evt.SimpleMessage("You have the Lost Book of Khel, however you lack the Lich Jars needed to complete the transformation!  Return here when you have one for each necromancer in your party!")
                return
            end
        end
    end
    evt.SimpleMessage("You have brought everything needed to perform the transformation!  So be it!  All necromancer’s in your party will be transformed into Liches!  May the dark energies flow through them for all eternity!  The rest of you will gain what knowledge I can teach them as reward for their assistance!  Lets begin!\n\nAfter we have completed, good friend Lathean can handle any future promotions for your party.")
    for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
        evt.ForPlayer(player)
        if IsAtLeast(ClassId, 0) then
            SetValue(ClassId, 1)
            AddValue(Experience, 35000)
            SetAward(Award(34)) -- Promoted to Lich.
            RemoveItem(628) -- Lich Jar
        else
            AddValue(Experience, 25000)
            SetAward(Award(35)) -- Found the Lost Book of Khel.
        end
    end
    evt.ForPlayer(Players.All)
    RemoveItem(611) -- Lost Book of Kehl
    ClearQBit(QBit(82)) -- Find the Lost Book of Khel and return it to Vertrinus in Shadowspire.
    evt.SetNPCTopic(74, 0, 742) -- Vetrinus Taleshire topic 0: Travel with you!
    return
end)

RegisterGlobalEvent(90, "Return of Korbu", function()
    evt.ForPlayer(Players.All)
    if HasItem(627) then -- Remains of Korbu
        if not HasItem(612) then -- Sarcophagus of Korbu
            evt.SimpleMessage("You return to us with the remains of Korbu, but where is his Sarcophagus? We cannot complete the act of reanimation without it!  Return to us when you have both the remains and the Sarcophagus!")
            return
        end
        evt.SimpleMessage("You have brought us the Sarcophagus of Korbu and his sacred remains.  We will attempt to reanimate Korbu and seek his wisdom in these troubled times!  The vampires among you will be transformed into Nosferatu, and the others will be taught what skills we can teach them as reward for your service.")
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if IsAtLeast(ClassId, 12) then
                SetValue(ClassId, 13)
                AddValue(Experience, 35000)
                SetAward(Award(32)) -- Promoted to Nosferatu.
                RemoveItem(627) -- Remains of Korbu
                RemoveItem(612) -- Sarcophagus of Korbu
            else
                AddValue(Experience, 25000)
                SetAward(Award(33)) -- Found the Sarcophagus and Remains of Korbu.
            end
        end
        ClearQBit(QBit(80)) -- Find the Sarcophagus of Korbu and Korbu's Remains and return them to Lathean in Shadowspire.
        evt.ForPlayer(Players.All)
        RemoveItem(627) -- Remains of Korbu
        RemoveItem(612) -- Sarcophagus of Korbu
        evt.SetNPCTopic(75, 1, 739) -- Lathean topic 1: Promote Vampires
        return
    elseif HasItem(612) then -- Sarcophagus of Korbu
        evt.SimpleMessage("You return to us with the Sarcophagus of Korbu, but where are his remains? We cannot complete the act of reanimation without them!  Return to us when you have both the Sarcophagus and his remains!")
    else
        evt.SimpleMessage("We need to consult Korbu!  You have agreed to bring us his remains and his Sarcophagus!  Do not bother us until you have these items!")
    end
    return
end)
RegisterCanShowTopic(90, function()
    evt._BeginCanShowTopic(90)
    local visible = true
    if IsQBitSet(QBit(80)) then -- Find the Sarcophagus of Korbu and Korbu's Remains and return them to Lathean in Shadowspire.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(91, "Thanks for your help!", function()
    evt.SimpleMessage("Thank you for finding the Prophecies of the Sun.  May the Sun always light you way and provide you with protection!")
    return
end)

RegisterGlobalEvent(92, "Thanks for your help!", function()
    evt.SimpleMessage("You returned Korbu to us, and we will always be in your debt!  Now leave me, so that I may consult the elders!")
    return
end)

RegisterGlobalEvent(93, "Thanks for your help!", function()
    evt.SimpleMessage("We need to consult Korbu!  You have agreed to bring us his remains and his Sarcophagus!  Do not bother us until you have these items!")
    return
end)

RegisterGlobalEvent(94, "Alliance", function()
    evt.SimpleMessage("Bastian Loudrin has been a great friend to the guild. Sadly, I must refuse his request at this time. Even as we speak, my guild is embroiled in a battle for its very survival. For you see, the Temple of the Sun has declared a holy war on us. Most of our members are away in the fields either leading armies or raising zombies to serve in them.\n\nI wish I could say otherwise, but the accursed temple holds the upper hand. If only the balance would tilt in our favor.")
    evt.SetNPCTopic(9, 0, 95) -- Sandro topic 0: Quest
    return
end)
RegisterCanShowTopic(94, function()
    evt._BeginCanShowTopic(94)
    local visible = true
    if IsQBitSet(QBit(14)) then -- Form an alliance with the Necromancers' Guild in Shadowspire. - Given by Bastian Lourdrin (area 3). Activates Merchanthouse in Alvar. Taken by Sandro (area 6) or when quest 15 is done.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(95, "Quest", function()
    if not IsQBitSet(QBit(28)) then -- Bring the Nightshade Brazier to the Necromancers' Guild leader, Sandro. The Brazier is in the Temple of the Sun. - Given and taken by Sandro (area 6). Taken when Qbit 27 set.
        evt.SimpleMessage("If we had the Nightshade Brazier back in our possession, Shadowspire's defense would not be an issue. We could bring this war to the doors of the Sun Temple. We would annihilate them!\n\nKnowing its importance, the clerics keep the brazier in a secure chamber deep within their temple. Dyson Leland believes he can gain access to that chamber. Bring him to the temple, recover the brazier and return it to me. You want me in your alliance? Well, do this for me, and I will be in your debt.\n\nIf you have any questions about the Nightshade Brazier ask Thant. It was he who created the thing.")
        SetQBit(QBit(28)) -- Bring the Nightshade Brazier to the Necromancers' Guild leader, Sandro. The Brazier is in the Temple of the Sun. - Given and taken by Sandro (area 6). Taken when Qbit 27 set.
        if IsQBitSet(QBit(89)) then -- Dyson Leland talks to you about the Necromancers. For global event 97-100.
            evt.SetNPCTopic(11, 3, 634) -- Dyson Leland topic 3: Roster Join Event
            return
        elseif IsQBitSet(QBit(90)) then -- Dyson Leland talks to you about the Temple of the Sun. For Global event 97-100.
            evt.SetNPCTopic(11, 3, 634) -- Dyson Leland topic 3: Roster Join Event
            return
        else
            return
        end
    end
    evt.SimpleMessage("I will not join you until the security of the guild is secure. Bring me the Nightshade Brazier from the Temple of the Sun in Murmurwoods. We will talk again of alliance after that is done.")
    return
end)

RegisterGlobalEvent(96, "Dyson Leland", function()
    evt.SimpleMessage("Early on our conflict, the Sun Temple attempted to infiltrate our ranks with a spy. Such foolishness--thinking they could so easily deceive a host of dark magicians!\n\nIt was child's play to unmask their agent--one \"Dyson Leland.\" Since then we have turned him against his former masters, or so it would seem. Frankly, I don't entirely trust in his loyalty. Still, he has proven useful. As long as he does, we will continue to let him live.")
    return
end)
RegisterCanShowTopic(96, function()
    evt._BeginCanShowTopic(96)
    local visible = true
    if HasPlayer(34) then -- Dyson Leyland
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(97, "Necromancers", function()
    evt.SimpleMessage("How can anyone's quest for power bring him to participate in the horrors of the Dark Path? And yet, here is a whole house of them! Oh, they will call themselves \"seekers of knowledge,\" but these magicians of death are abomination! Loathsome corruption incarnate!\n\nOnly through my own fear can the foul Necromancers' Guild call itself \"my master.\"")
    SetQBit(QBit(89)) -- Dyson Leland talks to you about the Necromancers. For global event 97-100.
    if not IsQBitSet(QBit(90)) then return end -- Dyson Leland talks to you about the Temple of the Sun. For Global event 97-100.
    if IsQBitSet(QBit(28)) then -- Bring the Nightshade Brazier to the Necromancers' Guild leader, Sandro. The Brazier is in the Temple of the Sun. - Given and taken by Sandro (area 6). Taken when Qbit 27 set.
        evt.SetNPCTopic(11, 3, 634) -- Dyson Leland topic 3: Roster Join Event
        return
    elseif IsQBitSet(QBit(26)) then -- Find the skeleton transformer in the Shadowspire Necromancers' Guild. Destroy it and return to Oskar Tyre. - Given and taken by Oskar Tyre (area 7). Taken when Qbit 29 set.
        evt.SetNPCTopic(11, 3, 634) -- Dyson Leland topic 3: Roster Join Event
    else
        evt.SetNPCTopic(11, 3, 100) -- Dyson Leland topic 3: Join
    end
    return
end)

RegisterGlobalEvent(98, "Sun Temple", function()
    evt.SimpleMessage("When I was young, all I wanted to do was to join the Order of Light--to be a selfless servant of the good. As soon as I was of age, I entered the Temple of the Sun with a heart filled with the fire of purity.\n\nWhat a fool I was. If there is goodness in the world, I have not seen it. There is certainly none in the halls of the Sun Temple! Hiding behind the righteousness of sanctity, Order members perform the worst crimes of greed and self-indulgence. If it were not so horrid, it would pass for something like irony.")
    SetQBit(QBit(90)) -- Dyson Leland talks to you about the Temple of the Sun. For Global event 97-100.
    if not IsQBitSet(QBit(89)) then return end -- Dyson Leland talks to you about the Necromancers. For global event 97-100.
    if IsQBitSet(QBit(28)) then -- Bring the Nightshade Brazier to the Necromancers' Guild leader, Sandro. The Brazier is in the Temple of the Sun. - Given and taken by Sandro (area 6). Taken when Qbit 27 set.
        evt.SetNPCTopic(11, 3, 634) -- Dyson Leland topic 3: Roster Join Event
        return
    elseif IsQBitSet(QBit(26)) then -- Find the skeleton transformer in the Shadowspire Necromancers' Guild. Destroy it and return to Oskar Tyre. - Given and taken by Oskar Tyre (area 7). Taken when Qbit 29 set.
        evt.SetNPCTopic(11, 3, 634) -- Dyson Leland topic 3: Roster Join Event
    else
        evt.SetNPCTopic(11, 3, 100) -- Dyson Leland topic 3: Join
    end
    return
end)

RegisterGlobalEvent(99, "Yourself", function()
    evt.SimpleMessage("A few months ago, I was called to a private audience with the Sun Temple head priest, Oskar Tyre. He sent me out on a mission of infiltration against the Necromancers' Guild. \"Become as they are,\" he said. \"Gain their trust. While you bide your time waiting to deliver a killing blow, feed us their secrets.\"\n\nA too simple plan from too simple a leader! Oh, I did as he said, bathing myself in evil so I might seem evil. But it was as if the guild could see into my heart. I was unmasked as a spy. Under threat of death, I now follow their orders. ")
    return
end)

RegisterGlobalEvent(100, "Join", function()
    evt.SimpleMessage("Join with you? An interesting idea. But what can you offer me? After all I have been through I find myself consumed with a thirst for revenge. I would go with you, but am unwilling to spend my efforts lightly. Give me an opportunity to hurt one of my enemies--the cursed Temple of the Sun or the abominable Necromancers' Guild--and I will travel with you gladly.")
    return
end)

RegisterGlobalEvent(101, "Thant", function()
    evt.SimpleMessage("Now that the Nightshade Brazier covers Shadowspire in its fortifying darkness. Thant goes to lead his minions.")
    return
end)

RegisterGlobalEvent(102, "Alliance", function()
    evt.SimpleMessage("Certainly the elemental unrest concerns us greatly. Why one need travel only a short distance north from our temple to see a great maelstrom of unnatural duration and fury. But sadly we have other matters pressing.\n\nThe sick horror that is the Necromancers' Guild must be blighted from this land! We wage holy war on the evil in Shadowspire. Our entire spirit and power goes into the campaign we wage against Sandro and his minions. Until that is done we cannot entertain participation in your alliance.")
    evt.SetNPCTopic(37, 0, 103) -- Oskar Tyre topic 0: Quest
    return
end)
RegisterCanShowTopic(102, function()
    evt._BeginCanShowTopic(102)
    local visible = true
    if IsQBitSet(QBit(15)) then -- Form an alliance with the Temple of the Sun in Murmurwoods. - Given by Bastian Lourdrin (area 3). Activates Merchanthouse in Alvar. Taken by Oskar Tyre (area 7), or when quest 27 is done.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(103, "Quest", function()
    if IsQBitSet(QBit(27)) then -- Skeleton Transformer Destroyed.
        evt.SimpleMessage("Excellent work! With the Skeleton Transformer destroyed, I am more than confident that the light of righteousness will cleanse Shadowspire of evil. The Necromancers' Guild is as good as no more.\n\nAs I agreed, you may now consider the Temple of the Sun an ally against the elemental cataclysm. I myself will sit on your alliance council in Ravenshore. I will make my departure arrangements with all due haste.")
        ClearQBit(QBit(26)) -- Find the skeleton transformer in the Shadowspire Necromancers' Guild. Destroy it and return to Oskar Tyre. - Given and taken by Oskar Tyre (area 7). Taken when Qbit 29 set.
        ClearQBit(QBit(14)) -- Form an alliance with the Necromancers' Guild in Shadowspire. - Given by Bastian Lourdrin (area 3). Activates Merchanthouse in Alvar. Taken by Sandro (area 6) or when quest 15 is done.
        ClearQBit(QBit(15)) -- Form an alliance with the Temple of the Sun in Murmurwoods. - Given by Bastian Lourdrin (area 3). Activates Merchanthouse in Alvar. Taken by Oskar Tyre (area 7), or when quest 27 is done.
        ClearQBit(QBit(28)) -- Bring the Nightshade Brazier to the Necromancers' Guild leader, Sandro. The Brazier is in the Temple of the Sun. - Given and taken by Sandro (area 6). Taken when Qbit 27 set.
        SetQBit(QBit(20)) -- Allied with Temple of the Sun. Destroy the Skeleton Transformer done.
        evt.SetNPCTopic(37, 0, 0) -- Oskar Tyre topic 0 cleared
        AddValue(History(11), 0)
        evt.ForPlayer(Players.All)
        AddValue(Experience, 50000)
        evt.ForPlayer(Players.Member0)
        AddValue(Gold, 10000)
        evt.ForPlayer(Players.All)
        SetAward(Award(11)) -- Formed and alliance with the Temple of the Sun.
        return
    elseif IsQBitSet(QBit(26)) then -- Find the skeleton transformer in the Shadowspire Necromancers' Guild. Destroy it and return to Oskar Tyre. - Given and taken by Oskar Tyre (area 7). Taken when Qbit 29 set.
        evt.SimpleMessage("You come here again with talk of alliance? I have told you what you must do. Go to the Necromancers' Guild in Shadowspire, find Dyson Leland and help him to destroy their Skeleton Transformer!")
    else
        evt.SimpleMessage("Then again, we could spare some resources for your alliance if the war would turn in our favor. Perhaps you could be our agent of fortune?\n\nInside the Necromancers' Guild is a device known as the \"Skeleton Transformer.\" It converts living creatures into the skeletons which the dark mages use for the bulk of their reinforcements. If it were destroyed, we would quickly have the upper hand.\n\nWe have an agent, Dyson Leland, placed in their guild. Find him and help him to wreck their skeleton making device. Do this and I will consider your request more favorably.")
        SetQBit(QBit(26)) -- Find the skeleton transformer in the Shadowspire Necromancers' Guild. Destroy it and return to Oskar Tyre. - Given and taken by Oskar Tyre (area 7). Taken when Qbit 29 set.
    end
    return
end)

RegisterGlobalEvent(104, "Alliance", function()
    evt.SimpleMessage("Do you take the prophecy so lightly that you shirk the role it has cast for you? These are dire times calling for dire actions from all. Go forth across the land and forge the unity represented by the alliance. Go, unless you favor the oblivion that threatens us!")
    return
end)

RegisterGlobalEvent(105, "Strange Gateways", function()
    evt.SimpleMessage("Using Arion Hunter's boats we have managed to gather some information. I sent one to Ravage Roaming and another to the Dagger Wound Islands. It is reported that strange portal gateways have appeared in both regions. The gateway in the islands stands on the slopes of the large volcano that rose from the sea southeast of the main island. The Ravage Roaming portal is in the middle of the large lake. It is said that the water which formed the lake flooded out of the gateway.")
    return
end)

RegisterGlobalEvent(106, "Ironfists", function()
    evt.SimpleMessage("Within hours of our first meeting, a most fortuitous development occurred. We were contacted by a great sage, Xanthor, of the Ironfist courts of Enroth!\n\nUsing his great magic, he projected his image into this very chamber. He and Roland and Catherine Ironfist were at sea off our shores when the cataclysm occurred. They survived the resulting storms and now would like to land in Ravenshore to aid the alliance. Unfortunately, they are blocked by the Regnan pirate fleet. We must help them to land. Xanthor claims much knowledge of what has happened here. We need his council!")
    evt.SetNPCTopic(53, 0, 107) -- Elgar Fellmoon topic 0: Quest
    return
end)

RegisterGlobalEvent(107, "Quest", function()
    if IsQBitSet(QBit(37)) then -- Regnan Pirate Fleet is sunk.
        evt.SimpleMessage("Your good work sinking the Regnan fleet has already had the desired results. Just yesterday morning, Catherine and Roland Ironfist arrived along with their sage, Xanthor. With them in the alliance, we are made stronger--immeasurably so.\n\nI will admit that the time of this crisis has contained some of my darkest moments. Thanks to your efforts I believe that the worst of this is over. I have hopes that we will indeed survive this.")
        ClearQBit(QBit(36)) -- Sink the Regnan Fleet. Return to the Ravenshore council chamber. - Given and taken at Ravenshore council chamber.
        SetQBit(QBit(38)) -- Quest 36 is done.
        evt.SetNPCTopic(53, 0, 109) -- Elgar Fellmoon topic 0: Xanthor
        evt.ForPlayer(Players.All)
        AddValue(Experience, 100000)
        evt.ForPlayer(Players.Member0)
        AddValue(Gold, 10000)
        evt.ForPlayer(Players.All)
        SetAward(Award(12)) -- Sunk the Regnan fleet allowing Roland and Catherine Ironfist to join the alliance.
        return
    elseif IsQBitSet(QBit(36)) then -- Sink the Regnan Fleet. Return to the Ravenshore council chamber. - Given and taken at Ravenshore council chamber.
        evt.SimpleMessage("You must sink that Regnan fleet! It is imperative that the Ironfists be allowed to land safely. Their sage Xanthor has knowledge of the crisis that we cannot do without.")
    else
        evt.SimpleMessage("Our sources believe the main Regnan fleet is in a hidden port somewhere on Regna Island. If you could sink the fleet in dock you could greatly cripple their ability to patrol the seas off our shore. Unfortunately, we don't have a fleet of our own strong enough to make a landing on Regna.\n\nBrekish Onefang has gotten message to us that the Regnans have built an outpost on an atoll off the main Dagger Wound Island. He believes this outpost is resupplied by mysterious means. His scouts never see ships land there, but they are always well stocked. Perhaps you should go there and solve the mystery. Perhaps the answer will convey you to Regna?\n\nRegardless of the means, the Regnan fleet must be sunk if the Ironfists are to land in Ravenshore.")
        SetQBit(QBit(36)) -- Sink the Regnan Fleet. Return to the Ravenshore council chamber. - Given and taken at Ravenshore council chamber.
        AddValue(History(14), 0)
    end
    return
end)

RegisterGlobalEvent(108, "Pirates", function()
    evt.SimpleMessage("For all their claims of empire and their airs of civilization, the Regnans are the worst scum of Jadame. Why I cannot find myself the least bit surprised that they would take advantage of the crisis to expand their pirating operations. What concerns me most is their new outpost on Dagger Wound. I am sure they mean to use it as a base of attack on the continent. Why, it even puts them in striking distance of Ravenshore!")
    return
end)

RegisterGlobalEvent(109, "Xanthor", function()
    evt.SimpleMessage("I have only met with him briefly, but I am convinced that Xanthor is remarkably knowledgeable about the workings of the elemental planes. Apparently he learned much from the Ironfists' elemental allies during their recent campaigns against the devils of Erathia.\n\nEven now he studies the strange crystal in the town square. You may find him there, or perhaps in the nearby residence we have provided him.")
    evt.SetNPCTopic(53, 0, 110) -- Elgar Fellmoon topic 0: Quest
    return
end)

RegisterGlobalEvent(110, "Quest", function()
    if not IsQBitSet(QBit(91)) then -- Consult the Ironfists' court sage, Xanthor about the Ravenshore crystal. - Given by NPC 53 (Fellmoon), taken by XANTHOR.
        evt.SimpleMessage("We of the council have great faith in this Xanthor. He has told me that he is formulating a plan for dealing with the elemental crisis. If anyone can find a solution to our problems, it is he.\n\nIf you would help us further, be of service to this great sage. Consult with him about the crystal and see what you might do for him.")
        SetQBit(QBit(91)) -- Consult the Ironfists' court sage, Xanthor about the Ravenshore crystal. - Given by NPC 53 (Fellmoon), taken by XANTHOR.
        evt.MoveNPC(23, 276) -- Xanthor -> Hostel
        evt.MoveNPC(77, 0) -- Derrin Delver -> removed
        return
    end
    evt.SimpleMessage("We look to Xanthor to formulate our next actions. Go to him and see how you can help.")
    return
end)

RegisterGlobalEvent(111, "Ironfists' Arrival", function()
    evt.SimpleMessage("That we have been joined by the royal court of Enroth has been nothing but good. I was worried they would be afflicted with the need for pomp which infects many other monarchs. I am gladdened to report that this is not the case with this king and queen. They disembarked and set directly to work on our problem. As key members of our alliance, you will find access to them easy. We have put them up in houses here in Ravenshore.")
    return
end)

RegisterGlobalEvent(112, "Plane of Fire", function()
    evt.SimpleMessage("From what Xanthor has told us, I'm sure all of the elemental planes are dangerous. Still, I would advise you to take particular caution when exploring the Plane of Fire. Its denizens, according to reports from the Ironsand Desert, are being particularly belligerent.")
    return
end)

RegisterGlobalEvent(113, "Plane Between Planes", function()
    evt.SimpleMessage("All I know of the Plane Between Planes is what I learned from the Alvarian loremasters. Still, if the Destroyer's base is there, proceed with the greatest caution! It is said the plane is made of the stuff of chaos from which all the other planes are formed as if from clay. While chaos has a form, it is fluid. Whatever you see there will not be as it seems. And what is there may be subject to continuous change.")
    return
end)

RegisterGlobalEvent(114, "Elemental Lord Prisons", function()
    evt.SimpleMessage("What the Alvar loremasters told me of the Plane Between Planes applies here. While I am sure the prisons of the elemental lords are prisons in every sense of the word, I am equally sure that they will not appear as one would expect.")
    return
end)

RegisterGlobalEvent(115, "Merchant House", function()
    evt.SimpleMessage("The Merchant Guild of Alvar owes you a great debt. As a small measure of repayment, we have decided to make this merchanthouse permanently available to you. Please take this gift from us as a token of our profound gratitude for your valorous deeds.")
    return
end)

RegisterGlobalEvent(116, "Dragon Hunting", function()
    evt.SimpleMessage("I know being part of your alliance is important work. Still, I do miss the hunt! I keep imagining all the good fun my men are having while I'm here pushing around papers.\n\nHurry up with this alliance business! I want to get this mess taken care of with dispatch! Without the thrill of the hunt, my life is missing its usual spark.")
    return
end)

RegisterGlobalEvent(117, "Blackwell Cooper", function()
    evt.SimpleMessage("Judging from the tactics employed by the Regnan pirates, I suspect that Blackwell Cooper is involved. Cooper is an old…shall we say, \"associate,\" of mine. Why, if I were a gambling man, I'd bet gold that he is leading the Regnan expeditionary force on Dagger Wound.")
    return
end)

RegisterGlobalEvent(118, "Xanthor", function()
    evt.SimpleMessage("I know I hold the council's minority opinion on the subject, but really, I don't see why we have to involve some charlatan magician in this matter! Surely this crisis is solvable, like most things, with judicious application of a length of well-forged steel.")
    return
end)

RegisterGlobalEvent(119, "Raising an Army", function()
    evt.SimpleMessage("Fah! If you ask me, this idea of Xanthor's is foolhardy! I say if we're facing attack by elemental armies, we should be raising an army to meet them. Frankly, all this talk of prophecy leaves me uneasy. This council is too much under the sway of the Ironfist's pet wizard. I say we take the fight to the elemental planes and introduce the invaders to the sharp edges of our blades!")
    return
end)

RegisterGlobalEvent(120, "Plane Between Planes", function()
    evt.SimpleMessage("I tell you, this Xanthor is sending you on a wild goose chase. \"Plane Between Planes,\" indeed! What hogwash! The worst of it is that we make no preparations for war in the event the crazy scheme fails, which I expect it will. This mad following of prophecy flies in the face of good military sense!")
    return
end)

RegisterGlobalEvent(121, "Xanthor", function()
    evt.SimpleMessage("I have had more of my share of doubts about this Xanthor, but it is the mark of a man how readily he admits his errors. It is clear to me now that he has given nothing but good and effective advise. If he tells you to rescue the elemental lords, then that is what you must do. Go! And good luck!")
    return
end)

RegisterGlobalEvent(122, "Dragon Hunting", function()
    evt.SimpleMessage("Good to see you again, Heroes of Jadame. A good job there, saving the world, and all. You certainly have my thanks, and I'm sure, the thanks of many.\n\nI'm sure you've got plenty of other opportunities at this point, but let me know if you want a job hunting Dragons. Probably not much of a challenge for the likes of you, but the offer stands!")
    return
end)

RegisterGlobalEvent(123, "Accommodations", function()
    evt.SimpleMessage("Small ones, hurry with your alliance preparations! My patience with this land lacking in caves and prey grows dangerously thin. Not only must I sleep in a barn, these people do not even raise cattle. I must live off of fish! Fah!\n\nIf you value my good temper, be quick!")
    return
end)

RegisterGlobalEvent(124, "Regna Island", function()
    evt.SimpleMessage("Reaching Regna Island is no small challenge. One of my scouts has reported to me that Regnan boats lie thick on the sea. He also said he saw that the Regnans have a craft that can travel beneath the water. It is said they supply their Dagger Wound outpost with the craft. Perhaps you can use it to reach Regna. The pirates will either miss your passage or take you for one of their own.")
    return
end)

RegisterGlobalEvent(125, "Quixote's Treasure", function()
    evt.SimpleMessage("I know this is not the time to think of revenge, but I would pass onto you something I learned about my enemy, Charles Quixote. The Minotaur king, Masul, mentioned that Quixote keeps a sword of great power with him in his keep. It is called, \"Snake.\" Perhaps your acquiring of it would help the alliance cause?")
    return
end)

RegisterGlobalEvent(126, "Gateways", function()
    evt.SimpleMessage("My Dragon patrols have located two of the elemental gateways. One lies on the side of a large volcano southeast of the largest Dagger Wound Islands. The other is located in the center of the large lake in Ravage Roaming. I know not where they lead, but you will have to cross a lot of water to reach either.")
    return
end)

RegisterGlobalEvent(127, "Crystal Dragons", function()
    evt.SimpleMessage("An Erathian Dragon visited my cave shortly before you arrived there. He reported to me that a new type of Dragon, one seemingly made of crystalline rock, has been seen in Erathia. I'm not sure why I tell you this. Perhaps the giant crystal in the town square reminds me of the story. ")
    return
end)

RegisterGlobalEvent(128, "The Destroyer", function()
    evt.SimpleMessage("Interesting that the Destroyer himself sends you to undo his works. I guess I am not surprised. The workings of the greater Powers are mysterious at best.")
    return
end)

RegisterGlobalEvent(129, "Great Deeds", function()
    evt.SimpleMessage("You have done this land and Dragonkind a great service. For this, we owe you. Know that we will tolerate your presence in our caves, further, we will not hunt you as prey.")
    return
end)

RegisterGlobalEvent(130, "The Light", function()
    evt.SimpleMessage("Did you know that our temple in Murmurwoods is the first in this land of Jadame? It is our mission to bring the Light to all corners of the world--even here. We were surprised to see that our enemies, the Necromancers' Guild had preceded our arrival with their own. But no matter, they will soon be dealt with.\n\nSay, don't you think this merchant house would make a fine Sun Temple? I will bring it up with Fellmoon after the crisis is over.")
    return
end)

RegisterGlobalEvent(131, "Mace of the Sun", function()
    evt.SimpleMessage("If you're off to Regna, you might want to look for the Mace of the Sun. When my brothers and I made the crossing from Erathia, we were attacked by the Regnan fleet. All but one of our ships escaped. Sadly, the lost ship was the one carrying the mission leader, Brother Howe. He had the weapon in his possession. I saw Brother Howe slain by the pirates, but perhaps they still have the mace.")
    return
end)

RegisterGlobalEvent(132, "Ironfists", function()
    evt.SimpleMessage("I am pleased with these Ironfists and their sage, Xanthor. Though we have never worked together directly, their work in Enroth and Erathia against the Necromancers' Guild and the devils have clearly marked them as servants of The Light. I have full faith in their plans for saving us from the crisis.")
    return
end)

RegisterGlobalEvent(133, "Plane of Air", function()
    evt.SimpleMessage("The Sun Temple has had much time to study the gateway which appeared in Murmurwoods. I am positive it leads to the Plane of Air. On several occasions my brothers have seen air spirits around the gateway. Some of the braver have peered through it and have reported seeing a whirling realm of clouds.")
    return
end)

RegisterGlobalEvent(134, "Source of the Crisis", function()
    evt.SimpleMessage("As a Priest of the Light, I have my own ideas about the source of the crisis. I am positive that either the Temple of the Moon or the Necromancers' Guild is somehow involved. Great Light! What if they've banded together? What a horrid thought.")
    return
end)

RegisterGlobalEvent(135, "Devils", function()
    evt.SimpleMessage("I'm not sure you can trust the words of this so called, \"Destroyer.\" Certainly he is not the Destroyer of scripture. And all this talk of Kreegans and men living on many worlds. It flies in the face of the Truth my temple has shepherded from the beginning of time!")
    return
end)

RegisterGlobalEvent(136, "Servants of the Light", function()
    evt.SimpleMessage("It is good to have you with us, Heroes of Jadame. Know that the Temple of the Sun also considers you servants of the Light. You are always welcome among us.")
    return
end)

RegisterGlobalEvent(137, "The Library", function()
    evt.SimpleMessage("I wish my first visit to Ravenshore was made under better circumstances. This town has a lot to offer and I wish I had time to explore it more. On the bright side, this merchant house has a great library. Have you seen it?")
    return
end)

RegisterGlobalEvent(138, "Pirate Raid", function()
    evt.SimpleMessage("The Regnans have built and outpost on one of the Dagger Wound Islands. We fear they may attack Ravenshore. If this happens, we will evacuate the city. We will return once the garrison has rid Ravenshore of pirates.")
    return
end)
RegisterCanShowTopic(138, function()
    evt._BeginCanShowTopic(138)
    local visible = true
    if IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(139, "Catherine Ironfist", function()
    evt.SimpleMessage("When I became herd leader, I never expected my reign would be so full of rich experience. Certainly I never thought I'd meet anyone like Queen Catherine! Did you know that until she abdicated her rule in Erathia, she was ruler of both it and Enroth?")
    return
end)

RegisterGlobalEvent(140, "Plane of Water", function()
    evt.SimpleMessage("As you know, the gateway leading to the Plane of Water appeared near Balthazar Lair in Ravage Roaming. It lies in the middle of the lake created by the great flood that poured forth from it.")
    return
end)

RegisterGlobalEvent(141, "Iron Rations", function()
    if not IsQBitSet(QBit(99)) then -- Masul gave party food.
        evt.SimpleMessage("You may have difficulty finding supplies in the lands beyond the crystal. When I left Balthazar Lair, I brought with me a quantity of the iron rations carried by my armies on campaign. Here, take what I have. They are light and nourishing. I hope you find them useful.")
        AddValue(Food, 20)
        SetQBit(QBit(99)) -- Masul gave party food.
        return
    end
    evt.SimpleMessage("I have no more rations to give. If you need more, you'll have to find food elsewhere.")
    return
end)

RegisterGlobalEvent(142, "Salvation", function()
    evt.SimpleMessage("Why if the imprisonment of the elemental lords is what started this crisis, then surely releasing them is the way to end it! They are beings of almost unimaginable power. Once freed of the Destroyer's control, they would be able to set things right again. This must be what the prophecy speaks of!")
    return
end)

RegisterGlobalEvent(143, "Keys to the City", function()
    evt.SimpleMessage("It cannot be said enough. My herd as well as all the beings of Jadame are forever in your debt. Thanks to your good work here and in the planes, Balthazar Lair can once again know greatness. You and your comrades are welcome here any time you wish to visit. A blessing on you all!")
    return
end)

RegisterGlobalEvent(144, "Temple of the Sun", function()
    evt.SimpleMessage("I can't help feeling that I could be doing better work elsewhere. I'm sure Thant can handle operation of the guild in my absence, but still, sitting here on my hands while we are at war with the Sun Temple tries my patience. You really must be quicker about your duties!")
    return
end)

RegisterGlobalEvent(145, "Pirate Mages", function()
    evt.SimpleMessage("When one thinks of the Regnans, the phrase \"masters of magic\" doesn't normally come to mind. But I caution you, the Regnan pirates have held their island for many centuries. They have had much time to both acquire and study arcane knowledge. Some powerful magicians live there. If you must face them in combat, be prepared for anything.")
    return
end)

RegisterGlobalEvent(146, "Wizards", function()
    evt.SimpleMessage("It is not true that we of the Necromancers' Guild do not respect mages of other schools. That they have chosen paths leading to lesser powers is of their own concerns. This Xanthor is formidable for a wizard not of the Dark Path. As much as is possible, I find his advise, passably worthy.")
    return
end)

RegisterGlobalEvent(147, "Ring of Planes", function()
    evt.SimpleMessage("I have learned that the Dark Dwarves of Alvar hold an item I have long coveted, but may be of particular use to you if you when you travel among the elemental planes. The Ring of Planes conveys upon its wearer powerful wards against damaging spells of earth, water, air, and fire.")
    return
end)
RegisterCanShowTopic(147, function()
    evt._BeginCanShowTopic(147)
    local visible = true
    if HasItem(519) then -- Ring of Planes
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(148, "Nightmares", function()
    evt.SimpleMessage("In my studies I have learned something of this Plane Between Planes. It is written that its denizens are not born in the normal fashion. I have heard that creatures can be found there which manifest the energies of the nightmare dreams of humankind. I have little more information, but I imagine such a creature would be both powerful and malevolent.")
    return
end)

RegisterGlobalEvent(149, "Elemental Wars", function()
    evt.SimpleMessage("A basic fact of magic is that Fire opposes Water, and Air opposes Earth. Within these parings, the one element has weaknesses regarding its opposite element. I expect the Destroyer exploits this principle in the construction of his prisons.")
    return
end)

RegisterGlobalEvent(150, "Safety", function()
    evt.SimpleMessage("I know I speak for the guild when I say we owe you a debt of gratitude. I discharge this debt by granting you and your companions safe passage through all lands under our control. No guild member will kidnap you for arcane experimentation, nor will any member consider you feed for his servants, living or otherwise. This guild edict will be in effect for a period of one year from today.\n\nAnd of course, you have my personal, thanks.")
    return
end)

RegisterGlobalEvent(151, "Xanthor", function()
    evt.SimpleMessage("The master is not here at present. He went to consult with Elgar Fellmoon at the council chamber. Perhaps you will find him there.")
    return
end)

RegisterGlobalEvent(152, "The Crystal", function()
    evt.SimpleMessage("The crystal placed by the Destroyer in the town square serves two functions. One, if we do nothing, it will destroy the world. Two, it acts as a gateway to another realm of existence--the Plane Between Planes--where the Destroyer most certainly has his base.\n\nThe crystal calls forth the elemental forces into our world and draws them to it. When these forces meet here at the crystal, the world will be destroyed in cataclysm. If we are to prevent this someone will have to use the crystal as a gateway to reach the Destroyer and either convince him to end his assault, or eliminate him.")
    ClearQBit(QBit(91)) -- Consult the Ironfists' court sage, Xanthor about the Ravenshore crystal. - Given by NPC 53 (Fellmoon), taken by XANTHOR.
    SetQBit(QBit(92)) -- Quest 91 done.
    evt.SetNPCTopic(23, 0, 153) -- Xanthor topic 0: Quest
    evt.SetNPCTopic(23, 1, 154) -- Xanthor topic 1: Gateway
    return
end)

RegisterGlobalEvent(153, "Quest", function()
    if not IsQBitSet(QBit(41)) then -- Bring the Heart of Water from the Plane of Water to Xanthor. - Given by XANTHOR. Taken when 41-44 done simultaneously.
        evt.SimpleMessage("Since the crystal is attuned to the elemental forces, it will only pass through those who are themselves so attuned. I believe it is possible to create a key that will simulate attunement for a small group such as yourselves. I can make the key, but require components of pure elemental forces to do so.\n\nSuch components exist in only one form that I know of. On each of the four elemental planes, you will find gemstones called the \"elemental hearts.\" Bring these to me and I will build the key to open the crystal gateway.")
        SetQBit(QBit(41)) -- Bring the Heart of Water from the Plane of Water to Xanthor. - Given by XANTHOR. Taken when 41-44 done simultaneously.
        SetQBit(QBit(42)) -- Bring the Heart of Air from the Plane of Air to Xanthor. - Given by XANTHOR. Taken when 41-44 done simultaneously.
        SetQBit(QBit(43)) -- Bring the Heart of Earth from the Plane of Earth to Xanthor. - Given by XANTHOR. Taken when 41-44 done simultaneously.
        SetQBit(QBit(44)) -- Bring the Heart of Fire from the Plane of Fire to Xanthor. - Given by XANTHOR. Taken when 41-44 done simultaneously.
        AddValue(History(16), 0)
        evt.SetNPCTopic(53, 0, 0) -- Elgar Fellmoon topic 0 cleared
        evt.SetNPCTopic(53, 1, 112) -- Elgar Fellmoon topic 1: Plane of Fire
        evt.SetNPCTopic(65, 0, 119) -- Sir Charles Quixote topic 0: Raising an Army
        evt.SetNPCTopic(66, 0, 126) -- Deftclaw Redreaver topic 0: Gateways
        evt.SetNPCTopic(67, 0, 133) -- Oskar Tyre topic 0: Plane of Air
        evt.SetNPCTopic(68, 0, 140) -- Masul topic 0: Plane of Water
        evt.SetNPCTopic(69, 0, 147) -- Sandro topic 0: Ring of Planes
        return
    end
    evt.ForPlayer(Players.All)
    if HasItem(606) then -- Heart of Fire
        evt.SimpleMessage("I am glad that you have had some measure of success in retrieving the elemental hearts, but what you have is not enough. I need one from each of the four elemental planes before I can build the key to the crystal gateway. Bring me the rest of the hearts so we can proceed.")
        return
    elseif HasItem(607) then -- Heart of Water
        evt.SimpleMessage("I am glad that you have had some measure of success in retrieving the elemental hearts, but what you have is not enough. I need one from each of the four elemental planes before I can build the key to the crystal gateway. Bring me the rest of the hearts so we can proceed.")
        return
    elseif HasItem(608) then -- Heart of Air
        evt.SimpleMessage("I am glad that you have had some measure of success in retrieving the elemental hearts, but what you have is not enough. I need one from each of the four elemental planes before I can build the key to the crystal gateway. Bring me the rest of the hearts so we can proceed.")
        return
    elseif HasItem(609) then -- Heart of Earth
        evt.SimpleMessage("I am glad that you have had some measure of success in retrieving the elemental hearts, but what you have is not enough. I need one from each of the four elemental planes before I can build the key to the crystal gateway. Bring me the rest of the hearts so we can proceed.")
    else
        evt.SimpleMessage("To go through the crystal gateway and confront the Destroyer, you need the key I must build! To build this key, I need the elemental heart gemstones from the four elemental planes! Go and get these for me!")
    end
    return
end)

RegisterGlobalEvent(154, "Gateway", function()
    evt.SimpleMessage("Something about this crystal seems to put a compulsion on the denizens of the elemental planes. Why else would they make war on our plane? I have heard yours and other first hand reports. It seems almost as if these elementals are driven by a madness.\n\nAnd madness it is! For destroying Enroth would create a mighty planar unbalance which would certainly victimize their own planes. They might even conceivably be themselves destroyed in the cataclysm. At the very least, they risk changing the nature of their own planes. I cannot see how such change could possibly be for the better!")
    return
end)

RegisterGlobalEvent(155, "Elemental Lords", function()
    evt.SimpleMessage("That the elemental lords are imprisoned on the Plane Between Planes explains much. I had wondered why the denizens of the Earth, Air, Water, and Fire Planes have become so hostile. Usually, they are content to keep to their own place in the order. I suppose it was necessary for the Destroyer to take the lords from their homelands. Without the lords calming presence, it would be much easier for him to compel the elementals as he has.\n\nIt is important for you to free the elemental lords. They can restore order to their planes and prevent the cataclysm!")
    return
end)

RegisterGlobalEvent(156, "The Destroyer", function()
    evt.SimpleMessage("Yes, I have heard the name, \"Escaton.\" He is variously called in the legends of many cultures. I know not his nature, but it is his purpose to destroy worlds.\n\nYes, \"worlds,\" I say. More and more evidence points to the conclusion that Enroth is not the only place in this universe where there is life. Tales from before the Silence speak of many living among the stars. Yes, it sounds impossible to think that one could live on a light in the sky, but consider that these stars may be like our sun. If this is so, then why can't these suns shine on other places like Enroth? If this was the case, then there could be a \"destroyer of worlds.\" I believe that this is what we face.")
    return
end)

RegisterGlobalEvent(157, "Leaving", function()
    evt.SimpleMessage("No, I don't think I will be leaving when the Ironfists continue their journey back to Enroth. Perhaps I will join with them in some years, but for now, I find myself fascinated by these lands. Though it is destroyed, I would study the remains of the crystal gateway. Never in my knowledge has there been in this world an artifact of comparable power. Perhaps I will find some use for the crystal shards?\n\nNo matter. Regardless, when the Ironfists go, they will go without me.")
    return
end)

RegisterGlobalEvent(158, "Nightshade Brazier", function()
    evt.SimpleMessage("Without false modesty I must say that the Nightshade Brazier is the greatest creation of my dark arts. When its fires are properly tended, the accursed sun is incapable of shining within its area of influence. The soothing shadow of night takes up permanent residence over a vast region. Within these boundaries, vampires and other night creatures know freedoms they would not otherwise know. We are free of the crypts with no worries of the destroying light of day!\n\nAnd now the Temple of the Sun has taken my prize. It must be retrieved!")
    return
end)

RegisterGlobalEvent(159, "Who Are You?", function()
    evt.SimpleMessage("I am Escaton the Destroyer also called \"Devil's Doom,\" \"The Spider in the Web Gate\" and \"Ruin.\" There are places where I am worshiped as a god. But to myself I think of myself only as a servant to my greater masters.\n\nKnow too that I have brought the cataclysm to your world, which must be destroyed. It is a doom you have brought on yourselves by failing to eliminate the devil Kreegans from your realms. ")
    evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
    evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
    evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
    evt.SetNPCTopic(26, 3, 163) -- Escaton topic 3: Save the World
    evt.SetNPCTopic(23, 0, 155) -- Xanthor topic 0: Elemental Lords
    evt.SetNPCTopic(23, 1, 156) -- Xanthor topic 1: The Destroyer
    evt.SetNPCGreeting(23, 112) -- Xanthor greeting: You are back? Have you need of advice? Or are you finding the task at hand too difficult?
    SetQBit(QBit(235)) -- Have talked to Escaton
    SetValue(MapVar(31), 4)
    SetValue(MapVar(32), 4)
    SetValue(MapVar(33), 4)
    return
end)

RegisterGlobalEvent(160, "Masters", function()
    if IsAtLeast(MapVar(31), 4) then
        evt.SimpleMessage("My masters are those who created me. They gave me form and function. I have thus proven indestructible. I destroy worlds infested by Kreegans.")
        SetValue(MapVar(31), 3)
        return
    elseif IsAtLeast(MapVar(31), 3) then
        evt.SimpleMessage("On your world they speak of a Silence which has lasted for a thousand years and more. I am old beyond that and my masters are ancient to me.")
        SetValue(MapVar(31), 2)
        return
    elseif IsAtLeast(MapVar(31), 2) then
        evt.SimpleMessage("There are more worlds than yours--a myriad of them. These worlds were once held in a great web whose threads could be traversed like bridges over rivers. What you call the Silence was marked by the breaking of the web which was built by my masters.")
        SetValue(MapVar(31), 1)
        return
    elseif IsAtLeast(MapVar(31), 1) then
        evt.SimpleMessage("At one time my ancient masters were caretakers of more worlds than there are apples in a bushel. Before the Kreegans--before the Silence--they were worlds of wonder. My masters were kings and queens of a golden civilization. I was made, not because I was needed, but because I could be made--a protector of that which needed no protection...a symbol of might to a mighty people.\n\nBut now, and for a millennium, the Kreegan blight has eaten away the splendor of the worlds. And so have my masters fallen. They are warlords and generals, and I am their greatest soldier.")
        SetValue(MapVar(31), 4)
    else
        evt.SimpleMessage("My masters are those who created me. They gave me form and function. I have thus proven indestructible. I destroy worlds infested by Kreegans.")
        SetValue(MapVar(31), 3)
    end
    return
end)

RegisterGlobalEvent(161, "Cataclysm", function()
    if IsAtLeast(MapVar(32), 4) then
        evt.SimpleMessage("Your world will be destroyed by the elemental forces that created it. The crystal in Jadame's central city compels those who live on the elemental planes to open their worlds onto yours. When their worlds meet at the crystal, the reaction will unleash irrepressible destruction across the lands, sky and sea. All things living will live no longer.")
        SetValue(MapVar(32), 3)
        return
    elseif IsAtLeast(MapVar(32), 3) then
        evt.SimpleMessage("The cataclysm was brought into being when I performed the ritual Convocation of Cataclysm which brought into being the crystal. It is a weapon of last resort created by my masters to defend themselves against the Kreegans.\n\nI do have other weapons. But when I became aware of the Kreegans infestation on your world, I deemed the use of ultimate force necessary. Your world has fallen so far--it seemed certain you would not be able to defend yourselves against my enemies. Though I underestimated your abilities, and the Kreegans were ultimately destroyed, I still feel that I was right to err on the side of caution.")
        SetValue(MapVar(32), 2)
        return
    elseif IsAtLeast(MapVar(32), 2) then
        evt.SimpleMessage("My masters, afraid the Kreegans would learn ways to corrupt me, have made me incorruptible. I am unable to undo the Convocation of Cataclysm once it has been performed. This command of theirs is part of my very being. I am powerless but to obey.")
        SetValue(MapVar(32), 1)
        return
    elseif IsAtLeast(MapVar(32), 1) then
        evt.SimpleMessage("The Convocation of Cataclysm, as powerful as it is, cannot of itself destroy a world. Each of the elemental planes is ruled by a lord. These lords can fight the compulsion placed on their lesser subjects. For this reason, I have removed the lords from their realms. They are my \"guests\" for the time being.\n\nOnce the cataclysm has run its course, I will return them so that they might rebuild your realm and theirs.")
        SetValue(MapVar(32), 4)
    else
        evt.SimpleMessage("Your world will be destroyed by the elemental forces that created it. The crystal in Jadame's central city compels those who live on the elemental planes to open their worlds onto yours. When their worlds meet at the crystal, the reaction will unleash irrepressible destruction across the lands, sky and sea. All things living will live no longer.")
        SetValue(MapVar(32), 3)
    end
    return
end)

RegisterGlobalEvent(162, "Kreegans", function()
    if IsAtLeast(MapVar(33), 4) then
        evt.SimpleMessage("In the time since the Silence, your world has lost knowledge of the Kreegan's origin. That they resemble the devils of myth has been enough for you, and indeed, \"devils\" is what most call them. The truth is they came from the beyond. Before they attacked us, my masters had no knowledge of them.\n\nThe Kreegans infest our worlds and spread if they can. It would seem in an endless universe that they could expand in another direction than ours. But they have not made this choice so we must defend ourselves from them.")
        SetValue(MapVar(33), 3)
        return
    elseif IsAtLeast(MapVar(33), 3) then
        evt.SimpleMessage("I am aware that the king and queen of Enroth have rid your world of Kreegans. Still, your world is to be destroyed. Once I am called, I must perform the Convocation. Once the Convocation is begun, it must continue.\n\nI was called while Kreegan still lived on your world. It matters not that they were dust by the time I arrived.")
        SetValue(MapVar(33), 2)
        return
    elseif IsAtLeast(MapVar(33), 2) then
        evt.SimpleMessage("If it were not for the Kreegans and the state of war they impose, my masters could rebuild the Web of Worlds and lift what you call \"The Silence.\" My masters have attempted to rebuild the Web many times, but the Kreegans always destroy it. Now they have concluded that the Kreegans must be entirely eliminated or the golden civilization will never rise again. It is to fulfill this purpose that I have been created.")
        SetValue(MapVar(33), 1)
        return
    elseif IsAtLeast(MapVar(33), 1) then
        evt.SimpleMessage("As far as I'm able to feel such, I am amazed that your world was able to eliminate its Kreegan infestation. They are quite a bit more…advanced than you. The king and queen of Enroth must be strategists of the highest order. Too bad that they were not able to finish their task sooner.\n\nIf I could regret, I would regret having to needlessly annihilate your world.")
        SetValue(MapVar(33), 4)
    else
        evt.SimpleMessage("In the time since the Silence, your world has lost knowledge of the Kreegan's origin. That they resemble the devils of myth has been enough for you, and indeed, \"devils\" is what most call them. The truth is they came from the beyond. Before they attacked us, my masters had no knowledge of them.\n\nThe Kreegans infest our worlds and spread if they can. It would seem in an endless universe that they could expand in another direction than ours. But they have not made this choice so we must defend ourselves from them.")
        SetValue(MapVar(33), 3)
    end
    return
end)

RegisterGlobalEvent(163, "Save the World", function()
    evt.SimpleMessage("Yes, your world does need saving! The cataclysm, if not stopped, will destroy it utterly.\n\nA quandary for you: I, as bringer of the cataclysm know how it can be ended. Further, I acknowledge that since there are no longer Kreegans on your world it need not be destroyed. But, as servant to my masters, I am compelled to let the cataclysm continue by not divulging my knowledge to you.\n\nStill I will ask you some questions. Perhaps there is something for you in the answers?")
    SetQBit(QBit(98)) -- Escaton, heard the first message in global event 163
    evt.SetNPCTopic(26, 0, 164) -- Escaton topic 0: Riddle One
    evt.SetNPCTopic(26, 1, 165) -- Escaton topic 1: Riddle Two
    evt.SetNPCTopic(26, 2, 166) -- Escaton topic 2: Riddle Three
    evt.SetNPCTopic(26, 3, 0) -- Escaton topic 3 cleared
    return
end)

RegisterGlobalEvent(164, "Riddle One", function(continueStep)
    if continueStep == 2 then
        evt.SimpleMessage("That doesn't seem right at all.")
        evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
        evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
        evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
        evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
        return
    end
    if continueStep == 4 then
        if IsQBitSet(QBit(95)) then -- Escaton, riddle two answered correctly.
            if not IsQBitSet(QBit(96)) then -- Escaton, riddle three answered correctly.
                evt.SimpleMessage("Yes. Your answer seems to fit the riddle nicely. Perhaps that is the correct answer.")
                SetQBit(QBit(94)) -- Escaton, riddle one answered correctly.
                if IsQBitSet(QBit(95)) then -- Escaton, riddle two answered correctly.
                    SetAutonote(11) -- Destroyer's Riddles. Riddle One: "Prison." Riddle Two: "Inside." Riddle Three: ? Prison + Inside + ?
                    ClearAutonote(14) -- Destroyer's Riddles. Riddle One: ? Riddle Two: "Inside." Riddle Three: ? ? + Inside + ?
                    evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
                    evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
                    evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
                    evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
                    return
                elseif IsQBitSet(QBit(96)) then -- Escaton, riddle three answered correctly.
                    SetAutonote(12) -- Destroyer's Riddles. Riddle One: "Prison." Riddle Two: ? Riddle Three: "Egg." Prison + ? + Egg
                    ClearAutonote(16) -- Destroyer's Riddles. Riddle One: ? Riddle Two: ? Riddle Three: "Egg." ? + ? + Egg
                else
                    SetAutonote(10) -- Destroyer's Riddles. Riddle One: "Prison." Riddle Two: ? Riddle Three: ? Prison + ? + ?
                end
            evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
            evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
            evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
            evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
            return
            end
            evt.SimpleMessage("I would judge that you've answered the riddles correctly. I suppose in asking them to you I have in some way helped you. As far as I and my nature are concerned, this is sufficient.\n\nAs a reward for your performance, take this small bauble. I have more than one and therefore, more than I require. And see? I can give it to you because I don't know you have the knowledge to use it.")
            SetQBit(QBit(97)) -- Escaton, all riddles answered correctly.
            SetQBit(QBit(48)) -- Rescue Pyrannaste, Lord of Fire. - Given by Eschaton. Taken by rescue of Pyrannaste.
            SetQBit(QBit(50)) -- Rescue Gralkor the Cruel, Lord of Earth. - Given by Eschaton. Taken by rescue of Gralkor.
            SetQBit(QBit(52)) -- Rescue Acwalander, Lord of Water. - Given by Eschaton. Taken by rescue of Acwalander.
            SetQBit(QBit(54)) -- Rescue Shalwend, Lord of Air. - Given by Eschaton. Taken by rescue of Shalwend.
            ClearQBit(QBit(46)) -- Find the cause of the cataclysm through the Crystal Gateway. - Given by XANTHOR. Taken by Eschaton.
            SetQBit(QBit(47)) -- Quest 46 done. Used to allow entrance to elemental lord prisons. Now player needs item 629.
            AddValue(InventoryItem(629), 629) -- Ring of Keys
            SetQBit(QBit(220)) -- Ring of Keys - I lost it
            AddValue(History(18), 0)
            ClearAutonote(15) -- Destroyer's Riddles. Riddle One: ? Riddle Two: "Inside." Riddle Three: "Egg." ? + Inside + Egg
            SetAutonote(13) -- Destroyer's Riddles. Riddle One: "Prison." Riddle Two: "Inside." Riddle Three: "Egg." Prison + Inside + Egg
            evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
            evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
            evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
            evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
            return
        end
        evt.SimpleMessage("Yes. Your answer seems to fit the riddle nicely. Perhaps that is the correct answer.")
        SetQBit(QBit(94)) -- Escaton, riddle one answered correctly.
        if IsQBitSet(QBit(95)) then -- Escaton, riddle two answered correctly.
            SetAutonote(11) -- Destroyer's Riddles. Riddle One: "Prison." Riddle Two: "Inside." Riddle Three: ? Prison + Inside + ?
            ClearAutonote(14) -- Destroyer's Riddles. Riddle One: ? Riddle Two: "Inside." Riddle Three: ? ? + Inside + ?
            evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
            evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
            evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
            evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
            return
        elseif IsQBitSet(QBit(96)) then -- Escaton, riddle three answered correctly.
            SetAutonote(12) -- Destroyer's Riddles. Riddle One: "Prison." Riddle Two: ? Riddle Three: "Egg." Prison + ? + Egg
            ClearAutonote(16) -- Destroyer's Riddles. Riddle One: ? Riddle Two: ? Riddle Three: "Egg." ? + ? + Egg
        else
            SetAutonote(10) -- Destroyer's Riddles. Riddle One: "Prison." Riddle Two: ? Riddle Three: ? Prison + ? + ?
        end
    evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
    evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
    evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
    evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
    return
    end
    if continueStep ~= nil then return end
    if not IsQBitSet(QBit(94)) then -- Escaton, riddle one answered correctly.
        evt.AskQuestion(164, 2, 595, 4, 100, 101, "Where does one serve to pay,\n  Is not free to leave,\n  But is free when one leaves?", {"prison", "jail"})
        return nil
    end
    evt.SimpleMessage("Jails, prisons and cells come in many forms. We hear of so called \"prisons of the mind.\" But I wonder. The riddle seems to speak of a physical prison. What think you?")
    evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
    evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
    evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
    evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
    return
end)

RegisterGlobalEvent(165, "Riddle Two", function(continueStep)
    if continueStep == 2 then
        evt.SimpleMessage("I suppose that could work…no, on second thought, it seems entirely wrong.")
        evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
        evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
        evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
        evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
        return
    end
    if continueStep == 4 then
        if IsQBitSet(QBit(94)) then -- Escaton, riddle one answered correctly.
            if not IsQBitSet(QBit(96)) then -- Escaton, riddle three answered correctly.
                evt.SimpleMessage("The vagaries of language are many. Still, your answer seems to apply well to the question.")
                SetQBit(QBit(95)) -- Escaton, riddle two answered correctly.
                if IsQBitSet(QBit(94)) then -- Escaton, riddle one answered correctly.
                    SetAutonote(11) -- Destroyer's Riddles. Riddle One: "Prison." Riddle Two: "Inside." Riddle Three: ? Prison + Inside + ?
                    ClearAutonote(10) -- Destroyer's Riddles. Riddle One: "Prison." Riddle Two: ? Riddle Three: ? Prison + ? + ?
                    evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
                    evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
                    evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
                    evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
                    return
                elseif IsQBitSet(QBit(96)) then -- Escaton, riddle three answered correctly.
                    SetAutonote(15) -- Destroyer's Riddles. Riddle One: ? Riddle Two: "Inside." Riddle Three: "Egg." ? + Inside + Egg
                    ClearAutonote(16) -- Destroyer's Riddles. Riddle One: ? Riddle Two: ? Riddle Three: "Egg." ? + ? + Egg
                else
                    SetAutonote(14) -- Destroyer's Riddles. Riddle One: ? Riddle Two: "Inside." Riddle Three: ? ? + Inside + ?
                end
            evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
            evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
            evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
            evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
            return
            end
            evt.SimpleMessage("I would judge that you've answered the riddles correctly. I suppose in asking them to you I have in some way helped you. As far as I and my nature are concerned, this is sufficient.\n\nAs a reward for your performance, take this small bauble. I have more than one and therefore, more than I require. And see? I can give it to you because I don't know you have the knowledge to use it.")
            SetQBit(QBit(97)) -- Escaton, all riddles answered correctly.
            SetQBit(QBit(48)) -- Rescue Pyrannaste, Lord of Fire. - Given by Eschaton. Taken by rescue of Pyrannaste.
            SetQBit(QBit(50)) -- Rescue Gralkor the Cruel, Lord of Earth. - Given by Eschaton. Taken by rescue of Gralkor.
            SetQBit(QBit(52)) -- Rescue Acwalander, Lord of Water. - Given by Eschaton. Taken by rescue of Acwalander.
            SetQBit(QBit(54)) -- Rescue Shalwend, Lord of Air. - Given by Eschaton. Taken by rescue of Shalwend.
            ClearQBit(QBit(46)) -- Find the cause of the cataclysm through the Crystal Gateway. - Given by XANTHOR. Taken by Eschaton.
            SetQBit(QBit(47)) -- Quest 46 done. Used to allow entrance to elemental lord prisons. Now player needs item 629.
            AddValue(InventoryItem(629), 629) -- Ring of Keys
            SetQBit(QBit(220)) -- Ring of Keys - I lost it
            AddValue(History(18), 0)
            ClearAutonote(12) -- Destroyer's Riddles. Riddle One: "Prison." Riddle Two: ? Riddle Three: "Egg." Prison + ? + Egg
            SetAutonote(13) -- Destroyer's Riddles. Riddle One: "Prison." Riddle Two: "Inside." Riddle Three: "Egg." Prison + Inside + Egg
            evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
            evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
            evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
            evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
            return
        end
        evt.SimpleMessage("The vagaries of language are many. Still, your answer seems to apply well to the question.")
        SetQBit(QBit(95)) -- Escaton, riddle two answered correctly.
        if IsQBitSet(QBit(94)) then -- Escaton, riddle one answered correctly.
            SetAutonote(11) -- Destroyer's Riddles. Riddle One: "Prison." Riddle Two: "Inside." Riddle Three: ? Prison + Inside + ?
            ClearAutonote(10) -- Destroyer's Riddles. Riddle One: "Prison." Riddle Two: ? Riddle Three: ? Prison + ? + ?
            evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
            evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
            evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
            evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
            return
        elseif IsQBitSet(QBit(96)) then -- Escaton, riddle three answered correctly.
            SetAutonote(15) -- Destroyer's Riddles. Riddle One: ? Riddle Two: "Inside." Riddle Three: "Egg." ? + Inside + Egg
            ClearAutonote(16) -- Destroyer's Riddles. Riddle One: ? Riddle Two: ? Riddle Three: "Egg." ? + ? + Egg
        else
            SetAutonote(14) -- Destroyer's Riddles. Riddle One: ? Riddle Two: "Inside." Riddle Three: ? ? + Inside + ?
        end
    evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
    evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
    evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
    evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
    return
    end
    if continueStep ~= nil then return end
    if not IsQBitSet(QBit(95)) then -- Escaton, riddle two answered correctly.
        evt.AskQuestion(165, 2, 599, 4, 102, 103, "What is there when\n  You enter a room,\n  And cannot be outside,\n  Though you leave the door open?", {"in", "inside"})
        return nil
    end
    evt.SimpleMessage("Inside. Inside what? And what is inside? And while we're asking...why?")
    evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
    evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
    evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
    evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
    return
end)

RegisterGlobalEvent(166, "Riddle Three", function(continueStep)
    if continueStep == 2 then
        evt.SimpleMessage("I don't see how that could be the answer. Really I can't.")
        evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
        evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
        evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
        evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
        return
    end
    if continueStep == 4 then
        if IsQBitSet(QBit(94)) then -- Escaton, riddle one answered correctly.
            if not IsQBitSet(QBit(95)) then -- Escaton, riddle two answered correctly.
                evt.SimpleMessage("What else indeed could the answer be? I'm sure if one were to apply some thought, one could think of something. Still in these matters, it is best to have confidence in one's clearest thought. I suppose your answer could be correct.")
                SetQBit(QBit(96)) -- Escaton, riddle three answered correctly.
                if IsQBitSet(QBit(94)) then -- Escaton, riddle one answered correctly.
                    SetAutonote(12) -- Destroyer's Riddles. Riddle One: "Prison." Riddle Two: ? Riddle Three: "Egg." Prison + ? + Egg
                    ClearAutonote(10) -- Destroyer's Riddles. Riddle One: "Prison." Riddle Two: ? Riddle Three: ? Prison + ? + ?
                    evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
                    evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
                    evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
                    evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
                    return
                elseif IsQBitSet(QBit(95)) then -- Escaton, riddle two answered correctly.
                    SetAutonote(15) -- Destroyer's Riddles. Riddle One: ? Riddle Two: "Inside." Riddle Three: "Egg." ? + Inside + Egg
                    ClearAutonote(14) -- Destroyer's Riddles. Riddle One: ? Riddle Two: "Inside." Riddle Three: ? ? + Inside + ?
                else
                    SetAutonote(16) -- Destroyer's Riddles. Riddle One: ? Riddle Two: ? Riddle Three: "Egg." ? + ? + Egg
                end
            evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
            evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
            evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
            evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
            return
            end
            evt.SimpleMessage("I would judge that you've answered the riddles correctly. I suppose in asking them to you I have in some way helped you. As far as I and my nature are concerned, this is sufficient.\n\nAs a reward for your performance, take this small bauble. I have more than one and therefore, more than I require. And see? I can give it to you because I don't know you have the knowledge to use it.")
            SetQBit(QBit(97)) -- Escaton, all riddles answered correctly.
            SetQBit(QBit(48)) -- Rescue Pyrannaste, Lord of Fire. - Given by Eschaton. Taken by rescue of Pyrannaste.
            SetQBit(QBit(50)) -- Rescue Gralkor the Cruel, Lord of Earth. - Given by Eschaton. Taken by rescue of Gralkor.
            SetQBit(QBit(52)) -- Rescue Acwalander, Lord of Water. - Given by Eschaton. Taken by rescue of Acwalander.
            SetQBit(QBit(54)) -- Rescue Shalwend, Lord of Air. - Given by Eschaton. Taken by rescue of Shalwend.
            ClearQBit(QBit(46)) -- Find the cause of the cataclysm through the Crystal Gateway. - Given by XANTHOR. Taken by Eschaton.
            SetQBit(QBit(47)) -- Quest 46 done. Used to allow entrance to elemental lord prisons. Now player needs item 629.
            AddValue(InventoryItem(629), 629) -- Ring of Keys
            SetQBit(QBit(220)) -- Ring of Keys - I lost it
            AddValue(History(18), 0)
            ClearAutonote(11) -- Destroyer's Riddles. Riddle One: "Prison." Riddle Two: "Inside." Riddle Three: ? Prison + Inside + ?
            SetAutonote(13) -- Destroyer's Riddles. Riddle One: "Prison." Riddle Two: "Inside." Riddle Three: "Egg." Prison + Inside + Egg
            evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
            evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
            evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
            evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
            return
        end
        evt.SimpleMessage("What else indeed could the answer be? I'm sure if one were to apply some thought, one could think of something. Still in these matters, it is best to have confidence in one's clearest thought. I suppose your answer could be correct.")
        SetQBit(QBit(96)) -- Escaton, riddle three answered correctly.
        if IsQBitSet(QBit(94)) then -- Escaton, riddle one answered correctly.
            SetAutonote(12) -- Destroyer's Riddles. Riddle One: "Prison." Riddle Two: ? Riddle Three: "Egg." Prison + ? + Egg
            ClearAutonote(10) -- Destroyer's Riddles. Riddle One: "Prison." Riddle Two: ? Riddle Three: ? Prison + ? + ?
            evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
            evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
            evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
            evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
            return
        elseif IsQBitSet(QBit(95)) then -- Escaton, riddle two answered correctly.
            SetAutonote(15) -- Destroyer's Riddles. Riddle One: ? Riddle Two: "Inside." Riddle Three: "Egg." ? + Inside + Egg
            ClearAutonote(14) -- Destroyer's Riddles. Riddle One: ? Riddle Two: "Inside." Riddle Three: ? ? + Inside + ?
        else
            SetAutonote(16) -- Destroyer's Riddles. Riddle One: ? Riddle Two: ? Riddle Three: "Egg." ? + ? + Egg
        end
    evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
    evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
    evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
    evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
    return
    end
    if continueStep ~= nil then return end
    if not IsQBitSet(QBit(96)) then -- Escaton, riddle three answered correctly.
        evt.AskQuestion(166, 2, 603, 4, 104, 105, "A moon colored box\n  meant to be opened from the inside\n  protects the sun colored\n  treasure of life.\n  What is it?", {"egg", "an egg"})
        return nil
    end
    evt.SimpleMessage("\"Egg,\" yes. or perhaps, \"eggs.\" Eggs are a source of life, a seed of sorts. They are also of an unusual shape not found in many places elsewhere. Perhaps placing the answer in context will give a clue or some direction.")
    evt.SetNPCTopic(26, 0, 160) -- Escaton topic 0: Masters
    evt.SetNPCTopic(26, 1, 161) -- Escaton topic 1: Cataclysm
    evt.SetNPCTopic(26, 2, 162) -- Escaton topic 2: Kreegans
    evt.SetNPCTopic(26, 3, 171) -- Escaton topic 3: Riddles
    return
end)

RegisterGlobalEvent(167, "Release Shalwend", function()
    if IsQBitSet(QBit(51)) and IsQBitSet(QBit(53)) and IsQBitSet(QBit(49)) then -- Quest 50 done.
        evt.SimpleMessage("Thank you for releasing me. Know that Shalwend, Lord of Air, holds you in his favor. \n\nI go now to restore order to my realm and to join with my fellow lords to do what I can for yours. Be warned! Our actions will destabilize the crystal gateway. Leave now for your home, lest you be trapped here forever.  Inform Xanthor of what has happened here. Farewell")
        SetQBit(QBit(56)) -- All Lords from quests 48, 50, 52, 54 rescued.
        AddValue(History(19), 0)
    else
        evt.SimpleMessage("Thank you for releasing me. I go now to restore order to my realm and to do what I can for yours. Know that Shalwend, Lord of Air, holds you in his favor. Farewell.")
    end
    evt.SetNPCTopic(30, 0, 0) -- Shalwend topic 0 cleared
    evt.MoveNPC(30, 0) -- Shalwend -> removed
    evt.ForPlayer(Players.All)
    AddValue(Experience, 100000)
    evt.ForPlayer(Players.Member0)
    AddValue(Gold, 10000)
    evt.ForPlayer(Players.All)
    ClearQBit(QBit(54)) -- Rescue Shalwend, Lord of Air. - Given by Eschaton. Taken by rescue of Shalwend.
    SetQBit(QBit(55)) -- Quest 54 done.
    SetAward(Award(14)) -- Rescued Shalwend, Lord of Air.
    return
end)

RegisterGlobalEvent(168, "Release Acwalander", function()
    if IsQBitSet(QBit(51)) and IsQBitSet(QBit(55)) and IsQBitSet(QBit(49)) then -- Quest 50 done.
        evt.SimpleMessage("\"The Destroyer\" is a fitting moniker for one who would imprison me in such a fashion. If it were not for you, I, Acwalander, Lord of Water, would have soon perished. My passing would have had an unbalancing effect across all the planes. Thank you. I go now to gather with the other lords. Together we will set things right.\n\n Be warned! Our actions will destabilize the crystal gateway. Leave now for your home, lest you be trapped here forever. Inform Xanthor of what has happened here. Farewell.")
        SetQBit(QBit(56)) -- All Lords from quests 48, 50, 52, 54 rescued.
        AddValue(History(19), 0)
    else
        evt.SimpleMessage("\"The Destroyer\" is a fitting moniker for one who would imprison me in such a fashion. If it were not for you, I, Acwalander, Lord of Water, would have soon perished. My passing would have had an unbalancing effect across all the planes. Thank you. I go now to set things right.")
    end
    evt.SetNPCTopic(28, 0, 0) -- Acwalander topic 0 cleared
    evt.MoveNPC(28, 0) -- Acwalander -> removed
    evt.ForPlayer(Players.All)
    AddValue(Experience, 100000)
    evt.ForPlayer(Players.Member0)
    AddValue(Gold, 10000)
    evt.ForPlayer(Players.All)
    ClearQBit(QBit(52)) -- Rescue Acwalander, Lord of Water. - Given by Eschaton. Taken by rescue of Acwalander.
    SetQBit(QBit(53)) -- Quest 52 done.
    SetAward(Award(15)) -- Rescued Acwalander, Lord of Water.
    return
end)

RegisterGlobalEvent(169, "Release Gralkor", function()
    if IsQBitSet(QBit(55)) and IsQBitSet(QBit(53)) and IsQBitSet(QBit(49)) then -- Quest 54 done.
        evt.SimpleMessage("I am free! Now will he who was fool enough to jail me--this Destroyer--feel my wrath. That I, the Lord of Earth, am called \"Gralkor the Cruel\" is no mistake. The suffering I have felt will be his returned in multitudes!\n\nI go now to gather with the other lords. Together we will set things right. Be warned! Our actions will destabilize the crystal gateway. Leave now for your home, lest you be trapped here forever. Inform Xanthor of what has happened here. Farewell")
        SetQBit(QBit(56)) -- All Lords from quests 48, 50, 52, 54 rescued.
        AddValue(History(19), 0)
    else
        evt.SimpleMessage("I am free! Now will he who was fool enough to jail me--this Destroyer--feel my wrath. That I, the Lord of Earth, am called \"Gralkor the Cruel\" is no mistake. The suffering I have felt will be his returned in multitudes!")
    end
    evt.SetNPCTopic(29, 0, 0) -- Gralkor the Cruel topic 0 cleared
    evt.MoveNPC(29, 0) -- Gralkor the Cruel -> removed
    evt.ForPlayer(Players.All)
    AddValue(Experience, 100000)
    evt.ForPlayer(Players.Member0)
    AddValue(Gold, 10000)
    evt.ForPlayer(Players.All)
    ClearQBit(QBit(50)) -- Rescue Gralkor the Cruel, Lord of Earth. - Given by Eschaton. Taken by rescue of Gralkor.
    SetQBit(QBit(51)) -- Quest 50 done.
    SetAward(Award(16)) -- Rescued Gralkor the Cruel, Lord of Earth.
    return
end)

RegisterGlobalEvent(170, "Release Pyrannaste", function()
    if IsQBitSet(QBit(51)) and IsQBitSet(QBit(53)) and IsQBitSet(QBit(55)) then -- Quest 50 done.
        evt.SimpleMessage("Free at last. My torment is over, but what of my subjects? I know the Destroyer has them compelled to a terrible task. My presence will sooth them. I must go to restore order to my realm and yours.\n\nBefore I return to the Plane of Fire, I will gather with the other lords. Together we will set things right. Be warned! Our actions will destabilize the crystal gateway. Leave now for your home, lest you be trapped here forever.  Inform Xanthor of what has happened here. Farewell")
        SetQBit(QBit(56)) -- All Lords from quests 48, 50, 52, 54 rescued.
        AddValue(History(19), 0)
    else
        evt.SimpleMessage("Free at last. My torment is over, but what of my subjects? I know the Destroyer has them compelled to a terrible task. My presence will sooth them. I must go. I must…farewell…")
    end
    evt.SetNPCTopic(27, 0, 0) -- Pyrannaste topic 0 cleared
    evt.MoveNPC(27, 0) -- Pyrannaste -> removed
    evt.ForPlayer(Players.All)
    AddValue(Experience, 100000)
    evt.ForPlayer(Players.Member0)
    AddValue(Gold, 10000)
    evt.ForPlayer(Players.All)
    ClearQBit(QBit(48)) -- Rescue Pyrannaste, Lord of Fire. - Given by Eschaton. Taken by rescue of Pyrannaste.
    SetQBit(QBit(49)) -- Quest 48 done.
    SetAward(Award(17)) -- Rescued Pyrannaste, Lord of Fire.
    return
end)

RegisterGlobalEvent(171, "Riddles", function()
    if not IsQBitSet(QBit(97)) then -- Escaton, all riddles answered correctly.
        evt.SimpleMessage("Though I must destroy your world, what I need do I have already done. Until the cataclysm has culminated, there is nothing to stop me from indulging you with my conversation. This cannot continue forever. Nothing does.\n\nSometimes questions create more questions. Sometimes they provide answers. I wonder what my questions will provide you?")
        evt.SetNPCTopic(26, 0, 164) -- Escaton topic 0: Riddle One
        evt.SetNPCTopic(26, 1, 165) -- Escaton topic 1: Riddle Two
        evt.SetNPCTopic(26, 2, 166) -- Escaton topic 2: Riddle Three
        evt.SetNPCTopic(26, 3, 0) -- Escaton topic 3 cleared
        return
    end
    evt.SimpleMessage("My masters have made me a holder, and not a giver, of knowledge. Still perhaps you have given yourself knowledge through my questions? I have given you all the questions I will, so you must look at what you have. Perhaps you should question the answers.\n\nA \"prison\" implies a prisoner. Who? \"Inside?\" Inside of what? And \"egg.\" What kind of egg? A bird's egg? Perhaps something like an egg?")
    return
end)

RegisterGlobalEvent(172, "Raiders", function()
    evt.SimpleMessage("There are many predators who would take advantage of the lair in this vulnerable time. I've already driven off looters…and worse. One of Zog's patrols stopped by soon after the flood. I fought them off, but some escaped. I am sure they will be back in greater numbers.")
    evt.SetNPCTopic(70, 2, 173) -- Thanys topic 2: Join
    return
end)

RegisterGlobalEvent(173, "Join", function()
    evt.SimpleMessage("No! Someone must remain here to guard the lair against the barbarian raiders. Come back after you've helped my herd. I may consider joining you then.")
    return
end)

RegisterGlobalEvent(174, "Quest", function()
    evt.SimpleMessage("Yellow Fever is a very crippling disease that pops up every few years.  Usually we arrange for medicine from the mainland, but now that the bridges are destroyed, no one can make it to the docks!")
    evt.SetNPCTopic(78, 0, 175) -- Aislen topic 0: Quest
    return
end)

RegisterGlobalEvent(175, "Quest", function()
    evt.SimpleMessage("Here, take these scrolls of Cure Disease.  Maybe we can at least prevent an epidemic!  The six huts on the outer islands are infected.  If the teleporters between the islands are repaired, you can take these scrolls to the huts.  Unfortunately you will have to find three more scrolls in your travels.")
    SetQBit(QBit(101)) -- Deliver Cure Disease Scrolls to the six huts on the outer Dagger Wound Islands. Return to Aislen on Dagger Wound Island.
    evt.SetNPCTopic(78, 0, 176) -- Aislen topic 0: Have you stopped the epidemic?
    AddValue(InventoryItem(373), 373) -- Cure Disease
    AddValue(InventoryItem(373), 373) -- Cure Disease
    AddValue(InventoryItem(373), 373) -- Cure Disease
    return
end)
RegisterCanShowTopic(175, function()
    evt._BeginCanShowTopic(175)
    local visible = true
    if IsQBitSet(QBit(108)) then -- Yellow Fever epidemic cured!
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(176, "Have you stopped the epidemic?", function()
    evt.SimpleMessage("The Yellow Fever epidemic is over!  Thank you for your help!")
    ClearQBit(QBit(101)) -- Deliver Cure Disease Scrolls to the six huts on the outer Dagger Wound Islands. Return to Aislen on Dagger Wound Island.
    AddValue(Gold, 1500)
    evt.ForPlayer(Players.All)
    SetAward(Award(18)) -- Stopped the Yellow Fever Epidemic on Dagger Wound Island
    evt.SetNPCTopic(78, 0, 661) -- Aislen topic 0: Pirate Raids
    return
end)
RegisterCanShowTopic(176, function()
    evt._BeginCanShowTopic(176)
    local visible = true
    if IsQBitSet(QBit(108)) then -- Yellow Fever epidemic cured!
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(177, "Quest", function()
    evt.SimpleMessage("I hear that Yellow Fever is once again spreading through the people.  Usually the water supply here on the main island is the primary source of the disease.  We used to get an Anointed Herb Potion from the mainland when the disease popped up.  Without access to the dock however, we cannot get this needed cure.  If you find a way to the mainland, perhaps the smugglers of Ravenshore have the cure.  If you can procure the Anointed Potion, return to me with it!")
    SetQBit(QBit(109)) -- Find and return an Anointed Potion to Languid in the Dagger Wound Islands.
    evt.SetNPCTopic(79, 0, 178) -- Languid topic 0: Do you have the antidote?
    return
end)
RegisterCanShowTopic(177, function()
    evt._BeginCanShowTopic(177)
    local visible = true
    if IsQBitSet(QBit(110)) then -- Poison removed from water supply!
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(178, "Do you have the antidote?", function()
    evt.ForPlayer(Players.All)
    if not HasItem(616) then -- Anointed Herb Potion
        evt.SimpleMessage("Without the Anointed Herb Potion we cannot remove the poison from our water supply!")
        return
    end
    evt.SimpleMessage("Thank you!  I will go introduce this to the water supply!")
    RemoveItem(616) -- Anointed Herb Potion
    evt.ForPlayer(Players.All)
    AddValue(Experience, 7500)
    evt.ForPlayer(Players.Member0)
    AddValue(Gold, 2000)
    evt.ForPlayer(Players.All)
    ClearQBit(QBit(109)) -- Find and return an Anointed Potion to Languid in the Dagger Wound Islands.
    ClearQBit(QBit(245)) -- Annointed Herb Potion - I lost it!
    SetQBit(QBit(110)) -- Poison removed from water supply!
    SetAward(Award(59)) -- Brought the Annointed Herb Potion to Languid on the Dagger Wound Islands.
    evt.SetNPCTopic(79, 0, 0) -- Languid topic 0 cleared
    return
end)

RegisterGlobalEvent(179, "Potion of Pure Speed", function()
    evt.SimpleMessage("Perhaps you can bring me the basic ingredients for a Potion of Pure speed?  With them I can make this incredible potion and finish my studies in alchemy!  I will reward you well for your assistance!")
    SetQBit(QBit(113)) -- Bring Thistle on the Dagger Wound Islands the basic ingredients for a potion of Pure Speed.
    evt.SetNPCTopic(88, 0, 0) -- Thistle topic 0 cleared
    return
end)
RegisterCanShowTopic(179, function()
    evt._BeginCanShowTopic(179)
    local visible = true
    if IsQBitSet(QBit(113)) then -- Bring Thistle on the Dagger Wound Islands the basic ingredients for a potion of Pure Speed.
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(180, "Ingredients", function()
    evt.SimpleMessage("Black Potions are made of a complex blending of many of the three basic alchemical reagents. Red reagents include Widowsweep Berries, Wolf's Eye, and Phials of Gog Blood.  Some blue reagents are Phoenix Feather, Phima Root, Meteor Fragment and Will O' Wisps Heart.  And some yellow reagents are Datura, Dragon Turtle Fang, Poppy Pods and Thornbark.")
    return
end)

RegisterGlobalEvent(181, "Do you have the Ingredients?", function()
    if not evt.CheckItemsCount(DecorVar(2), 4) then
        evt.SimpleMessage("You are missing all or some of the needed ingredients.  Return when you have them all.")
        return
    end
    if not evt.CheckItemsCount(DecorVar(7), 2) then
        evt.SimpleMessage("You are missing all or some of the needed ingredients.  Return when you have them all.")
        return
    end
    if not evt.CheckItemsCount(DecorVar(12), 1) then
        evt.SimpleMessage("You are missing all or some of the needed ingredients.  Return when you have them all.")
        return
    end
    evt.SimpleMessage("The ingredients!  Thank you!  Take this as a reward!")
    evt.RemoveItems(DecorVar(2))
    evt.RemoveItems(DecorVar(7))
    evt.RemoveItems(DecorVar(12))
    ClearQBit(QBit(113)) -- Bring Thistle on the Dagger Wound Islands the basic ingredients for a potion of Pure Speed.
    SetQBit(QBit(114)) -- returned ingredients for a potion of Pure Speed
    AddValue(InventoryItem(265), 265) -- Pure Speed
    evt.ForPlayer(Players.All)
    AddValue(Experience, 1000)
    evt.SetNPCTopic(88, 2, 0) -- Thistle topic 2 cleared
    return
end)
RegisterCanShowTopic(181, function()
    evt._BeginCanShowTopic(181)
    local visible = true
    if IsQBitSet(QBit(113)) then -- Bring Thistle on the Dagger Wound Islands the basic ingredients for a potion of Pure Speed.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(182, "Quest", function()
    evt.SimpleMessage("I believe I may know how to stop the destructive force of the mountain of fire!  I have found an ancient spell that should give me the power to send the mountain of fire back into the sea! To complete the spell I need an ancient relic called the Idol of the Snake.  With this item of power I should be able to complete the spell.")
    SetQBit(QBit(111)) -- Bring Hiss on the Dagger Wound Islands the Idol of the Snake from the Abandoned Temple.
    evt.SetNPCTopic(89, 0, 183) -- Hiss topic 0: Do you have the Idol?
    return
end)
RegisterCanShowTopic(182, function()
    evt._BeginCanShowTopic(182)
    local visible = true
    if IsQBitSet(QBit(112)) then -- Found Idol of the Snake
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(183, "Do you have the Idol?", function()
    evt.ForPlayer(Players.All)
    if not HasItem(630) then -- Idol of the Snake
        evt.SimpleMessage("Where is the Idol?  Do not waste my time unless you have it!")
        return
    end
    evt.SimpleMessage("Thank you for returning with the Idol.  Upon further study I discovered that the entire spell was useless.  Still, this is not your fault and you deserve some reward for returning to me!")
    evt.ForPlayer(Players.All)
    RemoveItem(630) -- Idol of the Snake
    AddValue(Experience, 7500)
    evt.ForPlayer(Players.Member0)
    AddValue(Gold, 2000)
    evt.ForPlayer(Players.All)
    ClearQBit(QBit(111)) -- Bring Hiss on the Dagger Wound Islands the Idol of the Snake from the Abandoned Temple.
    SetQBit(QBit(112)) -- Found Idol of the Snake
    SetAward(Award(51)) -- Recovered Idol of the Snake for Hiss of Blood Drop village.
    evt.SetNPCTopic(89, 0, 0) -- Hiss topic 0 cleared
    return
end)

RegisterGlobalEvent(184, "Quest", function()
    evt.SimpleMessage("The packs of Dire Wolves that roam this region are a threat to travelers and commerce.  The Merchants of Alvar have instructed me to hire competent people to hunt down these wolves and to \"thin the pack\" in their words.  You look like skilled adventurers!  I will reward you well if you can eliminate the entire pack and those in their lair.")
    SetQBit(QBit(139)) -- Kill all Dire Wolves in Ravenshore. Return to Maddigan in Ravenshore.
    evt.SetNPCTopic(91, 0, 186) -- Maddigan the Tracker topic 0: Finally!
    return
end)

RegisterGlobalEvent(185, "Dire Wolf Pelts", function()
    evt.SimpleMessage("I pay 250 gold for every intact Dire Wolf Pelt that you return to me.")
    evt.ForPlayer(Players.All)
    if HasItem(633) then -- Dire Wolf Pelt
        evt.ForPlayer(Players.Member0)
        AddValue(Gold, 250)
        evt.ForPlayer(Players.All)
        RemoveItem(633) -- Dire Wolf Pelt
        return
    end
    evt.SimpleMessage("You have no more pelts, return when you have more!")
    return
end)

RegisterGlobalEvent(186, "Finally!", function()
    evt.SimpleMessage("You have killed all of the dire wolves in the region!  Travelers are once again safe. However, I now find myself in need of a new business!")
    AddValue(Gold, 2500)
    evt.ForPlayer(Players.All)
    AddValue(Experience, 7500)
    ClearQBit(QBit(139)) -- Kill all Dire Wolves in Ravenshore. Return to Maddigan in Ravenshore.
    SetAward(Award(60)) -- Killed all of the Dire Wolves in the Ravenshore area.
    evt.SetNPCTopic(91, 0, 0) -- Maddigan the Tracker topic 0 cleared
    return
end)
RegisterCanShowTopic(186, function()
    evt._BeginCanShowTopic(186)
    local visible = true
    if IsQBitSet(QBit(140)) then -- Killed all Dire Wolves in Ravenshore
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(187, "Quest", function()
    if not IsQBitSet(QBit(120)) then -- Rescued Smuggler Leader's Familly
        evt.SimpleMessage("The Merchants of Alvar took my family into what they termed \"protective custody\" and use this as the means to secure my services. However as the caravan with my family was returning to Alvar, they were attacked by Ogres and bandits.  The Ogre Zog, took my family from them!  He took them to his fortress in the Alvar region.  Now, I am to spy on the Merchants of Alvar for him.  As long as I do so, my family lives.  If I stop, they die.  Can you rescue them for me?")
        SetQBit(QBit(119)) -- Rescue Arion Hunter's daughter from Ogre Fortress in Alvar.
        return
    end
    evt.SimpleMessage("My family returned and told me of how you rescued them.  Tell the Merchants of Alvar, that they no longer need rely upon our \"bargain.\"  I will keep my word to them and to you, my boats will always be at your service!")
    ClearQBit(QBit(120)) -- Rescued Smuggler Leader's Familly
    evt.ForPlayer(Players.All)
    AddValue(Experience, 15000)
    SetAward(Award(56)) -- Rescued Irabelle Hunter from the Ogre Fortress in Alvar.
    evt.ForPlayer(Players.Member0)
    AddValue(Gold, 10000)
    evt.SetNPCTopic(4, 2, 0) -- Arion Hunter topic 2 cleared
    return
end)

RegisterGlobalEvent(188, "Quest", function()
    evt.SimpleMessage("I send periodic reports of the activities of the Merchants of Alvar to the Dread Pirate Stanley in the tavern, The Pirate's Rest on the Island of Regna. Now that the Merchants have \"bargained\" for my assistance, we must deliver a false set of reports to keep Stanley from being suspicious.  Take this report to him in Harecksburg on the island of Regna!")
    SetQBit(QBit(117)) -- Deliver fake report to the Dread Pirate Stanley in the Pirate's Rest Tavern on the Island of Regna.
    SetQBit(QBit(282)) -- False Report - I lost it!
    AddValue(InventoryItem(602), 602) -- False Report
    evt.SetNPCTopic(4, 1, 189) -- Arion Hunter topic 1: Report has been delivered?
    return
end)
RegisterCanShowTopic(188, function()
    evt._BeginCanShowTopic(188)
    local visible = true
    if IsQBitSet(QBit(118)) then -- Delivered false report to Stanley
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(189, "Report has been delivered?", function()
    evt.SimpleMessage("You delivered the report to Stanley?  This is will at least buy us sometime before he becomes suspicious of the activities here in Ravenshore and those of the Merchants in Alvar.")
    evt.ForPlayer(Players.All)
    AddValue(Experience, 10000)
    evt.SetNPCTopic(4, 1, 299) -- Arion Hunter topic 1: Fate of Jadame
    return
end)
RegisterCanShowTopic(189, function()
    evt._BeginCanShowTopic(189)
    local visible = true
    if IsQBitSet(QBit(118)) then -- Delivered false report to Stanley
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(190, "Anointed Herb Potion", function()
    evt.SimpleMessage("I hear that you are looking for an Anointed Herb potion to purify the water supply.  The Smugglers of Jadame deal with all kind of strange goods.  If anyone would know about or have this anointed herb potion, it would be them!")
    return
end)
RegisterCanShowTopic(190, function()
    evt._BeginCanShowTopic(190)
    local visible = true
    if IsQBitSet(QBit(109)) then -- Find and return an Anointed Potion to Languid in the Dagger Wound Islands.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(191, "Naga Hides", function()
    evt.SimpleMessage("The Dark Elves of Alvar pay well for leather made from Naga Hides. Once treated and tanned, the Naga Hides can last almost longer than a Dark Elf's lifetime! ")
    return
end)

RegisterGlobalEvent(192, "500 Gold!", function()
    evt.SimpleMessage("I will pay you 500 gold for each Naga Hide you bring.")
    evt.ForPlayer(Players.All)
    if HasItem(632) then -- Naga Hide
        RemoveItem(632) -- Naga Hide
        evt.ForPlayer(Players.Member0)
        AddValue(Gold, 500)
        return
    end
    evt.SimpleMessage("You do not have any Naga Hides!  You waste my time!")
    return
end)

RegisterGlobalEvent(193, "Quest", function()
    evt.SimpleMessage("Many decades ago, the legendary Priest of the Sun, Camien Thryce, led a crusade against the Necromancers' Guild in Shadowspire.  The Guild was able to defeat Thryce's forces with the aid of the Vampires that also dwell in the Shadowspire region.  Camien Thryce carried with him the clerical artifact called Eclipse with him into battle.  The shield was lost when Thryce was struck down by a Nosferatu in the final battle.")
    SetQBit(QBit(127)) -- Recover the shield, Eclipse, for Lathius in Ravenshore.
    evt.SetNPCTopic(98, 0, 194) -- Lathius topic 0: Eclipse
    return
end)
RegisterCanShowTopic(193, function()
    evt._BeginCanShowTopic(193)
    local visible = true
    if IsQBitSet(QBit(128)) then -- Recovered the the Shield, Eclipse for Lathius
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(194, "Eclipse", function()
    evt.ForPlayer(Players.All)
    if not HasItem(516) then -- Eclipse
        evt.SimpleMessage("Where is Eclipse?  Return to me when you have found the shield!")
        return
    end
    evt.SimpleMessage("You have recovered the shield, Eclipse?  The Temple is grateful for you help in recovering this potent artifact.  Please, continue to carry the shield with our blessing.")
    evt.ForPlayer(Players.All)
    AddValue(Experience, 25000)
    evt.ForPlayer(Players.Member0)
    AddValue(Gold, 2000)
    evt.ForPlayer(Players.All)
    ClearQBit(QBit(127)) -- Recover the shield, Eclipse, for Lathius in Ravenshore.
    ClearQBit(QBit(283)) -- Eclipse - I lost it!
    SetQBit(QBit(128)) -- Recovered the the Shield, Eclipse for Lathius
    SetAward(Award(55)) -- Found the shield Eclipse.
    evt.SetNPCTopic(98, 0, 703) -- Lathius topic 0: Use Eclipse well!
    return
end)

RegisterGlobalEvent(195, "Delicacy", function()
    evt.SimpleMessage("Royal Wasp Jelly is a delicacy!  The upper caste of Merchants enjoys this tasty treat with almost every meal!")
    return
end)

RegisterGlobalEvent(196, "1000 Gold!", function()
    evt.SimpleMessage("I pay 1000 gold for Royal Wasp Jelly!")
    return
end)

RegisterGlobalEvent(197, "Royal Wasp Jelly", function()
    -- Missing legacy show message text 768
    evt.ForPlayer(Players.All)
    if HasItem(635) then -- Royal Wasp Jelly
        evt.ForPlayer(Players.Member0)
        AddValue(Gold, 1000)
        evt.ForPlayer(Players.All)
        RemoveItem(635) -- Royal Wasp Jelly
        return
    end
    evt.SimpleMessage("Return when you have Wasp Jelly and then I will pay you!")
    return
end)

RegisterGlobalEvent(198, "Quest", function()
    if IsQBitSet(QBit(130)) then -- Killed all Ogres in Alvar canyon area and in Ogre Fortress
        evt.SimpleMessage("Excellent!  Now that the Ogres are cleared from the roads and no longer inhabit the fortress, the roads to Ravenshore, Ironsand and Murmurwoods are safe again!  Please take this 5000 gold as reward!")
        evt.ForPlayer(Players.Member0)
        AddValue(Gold, 5000)
        evt.ForPlayer(Players.All)
        AddValue(Experience, 10000)
        SetAward(Award(53)) -- Killed all of the Ogres in the Alvar region.
        ClearQBit(QBit(129)) -- Kill all Ogres in the Alvar canyon area and in Ogre Fortress and return to Keldon in Alvar.
        evt.SetNPCTopic(123, 0, 200) -- Keldon topic 0: It's safe to travel again!
        return
    elseif IsQBitSet(QBit(129)) then -- Kill all Ogres in the Alvar canyon area and in Ogre Fortress and return to Keldon in Alvar.
        evt.SimpleMessage("You have not defeated all of the Ogres!  The roads will not be safe until they are destroyed!")
    else
        evt.SimpleMessage("The forces of the Ogre Mage, Zog moved into this area right around the time that the bright flash traveled across the night sky.  They harass and even kill travelers who seek to reach the city of Alvar. It would be of great service to Alvar if you were to eliminate all of the Ogres that harass the roads to Alvar and the Ogres in the fortress near the city of Alvar.  Return to me when you have killed all of the ogres in this region, and I will reward you.")
        SetQBit(QBit(129)) -- Kill all Ogres in the Alvar canyon area and in Ogre Fortress and return to Keldon in Alvar.
    end
    return
end)

RegisterGlobalEvent(199, "Bounty for Ogre Ears", function()
    evt.SimpleMessage("I pay 500 gold for Ogre Ears.  The Merchant Guild of Alvar supports me in paying this bounty to anyone who can kill and ogre.")
    evt.ForPlayer(Players.All)
    if HasItem(653) then -- Ogre Ear
        evt.ForPlayer(Players.Member0)
        AddValue(Gold, 500)
        evt.ForPlayer(Players.All)
        RemoveItem(653) -- Ogre Ear
        return
    end
    evt.SimpleMessage("Return to me with Ogre ears if you wish to be paid!")
    return
end)

RegisterGlobalEvent(200, "It's safe to travel again!", function()
    evt.SimpleMessage("Excellent!  Now that the Ogres are cleared from the roads and no longer inhabit the fortress, the roads to Ravenshore, Ironsand and Murmurwoods are safe again!  ")
    return
end)

RegisterGlobalEvent(201, "Potion of Pure Luck", function()
    evt.SimpleMessage("A Potion of Pure Luck would be of great assistance to any merchant.  One could stumble upon any number of great deals if his Luck was at its highest!  Bring me the basic ingredients for a Potion of Pure Luck and I will reward you well!")
    SetQBit(QBit(115)) -- Bring Rihansi in Alvar the basic ingredients for a potion of Pure Luck.
    evt.SetNPCTopic(99, 0, 0) -- Rihansi topic 0 cleared
    return
end)
RegisterCanShowTopic(201, function()
    evt._BeginCanShowTopic(201)
    local visible = true
    if IsQBitSet(QBit(115)) then -- Bring Rihansi in Alvar the basic ingredients for a potion of Pure Luck.
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(202, "Ingredients", function()
    evt.SimpleMessage("Black Potions are made of a complex blending of many of the three basic alchemical reagents. Red reagents include Widowsweep Berries, Wolf's Eye, and Phials of Gog Blood.  Some blue reagents are Phoenix Feather, Phima Root, Meteor Fragment and Will O' Wisps Heart.  And some yellow reagents are Datura, Dragon Turtle Fang, Poppy Pods and Thornbark.")
    return
end)

RegisterGlobalEvent(203, "Do you have the Ingredients?", function()
    if not evt.CheckItemsCount(DecorVar(2), 2) then
        evt.SimpleMessage("You are missing all or some of the needed ingredients.  Return when you have them all.")
        return
    end
    if not evt.CheckItemsCount(DecorVar(7), 3) then
        evt.SimpleMessage("You are missing all or some of the needed ingredients.  Return when you have them all.")
        return
    end
    if not evt.CheckItemsCount(DecorVar(12), 3) then
        evt.SimpleMessage("You are missing all or some of the needed ingredients.  Return when you have them all.")
        return
    end
    evt.SimpleMessage("Excellent!  With this I can brew another Potion of Pure Luck.  Take this potion as your reward!")
    evt.RemoveItems(DecorVar(2))
    evt.RemoveItems(DecorVar(7))
    evt.RemoveItems(DecorVar(12))
    ClearQBit(QBit(115)) -- Bring Rihansi in Alvar the basic ingredients for a potion of Pure Luck.
    SetQBit(QBit(116)) -- returned ingredients for a potion of Pure Luck
    AddValue(InventoryItem(264), 264) -- Pure Luck
    evt.ForPlayer(Players.All)
    AddValue(Experience, 5000)
    evt.SetNPCTopic(99, 2, 0) -- Rihansi topic 2 cleared
    return
end)
RegisterCanShowTopic(203, function()
    evt._BeginCanShowTopic(203)
    local visible = true
    if IsQBitSet(QBit(115)) then -- Bring Rihansi in Alvar the basic ingredients for a potion of Pure Luck.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(204, "Wasp Stingers", function()
    evt.SimpleMessage("Wasp stingers!  From cold remedies to herbal teas, a little bit of ground wasp stinger goes a long way!  Don't trust those who sell that weak ground wyvern horn!  Only wasp stinger will do if you want the best!  I'll pay you for every stinger you bring me!")
    return
end)

RegisterGlobalEvent(205, "500 Gold!", function()
    evt.SimpleMessage("I pay 500 gold for every wasp stinger you bring me!")
    evt.ForPlayer(Players.All)
    if HasItem(654) then -- Wasp Stingers
        evt.ForPlayer(Players.Member0)
        AddValue(Gold, 500)
        evt.ForPlayer(Players.All)
        RemoveItem(654) -- Wasp Stingers
        return
    end
    evt.SimpleMessage("I only pay for Wasp Stingers!  Nothing more, nothing less!")
    return
end)

RegisterGlobalEvent(206, "Survival!", function()
    evt.SimpleMessage("Trolls have a natural fear of fire!  Many of us perished when the Gate of Fire opened and spilled out the lake of fire! Without appropriate protection, there was nothing we could do.")
    return
end)

RegisterGlobalEvent(207, "Quest", function()
    evt.SimpleMessage("The survivors in this region need Potions of Fire Resistance!  With them we can survive until a place is found for us to move to!  Take these potions!  Unfortunately they are all I have!  Deliver them to the six southernmost houses that remain standing in the village of Rust!")
    SetQBit(QBit(142)) -- Deliver Fire Resistance Potions to the six southernmost houses of Rust. Return to Hobert in Rust.
    AddValue(InventoryItem(256), 256) -- Fire Resistance
    AddValue(InventoryItem(256), 256) -- Fire Resistance
    AddValue(InventoryItem(256), 256) -- Fire Resistance
    evt.SetNPCTopic(186, 1, 208) -- Pole topic 1: Not enough potions?
    return
end)
RegisterCanShowTopic(207, function()
    evt._BeginCanShowTopic(207)
    local visible = true
    if IsQBitSet(QBit(149)) then -- Southern houses of Rust all have Potions of Fire Resistance.
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(208, "Not enough potions?", function()
    if not IsQBitSet(QBit(149)) then -- Southern houses of Rust all have Potions of Fire Resistance.
        evt.SimpleMessage("You have not delivered Potions of Fire Resistance to all of the houses!  If the lake of fire grows in size everyone will perish!")
        return
    end
    evt.SimpleMessage("Thanks for providing Potions of Fire Resistance to the southernmost houses here in Rust.  Perhaps we can survive until a new home can be found for us!")
    evt.ForPlayer(Players.Member0)
    AddValue(Gold, 1500)
    evt.ForPlayer(Players.All)
    SetAward(Award(52)) -- Brought Potions of Fire Resistance to the southern houses of Rust.
    ClearQBit(QBit(142)) -- Deliver Fire Resistance Potions to the six southernmost houses of Rust. Return to Hobert in Rust.
    evt.SetNPCTopic(186, 1, 209) -- Pole topic 1: The village can hold its own.
    return
end)

RegisterGlobalEvent(209, "The village can hold its own.", function()
    evt.SimpleMessage("You have at least pushed our demise away for a time, but a new home needs to be found for us!  Thank you for delivering the Potions of Fire Resistance!")
    return
end)

RegisterGlobalEvent(210, "Potion of Pure Endurance", function()
    evt.SimpleMessage("Endurance.  That ability which keeps a warrior on his feet, or lets him down gently as he slides into unconsciousness.  A Potion of Pure Endurance can boost a person's ability to take damage to a legendary strength!  Bring me the basic ingredients of a Potion of Pure Endurance and I will reward you well.")
    SetQBit(QBit(121)) -- Bring Talion in the Ironsand Desert the basic ingredients for a potion of Pure Endurance.
    evt.SetNPCTopic(160, 0, 212) -- Talion topic 0: Do you have the Ingredients?
    return
end)
RegisterCanShowTopic(210, function()
    evt._BeginCanShowTopic(210)
    local visible = true
    if IsQBitSet(QBit(121)) then -- Bring Talion in the Ironsand Desert the basic ingredients for a potion of Pure Endurance.
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(211, "Ingredients", function()
    evt.SimpleMessage("Black Potions are made of a complex blending of many of the three basic alchemical reagents. Red reagents include Widowsweep Berries, Wolf's Eye, and Phials of Gog Blood.  Some blue reagents are Phoenix Feather, Phima Root, Meteor Fragment and Will O' Wisps Heart.  And some yellow reagents are Datura, Dragon Turtle Fang, Poppy Pods and Thornbark.")
    return
end)

RegisterGlobalEvent(212, "Do you have the Ingredients?", function()
    if not evt.CheckItemsCount(DecorVar(2), 2) then
        evt.SimpleMessage("You are missing all or some of the needed ingredients.  Return when you have them all.")
        return
    end
    if not evt.CheckItemsCount(DecorVar(7), 4) then
        evt.SimpleMessage("You are missing all or some of the needed ingredients.  Return when you have them all.")
        return
    end
    if not evt.CheckItemsCount(DecorVar(12), 1) then
        evt.SimpleMessage("You are missing all or some of the needed ingredients.  Return when you have them all.")
        return
    end
    evt.SimpleMessage("Excellent!  With this I can brew another Potion of Pure Luck.  Take this potion as your reward!")
    evt.RemoveItems(DecorVar(2))
    evt.RemoveItems(DecorVar(7))
    evt.RemoveItems(DecorVar(12))
    ClearQBit(QBit(121)) -- Bring Talion in the Ironsand Desert the basic ingredients for a potion of Pure Endurance.
    SetQBit(QBit(122)) -- returned ingredients for a potion of Pure Endurance
    AddValue(InventoryItem(267), 267) -- Pure Endurance
    evt.ForPlayer(Players.All)
    AddValue(Experience, 5000)
    evt.SetNPCTopic(160, 2, 0) -- Talion topic 2 cleared
    return
end)
RegisterCanShowTopic(212, function()
    evt._BeginCanShowTopic(212)
    local visible = true
    if IsQBitSet(QBit(121)) then -- Bring Talion in the Ironsand Desert the basic ingredients for a potion of Pure Endurance.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(213, "Quest", function()
    evt.SimpleMessage("The Dragonbane Flower has many medicinal uses.  It also has some uses that are less than medicinal.  From this flower we can distill a poison that is deadly to Dragons.  With it we should be able to make quick work of the Dragon vermin that infest this region.  Find this flower and return to me with it.  You will not be disappointed by my reward.")
    SetQBit(QBit(150)) -- Find a Dragonbane Flower for Calindril in Garrote Gorge.
    evt.SetNPCTopic(231, 0, 214) -- Calindril topic 0: Poison!
    return
end)
RegisterCanShowTopic(213, function()
    evt._BeginCanShowTopic(213)
    local visible = true
    if IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(214, "Poison!", function()
    evt.ForPlayer(Players.All)
    if not HasItem(636) then -- Dragonbane Flower
        evt.SimpleMessage("I asked for the Dragonbane Flower and you return empty handed.  Why waste my time?")
        return
    end
    SetQBit(QBit(151)) -- Found Dragonbane for Dragon Hunters
    ClearQBit(QBit(150)) -- Find a Dragonbane Flower for Calindril in Garrote Gorge.
    RemoveItem(636) -- Dragonbane Flower
    evt.ForPlayer(Players.Member0)
    AddValue(Gold, 1500)
    evt.ForPlayer(Players.All)
    AddValue(Experience, 10000)
    SetAward(Award(57)) -- Found the Dragonbane flower for Calindril in the Garrote Gorge Dragon Hunter's Fort.
    evt.SimpleMessage("The Dragons of Garrote Gorge are susceptible to a poison that can be distilled from the rare dragonbane flower.  The flower also is the only means of an antidote for the Dragons.")
    evt.SetNPCTopic(231, 0, 215) -- Calindril topic 0: Thanks for your help!
    return
end)

RegisterGlobalEvent(215, "Thanks for your help!", function()
    evt.SimpleMessage("Yes, this is indeed the Dragonbane Flower.  Once we have distilled the poison, we will wipe the Dragon population out!")
    return
end)

RegisterGlobalEvent(216, "Quest", function()
    evt.SimpleMessage("The Dragonbane Flower has many medicinal uses.  It also has some uses that are less than medicinal.  From this flower a poison is made that is deadly to dragons, but the poison's antidote is also found in its petals. Find this flower and return to me with it.  You will not be disappointed by my reward.")
    SetQBit(QBit(152)) -- Find a Dragonbane Flower for the Balion Tearwing in the Garrote Gorge Dragon Caves.
    evt.SetNPCTopic(239, 0, 217) -- Balion Tearwing topic 0: Poison!
    return
end)
RegisterCanShowTopic(216, function()
    evt._BeginCanShowTopic(216)
    local visible = true
    if IsQBitSet(QBit(21)) then -- Allied with Charles Quioxte's Dragon Hunters. Return Dragon Egg to Quixote done.
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(217, "Poison!", function()
    evt.ForPlayer(Players.All)
    if not HasItem(636) then -- Dragonbane Flower
        evt.SimpleMessage("I asked for the Dragonbane Flower and you return empty handed.  Why waste my time?")
        return
    end
    SetQBit(QBit(153)) -- Found Dragonbane for Dragons
    ClearQBit(QBit(152)) -- Find a Dragonbane Flower for the Balion Tearwing in the Garrote Gorge Dragon Caves.
    RemoveItem(636) -- Dragonbane Flower
    evt.ForPlayer(Players.Member0)
    AddValue(Gold, 1500)
    evt.ForPlayer(Players.All)
    AddValue(Experience, 10000)
    SetAward(Award(58)) -- Found the Dragonbane flower for Balion Tearwing in Garrote Gorge.
    evt.SimpleMessage("The Dragons of Garrote Gorge are susceptible to a poison that can be distilled from the rare dragonbane flower.  The flower also is the only means of an antidote for the Dragons.")
    evt.SetNPCTopic(239, 0, 218) -- Balion Tearwing topic 0: Thanks for your help!
    return
end)

RegisterGlobalEvent(218, "Thanks for your help!", function()
    evt.SimpleMessage("Yes, this is indeed the Dragonbane Flower.  Once the petals are ingested we will be protected from the poison that the Dragon Hunter's would use against us.  ")
    return
end)

RegisterGlobalEvent(219, "Quest", function()
    if IsQBitSet(QBit(155)) then -- Killed all Dragons in Garrote Gorge Area
        ClearQBit(QBit(154)) -- Kill all the Dragons in the Garrote Gorge wilderness area. Return to Avalon in Garrote Gorge.
        evt.SimpleMessage("With all of the Dragons in the wilderness defeated, we can move on the Dragon Cave and eliminate the Dragons once and for all!  Thanks again for your help in defeating them.")
        AddValue(Gold, 2500)
        evt.ForPlayer(Players.All)
        AddValue(Experience, 20000)
        SetAward(Award(62)) -- Killed all of the Dragons in the Garrote Gorge area for Avalon in the Garrote Gorge Dragon Hunter's Fort.
        evt.SetNPCTopic(240, 0, 220) -- Avalon topic 0: At last!
        return
    elseif IsQBitSet(QBit(154)) then -- Kill all the Dragons in the Garrote Gorge wilderness area. Return to Avalon in Garrote Gorge.
        evt.SimpleMessage("You have not slain all of the vermin.  I have reports here that tell of Dragons still in the region.  Return when you have slain them all!")
    else
        evt.SimpleMessage("You seek to gain the favor of Charles Quixote?  Help us in his crusade against the Dragons of Garrote Gorge. If all of the Dragons in the region and in the Dragon Cave are slain, Charles Quixote will be sure to hear of your name! Return to me when they are all dead!  I will reward you well.")
        SetQBit(QBit(154)) -- Kill all the Dragons in the Garrote Gorge wilderness area. Return to Avalon in Garrote Gorge.
    end
    return
end)
RegisterCanShowTopic(219, function()
    evt._BeginCanShowTopic(219)
    local visible = true
    if IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(220, "At last!", function()
    evt.SimpleMessage("You have slain the vermin!  Here is the reward that I promised!  I will also personally mention your assistance to Charles Quixote!")
    return
end)

RegisterGlobalEvent(221, "Quest", function()
    if IsQBitSet(QBit(158)) then -- Killed all Dragon Hunters in Garrote Gorge wilderness area
        evt.SimpleMessage("With all of the Dragon hunters in the wilderness defeated, we can move on their camp and eliminate them once and for all!  Thanks again for your help in defeating them.")
        AddValue(Gold, 2500)
        evt.ForPlayer(Players.All)
        AddValue(Experience, 20000)
        SetAward(Award(63)) -- Killed all of the Dragon Hunters in the Garrote Gorge are for Jerin Flame-eye in the Dragon Cave of Garrote Gorge.
        ClearQBit(QBit(157)) -- Kill all the Dragon Hunter's in the Garrote Gorge wilderness area. Return to Jerin Flame-eye in the Garrote Gorge Dragon Caves.
        evt.SetNPCTopic(273, 0, 222) -- Jerin Flame-eye topic 0: Land is ours yet again!
        return
    elseif IsQBitSet(QBit(157)) then -- Kill all the Dragon Hunter's in the Garrote Gorge wilderness area. Return to Jerin Flame-eye in the Garrote Gorge Dragon Caves.
        evt.SimpleMessage("You have not slain all of the Dragon hunters.  A Flight returned just moments ago and reported seeing them out on the plains.  Return when you have slain them all!")
    else
        evt.SimpleMessage("You seek the favor of Deftclaw Redreaver?  Don't we all?  If you were to kill all of the Dragon hunters in the Garrote Gorge wilderness, I would be certain to mention you to him.  I would also be in the position to offer you a generous reward!")
        SetQBit(QBit(157)) -- Kill all the Dragon Hunter's in the Garrote Gorge wilderness area. Return to Jerin Flame-eye in the Garrote Gorge Dragon Caves.
    end
    return
end)
RegisterCanShowTopic(221, function()
    evt._BeginCanShowTopic(221)
    local visible = true
    if IsQBitSet(QBit(21)) then -- Allied with Charles Quioxte's Dragon Hunters. Return Dragon Egg to Quixote done.
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(222, "Land is ours yet again!", function()
    evt.SimpleMessage("The infernal dragon hunters of Charles Quixote are dead? Fantastic!  We can once again enjoy the peace of Garrote Gorge without fear.  Here is your promised reward!  I will go speak with Deftclaw Redreaver of your bravery this instant!")
    return
end)

RegisterGlobalEvent(223, "Quest", function()
    evt.SimpleMessage("The Drum of Victory needs to be recovered if we are to ever defeat the Dragons in this region.  If you were to recover the Drum I would reward you well!")
    SetQBit(QBit(160)) -- Find the Legendary Drum of Victory. Return it to Zelim in Garrote Gorge.
    evt.SetNPCTopic(274, 0, 225) -- Zelim topic 0: Where is the drum?
    return
end)

RegisterGlobalEvent(224, "Drum of Victory History", function()
    evt.SimpleMessage("The Drum of Victory was brought here by Charles Quixote.  Its deafening sound drives terror into the heart of any Dragon who hears it.  Unfortunately is was lost in a battle against the Nagas when Charles Quixote was trying to establish his keep, here in Garrote Gorge.")
    return
end)

RegisterGlobalEvent(225, "Where is the drum?", function()
    evt.ForPlayer(Players.All)
    if not HasItem(615) then -- Drum of Victory
        evt.SimpleMessage("Return when you have the Drum of Victory.  You waste your time and mine otherwise!")
        return
    end
    evt.SimpleMessage("You have returned with the Drum of Victory!  Charles will be grateful for its return!  Here is your promised reward.")
    evt.ForPlayer(Players.Member0)
    AddValue(Gold, 1500)
    evt.ForPlayer(Players.All)
    ClearQBit(QBit(160)) -- Find the Legendary Drum of Victory. Return it to Zelim in Garrote Gorge.
    ClearQBit(QBit(246)) -- Drum of Victory - I lost it!
    RemoveItem(615) -- Drum of Victory
    AddValue(Experience, 20000)
    evt.SetNPCTopic(274, 0, 0) -- Zelim topic 0 cleared
end)

RegisterGlobalEvent(226, "Quest", function()
    evt.SimpleMessage("For years the Guild of Necromancers has searched for the Bone of Doom.  The powerful artifact would be of great use to them if recovered.  If you were to find this item and bring it to me, you will be rewarded beyond your wildest dreams.")
    SetQBit(QBit(166)) -- Find the Bone of Doom for Tantilion of Shadowspire.
    evt.SetNPCTopic(275, 0, 228) -- Tantilion topic 0: Great!
    return
end)

RegisterGlobalEvent(227, "Bone History", function()
    evt.SimpleMessage("In times almost forgotten a powerful Necromancer named Zacharia almost dominated all of Jadame.  His mastery of the dark arts of necromancy and the elemental magics were combined with an unnaturally strong afinity for Dark energy. His legions of undead helped him enslave all peoples, including the Dark Elves of Alvar.  A plan was made by the Temple of the Sun to defeat Zacharia.  Utilizing the combined might of all of the Clerics in the Temple they forged the sword named Solkrist.  The Patriarch of the Temple led the legions of the Sun against the forces of Zacharia.  The battle raged for years after which the forces of the Temple of the Sun found themselves at the base of the dreaded Shadowspire.  There the Patriarch battled Zarcharia in single combat. At the end of the battle both the Patriarch and Zacharia lay dead.  The Patriarch had cut the left arm from Zacharia's body just as the Necromancer's last spell stopped the Patriarch's heart.  The power of the sword Solkrist instantly slew the Necromancer.  Solkrist disappeared forever in the mayhem after the fight, as did the arm of Zacharia.  The bone from this arm was so instilled with such Dark Magic that it was called the Bone of Doom.")
    return
end)

RegisterGlobalEvent(228, "Great!", function()
    evt.ForPlayer(Players.All)
    if not HasItem(637) then -- Bone of Doom
        evt.SimpleMessage("I ask for the Bone, and you return with nothing. Be gone!")
        return
    end
    evt.SimpleMessage("Ah, the Bone of Doom!  The legend of Zacharia will continue!  Here is your reward!")
    AddValue(Gold, 1500)
    ClearQBit(QBit(166)) -- Find the Bone of Doom for Tantilion of Shadowspire.
    ClearQBit(QBit(247)) -- Bone of Doom - I lost it!
    evt.ForPlayer(Players.All)
    RemoveItem(637) -- Bone of Doom
    AddValue(Experience, 7500)
    evt.ForPlayer(Players.Member0)
    AddValue(Gold, 7500)
    evt.SetNPCTopic(275, 0, 0) -- Tantilion topic 0 cleared
end)

RegisterGlobalEvent(229, "Quest", function()
    evt.SimpleMessage("Some say that Iseldir's Puzzle Box is cursed and that use of it will make the owner go slowly mad.  This can't be true!  All of my studies have provided me with enough proof to determine that the box is the ultimate game in Jadame--not that ridiculous card game, Arcomage.  The last reported owner of Iseldir's Puzzle Box was Zanthora, who is also known as the Mad Necromancer of Shadowspire.")
    SetQBit(QBit(162)) -- Find Iseldir's Puzzle Box for Benefice of Shadowspire.
    evt.SetNPCTopic(276, 0, 231) -- Benefice topic 0: Hours of Enjoyment!
    return
end)

RegisterGlobalEvent(230, "Puzzle History", function()
    evt.SimpleMessage("I ask you to recover the Puzzle Box and you return with nothing.  So you reward is nothing.  Return with the box!")
    return
end)

RegisterGlobalEvent(231, "Hours of Enjoyment!", function()
    evt.ForPlayer(Players.All)
    if not HasItem(613) then -- Puzzle Box
        evt.SimpleMessage("I need not see you again until you have the Puzzle Box!")
        return
    end
    evt.SimpleMessage("The Puzzle Box is mine!  Hours of mindless enjoyment at my finger tips!  Here, take you reward for it is nothing compared to the box!")
    AddValue(Gold, 1500)
    ClearQBit(QBit(162)) -- Find Iseldir's Puzzle Box for Benefice of Shadowspire.
    ClearQBit(QBit(249)) -- Puzzle Box - I lost it!
    evt.ForPlayer(Players.All)
    RemoveItem(613) -- Puzzle Box
    AddValue(Experience, 15000)
    evt.SetNPCTopic(276, 0, 0) -- Benefice topic 0 cleared
end)

RegisterGlobalEvent(232, "Potion of Pure Intellect", function()
    evt.SimpleMessage("A Necromancer's greatest ability is his Intellect!  Without sufficient Intellect, a Necromancer can find himself without spell points when he needs them most! If you bring me the basic ingredients of a Potion of Pure Intellect, I will reward you with the potion that I create!")
    SetQBit(QBit(123)) -- Bring Kelvin in Shadowspire the basic ingredients for a potion of Pure Intellect.
    evt.SetNPCTopic(185, 0, 0) -- Kelvin topic 0 cleared
    return
end)
RegisterCanShowTopic(232, function()
    evt._BeginCanShowTopic(232)
    local visible = true
    if IsQBitSet(QBit(123)) then -- Bring Kelvin in Shadowspire the basic ingredients for a potion of Pure Intellect.
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(233, "War between the Guild and Temple", function()
    evt.SimpleMessage("Centuries ago the largest battle to date between the Guild of Necromancers and the Temple of the Sun was fought on this spot!  So much magical energy was released that the very ground was scorched and is black to this very day!")
    return
end)

RegisterGlobalEvent(234, "Do you have the Ingredients?", function()
    if not evt.CheckItemsCount(DecorVar(2), 1) then
        evt.SimpleMessage("You are missing all or some of the needed ingredients.  Return when you have them all.")
        return
    end
    if not evt.CheckItemsCount(DecorVar(7), 2) then
        evt.SimpleMessage("You are missing all or some of the needed ingredients.  Return when you have them all.")
        return
    end
    if not evt.CheckItemsCount(DecorVar(12), 4) then
        evt.SimpleMessage("You are missing all or some of the needed ingredients.  Return when you have them all.")
        return
    end
    evt.SimpleMessage("You have returned with the ingredients, holding up you end of the bargain.  Here is your Potion of Pure Intellect.")
    evt.RemoveItems(DecorVar(2))
    evt.RemoveItems(DecorVar(7))
    evt.RemoveItems(DecorVar(12))
    ClearQBit(QBit(123)) -- Bring Kelvin in Shadowspire the basic ingredients for a potion of Pure Intellect.
    SetQBit(QBit(124)) -- returned ingredients for a potion of Pure Intellect
    AddValue(InventoryItem(266), 266) -- Pure Intellect
    evt.ForPlayer(Players.All)
    AddValue(Experience, 5000)
    evt.SetNPCTopic(185, 2, 0) -- Kelvin topic 2 cleared
    return
end)
RegisterCanShowTopic(234, function()
    evt._BeginCanShowTopic(234)
    local visible = true
    if IsQBitSet(QBit(123)) then -- Bring Kelvin in Shadowspire the basic ingredients for a potion of Pure Intellect.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(235, "Quest", function()
    evt.SimpleMessage("We seek to put to rest the soul of the Nosferatu called Korbu.  We have heard rumors that the vampires of Shadowspire seek to resurrect this ancient evil.  There is a Vial of Grave Dirt kept hidden in the Vampire Crypt in the region of Shadowspire that is instrumental in bringing Korbu back to life.  Find us this vial and return it to us.  We will always be in your debt and we will reward you well.")
    SetQBit(QBit(164)) -- Find a Vial of Grave Dirt. Return it to Halien in Shadowspire.
    evt.SetNPCTopic(277, 0, 237) -- Hallien topic 0: Do you have the vial?
    return
end)

RegisterGlobalEvent(236, "Vial of Grave Dirt", function()
    evt.SimpleMessage("Korbu scattered vials of the dirt from his original grave to safe guard himself.  This way he could always gain access to the dirt and move his crypt if he needed to.")
    return
end)

RegisterGlobalEvent(237, "Do you have the vial?", function()
    evt.ForPlayer(Players.All)
    if not HasItem(614) then -- Vial of Grave Earth
        evt.SimpleMessage("Where is the Vial of Grave Dirt?  Do not bother me until you have it!")
        return
    end
    evt.SimpleMessage("Ah, once we perform the Rites of Purification upon this dirt, Korbu will rest eternally.  We are in your debt and here is your reward as promised!")
    evt.ForPlayer(Players.Member0)
    AddValue(Gold, 1500)
    evt.ForPlayer(Players.All)
    RemoveItem(614) -- Vial of Grave Earth
    ClearQBit(QBit(164)) -- Find a Vial of Grave Dirt. Return it to Halien in Shadowspire.
    ClearQBit(QBit(248)) -- Vial of Grave Dirt - I lost it!
    AddValue(Experience, 22000)
    evt.SetNPCTopic(277, 0, 0) -- Hallien topic 0 cleared
    return
end)

RegisterGlobalEvent(238, "Potion of Pure Personality", function()
    evt.SimpleMessage("Personality--the cleric's truest strength.  If you were to provide me with the basic ingredients of a Potion of Pure Personality, I would be more than happy to brew one for you!  Bring me the ingredients!")
    SetQBit(QBit(125)) -- Bring Castigeir in Murmurwoods the basic ingredients for a potion of Pure Personality.
    evt.SetNPCTopic(232, 0, 0) -- Castigeir topic 0 cleared
    return
end)
RegisterCanShowTopic(238, function()
    evt._BeginCanShowTopic(238)
    local visible = true
    if IsQBitSet(QBit(125)) then -- Bring Castigeir in Murmurwoods the basic ingredients for a potion of Pure Personality.
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(239, "Ingredients", function()
    evt.SimpleMessage("Black Potions are made of a complex blending of many of the three basic alchemical reagents. Red reagents include Widowsweep Berries, Wolf's Eye, and Phials of Gog Blood.  Some blue reagents are Phoenix Feather, Phima Root, Meteor Fragment and Will O' Wisps Heart.  And some yellow reagents are Datura, Dragon Turtle Fang, Poppy Pods and Thornbark.")
    return
end)

RegisterGlobalEvent(240, "Thanks for the Ingredients", function()
    if not evt.CheckItemsCount(DecorVar(2), 1) then
        evt.SimpleMessage("You are missing all or some of the needed ingredients.  Return when you have them all.")
        return
    end
    if not evt.CheckItemsCount(DecorVar(7), 4) then
        evt.SimpleMessage("You are missing all or some of the needed ingredients.  Return when you have them all.")
        return
    end
    if not evt.CheckItemsCount(DecorVar(12), 2) then
        evt.SimpleMessage("You are missing all or some of the needed ingredients.  Return when you have them all.")
        return
    end
    evt.SimpleMessage("Ah, you learned the recipe or are very lucky!  Here is your potion!")
    evt.RemoveItems(DecorVar(2))
    evt.RemoveItems(DecorVar(7))
    evt.RemoveItems(DecorVar(12))
    ClearQBit(QBit(125)) -- Bring Castigeir in Murmurwoods the basic ingredients for a potion of Pure Personality.
    SetQBit(QBit(126)) -- returned ingredients for a potion of Pure Personallity
    AddValue(InventoryItem(268), 268) -- Pure Personality
    evt.ForPlayer(Players.All)
    AddValue(Experience, 5000)
    evt.SetNPCTopic(232, 2, 0) -- Castigeir topic 2 cleared
    return
end)
RegisterCanShowTopic(240, function()
    evt._BeginCanShowTopic(240)
    local visible = true
    if IsQBitSet(QBit(125)) then -- Bring Castigeir in Murmurwoods the basic ingredients for a potion of Pure Personality.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(241, "Ancient Wyverns", function()
    evt.SimpleMessage("Wyverns are one of the toughest creatures that roam the continent of Jadame.  The Ancient Wyvern can even slay the mightiest adventurer with one blow.  The horn of the Ancient Wyvern is said to have many medicinal any magical properties.  There are many people who pay well for ground wyvern horn.")
    return
end)

RegisterGlobalEvent(242, "Bounty for Horn of the Wyvern", function()
    evt.SimpleMessage("I will buy Wyvern horns from you for 1500 gold!  I grind these horns up and sell them throughout Jadame.  Someday I hope to be able to ship them over sea to Enroth and Erathia.  That of course depends on whether the Pirates of Regna are still a problem to shipping or not!")
    evt.SetNPCTopic(187, 1, 243) -- Xevius topic 1: 1500 gold!
    return
end)

RegisterGlobalEvent(243, "1500 gold!", function()
    evt.SimpleMessage("1500 gold!")
    evt.ForPlayer(Players.All)
    if HasItem(640) then -- Wyvern Horn
        evt.ForPlayer(Players.Member0)
        AddValue(Gold, 500)
        evt.ForPlayer(Players.All)
        RemoveItem(640) -- Wyvern Horn
        return
    end
    evt.SimpleMessage("Return when you have more Wyvern Horns and I will pay you more!")
    return
end)

RegisterGlobalEvent(244, "Potion of Pure Accuracy", function()
    evt.SimpleMessage("Accuracy can determine who lives and who dies in battle.  If you cannot hit your opponent you will surely perish!  If you bring me the ingredients of a Potion of Pure Accuracy, I will brew that potion for you.")
    SetQBit(QBit(133)) -- returned ingredients for a potion of Pure Accuracy
    evt.SetNPCTopic(124, 0, 0) -- Galvinus topic 0 cleared
    return
end)
RegisterCanShowTopic(244, function()
    evt._BeginCanShowTopic(244)
    local visible = true
    if IsQBitSet(QBit(133)) then -- returned ingredients for a potion of Pure Accuracy
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(245, "Ingredients", function()
    evt.SimpleMessage("Black Potions are made of a complex blending of many of the three basic alchemical reagents. Red reagents include Widowsweep Berries, Wolf's Eye, and Phials of Gog Blood.  Some blue reagents are Phoenix Feather, Phima Root, Meteor Fragment and Will O' Wisps Heart.  And some yellow reagents are Datura, Dragon Turtle Fang, Poppy Pods and Thornbark.")
    return
end)

RegisterGlobalEvent(246, "Do you have the Ingredients?", function()
    if not evt.CheckItemsCount(DecorVar(2), 2) then
        evt.SimpleMessage("You are missing all or some of the needed ingredients.  Return when you have them all.")
        return
    end
    if not evt.CheckItemsCount(DecorVar(7), 1) then
        evt.SimpleMessage("You are missing all or some of the needed ingredients.  Return when you have them all.")
        return
    end
    if not evt.CheckItemsCount(DecorVar(12), 4) then
        evt.SimpleMessage("You are missing all or some of the needed ingredients.  Return when you have them all.")
        return
    end
    evt.SimpleMessage("Ah, the right ingredients always do the trick! Here is your potion.")
    evt.RemoveItems(DecorVar(2))
    evt.RemoveItems(DecorVar(7))
    evt.RemoveItems(DecorVar(12))
    ClearQBit(QBit(133)) -- returned ingredients for a potion of Pure Accuracy
    SetQBit(QBit(134)) -- Gave Gem of Restoration to Blazen Stormlance
    AddValue(InventoryItem(269), 269) -- Pure Accuracy
    evt.ForPlayer(Players.All)
    AddValue(Experience, 5000)
    evt.SetNPCTopic(124, 2, 0) -- Galvinus topic 2 cleared
    return
end)
RegisterCanShowTopic(246, function()
    evt._BeginCanShowTopic(246)
    local visible = true
    if IsQBitSet(QBit(133)) then -- returned ingredients for a potion of Pure Accuracy
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(247, "Dread Pirate Stanley's Treasure", function()
    evt.SimpleMessage("The legendary Pirate Stanley is rumored to have stolen hundreds and thousands of gold pieces from the Merchants of Alvar.  No one has ever found where he has hidden his treasure.  Some say it isn't even hidden on the Island of Regna.")
    return
end)

RegisterGlobalEvent(248, "Riches", function()
    evt.SimpleMessage("Years and years ago, I remember hearing that Stanley journeyed to Ravage Roaming to speak with the Ogre Mage Zog about a curse that had fallen upon him.  Apparently his memory was fading, and he was certain that an evil mage was responsible.")
    return
end)

RegisterGlobalEvent(249, "Quest", function()
    if not IsQBitSet(QBit(168)) then -- Found the treasure of the Dread Pirate Stanley!
        evt.SimpleMessage("You have not found the treasure of the Dread Pirate Stanley!  ")
        SetQBit(QBit(236)) -- Find the treasure of the Dread Pirate Stanley.
        return
    end
    AddValue(Experience, 15500)
    evt.SimpleMessage("He who finds the treasure of the Dread Pirate Stanley will be a rich person!  Will that person be you?")
    ClearQBit(QBit(236)) -- Find the treasure of the Dread Pirate Stanley.
    evt.SetNPCTopic(278, 0, 0) -- One-Eye topic 0 cleared
    return
end)

RegisterGlobalEvent(250, "Buy Tobersk Fruit for 200 gold", function()
    evt.SimpleMessage("Tobersk fruit is native only to the Dagger Wound Island region.  Here the mild winters and humid summers provide the perfect conditions for the Tobersk fruit to achieve the correct levels of sugar and juice.  The pulp masters in Ravenshore pay good money for the tobersk fruit.")
    ClearQBit(QBit(251)) -- Bought Item pulp
    if IsAtLeast(Gold, 200) then
        SubtractValue(Gold, 200)
        AddValue(InventoryItem(643), 643) -- Tobersk Fruit
        SetQBit(QBit(250)) -- Bought Item fruit
        SetQBit(QBit(259)) -- Can't keep buying fruit
        return
    end
    evt.SimpleMessage("You don't have enough gold!")
    return
end)
RegisterCanShowTopic(250, function()
    evt._BeginCanShowTopic(250)
    local visible = true
    if IsQBitSet(QBit(252)) then -- Bought Item brandy
        visible = true
        return visible
    else
        if IsQBitSet(QBit(259)) then -- Can't keep buying fruit
            visible = false
            return visible
        else
            visible = true
            return visible
        end
    end
end)

RegisterGlobalEvent(251, "Sell Tobersk Brandy", function()
    evt.ForPlayer(Players.All)
    if not HasItem(645) then return end -- Tobersk Brandy
    evt.SimpleMessage("Tobersk brandy is favorite drink of the Lizardmen of Dagger Wound Island.  Some call it an acquired taste.  How ever you look at it, it equals pure profit!")
    RemoveItem(645) -- Tobersk Brandy
    ClearQBit(QBit(261)) -- Can't keep buying brandy
    evt.ForPlayer(Players.Current)
    if IsAtLeast(DayOfWeek, 0) then
        AddValue(Gold, 557)
        return
    elseif IsAtLeast(DayOfWeek, 1) then
        AddValue(Gold, 589)
        return
    elseif IsAtLeast(DayOfWeek, 2) then
        AddValue(Gold, 511)
        return
    elseif IsAtLeast(DayOfWeek, 3) then
        AddValue(Gold, 577)
        return
    elseif IsAtLeast(DayOfWeek, 4) then
        AddValue(Gold, 513)
        return
    elseif IsAtLeast(DayOfWeek, 5) then
        AddValue(Gold, 544)
        return
    elseif IsAtLeast(DayOfWeek, 6) then
        AddValue(Gold, 511)
        return
    else
        return
    end
end)

RegisterGlobalEvent(252, "Buy Tobersk Pulp for 300 gold", function()
    evt.SimpleMessage("Tobersk fruit is processed in Ravenshore into tobersk pulp.  Its from this pulp that the master brewers in Alvar distill tobersk brandy.")
    ClearQBit(QBit(250)) -- Bought Item fruit
    if IsAtLeast(Gold, 300) then
        SubtractValue(Gold, 300)
        AddValue(InventoryItem(644), 644) -- Tobersk Pulp
        SetQBit(QBit(251)) -- Bought Item pulp
        SetQBit(QBit(260)) -- Can't keep buying pulp
        return
    end
    evt.SimpleMessage("You don't have enough gold!")
    return
end)
RegisterCanShowTopic(252, function()
    evt._BeginCanShowTopic(252)
    local visible = true
    if IsQBitSet(QBit(250)) then -- Bought Item fruit
        visible = true
        return visible
    else
        if IsQBitSet(QBit(260)) then -- Can't keep buying pulp
            visible = false
            return visible
        else
            visible = true
            return visible
        end
    end
end)

RegisterGlobalEvent(253, "Sell Tobersk Fruit", function()
    evt.ForPlayer(Players.All)
    if not HasItem(643) then return end -- Tobersk Fruit
    evt.SimpleMessage("Here the mild winters and humid summers provide the perfect conditions for the tobersk fruit to achieve the correct levels of sugar and juice.  Here you can purchase tobersk fruit so our pulp masters can labor over the fruit, processing it into tobersk pulp.")
    RemoveItem(643) -- Tobersk Fruit
    ClearQBit(QBit(259)) -- Can't keep buying fruit
    evt.ForPlayer(Players.Current)
    if IsAtLeast(DayOfWeek, 0) then
        AddValue(Gold, 261)
        return
    elseif IsAtLeast(DayOfWeek, 1) then
        AddValue(Gold, 286)
        return
    elseif IsAtLeast(DayOfWeek, 2) then
        AddValue(Gold, 237)
        return
    elseif IsAtLeast(DayOfWeek, 3) then
        AddValue(Gold, 255)
        return
    elseif IsAtLeast(DayOfWeek, 4) then
        AddValue(Gold, 294)
        return
    elseif IsAtLeast(DayOfWeek, 5) then
        AddValue(Gold, 273)
        return
    elseif IsAtLeast(DayOfWeek, 6) then
        AddValue(Gold, 244)
        return
    else
        return
    end
end)

RegisterGlobalEvent(254, "Buy Tobersk Brandy 500 gold", function()
    evt.SimpleMessage("Tobersk brandy is a favorite drink among the Lizardmen of Dagger Wound Island.  Some call it an acquired taste.  How ever you look at it, it equals pure profit!  Be gentle with the bottles as you travel back to the islands.")
    ClearQBit(QBit(251)) -- Bought Item pulp
    if IsAtLeast(Gold, 500) then
        SubtractValue(Gold, 500)
        AddValue(InventoryItem(645), 645) -- Tobersk Brandy
        SetQBit(QBit(252)) -- Bought Item brandy
        SetQBit(QBit(261)) -- Can't keep buying brandy
        return
    end
    evt.SimpleMessage("You don't have enough gold!")
    return
end)
RegisterCanShowTopic(254, function()
    evt._BeginCanShowTopic(254)
    local visible = true
    if IsQBitSet(QBit(251)) then -- Bought Item pulp
        visible = true
        return visible
    else
        if IsQBitSet(QBit(261)) then -- Can't keep buying brandy
            visible = false
            return visible
        else
            visible = true
            return visible
        end
    end
end)

RegisterGlobalEvent(255, "Sell Tobersk Pulp", function()
    evt.ForPlayer(Players.All)
    if not HasItem(644) then return end -- Tobersk Pulp
    evt.SimpleMessage("Tobersk pulp is combined with the waters of the Alvar River and is distilled over time until the brew masters declare it ready for consumption. ")
    RemoveItem(644) -- Tobersk Pulp
    ClearQBit(QBit(260)) -- Can't keep buying pulp
    evt.ForPlayer(Players.Current)
    if IsAtLeast(DayOfWeek, 0) then
        AddValue(Gold, 394)
        return
    elseif IsAtLeast(DayOfWeek, 1) then
        AddValue(Gold, 341)
        return
    elseif IsAtLeast(DayOfWeek, 2) then
        AddValue(Gold, 351)
        return
    elseif IsAtLeast(DayOfWeek, 3) then
        AddValue(Gold, 337)
        return
    elseif IsAtLeast(DayOfWeek, 4) then
        AddValue(Gold, 373)
        return
    elseif IsAtLeast(DayOfWeek, 5) then
        AddValue(Gold, 355)
        return
    elseif IsAtLeast(DayOfWeek, 6) then
        AddValue(Gold, 386)
        return
    else
        return
    end
end)

RegisterGlobalEvent(256, "Buy Heartwood of Jadame for 1000 gold", function()
    evt.SimpleMessage("The Heartwood of Jadame is used by the vampires of the Shadowspire region in the construction of their coffins.  The Heartwood's durability provides the coffin's owner with many years of rest during the daylight hours.")
    ClearQBit(QBit(255)) -- Bought Sunfish
    if IsAtLeast(Gold, 1000) then
        SubtractValue(Gold, 1000)
        AddValue(InventoryItem(646), 646) -- Heartwood of Jadame
        SetQBit(QBit(253)) -- Bought heartwood
        SetQBit(QBit(262)) -- Can't keep buying heartwood
        return
    end
    evt.SimpleMessage("You don't have enough gold!")
    return
end)
RegisterCanShowTopic(256, function()
    evt._BeginCanShowTopic(256)
    local visible = true
    if IsQBitSet(QBit(255)) then -- Bought Sunfish
        visible = true
        return visible
    else
        if IsQBitSet(QBit(262)) then -- Can't keep buying heartwood
            visible = false
            return visible
        else
            visible = true
            return visible
        end
    end
end)

RegisterGlobalEvent(257, "Sell Dried Sunfish", function()
    evt.ForPlayer(Players.All)
    if not HasItem(648) then return end -- Dried Sunfish
    evt.SimpleMessage("Dried sunfish is a delicacy enjoyed by the High Clerics of the Temple of the Sun.  They pay good money for deliveries of this flaky, somewhat salty fish.")
    RemoveItem(648) -- Dried Sunfish
    ClearQBit(QBit(264)) -- Can't keep buying sinfish
    evt.ForPlayer(Players.Current)
    if IsAtLeast(DayOfWeek, 0) then
        AddValue(Gold, 2234)
        return
    elseif IsAtLeast(DayOfWeek, 1) then
        AddValue(Gold, 2267)
        return
    elseif IsAtLeast(DayOfWeek, 2) then
        AddValue(Gold, 2250)
        return
    elseif IsAtLeast(DayOfWeek, 3) then
        AddValue(Gold, 2291)
        return
    elseif IsAtLeast(DayOfWeek, 4) then
        AddValue(Gold, 2244)
        return
    elseif IsAtLeast(DayOfWeek, 5) then
        AddValue(Gold, 2285)
        return
    elseif IsAtLeast(DayOfWeek, 6) then
        AddValue(Gold, 2273)
        return
    else
        return
    end
end)

RegisterGlobalEvent(258, "Buy Pirate Amulets for 1500 gold", function()
    evt.SimpleMessage("The Pirates of Regna like flamboyant jewelry!  Amulets that fail to take enchantments cast by the Necromancers of Shadowspire fill this need quite well.  The Pirates pay some of their \"hard earned\" bounty to get these amulets.")
    ClearQBit(QBit(253)) -- Bought heartwood
    if IsAtLeast(Gold, 1500) then
        SubtractValue(Gold, 1500)
        AddValue(InventoryItem(647), 647) -- Flawed Amulets
        SetQBit(QBit(254)) -- Bought amulets
        SetQBit(QBit(263)) -- Can't keep buying amulets
        return
    end
    evt.SimpleMessage("You don't have enough gold!")
    return
end)
RegisterCanShowTopic(258, function()
    evt._BeginCanShowTopic(258)
    local visible = true
    if IsQBitSet(QBit(253)) then -- Bought heartwood
        visible = true
        return visible
    else
        if IsQBitSet(QBit(263)) then -- Can't keep buying amulets
            visible = false
            return visible
        else
            visible = true
            return visible
        end
    end
end)

RegisterGlobalEvent(259, "Sell Heartwood of Jadame", function()
    evt.ForPlayer(Players.All)
    if not HasItem(646) then return end -- Heartwood of Jadame
    evt.SimpleMessage("The Heartwood of Jadame is used by the Vampires of the Shadowspire region in the construction of their coffins.  The Heartwood's durability provides the coffin's owner with many years of rest during the daylight hours.")
    RemoveItem(646) -- Heartwood of Jadame
    ClearQBit(QBit(262)) -- Can't keep buying heartwood
    evt.ForPlayer(Players.Current)
    if IsAtLeast(DayOfWeek, 0) then
        AddValue(Gold, 1761)
        return
    elseif IsAtLeast(DayOfWeek, 1) then
        AddValue(Gold, 1786)
        return
    elseif IsAtLeast(DayOfWeek, 2) then
        AddValue(Gold, 1637)
        return
    elseif IsAtLeast(DayOfWeek, 3) then
        AddValue(Gold, 1655)
        return
    elseif IsAtLeast(DayOfWeek, 4) then
        AddValue(Gold, 1794)
        return
    elseif IsAtLeast(DayOfWeek, 5) then
        AddValue(Gold, 1773)
        return
    elseif IsAtLeast(DayOfWeek, 6) then
        AddValue(Gold, 1744)
        return
    else
        return
    end
end)

RegisterGlobalEvent(260, "Buy Dried Sunfish for 2000 gold", function()
    evt.SimpleMessage("Dried Sunfish is a delicacy enjoyed by the High Clerics of the Temple of the Sun.  They pay good money for deliveries of this flaky, somewhat salty fish.")
    ClearQBit(QBit(254)) -- Bought amulets
    if IsAtLeast(Gold, 2000) then
        SubtractValue(Gold, 2000)
        AddValue(InventoryItem(648), 648) -- Dried Sunfish
        SetQBit(QBit(255)) -- Bought Sunfish
        SetQBit(QBit(264)) -- Can't keep buying sinfish
        return
    end
    evt.SimpleMessage("You don't have enough gold!")
    return
end)
RegisterCanShowTopic(260, function()
    evt._BeginCanShowTopic(260)
    local visible = true
    if IsQBitSet(QBit(254)) then -- Bought amulets
        visible = true
        return visible
    else
        if IsQBitSet(QBit(264)) then -- Can't keep buying sinfish
            visible = false
            return visible
        else
            visible = true
            return visible
        end
    end
end)

RegisterGlobalEvent(261, "Sell Pirate Amulets", function()
    evt.ForPlayer(Players.All)
    if not HasItem(647) then return end -- Flawed Amulets
    evt.SimpleMessage("The Pirates of Regna like flamboyant jewelry!  Amulets that fail to take enchantments cast by the Necromancers of Shadowspire fill this need quite well.  The Pirates pay some of their \"hard earned\" bounty to get these amulets.")
    RemoveItem(647) -- Flawed Amulets
    ClearQBit(QBit(263)) -- Can't keep buying amulets
    evt.ForPlayer(Players.Current)
    if IsAtLeast(DayOfWeek, 0) then
        AddValue(Gold, 1994)
        return
    elseif IsAtLeast(DayOfWeek, 1) then
        AddValue(Gold, 2041)
        return
    elseif IsAtLeast(DayOfWeek, 2) then
        AddValue(Gold, 2051)
        return
    elseif IsAtLeast(DayOfWeek, 3) then
        AddValue(Gold, 2037)
        return
    elseif IsAtLeast(DayOfWeek, 4) then
        AddValue(Gold, 1973)
        return
    elseif IsAtLeast(DayOfWeek, 5) then
        AddValue(Gold, 1955)
        return
    elseif IsAtLeast(DayOfWeek, 6) then
        AddValue(Gold, 2086)
        return
    else
        return
    end
end)

RegisterGlobalEvent(262, "Buy Silver Dust of the Sea for 5000 gold", function()
    evt.SimpleMessage("Purchase Silver Dust of the Sea made by the Necromancers of Shadowspire. It is used by the smugglers of Ravenshore to hide their boats.  It provides the boats with a limited form of invisibility.")
    ClearQBit(QBit(267)) -- Can't keep buying Ground Wyvern horn
    if IsAtLeast(Gold, 5000) then
        SubtractValue(Gold, 5000)
        AddValue(InventoryItem(649), 649) -- Silver Dust of the Sea
        SetQBit(QBit(253)) -- Bought heartwood
        SetQBit(QBit(262)) -- Can't keep buying heartwood
        return
    end
    evt.SimpleMessage("You don't have enough gold!")
    return
end)
RegisterCanShowTopic(262, function()
    evt._BeginCanShowTopic(262)
    local visible = true
    if IsQBitSet(QBit(258)) then -- Bought Item Ground Wyvern Horn
        visible = true
        return visible
    else
        if IsQBitSet(QBit(265)) then -- Can't keep buying Silver Dust of the Sea
            visible = false
            return visible
        else
            visible = true
            return visible
        end
    end
end)

RegisterGlobalEvent(263, "Sell Ground Wyvern Horn", function()
    evt.ForPlayer(Players.All)
    if not HasItem(651) then return end -- Ground Wyvern Horn
    evt.SimpleMessage("Ground Wyvern Horn is reported to be one of the most potent reagents used by the necromancers of Shadowspire.  Unlike the reagents used by alchemists, this reagent is only used by the highest ranking members of the Necromancers' Guild.")
    RemoveItem(651) -- Ground Wyvern Horn
    ClearQBit(QBit(267)) -- Can't keep buying Ground Wyvern horn
    evt.ForPlayer(Players.Current)
    if IsAtLeast(DayOfWeek, 0) then
        AddValue(Gold, 8234)
        return
    elseif IsAtLeast(DayOfWeek, 1) then
        AddValue(Gold, 8267)
        return
    elseif IsAtLeast(DayOfWeek, 2) then
        AddValue(Gold, 8250)
        return
    elseif IsAtLeast(DayOfWeek, 3) then
        AddValue(Gold, 8291)
        return
    elseif IsAtLeast(DayOfWeek, 4) then
        AddValue(Gold, 8244)
        return
    elseif IsAtLeast(DayOfWeek, 5) then
        AddValue(Gold, 8285)
        return
    elseif IsAtLeast(DayOfWeek, 6) then
        AddValue(Gold, 8273)
        return
    else
        return
    end
end)

RegisterGlobalEvent(264, "Buy Forged Credit Vouchers for 6500 gold", function()
    evt.SimpleMessage("These Forged Credit Vouchers are used by agents of the Ogre Mage Zog to acquire gold from the Merchants of Alvar.")
    ClearQBit(QBit(265)) -- Can't keep buying Silver Dust of the Sea
    if IsAtLeast(Gold, 6500) then
        SubtractValue(Gold, 6500)
        AddValue(InventoryItem(650), 650) -- Forged Vouchers
        SetQBit(QBit(257)) -- Bought Item Forged Credit Vouchers
        SetQBit(QBit(266)) -- Can't keep buying Forged Credit Vouchers
        return
    end
    evt.SimpleMessage("You don't have enough gold!")
    return
end)
RegisterCanShowTopic(264, function()
    evt._BeginCanShowTopic(264)
    local visible = true
    if IsQBitSet(QBit(256)) then -- Bought Item Silver Dust of the Sea
        visible = true
        return visible
    else
        if IsQBitSet(QBit(266)) then -- Can't keep buying Forged Credit Vouchers
            visible = false
            return visible
        else
            visible = true
            return visible
        end
    end
end)

RegisterGlobalEvent(265, "Sell Silver Dust of the Sea", function()
    evt.ForPlayer(Players.All)
    if not HasItem(649) then return end -- Silver Dust of the Sea
    evt.SimpleMessage("Purchase Silver Dust of the Sea made by the necromancers of Shadowspire. It is used by the Smuggler's of Ravenshore to hide their boats.  It provides the boats with a limited form of invisibility.")
    RemoveItem(649) -- Silver Dust of the Sea
    ClearQBit(QBit(265)) -- Can't keep buying Silver Dust of the Sea
    evt.ForPlayer(Players.Current)
    if IsAtLeast(DayOfWeek, 0) then
        AddValue(Gold, 6261)
        return
    elseif IsAtLeast(DayOfWeek, 1) then
        AddValue(Gold, 6286)
        return
    elseif IsAtLeast(DayOfWeek, 2) then
        AddValue(Gold, 6237)
        return
    elseif IsAtLeast(DayOfWeek, 3) then
        AddValue(Gold, 6255)
        return
    elseif IsAtLeast(DayOfWeek, 4) then
        AddValue(Gold, 6294)
        return
    elseif IsAtLeast(DayOfWeek, 5) then
        AddValue(Gold, 6273)
        return
    elseif IsAtLeast(DayOfWeek, 6) then
        AddValue(Gold, 6244)
        return
    else
        return
    end
end)

RegisterGlobalEvent(266, "Buy Ground Wyvern Horn for 7500 gold", function()
    evt.SimpleMessage("Ground Wyvern Horn is reported to be one of the most potent reagents used by the necromancers of Shadowspire.  Unlike the reagents used by alchemists, this reagents is only used by the highest members of the Necromancers' Guild.")
    ClearQBit(QBit(266)) -- Can't keep buying Forged Credit Vouchers
    if IsAtLeast(Gold, 7500) then
        SubtractValue(Gold, 7500)
        AddValue(InventoryItem(651), 651) -- Ground Wyvern Horn
        SetQBit(QBit(258)) -- Bought Item Ground Wyvern Horn
        SetQBit(QBit(267)) -- Can't keep buying Ground Wyvern horn
        return
    end
    evt.SimpleMessage("You don't have enough gold!")
    return
end)
RegisterCanShowTopic(266, function()
    evt._BeginCanShowTopic(266)
    local visible = true
    if IsQBitSet(QBit(257)) then -- Bought Item Forged Credit Vouchers
        visible = true
        return visible
    else
        if IsQBitSet(QBit(267)) then -- Can't keep buying Ground Wyvern horn
            visible = false
            return visible
        else
            visible = true
            return visible
        end
    end
end)

RegisterGlobalEvent(267, "Sell Forged Credit Vouchers", function()
    evt.ForPlayer(Players.All)
    if not HasItem(650) then return end -- Forged Vouchers
    evt.SimpleMessage("These Forged Credit Vouchers are used by agents of the Ogre Mage Zog to acquire gold from the Merchants of Alvar.")
    RemoveItem(650) -- Forged Vouchers
    ClearQBit(QBit(266)) -- Can't keep buying Forged Credit Vouchers
    evt.ForPlayer(Players.Current)
    if IsAtLeast(DayOfWeek, 0) then
        AddValue(Gold, 7294)
        return
    elseif IsAtLeast(DayOfWeek, 1) then
        AddValue(Gold, 7241)
        return
    elseif IsAtLeast(DayOfWeek, 2) then
        AddValue(Gold, 7251)
        return
    elseif IsAtLeast(DayOfWeek, 3) then
        AddValue(Gold, 7237)
        return
    elseif IsAtLeast(DayOfWeek, 4) then
        AddValue(Gold, 7273)
        return
    elseif IsAtLeast(DayOfWeek, 5) then
        AddValue(Gold, 7255)
        return
    elseif IsAtLeast(DayOfWeek, 6) then
        AddValue(Gold, 7286)
        return
    else
        return
    end
end)

RegisterGlobalEvent(268, "Empty Barrel", function()
    evt.StatusText("Empty Barrel")
end)

RegisterGlobalEvent(269, "Red Barrel", function()
    evt.StatusText("+2 Might permanent")
    AddValue(BaseMight, 2)
    SetAutonote(33) -- Red liquid grants Might.
    evt.ChangeEvent(268)
end)

RegisterGlobalEvent(270, "Yellow Barrel", function()
    evt.StatusText("+2 Accuracy permanent")
    AddValue(BaseAccuracy, 2)
    SetAutonote(37) -- Yellow liquid grants Accuracy.
    evt.ChangeEvent(268)
end)

RegisterGlobalEvent(271, "Blue Barrel", function()
    evt.StatusText("+2 Personality permanent")
    AddValue(BasePersonality, 2)
    SetAutonote(35) -- Blue liquid grants Personality.
    evt.ChangeEvent(268)
end)

RegisterGlobalEvent(272, "Orange Barrel", function()
    evt.StatusText("+2 Intellect permanent")
    AddValue(BaseIntellect, 2)
    SetAutonote(34) -- Orange liquid grants Intellect.
    evt.ChangeEvent(268)
end)

RegisterGlobalEvent(273, "Green Barrel", function()
    evt.StatusText("+2 Endurance permanent")
    AddValue(BaseEndurance, 2)
    SetAutonote(36) -- Green liquid grants Endurance.
    evt.ChangeEvent(268)
end)

RegisterGlobalEvent(274, "Purple Barrel", function()
    evt.StatusText("+2 Speed permanent")
    AddValue(BaseSpeed, 2)
    SetAutonote(38) -- Purple liquid grants Speed.
    evt.ChangeEvent(268)
end)

RegisterGlobalEvent(275, "White Barrel", function()
    evt.StatusText("+2 Luck permanent")
    AddValue(BaseLuck, 2)
    SetAutonote(39) -- White liquid grants Luck.
    evt.ChangeEvent(268)
end)

RegisterGlobalEvent(276, "Empty Cauldron", function()
    evt.StatusText("Empty Cauldron")
end)

RegisterGlobalEvent(277, "Steaming Cauldron", function()
    evt.StatusText("+2 Fire Resistance permanent")
    AddValue(FireResistance, 2)
    SetAutonote(40) -- Steaming liquid grants Fire Resistance.
    evt.ChangeEvent(276)
end)

RegisterGlobalEvent(278, "Frosty Cauldron", function()
    evt.StatusText("+2 Water Resistance permanent")
    AddValue(WaterResistance, 2)
    SetAutonote(41) -- Frosty liquid grants Water Resistance.
    evt.ChangeEvent(276)
end)

RegisterGlobalEvent(279, "Shocking Cauldron", function()
    evt.StatusText("+2 Air Resistance permanent")
    AddValue(AirResistance, 2)
    SetAutonote(42) -- Shocking liquid grants Air Resistance.
    evt.ChangeEvent(276)
end)

RegisterGlobalEvent(280, "Dirty Cauldron", function()
    evt.StatusText("+2 Earth Resistance permanent")
    AddValue(EarthResistance, 2)
    SetAutonote(43) -- Dirty liquid grants Earth Resistance.
    evt.ChangeEvent(276)
end)

RegisterGlobalEvent(281, "Trash Heap", function()
    local randomStep = PickRandomOption(281, 1, {1, 6, 11})
    if randomStep == 1 then
        if not IsAtLeast(PerceptionSkill, 1) then
            SetValue(DiseasedYellow, 0)
            evt.StatusText("Diseased!")
        end
        evt.GiveItem(1, ItemType.Armor_)
    elseif randomStep == 6 then
        if not IsAtLeast(PerceptionSkill, 1) then
            SetValue(DiseasedYellow, 0)
            evt.StatusText("Nothing Here")
        end
        evt.GiveItem(2, ItemType.Armor_)
    elseif randomStep == 11 then
        if not IsAtLeast(PerceptionSkill, 1) then
            SetValue(DiseasedRed, 0)
            evt.StatusText("Poisoned!")
        end
        evt.GiveItem(3, ItemType.Armor_)
    end
    evt.ChangeEvent(284)
end)

RegisterGlobalEvent(282, "Trash Heap", function()
    local randomStep = PickRandomOption(282, 1, {1, 6, 11})
    if randomStep == 1 then
        if not IsAtLeast(PerceptionSkill, 1) then
            SetValue(DiseasedYellow, 0)
            evt.StatusText("Diseased!")
        end
        evt.GiveItem(1, ItemType.Weapon_)
    elseif randomStep == 6 then
        if not IsAtLeast(PerceptionSkill, 1) then
            SetValue(DiseasedYellow, 0)
            evt.StatusText("Nothing Here")
        end
        evt.GiveItem(2, ItemType.Weapon_)
    elseif randomStep == 11 then
        if not IsAtLeast(PerceptionSkill, 1) then
            SetValue(DiseasedRed, 0)
            evt.StatusText("Poisoned!")
        end
        evt.GiveItem(3, ItemType.Weapon_)
    end
    evt.ChangeEvent(284)
end)

RegisterGlobalEvent(283, "Trash Heap", function()
    local randomStep = PickRandomOption(283, 1, {1, 6, 11})
    if randomStep == 1 then
        if not IsAtLeast(PerceptionSkill, 1) then
            SetValue(DiseasedYellow, 0)
            evt.StatusText("Diseased!")
        end
        evt.GiveItem(1, ItemType.Misc)
    elseif randomStep == 6 then
        if not IsAtLeast(PerceptionSkill, 1) then
            SetValue(DiseasedYellow, 0)
            evt.StatusText("Nothing Here")
        end
        evt.GiveItem(2, ItemType.Misc)
    elseif randomStep == 11 then
        if not IsAtLeast(PerceptionSkill, 1) then
            SetValue(DiseasedRed, 0)
            evt.StatusText("Poisoned!")
        end
        evt.GiveItem(3, ItemType.Misc)
    end
    evt.ChangeEvent(284)
end)

RegisterGlobalEvent(284, "Trash Heap", function()
    local randomStep = PickRandomOption(284, 1, {1, 5})
if randomStep == 1 then
        if not IsAtLeast(PerceptionSkill, 1) then
            SetValue(DiseasedYellow, 0)
            evt.StatusText("Diseased!")
            return
        end
        evt.StatusText("Nothing Here")
elseif randomStep == 5 then
        evt.StatusText("Nothing Here")
    end
end)

RegisterGlobalEvent(285, "Camp Fire", function()
    local randomStep = PickRandomOption(285, 1, {1, 4, 7})
if randomStep == 1 then
        AddValue(Food, 3)
        evt.ChangeEvent(0)
        return
elseif randomStep == 4 then
        AddValue(Food, 2)
        evt.ChangeEvent(0)
        return
elseif randomStep == 7 then
        AddValue(Food, 1)
        evt.ChangeEvent(0)
        return
    end
end)

RegisterGlobalEvent(286, "Camp Fire", function()
    local randomStep = PickRandomOption(286, 1, {1, 4, 7})
if randomStep == 1 then
        AddValue(Food, 4)
        evt.ChangeEvent(0)
        return
elseif randomStep == 4 then
        AddValue(Food, 3)
        evt.ChangeEvent(0)
        return
elseif randomStep == 7 then
        AddValue(Food, 2)
        evt.ChangeEvent(0)
        return
    end
end)

RegisterGlobalEvent(287, "Food Bowl", function()
    AddValue(InventoryItem(655), 655) -- Green Apple
    evt.ChangeEvent(0)
end)

RegisterGlobalEvent(288, "Empty Cask", function()
    evt.StatusText("Empty Cask")
end)

RegisterGlobalEvent(289, "Cask", function()
    local randomStep = PickRandomOption(289, 1, {1, 1, 1, 8, 8, 8})
    if randomStep == 1 then
        local randomStep = PickRandomOption(289, 2, {2, 2, 2, 5, 5, 5})
        if randomStep == 2 then
            SetValue(PoisonedYellow, 0)
            evt.StatusText("Poisoned!")
        elseif randomStep == 5 then
            SetValue(PoisonedGreen, 0)
            evt.StatusText("Drunk!")
        end
    elseif randomStep == 8 then
        local randomStep = PickRandomOption(289, 9, {9, 9, 11, 11, 13, 15})
        if randomStep == 9 then
            AddValue(InventoryItem(202), 202) -- Phial of Gog Blood
        elseif randomStep == 11 then
            AddValue(InventoryItem(210), 210) -- Poppy Pod
        elseif randomStep == 13 then
            AddValue(InventoryItem(212), 212) -- Sulfur
        elseif randomStep == 15 then
            AddValue(InventoryItem(218), 218) -- Mercury
        end
    end
    evt.ChangeEvent(288)
end)

RegisterGlobalEvent(290, "Yellow Fever", function()
    if IsQBitSet(QBit(108)) then -- Yellow Fever epidemic cured!
        evt.SimpleMessage("The Yellow Fever epidemic is over!  Thank you for your help!")
        return
    elseif IsQBitSet(QBit(102)) then -- Delivered cure to hut 1
        evt.SimpleMessage("Thanks for the cure! Be sure to deliver scrolls to those who still suffer from the Yellow Fever.")
    else
        evt.ForPlayer(Players.All)
        if not HasItem(373) then -- Cure Disease
            evt.SimpleMessage("I am very sick, without a Cure Disease scroll I will surely perish from Yellow Fever!.")
            return
        end
        RemoveItem(373) -- Cure Disease
        SetQBit(QBit(102)) -- Delivered cure to hut 1
        evt.ForPlayer(Players.All)
        AddValue(Experience, 250)
        if IsQBitSet(QBit(102)) then -- Delivered cure to hut 1
            if IsQBitSet(QBit(103)) then -- Delivered cure to hut 2
                if IsQBitSet(QBit(104)) then -- Delivered cure to hut 3
                    if IsQBitSet(QBit(105)) then -- Delivered cure to hut 4
                        if IsQBitSet(QBit(106)) then -- Delivered cure to hut 5
                            if IsQBitSet(QBit(107)) then -- Delivered cure to hut 6
                                evt.ForPlayer(Players.All)
                                AddValue(Experience, 1500)
                                evt.SimpleMessage("The Yellow Fever epidemic is over!  Thank you for your help!")
                                SetQBit(QBit(108)) -- Yellow Fever epidemic cured!
                                return
                            end
                        end
                    end
                end
            end
        end
        evt.SimpleMessage("Thanks for the cure, but others in the area are still sick!  Be sure to deliver the cure to them as well!")
    end
    return
end)
RegisterCanShowTopic(290, function()
    evt._BeginCanShowTopic(290)
    local visible = true
    if IsQBitSet(QBit(101)) then -- Deliver Cure Disease Scrolls to the six huts on the outer Dagger Wound Islands. Return to Aislen on Dagger Wound Island.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(291, "Yellow Fever", function()
    if IsQBitSet(QBit(108)) then -- Yellow Fever epidemic cured!
        evt.SimpleMessage("The Yellow Fever epidemic is over!  Thank you for your help!")
        return
    elseif IsQBitSet(QBit(103)) then -- Delivered cure to hut 2
        evt.SimpleMessage("Thanks for the cure! Be sure to deliver scrolls to those who still suffer from the Yellow Fever.")
    else
        evt.ForPlayer(Players.All)
        if not HasItem(373) then -- Cure Disease
            evt.SimpleMessage("I am very sick, without a Cure Disease scroll I will surely perish from Yellow Fever!.")
            return
        end
        RemoveItem(373) -- Cure Disease
        SetQBit(QBit(103)) -- Delivered cure to hut 2
        evt.ForPlayer(Players.All)
        AddValue(Experience, 250)
        if IsQBitSet(QBit(103)) then -- Delivered cure to hut 2
            if IsQBitSet(QBit(102)) then -- Delivered cure to hut 1
                if IsQBitSet(QBit(104)) then -- Delivered cure to hut 3
                    if IsQBitSet(QBit(105)) then -- Delivered cure to hut 4
                        if IsQBitSet(QBit(106)) then -- Delivered cure to hut 5
                            if IsQBitSet(QBit(107)) then -- Delivered cure to hut 6
                                evt.ForPlayer(Players.All)
                                AddValue(Experience, 1500)
                                evt.SimpleMessage("The Yellow Fever epidemic is over!  Thank you for your help!")
                                SetQBit(QBit(108)) -- Yellow Fever epidemic cured!
                                return
                            end
                        end
                    end
                end
            end
        end
        evt.SimpleMessage("Thanks for the cure, but others in the area are still sick!  Be sure to deliver the cure to them as well!")
    end
    return
end)
RegisterCanShowTopic(291, function()
    evt._BeginCanShowTopic(291)
    local visible = true
    if IsQBitSet(QBit(101)) then -- Deliver Cure Disease Scrolls to the six huts on the outer Dagger Wound Islands. Return to Aislen on Dagger Wound Island.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(292, "Yellow Fever", function()
    if IsQBitSet(QBit(108)) then -- Yellow Fever epidemic cured!
        evt.SimpleMessage("The Yellow Fever epidemic is over!  Thank you for your help!")
        return
    elseif IsQBitSet(QBit(104)) then -- Delivered cure to hut 3
        evt.SimpleMessage("Thanks for the cure! Be sure to deliver scrolls to those who still suffer from the Yellow Fever.")
    else
        evt.ForPlayer(Players.All)
        if not HasItem(373) then -- Cure Disease
            evt.SimpleMessage("I am very sick, without a Cure Disease scroll I will surely perish from Yellow Fever!.")
            return
        end
        RemoveItem(373) -- Cure Disease
        SetQBit(QBit(104)) -- Delivered cure to hut 3
        evt.ForPlayer(Players.All)
        AddValue(Experience, 250)
        if IsQBitSet(QBit(104)) then -- Delivered cure to hut 3
            if IsQBitSet(QBit(102)) then -- Delivered cure to hut 1
                if IsQBitSet(QBit(103)) then -- Delivered cure to hut 2
                    if IsQBitSet(QBit(105)) then -- Delivered cure to hut 4
                        if IsQBitSet(QBit(106)) then -- Delivered cure to hut 5
                            if IsQBitSet(QBit(107)) then -- Delivered cure to hut 6
                                evt.ForPlayer(Players.All)
                                AddValue(Experience, 1500)
                                evt.SimpleMessage("The Yellow Fever epidemic is over!  Thank you for your help!")
                                SetQBit(QBit(108)) -- Yellow Fever epidemic cured!
                                return
                            end
                        end
                    end
                end
            end
        end
        evt.SimpleMessage("Thanks for the cure, but others in the area are still sick!  Be sure to deliver the cure to them as well!")
    end
    return
end)
RegisterCanShowTopic(292, function()
    evt._BeginCanShowTopic(292)
    local visible = true
    if IsQBitSet(QBit(101)) then -- Deliver Cure Disease Scrolls to the six huts on the outer Dagger Wound Islands. Return to Aislen on Dagger Wound Island.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(293, "Yellow Fever", function()
    if IsQBitSet(QBit(108)) then -- Yellow Fever epidemic cured!
        evt.SimpleMessage("The Yellow Fever epidemic is over!  Thank you for your help!")
        return
    elseif IsQBitSet(QBit(105)) then -- Delivered cure to hut 4
        evt.SimpleMessage("Thanks for the cure! Be sure to deliver scrolls to those who still suffer from the Yellow Fever.")
    else
        evt.ForPlayer(Players.All)
        if not HasItem(373) then -- Cure Disease
            evt.SimpleMessage("I am very sick, without a Cure Disease scroll I will surely perish from Yellow Fever!.")
            return
        end
        RemoveItem(373) -- Cure Disease
        SetQBit(QBit(105)) -- Delivered cure to hut 4
        evt.ForPlayer(Players.All)
        AddValue(Experience, 250)
        if IsQBitSet(QBit(105)) then -- Delivered cure to hut 4
            if IsQBitSet(QBit(102)) then -- Delivered cure to hut 1
                if IsQBitSet(QBit(103)) then -- Delivered cure to hut 2
                    if IsQBitSet(QBit(104)) then -- Delivered cure to hut 3
                        if IsQBitSet(QBit(106)) then -- Delivered cure to hut 5
                            if IsQBitSet(QBit(107)) then -- Delivered cure to hut 6
                                evt.ForPlayer(Players.All)
                                AddValue(Experience, 1500)
                                evt.SimpleMessage("The Yellow Fever epidemic is over!  Thank you for your help!")
                                SetQBit(QBit(108)) -- Yellow Fever epidemic cured!
                                return
                            end
                        end
                    end
                end
            end
        end
        evt.SimpleMessage("Thanks for the cure, but others in the area are still sick!  Be sure to deliver the cure to them as well!")
    end
    return
end)
RegisterCanShowTopic(293, function()
    evt._BeginCanShowTopic(293)
    local visible = true
    if IsQBitSet(QBit(101)) then -- Deliver Cure Disease Scrolls to the six huts on the outer Dagger Wound Islands. Return to Aislen on Dagger Wound Island.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(294, "Yellow Fever", function()
    if IsQBitSet(QBit(108)) then -- Yellow Fever epidemic cured!
        evt.SimpleMessage("The Yellow Fever epidemic is over!  Thank you for your help!")
        return
    elseif IsQBitSet(QBit(106)) then -- Delivered cure to hut 5
        evt.SimpleMessage("Thanks for the cure! Be sure to deliver scrolls to those who still suffer from the Yellow Fever.")
    else
        evt.ForPlayer(Players.All)
        if not HasItem(373) then -- Cure Disease
            evt.SimpleMessage("I am very sick, without a Cure Disease scroll I will surely perish from Yellow Fever!.")
            return
        end
        RemoveItem(373) -- Cure Disease
        SetQBit(QBit(106)) -- Delivered cure to hut 5
        evt.ForPlayer(Players.All)
        AddValue(Experience, 250)
        if IsQBitSet(QBit(106)) then -- Delivered cure to hut 5
            if IsQBitSet(QBit(102)) then -- Delivered cure to hut 1
                if IsQBitSet(QBit(103)) then -- Delivered cure to hut 2
                    if IsQBitSet(QBit(104)) then -- Delivered cure to hut 3
                        if IsQBitSet(QBit(105)) then -- Delivered cure to hut 4
                            if IsQBitSet(QBit(107)) then -- Delivered cure to hut 6
                                evt.ForPlayer(Players.All)
                                AddValue(Experience, 1500)
                                evt.SimpleMessage("The Yellow Fever epidemic is over!  Thank you for your help!")
                                SetQBit(QBit(108)) -- Yellow Fever epidemic cured!
                                return
                            end
                        end
                    end
                end
            end
        end
        evt.SimpleMessage("Thanks for the cure, but others in the area are still sick!  Be sure to deliver the cure to them as well!")
    end
    return
end)
RegisterCanShowTopic(294, function()
    evt._BeginCanShowTopic(294)
    local visible = true
    if IsQBitSet(QBit(101)) then -- Deliver Cure Disease Scrolls to the six huts on the outer Dagger Wound Islands. Return to Aislen on Dagger Wound Island.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(295, "Yellow Fever", function()
    if IsQBitSet(QBit(108)) then -- Yellow Fever epidemic cured!
        evt.SimpleMessage("The Yellow Fever epidemic is over!  Thank you for your help!")
        return
    elseif IsQBitSet(QBit(107)) then -- Delivered cure to hut 6
        evt.SimpleMessage("Thanks for the cure! Be sure to deliver scrolls to those who still suffer from the Yellow Fever.")
    else
        evt.ForPlayer(Players.All)
        if not HasItem(373) then -- Cure Disease
            evt.SimpleMessage("I am very sick, without a Cure Disease scroll I will surely perish from Yellow Fever!.")
            return
        end
        RemoveItem(373) -- Cure Disease
        SetQBit(QBit(107)) -- Delivered cure to hut 6
        evt.ForPlayer(Players.All)
        AddValue(Experience, 250)
        if IsQBitSet(QBit(107)) then -- Delivered cure to hut 6
            if IsQBitSet(QBit(102)) then -- Delivered cure to hut 1
                if IsQBitSet(QBit(103)) then -- Delivered cure to hut 2
                    if IsQBitSet(QBit(104)) then -- Delivered cure to hut 3
                        if IsQBitSet(QBit(105)) then -- Delivered cure to hut 4
                            if IsQBitSet(QBit(106)) then -- Delivered cure to hut 5
                                evt.ForPlayer(Players.All)
                                AddValue(Experience, 1500)
                                evt.SimpleMessage("The Yellow Fever epidemic is over!  Thank you for your help!")
                                SetQBit(QBit(108)) -- Yellow Fever epidemic cured!
                                return
                            end
                        end
                    end
                end
            end
        end
        evt.SimpleMessage("Thanks for the cure, but others in the area are still sick!  Be sure to deliver the cure to them as well!")
    end
    return
end)
RegisterCanShowTopic(295, function()
    evt._BeginCanShowTopic(295)
    local visible = true
    if IsQBitSet(QBit(101)) then -- Deliver Cure Disease Scrolls to the six huts on the outer Dagger Wound Islands. Return to Aislen on Dagger Wound Island.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(296, "Rothnax", function()
    evt.SimpleMessage("My brother Rohtnax lives!  And you have repaired the Portals of Stone?  I must return home to him, so that we can plan our family's survival!")
    SetQBit(QBit(138)) -- Found Isthric the Tongue
    evt.MoveNPC(90, 225) -- Isthric the Tongue -> Rohtnax's House
    evt.SetNPCTopic(90, 0, 297) -- Isthric the Tongue topic 0: Thank you again!
    return
end)

RegisterGlobalEvent(297, "Thank you again!", function()
    return
end)
RegisterCanShowTopic(297, function()
    evt._BeginCanShowTopic(297)
    local visible = true
    if IsQBitSet(QBit(134)) then -- Gave Gem of Restoration to Blazen Stormlance
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(298, "Report!", function()
    evt.SimpleMessage("You're new aren't you?  Tell Arion Hunter that I expect more of his rabble than the likes of you!  Give me the reports and leave my sight!  You make me sick!")
    ClearQBit(QBit(117)) -- Deliver fake report to the Dread Pirate Stanley in the Pirate's Rest Tavern on the Island of Regna.
    evt.ForPlayer(Players.All)
    RemoveItem(602) -- False Report
    SetAward(Award(61)) -- Delivered False Report to the Dread Pirate Stanley for Arion Hunter.
    ClearQBit(QBit(282)) -- False Report - I lost it!
    AddValue(Experience, 20000)
    evt.ForPlayer(Players.Member0)
    AddValue(Gold, 15000)
    evt.SetNPCTopic(296, 0, 0) -- Dread Pirate Stanley topic 0 cleared
    evt.MoveNPC(296, 0) -- Dread Pirate Stanley -> removed
    return
end)
RegisterCanShowTopic(298, function()
    evt._BeginCanShowTopic(298)
    local visible = true
    if IsQBitSet(QBit(117)) then -- Deliver fake report to the Dread Pirate Stanley in the Pirate's Rest Tavern on the Island of Regna.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(299, "Fate of Jadame", function()
    if not IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
        evt.SimpleMessage("Who knows the fate of Jadame now.  Perhaps you will find a way to save us from destruction?")
        return
    end
    evt.SimpleMessage("Jadame owes you a great debt!  You have saved the entire world from total destruction!")
    return
end)

RegisterGlobalEvent(417, "Puddle Thain", function()
    evt.SimpleMessage("Puddle Thain, is a most promising student.  If you seek Expert instruction in the uses of the Staff, you can find him in the city of Ravenshore.")
    SetAutonote(128) -- You may receive Expert Staff instruction from Puddle Thain in the city of Ravenshore.
    return
end)

RegisterGlobalEvent(418, "Celia Stone", function()
    evt.SimpleMessage("Celia Stone, Master of the Staff, dwells in Troll village of Rust in the Ironsand Desert.  She can instruct you to Mastery of the Staff is that is what you desire.")
    SetAutonote(129) -- Master Staff is taught by Celia Stone located in the village of Rust. Rust is in the Ironsand Desert.
    return
end)

RegisterGlobalEvent(419, "Tristen Stillwater", function()
    evt.SimpleMessage("Grand Master Tristen Stillwater, instructs all students of the Staff.  Only he can help you in attaining Grand Mastery of this fine weapon.  Seek him out in the city of Twilight at the base of the Shadowspire.")
    SetAutonote(130) -- The Grand Master of Staff, Tristen Stillwater is located in the Shadowspire city of Twilight.
    return
end)

RegisterGlobalEvent(420, "Aerie Luodrin", function()
    evt.SimpleMessage("Aerie Luodrin currently dwells in Ravenshore.  She is a most dedicated student of the uses of the Sword and can instruct you to and Expert skill level with the weapon.")
    SetAutonote(131) -- You may receive Expert Sword training from Aerie Luodrin in the city of Ravenshore.
    return
end)

RegisterGlobalEvent(421, "Jaycin Cardron", function()
    evt.SimpleMessage("Unfortunately Jaycin Cardron, Master of the Sword, felt that his skills would be more, shall we say, \"profitable taught\" to the Dragon Hunter's of Garrote Gorge.  If you seek Master skill level with the Sword, you will have to go to him at the Garrote Gorge Dragon Hunter Camp.")
    SetAutonote(132) -- Master Sword is taught by Jaycin Cardron. You can find her in the Garrote Gorge Dragon Hunter's Camp.
    return
end)

RegisterGlobalEvent(422, "Miyon Dragontracker", function()
    evt.SimpleMessage("Miyon Dragontracker, Grand Master of the Sword, has joined the knight, Charles Quixote in his quest to exterminate the Dragons of Garrote Gorge.  You can find Miyon at the Dragon Hunter's Fort.")
    SetAutonote(133) -- The Grand Master of Sword, Miyon Dragontracker can be found on the island of Regna.
    return
end)

RegisterGlobalEvent(423, "Lori Vespers", function()
    evt.SimpleMessage("The Expert instructor of the Dagger, Lori Vespers, lives in the Dark Elf city of Alvar.  Seek her out there.")
    SetAutonote(134) -- The Expert Dagger instructor, Lori Vespers, lives in the Dark Elf city of Alvar.
    return
end)

RegisterGlobalEvent(424, "Jobber", function()
    evt.SimpleMessage("Master Jobber can instruct students of the Dagger to Mastery.  He lives in the city of Ravenshore.")
    SetAutonote(135) -- Master Jobber teaches Master Dagger. He lives in the city of Ravenshore.
    return
end)

RegisterGlobalEvent(425, "Karla Nirses", function()
    evt.SimpleMessage("Karla Nirses, the Grand Master of the Dagger trains all Regnan Pirates in the uses of the Dagger.  She dwells with them on the Island of Regna as they pay her well.")
    SetAutonote(136) -- Karla Nirses, the Grand Master Dagger teacher, can be found on Regna Island.
    return
end)

RegisterGlobalEvent(426, "Herald Foestryke", function()
    evt.SimpleMessage("Herald Foestryke, one of Charles Quixote's finest knights, is the Expert teacher of the skills of the Axe.  He can be found at the Dragon Hunter's Camp in Garrote Gorge.")
    SetAutonote(137) -- Herald Foestryke teaches Expert Axe in the Dragon Hunter's Camp located in Garrote Gorge.
    return
end)

RegisterGlobalEvent(427, "Jasp Hunter", function()
    evt.SimpleMessage("Jasp Hunter is the Master instructor of the axe.  He can teach you the skills that will lead to Mastery of the axe.  His home is in the seaside city of Ravenshore.")
    SetAutonote(138) -- Jasp Hunter is the Master Axe instructor. His home is in the seaside city of Ravenshore.
    return
end)

RegisterGlobalEvent(428, "Garic Senjac", function()
    evt.SimpleMessage("Grand Master Garic Senjac, is the Grand Master teacher of the ways of the Axe.  His home is in Balthazar Lair in the Ravage Roaming region.")
    SetAutonote(139) -- Grand Master Garic Senjac, the Grand Master Axe teacher makes his home in Balthazar Lair located in Ravage Roaming.
    return
end)

RegisterGlobalEvent(429, "Matric Townsaver", function()
    evt.SimpleMessage("Matric Townsaver defended the city of Ravenshore against many Regnan Pirate raids.  His skill and instruction of the uses of the spear allowed the townsfolk to push the Pirates back. He can instruct you to Expert skill level with the spear.")
    SetAutonote(140) -- Matric Townsaver teaches Expert Spear from his home in Ravenshore.
    return
end)

RegisterGlobalEvent(430, "Ashandra Withersmythe", function()
    evt.SimpleMessage("Ashandra Withersmythe is the Master teacher of the Spear.  Her instruction of the ways of the Spear will lead you to Mastery of the weapon.  She lives in the merchant city of Alvar.")
    SetAutonote(141) -- Ashandra Withersmythe is the Master teacher of the Spear. She lives in the merchant city of Alvar.
    return
end)

RegisterGlobalEvent(431, "Yarrow", function()
    evt.SimpleMessage("Yarrow is the Grand Master of the Spear.  Her keen eye and stalking ability have aided her in attaining this level of skill.  She uses the Spear to stalk the poisonous couatl of the jungles of the Dagger Wound Islands.")
    SetAutonote(142) -- Yarrow is the Grand Master of the Spear. You can find her on the Dagger Wound Islands.
    return
end)

RegisterGlobalEvent(432, "Shivan Keeneye", function()
    evt.SimpleMessage("Shivan Keeneye is an Expert shot with the Bow.  Her teachings can lead you to an Expert skill level with this ranged weapon.  She lives in the village of Blood Drop on the Dagger Wound Islands.")
    SetAutonote(143) -- Shivan Keeneye, the Expert Bow teacher lives in the village of Blood Drop on the Dagger Wound Islands.
    return
end)

RegisterGlobalEvent(433, "Oberic Nosewort", function()
    evt.SimpleMessage("Master Oberic Nosewort teaches students of the bow in his home in Ravenshore.  If you seek Mastery of this weapon you must seek him out there.")
    SetAutonote(144) -- Master Bow teacher Oberic Nosewort lives in Ravenshore city
    return
end)

RegisterGlobalEvent(434, "Solis", function()
    evt.SimpleMessage("Solis, Grand Master of the Bow, lives in the Dark Elf city of Alvar.  She can teach you Grand Mastery of the Bow.")
    SetAutonote(145) -- Solis, Grand Master of the Bow, lives in the Dark Elf city of Alvar.
    return
end)

RegisterGlobalEvent(435, "Lisha Sourbrow", function()
    evt.SimpleMessage("Lisha Sourbrow teaches Expert uses of the Mace from her home in Ravenshore.")
    SetAutonote(146) -- Lisha Sourbrow teaches Expert Mace from her home in Ravenshore.
    return
end)

RegisterGlobalEvent(436, "Robert Morningstar", function()
    evt.SimpleMessage("Robert Morningstar, teaches Mastery of the Mace to the knights in Garrote Gorge.")
    SetAutonote(147) -- Master Mace teacher, Robert Morningstar, trains the knights of the Garrote Gorge Dragon Hunter's Camp.
    return
end)

RegisterGlobalEvent(437, "Brother Hearthsworn", function()
    evt.SimpleMessage("Brother Hearthsworn, the Grand Master of the Mace, retired to the peace of the Ironsand Desert, seeking tranquility among the dunes of that region.  His home is in the village of Rust.")
    SetAutonote(148) -- Brother Hearthsworn, the Grand Master Mace teacher, can be found in the village of Rust located in the Ironsand Desert.
    return
end)

RegisterGlobalEvent(438, "Qillain Moore", function()
    evt.SimpleMessage("Qillain Moore used to serve the knight, Charles Quixote, but disagreed with his crusade to slay all the Dragons in the Garrote Gorge area. Moore still teaches Expert uses of the Shield from his home in the city of Alvar.")
    SetAutonote(152) -- Expert Shield teacher, Qillain Moore, lives in the the city of Alvar.
    return
end)

RegisterGlobalEvent(439, "Sheldon Nightwood", function()
    evt.SimpleMessage("Sheldon Nightwood lives in the city of Twilight, beneath the Necromancers' Guild on the Shadowspire.  She can teach you Mastery of the Shield.")
    SetAutonote(153) -- Master Shield teacher, Sheldon Nightwood lives in the Shadowspire city of Twilight.
    return
end)

RegisterGlobalEvent(440, "Peryn Reaverston", function()
    evt.SimpleMessage("The knight, Peryn Reaverston, holds the title of Grand Master of the Shield.  He is currently in service to Charles Quixote and teaches knights in the proper uses of the shield.  Search him out in the Dragon Hunter's Camp in Garrote Gorge.")
    SetAutonote(154) -- Peryn Reaverston, Grand Master Shield instructor, lives in the Dragon Hunter's Camp in Garrote Gorge.
    return
end)

RegisterGlobalEvent(441, "Thadin", function()
    evt.SimpleMessage("The Lizardman Thadin is the Expert instructor of the use of Leather armor.  His instruction will give you an Expert skill level with this armor.  You can find him on the Island of Dagger Wound.")
    SetAutonote(155) -- Thadin is the Expert Leather instructor. You can find him on the Island of Dagger Wound.
    return
end)

RegisterGlobalEvent(442, "Shamus Hollyfield", function()
    evt.SimpleMessage("Master Shamus Hollyfield dwells in the Minotaur city, Balthazar Lair, which is located in the Ravage Roaming region.  He can teach you Mastery of Leather armor.")
    SetAutonote(156) -- Master Leather instructor Shamus Hollyfield dwells in the Minotaur city, Balthazar Lair, which is located in the Ravage Roaming region.
    return
end)

RegisterGlobalEvent(443, "Medwari Elmsmire", function()
    evt.SimpleMessage("Medwari Elmsmire makes the finest Leather armor in the realm.  She also holds the title of Grand Master of Leather Armor and can instruct you at her home in the village of Rust in the Ironsand Desert.")
    SetAutonote(157) -- Medwari Elmsmire, the Grand Master of Leather makes her home in the village of Rust in the Ironsand Desert.
    return
end)

RegisterGlobalEvent(444, "Tobren Forgewright", function()
    evt.SimpleMessage("Tobren Forgewright assisted the city of Ravenshore in the First Pirate War.  Her forge glowed for four weeks straight as she made chain armor for the defenders of Ravenshore.  She still teaches Expert use of the armor from her home in the seaside port of Ravenshore.")
    SetAutonote(158) -- Tobren Forgewright the Expert Chain teacher lives in the seaside port of Ravenshore.
    return
end)

RegisterGlobalEvent(445, "Halian Eversmyle", function()
    evt.SimpleMessage("Halian Eversmyle learned all the skills he could from the Grand Master of Chain armor and then fled to the city of Alvar where he teaches Mastery of this armor to the Merchants of Alvar.  He will instruct you to Mastery as well.")
    SetAutonote(159) -- Master Chain instructor, Halian Eversmyle, can be found in the city of Alvar.
    return
end)

RegisterGlobalEvent(446, "Seline Burnkindle", function()
    evt.SimpleMessage("Grand Master Seline Burnkindle teaches ways of using chain armor to its greatest advantage.  She lives among the Pirates of Regna.")
    SetAutonote(160) -- Grand Master of Chain, Seline Burnkindle, teaches from her home on the island of Renga.
    return
end)

RegisterGlobalEvent(447, "Bone", function()
    evt.SimpleMessage("Bone teaches the Expert skills of Plate armor from his hut on Dagger Wound Island.")
    SetAutonote(161) -- Bone teaches Expert Plate armor use from his hut on the Dagger Wound Islands.
    return
end)

RegisterGlobalEvent(448, "Botham", function()
    evt.SimpleMessage("Master Botham was one of the finest warriors in the First Pirate War.  Ravenshore owes him a debt of gratitude.  Botham and his fellow swordsman led the charge against the first wave of Regnans.  Their Plate armor deflected all but the most serious blows.  He still teaches Mastery of Plate armor from his home.")
    SetAutonote(162) -- The Master Plate instructor, Botham, lives in the city of Ravenshore.
    return
end)

RegisterGlobalEvent(449, "Seth Ironfist", function()
    evt.SimpleMessage("Seth Ironfist, Grand Master of Plate Armor, is the true force behind Charles Quixote's crusade against the Dragons of Garrote Gorge.  Without his instruction in the use of Plate armor, Quixote's knights would be mere fodder before the wrath Redreaver's Dragons.")
    SetAutonote(163) -- Seth Ironfist, Grand Master of Plate Armor teaches in the Dragon Hunter's Camp in Garrote Gorge.
    return
end)

RegisterGlobalEvent(450, "Taren Temper", function()
    evt.SimpleMessage("Taren Temper, fled Erathia to make a new life for himself among those who know nothing of the Temper history.  He teaches Expert skills in Fire Magic from his home in Ravenshore.")
    SetAutonote(164) -- Taren Temper teaches Expert Fire Magic from his home in Ravenshore.
    return
end)

RegisterGlobalEvent(451, "Solomon Steele", function()
    evt.SimpleMessage("Solomon Steele, Master of Fire, lives in the tranquil city of Alvar.  He can teach you Mastery of Fire Magic.")
    SetAutonote(165) -- Solomon Steele, Master instructor of Fire Magic, lives in the tranquil city of Alvar.
    return
end)

RegisterGlobalEvent(452, "Burn", function()
    evt.SimpleMessage("Burn, Grand Master of Fire dwells in the oppressive heat of the Plane of Fire.  Perhaps the Gate of Fire that has appeared in the Ironsand Desert will lead you to him.  He can instruct you in Grand Mastery of Fire Magic.  ")
    SetAutonote(166) -- Burn, Grand Master of Fire Magic dwells in the oppressive heat of the Plane of Fire.
    return
end)

RegisterGlobalEvent(453, "Reshie", function()
    evt.SimpleMessage("Reshie teaches the Expert skill of Air Magic from his home on the Dagger Wound Islands.")
    SetAutonote(167) -- Reshie teaches the Expert skill of Air Magic from his home on the Dagger Wound Islands.
    return
end)

RegisterGlobalEvent(454, "Hollis Stormeye", function()
    evt.SimpleMessage("Hollis Stormeye, Master of Air, made her home in Balthazar Lair, home of the Minotaurs.  ")
    SetAutonote(168) -- Hollis Stormeye, Master Air Magic teacher, makes her home in Balthazar Lair located in Ravage Roaming.
    return
end)

RegisterGlobalEvent(455, "Cloud Nedlon", function()
    evt.SimpleMessage("Cloud Nedlon sought to make a deal with the Lords of Air.  He left to find a way into the Plane of Air, where he thought he would learn all that remained unclear to him about the ways of Air Magic.  You will have to travel to the Plane of Air to see if he was successful.")
    SetAutonote(169) -- Cloud Nedlon, the Grand Master of Air may be found on the Plane of Air.
    return
end)

RegisterGlobalEvent(456, "Ulbrecht Pederton", function()
    evt.SimpleMessage("Ulbrecht Pederton single handedly stopped the Second Pirate War.  He charged down the beach to come to Ravenshore's defense as the pirates began to land.  He manipulated the sea itself and forced the Regnan fleet back into the ocean.  Unfortunately this effort cost him the ability to use magic altogether.  He still, however, teaches the knowledge of Expert Water Magic.  He lives in Ravenshore to this day.")
    SetAutonote(170) -- Ulbrecht Pederton, Expert teacher of Water Magic lives in Ravenshore city.
    return
end)

RegisterGlobalEvent(457, "Gregory Mist", function()
    evt.SimpleMessage("Gregory Mist, Master of Water, makes his home in the village of Rust in the Ironsand Desert.  He claims to have a plan to use his magic to change the hot desert into a verdant green plain.  If he has the time, he can teach you Mastery of Water Magic.")
    SetAutonote(171) -- Gregory Mist, Master teacher of Water Magic, makes his home in the village of Rust in the Ironsand Desert.
    return
end)

RegisterGlobalEvent(458, "Black Current", function()
    evt.SimpleMessage("Black Current was once a powerful mage in this region.  Her ambition for power outgrew her caution and she attempted to conquer the Plane of Water.  She summoned a gate to the plane and stepped through.  She was never heard from again.  She was the Grand Master of Water Magic.  If she still lives you may find her in the Plane of Water.")
    SetAutonote(172) -- Black Current, the Grand Master teacher of Water Magic may be found on the Plane of Water.
    return
end)

RegisterGlobalEvent(459, "Ostrin Grivic", function()
    evt.SimpleMessage("Ostrin Grivic, Expert instructor of Earth Magic, lives in the village of Blood Drop on the Dagger Wound Islands.")
    SetAutonote(173) -- Ostrin Grivic, Expert instructor of Earth Magic, lives in the village of Blood Drop on the Dagger Wound Islands.
    return
end)

RegisterGlobalEvent(460, "Dorothy Sablewood", function()
    evt.SimpleMessage("Earth Magic Master Dorothy Sablewood helped end the First Pirate War.  With the aid of an unknown Air Mage, she erected walls of clay to keep the Regnan Pirates from leaving their boats.  She now teaches her skills from her home in Alvar.")
    SetAutonote(174) -- The Master teacher of Earth Magic, Dorothy Sablewood, lives in the city of Alvar.
    return
end)

RegisterGlobalEvent(461, "Griven", function()
    evt.SimpleMessage("Grand Master Griven passed into the Plane of Earth after teaching his final lesson to Dorothy Sablewood.  Perhaps he lives there to this day.  Who knows what transpires in an elemental plane?")
    SetAutonote(175) -- The Grand Master instructor of Air Magic, Griven, may be found on the Plane of Air.
    return
end)

RegisterGlobalEvent(462, "Straton Hawthorne", function()
    evt.SimpleMessage("Straton Hawthorne can raise you to Expert level in the arts of Spirit Magic. He makes his home in the port city of Ravenshore.")
    SetAutonote(176) -- Straton Hawthorne can raise you to Expert level in the arts of Spirit Magic. He makes his home in the port city of Ravenshore.
    return
end)

RegisterGlobalEvent(463, "Bethold Kern", function()
    evt.SimpleMessage("Master Bethold Kern, serves the knight Charles Quixote in his crusade against the Dragons of the Garrote Gorge region.  Search him out there at the Dragon Hunter's Camp.  If you are lucky, he will have time to instruct you in Mastery of Spirit Magic.")
    SetAutonote(177) -- Spirit Magic Master instructor, Bethold Kern, can be found in the Garrote Gorge Dragon Hunter's Camp.
    return
end)

RegisterGlobalEvent(464, "Lasiter Ravensight", function()
    evt.SimpleMessage("Lasiter Ravensight, is the Grand Master of Spirit Magic.  He lives in the Murmurwoods close to the Temple of the Sun, where he continues his studies in to the essence of Spirit.  He can raise your skill in Spirit Magic to Grand Mastery.")
    SetAutonote(178) -- Lasiter Ravensight, is the Grand Master teacher of Spirit Magic. He lives in the Murmurwoods close to the Temple of the Sun.
    return
end)

RegisterGlobalEvent(465, "Shane Krewlen", function()
    evt.SimpleMessage("Shane Krewlen, student of Mind Magic, can instruct you in the Expert skills of this arcane magic.  Seek him out in the Dark Elf city of Alvar.")
    SetAutonote(179) -- Shane Krewlen, Expert instructor of Mind Magic, lives in the Dark Elf city of Alvar.
    return
end)

RegisterGlobalEvent(466, "Barthine Lotts", function()
    evt.SimpleMessage("Barthine Lotts, Master of Mind Magic, dwells in the Minotaur city of Balthazar Lair in the Ravage Roaming region.  Through her instruction can gain Mastery of Mind Magic.")
    SetAutonote(180) -- Barthine Lotts, Master of Mind Magic, dwells in the Minotaur city of Balthazar Lair in the Ravage Roaming region.
    return
end)

RegisterGlobalEvent(467, "Gilad Dreamwright", function()
    evt.SimpleMessage("Gilad Dreamwright, Grand Master of Mind Magic, has joined many other Grand Masters of Magic in the Murmurwoods region.  Here they work with the Temple of the Sun to further their combined skills and knowledge.  Gilad can instruct you to Grand Master skill level in Mind Magic.")
    SetAutonote(181) -- Gilad Dreamwright, Grand Master of Mind Magic, lives in Murmurwoods near the Temple of the Sun.
    return
end)

RegisterGlobalEvent(468, "Zevah Poised", function()
    evt.SimpleMessage("Zevah Poised, Expert instructor of the arcane skills of Body Magic, lives with his people on the Islands of Dagger Wound in the Ifarine Sea.")
    SetAutonote(182) -- Zevah Poised, Expert instructor of Body Magic, lives with his people on the Islands of Dagger Wound.
    return
end)

RegisterGlobalEvent(469, "Tugor Arin", function()
    evt.SimpleMessage("Tugor Arin, Master of Body Magic, practices his healing skills in the service of the knight Charles Quixote in the Garrote Gorge region.  His skills in Body Magic are put to good use healing the unfortunate young knights who are wounded in the crusade against the Dragons of Garrote Gorge.")
    SetAutonote(183) -- Tugor Arin, Master of Body Magic can be found in the Garrote Gorge Dragon Hunter's Camp.
    return
end)

RegisterGlobalEvent(470, "Critias Snowtree", function()
    evt.SimpleMessage("Grand Master Critias Snowtree, dwells in the peace of the Murmurwoods forest away from the trials and troubles of the world.  Only he can instruct you in the ways of Body Magic and raise you to Grand Mastery of this arcane skill.")
    SetAutonote(184) -- Grand Master of Body Magic, Critias Snowtree, dwells in the Murmurwoods forest.
    return
end)

RegisterGlobalEvent(471, "Archibald Dawnsglow", function()
    evt.SimpleMessage("Archibald Dawnsglow, Expert instructor of Light Magic, practices his arts in the city of Ravenshore on the Ifarine Sea.  His parents gave his name not knowing that it was the same name as the leader of the Erathian Necromancers' Guild.  Archibald desires to have his own name made in the Light, not in the darkness of his namesake.")
    SetAutonote(185) -- Archibald Dawnsglow, Expert instructor of Light Magic, practices his arts in the city of Ravenshore.
    return
end)

RegisterGlobalEvent(472, "Lunius Dawnbringer", function()
    evt.SimpleMessage("Master Lunius Dawnbringer, dwells among the the Clerics of Murmurwoods.He can promote you to Master of Light Magic, if you can survive the dangers of the forest.")
    SetAutonote(186) -- Master Light Magic teacher, Lunius Dawnbringer, dwells near the Temple of the Sun in the Murmurwoods.
    return
end)

RegisterGlobalEvent(473, "Aldrin Cleareye", function()
    evt.SimpleMessage("Aldrin Cleareye, Grand Master of the Light, makes his home on the island of Regna.  He hopes to bring an end to the Pirates evil ways.  He can instruct you to Grand Masterey, if you survive the Pirates.")
    SetAutonote(187) -- Aldrin Cleareye, Grand Master of the Light, lives on the island of Regna.
    return
end)

RegisterGlobalEvent(474, "Patwin Darkenmore", function()
    evt.SimpleMessage("Patwin Darkenmore, Expert teacher of the ways of Dark Magic, lives among the Dark Elves of Alvar.  ")
    SetAutonote(188) -- Patwin Darkenmore, Expert teacher of the ways of Dark Magic, lives among the Dark Elves of Alvar.
    return
end)

RegisterGlobalEvent(475, "Carla Umberpool", function()
    evt.SimpleMessage("Dark Magic Master Carla Umberpool followed the travels of Sithicus Shadowrunner, Grand Master of the Dark, and makes her home with the Necromancers of Shadowspire.")
    SetAutonote(189) -- Dark Magic Master Carla Umberpool has a home in the village of Twilight at the base of the Shadowspire.
    return
end)

RegisterGlobalEvent(476, "Sithicus Shadowrunner", function()
    evt.SimpleMessage("Sithicus Shadowrunner, Grand Master of the art of Dark Magic, and has established a home on the Island of Regna.  Here the pirate captains get her blessing on the ships before a raid.  She can instruct you in Grand Mastery of Dark Magic.")
    SetAutonote(190) -- Sithicus Shadowrunner, the Grand Master Dark Magic instructor, lives on the island of Regna.
    return
end)

RegisterGlobalEvent(477, "Kyra Sparkmen", function()
    evt.SimpleMessage("Kyra Sparkmen, Expert teacher of the Identify Item skill, lives in the city of Alvar.  ")
    SetAutonote(200) -- Kyra Sparkmen, Expert teacher of the Identify Item skill, lives in the city of Alvar.
    return
end)

RegisterGlobalEvent(478, "Eithian", function()
    evt.SimpleMessage("Eithian, Master instructor of the Identify Item skill, serves the Merchants of Alvar, and currently lives on the Dagger Wound Islands. Many travelers bring their prizes to Eithian for identification.  He may have to time to instruct you to Mastery of this skill if you travel to him.")
    SetAutonote(201) -- Eithian, Master instructor of the Identify Item skill, lives on the Dagger Wound Islands.
    return
end)

RegisterGlobalEvent(479, "Elzbet Roggen", function()
    evt.SimpleMessage("Elzbet Roggen, Grand Master of the Identify Item skill, lives in the Shadowspire city of Twilight.  She can teach you what is needed to achieve Grand Mastery.")
    SetAutonote(202) -- Elzbet Roggen, Grand Master of the Identify Item skill, lives in the Shadowspire city of Twilight.
    return
end)

RegisterGlobalEvent(480, "Fishner Thomb", function()
    evt.SimpleMessage("Fishner Thomb, retired from service with the Merchants of Alvar and returned to his home Island of Dagger Wound in the Ifarine Sea.  Seek him out there for his teachings in the Expert way of being a Merchant.")
    SetAutonote(203) -- Fishner Thomb Expert Merchant instructor makes his home on the Islands of Dagger Wound.
    return
end)

RegisterGlobalEvent(481, "Fenton Iverson", function()
    evt.SimpleMessage("Fenton Iverson, Master Merchant of Alvar, tests all who wish to advanced with the skills of a Merchant.  You will find Fenton in the merchant city of Alvar, where he can instruct you to Mastery of the Merchant skill.")
    SetAutonote(204) -- Fenton Iverson, Master Merchant instructor, lives in the merchant city of Alvar.
    return
end)

RegisterGlobalEvent(482, "Raven Quicktoungue", function()
    evt.SimpleMessage("Raven Quicktoungue, Grand Master Merchant of Alvar, dwells in the city of Ravenshore.  There, Raven can watch the interaction of numerous races as the trade with each other.  Only he can raise your knowledge to Grand Mastery of the merchant skill.")
    SetAutonote(205) -- Raven Quicktoungue, Grand Master Merchant instructor, dwells in the city of Ravenshore.
    return
end)

RegisterGlobalEvent(483, "Evandar Lotts", function()
    evt.SimpleMessage("Evandar Lotts teaches the Expert skills of Repairing Items.  He dwells in the seaside city of Ravenshore.")
    SetAutonote(206) -- Evandar Lotts teaches the Expert skills of Repairing Items. He dwells in the seaside city of Ravenshore.
    return
end)

RegisterGlobalEvent(484, "Quick Jeni", function()
    evt.SimpleMessage("Quick Jeni, is the Master of the Repair Item skill. She lives in the village around the Dargon Hunter's Fort in Garrote Gorge.")
    SetAutonote(207) -- Quick Jeni, is the Master of the Repair Item skill. She lives in the village around the Dragon Hunter's Fort in Garrote Gorge.
    return
end)

RegisterGlobalEvent(485, "Quethrin Tonk", function()
    evt.SimpleMessage("Quethrin Tonk, Grand Master of the Repair Item skill, dwells in the tranquil Murmurwoods.  His skills have proven invaluable to the Temple of the Sun.")
    SetAutonote(208) -- Quethrin Tonk, Grand Master of the Repair Item skill, dwells in Murmurwoods.
    return
end)

RegisterGlobalEvent(486, "Menasaur", function()
    evt.SimpleMessage("Menasaur, the strongest Lizardmen on the Dagger Wound Islands, is the Expert instructor of the Body Building skill. ")
    SetAutonote(209) -- Menasaur, lives on the Dagger Wound Islands. He is the Expert instructor of Body Building.
    return
end)

RegisterGlobalEvent(487, "Kenneth Otterton", function()
    evt.SimpleMessage("Kenneth Otterton, holds the title of Crusader, and serves under the knight Charles Quixote in Garrote Gorge.  Rumor has it that he wrestled a Dragon to the ground single-handedly.  Of course, other knights had to assist in the kill.  Kenneth also holds the title, Master Instructor of Body Building.")
    SetAutonote(210) -- Kenneth Otterton, the Master instructor of Body Building lives in the Dragon Hunter's Camp in Garrote Gorge.
    return
end)

RegisterGlobalEvent(488, "Mikel Smithson", function()
    evt.SimpleMessage("Mikel Smithson, holds the title of Strongest in Jadame.  He is also the Grand Master of the Body Building skill.  Seek him out in the village of Rust in the Ironsand Desert if you wish to perfect the strength of your bodies.")
    SetAutonote(211) -- Mikel Smithson is the Grand Master of the Body Building skill. Seek him out in the village of Rust in the Ironsand Desert.
    return
end)

RegisterGlobalEvent(489, "Alton Putnam", function()
    evt.SimpleMessage("Alton Putnam, is an Expert in the art of Meditation.  He can instruct you if you seek him out in the seaside city of Ravenshore.")
    SetAutonote(212) -- Alton Putnam, is an Expert in the art of Meditation. He can instruct you if you seek him out in the seaside city of Ravenshore.
    return
end)

RegisterGlobalEvent(490, "Gretchin Nevermore", function()
    evt.SimpleMessage("Gretchin Nevermore, instructs all Clerics of the Sun the Master arts of Meditation. He dwells in the Murmurwoods near the Temple of the Sun.")
    SetAutonote(213) -- Gretchin Nevermore, the teacher of Master Meditation, dwells in the merchant city of Alvar.
    return
end)

RegisterGlobalEvent(491, "Lenord Nightcrawler", function()
    evt.SimpleMessage("Lenord Nightcrawler, Grand Master of Meditation, serves as one of the foremost members of the Necromancers' Guild of Shadowspire.  He instructs all necromancers in the art of Meditation from his home in the village of Twilight.")
    SetAutonote(214) -- Lenord Nightcrawler, Grand Master of Meditation, teaches from his home in the village of Twilight.
    return
end)

RegisterGlobalEvent(492, "Silk Nightwalker", function()
    evt.SimpleMessage("Silk Nightwalker, Expert teacher of the Perception skill, makes his home in the Dark Elf city of Alvar.  Instructing the Merchants of Alvar in the skills needed to detect that which is supposed to remain secret occupies most of his time, however him may take the time to instruct you if luck is with you.")
    SetAutonote(215) -- Silk Nightwalker, Expert teacher of the Perception skill, makes his home in the Dark Elf city of Alvar.
    return
end)

RegisterGlobalEvent(493, "Helga Steeleye", function()
    evt.SimpleMessage("Helga Steeleye, lives among the necromancers of Shadowspire in the village of Twilight.  The Necromancers' Guild is thankful for her Master level instructions in the skill of Perception.")
    SetAutonote(216) -- Helga Steeleye, teacher of Master Perception, lives in the Shadowspire city of Twilight.
    return
end)

RegisterGlobalEvent(494, "Balan Suretrail", function()
    evt.SimpleMessage("Grand Master Balan Suretrail lives in the Minotaur city of Balthazar Lair.  To gain his instruction in the skill of Perception, you must seek him out in Ravage Roaming.")
    SetAutonote(217) -- Grand Master instructor of Perception, Balan Suretrail lives in the Minotaur city of Balthazar Lair.
    return
end)

RegisterGlobalEvent(495, "Kethric Tarent", function()
    evt.SimpleMessage("Kethric Tarent, teaches the Expert knowledge of Regeneration from his home in the Ironsand Desert, in the village of Rust.")
    SetAutonote(218) -- Kethric Tarent, teaches Expert Regeneration from his home in the Ironsand Desert village of Rust.
    return
end)

RegisterGlobalEvent(496, "William Sampson", function()
    evt.SimpleMessage("William Sampson, Master of Regeneration, lives in the peace of the Murmurwoods.  He uses the libraries of the Temple of the Sun to further his knowledge of Trollish history.")
    SetAutonote(219) -- William Sampson, Master Regeneration instructor, lives in Murmurwoods.
    return
end)

RegisterGlobalEvent(497, "Ush the Many Tailed", function()
    evt.SimpleMessage("Ush the Many Tailed, Grand Master of Regeneration and legendary warrior, lives among his people on Dagger Wound Island.  Legends say he has lost his tail thirteen times in battle against the Regnan Pirates, and each time he has grown a new tail!")
    SetAutonote(220) -- Ush the Many Tailed, Grand Master Regeneration teacher, lives among his people on the Dagger Wound Islands.
    return
end)

RegisterGlobalEvent(498, "Chevon Wist", function()
    evt.SimpleMessage("Chevon Wist, teaches the Expert knowledge of the Disarm Trap skill, which has proven useful to those who explore the ruined temples near his home on the Dagger Wound Islands.")
    SetAutonote(221) -- Chevon Wist, teaches Expert Disarm Trap from his home on the Dagger Wound Islands.
    return
end)

RegisterGlobalEvent(499, "Kelli Lightfingers", function()
    evt.SimpleMessage("Kelli Lightfingers, Master of Disarming Traps, has retired to her home in the merchant city of Alvar.  There she still teaches young merchants the skills of trapping and disarming chests.  If you are worthy she can raise your Disarm Trap skills to that of a Master.")
    SetAutonote(222) -- Kelli Lightfingers, Master of Disarming Traps, teaches from her home in the city of Alvar.
    return
end)

RegisterGlobalEvent(500, "Gareth Lifter", function()
    evt.SimpleMessage("Gareth Lifter, Grand Master of Disarming Traps, lives on the opulent island of Regna, where he teaches his fellow pirates in the best way to trap their chests of stolen booty.")
    SetAutonote(223) -- Gareth Lifter, Grand Master of Disarming Traps, teaches from his home on the island of Regna.
    return
end)

RegisterGlobalEvent(507, "Tessa Maker", function()
    evt.SimpleMessage("Tessa Maker, Expert in Monster Identification, seeks to improve her skills by cataloging the different Dragons of Garrote Gorge.  She is currently in the service of the knight, Charles Quixote.")
    SetAutonote(230) -- Tessa Maker, Expert in Monster Identification, lives in the Garrote Gorge Dragon Hunter's Camp.
    return
end)

RegisterGlobalEvent(508, "Matric Keenedge", function()
    evt.SimpleMessage("Matric Keenedge, Master of the skill of Identify Monster, is currently studying the creatures of the Murmurwoods.  If you seek Mastery of this skill you need to seek him out there.")
    SetAutonote(231) -- Matric Keenedge, Master Identify Monster teacher, can be found in Murmurwoods.
    return
end)

RegisterGlobalEvent(509, "Blacken Stonecleaver", function()
    evt.SimpleMessage("Blacken Stonecleaver, Grand Master of Monster Identification, has seen every creature on the continent of Jadame.  He can teach you his knowledge if you find his home in the city of Ravenshore.")
    SetAutonote(232) -- Blacken Stonecleaver, Grand Master of Monster Identification, teaches his skill from his home in the city of Ravenshore.
    return
end)

RegisterGlobalEvent(510, "Norbert Slayer", function()
    evt.SimpleMessage("Knight Norbert Slayer, instructs all of Charles Quixote's knights in the Expert forms of  Armsmastery.  If you travel to Garrote Gorge, you can attend one of his teachings.")
    SetAutonote(233) -- Knight Norbert Slayer, Expert Armsmaster instructor, lives in the Garrote Gorge Dragon Hunter's Camp.
    return
end)

RegisterGlobalEvent(511, "Lasatin the Scarred", function()
    evt.SimpleMessage("Lasatin the Scarred, Master of the Armsmaster skill, lives on the Islands of Dagger Wound.")
    SetAutonote(234) -- Lasatin the Scarred, Master teacher of the Armsmaster skill, lives on the Islands of Dagger Wound.
    return
end)

RegisterGlobalEvent(512, "Jasper Steelcoif", function()
    evt.SimpleMessage("Jasper Steelcoif, Grand Master of the Armsmaster skill, is one of the leaders of the Regnan Pirate Council.  He instructs all pirates in the use of weapons.  If you are brave enough to travel to Regna--and survive his instruction--you too, will have Grand Mastery of this skill.")
    SetAutonote(235) -- Jasper Steelcoif, Grand Master teacher of the Armsmaster skill, can be found on Regna Island.
    return
end)

RegisterGlobalEvent(516, "Tabitha Watershed", function()
    evt.SimpleMessage("Tabitha Watershed, Expert Alchemist, teaches the skills of potions and poultices from her home in the merchant city of Alvar.")
    SetAutonote(239) -- Tabitha Watershed, Expert Alchemy instructor, teaches from her home in the merchant city of Alvar.
    return
end)

RegisterGlobalEvent(517, "Kethry Treasurestone", function()
    evt.SimpleMessage("Kethry Treasurestone, Master Alchemist, lives in the Murmurwoods, studying plants and mushrooms that grow in that peaceful forest.")
    SetAutonote(240) -- Kethry Treasurestone, Master Alchemy teacher, lives in the Murmurwoods region.
    return
end)

RegisterGlobalEvent(518, "Ich", function()
    evt.SimpleMessage("Ich, Grand Master of Alchemy, has studied the art of brewing for decades.  He knows all there is to know about blending reagents into beneficial and harmful potions.  Seek out his home in the lush jungles of the Dagger Wound Islands.")
    SetAutonote(241) -- Ich, Grand Master of Alchemy, teaches from his home in the lush jungles of the Dagger Wound Islands.
    return
end)

RegisterGlobalEvent(519, "Petra Mithrit", function()
    evt.SimpleMessage("Petra Mithrit, Expert in the skill of Learning, dwells near the Temple of the Sun in the Murmurwoods.")
    SetAutonote(242) -- Petra Mithrit, Expert teacher of the Learning skill, dwells near the Temple of the Sun in the Murmurwoods.
    return
end)

RegisterGlobalEvent(520, "Garret Mistspring", function()
    evt.SimpleMessage("Garret Mistspring, Master of Learning, instructs all students of necromancy in the art of Learning.  For this the Necromancers' Guild rewards him well.  His home is in the hamlet of Twilight at the base of the Shadowspire.")
    SetAutonote(243) -- Garret Mistspring, Master of Learning, instructs students from his home is in the Shadowspire city of Twilight.
    return
end)

RegisterGlobalEvent(521, "Wanda Lightsworn", function()
    evt.SimpleMessage("Wanda Lightsworn, Grand Master of Learning, is in the hire of Charles Quixote, and instructs all of his knights in the skills of Learning.  It is the hope of Charles Quixote that this will give his forces and edge in battle against the Dragons of Garrote Gorge.")
    SetAutonote(244) -- Wanda Lightsworn, Grand Master of Learning, lives in the Garrote Gorge Dragon Hunter's Camp.
    return
end)

RegisterGlobalEvent(522, "Flynn Shador", function()
    evt.SimpleMessage("Flynn Shador, Expert Vampire, lives in the city of Twilight, serving as eyes and a safe house for any Vampires that travel to that region.  He can instruct you in the Expert abilities of a Vampire.")
    SetAutonote(194) -- Flynn Shador, Expert Vampire ability instructor, lives in the Shadowspire city of Twilight.
    return
end)

RegisterGlobalEvent(523, "Douglas Dirthmoore", function()
    evt.SimpleMessage("Douglas Dirthmoore, Master Vampire, will teach any whose skills measure up to his standards.  Once he is done with you, you will have Mastered the abilities native to all Vampires.  His home is in the Shadowspire village of Twilight.")
    SetAutonote(195) -- Douglas Dirthmoore, Master Vampire ability instructor, makes his home in the Shadowspire city of Twilight.
    return
end)

RegisterGlobalEvent(524, "Payge Arachnia", function()
    evt.SimpleMessage("Though no one knows for sure, Payge Arachnia, Grand Master Vampire, is rumored to be the first Vampire on the continent of Jadame. She knows all there is to be known about living as a Vampire and can teach you the Grand Master abilities she possesses.  Seek out her lair in Shadowspire.")
    SetAutonote(196) -- Payge Arachnia, Grand Master Vampire ability instructor, lives in her lair located in Shadowspire.
    return
end)

RegisterGlobalEvent(525, "Fedwin Dervish", function()
    evt.SimpleMessage("Fedwin Dervish, can instruct you in the Expert ways of the Dark Elf.  Once you have learned from him, you will have begun a great journey to becoming a leader of your people.  Search him out in the Dark Elf city of Alvar.")
    SetAutonote(191) -- Fedwin Dervish, can instruct you in the Expert ways of the Dark Elf ability. Search him out in the Dark Elf city of Alvar.
    return
end)

RegisterGlobalEvent(526, "Lanshee Caverhill", function()
    evt.SimpleMessage("Lanshee Caverhill, Master Merchant of Alvar currently lives in the seaside port of Ravenshore.  She knows all about Mastering the natural abilities all Dark Elves have.")
    SetAutonote(192) -- Lanshee Caverhill lives in the seaside port of Ravenshore. She teaches the Master skills of the Dark Elf ability.
    return
end)

RegisterGlobalEvent(527, "Ton Agraynel", function()
    evt.SimpleMessage("Ton Agraynel, Master Merchant of Alvar, can instruct you in the Grand Master skills of a Dark Elf.  You will have to prove yourself worthy of his instruction, but the benefits are well worth the effort.")
    SetAutonote(193) -- Ton Agraynel can instruct you in the Grand Master skills of a Dark Elf. He lives in the city of Alvar.
    return
end)

RegisterGlobalEvent(528, "Ishton", function()
    evt.SimpleMessage("Ishton, Junior Flight Leader of the Dragons of Garrote Gorge, instructs all young Dragons to an Expert skill level with their racial Dragon abilities.  He dwells here, in the Dragon Caves of Garrote Gorge.")
    SetAutonote(197) -- Ishton instructs Dragons to an Expert skill level with their racial Dragon abilities. He dwells in the Dragon Caves of Garrote Gorge.
    return
end)

RegisterGlobalEvent(529, "Erthint", function()
    evt.SimpleMessage("Master Dragon Erthint is the Flight Leader of all of the Dragons that serve under Deftclaw Redreaver, and can instruct a Dragon in Mastery of his natural Dragon abilities. Erthint lives in the Dragon Caves of Garrote Gorge.")
    SetAutonote(198) -- Master Dragon ability instructor, Erthint, lives in the Dragon Caves of Garrote Gorge.
    return
end)

RegisterGlobalEvent(530, "Klain Scarwing", function()
    evt.SimpleMessage("Klain Scarwing, is second in strength only to Deftclaw Redreaver himself.  Klain holds the title of Grand Master Dragon and instructs all Dragons in the use of their natural abilities.  See him if you wish to attain Grand Master status.  He dwells here in the Dragon Caves of Garrote Gorge.")
    SetAutonote(199) -- Klain, the Grand Master Dragon ability instructor dwells in the Dragon Caves of Garrote Gorge.
    return
end)

RegisterGlobalEvent(531, "Haste Pedestal", function()
    evt.CastSpell(5, 5, 4, 0, 0, 0, 0, 0, 0) -- Haste
end)

RegisterGlobalEvent(532, "Earth Resistance Pedestal", function()
    evt.CastSpell(36, 5, 4, 0, 0, 0, 0, 0, 0) -- Earth Resistance
end)

RegisterGlobalEvent(533, "Day of the Gods Pedestal", function()
    evt.CastSpell(83, 5, 4, 0, 0, 0, 0, 0, 0) -- Day of the Gods
end)

RegisterGlobalEvent(534, "Shield Pedestal", function()
    evt.CastSpell(17, 5, 4, 0, 0, 0, 0, 0, 0) -- Shield
end)

RegisterGlobalEvent(535, "Water Resistance Pedestal", function()
    evt.CastSpell(25, 5, 4, 0, 0, 0, 0, 0, 0) -- Water Resistance
end)

RegisterGlobalEvent(536, "Fire Resistance Pedestal", function()
    evt.CastSpell(3, 5, 4, 0, 0, 0, 0, 0, 0) -- Fire Resistance
end)

RegisterGlobalEvent(537, "Heroism Pedestal", function()
    evt.CastSpell(51, 5, 4, 0, 0, 0, 0, 0, 0) -- Heroism
end)

RegisterGlobalEvent(538, "Immolation Pedestal", function()
    evt.CastSpell(8, 5, 4, 0, 0, 0, 0, 0, 0) -- Immolation
end)

RegisterGlobalEvent(539, "Mind Resistance Pedestal", function()
    evt.CastSpell(58, 5, 4, 0, 0, 0, 0, 0, 0) -- Mind Resistance
end)

RegisterGlobalEvent(540, "Body Resistance Pedestal", function()
    evt.CastSpell(69, 5, 4, 0, 0, 0, 0, 0, 0) -- Body Resistance
end)

RegisterGlobalEvent(541, "Stone Skin Pedestal", function()
    evt.CastSpell(38, 5, 4, 0, 0, 0, 0, 0, 0) -- Stone Skin
end)

RegisterGlobalEvent(542, "Air Resistance Pedestal", function()
    evt.CastSpell(14, 5, 4, 0, 0, 0, 0, 0, 0) -- Air Resistance
end)

RegisterGlobalEvent(543, "Game of Might", function()
    if IsAtLeast(2031849, 31) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualMight, 25) then
        AddValue(SkillPoints, 3)
        evt.StatusText("You win!  +3 Skill Points")
        AddValue(2031849, 31)
    else
        evt.StatusText("You have failed the game!")
    end
    return
end)

RegisterGlobalEvent(544, "Game of Endurance", function()
    if IsAtLeast(2097385, 32) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualEndurance, 25) then
        AddValue(SkillPoints, 3)
        evt.StatusText("You win!  +3 Skill Points")
        AddValue(2097385, 32)
    else
        evt.StatusText("You have failed the game!")
    end
    return
end)

RegisterGlobalEvent(545, "Game of Intellect", function()
    if IsAtLeast(2162921, 33) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualIntellect, 25) then
        AddValue(SkillPoints, 3)
        evt.StatusText("You win!  +3 Skill Points")
        AddValue(2162921, 33)
    else
        evt.StatusText("You have failed the game!")
    end
    return
end)

RegisterGlobalEvent(546, "Game of Personality", function()
    if IsAtLeast(2228457, 34) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualPersonality, 25) then
        AddValue(SkillPoints, 3)
        evt.StatusText("You win!  +3 Skill Points")
        AddValue(2228457, 34)
    else
        evt.StatusText("You have failed the game!")
    end
    return
end)

RegisterGlobalEvent(547, "Game of Accuracy", function()
    if IsAtLeast(2293993, 35) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualAccuracy, 25) then
        AddValue(SkillPoints, 3)
        evt.StatusText("You win!  +3 Skill Points")
        AddValue(2293993, 35)
    else
        evt.StatusText("You have failed the game!")
    end
    return
end)

RegisterGlobalEvent(548, "Game of Speed", function()
    if IsAtLeast(2359529, 36) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualSpeed, 25) then
        AddValue(SkillPoints, 3)
        evt.StatusText("You win!  +3 Skill Points")
        AddValue(2359529, 36)
    else
        evt.StatusText("You have failed the game!")
    end
    return
end)

RegisterGlobalEvent(549, "Game of Luck", function()
    if IsAtLeast(2425065, 37) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualLuck, 25) then
        AddValue(SkillPoints, 3)
        evt.StatusText("You win!  +3 Skill Points")
        AddValue(2425065, 37)
    else
        evt.StatusText("You have failed the game!")
    end
    return
end)

RegisterGlobalEvent(550, "Contest of Might", function()
    if IsAtLeast(2490601, 38) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualMight, 50) then
        AddValue(SkillPoints, 5)
        evt.StatusText("You win!  +5 Skill Points")
        AddValue(2490601, 38)
    else
        evt.StatusText("You have failed the contest!")
    end
    return
end)

RegisterGlobalEvent(551, "Contest of Endurance", function()
    if IsAtLeast(2556137, 39) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualEndurance, 50) then
        AddValue(SkillPoints, 5)
        evt.StatusText("You win!  +5 Skill Points")
        AddValue(2556137, 39)
    else
        evt.StatusText("You have failed the contest!")
    end
    return
end)

RegisterGlobalEvent(552, "Contest of Intellect", function()
    if IsAtLeast(2621673, 40) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualIntellect, 50) then
        AddValue(SkillPoints, 5)
        evt.StatusText("You win!  +5 Skill Points")
        AddValue(2621673, 40)
    else
        evt.StatusText("You have failed the contest!")
    end
    return
end)

RegisterGlobalEvent(553, "Contest of Personality", function()
    if IsAtLeast(2687209, 41) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualPersonality, 50) then
        AddValue(SkillPoints, 5)
        evt.StatusText("You win!  +5 Skill Points")
        AddValue(2687209, 41)
    else
        evt.StatusText("You have failed the contest!")
    end
    return
end)

RegisterGlobalEvent(554, "Contest of Accuracy", function()
    if IsAtLeast(2752745, 42) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualAccuracy, 50) then
        AddValue(SkillPoints, 5)
        evt.StatusText("You win!  +5 Skill Points")
        AddValue(2752745, 42)
    else
        evt.StatusText("You have failed the contest!")
    end
    return
end)

RegisterGlobalEvent(555, "Contest of Speed", function()
    if IsAtLeast(2818281, 43) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualSpeed, 50) then
        AddValue(SkillPoints, 5)
        evt.StatusText("You win!  +5 Skill Points")
        AddValue(2818281, 43)
    else
        evt.StatusText("You have failed the contest!")
    end
    return
end)

RegisterGlobalEvent(556, "Contest of Luck", function()
    if IsAtLeast(2883817, 44) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualLuck, 50) then
        AddValue(SkillPoints, 5)
        evt.StatusText("You win!  +5 Skill Points")
        AddValue(2883817, 44)
    else
        evt.StatusText("You have failed the contest!")
    end
    return
end)

RegisterGlobalEvent(557, "Test of Might", function()
    if IsAtLeast(2949353, 45) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualMight, 100) then
        AddValue(SkillPoints, 7)
        evt.StatusText("You win!  +7 Skill Points")
        AddValue(2949353, 45)
    else
        evt.StatusText("You have failed the test!")
    end
    return
end)

RegisterGlobalEvent(558, "Test of Endurance", function()
    if IsAtLeast(3014889, 46) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualEndurance, 100) then
        AddValue(SkillPoints, 7)
        evt.StatusText("You win!  +7 Skill Points")
        AddValue(3014889, 46)
    else
        evt.StatusText("You have failed the test!")
    end
    return
end)

RegisterGlobalEvent(559, "Test of Intellect", function()
    if IsAtLeast(3080425, 47) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualIntellect, 100) then
        AddValue(SkillPoints, 7)
        evt.StatusText("You win!  +7 Skill Points")
        AddValue(3080425, 47)
    else
        evt.StatusText("You have failed the test!")
    end
    return
end)

RegisterGlobalEvent(560, "Test of Personality", function()
    if IsAtLeast(3145961, 48) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualPersonality, 100) then
        AddValue(SkillPoints, 7)
        evt.StatusText("You win!  +7 Skill Points")
        AddValue(3145961, 48)
    else
        evt.StatusText("You have failed the test!")
    end
    return
end)

RegisterGlobalEvent(561, "Test of Accuracy", function()
    if IsAtLeast(3211497, 49) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualAccuracy, 100) then
        AddValue(SkillPoints, 7)
        evt.StatusText("You win!  +7 Skill Points")
        AddValue(3211497, 49)
    else
        evt.StatusText("You have failed the test!")
    end
    return
end)

RegisterGlobalEvent(562, "Test of Speed", function()
    if IsAtLeast(3277033, 50) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualSpeed, 100) then
        AddValue(SkillPoints, 7)
        evt.StatusText("You win!  +7 Skill Points")
        AddValue(3277033, 50)
    else
        evt.StatusText("You have failed the test!")
    end
    return
end)

RegisterGlobalEvent(563, "Test of Luck", function()
    if IsAtLeast(3342569, 51) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualLuck, 100) then
        AddValue(SkillPoints, 7)
        evt.StatusText("You win!  +7 Skill Points")
        AddValue(3342569, 51)
    else
        evt.StatusText("You have failed the test!")
    end
    return
end)

RegisterGlobalEvent(564, "Challenge of Might", function()
    if IsAtLeast(3408105, 52) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualMight, 200) then
        AddValue(SkillPoints, 10)
        evt.StatusText("You win!  +10 Skill Points")
        AddValue(3408105, 52)
    else
        evt.StatusText("You have failed the challenge!")
    end
    return
end)

RegisterGlobalEvent(565, "Challenge of Endurance", function()
    if IsAtLeast(3473641, 53) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualEndurance, 200) then
        AddValue(SkillPoints, 10)
        evt.StatusText("You win!  +10 Skill Points")
        AddValue(3473641, 53)
    else
        evt.StatusText("You have failed the challenge!")
    end
    return
end)

RegisterGlobalEvent(566, "Challenge of Intellect", function()
    if IsAtLeast(3539177, 54) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualIntellect, 200) then
        AddValue(SkillPoints, 10)
        evt.StatusText("You win!  +10 Skill Points")
        AddValue(3539177, 54)
    else
        evt.StatusText("You have failed the challenge!")
    end
    return
end)

RegisterGlobalEvent(567, "Challenge of Personality", function()
    if IsAtLeast(3604713, 55) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualPersonality, 200) then
        AddValue(SkillPoints, 10)
        evt.StatusText("You win!  +10 Skill Points")
        AddValue(3604713, 55)
    else
        evt.StatusText("You have failed the challenge!")
    end
    return
end)

RegisterGlobalEvent(568, "Challenge of Accuracy", function()
    if IsAtLeast(3670249, 56) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualAccuracy, 200) then
        AddValue(SkillPoints, 10)
        evt.StatusText("You win!  +10 Skill Points")
        AddValue(3670249, 56)
    else
        evt.StatusText("You have failed the challenge!")
    end
    return
end)

RegisterGlobalEvent(569, "Challenge of Speed", function()
    if IsAtLeast(3735785, 57) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualSpeed, 200) then
        AddValue(SkillPoints, 10)
        evt.StatusText("You win!  +10 Skill Points")
        AddValue(3735785, 57)
    else
        evt.StatusText("You have failed the challenge!")
    end
    return
end)

RegisterGlobalEvent(570, "Challenge of Luck", function()
    if IsAtLeast(3801321, 58) then
        evt.StatusText("You have already won!")
        return
    elseif IsAtLeast(ActualLuck, 200) then
        AddValue(SkillPoints, 10)
        evt.StatusText("You win!  +10 Skill Points")
        AddValue(3801321, 58)
    else
        evt.StatusText("You have failed the challenge!")
    end
    return
end)

RegisterGlobalEvent(571, "Fire Resistance Potion", function()
    if IsQBitSet(QBit(149)) then -- Southern houses of Rust all have Potions of Fire Resistance.
        evt.SimpleMessage("You have at least pushed our demise away for a time, but a new home needs to be found for us!  Thank you for delivering the Potions of Fire Resistance!")
        return
    elseif IsQBitSet(QBit(143)) then -- Delivered potion to house 1
        evt.SimpleMessage("Thanks for the potion!")
    else
        evt.ForPlayer(Players.All)
        if not HasItem(256) then -- Fire Resistance
            evt.SimpleMessage("I an defenseless against the onslaught of the sea of fire!  I need a Potion of Fire Resistance!")
            return
        end
        RemoveItem(256) -- Fire Resistance
        SetQBit(QBit(143)) -- Delivered potion to house 1
        evt.ForPlayer(Players.All)
        AddValue(Experience, 1000)
    end
    if IsQBitSet(QBit(144)) then -- Delivered potion to house 2
        if IsQBitSet(QBit(145)) then -- Delivered potion to house 3
            if IsQBitSet(QBit(146)) then -- Delivered potion to house 4
                if IsQBitSet(QBit(147)) then -- Delivered potion to house 5
                    if IsQBitSet(QBit(148)) then -- Delivered potion to house 6
                        evt.ForPlayer(Players.All)
                        AddValue(Experience, 7500)
                        evt.SimpleMessage("Thanks for providing Potions of Fire Resistance to the southernmost houses here in Rust.  Perhaps we can survive until a new home can be found for us!")
                        SetQBit(QBit(149)) -- Southern houses of Rust all have Potions of Fire Resistance.
                        return
                    end
                end
            end
        end
    end
    evt.SimpleMessage("Thanks for the potion, but others in the area are without protection!  Be sure to deliver a potion to them as well!")
    return
end)
RegisterCanShowTopic(571, function()
    evt._BeginCanShowTopic(571)
    local visible = true
    if IsQBitSet(QBit(142)) then -- Deliver Fire Resistance Potions to the six southernmost houses of Rust. Return to Hobert in Rust.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(572, "Fire Resistance Potion", function()
    if IsQBitSet(QBit(149)) then -- Southern houses of Rust all have Potions of Fire Resistance.
        evt.SimpleMessage("You have at least pushed our demise away for a time, but a new home needs to be found for us!  Thank you for delivering the Potions of Fire Resistance!")
        return
    elseif IsQBitSet(QBit(144)) then -- Delivered potion to house 2
        evt.SimpleMessage("Thanks for the potion!")
    else
        evt.ForPlayer(Players.All)
        if not HasItem(256) then -- Fire Resistance
            evt.SimpleMessage("I an defenseless against the onslaught of the sea of fire!  I need a Potion of Fire Resistance!")
            return
        end
        RemoveItem(256) -- Fire Resistance
        SetQBit(QBit(144)) -- Delivered potion to house 2
        evt.ForPlayer(Players.All)
        AddValue(Experience, 1000)
    end
    if IsQBitSet(QBit(143)) then -- Delivered potion to house 1
        if IsQBitSet(QBit(145)) then -- Delivered potion to house 3
            if IsQBitSet(QBit(146)) then -- Delivered potion to house 4
                if IsQBitSet(QBit(147)) then -- Delivered potion to house 5
                    if IsQBitSet(QBit(148)) then -- Delivered potion to house 6
                        evt.ForPlayer(Players.All)
                        AddValue(Experience, 1500)
                        evt.SimpleMessage("Thanks for providing Potions of Fire Resistance to the southernmost houses here in Rust.  Perhaps we can survive until a new home can be found for us!")
                        SetQBit(QBit(149)) -- Southern houses of Rust all have Potions of Fire Resistance.
                        return
                    end
                end
            end
        end
    end
    evt.SimpleMessage("Thanks for the potion, but others in the area are without protection!  Be sure to deliver a potion to them as well!")
    return
end)
RegisterCanShowTopic(572, function()
    evt._BeginCanShowTopic(572)
    local visible = true
    if IsQBitSet(QBit(142)) then -- Deliver Fire Resistance Potions to the six southernmost houses of Rust. Return to Hobert in Rust.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(573, "Fire Resistance Potion", function()
    if IsQBitSet(QBit(149)) then -- Southern houses of Rust all have Potions of Fire Resistance.
        evt.SimpleMessage("You have at least pushed our demise away for a time, but a new home needs to be found for us!  Thank you for delivering the Potions of Fire Resistance!")
        return
    elseif IsQBitSet(QBit(145)) then -- Delivered potion to house 3
        evt.SimpleMessage("Thanks for the potion!")
    else
        evt.ForPlayer(Players.All)
        if not HasItem(256) then -- Fire Resistance
            evt.SimpleMessage("I an defenseless against the onslaught of the sea of fire!  I need a Potion of Fire Resistance!")
            return
        end
        RemoveItem(256) -- Fire Resistance
        SetQBit(QBit(145)) -- Delivered potion to house 3
        evt.ForPlayer(Players.All)
        AddValue(Experience, 1000)
    end
    if IsQBitSet(QBit(143)) then -- Delivered potion to house 1
        if IsQBitSet(QBit(144)) then -- Delivered potion to house 2
            if IsQBitSet(QBit(146)) then -- Delivered potion to house 4
                if IsQBitSet(QBit(147)) then -- Delivered potion to house 5
                    if IsQBitSet(QBit(148)) then -- Delivered potion to house 6
                        evt.ForPlayer(Players.All)
                        AddValue(Experience, 1500)
                        evt.SimpleMessage("Thanks for providing Potions of Fire Resistance to the southernmost houses here in Rust.  Perhaps we can survive until a new home can be found for us!")
                        SetQBit(QBit(149)) -- Southern houses of Rust all have Potions of Fire Resistance.
                        return
                    end
                end
            end
        end
    end
    evt.SimpleMessage("Thanks for the potion, but others in the area are without protection!  Be sure to deliver a potion to them as well!")
    return
end)
RegisterCanShowTopic(573, function()
    evt._BeginCanShowTopic(573)
    local visible = true
    if IsQBitSet(QBit(142)) then -- Deliver Fire Resistance Potions to the six southernmost houses of Rust. Return to Hobert in Rust.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(574, "Fire Resistance Potion", function()
    if IsQBitSet(QBit(149)) then -- Southern houses of Rust all have Potions of Fire Resistance.
        evt.SimpleMessage("You have at least pushed our demise away for a time, but a new home needs to be found for us!  Thank you for delivering the Potions of Fire Resistance!")
        return
    elseif IsQBitSet(QBit(146)) then -- Delivered potion to house 4
        evt.SimpleMessage("Thanks for the potion!")
    else
        evt.ForPlayer(Players.All)
        if not HasItem(256) then -- Fire Resistance
            evt.SimpleMessage("I an defenseless against the onslaught of the sea of fire!  I need a Potion of Fire Resistance!")
            return
        end
        RemoveItem(256) -- Fire Resistance
        SetQBit(QBit(146)) -- Delivered potion to house 4
        evt.ForPlayer(Players.All)
        AddValue(Experience, 1000)
    end
    if IsQBitSet(QBit(143)) then -- Delivered potion to house 1
        if IsQBitSet(QBit(144)) then -- Delivered potion to house 2
            if IsQBitSet(QBit(145)) then -- Delivered potion to house 3
                if IsQBitSet(QBit(147)) then -- Delivered potion to house 5
                    if IsQBitSet(QBit(148)) then -- Delivered potion to house 6
                        evt.ForPlayer(Players.All)
                        AddValue(Experience, 1500)
                        evt.SimpleMessage("Thanks for providing Potions of Fire Resistance to the southernmost houses here in Rust.  Perhaps we can survive until a new home can be found for us!")
                        SetQBit(QBit(149)) -- Southern houses of Rust all have Potions of Fire Resistance.
                        return
                    end
                end
            end
        end
    end
    evt.SimpleMessage("Thanks for the potion, but others in the area are without protection!  Be sure to deliver a potion to them as well!")
    return
end)
RegisterCanShowTopic(574, function()
    evt._BeginCanShowTopic(574)
    local visible = true
    if IsQBitSet(QBit(142)) then -- Deliver Fire Resistance Potions to the six southernmost houses of Rust. Return to Hobert in Rust.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(575, "Fire Resistance Potion", function()
    if IsQBitSet(QBit(149)) then -- Southern houses of Rust all have Potions of Fire Resistance.
        evt.SimpleMessage("You have at least pushed our demise away for a time, but a new home needs to be found for us!  Thank you for delivering the Potions of Fire Resistance!")
        return
    elseif IsQBitSet(QBit(147)) then -- Delivered potion to house 5
        evt.SimpleMessage("Thanks for the potion!")
    else
        evt.ForPlayer(Players.All)
        if not HasItem(256) then -- Fire Resistance
            evt.SimpleMessage("I an defenseless against the onslaught of the sea of fire!  I need a Potion of Fire Resistance!")
            return
        end
        RemoveItem(256) -- Fire Resistance
        SetQBit(QBit(147)) -- Delivered potion to house 5
        evt.ForPlayer(Players.All)
        AddValue(Experience, 1000)
    end
    if IsQBitSet(QBit(143)) then -- Delivered potion to house 1
        if IsQBitSet(QBit(144)) then -- Delivered potion to house 2
            if IsQBitSet(QBit(145)) then -- Delivered potion to house 3
                if IsQBitSet(QBit(146)) then -- Delivered potion to house 4
                    if IsQBitSet(QBit(148)) then -- Delivered potion to house 6
                        evt.ForPlayer(Players.All)
                        AddValue(Experience, 1500)
                        evt.SimpleMessage("Thanks for providing Potions of Fire Resistance to the southernmost houses here in Rust.  Perhaps we can survive until a new home can be found for us!")
                        SetQBit(QBit(149)) -- Southern houses of Rust all have Potions of Fire Resistance.
                        return
                    end
                end
            end
        end
    end
    evt.SimpleMessage("Thanks for the potion, but others in the area are without protection!  Be sure to deliver a potion to them as well!")
    return
end)
RegisterCanShowTopic(575, function()
    evt._BeginCanShowTopic(575)
    local visible = true
    if IsQBitSet(QBit(142)) then -- Deliver Fire Resistance Potions to the six southernmost houses of Rust. Return to Hobert in Rust.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(576, "Fire Resistance Potion", function()
    if IsQBitSet(QBit(149)) then -- Southern houses of Rust all have Potions of Fire Resistance.
        evt.SimpleMessage("You have at least pushed our demise away for a time, but a new home needs to be found for us!  Thank you for delivering the Potions of Fire Resistance!")
        return
    elseif IsQBitSet(QBit(148)) then -- Delivered potion to house 6
        evt.SimpleMessage("Thanks for the potion!")
    else
        evt.ForPlayer(Players.All)
        if not HasItem(256) then -- Fire Resistance
            evt.SimpleMessage("I an defenseless against the onslaught of the sea of fire!  I need a Potion of Fire Resistance!")
            return
        end
        RemoveItem(256) -- Fire Resistance
        SetQBit(QBit(148)) -- Delivered potion to house 6
        evt.ForPlayer(Players.All)
        AddValue(Experience, 1000)
    end
    if IsQBitSet(QBit(143)) then -- Delivered potion to house 1
        if IsQBitSet(QBit(144)) then -- Delivered potion to house 2
            if IsQBitSet(QBit(145)) then -- Delivered potion to house 3
                if IsQBitSet(QBit(146)) then -- Delivered potion to house 4
                    if IsQBitSet(QBit(147)) then -- Delivered potion to house 5
                        evt.ForPlayer(Players.All)
                        AddValue(Experience, 1500)
                        evt.SimpleMessage("Thanks for providing Potions of Fire Resistance to the southernmost houses here in Rust.  Perhaps we can survive until a new home can be found for us!")
                        SetQBit(QBit(149)) -- Southern houses of Rust all have Potions of Fire Resistance.
                        return
                    end
                end
            end
        end
    end
    evt.SimpleMessage("Thanks for the potion, but others in the area are without protection!  Be sure to deliver a potion to them as well!")
    return
end)
RegisterCanShowTopic(576, function()
    evt._BeginCanShowTopic(576)
    local visible = true
    if IsQBitSet(QBit(142)) then -- Deliver Fire Resistance Potions to the six southernmost houses of Rust. Return to Hobert in Rust.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(577, "Guild of Bounty Hunters", function()
    if IsQBitSet(QBit(169)) then -- Named Novice Bounty Hunter by the Guild of Bounty Hunters
        evt.SimpleMessage("Greetings Novice Bounty Hunter! The Guild of Bounty Hunters serves the public by paying qualified individuals a fee for eliminating the threat of certain creatures or bandits in the realm of Jadame.  To achieve the rank of Journeyman Bounty Hunter you will have to earn a total bounty of 30,000 gold.")
        return
    elseif IsQBitSet(QBit(170)) then -- Named Journeyman Bounty Hunter by the Guild of Bounty Hunters
        evt.SimpleMessage("Greetings Journeyman Bounty Hunter! The Guild of Bounty Hunters serves the public by paying qualified individuals a fee for eliminating the threat of certain creatures or bandits in the realm of Jadame.  To achieve the rank of Master Bounty Hunter you will have to earn a total bounty of 70,000 gold.")
        return
    elseif IsQBitSet(QBit(171)) then -- Named Novice Master Hunter by the Guild of Bounty Hunters
        evt.SimpleMessage("Greetings Master Bounty Hunter! The Guild of Bounty Hunters thanks you for your services to all of Jadame. We are at your disposal!")
    else
        evt.SimpleMessage("The Guild of Bounty Hunters serves the public by paying qualified individuals a fee for eliminating the threat of certain creatures or bandits in the realm of Jadame.  To achieve the rank of Novice Bounty Hunter you will have to earn 10,000 gold worth of bounties.")
    end
    return
end)

RegisterGlobalEvent(578, "Bounty!", function()
    if not evt.IsTotalBountyInRange(10000, 29999) then
        if not evt.IsTotalBountyInRange(30000, 69999) then
            if not evt.IsTotalBountyInRange(70000, 1000000) then
                evt.SimpleMessage("You have not gathered sufficient bounties to allow us to promote you!")
                return
            end
            evt.SimpleMessage("You currently hold the rank of Master Bounty Hunter! This is the highest rank of our guild.")
            for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
                evt.ForPlayer(player)
                if not HasAward(Award(40)) then -- Have earned status of Master Bounty Hunter.
                    ClearAward(Award(39)) -- Have earned status of Journeyman Bounty Hunter.
                    SetAward(Award(40)) -- Have earned status of Master Bounty Hunter.
                    evt.ForPlayer(player)
                    AddValue(Experience, 1200000)
                end
            end
            evt.ForPlayer(Players.All)
            ClearQBit(QBit(170)) -- Named Journeyman Bounty Hunter by the Guild of Bounty Hunters
            SetQBit(QBit(171)) -- Named Novice Master Hunter by the Guild of Bounty Hunters
            evt.SetNPCTopic(297, 2, 0) -- Bryant Conlan topic 2 cleared
            evt.SetNPCTopic(298, 2, 0) -- Cahalli Evenall topic 2 cleared
            return
        end
        evt.SimpleMessage("You currently hold the rank of Journeyman Bounty Hunter, but lack sufficient bounty to be promoted to Master.")
            evt.ForPlayer(player)
            if not HasAward(Award(39)) then -- Have earned status of Journeyman Bounty Hunter.
                ClearAward(Award(38)) -- Have earned status of Novice Bounty Hunter.
                evt.ForPlayer(Players.Member0)
                SetAward(Award(39)) -- Have earned status of Journeyman Bounty Hunter.
                AddValue(Experience, 80000)
            end
            evt.ForPlayer(player)
            if not HasAward(Award(39)) then -- Have earned status of Journeyman Bounty Hunter.
                ClearAward(Award(38)) -- Have earned status of Novice Bounty Hunter.
                SetAward(Award(39)) -- Have earned status of Journeyman Bounty Hunter.
                evt.ForPlayer(Players.Member1)
                AddValue(Experience, 80000)
            end
            evt.ForPlayer(player)
            if not HasAward(Award(39)) then -- Have earned status of Journeyman Bounty Hunter.
                ClearAward(Award(38)) -- Have earned status of Novice Bounty Hunter.
                SetAward(Award(39)) -- Have earned status of Journeyman Bounty Hunter.
                evt.ForPlayer(Players.Member2)
                AddValue(Experience, 80000)
            end
            evt.ForPlayer(player)
            if not HasAward(Award(39)) then -- Have earned status of Journeyman Bounty Hunter.
                ClearAward(Award(38)) -- Have earned status of Novice Bounty Hunter.
                SetAward(Award(39)) -- Have earned status of Journeyman Bounty Hunter.
                evt.ForPlayer(Players.Member3)
                AddValue(Experience, 80000)
            end
            evt.ForPlayer(player)
            if not HasAward(Award(39)) then -- Have earned status of Journeyman Bounty Hunter.
                ClearAward(Award(38)) -- Have earned status of Novice Bounty Hunter.
                SetAward(Award(39)) -- Have earned status of Journeyman Bounty Hunter.
                evt.ForPlayer(Players.Member4)
                AddValue(Experience, 80000)
            end
        evt.ForPlayer(Players.All)
        ClearQBit(QBit(169)) -- Named Novice Bounty Hunter by the Guild of Bounty Hunters
        SetQBit(QBit(170)) -- Named Journeyman Bounty Hunter by the Guild of Bounty Hunters
        return
    end
    evt.SimpleMessage("You currently hold the rank of Novice Bounty Hunter, but lack sufficient bounty to be promoted to Journeyman.")
    for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
        evt.ForPlayer(player)
        if not HasAward(Award(38)) then -- Have earned status of Novice Bounty Hunter.
            SetAward(Award(38)) -- Have earned status of Novice Bounty Hunter.
            evt.ForPlayer(player)
            AddValue(Experience, 40000)
        end
    end
    evt.ForPlayer(Players.All)
    SetQBit(QBit(169)) -- Named Novice Bounty Hunter by the Guild of Bounty Hunters
    return
end)

RegisterGlobalEvent(580, "Arcomage Tournament", function()
    evt.SimpleMessage("To be declared Arcomage Champion, you must win a game of Arcomage in every tavern on, in, and under the continent of Jadame.  There are 11 such taverns sponsoring Arcomage events.  When you have accomplished this, return to me to claim the prize.")
    SetQBit(QBit(173)) -- Win a game of Arcomage in all eleven taverns, then return to Tonk Blueswan in Ravenshore.
    evt.SetNPCTopic(410, 0, 0) -- Tonk Blueswan topic 0 cleared
end)

RegisterGlobalEvent(581, "Cleric Necromancer War", function()
    if IsQBitSet(QBit(19)) then -- Allied with Necromancers Guild. Steal Nightshade Brazier done.
        evt.SimpleMessage("Through your delivery of the Nightshade Brazier into their hands, the Necromancers' Guild has come out on top in their war with the Temple of the Sun. The artifact's magic creates a permanent shadow of darkness which surrounds the Shadowspire region. Under this cover, vampires defend the land both day and night. This has allowed the guild to field larger forces of skeletons, zombies and other undead against the temple's armies. Each report I receive puts the heart of the battle closer and closer to the Sun Temple's doorstep.")
        return
    elseif IsQBitSet(QBit(20)) then -- Allied with Temple of the Sun. Destroy the Skeleton Transformer done.
        evt.SimpleMessage("Because you have destroyed the Necromancers' Guild Skeleton Transformer, the Temple of the Sun has come out on top in their war with the guild. The skeletons created by the device made up the bulk of the guild's reinforcements. Without these, the necromancers' forces crumble before the temple's advance. Each report I receive puts the heart of the battle closer to the Necromancers' Guild doorstep.")
    else
        evt.SimpleMessage("Lying as they do on opposite ends of the Light to Dark spectrum, relationships between the Necromancers' Guild and the Temple of the Sun have never been the best, but now they battle openly. Oskar Tyre, head priest of the Temple says a holy vision drove him to declare war on the guild so as to rid Jadame of the taint of darkness.\n\nBoth groups are relative newcomers to our continent. The guild has set up its foothold in Shadowspire, and the First (and only) Sun Temple of Jadame is in Murmurwoods.")
    end
    return
end)

RegisterGlobalEvent(582, "Dragon Hunters", function()
    if IsQBitSet(QBit(21)) then -- Allied with Charles Quioxte's Dragon Hunters. Return Dragon Egg to Quixote done.
        evt.SimpleMessage("It seems Charles Quixote's Dragon hunting operation in Garrote Gorge has almost completely wiped out Garrote Gorge's Dragon population. I'm sure once their done, those mountains will be safer to travel. Still, I wonder what Jadame will be like without Dragons.")
        return
    elseif IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
        evt.SimpleMessage("By recovering Deftclaw Redreaver's heir for him, you've allowed him to safely attack Charles Quixote's camp. Dragon hunters operate by isolating members of their prey. They just aren't prepared to face Dragons in number! Needless to say, the camp's production of Dragon goods has dwindled to a trickle. A pity. The guild used to turned a good profit off them.")
    else
        evt.SimpleMessage("The renown Dragon slayer, Charles Quixote of Erathia, has set up a hunting expedition in Garrote Gorge. This is no \"safari,\" in fact, it's the largest operation of this type I've heard of. The hunters have a permanent base from which they sell hides, eggs, baby dragons, and other items. Garrote Gorge has always had a large Dragon population, but I imagine they must be facing extinction--so efficient are Quixote's hunters.")
    end
    return
end)

RegisterGlobalEvent(583, "Minotaurs", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.SimpleMessage("The Minotaurs of Balthazar Lair in Ravage Roaming are a proud culture. Their recent defeat of the Vori Frost Giants has, if anything, made them even more fiercely independent--more sure of their ability to face any task alone. Still, I have told the guild that they would make great allies, both to face the current crisis and later as trade partners.")
        return
    end
    evt.SimpleMessage("By rescuing the Balthazar Lair Minotaurs, you have ingratiated them to yourselves and by extension, to our guild. Even through the crisis, trade relations with them have improved immeasurably. Once maters of the cataclysm are resolved, I'm sure we will see a tidy profit--a direct result from your good work.")
    return
end)

RegisterGlobalEvent(584, "A bridge too far?", function()
    if not IsQBitSet(QBit(2)) then -- Activate Area 1 teleporters 5 and 6.
        evt.SimpleMessage("With the bridges destroyed by the eruption of the mountain of fire, we cannot get to the boat dock!  We are cut off from the mainland!")
        return
    end
    evt.SimpleMessage("You have repaired the Portals of Stone?  We are all in your debt.  If only it was safe to travel through the Abandoned Temple!  Well, at least we can attempt to get to the boat dock through there.")
    return
end)

RegisterGlobalEvent(585, "Travel between the Islands", function()
    if not IsQBitSet(QBit(2)) then -- Activate Area 1 teleporters 5 and 6.
        evt.SimpleMessage("We used to travel freely between the islands using the bridges.  These bridges were destroyed when the mountain of fire erupted.  Many families are trapped on the outer islands.  We don’t even know if the people who live there are still alive.")
        return
    end
    evt.SimpleMessage("With the Portals of Stone repaired, we can at least check on the outer islands and those who live there.  We are in your debt for fixing the Portals of Stone.")
    return
end)

RegisterGlobalEvent(586, "The boat dock", function()
    if not IsQBitSet(QBit(2)) then -- Activate Area 1 teleporters 5 and 6.
        evt.SimpleMessage("The boat dock on the northernmost island is the only way to travel between Dagger Wound and the mainland.  With the bridges destroyed, we cannot get to the boat dock and those arriving from Ravenshore cannot get to the village of Blood Drop!")
        return
    end
    evt.SimpleMessage("We can get to the boat docks?  But we have to go through the Abandoned Temple?  Well that's something.  At least we can get to the boats.")
    return
end)

RegisterGlobalEvent(587, "Kreegans", function()
    evt.SimpleMessage("Did you know I was their captive for over six years? At first, I thought they were devils from hell, but now I am not so sure. They looked like devils surely, but did not act as demons. No, I think they were but another type of monstrous race, like ogres or goblins. Regardless, devils or not, I am glad the world is rid of them!")
    return
end)

RegisterGlobalEvent(588, "Elemental Lords", function()
    evt.SimpleMessage("Catherine and I have had dealings with these \"lords\" of the elemental planes. I've never trusted them, and now it seems I am right. They were our recent allies against the Kreegans, but a few months later, we find ourselves at war with them here! In both cases I understand neither their reasons for helping or hindrance. They are fickle beings at best...\"treacherous\" is perhaps a better word for them.")
    return
end)

RegisterGlobalEvent(589, "Enroth", function()
    evt.SimpleMessage("I must say I'm looking forward to returning to my lands of Enroth. It has been so long since I've seen them, or my son, Prince Nicolai. He was just a lad when I saw him last and now he is nearly grown. Sir Humphrey was a good choice for regent, but the land has been too long without its king at the reins of state.")
    return
end)

RegisterGlobalEvent(590, "Erathia", function()
    evt.SimpleMessage("After we defeated the Kreegans in Erathia, I abdicated my throne into the regenthood of one of my generals, Morgan Kendal. I have left in his capable hands the task of choosing Erathia's new ruler. I'm sure this seems to be much to give up, but I am first and foremost, the queen of Enroth. We were sailing for there when the cataclysm struck, drawing us here.")
    return
end)

RegisterGlobalEvent(591, "Kreegans", function()
    evt.SimpleMessage("The Kreegans? They are no more; I am sure of it. After we put down Lucifer Kreegan, my armies scoured Eofol searching for any signs of their continued existence. We found none. No, the Kreegan infestation of our world is eliminated.")
    return
end)

RegisterGlobalEvent(592, "Elementals", function()
    evt.SimpleMessage("I fought alongside elementals in our campaigns against the Kreegan. I found them stalwart and loyal. I know Roland disagrees, but I cannot call their hostility here a case of fickleness. No, I think something else drives them to attack us--magic perhaps? You should speak with our sage, Xanthor. He has been studying the Destroyer's crystal. I'm sure he's come up with some theory by now.")
    return
end)

RegisterGlobalEvent(594, "Make Weapon", function()
    if HasItem(691) then -- Stalt-laced ore
        RemoveItem(691) -- Stalt-laced ore
        evt.GiveItem(6, ItemType.Weapon_)
        evt.SimpleMessage("Here's your weapon. If you find more ore, I'll be happy to make you more weapons.")
        return
    elseif HasItem(690) then -- Erudine-laced ore
        RemoveItem(690) -- Erudine-laced ore
        evt.GiveItem(5, ItemType.Weapon_)
        evt.SimpleMessage("Here's your weapon. If you find more ore, I'll be happy to make you more weapons.")
        return
    elseif HasItem(689) then -- Kergar-laced ore
        RemoveItem(689) -- Kergar-laced ore
        evt.GiveItem(4, ItemType.Weapon_)
        evt.SimpleMessage("Here's your weapon. If you find more ore, I'll be happy to make you more weapons.")
        return
    elseif HasItem(688) then -- Phylt-laced ore
        RemoveItem(688) -- Phylt-laced ore
        evt.GiveItem(3, ItemType.Weapon_)
        evt.SimpleMessage("Here's your weapon. If you find more ore, I'll be happy to make you more weapons.")
        return
    elseif HasItem(687) then -- Siertal-laced ore
        RemoveItem(687) -- Siertal-laced ore
        evt.GiveItem(2, ItemType.Weapon_)
        evt.SimpleMessage("Here's your weapon. If you find more ore, I'll be happy to make you more weapons.")
        return
    elseif HasItem(686) then -- Iron-laced ore
        RemoveItem(686) -- Iron-laced ore
        evt.GiveItem(1, ItemType.Weapon_)
        evt.SimpleMessage("Here's your weapon. If you find more ore, I'll be happy to make you more weapons.")
    else
        evt.SimpleMessage("You need ore for me to create weapons.  The better the ore, the better the weapon I can make.")
    end
    return
end)

RegisterGlobalEvent(595, "Make Armor", function()
    if HasItem(691) then -- Stalt-laced ore
        RemoveItem(691) -- Stalt-laced ore
        evt.GiveItem(6, ItemType.Armor_)
        evt.SimpleMessage("Here's your armor. If you find more ore, I'll be happy to make you more armor.")
        return
    elseif HasItem(690) then -- Erudine-laced ore
        RemoveItem(690) -- Erudine-laced ore
        evt.GiveItem(5, ItemType.Armor_)
        evt.SimpleMessage("Here's your armor. If you find more ore, I'll be happy to make you more armor.")
        return
    elseif HasItem(689) then -- Kergar-laced ore
        RemoveItem(689) -- Kergar-laced ore
        evt.GiveItem(4, ItemType.Armor_)
        evt.SimpleMessage("Here's your armor. If you find more ore, I'll be happy to make you more armor.")
        return
    elseif HasItem(688) then -- Phylt-laced ore
        RemoveItem(688) -- Phylt-laced ore
        evt.GiveItem(3, ItemType.Armor_)
        evt.SimpleMessage("Here's your armor. If you find more ore, I'll be happy to make you more armor.")
        return
    elseif HasItem(687) then -- Siertal-laced ore
        RemoveItem(687) -- Siertal-laced ore
        evt.GiveItem(2, ItemType.Armor_)
        evt.SimpleMessage("Here's your armor. If you find more ore, I'll be happy to make you more armor.")
        return
    elseif HasItem(686) then -- Iron-laced ore
        RemoveItem(686) -- Iron-laced ore
        evt.GiveItem(1, ItemType.Armor_)
        evt.SimpleMessage("Here's your armor. If you find more ore, I'll be happy to make you more armor.")
    else
        evt.SimpleMessage("You need ore for me to create armor.  The better the ore, the better the armor I can make.")
    end
    return
end)

RegisterGlobalEvent(596, "Make Item", function()
    if HasItem(691) then -- Stalt-laced ore
        RemoveItem(691) -- Stalt-laced ore
        evt.GiveItem(6, ItemType.Misc)
        evt.SimpleMessage("Here is your item. If you find more ore, I'll be happy to make you more items.")
        return
    elseif HasItem(690) then -- Erudine-laced ore
        RemoveItem(690) -- Erudine-laced ore
        evt.GiveItem(5, ItemType.Misc)
        evt.SimpleMessage("Here is your item. If you find more ore, I'll be happy to make you more items.")
        return
    elseif HasItem(689) then -- Kergar-laced ore
        RemoveItem(689) -- Kergar-laced ore
        evt.GiveItem(4, ItemType.Misc)
        evt.SimpleMessage("Here is your item. If you find more ore, I'll be happy to make you more items.")
        return
    elseif HasItem(688) then -- Phylt-laced ore
        RemoveItem(688) -- Phylt-laced ore
        evt.GiveItem(3, ItemType.Misc)
        evt.SimpleMessage("Here is your item. If you find more ore, I'll be happy to make you more items.")
        return
    elseif HasItem(687) then -- Siertal-laced ore
        RemoveItem(687) -- Siertal-laced ore
        evt.GiveItem(2, ItemType.Misc)
        evt.SimpleMessage("Here is your item. If you find more ore, I'll be happy to make you more items.")
        return
    elseif HasItem(686) then -- Iron-laced ore
        RemoveItem(686) -- Iron-laced ore
        evt.GiveItem(1, ItemType.Misc)
        evt.SimpleMessage("Here is your item. If you find more ore, I'll be happy to make you more items.")
    else
        evt.SimpleMessage("You need ore for me to create items.  The better the ore, the better the items I can make.")
    end
    return
end)

RegisterGlobalEvent(597, "Arcomage Tournament", function()
    if IsQBitSet(QBit(174)) then -- Won all Arcomage games
        evt.SimpleMessage("Congratulations!  You have become the Arcomage Champion!  The prize is waiting in the chest right outside my house.")
        ClearQBit(QBit(173)) -- Win a game of Arcomage in all eleven taverns, then return to Tonk Blueswan in Ravenshore.
        ClearQBit(QBit(174)) -- Won all Arcomage games
        evt.ForPlayer(Players.All)
        AddValue(Experience, 50000)
        SetQBit(QBit(175)) -- Finished ArcoMage Quest - Get the treasure
        SetAward(Award(41)) -- Arcomage Champion.
        evt.SetNPCGreeting(410, 0) -- Tonk Blueswan greeting cleared
        evt.SetNPCTopic(410, 1, 0) -- Tonk Blueswan topic 1 cleared
    elseif IsQBitSet(QBit(173)) then -- Win a game of Arcomage in all eleven taverns, then return to Tonk Blueswan in Ravenshore.
        evt.SimpleMessage("You must claim a victory at ALL 11 taverns.  Until you do, you cannot be declared Arcomage Champion.")
    else
        evt.SimpleMessage("To be declared Arcomage Champion, you must win a game of Arcomage in every tavern on, in, and under the continent of Jadame.  There are 11 such taverns sponsoring Arcomage events.  When you have accomplished this, return to me to claim the prize.")
        SetQBit(QBit(173)) -- Win a game of Arcomage in all eleven taverns, then return to Tonk Blueswan in Ravenshore.
    end
    return
end)

RegisterGlobalEvent(598, "Rock Spire", function()
    if not IsAtLeast(PerceptionSkill, 1) then
        SetValue(DiseasedYellow, 0)
        -- Missing legacy status text 806
        return
    end
    evt.SummonItem(35, 4010, 7736, 544, 1000, 1, false) -- Phirna Root
    evt.SummonItem(36, 4010, 7736, 544, 1000, 1, false) -- Widowsweep Berries
    evt.SummonItem(37, 4010, 7736, 544, 1000, 1, false) -- Mushrooms
    evt.SummonItem(38, 4010, 7736, 544, 1000, 1, false) -- Poppy Pod
    evt.SummonItem(39, 4010, 7736, 544, 1000, 1, false) -- Datura
    -- Missing legacy status text 805
    return
end)

RegisterGlobalEvent(654, "My Life", function()
    if not IsQBitSet(QBit(179)) then -- Quests 176-178 done.
        evt.SimpleMessage("Even as a lad I knew I had a special relationship with cheese. Why, my first memory is of nibbling a bit of farmer's cheddar from my mother's hand! From that day I knew it would be my passion to eat cheese, to know all of the endless variety of its tasty wonderment, and to search the world for rare and exotic cheese-stuff. And so have I made my life...and destiny.")
        return
    end
    evt.SimpleMessage("With the cheeses you have brought me, I have now eaten all of the world's known cheeses. Now none can say that I, Asael Fromago, am not history's most eminent connoisseur of cheese! None can compare to my glory! Ha-ha-ha…")
    return
end)

RegisterGlobalEvent(655, "Vori Cheese Masters", function()
    evt.SimpleMessage("There are no people more dedicated to cheesecraft than the august cheese masters of Vori. Otherwise known to be rather barbaric, the Vori Frost Giants are true emblems of the potential of civilized development--at least as far as cheese making is concerned. Did you know that they have forty-two different words for \"cheese.\"")
    return
end)

RegisterGlobalEvent(656, "Quest", function()
    if not IsQBitSet(QBit(176)) then -- Find a wheel of Frelandeau Cheese. Bring it to Asael Fromago in Alvar.
        evt.SimpleMessage("I have traveled to these lands to catalog its array of available cheese. My task is nearly complete, but there are yet three cheeses I have yet to sample. These are Frelandeau, Eldenbrie and Dunduck. I would reward highly any who could locate these rare and reputedly tasty culinary gems for me.")
        SetQBit(QBit(176)) -- Find a wheel of Frelandeau Cheese. Bring it to Asael Fromago in Alvar.
        SetQBit(QBit(177)) -- Find a log of Eldenbrie Cheese. Bring it to Asael Fromago in Alvar.
        SetQBit(QBit(178)) -- Find a ball of Dunduck Cheese. Bring it to Asael Fromago in Alvar.
        return
    end
    evt.ForPlayer(Players.All)
    if HasItem(658) then -- Wheel of Frelandeau
        if HasItem(659) then -- Log of Eldenbrie
            if HasItem(660) then -- Ball of Dunduck
                evt.SimpleMessage("Excellent! Give me the cheeses! I must consume them!\n\nAh….munch munch….frelandeau, exquisite….mmmm, and eldenbrie, wondrously smoky…and hmmm, dunduck…well, that's not very nice, is it?\n\nYou have made my Jadamean cheese cataloging safari a success! I can die a happy man! You have the humble thanks of a man of cheese. And here is your promised reward!")
                evt.ForPlayer(Players.Member0)
                AddValue(Gold, 25000)
                evt.ForPlayer(Players.All)
                AddValue(Experience, 20000)
                RemoveItem(658) -- Wheel of Frelandeau
                RemoveItem(659) -- Log of Eldenbrie
                RemoveItem(660) -- Ball of Dunduck
                SetAward(Award(42)) -- Retrieved three cheeses for Asael Fromago, the Cheese Connoisseur of Alvar.
                ClearQBit(QBit(176)) -- Find a wheel of Frelandeau Cheese. Bring it to Asael Fromago in Alvar.
                ClearQBit(QBit(177)) -- Find a log of Eldenbrie Cheese. Bring it to Asael Fromago in Alvar.
                ClearQBit(QBit(178)) -- Find a ball of Dunduck Cheese. Bring it to Asael Fromago in Alvar.
                SetQBit(QBit(179)) -- Quests 176-178 done.
                evt.SetNPCTopic(442, 2, 0) -- Asael Fromago topic 2 cleared
                return
            elseif HasItem(658) then -- Wheel of Frelandeau
                evt.SimpleMessage("Very good, you have found me some of the cheese I seek. But now I have my heart set on a full cheese tasting with all three cheeses eaten at once so I can savor them in comparison. Come back when you have then all. I will not take what you have now. I don't think I could resist sampling what you leave--and then the cheese tasting would be ruined!")
                return
            elseif HasItem(659) then -- Log of Eldenbrie
                evt.SimpleMessage("Very good, you have found me some of the cheese I seek. But now I have my heart set on a full cheese tasting with all three cheeses eaten at once so I can savor them in comparison. Come back when you have then all. I will not take what you have now. I don't think I could resist sampling what you leave--and then the cheese tasting would be ruined!")
                return
            elseif HasItem(660) then -- Ball of Dunduck
                evt.SimpleMessage("Very good, you have found me some of the cheese I seek. But now I have my heart set on a full cheese tasting with all three cheeses eaten at once so I can savor them in comparison. Come back when you have then all. I will not take what you have now. I don't think I could resist sampling what you leave--and then the cheese tasting would be ruined!")
            else
                evt.SimpleMessage("You say you will find me the cheeses I desire, but here you are returned, empty-handed! Do not waste my precious time! Bring me cheese--Frelandeau, Eldenbrie and Dunduck! Do not return until you have them!")
            end
            return
        elseif HasItem(658) then -- Wheel of Frelandeau
            evt.SimpleMessage("Very good, you have found me some of the cheese I seek. But now I have my heart set on a full cheese tasting with all three cheeses eaten at once so I can savor them in comparison. Come back when you have then all. I will not take what you have now. I don't think I could resist sampling what you leave--and then the cheese tasting would be ruined!")
            return
        elseif HasItem(659) then -- Log of Eldenbrie
            evt.SimpleMessage("Very good, you have found me some of the cheese I seek. But now I have my heart set on a full cheese tasting with all three cheeses eaten at once so I can savor them in comparison. Come back when you have then all. I will not take what you have now. I don't think I could resist sampling what you leave--and then the cheese tasting would be ruined!")
            return
        elseif HasItem(660) then -- Ball of Dunduck
            evt.SimpleMessage("Very good, you have found me some of the cheese I seek. But now I have my heart set on a full cheese tasting with all three cheeses eaten at once so I can savor them in comparison. Come back when you have then all. I will not take what you have now. I don't think I could resist sampling what you leave--and then the cheese tasting would be ruined!")
        else
            evt.SimpleMessage("You say you will find me the cheeses I desire, but here you are returned, empty-handed! Do not waste my precious time! Bring me cheese--Frelandeau, Eldenbrie and Dunduck! Do not return until you have them!")
        end
        return
    elseif HasItem(658) then -- Wheel of Frelandeau
        evt.SimpleMessage("Very good, you have found me some of the cheese I seek. But now I have my heart set on a full cheese tasting with all three cheeses eaten at once so I can savor them in comparison. Come back when you have then all. I will not take what you have now. I don't think I could resist sampling what you leave--and then the cheese tasting would be ruined!")
        return
    elseif HasItem(659) then -- Log of Eldenbrie
        evt.SimpleMessage("Very good, you have found me some of the cheese I seek. But now I have my heart set on a full cheese tasting with all three cheeses eaten at once so I can savor them in comparison. Come back when you have then all. I will not take what you have now. I don't think I could resist sampling what you leave--and then the cheese tasting would be ruined!")
        return
    elseif HasItem(660) then -- Ball of Dunduck
        evt.SimpleMessage("Very good, you have found me some of the cheese I seek. But now I have my heart set on a full cheese tasting with all three cheeses eaten at once so I can savor them in comparison. Come back when you have then all. I will not take what you have now. I don't think I could resist sampling what you leave--and then the cheese tasting would be ruined!")
    else
        evt.SimpleMessage("You say you will find me the cheeses I desire, but here you are returned, empty-handed! Do not waste my precious time! Bring me cheese--Frelandeau, Eldenbrie and Dunduck! Do not return until you have them!")
    end
    return
end)

RegisterGlobalEvent(657, "The Stranger", function()
    evt.SimpleMessage("The night the stranger came through here was the same night that the crystal erupted in the center of town.  I only caught a glimpse of the stranger.  He didn’t appear the potent mage that he was.  I was not in the town square when he summoned the crystal, but I did see the flash of light that traveled across the sky.  It was truly a terrible night.")
    return
end)

RegisterGlobalEvent(658, "Night of the Crystal", function()
    evt.SimpleMessage("A wanderer came into town.  Several ruffians sought to relieve this traveler of whatever wealth he possibly possessed. The wanderer barely paid any of them much notice.  With a small flick of his wrist all fell before him.  Then he walked to the town square and summoned the giant crystal that you'll find there today.")
    return
end)

RegisterGlobalEvent(659, "The Crystal", function()
    evt.SimpleMessage("There is an ancient saying among the Dark Elf people,  \"a thing lives only as long as the last person who remembers it.\"  The events the night the crystal burst forth into our lives will live for a very long time.  Many of us saw the events of that night.  The mage who summoned forth the crystal said not one word to anyone us.  When he looked upon us, it seemed that all there was in his heart and eyes was pity.")
    return
end)

RegisterGlobalEvent(660, "Wandering Mage", function()
    evt.SimpleMessage("When the mage came into town I didn’t think much of it.  This is Ravenshore.  Everyone who travels the roads of Jadame comes through here at some time or another.  I guess I should have paid more attention to him.  Seems he caused quite a stir in the town square.")
    return
end)

RegisterGlobalEvent(661, "Pirate Raids", function()
    evt.SimpleMessage("The Pirates of Regna own the seas.  No one can stand against them!  Several years ago, some fishing boat captains thought that they could sail to Erathia to get help dealing with the pirates.  We never saw or heard from them again.")
    return
end)

RegisterGlobalEvent(662, "Regnans", function()
    evt.SimpleMessage("The Regnans are the worst slime to ever set foot on the shore of Jadame. They keep the peoples of this continent from trading with Erathia and Enroth.  What choice do we have?  Even the Merchants of Alvar couldn’t muster a fleet to deal with the pirates.  Rumor says that there are smugglers around that have found ways around the pirate blockades.")
    return
end)

RegisterGlobalEvent(663, "Empire of the Endless Ocean", function()
    evt.SimpleMessage("The Regnans call themselves the Empire of the Endless Ocean--trying to make more of themselves than there really is.  All they are is bullies and bandits.  Of course, don’t tell them that I said that!")
    return
end)

RegisterGlobalEvent(664, "Ogres and Bandits", function()
    evt.SimpleMessage("Over the last few weeks there have been reports of bandits and Ogres robbing travelers on all of the major roads of Jadame. Times just seem to be getting worse.  Between the Regnan Pirates and these bandits it seems that no one is safe to travel by any means.")
    return
end)

RegisterGlobalEvent(665, "Overland Travel", function()
    evt.SimpleMessage("Several of the warriors got together to go take care of the ogres that were camping on the road to Ravenshore.  That’s when we first had word of the fortress they were constructing to the southwest of here.  Since the fortress was completed the roads to the south and west have not been safe.")
    return
end)

RegisterGlobalEvent(666, "Smugglers", function()
    evt.SimpleMessage("The Smuggler of Jadame may be a myth, but I think not.  The Merchants of Alvar seem to be able to send small amounts of goods away across the sea to Erathia and Enroth.  Yet they own no boats of their own.   This would seem to support the idea that there really are smugglers.  Now why they work for the merchants is beyond the likes of me.")
    return
end)

RegisterGlobalEvent(667, "Wererats!", function()
    evt.SimpleMessage("Wererats!  They are the worst of scum!  The pick through our trash at night!  Always scurrying around in the dark!  Never seen when the sun is up.  Gives one the shivers it does!")
    return
end)

RegisterGlobalEvent(668, "Cyclopes of Ironsand", function()
    evt.SimpleMessage("The Cyclopes that dwell to the southeast of here have always been a threat to the village of Rust!  But the village has always been able to push back any raid.  They aren't so tough in small numbers, but if they can catch you out in the desert unaware, you will not survive!  ")
    return
end)

RegisterGlobalEvent(669, "Sea of Fire", function()
    evt.SimpleMessage("The sea of fire took us all by surprise.  It spread through the eastern half of the village like wildfire.  Luckily its growth seems to have slowed.  Still I don’t know how much longer any of us can last.")
    return
end)

RegisterGlobalEvent(670, "Find us a home!", function()
    evt.SimpleMessage("We need to find a new place to live!  There is no way any people could live under these conditions.  Even the Cyclopes will be forced to move.  There are legends that talk about the ancient homeland that we traveled here from.  The stories say that it was lush and green.  If we only had such a place to return to.")
    return
end)

RegisterGlobalEvent(671, "Ore Traders", function()
    evt.SimpleMessage("There are traders in Alvar and Shadowspire that trade for the different types of ore that can be found all over Jadame.  They use the ore to create items that they are more than happy to trade for more ore!")
    return
end)

RegisterGlobalEvent(672, "Vault of Time", function()
    evt.SimpleMessage("You know, it is said the Vault of Time was here before Ravenshore; the town was built around it. It is supposed to contain the treasure of the old Emperor Thorn who ruled the lands around here hundreds of years ago. Many come here to try and open the vault, but none succeed.")
    return
end)

RegisterGlobalEvent(673, "Renegade Dragons", function()
    evt.SimpleMessage("As if Quixote was not enough of a problem to plague us, we must also contend with Ilsingore, Ilsingore and Old Loeb--renegades among our kind! They think they can rebuild our race by scattering across Jadame and starting their own tribes. Fools! All they do is weaken us by removing themselves from our numbers. Yaardrake has fled to the Ironsand Desert. I know not where the others have gone.")
    return
end)

RegisterGlobalEvent(674, "Other Dragons", function()
    evt.SimpleMessage("While Garrote Gorge has the highest concentration of dragons in Jadame, I hear there is hunting to be had elsewhere. For instance, there is rumored to be a great old dragon out in the Ironsand Desert. Another is supposed to be somewhere in the badlands of Ravage Roaming.")
    return
end)

RegisterGlobalEvent(675, "Dragon on Regna", function()
    evt.SimpleMessage("When Charles Quixote brought us over from Erathia, we sailed past Regna Island. Since this was our first sight of Jadamean land on the voyage, it was an omen of our hunting expedition's future success that I saw an ancient dragon winging its way towards the island. How I wish I could get a spear in that one! It was the biggest dragon I'd ever seen!")
    return
end)

RegisterGlobalEvent(676, "The Destroyer", function()
    evt.SimpleMessage("Yes, I was here the day the Destroyer walked through Ravenshore! I was at the blacksmith's getting a knife sharpened. He walked right past us like he owned the town. A crowd was following him at a distance. One of them threw a rock, but it bounced off a magic shield surrounding him. He didn't even seem to notice. Later I heard an explosion from the town square. I ran out to look, but the Destroyer was gone and that crystal and scattered bodies were all that remained.")
    return
end)

RegisterGlobalEvent(677, "The Destroyer", function()
    evt.SimpleMessage("Yeah, I saw the \"Destroyer\" and well named he is! I thought he was a rich merchant, and he looked like easy prey, so I…well, I tried to rob him. I ran ahead of him and lay in ambush in an alley, waiting for him to pass. When he walked by, I made a grab for him. My mistake! I didn't even touch him! As soon as I got near him, I was thrown back by his magic. In fact, I was thrown over a house into the next street!")
    return
end)

RegisterGlobalEvent(678, "Temple of Eep", function()
    evt.SimpleMessage("Those cursed ratmen--those so-called \"Priests of Eep\"--are nothing but trouble. More like a pack of thieves than holy men, they are! I'll warn you, traveler. Keep an eye on your equipment when they're around. They'll steal anything that isn't nailed down.")
    return
end)

RegisterGlobalEvent(679, "Cheese", function()
    evt.SimpleMessage("Well, if you're looking for cheese, I daresay you will find it in the churches of Eep. You know mice like cheese. Well, this rule also applies to the ratmen of Eep. It is said that they keep a horde of the stuff in each of their temples.")
    return
end)

RegisterGlobalEvent(680, "Gralkor the Cruel", function()
    evt.SimpleMessage("On top of all of our problems here, the lord of our plane, Gralkor the Cruel is missing. He is a being of great power and could no doubt fight the dark magic which assails this plane.")
    return
end)

RegisterGlobalEvent(681, "Plane of Earth", function()
    evt.SimpleMessage("I wish I understood what has happened here. One day it was life as usual here…and this is normally a peaceful realm. Then suddenly everyone was howling with violent madness and was filled with a thirst to crush your land of Jadame. Even now my fellow Earth Plane denizens work single-mindedly to push the firmament of our realm into yours.")
    return
end)

RegisterGlobalEvent(682, "Shalwend", function()
    evt.SimpleMessage("Perhaps the reason I am not affected by the madness is that I carry with me an amulet given to me by the lord of this plane, Shalwend. It is said in our legends that he and the other elemental lords made your world. No doubt if Shalwend was here he could stop the creeping madness, but he is missing! Where is our lord in our time of greatest need?")
    return
end)

RegisterGlobalEvent(683, "Plane of Air", function()
    evt.SimpleMessage("It was clearly magic which caused the madness that has taken my fellow Plane of Air dwellers. On the day it struck there was instant chaos. All who were affected dropped what they were doing and began to howl. It was a chorus of horror! Only a handful of us maintain our sanity. Now, day by day, our glorious realm falls further and further towards a state of hellish decline.")
    return
end)

RegisterGlobalEvent(684, "Plane of Water", function()
    evt.SimpleMessage("I am not unschooled in the ways of magic. Clearly some spell of almost unimaginable power has affected those that live in this watery realm. My main curiosity is to know why this has occurred. Clearly no one would risk using such power if it was not to achieve some terrible end. All I know is that the Plane of Water makes war upon your realm. From here, I can discern no reason to it!")
    return
end)

RegisterGlobalEvent(685, "Acwalander", function()
    evt.SimpleMessage("W-what has h-happened to my home w-waters? All are c-consumed by m-m-madness! And worse, our l-lord is m-missing! Where is our r-ruler, th-the mighty Acw-w-walander! W-without him w-we are d-doomed!")
    return
end)

RegisterGlobalEvent(686, "Pyrannaste", function()
    evt.SimpleMessage("I know to your eyes, this plane must seem a hell-scape. But I tell you, normally it is not so. Before the madness we lived here together in a state of peace and harmony. But then, one day the madness fell and our Lord Pyrannaste was nowhere to be found. Perhaps his absence caused the madness? It may be so, he has never before been gone from this realm in my memory.")
    return
end)

RegisterGlobalEvent(687, "Plane of Fire", function()
    evt.SimpleMessage("Though the madness affects almost all of those that live here, it has not robbed them of their cunning. As I am sure you are aware, they make war on your realm, but it is not with crazed abandon that they do so. Leaders have emerged among the affected, and these make shrewd military designs against you. Even now they mass near the gateway to Jadame in preparation for a massive assault.")
    return
end)

RegisterGlobalEvent(688, "Adventure", function()
    if not IsQBitSet(QBit(19)) then -- Allied with Necromancers Guild. Steal Nightshade Brazier done.
        evt.SimpleMessage("I wish I could join with you. Sadly, our war with the Temple of the Sun takes up all of our time. The guild cannot spare me now.")
        return
    end
    evt.SimpleMessage("Well, now that things seem to be settled with our little war with the Temple of the Sun. Sandro has said that guild members may turn their attention to other matters. Since arriving in Jadame, I have seen little of it save for the lands of Shadowspire. Say...perhaps you could use my services!")
    evt.SetNPCTopic(466, 0, 617) -- Hevatia Deverbero topic 0: Roster Join Event
    return
end)

RegisterGlobalEvent(689, "Join with Us", function()
    if not IsQBitSet(QBit(20)) then -- Allied with Temple of the Sun. Destroy the Skeleton Transformer done.
        evt.SimpleMessage("I wish I could. Unfortunately, we make holy war with the foul Necromancers' Guild. All of the Sun Temple's resources, including myself, are dedicated to that cause.")
        return
    end
    evt.SimpleMessage("Yes! I would love to join with you. Now that our holy war against the foul Necromancers' Guild seems to be going well, I find I have little to do around here. I will go with you if you will take me.")
    evt.SetNPCTopic(467, 0, 618) -- Verish  topic 0: Roster Join Event
    return
end)

RegisterGlobalEvent(690, "Adventure", function()
    if not IsQBitSet(QBit(21)) then -- Allied with Charles Quioxte's Dragon Hunters. Return Dragon Egg to Quixote done.
        evt.SimpleMessage("Go with you? I think not. Why would I want to join up with a bunch of amateurs when I have all the action I can handle here? Don't make me laugh. What can you offer me that a life of Dragon hunting does not?")
        return
    end
    evt.SimpleMessage("Adventure with you? Yes I will. In fact, before he left, Charles Quixote suggested just that. \"Nelix,\" he said, \"if those alliance heroes come by, you ought to consider going with them.\" Apparently, he thinks highly of you. Well, his recommendation is enough for me. Shall we go?")
    evt.SetNPCTopic(468, 0, 619) -- Nelix Uriel topic 0: Roster Join Event
    return
end)

RegisterGlobalEvent(691, "Come with Us", function()
    if not IsQBitSet(QBit(34)) then -- Alliance Council formed. Quest 13 done.
        evt.SimpleMessage("Go with you? I like the idea, but I must stay here. I am one of the last veteran warriors left here. I must stay to protect the village.")
        return
    end
    evt.SimpleMessage("Yes, that sounds good. Though the village could use me to protect it, I think the best I could do for it would be to go with you. My people will be destroyed if the cataclysm is not ended. If I can do something to stop it, I should.")
    evt.SetNPCTopic(469, 0, 620) -- Sethrc Thistlebone topic 0: Roster Join Event
    return
end)

RegisterGlobalEvent(692, "Adventure", function()
    if not IsQBitSet(QBit(34)) then -- Alliance Council formed. Quest 13 done.
        evt.SimpleMessage("Join you? I must decline the offer. Though you have done a great service for my herd, I am not yet sure of your leadership. I want to help fight the cataclysm, but I'm not sure your way is the right one.")
        return
    end
    evt.SimpleMessage("Join your group? I would be glad to. Not only have you done a great service for my herd, it has become clear to me that your actions will decide our very survival.")
    evt.SetNPCTopic(470, 0, 621) -- Rionel topic 0: Roster Join Event
    return
end)

RegisterGlobalEvent(693, "Adventure", function()
    if not IsQBitSet(QBit(34)) then -- Alliance Council formed. Quest 13 done.
        evt.SimpleMessage("I see you too are adventurers. But…well, can I be frank? Though I don't doubt your potential, clearly you are not the most experienced group I've seen. I'd be happy to join you if you were more…shall we say, \"seasoned?\"")
        return
    end
    evt.SimpleMessage("Don't think your exploits have gone unnoticed! Clearly you are adventurers of the highest caliber. I would consider joining your team…that is, if you will have me.")
    evt.SetNPCTopic(471, 0, 622) -- Adric Stellare topic 0: Roster Join Event
    return
end)

RegisterGlobalEvent(694, "Go with Us", function()
    if not IsQBitSet(QBit(34)) then -- Alliance Council formed. Quest 13 done.
        evt.SimpleMessage("No. I am an elder vampire. To be clear, you're not worthy of me. I seek adventure, not to be your caretaker. I don't have the patience to teach you all the basics.")
        return
    end
    evt.SimpleMessage("Yes! Yes! An excellent idea. You are just the kind of companions I am seeking. I have heard of you and your adventures.")
    evt.SetNPCTopic(472, 0, 623) -- Infaustus  topic 0: Roster Join Event
    return
end)

RegisterGlobalEvent(695, "Come with Us", function()
    if not IsQBitSet(QBit(34)) then -- Alliance Council formed. Quest 13 done.
        evt.SimpleMessage("I think not. Now that I've had a chance to look at you, it is clear that you are not worthy of my company. I seek a group of greater renown.")
        return
    end
    evt.SimpleMessage("Yes, you seem worthy of my company. Very well, I will go if you will have me.")
    evt.SetNPCTopic(473, 0, 624) -- Brimstone topic 0: Join
    return
end)

RegisterGlobalEvent(696, "Join Us", function()
    if not IsQBitSet(QBit(38)) then -- Quest 36 is done.
        evt.SimpleMessage("You must be joking! I am a rightly famous knight. Why would I want to travel with such riff-raff as yourselves? Oh, it might be fun after a fashion, but I do have my reputation to think of.")
        return
    end
    evt.SimpleMessage("I must say I find the idea appealing. Hmmm, yes! The taste of the open road is just what I need. I have been long at this business of dragon slaying, and I must say it grows stale. A man must keep himself interested. I will go with you if you like.")
    evt.SetNPCTopic(476, 0, 627) -- Tempus  topic 0: Roster Join Event
    return
end)

RegisterGlobalEvent(697, "Join Us", function()
    if not IsQBitSet(QBit(38)) then -- Quest 36 is done.
        evt.SimpleMessage("Join you? Ho-ho. What an amusing idea. Why would the great Thorne Understone travel with the likes of you?")
        return
    end
    evt.SimpleMessage("Yes! That sounds great. From what I hear of your adventures you have a chance to know greatness. With my help, we could make that chance a certainty. Well, shall we? I'm always looking for a chance to add to my legend!")
    evt.SetNPCTopic(477, 0, 628) -- Thorne Understone topic 0: Roster Join Event
    return
end)

RegisterGlobalEvent(698, "Adventure", function()
    if not IsQBitSet(QBit(38)) then -- Quest 36 is done.
        evt.SimpleMessage("Yes, adventure is a fine thing. Why I have had several. In fact, let me tell you about the time I….Say, it just occurred to me you are suggesting I adventure with you! A nice offer, but well…how can I say this politely? You're just not seasoned enough. I'm afraid I would grow bored with the kinds of challenges you are ready to face.")
        return
    end
    evt.SimpleMessage("Ah, \"adventure.\" Surely I have not had enough of it recently. Since our war with the Frost Giants, I have done little but train young warriors. Say, you wouldn't happen to want a traveling companion? Perhaps I could come with you. I have many skills you might find useful, and I swing a deadly axe!")
    evt.SetNPCTopic(478, 0, 629) -- Ulbrecht topic 0: Roster Join Event
    return
end)

RegisterGlobalEvent(699, "Come with Us", function()
    if not IsQBitSet(QBit(38)) then -- Quest 36 is done.
        evt.SimpleMessage("Though I may not look it after my long sleep, know that you speak with one of the greatest vampires alive today. Go with you? I think not. Your inexperience would make you more of a hindrance to me than anything. I would do better on my own.")
        return
    end
    evt.SimpleMessage("Ah, you suggest I come along with you to see the land for myself. An excellent suggestion. I am certainly well rested enough! Very well, I am ready to travel if you will take me.")
    evt.SetNPCTopic(480, 0, 631) -- Artorius Veritas topic 0: Roster Join Event
    return
end)

RegisterGlobalEvent(700, "Join Us", function()
    if not IsQBitSet(QBit(38)) then -- Quest 36 is done.
        evt.SimpleMessage("Join you? What a fool's notion. I already travel with a certain number of fleas. I don't need any more parasites. Be gone!")
        return
    end
    evt.SimpleMessage("Join you! Ha! I admire your audacity. Yes…admire it a great deal. Very well. You have my respect. I will go with you.")
    evt.SetNPCTopic(481, 0, 632) -- Duroth the Eternal topic 0: Join
    return
end)

RegisterGlobalEvent(701, "The Family Tomb", function()
    evt.SimpleMessage("The Snapfinger family tomb is one of the lowest in our village's burial catacombs. Since we are such an honored family, our crypt is the largest. It isn't the easiest place to find--even I have become lost looking for it! When I do, I find it by keeping a hand on the right-side wall. I eventually get there.")
    return
end)

RegisterGlobalEvent(702, "Have you found the shield?", function()
    evt.SimpleMessage("Have you found the shield?  The recovery of Eclipse is very important to the Temple of the Sun!  You must help us find it!")
    return
end)
RegisterCanShowTopic(702, function()
    evt._BeginCanShowTopic(702)
    local visible = true
    if IsQBitSet(QBit(128)) then -- Recovered the the Shield, Eclipse for Lathius
        visible = false
        return visible
    else
        visible = true
        return visible
    end
end)

RegisterGlobalEvent(703, "Use Eclipse well!", function()
    evt.SimpleMessage("Thanks again for recovering the shield Eclipse!  I hope it has proven helpful in your adventures.")
    return
end)

RegisterGlobalEvent(706, "Come with Us", function()
    if not IsQBitSet(QBit(59)) then -- Returned to the Merchant guild in Alvar with overdune. Quest 25 done.
        evt.SimpleMessage("I'm sorry. I'd like to adventure, yes, but you're just not at my level.")
        return
    end
    evt.SimpleMessage("Sure, why not? I'm ready to go--just have to grab my gear! I'll show the guild who is worthy and who isn't!")
    evt.SetNPCTopic(458, 0, 609) -- Karanya Memoria topic 0: Roster Join Event
    return
end)

RegisterGlobalEvent(707, "Come with Us", function()
    if not IsQBitSet(QBit(59)) then -- Returned to the Merchant guild in Alvar with overdune. Quest 25 done.
        evt.SimpleMessage("No…no, that life is over for me. Besides, if I were to take up the mace again, it would be with other companions. I'm afraid--if I may speak bluntly--I just can't see myself traveling with a group as inexperienced as yours.")
        return
    end
    evt.SimpleMessage("Say, that sounds grand! Yes, I will go with you, if you will have me.")
    evt.SetNPCTopic(459, 0, 610) -- Maylander  topic 0: Roster Join Event
    return
end)

RegisterGlobalEvent(708, "Join Us", function()
    if not IsQBitSet(QBit(59)) then -- Returned to the Merchant guild in Alvar with overdune. Quest 25 done.
        evt.SimpleMessage("I think not! Why would I travel with the likes of you? Perhaps you didn't catch my name, \"Jasp Thelbourne?\" Yes, that \"Thelbourne,\" rabble. No, whatever you're up to, I'm not interested.")
        return
    end
    evt.SimpleMessage("Yes, we'd make quite a team! We have all done such great deeds, how could not further greatness follow from our joining together? I'll go with you if you want.")
    evt.SetNPCTopic(463, 0, 614) -- Jasp Thelbourne topic 0: Roster Join Event
    return
end)

RegisterGlobalEvent(709, "Ogre Raiders", function()
    if not IsQBitSet(QBit(67)) then -- I have killed all the oges in the ogre fort
        evt.SimpleMessage("I tell you, with all that's going on, it's like an honest merchant can't get business done! I mean, we've always had to deal with Ogre raiders, but now they've grown so bold as to have built a fort right here in Alvar! Now no caravans can take the west road to Murmurwoods. The worst of it is most of my trade with the Temple of the Sun there!")
        return
    end
    evt.SimpleMessage("You have done us all a great service by clearing out the Ogre's fort. Now our caravans can freely travel to Murmurwoods. I thank you…and my purse certainly thanks you!")
    return
end)

RegisterGlobalEvent(710, "Wasps", function()
    evt.SimpleMessage("Sure we have wasps in Alvar--and rather large ones, too--but we tolerate them for good reason. Many of our customers desire wasp products. Say…if you want to get in on the action, the trader, Veldon, is a broker for wasp parts. He lives here in town, and I hear he is currently trying to fill a large order for wasp stingers.")
    return
end)

RegisterGlobalEvent(711, "Trained Dragons", function()
    evt.SimpleMessage("Not many people know this, but it is possible to train a Dragon. It's sort of like breaking a horse, except that it requires more special equipment and a lot of magic. Those tame Dragons outside the fort are an example of my work. Right now they are loyal to us, but I will bond them to their ultimate customer, Fennis Greenwood, a minor lord back in Erathia. Well, I will do so as soon as he pays us, that is.")
    return
end)

RegisterGlobalEvent(712, "Zanthora", function()
    evt.SimpleMessage("Zanthora is a strange character. Not to say that members of the Necromancers' Guild are not all strange, but she is truly mad. I hear that other guild members simply refuse to work with her--so terrible are her experiments. Still, they value her dark genius. To keep her around, they built her a lab of her own out on the marshy wastes outside of town.")
    return
end)

RegisterGlobalEvent(713, "Vampire Crypt", function()
    evt.SimpleMessage("For the most part, the Necromancers' Guild has the local vampires under control…mostly. But there's one place you don't want to go! Most of them sleep in a communal crypt north of the guild. Watch out if you go there. They're a bit, shall we say…\"territorial.\"")
    return
end)

RegisterGlobalEvent(714, "The Guild", function()
    evt.SimpleMessage("The Necromancers' Guild? Hey, I think they're great. You should have seen this place before they came--nothing going on at all! Sure, we got vampires, skeletons and other undead running around. Still, I gotta say, things are sure a lot more lively around here!")
    return
end)

RegisterGlobalEvent(715, "Coffins", function()
    evt.SimpleMessage("As you might imagine, business is great. Oh, sure, the guild necromancers turn most of my customers into skeletons and zombies, but vampires are repeat business! Want a piece of the action? There's a wood dealer in town, Mylander, who is always looking for good Murmurwood lumber. If you have any he'll pay a pretty penny for it.")
    return
end)

RegisterGlobalEvent(716, "Lava Tunnel", function()
    evt.SimpleMessage("Hunting has become pretty hazardous of late, but still we must do it if we are to eat! Yesterday I was out along the western shore of the fire lake and found a tunnel that seems to go under the lake. I didn't explore it though. It was infested with gogs and worse...like everything else around here these days.")
    return
end)

RegisterGlobalEvent(717, "Navigation", function()
    evt.SimpleMessage("Even we who live here get lost. If you would not lose your way, follow the floating waystones. Ahhh…the madness returns….It returns!")
    return
end)

RegisterGlobalEvent(718, "The Easy Life", function()
    evt.SimpleMessage("Ah, I'm glad you're out saving the world. I mean, someone has to do it. Me, I'm for the easy life. As long as I got my boat and my pole, and the fish are biting, I don't see any reason to do much else. Good luck to you though!")
    return
end)

RegisterGlobalEvent(719, "Dread Pirate Stanley", function()
    evt.SimpleMessage("That Stanley, now there's a Regnan with some spark! Why I hear he's the one that got us in good with that thar Zog the Jackal--some sort of Ogre or giant Troll or something, I think--a genuine barbarian king. Now we got us our ships on the seas and a bunch of club swinging devils on the land. I tell ya, the Great and Mighty Regnan Empire is headed for greatness, what with the likes of the Dread Pirate Stanley doing for us!")
    return
end)

RegisterGlobalEvent(720, "Jadamean Smugglers", function()
    evt.SimpleMessage("Oh sure, we Regnans have to put up with a bit of competition--I'm talking about smugglers, you know--but I understand the Dread Pirate Stanley is putting the clamp on that. Why I understand he kidnapped Arion Hunter's family just so he can pressure the wererat into staying off our turf. ")
    return
end)

RegisterGlobalEvent(721, "Stanley's Treasure", function()
    evt.SimpleMessage("Yeah, I know the \"Dread\" Pirate Stanley is the hero of the moment around here, but I say, fah! Sure he's done a lot for Regna, but no man does anything that doesn't help himself. Why I hear old Stanley's been shaving off the top of every deal he's in--and that's a lot of deals! What I'd like to know is where he keeps his booty. Probably not on Regna, I reckon. It wouldn't be a fortnight before someone dug it up!")
    return
end)

RegisterGlobalEvent(722, "Hidden Treasure", function()
    evt.SimpleMessage("I have come up with a scheme for finding hidden treasure. Before you barged in, I was hard at work formulating a spell for sensing gold hidden beneath the ground. If I am successful, I plan to have a Dragon carry me over the wastelands of Ravage Roaming where the Dread Pirate Stanley's treasure is rumored to be buried. My spell will find it and I will be a wealthy man.")
    return
end)

RegisterGlobalEvent(723, "Burial Mound", function()
    evt.SimpleMessage("You mean the one just north of here? Well, none of us have anything to do with it. It's haunted!")
    return
end)

RegisterGlobalEvent(724, "Followers of Eep", function()
    evt.SimpleMessage("I don't know where they're at, but I know there's some of them ratmen around here somewhere. At night I hear all sorts of squeaking and scuffling outside. In the morning, pretty much everything that isn't under lock or bolted down is gone. If I knew where that Eep church was. I'd take some of my boys over for a little...talk.")
    return
end)

RegisterGlobalEvent(725, "Water Gateway", function()
    evt.SimpleMessage("I was out with one of the crews working along the new lake searching for things that were washed out of the lair. We think we found the source of the flood. There is a strange gateway out in the middle of the lake. We don't have any boats, so we didn't explore it, but even from the shore, it is clear to see that it leads to a watery realm.")
    return
end)

RegisterGlobalEvent(726, "Pirate Fortress", function()
    evt.SimpleMessage("Well, if you haven't been to the fortress, that's the first place you should go. As you are aware from your orientation, the so-called fortress on this island is just a front to fool our enemies. You'll need to make your way to the real fort on the crescent island. Just take the underground passage marked on your orientation map.")
    return
end)

RegisterGlobalEvent(727, "Regnan Culture", function()
    evt.SimpleMessage("I know they call us \"pirates\" on Jadame, but really, we're just running our empire. It is not our fault that our Jadamean subjects refuse to acknowledge our rule and do not pay their taxes. Since they do not pay, we're forced to collect tribute in the form of booty. Actually we prefer it this way--saves us the trouble of having to actually rule the continent.")
end)

RegisterGlobalEvent(728, "Nightshade Amulets", function()
    if not IsQBitSet(QBit(19)) then -- Allied with Necromancers Guild. Steal Nightshade Brazier done.
        evt.SimpleMessage("We vampires cannot normally walk about in the daylight, but Thant the Necromancers' Guildmaster has created an artifact to deal with this. A vampire wearing one of his Nightshade Amulets can move about freely day or night. Sadly, there are few available. I myself do not have one so must stay indoors during the day.")
        return
    end
    evt.SimpleMessage("Normally, we vampires need one of Thant's Nightshade Amulets to travel freely during the day, but since you've brought us the Nightshade Brazier, glorious night covers Shadowspire around the clock! Now those of us who don't have the amulets can walk about during the day...well, at least as long as we stay in the area.")
    return
end)

RegisterGlobalEvent(729, "Gaudy Jewelry", function()
    evt.SimpleMessage("Though it isn't my style, I must say a lot of folks around here like to cover themselves with all sorts of jewelry. They say it's fashion, but I just find it gaudy. Anyway, if you have any to sell go find Pavel in town. He does a brisk trade in all sorts of tacky junk.")
    return
end)

RegisterGlobalEvent(730, "Sunfish", function()
    evt.SimpleMessage("You looking for sunfish? Sorry, can't help you. Funny thing is, I had a whole catch of them just last week, but Pavel the merchant bought the whole lot. Maybe you can get them from him.")
    return
end)

RegisterGlobalEvent(731, "The Warehouse", function()
    evt.SimpleMessage("We have a small warehouse downstairs. You are free to use the chests there to store extra equipment. Put anything in there you don't want to wander off!")
    return
end)

RegisterGlobalEvent(732, "Hint", function()
    evt.ForPlayer(Players.All)
    if IsQBitSet(QBit(4)) then -- Letter from Q Bit 3 delivered.
        if not IsQBitSet(QBit(24)) then -- Received Reward from Elgar Fellmoon for completing quest 9.
            evt.SimpleMessage("I see a vision of you in which you take a letter from Elgar Fellmoon in Ravenshore to Arion Hunter, the leader of the Ravenshore smugglers. After this, you return to Fellmoon. The end of the vision is a blur, so you must not have lived entirely through it. Still, it is your fate to do these things.")
            SetAutonote(274) -- I see a vision of you in which you take a letter from Elgar Fellmoon in Ravenshore to Arion Hunter, the leader of the Ravenshore smugglers. After this, you return to Fellmoon. The end of the vision is a blur, so you must not have lived entirely through it. Still, it is your fate to do these things.
            return
        end
        if not IsQBitSet(QBit(12)) then -- Quest 11 is done.
            evt.SimpleMessage("I don't need my vision to tell me what you must do next. Do as Fellmoon asked of you. Go seek Bastian Loudrin, the guildmaster of the Alvarian Merchant Guild. He is in the city of Alvar.")
            SetAutonote(275) -- I don't need my vision to tell me what you must do next. Do as Fellmoon asked of you. Go seek Bastian Loudrin, the guildmaster of the Alvarian Merchant Guild. He is in the city of Alvar.
            return
        end
        if IsQBitSet(QBit(62)) then -- Vilebites Ashes (item603) placed in troll tomb.
            if not IsQBitSet(QBit(59)) then -- Returned to the Merchant guild in Alvar with overdune. Quest 25 done.
                evt.SimpleMessage("It is clear to me that you must bring the Troll, Overdune, to the merchant guild in Alvar.")
                SetAutonote(278) -- It is clear to me that you must bring the Troll, Overdune, to the merchant guild in Alvar.
                return
            end
            if IsQBitSet(QBit(34)) then -- Alliance Council formed. Quest 13 done.
                if IsQBitSet(QBit(57)) then -- The Pirates invaded Ravenshore
                    evt.SimpleMessage("In case you haven't heard, Ravenshore is under attack by the Regnan pirates. The town has been evacuated. You must eliminate the pirate threat before the alliance council will return to guide you.")
                    SetAutonote(285) -- In case you haven't heard, Ravenshore is under attack by the Regnan pirates. The town has been evacuated. You must eliminate the pirate threat before the alliance council will return to guide you.
                    return
                elseif IsQBitSet(QBit(37)) then -- Regnan Pirate Fleet is sunk.
                    if not IsQBitSet(QBit(38)) then -- Quest 36 is done.
                        evt.SimpleMessage("Now that you've sunk the Regnan fleet. Go and seek the wisdom of your alliance council. They will give you the next task that will make your destiny.")
                        SetAutonote(286) -- Now that you've sunk the Regnan fleet. Go and seek the wisdom of your alliance council. They will give you the next task that will make your destiny.
                        return
                    end
                    if IsQBitSet(QBit(92)) then -- Quest 91 done.
                        if IsQBitSet(QBit(45)) then -- Quests 41-44 done. Items from 41-44 given to XANTHOR.
                            if IsQBitSet(QBit(47)) then -- Quest 46 done. Used to allow entrance to elemental lord prisons. Now player needs item 629.
                                if IsQBitSet(QBit(228)) then -- You have seen the Endgame movie
                                    evt.SimpleMessage("The Balance is restored. Now that your destiny is made, I can no longer guide you--my sight only pertains to what is connected to the fate of Balance. What you do now is up to you. Good luck to you, Heroes of Jadame!")
                                    SetAutonote(295) -- The Balance is restored. Now that your destiny is made, I can no longer guide you--my sight only pertains to what is connected to the fate of Balance. What you do now is up to you. Good luck to you, Heroes of Jadame!
                                    return
                                elseif IsQBitSet(QBit(56)) then -- All Lords from quests 48, 50, 52, 54 rescued.
                                    evt.SimpleMessage("Seek out Xanthor! Though he is but a piece in the game of Balance, the next move you make towards destiny it through a meeting with him.")
                                    SetAutonote(294) -- Seek out Xanthor! Though he is but a piece in the game of Balance, the next move you make towards destiny it through a meeting with him.
                                else
                                    evt.SimpleMessage("Your path is clear to my vision. You must seek out the four elemental lords and release them from their prisons. These prisons are in the Destroyer's realm--the Plane Between Planes.")
                                    SetAutonote(293) -- Your path is clear to my vision. You must seek out the four elemental lords and release them from their prisons. These prisons are in the Destroyer's realm--the Plane Between Planes.
                                end
                                return
                            elseif IsQBitSet(QBit(235)) then -- Have talked to Escaton
                                evt.SimpleMessage("You have talked to the Destroyer, but have failed to gather from him the key which will unlock your future. Return to him and continue your conversations.")
                                SetAutonote(292) -- You have talked to the Destroyer, but have failed to gather from him the key which will unlock your future. Return to him and continue your conversations.
                            else
                                evt.SimpleMessage("Your destiny lies through the crystal gateway in Ravenshore. It will take you to the Plane Between Planes. There you will find the source of the elemental cataclysm.")
                                SetAutonote(291) -- Your destiny lies through the crystal gateway in Ravenshore. It will take you to the Plane Between Planes. There you will find the source of the elemental cataclysm.
                            end
                            return
                        elseif HasItem(606) then -- Heart of Fire
                            if HasItem(607) then -- Heart of Water
                                if HasItem(608) then -- Heart of Air
                                    if not HasItem(609) then -- Heart of Earth
                                        evt.SimpleMessage("It is clear that you must do as Xanthor has asked of you. Go to the four elemental planes and find in each, an elemental heartstone.")
                                        SetAutonote(289) -- It is clear that you must do as Xanthor has asked of you. Go to the four elemental planes and find in each, an elemental heartstone.
                                        return
                                    end
                                    evt.SimpleMessage("Now that you have the four elemental heartstones, you must now bring them to Xanthor in Ravenshore.")
                                    SetAutonote(290) -- Now that you have the four elemental heartstones, you must now bring them to Xanthor in Ravenshore.
                                    return
                                end
                            end
                            evt.SimpleMessage("It is clear that you must do as Xanthor has asked of you. Go to the four elemental planes and find in each, an elemental heartstone.")
                            SetAutonote(289) -- It is clear that you must do as Xanthor has asked of you. Go to the four elemental planes and find in each, an elemental heartstone.
                            return
                        else
                            evt.SimpleMessage("It is clear that you must do as Xanthor has asked of you. Go to the four elemental planes and find in each, an elemental heartstone.")
                            SetAutonote(289) -- It is clear that you must do as Xanthor has asked of you. Go to the four elemental planes and find in each, an elemental heartstone.
                            return
                        end
                    elseif IsQBitSet(QBit(91)) then -- Consult the Ironfists' court sage, Xanthor about the Ravenshore crystal. - Given by NPC 53 (Fellmoon), taken by XANTHOR.
                        evt.SimpleMessage("I see an important link between the present and your future has not been forged. Seek out the sage, Xanthor who resides in Ravenshore. He will send you on your destiny's next task.")
                        SetAutonote(288) -- I see an important link between the present and your future has not been forged. Seek out the sage, Xanthor who resides in Ravenshore. He will send you on your destiny's next task.
                    else
                        evt.SimpleMessage("You must speak to the Ironfists' court sage, Xanthor. He is housed in Ravenshore.")
                        SetAutonote(287) -- You must speak to the Ironfists' court sage, Xanthor. He is housed in Ravenshore.
                    end
                    return
                elseif IsQBitSet(QBit(36)) then -- Sink the Regnan Fleet. Return to the Ravenshore council chamber. - Given and taken at Ravenshore council chamber.
                    evt.SimpleMessage("You must do as the alliance council has asked of you. Find a way to Regna Island and sink the Regnan port fleet.")
                    SetAutonote(284) -- You must do as the alliance council has asked of you. Find a way to Regna Island and sink the Regnan port fleet.
                else
                    evt.SimpleMessage("I see an important connection has not been made between the present and your future destiny. You must return to the council chamber in the Ravenshore merchant guild. The councilors will send you on the next step down your road.")
                    SetAutonote(283) -- I see an important connection has not been made between the present and your future destiny. You must return to the council chamber in the Ravenshore merchant guild. The councilors will send you on the next step down your road.
                end
                return
            elseif IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
                if IsQBitSet(QBit(19)) then -- Allied with Necromancers Guild. Steal Nightshade Brazier done.
                    if IsQBitSet(QBit(21)) then -- Allied with Charles Quioxte's Dragon Hunters. Return Dragon Egg to Quixote done.
                        evt.SimpleMessage("You have done good work in forging the alliances you have. It is now time for you to seek the council of those allies you have brought together. Seek them out in their council chamber within the merchant guild in Ravenshore.")
                        SetAutonote(282) -- You have done good work in forging the alliances you have. It is now time for you to seek the council of those allies you have brought together. Seek them out in their council chamber within the merchant guild in Ravenshore.
                        return
                    elseif IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
                        evt.SimpleMessage("You have done good work in forging the alliances you have. It is now time for you to seek the council of those allies you have brought together. Seek them out in their council chamber within the merchant guild in Ravenshore.")
                        SetAutonote(282) -- You have done good work in forging the alliances you have. It is now time for you to seek the council of those allies you have brought together. Seek them out in their council chamber within the merchant guild in Ravenshore.
                    else
                        evt.SimpleMessage("There is great turmoil in the Balance. It has taken me some time to know its source, but I know it now. There is conflict between the Dragons and Knights who fight in Garrote Gorge. It is your destiny to ally with one of the two at the expense of the other.")
                        SetAutonote(281) -- There is great turmoil in the Balance. It has taken me some time to know its source, but I know it now. There is conflict between the Dragons and Knights who fight in Garrote Gorge. It is your destiny to ally with one of the two at the expense of the other.
                    end
                    return
                elseif IsQBitSet(QBit(20)) then -- Allied with Temple of the Sun. Destroy the Skeleton Transformer done.
                    if IsQBitSet(QBit(21)) then -- Allied with Charles Quioxte's Dragon Hunters. Return Dragon Egg to Quixote done.
                        evt.SimpleMessage("You have done good work in forging the alliances you have. It is now time for you to seek the council of those allies you have brought together. Seek them out in their council chamber within the merchant guild in Ravenshore.")
                        SetAutonote(282) -- You have done good work in forging the alliances you have. It is now time for you to seek the council of those allies you have brought together. Seek them out in their council chamber within the merchant guild in Ravenshore.
                        return
                    elseif IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
                        evt.SimpleMessage("You have done good work in forging the alliances you have. It is now time for you to seek the council of those allies you have brought together. Seek them out in their council chamber within the merchant guild in Ravenshore.")
                        SetAutonote(282) -- You have done good work in forging the alliances you have. It is now time for you to seek the council of those allies you have brought together. Seek them out in their council chamber within the merchant guild in Ravenshore.
                    else
                        evt.SimpleMessage("There is great turmoil in the Balance. It has taken me some time to know its source, but I know it now. There is conflict between the Dragons and Knights who fight in Garrote Gorge. It is your destiny to ally with one of the two at the expense of the other.")
                        SetAutonote(281) -- There is great turmoil in the Balance. It has taken me some time to know its source, but I know it now. There is conflict between the Dragons and Knights who fight in Garrote Gorge. It is your destiny to ally with one of the two at the expense of the other.
                    end
                else
                    evt.SimpleMessage("There is great turmoil in the Balance. It has taken me some time to know its source, but I know it now. It is caused by the war between the clerics of the Temple of the Sun located in Murmurwoods, and the Necromancers' Guild of Shadowspire. It is your destiny to undo the turmoil by choosing one of these two to ally with.")
                    SetAutonote(280) -- There is great turmoil in the Balance. It has taken me some time to know its source, but I know it now. It is caused by the war between the clerics of the Temple of the Sun located in Murmurwoods, and the Necromancers' Guild of Shadowspire. It is your destiny to undo the turmoil by choosing one of these two to ally with.
                end
            else
                evt.SimpleMessage("I see far through space today, but not through time. A great disaster has befallen the Minotaurs of Balthazar Lair in Ravage Roaming. I feel that your destiny is linked with their fate. You must rescue them from their peril.")
                SetAutonote(279) -- I see far through space today, but not through time. A great disaster has befallen the Minotaurs of Balthazar Lair in Ravage Roaming. I feel that your destiny is linked with their fate. You must rescue them from their peril.
            end
            return
        elseif IsQBitSet(QBit(25)) then -- Find a witness to the lake of fire's formation. Bring him back to the merchant guild in Alvar. - Given and taken by Bastian Lourdrin (area 3).
            evt.SimpleMessage("In my dreams last night, I saw you traveling to the Ironsand Desert to find a witness to the formation of a great lake of fire which formed there during the cataclysm.")
            SetAutonote(277) -- In my dreams last night, I saw you traveling to the Ironsand Desert to find a witness to the formation of a great lake of fire which formed there during the cataclysm.
        else
            evt.SimpleMessage("I see an important connection has not been made between the present and your future. You must return to Bastian Loudrin and continue your conversations with him. He will send you on the next step down your road.")
            SetAutonote(276) -- I see an important connection has not been made between the present and your future. You must return to Bastian Loudrin and continue your conversations with him. He will send you on the next step down your road.
        end
        return
    elseif IsQBitSet(QBit(3)) then -- Deliver Dadeross' Letter to Elgar Fellmoon at the Merchant House in Ravenshore. - Given by Dadeross in Dagger Wound. Taken by Fellmoon in Ravenshore.
        evt.SimpleMessage("Hmmm…I cannot look too far ahead--for the ether is thick today. All I see is that you must deliver the letter Dadeross gave you to the merchant, Elgar Fellmoon. Fellmoon lives in the city of Ravenshore.")
        SetAutonote(273) -- Hmmm�I cannot look too far ahead--for the ether is thick today. All I see is that you must deliver the letter Dadeross gave you to the merchant, Elgar Fellmoon. Fellmoon lives in the city of Ravenshore.
    else
        evt.SimpleMessage("You are employed by the Merchants of Alvar, yes? Well, I think you should speak with Dadeross, the leader of your caravan. My far seeing vision tells me he is on the Dagger Wound Islands.")
        SetAutonote(272) -- You are employed by the Merchants of Alvar, yes? Well, I think you should speak with Dadeross, the leader of your caravan. My far seeing vision tells me he is on the Dagger Wound Islands.
    end
    return
end)

RegisterGlobalEvent(733, "Promote Dark Elves", function()
    evt.ForPlayer(Players.Member0)
    if HasAward(Award(19)) then -- Promoted to Elf Patriarch.
        evt.SimpleMessage("Cauri told me of how you helped her with the curse of the Basilisk.  She has instructed me to promote any Dark Elves that travel with you to Patriarch.")
        ClearQBit(QBit(39)) -- Find Cauri Blackthorne then return to Dantillion in Murmurwoods with information of her location. - Dark Elf Promotion to Patriarch
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if IsAtLeast(ClassId, 10) then
                SetValue(ClassId, 11)
                SetAward(Award(19)) -- Promoted to Elf Patriarch.
            else
                SetAward(Award(20)) -- Rescued Cauri Blackthorne.
            end
        end
        return
    elseif HasAward(Award(20)) then -- Rescued Cauri Blackthorne.
        evt.SimpleMessage("Cauri told me of how you helped her with the curse of the Basilisk.  She has instructed me to promote any Dark Elves that travel with you to Patriarch.")
        ClearQBit(QBit(39)) -- Find Cauri Blackthorne then return to Dantillion in Murmurwoods with information of her location. - Dark Elf Promotion to Patriarch
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if IsAtLeast(ClassId, 10) then
                SetValue(ClassId, 11)
                SetAward(Award(19)) -- Promoted to Elf Patriarch.
            else
                SetAward(Award(20)) -- Rescued Cauri Blackthorne.
            end
        end
    else
        evt.SimpleMessage("You cannot be promoted until we know where Cauri Blackthorne is!  Locate her, and she will promote you.  After she is found and has retuned to the Merchant Guild, I will be glad to promote any Dark Elves in your party to Patriarch.")
    end
    return
end)

RegisterGlobalEvent(734, "Promote Trolls", function()
    evt.ForPlayer(Players.Member0)
    if HasAward(Award(21)) then -- Promoted to War Troll.
        evt.SimpleMessage("Before Volog left, he instructed me to promote any Trolls that travel with you to War Troll.  The village of Rust will be forever thankful to you!")
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if IsAtLeast(ClassId, 6) then
                SetValue(ClassId, 7)
                SetAward(Award(21)) -- Promoted to War Troll.
            else
                SetAward(Award(22)) -- Found Troll Homeland.
            end
        end
        return
    elseif HasAward(Award(22)) then -- Found Troll Homeland.
        evt.SimpleMessage("Before Volog left, he instructed me to promote any Trolls that travel with you to War Troll.  The village of Rust will be forever thankful to you!")
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if IsAtLeast(ClassId, 6) then
                SetValue(ClassId, 7)
                SetAward(Award(21)) -- Promoted to War Troll.
            else
                SetAward(Award(22)) -- Found Troll Homeland.
            end
        end
    else
        evt.SimpleMessage("You cannot be promoted until the Ancient Troll Home has been found!  Return here when you have found it and talk with Volog.")
    end
    return
end)

RegisterGlobalEvent(735, "Promote Knights", function()
    evt.ForPlayer(Players.Member0)
    if HasAward(Award(23)) then -- Promoted to Champion.
        evt.SimpleMessage("Thanks for you help recovering the spear Ebonest!  I can promote any Knights that travel with you to Champion.")
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if IsAtLeast(ClassId, 4) then
                SetValue(ClassId, 5)
                SetAward(Award(23)) -- Promoted to Champion.
            else
                SetAward(Award(24)) -- Returned Ebonest to Charles Quixote.
            end
        end
        return
    elseif HasAward(Award(24)) then -- Returned Ebonest to Charles Quixote.
        evt.SimpleMessage("Thanks for you help recovering the spear Ebonest!  I can promote any Knights that travel with you to Champion.")
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if IsAtLeast(ClassId, 4) then
                SetValue(ClassId, 5)
                SetAward(Award(23)) -- Promoted to Champion.
            else
                SetAward(Award(24)) -- Returned Ebonest to Charles Quixote.
            end
        end
    else
        evt.SimpleMessage("You cannot be promoted to Champion until you have proven yourself worthy!  ")
    end
    return
end)

RegisterGlobalEvent(736, "Promote Dragons", function()
    evt.ForPlayer(Players.Member0)
    if HasAward(Award(26)) then -- Promoted to Great Wyrm.
        evt.SimpleMessage("You have proven yourself and I will promote any Dragons that travel with you to Great Wyrm.")
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if IsAtLeast(ClassId, 14) then
                SetValue(ClassId, 15)
                SetAward(Award(26)) -- Promoted to Great Wyrm.
            else
                SetAward(Award(27)) -- Gave the Sword of Whistlebone the Slayer to the Deftclaw Redreaver.
            end
        end
        return
    elseif HasAward(Award(27)) then -- Gave the Sword of Whistlebone the Slayer to the Deftclaw Redreaver.
        evt.SimpleMessage("You have proven yourself and I will promote any Dragons that travel with you to Great Wyrm.")
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if IsAtLeast(ClassId, 14) then
                SetValue(ClassId, 15)
                SetAward(Award(26)) -- Promoted to Great Wyrm.
            else
                SetAward(Award(27)) -- Gave the Sword of Whistlebone the Slayer to the Deftclaw Redreaver.
            end
        end
    else
        evt.SimpleMessage("You have not proven yourself worthy!  Until you strike a blow against the Dragon Hunters, none of you will be promoted!")
    end
    return
end)

RegisterGlobalEvent(737, "Promote Clerics", function()
    evt.ForPlayer(Players.Member0)
    if HasAward(Award(30)) then -- Promoted to Cleric of the Sun.
        evt.SimpleMessage("You are always welcome here!  Of course I will promote any Clerics that travel with you to Priest of the Sun!  ")
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if IsAtLeast(ClassId, 2) then
                SetValue(ClassId, 3)
                SetAward(Award(30)) -- Promoted to Cleric of the Sun.
            else
                SetAward(Award(31)) -- Found the lost Prophecies of the Sun and returned them to the Temple of the Sun.
            end
        end
        return
    elseif HasAward(Award(31)) then -- Found the lost Prophecies of the Sun and returned them to the Temple of the Sun.
        evt.SimpleMessage("You are always welcome here!  Of course I will promote any Clerics that travel with you to Priest of the Sun!  ")
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if IsAtLeast(ClassId, 2) then
                SetValue(ClassId, 3)
                SetAward(Award(30)) -- Promoted to Cleric of the Sun.
            else
                SetAward(Award(31)) -- Found the lost Prophecies of the Sun and returned them to the Temple of the Sun.
            end
        end
    else
        evt.SimpleMessage("You cannot be promoted to Priest of the Sun until you have recovered the Prophecies of the Sun!")
    end
    return
end)

RegisterGlobalEvent(738, "Promote Necromancers", function()
    evt.ForPlayer(Players.Member0)
    if HasAward(Award(34)) then -- Promoted to Lich.
        evt.SimpleMessage("Ah, you return seeking promotion for others in your party?  I have not forgotten your help in recovering the Lost Book of Kehl!  All Necromancers in your party will be promoted to Lich.  Be sure each Necromancer has a Lich Jar in his possession.")
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if not IsAtLeast(ClassId, 0) then
                if not HasItem(628) then -- Lich Jar
                    evt.SimpleMessage("You have the Lost Book of Khel, however you lack the Lich Jars needed to complete the transformation!  Return here when you have one for each necromancer in your party!")
                    return
                end
            end
        end
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if IsAtLeast(ClassId, 0) then
                SetValue(ClassId, 1)
                SetAward(Award(34)) -- Promoted to Lich.
                RemoveItem(628) -- Lich Jar
            else
                SetAward(Award(35)) -- Found the Lost Book of Khel.
            end
        end
        return
    elseif HasAward(Award(35)) then -- Found the Lost Book of Khel.
        evt.SimpleMessage("Ah, you return seeking promotion for others in your party?  I have not forgotten your help in recovering the Lost Book of Kehl!  All Necromancers in your party will be promoted to Lich.  Be sure each Necromancer has a Lich Jar in his possession.")
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if not IsAtLeast(ClassId, 0) then
                if not HasItem(628) then -- Lich Jar
                    evt.SimpleMessage("You have the Lost Book of Khel, however you lack the Lich Jars needed to complete the transformation!  Return here when you have one for each necromancer in your party!")
                    return
                end
            end
        end
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if IsAtLeast(ClassId, 0) then
                SetValue(ClassId, 1)
                SetAward(Award(34)) -- Promoted to Lich.
                RemoveItem(628) -- Lich Jar
            else
                SetAward(Award(35)) -- Found the Lost Book of Khel.
            end
        end
    else
        evt.SimpleMessage("You have not recovered the Lost Book of Kehl!  There will be no promotions until you return with the book!  Speak with Vetrinus Taleshire.")
    end
    return
end)

RegisterGlobalEvent(739, "Promote Vampires", function()
    evt.ForPlayer(Players.Member0)
    if HasAward(Award(32)) then -- Promoted to Nosferatu.
        evt.SimpleMessage("Any Vampires among you will be promoted to Nosferatu!  I remember those who helped in the recovery of the Remains of Korbu.")
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if IsAtLeast(ClassId, 12) then
                SetValue(ClassId, 13)
                SetAward(Award(32)) -- Promoted to Nosferatu.
            else
                SetAward(Award(33)) -- Found the Sarcophagus and Remains of Korbu.
            end
        end
        return
    elseif HasAward(Award(33)) then -- Found the Sarcophagus and Remains of Korbu.
        evt.SimpleMessage("Any Vampires among you will be promoted to Nosferatu!  I remember those who helped in the recovery of the Remains of Korbu.")
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if IsAtLeast(ClassId, 12) then
                SetValue(ClassId, 13)
                SetAward(Award(32)) -- Promoted to Nosferatu.
            else
                SetAward(Award(33)) -- Found the Sarcophagus and Remains of Korbu.
            end
        end
    else
        evt.SimpleMessage("You have not found Korbu and until you have I refuse to promote any of you!  Begone!")
    end
    return
end)

RegisterGlobalEvent(740, "Promote Minotuars", function()
    evt.ForPlayer(Players.Member0)
    if HasAward(Award(28)) then -- Promoted to Minotaur Lord.
        evt.SimpleMessage("The Herd of Masul is in debt to you.  Any Minotaurs in your party are promoted to Minotaur Lord!")
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if IsAtLeast(ClassId, 8) then
                SetValue(ClassId, 9)
                SetAward(Award(28)) -- Promoted to Minotaur Lord.
            else
                SetAward(Award(29)) -- Recovered Axe of Balthazar.
            end
        end
        return
    elseif HasAward(Award(29)) then -- Recovered Axe of Balthazar.
        evt.SimpleMessage("The Herd of Masul is in debt to you.  Any Minotaurs in your party are promoted to Minotaur Lord!")
        for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3, Players.Member4}) do
            evt.ForPlayer(player)
            if IsAtLeast(ClassId, 8) then
                SetValue(ClassId, 9)
                SetAward(Award(28)) -- Promoted to Minotaur Lord.
            else
                SetAward(Award(29)) -- Recovered Axe of Balthazar.
            end
        end
    else
        evt.SimpleMessage("You have not found the Axe of Balthazar!  You are not worthy of promotion!")
    end
    return
end)

RegisterGlobalEvent(741, "Thank you!", function()
    evt.SimpleMessage("My father sent you to rescue me?  I am grateful.  I will return to my father and let him know of your assistance!")
    evt.ForPlayer(Players.All)
    AddValue(Experience, 5000)
    evt.SetNPCTopic(285, 0, 0) -- Irabelle Hunter topic 0 cleared
    ClearQBit(QBit(119)) -- Rescue Arion Hunter's daughter from Ogre Fortress in Alvar.
    SetQBit(QBit(120)) -- Rescued Smuggler Leader's Familly
    return
end)
RegisterCanShowTopic(741, function()
    evt._BeginCanShowTopic(741)
    local visible = true
    if IsQBitSet(QBit(119)) then -- Rescue Arion Hunter's daughter from Ogre Fortress in Alvar.
        visible = true
        return visible
    else
        visible = false
        return visible
    end
end)

RegisterGlobalEvent(742, "Travel with you!", function()
    if not IsQBitSet(QBit(37)) then -- Regnan Pirate Fleet is sunk.
        evt.SimpleMessage("I cannot yet travel with you!  I would sooner sign on with a merchant caravan, than travel with you.  Return to me when you have discovered more of the world, and your place in it.")
        return
    end
    evt.SimpleMessage("I remember you!  The Book of Kehl has proven invaluable, and it would be a privilege to travel with you.")
    evt.SetNPCTopic(74, 0, 625) -- Vetrinus Taleshire topic 0: Roster Join Event
    return
end)

RegisterGlobalEvent(743, "Travel with you!", function()
    if not IsQBitSet(QBit(37)) then -- Regnan Pirate Fleet is sunk.
        evt.SimpleMessage("When you have grown and learned more of the ways of the world, then it would be my pleasure to travel with you.  Until then I have studies to complete here.")
        return
    end
    evt.SimpleMessage("Certainly!  Traveling with you would be an honor!")
    evt.SetNPCTopic(63, 0, 626) -- Dervish Chevron topic 0: Roster Join Event
    return
end)

RegisterGlobalEvent(744, "Rescue", function()
    evt.SimpleMessage("You have done us a great service, adventurers. On behalf of my herd, I give you our humblest thanks. Know that the Minotaurs of Balthazar Lair hold you in the highest regard. You will always be welcome among us.")
    evt.SetNPCTopic(70, 0, 613) -- Thanys topic 0: Roster Join Event
    evt.SetNPCTopic(70, 1, 0) -- Thanys topic 1 cleared
    evt.SetNPCTopic(70, 2, 0) -- Thanys topic 2 cleared
    return
end)

