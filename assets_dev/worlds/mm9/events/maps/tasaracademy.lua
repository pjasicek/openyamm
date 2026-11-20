-- Ta'Sar Academy, MM9 rework (level_generation/projects/mm9r_tasaracademy/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {BookButtonBack1 = 1, BookButtonFront1 = 2, Door0 = 3, Door1 = 4, Door10 = 5, Door13 = 6, Door14 = 7, Door15 = 8, Door16 = 9, Door17 = 10, Door18 = 11, Door19 = 12, Door2 = 23, Door20 = 13, Door21 = 14, Door22 = 15, Door23 = 16, Door24 = 17, Door25 = 18, Door26 = 19, Door27 = 20, Door28 = 21, Door29 = 22, Door3 = 24, Door30 = 25, Door31 = 26, Door32 = 27, Door33 = 28, Door4 = 29, Door5 = 30, Door6 = 31, Door7 = 32, Door8 = 33, Door9 = 34, DoubleDoorL11 = 35, DoubleDoorR11 = 36, LibraryDoor = 37, PitDoorLeft1 = 38, PitDoorRight1 = 39, RotatingBookcase1 = 40, SecretDoor0 = 41, SecretDoor1 = 42, Switch = 43, Switch1 = 44}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}, [44] = {3}}})

local GROUPS = {BookButtonBack1 = {1}, BookButtonFront1 = {2}, D0_1 = {3, 4}, D10_13 = {5, 6}, D14_15 = {7, 8}, D16_17 = {9, 10}, D18_19 = {11, 12}, D20_21 = {13, 14}, D22_23 = {15, 16}, D24_25 = {17, 18}, D26_27 = {19, 20}, D28_29 = {21, 22}, D2_3 = {23, 24}, D30_31 = {25, 26}, D32_33 = {27, 28}, D4_5 = {29, 30}, D6_7 = {31, 32}, D8_9 = {33, 34}, DD11 = {35, 36}, LibraryDoor = {37}, PitDoor = {38, 39}, RotatingBookcase1 = {40}, SecretDoor0 = {41}, SecretDoor1 = {42}, Switch = {43}, Switch1 = {44}}
local function openGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Open) end end
local function closeGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Close) end end
local function toggleGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Trigger) end end
local function inBox(b, x, y, z) return x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] and z + 170 >= b[1][3] and z <= b[2][3] end
local function hurt(amount, kind) evt.DamagePlayer(Players.All, kind or const.Damage.Physical, amount) end
local function give(raw, source)
    local item = MM9.ItemIds[raw]
    if item ~= nil and evt.GivePartyMemberItem(math.max(0, evt.GetCurrentPlayerIndex()), item) then return true end
    return MM9.giveItem(raw, source)
end
local BOX = {PitDoorTrigger1 = {{1064, -5326, -20}, {1476, -4914, 20}}, Spikes = {{1106, -5284, -666}, {1434, -4956, -512}}, Trigger0 = {{3752, -2290, 28}, {4072, -1970, 284}}, Trigger1 = {{3782, -3596, 28}, {4102, -3276, 284}}, Trigger2 = {{1663, -3601, 28}, {1983, -3281, 284}}, Trigger3 = {{1652, -2295, 28}, {1972, -1975, 284}}, Trigger4 = {{7341, -1179, 0}, {7569, 196, 164}}}

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(3, DoorAction.Trigger) evt.SetDoorState(4, DoorAction.Trigger) end   -- D0_1
handlers[102] = function() evt.SetDoorState(5, DoorAction.Trigger) evt.SetDoorState(6, DoorAction.Trigger) end   -- D10_13
handlers[103] = function() evt.SetDoorState(7, DoorAction.Trigger) evt.SetDoorState(8, DoorAction.Trigger) end   -- D14_15
handlers[104] = function() evt.SetDoorState(9, DoorAction.Trigger) evt.SetDoorState(10, DoorAction.Trigger) end   -- D16_17
handlers[105] = function() evt.SetDoorState(11, DoorAction.Trigger) evt.SetDoorState(12, DoorAction.Trigger) end   -- D18_19
handlers[106] = function() evt.SetDoorState(13, DoorAction.Trigger) evt.SetDoorState(14, DoorAction.Trigger) end   -- D20_21
handlers[107] = function() evt.SetDoorState(15, DoorAction.Trigger) evt.SetDoorState(16, DoorAction.Trigger) end   -- D22_23
handlers[108] = function() evt.SetDoorState(17, DoorAction.Trigger) evt.SetDoorState(18, DoorAction.Trigger) end   -- D24_25
handlers[109] = function() evt.SetDoorState(19, DoorAction.Trigger) evt.SetDoorState(20, DoorAction.Trigger) end   -- D26_27
handlers[110] = function() evt.SetDoorState(21, DoorAction.Trigger) evt.SetDoorState(22, DoorAction.Trigger) end   -- D28_29
handlers[111] = function() evt.SetDoorState(23, DoorAction.Trigger) evt.SetDoorState(24, DoorAction.Trigger) end   -- D2_3
handlers[112] = function() evt.SetDoorState(25, DoorAction.Trigger) evt.SetDoorState(26, DoorAction.Trigger) end   -- D30_31
handlers[113] = function() evt.SetDoorState(27, DoorAction.Trigger) evt.SetDoorState(28, DoorAction.Trigger) end   -- D32_33
handlers[114] = function() evt.SetDoorState(29, DoorAction.Trigger) evt.SetDoorState(30, DoorAction.Trigger) end   -- D4_5
handlers[115] = function() evt.SetDoorState(31, DoorAction.Trigger) evt.SetDoorState(32, DoorAction.Trigger) end   -- D6_7
handlers[116] = function() evt.SetDoorState(33, DoorAction.Trigger) evt.SetDoorState(34, DoorAction.Trigger) end   -- D8_9
handlers[117] = function() evt.SetDoorState(35, DoorAction.Trigger) evt.SetDoorState(36, DoorAction.Trigger) end   -- DD11
handlers[118] = function() evt.SetDoorState(40, DoorAction.Trigger) end   -- RotatingBookcase1
handlers[119] = function() evt.SetDoorState(41, DoorAction.Trigger) end   -- SecretDoor0
handlers[120] = function() evt.SetDoorState(42, DoorAction.Trigger) end   -- SecretDoor1

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest0
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest1
handlers[43] = function() evt.OpenChest(2) end   -- TreasureChest2
handlers[44] = function() evt.OpenChest(3) end   -- TreasureChest3


-- The library puzzle. TaSarBook.scr: the four textbooks (items 435-438) lie on the Start table; a book is taken
-- (:OnUse) when the key for the book before it is held (:KeyCheck: 436 needs 9517, 437 9518, 438 9519) and its
-- own table's key is not (:PlacedBook), and only until the library is solved (key 9516). TaSarTable.scr :OnUse:
-- a table given its own book gives its two keys (Offense 435: 9501, 9517; Strategy 436: 9502, 9518; Defense
-- 437: 9503, 9519; Intelligence 438: 9504, 9520) and takes every textbook the party carries, showing each on
-- itself ("<Location><item>"); :CheckAllKeys: with 9501-9504 key 9516, and the library's door opens.
local BOOKS = {"Start435", "Start436", "Start437", "Start438", "Offense435", "Offense436", "Offense437", "Offense438", "Strategy435", "Strategy436", "Strategy437", "Strategy438", "Defense435", "Defense436", "Defense437", "Defense438", "Intelligence435", "Intelligence436", "Intelligence437", "Intelligence438"}
local BOOK_KEY = {[435] = 9501, [436] = 9502, [437] = 9503, [438] = 9504}
local BOOK_NEEDS = {[435] = 0, [436] = 9517, [437] = 9518, [438] = 9519}
local function showBooks()
    for k, name in ipairs(BOOKS) do
        local location, item = string.match(name, "^(%a+)(%d+)$")
        evt.SetSprite(400 + k - 1, var("At" .. location .. item) == 1)
    end
end
local function takeBook(location, item)
    if var("At" .. location .. item) ~= 1 then return end
    local needs = BOOK_NEEDS[item]
    if needs ~= 0 and MM9.hasKey(needs) == 0 then return end
    if MM9.hasKey(BOOK_KEY[item]) == 1 then return end
    if MM9.hasKey(9516) == 1 then return end
    set("At" .. location .. item, 0)
    showBooks()
    give(item, "tasaracademy:" .. location .. item)
end
local function placeBooks(location, book, key, placedKey)
    if book ~= 0 and MM9.hasItem(book, "tasaracademy:table") == 1 then MM9.giveKey(key); MM9.giveKey(placedKey) end
    for item = 435, 438 do
        if MM9.hasItem(item, "tasaracademy:table") == 1 then
            MM9.takeItem(item, "tasaracademy:table")
            set("At" .. location .. item, 1)
        end
    end
    showBooks()
    if MM9.hasKey(9501) == 1 and MM9.hasKey(9502) == 1 and MM9.hasKey(9503) == 1 and MM9.hasKey(9504) == 1
            and MM9.hasKey(9516) == 0 then
        MM9.giveKey(9516)
        evt.PlaySoundName("door/door01open.wav", 0, 0, 0)
        openGroup("LibraryDoor")
    end
end
handlers[220] = function() placeBooks("Offense", 435, 9501, 9517) end   -- Prop164, TaSarTable.scr "Offense"
handlers[221] = function() placeBooks("Strategy", 436, 9502, 9518) end   -- Prop166, TaSarTable.scr "Strategy"
handlers[222] = function() placeBooks("Defense", 437, 9503, 9519) end   -- Prop163, TaSarTable.scr "Defense"
handlers[223] = function() placeBooks("Defense", 437, 9503, 9519) end   -- Prop168, TaSarTable.scr "Defense"
handlers[224] = function() placeBooks("Intelligence", 438, 9504, 9520) end   -- Prop165, TaSarTable.scr "Intelligence"
handlers[225] = function() placeBooks("Start", 0, 0, 0) end   -- Prop167, TaSarTable.scr "Start"
handlers[230] = function() takeBook("Start", 435) end   -- Start435, TaSarBook.scr "435 Start"
handlers[231] = function() takeBook("Start", 436) end   -- Start436, TaSarBook.scr "436 Start"
handlers[232] = function() takeBook("Start", 437) end   -- Start437, TaSarBook.scr "437 Start"
handlers[233] = function() takeBook("Start", 438) end   -- Start438, TaSarBook.scr "438 Start"
handlers[234] = function() takeBook("Offense", 435) end   -- Offense435, TaSarBook.scr "435 Offense"
handlers[235] = function() takeBook("Offense", 436) end   -- Offense436, TaSarBook.scr "436 Offense"
handlers[236] = function() takeBook("Offense", 437) end   -- Offense437, TaSarBook.scr "437 Offense"
handlers[237] = function() takeBook("Offense", 438) end   -- Offense438, TaSarBook.scr "438 Offense"
handlers[238] = function() takeBook("Strategy", 435) end   -- Strategy435, TaSarBook.scr "435 Strategy"
handlers[239] = function() takeBook("Strategy", 436) end   -- Strategy436, TaSarBook.scr "436 Strategy"
handlers[240] = function() takeBook("Strategy", 437) end   -- Strategy437, TaSarBook.scr "437 Strategy"
handlers[241] = function() takeBook("Strategy", 438) end   -- Strategy438, TaSarBook.scr "438 Strategy"
handlers[242] = function() takeBook("Defense", 435) end   -- Defense435, TaSarBook.scr "435 Defense"
handlers[243] = function() takeBook("Defense", 436) end   -- Defense436, TaSarBook.scr "436 Defense"
handlers[244] = function() takeBook("Defense", 437) end   -- Defense437, TaSarBook.scr "437 Defense"
handlers[245] = function() takeBook("Defense", 438) end   -- Defense438, TaSarBook.scr "438 Defense"
handlers[246] = function() takeBook("Intelligence", 435) end   -- Intelligence435, TaSarBook.scr "435 Intelligence"
handlers[247] = function() takeBook("Intelligence", 436) end   -- Intelligence436, TaSarBook.scr "436 Intelligence"
handlers[248] = function() takeBook("Intelligence", 437) end   -- Intelligence437, TaSarBook.scr "437 Intelligence"
handlers[249] = function() takeBook("Intelligence", 438) end   -- Intelligence438, TaSarBook.scr "438 Intelligence"

-- The library's secret door (LibraryDoor, Locked): only :CheckAllKeys opens it (unlock, use, lock: it stays open).
handlers[200] = function()
    if MM9.hasKey(9516) == 0 then evt.StatusText("The door is locked.") end
end

-- The Book of Rules (BookOfRules.scr :Onuse): a world item (391, hidden with key 59 or 166); its pickup gives 5000 experience, the quest sound and key 59 on Ludwig's errand (key 57), else key 166.
handlers[270] = function()
    if MM9.hasKey(59) == 1 or MM9.hasKey(166) == 1 then return end
    MM9.giveKey(MM9.hasKey(57) == 1 and 59 or 166)
    MM9.giveExperience(5000)
    MM9.playSound("sounds/events/quest.wav")
end

-- The rotating bookcase (RotatingBookcase1): either book button (BookButtonFront1, its DoubleDoor
-- BookButtonBack1) presses in and swings the bookcase (OpenTrigger toggle); the bookcase's Open/CloseTriggers
-- release the buttons. Pressed while it swings, nothing (the buttons are locked).
handlers[201] = function()
    if var("ButtonDown") == 1 then return end
    set("ButtonDown", 1)
    openGroup("BookButtonFront1"); openGroup("BookButtonBack1")
    toggleGroup("RotatingBookcase1")
    set("BookcaseTurns", var("BookcaseTurns") + 1)
    evt.StartTimer(152, seconds(5.5))
end
handlers[152] = function()
    evt.StopTimer(152)
    if var("ButtonDown") ~= 1 then return end
    set("ButtonDown", 0)
    closeGroup("BookButtonFront1"); closeGroup("BookButtonBack1")
end

-- The wall switches (Switch, Switch1; StartOpen): each click swings the switch and its secret door (SecretDoor1,
-- SecretDoor0: Open/CloseTriggers toggle), which shuts again after 7 s (CloseWaitTime); the hint goes
-- (PerceptionBrush1, PerceptionBrush0 off). MM9 locks Switch1 after its second swing; not carried (README).
handlers[202] = function()
    toggleGroup("Switch"); openGroup("SecretDoor1")
    set("FoundPerceptionBrush1", 1); set("PerceptionHints", 0); updateHints()
end
handlers[203] = function()
    toggleGroup("Switch1"); openGroup("SecretDoor0")
    set("FoundPerceptionBrush0", 1); set("PerceptionHints", 0); updateHints()
end

-- The cracked wall between the pit's tunnel and the library ("door crack", DestructableBrush, 25 hit points:
-- its DamageTrigger destroys "door crack 2", its DeathTrigger turns PerceptionBrush3 off): scene destructibles;
-- weapons break it as in MM9, a click still does (the shared click's killing blow).
handlers[205] = function() evt.DestroyDestructible(600) end
handlers[204] = function()   -- broken
    set("CrackBroken", 1)
    evt.DestroyDestructible(600)
    evt.PlaySoundName("events/rockfall.wav", 0, 0, 0)
    set("PerceptionHints", 0); updateHints()
end

-- The chalices (TaSarChalice.scr): the right one (Prop151, "Right") gives the active character 10
-- Might for a while (GiveAttribute 0 10 0 288000: MM9's stat 0 = Might) and key 9500; here once
-- per character (MM9 has no guard; a temporary bonus until rest). The others do nothing (";damage player").
handlers[210] = function()
    local who = math.max(0, evt.GetCurrentPlayerIndex())
    if var("Chalice" .. who) == 1 then evt.StatusText("Refreshing!") return end
    set("Chalice" .. who, 1)
    AddValue(MightBonus, 10)
    MM9.giveKey(9500)
    evt.StatusText("+10 Might (Temporary)")
end
handlers[211] = function() end

-- Letters and books (BookLetter.scr: DoLetter <p0>; the podium Prop159 reads its book Prop160 by PropTrigger.scr "Prop160 Use").
handlers[260] = function() evt.SimpleMessage("Challenging Students\n\nAs it has been said time and again, the unchallenged student will get lazy.  The way to prevent this is to keep the student from idleness.  A good instructor will surprise the student with tests, additional work, and failing all else, a good solid beating.  These forms of motivation have been proven time and again successful in creating a disciplined and hardy student.") end   -- Prop160, BookLetter.scr "434"
handlers[261] = function() evt.SimpleMessage("Challenging Students\n\nAs it has been said time and again, the unchallenged student will get lazy.  The way to prevent this is to keep the student from idleness.  A good instructor will surprise the student with tests, additional work, and failing all else, a good solid beating.  These forms of motivation have been proven time and again successful in creating a disciplined and hardy student.") end   -- Brazier48, BookLetter.scr "434"
handlers[262] = function() evt.SimpleMessage("Student Memo\n\nTo All Students:\nThe books on the pedestals are for instructors only!  If you attempt to read these books without knowing the proper sequence, you will be severely punished!\n\nSigned,\nWillian J. Nortley\nHeadmaster") end   -- Prop4, BookLetter.scr "433 Letter"
handlers[263] = function() evt.SimpleMessage("Artair Ordway\n\n..As Artair Ordway was the founder of the Ta'Sar Academy, it is only fitting that his statue is displayed prominently in the Trophy Room.  According to the documents, drinking from his cup will provide the warrior with his strength, but alas there are many cups in the Trophy Room.  It is also been said that woe be the soldier who tries, for drinking from the wrong cup will bring death a-knocking.") end   -- Prop2, BookLetter.scr "432"
handlers[264] = function() evt.SimpleMessage("Gavin's Instructions\n\nGavin,\nI have pressing matters to attend to.  If you wish to see the Book of War Rules, please put these books back where they belong.  Once you have completed that, finding the Book of Rules should not be difficult.\n\nSergeant Magnus") end   -- Prop96, BookLetter.scr "439 Letter"
handlers[265] = function() evt.SimpleMessage("Offense\n\nIn this section, you will find books on the subject of offense.") end   -- Prop174, BookLetter.scr "441 Letter"
handlers[266] = function() evt.SimpleMessage("Defense\n\nIn this section, you will find books on the subject of defense.") end   -- Prop175, BookLetter.scr "443 Letter"
handlers[267] = function() evt.SimpleMessage("Intelligence\n\nIn this section, you will find books on the subject of intelligence.") end   -- Prop177, BookLetter.scr "444 Letter"
handlers[268] = function() evt.SimpleMessage("Strategy\n\nIn this section, you will find books on the subject of strategy.") end   -- Prop178, BookLetter.scr "442 Letter"
handlers[269] = function() evt.SimpleMessage("Finding the War Rules\n\nAh, fine work Gavin!,\nI would like to make finding the Book of Rules easy for you, but such is not in my nature.  Being that I am your instructor in military intelligence, you must crack this code in order to find the book:\nBlf xzm urmw gsv Yllp lu Ifovh yvsrmw gsv ilgzgrmt yllphsvou rm gsv mvcg illn.") end   -- Prop179, BookLetter.scr "440 Letter"

-- The sparring (Trigger0-3 in the arena's mouths: GuardCaptain0 'Fight'; TaSarTeacher.scr :OnSpawn sends
-- 'Hate' to Student0-3 and DooksGuardCaptain0/1; TaSarStudent.scr :OnHate AddEnemy: the students' enemy
-- is "DooksGuardCaptain", the captains' "Guard"). Native: the Guard rows and the Half Orc Captain row
-- become enemies of each other as well as of the party.
function sparringRelations() evt.SetMonsterRelation(9111, 9104, 2); evt.SetMonsterRelation(9104, 9111, 2); evt.SetMonsterRelation(9113, 9104, 2); evt.SetMonsterRelation(9104, 9113, 2) end
-- A dead teacher takes no 'Fight' (MM9.receives): nobody is told to hate, the sparring never starts.
local function sparring()
    if var("Sparring") == 1 then return end
    if not MM9.receives("tasaracademy", "GuardCaptain0", "Fight", 16) then return end
    set("Sparring", 1)
    sparringRelations()
end

-- The crate in the store room (Trigger4: DestructableProp0 'Destroy'; its SpawnObject "Dagrell Scale 0.75"):
-- the crate is smashed and a small Dagrell comes out of it.
local function smashCrate()
    if var("CrateBroken") == 1 then return end
    set("CrateBroken", 1)
    evt.SetSprite(440, false)
    evt.PlaySoundName("events/crate_smash.wav", 0, 0, 0)
    evt.SetMonGroupBit(3, MonsterBits.Invisible, false)
    evt.SetMonGroupBit(3, MonsterBits.Hostile, true)
end

-- The PerceptionBrushes (Perception 10): the secret doors (0, 1), the trap doors (2), the cracked
-- wall (3), the bookcase's button (4) show to a party with the Perception for them; the secret doors' go once
-- found (their switches turn them off), the crack's once broken. Checked on load and every 3 s.
local function perceptive() return evt.CheckSkill(29, 0, 10) end
local HINTS = {PerceptionBrush0 = 450, PerceptionBrush1 = 451, PerceptionBrush2 = 452, PerceptionBrush3 = 453, PerceptionBrush4 = 454}
function updateHints()
    local want = perceptive() and 2 or 1
    if var("PerceptionHints") == want then return end
    set("PerceptionHints", want)
    for name, cog in pairs(HINTS) do
        local gone = var("Found" .. name) == 1 or (name == "PerceptionBrush3" and var("CrackBroken") == 1)
        evt.SetFacetBit(cog, FacetBits.Invisible, want == 1 or gone)
    end
end
handlers[151] = updateHints

-- The trap doors (PitDoorTrigger1: PitDoorRight1 toggle, its DoubleDoor PitDoorLeft1; CloseWaitTime 1, the
-- leaves' CloseTrigger turns the trigger on again) and the spikes under them (Spikes1: 40 once on landing).
local function trapDoors()
    openGroup("PitDoor")
    evt.PlaySoundName("door/door01open.wav", 0, 0, 0)
    set("PitTrips", var("PitTrips") + 1)
end

-- MM9's Trigger volumes, polled four times a second: each fires once on entry (the trap re-arms).
local VOLUMES = {
    {name = "PitDoorTrigger1", run = trapDoors, rearm = true},
    {name = "Trigger0", run = sparring}, {name = "Trigger1", run = sparring},
    {name = "Trigger2", run = sparring}, {name = "Trigger3", run = sparring},
    {name = "Trigger4", run = smashCrate},
    {name = "Spikes", run = function()
        hurt(40); set("SpikeHits", var("SpikeHits") + 1) end, rearm = true},
}
local inside, polls = {}, 0
handlers[150] = function()
    evt.StartTimer(150, seconds(0.25))
    local x, y, z = evt.GetPartyPosition()
    polls = polls + 1
    for _, v in ipairs(VOLUMES) do
        local now = inBox(BOX[v.name], x, y, z)
        if now and not inside[v.name] and var("Done" .. v.name) == 0 then
            if not v.rearm then set("Done" .. v.name, 1) end
            v.run()
        end
        inside[v.name] = now
    end
    if polls % 12 == 0 then updateHints() end
end

handlers[1] = function()   -- map load: the scripts' Init (TaSarBook.scr :Init, BookOfRules.scr :Main,
                           -- the crate, the sparring)
    if var("Init") == 0 then
        set("Init", 1)
        for _, item in ipairs({435, 436, 437, 438}) do set("AtStart" .. item, 1) end
    end
    showBooks()
    if var("CrateBroken") == 1 then evt.SetSprite(440, false) end
    if var("Sparring") == 1 then sparringRelations() end
    if MM9.hasKey(9516) == 1 then openGroup("LibraryDoor") end
    set("PerceptionHints", 0)
    updateHints()
    evt.StartTimer(150, seconds(0.25))
end
-- MM9's breakable brushes once built as click movers (destructibles.build_breakables): weapons break
-- them; a click still does, as a killing blow (refused while MM9's CanDamage is off).
handlers[38599] = function() evt.DamageDestructible(599, 1000000) end   -- door crack


RegisterEvent(101, "Door", handlers[101], "Door")
RegisterEvent(102, "Door", handlers[102], "Door")
RegisterEvent(103, "Door", handlers[103], "Door")
RegisterEvent(104, "Door", handlers[104], "Door")
RegisterEvent(105, "Door", handlers[105], "Door")
RegisterEvent(106, "Door", handlers[106], "Door")
RegisterEvent(107, "Door", handlers[107], "Door")
RegisterEvent(108, "Door", handlers[108], "Door")
RegisterEvent(109, "Door", handlers[109], "Door")
RegisterEvent(110, "Door", handlers[110], "Door")
RegisterEvent(111, "Door", handlers[111], "Door")
RegisterEvent(112, "Door", handlers[112], "Door")
RegisterEvent(113, "Door", handlers[113], "Door")
RegisterEvent(114, "Door", handlers[114], "Door")
RegisterEvent(115, "Door", handlers[115], "Door")
RegisterEvent(116, "Door", handlers[116], "Door")
RegisterEvent(117, "Door", handlers[117], "Door")
RegisterEvent(118, "Door", handlers[118], "Door")
RegisterEvent(119, "Door", handlers[119], "Door")
RegisterEvent(120, "Door", handlers[120], "Door")
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(43, "Chest", handlers[43], "Chest")
RegisterEvent(44, "Chest", handlers[44], "Chest")
RegisterEvent(220, "Table", handlers[220], "Table")
RegisterEvent(221, "Table", handlers[221], "Table")
RegisterEvent(222, "Table", handlers[222], "Table")
RegisterEvent(223, "Table", handlers[223], "Table")
RegisterEvent(224, "Table", handlers[224], "Table")
RegisterEvent(225, "Table", handlers[225], "Table")
RegisterEvent(230, "Textbook", handlers[230], "Book")
RegisterEvent(231, "Textbook", handlers[231], "Book")
RegisterEvent(232, "Textbook", handlers[232], "Book")
RegisterEvent(233, "Textbook", handlers[233], "Book")
RegisterEvent(234, "Textbook", handlers[234], "Book")
RegisterEvent(235, "Textbook", handlers[235], "Book")
RegisterEvent(236, "Textbook", handlers[236], "Book")
RegisterEvent(237, "Textbook", handlers[237], "Book")
RegisterEvent(238, "Textbook", handlers[238], "Book")
RegisterEvent(239, "Textbook", handlers[239], "Book")
RegisterEvent(240, "Textbook", handlers[240], "Book")
RegisterEvent(241, "Textbook", handlers[241], "Book")
RegisterEvent(242, "Textbook", handlers[242], "Book")
RegisterEvent(243, "Textbook", handlers[243], "Book")
RegisterEvent(244, "Textbook", handlers[244], "Book")
RegisterEvent(245, "Textbook", handlers[245], "Book")
RegisterEvent(246, "Textbook", handlers[246], "Book")
RegisterEvent(247, "Textbook", handlers[247], "Book")
RegisterEvent(248, "Textbook", handlers[248], "Book")
RegisterEvent(249, "Textbook", handlers[249], "Book")
RegisterEvent(270, "Book of Rules", handlers[270], "Book")
RegisterEvent(200, "Door", handlers[200], "Door")
RegisterEvent(201, "Book", handlers[201], "Book")
RegisterEvent(202, "Switch", handlers[202], "Switch")
RegisterEvent(203, "Switch", handlers[203], "Switch")
RegisterEvent(204, "Cracked wall", handlers[204])
RegisterEvent(205, "Cracked wall", handlers[205])
RegisterEvent(210, "Chalice", handlers[210], "Chalice")
RegisterEvent(211, "Chalice", handlers[211], "Chalice")
RegisterEvent(260, "Challenging Students", handlers[260], "Read")
RegisterEvent(261, "Challenging Students", handlers[261], "Read")
RegisterEvent(262, "Student Memo", handlers[262], "Read")
RegisterEvent(263, "Artair Ordway", handlers[263], "Read")
RegisterEvent(264, "Gavin's Instructions", handlers[264], "Read")
RegisterEvent(265, "Offense", handlers[265], "Read")
RegisterEvent(266, "Defense", handlers[266], "Read")
RegisterEvent(267, "Intelligence", handlers[267], "Read")
RegisterEvent(268, "Strategy", handlers[268], "Read")
RegisterEvent(269, "Finding the War Rules", handlers[269], "Read")
RegisterMapTimerEvent(150, seconds(3), handlers[150], "Trigger volumes", "", seconds(3))
RegisterMapTimerEvent(151, seconds(3), handlers[151], "Perception hints", "", seconds(3))
RegisterMapTimerEvent(152, seconds(3), handlers[152], "Book button", "", seconds(3))
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(38599, "door crack", handlers[38599], "Rocks")
