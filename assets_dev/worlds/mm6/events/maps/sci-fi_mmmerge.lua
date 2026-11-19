-- MMMerge map supplement: Control Center blaster training terminal.

ReplaceMapEvent(61, "Computer Terminal", function()
    evt.SetTexture(2927, "trekscon")
    SetQBit(QBit(1300)) -- Control Center blaster terminal was read.

    for playerIndex = 0, evt.GetPartyMemberCount() - 1 do
        evt.ForPlayer(playerIndex)

        if not IsAtLeast(BlasterSkill, 1) then
            SetValue(BlasterSkill, 1)
        end
    end

    evt.SimpleMessage(
        "\"Blaster weapons provide an effective, accurate ranged attack.  To operate the blaster, hold the grip " ..
        "comfortably in your hand, point the barrel at your target, and gently squeeze the trigger.  Should the " ..
        "weapon misfire, do not look into the barrel- give the weapon to an instructor and let them fix the problem.  " ..
        "Never point a blaster at something you do not want to vaporize.\"")
end, "Computer Terminal")

-- These three legacy messages contain CP1252 punctuation. Keep their UTF-8 text
-- here so exact localization keys can match without changing generated Lua.

ReplaceMapEvent(55, "Computer Terminal", function(continueStep)
    if continueStep ~= nil then return end
    evt.SetTexture(2930, "trekscon")
    evt.SetMessage("\"The room to your left is the main meeting hall.  Visiting dignitaries from around the world have feasted at banquets held in their honor.  In fact, it is said that at his 21st birthday party King Sheridan nearly choked to death on a piece of mogred, but was saved by a serving girl who he later married and made his Queen.  Ahh, l’amour.\"")
    evt._PressAnyKey(55, 3)
end, "Computer Terminal")

ReplaceMapEvent(56, "Computer Terminal", function(continueStep)
    if continueStep ~= nil then return end
    evt.SetTexture(2905, "trekscon")
    evt.SetMessage("\"Chief Engineer Wilson’s Personal Log.  I have locked myself in Storage Room #6 but currently have no means of escape.  The drone-bots have gone mad and have started killing everyone in sight.  I was able to access the main control terminal on Level Four despite warnings of a hazardous leak, and I sent a distress signal, but since we have not had contact with any of the colonies for several weeks, I do not believe that a rescue is possible.  I have also managed to seal this facility so that the drones can not escape.  It is my hope that the colonists will be able to mount some sort of defense by the time my encryption codes are broken.  Tell Emma I love her.  Wilson out.\"")
    evt._PressAnyKey(56, 3)
end, "Computer Terminal")

ReplaceMapEvent(60, "Computer Terminal", function(continueStep)
    if continueStep ~= nil then return end
    evt.SetTexture(2933, "trekscon")
    evt.SetMessage("\"Warning, intruder alert, Level Four, Section.  All drones proceed to Level Four to intercept intruders.  Reactor is offline.  Encryption integrity at 2.064%.  Warning, intruder alert, Level Four…\"")
    evt._PressAnyKey(60, 3)
end, "Computer Terminal")
