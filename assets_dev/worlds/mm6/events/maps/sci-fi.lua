-- Control Center
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [29] = {0},
    [30] = {1},
    [31] = {2},
    [32] = {3},
    [33] = {4},
    [34] = {5},
    [35] = {6},
    [36] = {7},
    [37] = {8},
    [65] = {9},
    [66] = {10},
    [67] = {11},
    [68] = {12},
    [69] = {13},
    },
    textureNames = {"trekscon"},
    spriteNames = {},
    castSpellIds = {15},
    timers = {
    { eventId = 71, repeating = true, intervalGameMinutes = 1.5, remainingGameMinutes = 1.5 },
    },
})

RegisterEvent(1, "Door", function()
    evt.StatusText("The door won't budge.")
end, "Door")

RegisterEvent(2, "Door", function()
    evt.SetDoorState(2, DoorAction.Trigger)
    evt.SetDoorState(3, DoorAction.Trigger)
    evt.SetDoorState(15, DoorAction.Open)
    evt.SetDoorState(16, DoorAction.Open)
end, "Door")

RegisterEvent(3, "Door", function()
    evt.SetDoorState(3, DoorAction.Close)
end, "Door")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(4, DoorAction.Close)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(5, DoorAction.Close)
end, "Door")

RegisterEvent(6, "Door", function()
    evt.SetDoorState(6, DoorAction.Close)
end, "Door")

RegisterEvent(7, "Door", function()
    evt.SetDoorState(7, DoorAction.Close)
    evt.SetDoorState(8, DoorAction.Open)
    evt.SetDoorState(9, DoorAction.Open)
end, "Door")

RegisterEvent(8, "Door", function()
    evt.SetDoorState(8, DoorAction.Close)
    evt.SetDoorState(7, DoorAction.Open)
    evt.SetDoorState(9, DoorAction.Open)
end, "Door")

RegisterEvent(9, "Door", function()
    evt.SetDoorState(9, DoorAction.Close)
    evt.SetDoorState(8, DoorAction.Open)
    evt.SetDoorState(7, DoorAction.Open)
end, "Door")

RegisterEvent(10, "Door", function()
    evt.SetDoorState(10, DoorAction.Close)
    evt.SetDoorState(11, DoorAction.Close)
end, "Door")

RegisterEvent(11, "Door", function()
    evt.SetDoorState(10, DoorAction.Close)
    evt.SetDoorState(11, DoorAction.Close)
end, "Door")

RegisterEvent(12, "Door", function()
    evt.SetDoorState(12, DoorAction.Close)
end, "Door")

RegisterEvent(13, "Door", function()
    evt.SetDoorState(13, DoorAction.Close)
end, "Door")

RegisterEvent(14, "Door", function()
    evt.SetDoorState(14, DoorAction.Close)
end, "Door")

RegisterEvent(15, "Door", function()
    evt.SetDoorState(15, DoorAction.Trigger)
    evt.SetDoorState(16, DoorAction.Trigger)
    evt.SetDoorState(2, DoorAction.Open)
    evt.SetDoorState(3, DoorAction.Open)
end, "Door")

RegisterEvent(16, "Door", function()
    evt.SetDoorState(16, DoorAction.Close)
end, "Door")

RegisterEvent(17, "Door", function()
    evt.SetDoorState(17, DoorAction.Close)
end, "Door")

RegisterEvent(18, "Door", function()
    evt.SetDoorState(18, DoorAction.Close)
end, "Door")

RegisterEvent(19, "Door", function()
    evt.SetDoorState(19, DoorAction.Close)
end, "Door")

RegisterEvent(20, "Door", function()
    evt.SetDoorState(20, DoorAction.Close)
end, "Door")

RegisterEvent(21, "Door", function()
    evt.SetDoorState(21, DoorAction.Close)
end, "Door")

RegisterEvent(22, "Door", function()
    evt.SetDoorState(22, DoorAction.Close)
end, "Door")

RegisterEvent(23, "Door", function()
    evt.SetDoorState(23, DoorAction.Close)
end, "Door")

RegisterEvent(24, "Door", function()
    evt.SetDoorState(24, DoorAction.Trigger)
    evt.SetDoorState(25, DoorAction.Trigger)
end, "Door")

RegisterEvent(25, "Door", function()
    evt.SetDoorState(25, DoorAction.Close)
end, "Door")

RegisterEvent(26, "Door", function()
    evt.SetDoorState(26, DoorAction.Trigger)
    evt.SetDoorState(1, DoorAction.Trigger)
end, "Door")

RegisterEvent(27, "Door", function()
    evt.SetDoorState(27, DoorAction.Trigger)
    evt.SetDoorState(28, DoorAction.Trigger)
end, "Door")

RegisterEvent(28, "Door", function()
    evt.SetDoorState(28, DoorAction.Close)
    evt.SetDoorState(27, DoorAction.Close)
end, "Door")

RegisterEvent(29, "Storage Container", function()
    evt.OpenChest(0)
end, "Storage Container")

RegisterEvent(30, "Storage Container", function()
    evt.OpenChest(1)
end, "Storage Container")

RegisterEvent(31, "Storage Container", function()
    evt.OpenChest(2)
end, "Storage Container")

RegisterEvent(32, "Storage Container", function()
    evt.OpenChest(3)
end, "Storage Container")

RegisterEvent(33, "Storage Container", function()
    evt.OpenChest(4)
end, "Storage Container")

RegisterEvent(34, "Storage Container", function()
    evt.OpenChest(5)
    evt.ForPlayer(Players.All)
    SetAward(Award(103)) -- Super-Goober
end, "Storage Container")

RegisterEvent(35, "Storage Container", function()
    evt.OpenChest(6)
end, "Storage Container")

RegisterEvent(36, "Storage Container", function()
    evt.OpenChest(7)
end, "Storage Container")

RegisterEvent(37, "Storage Container", function()
    evt.OpenChest(8)
end, "Storage Container")

RegisterEvent(38, "Legacy event 38", function()
    evt.SetLight(45, 1)
    evt.SetLight(46, 1)
    evt.SetLight(47, 1)
    evt.SetLight(48, 1)
    evt.SetLight(49, 1)
end)

RegisterEvent(39, "Legacy event 39", function()
    evt.SetLight(31, 1)
    evt.SetLight(32, 1)
    evt.SetLight(33, 1)
    evt.SetLight(34, 1)
    evt.SetLight(35, 1)
    evt.SetLight(36, 1)
    evt.SetLight(37, 1)
    evt.SetLight(38, 1)
    evt.SetLight(39, 1)
    evt.SetLight(40, 1)
    evt.SetLight(41, 1)
    evt.SetLight(42, 1)
    evt.SetLight(43, 1)
    evt.SetLight(44, 1)
    evt.SetLight(391, 1)
end)

RegisterEvent(40, "Legacy event 40", function()
    evt.SetLight(50, 1)
    evt.SetLight(51, 1)
    evt.SetLight(52, 1)
    evt.SetLight(53, 1)
    evt.SetLight(54, 1)
    evt.SetLight(55, 1)
    evt.SetLight(56, 1)
    evt.SetLight(57, 1)
    evt.SetLight(58, 1)
    evt.SetLight(59, 1)
end)

RegisterEvent(41, "Legacy event 41", function()
    evt.SetLight(60, 1)
    evt.SetLight(61, 1)
    evt.SetLight(62, 1)
    evt.SetLight(63, 1)
    evt.SetLight(64, 1)
    evt.SetLight(65, 1)
    evt.SetLight(66, 1)
    evt.SetLight(67, 1)
end)

RegisterEvent(42, "Legacy event 42", function()
    evt.SetLight(68, 1)
    evt.SetLight(69, 1)
    evt.SetLight(70, 1)
    evt.SetLight(71, 1)
    evt.SetLight(72, 1)
    evt.SetLight(73, 1)
    evt.SetLight(74, 1)
    evt.SetLight(75, 1)
end)

RegisterEvent(43, "Legacy event 43", function()
    evt.SetLight(77, 1)
    evt.SetLight(78, 1)
    evt.SetLight(79, 1)
end)

RegisterEvent(44, "Legacy event 44", function()
    evt.SetLight(389, 1)
    evt.SetLight(390, 1)
end)

RegisterEvent(45, "Legacy event 45", function()
    evt.SetLight(45, 0)
    evt.SetLight(46, 0)
    evt.SetLight(47, 0)
    evt.SetLight(48, 0)
    evt.SetLight(49, 0)
end)

RegisterEvent(46, "Legacy event 46", function()
    evt.SetLight(45, 0)
    evt.SetLight(46, 0)
    evt.SetLight(47, 0)
    evt.SetLight(48, 0)
    evt.SetLight(49, 0)
    evt.SetLight(31, 0)
    evt.SetLight(32, 0)
    evt.SetLight(33, 0)
    evt.SetLight(34, 0)
    evt.SetLight(35, 0)
    evt.SetLight(36, 0)
    evt.SetLight(37, 0)
    evt.SetLight(38, 0)
    evt.SetLight(39, 0)
    evt.SetLight(40, 0)
    evt.SetLight(41, 0)
    evt.SetLight(42, 0)
    evt.SetLight(43, 0)
    evt.SetLight(44, 0)
    evt.SetLight(391, 0)
end)

RegisterEvent(47, "Legacy event 47", function()
    evt.SetLight(31, 0)
    evt.SetLight(32, 0)
    evt.SetLight(33, 0)
    evt.SetLight(34, 0)
    evt.SetLight(35, 0)
    evt.SetLight(36, 0)
    evt.SetLight(37, 0)
    evt.SetLight(38, 0)
    evt.SetLight(39, 0)
    evt.SetLight(40, 0)
    evt.SetLight(41, 0)
    evt.SetLight(42, 0)
    evt.SetLight(43, 0)
    evt.SetLight(44, 0)
    evt.SetLight(391, 0)
    evt.SetLight(50, 0)
    evt.SetLight(51, 0)
    evt.SetLight(52, 0)
    evt.SetLight(53, 0)
    evt.SetLight(54, 0)
    evt.SetLight(55, 0)
    evt.SetLight(56, 0)
    evt.SetLight(57, 0)
    evt.SetLight(58, 0)
    evt.SetLight(59, 0)
    evt.CastSpell(15, 100, 3, -10880, -4224, 660, -10880, -4224, 400) -- Sparks
end)

RegisterEvent(48, "Legacy event 48", function()
    evt.SetLight(50, 0)
    evt.SetLight(51, 0)
    evt.SetLight(52, 0)
    evt.SetLight(53, 0)
    evt.SetLight(54, 0)
    evt.SetLight(55, 0)
    evt.SetLight(56, 0)
    evt.SetLight(57, 0)
    evt.SetLight(58, 0)
    evt.SetLight(59, 0)
    evt.SetLight(60, 0)
    evt.SetLight(61, 0)
    evt.SetLight(62, 0)
    evt.SetLight(63, 0)
    evt.SetLight(64, 0)
    evt.SetLight(65, 0)
    evt.SetLight(66, 0)
    evt.SetLight(67, 0)
end)

RegisterEvent(49, "Legacy event 49", function()
    evt.SetLight(60, 0)
    evt.SetLight(61, 0)
    evt.SetLight(62, 0)
    evt.SetLight(63, 0)
    evt.SetLight(64, 0)
    evt.SetLight(65, 0)
    evt.SetLight(66, 0)
    evt.SetLight(67, 0)
    evt.SetLight(68, 0)
    evt.SetLight(69, 0)
    evt.SetLight(70, 0)
    evt.SetLight(71, 0)
    evt.SetLight(72, 0)
    evt.SetLight(73, 0)
    evt.SetLight(74, 0)
    evt.SetLight(75, 0)
end)

RegisterEvent(50, "Legacy event 50", function()
    evt.SetLight(68, 0)
    evt.SetLight(69, 0)
    evt.SetLight(70, 0)
    evt.SetLight(71, 0)
    evt.SetLight(72, 0)
    evt.SetLight(73, 0)
    evt.SetLight(74, 0)
    evt.SetLight(75, 0)
    evt.SetLight(77, 0)
    evt.SetLight(78, 0)
    evt.SetLight(79, 0)
end)

RegisterEvent(51, "Legacy event 51", function()
    evt.SetLight(77, 0)
    evt.SetLight(78, 0)
    evt.SetLight(79, 0)
    evt.SetLight(389, 0)
    evt.SetLight(390, 0)
end)

RegisterEvent(52, "Legacy event 52", function()
    evt.SetLight(389, 0)
    evt.SetLight(390, 0)
end)

RegisterEvent(53, "Computer Terminal", function()
    evt.SetTexture(2899, "trekscon")
    evt.SimpleMessage("\"Hello and welcome to this self-guided tour of the Varn Planetary Control Facility.  We gladly welcome all visitors.  As you arrive at each key area, be sure to check any of our display screens for more information.  Enjoy your tour!\"")
end, "Computer Terminal")

RegisterEvent(54, "Computer Terminal", function()
    evt.SetTexture(2903, "trekscon")
    evt.SimpleMessage("\"This is the main equipment storage and repair facility.  By now, you may have noticed several floating Drone-bots.  They are responsible both for maintaining the key systems of this facility as well as sanitation.  If a unit becomes damaged, it is brought here to be repaired.\"")
end, "Computer Terminal")

RegisterEvent(55, "Computer Terminal", function()
    evt.SetTexture(2930, "trekscon")
    evt.SimpleMessage("\"The room to your left is the main meeting hall.  Visiting dignitaries from around the world have feasted at banquets held in their honor.  In fact, it is said that at his 21st birthday party King Sheridan nearly choked to death on a piece of mogred, but was saved by a serving girl who he later married and made his Queen.  Ahh, l’amour.\"")
end, "Computer Terminal")

RegisterEvent(56, "Computer Terminal", function()
    evt.SetTexture(2905, "trekscon")
    evt.SimpleMessage("\"Chief Engineer Wilson’s Personal Log.  I have locked myself in Storage Room #6 but currently have no means of escape.  The drone-bots have gone mad and have started killing everyone in sight.  I was able to access the main control terminal on Level Four despite warnings of a hazardous leak, and I sent a distress signal, but since we have not had contact with any of the colonies for several weeks, I do not believe that a rescue is possible.  I have also managed to seal this facility so that the drones can not escape.  It is my hope that the colonists will be able to mount some sort of defense by the time my encryption codes are broken.  Tell Emma I love her.  Wilson out.\"")
end, "Computer Terminal")

RegisterEvent(57, "Computer Terminal", function()
    evt.SetTexture(2911, "trekscon")
    evt.SimpleMessage("\"We apologize for any inconvenience, but we ask that all personnel evacuate the facility at this time.  Please do not be alarmed.  Thank you.\"")
end, "Computer Terminal")

RegisterEvent(58, "Computer Terminal", function()
    evt.SetTexture(2914, "trekscon")
    evt.SimpleMessage("\"Before entering the Planetary Reaction Chamber, please request a pair of Safety Goggles from one of our Drones.  During peak hours of operation, this facility can generate enough power to produce a light bright enough to be seen from space.  Please avoid looking directly into the light.\"")
end, "Computer Terminal")

RegisterEvent(59, "Computer Terminal", function()
    evt.SetTexture(2921, "trekscon")
    evt.SimpleMessage("\"Alert, environmental controls are offline on Level Four, Sections 18 through 96.  Access restricted to drones until further notice.\"")
end, "Computer Terminal")

RegisterEvent(60, "Computer Terminal", function()
    evt.SetTexture(2933, "trekscon")
    evt.SimpleMessage("\"Warning, intruder alert, Level Four, Section.  All drones proceed to Level Four to intercept intruders.  Reactor is offline.  Encryption integrity at 2.064%.  Warning, intruder alert, Level Four…\"")
end, "Computer Terminal")

RegisterEvent(61, "Computer Terminal", function()
    evt.SetTexture(2927, "trekscon")
    SetQBit(QBit(1300)) -- NPC
    evt.SimpleMessage("\"Blaster weapons provide an effective, accurate ranged attack.  To operate the blaster, hold the grip comfortably in your hand, point the barrel at your target, and gently squeeze the trigger.  Should the weapon misfire, do not look into the barrel- give the weapon to an instructor and let them fix the problem.  Never point a blaster at something you do not want to vaporize.\"")
end, "Computer Terminal")

RegisterEvent(62, "Legacy event 62", function()
    evt.StatusText("It's a short circuit!")
    evt.DamagePlayer(6, 0, 200)
end)

RegisterEvent(63, "Legacy event 63", function()
    evt.StatusText("It's a short circuit!")
    evt.DamagePlayer(6, 0, 200)
end)

RegisterEvent(64, "Legacy event 64", function()
    evt.StatusText("It's a short circuit!")
    evt.DamagePlayer(6, 0, 200)
end)

RegisterEvent(65, "Storage Container", function()
    evt.OpenChest(9)
end, "Storage Container")

RegisterEvent(66, "Storage Container", function()
    evt.OpenChest(10)
end, "Storage Container")

RegisterEvent(67, "Storage Container", function()
    evt.OpenChest(11)
end, "Storage Container")

RegisterEvent(68, "Storage Container", function()
    evt.OpenChest(12)
end, "Storage Container")

RegisterEvent(69, "Storage Container", function()
    evt.OpenChest(13)
end, "Storage Container")

RegisterEvent(70, "Exit", function()
    evt.MoveToMap(-1433, 2204, -495, 1536, 0, 0, 0, 0, "oracle.blv")
end, "Exit")

RegisterEvent(71, "Legacy event 71", function()
    evt.CastSpell(15, 100, 3, -5632, -4736, 660, -5632, -4000, 660) -- Sparks
end)

