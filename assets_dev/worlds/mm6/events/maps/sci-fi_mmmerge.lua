-- MMMerge map supplement: Control Center blaster training terminal.

ReplaceMapEvent(61, "Computer Terminal", function()
    evt.SetTexture(-2912, "trekscon")
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
