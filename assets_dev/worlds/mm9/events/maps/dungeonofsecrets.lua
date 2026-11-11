-- Dungeon of Secrets, MM9 rework (level_generation/projects/mm9r_dungeonofsecrets/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {Axe_Mover = 1, Blade = 2, Bottom_Axe = 3, Bottom_Door = 4, Side_Door = 5, Sliding_Panels = 6, Top_Axe = 7, Top_Door = 8, axe_door_01 = 9, axe_door_02 = 10, axe_door_03 = 11, axe_door_04 = 12, axe_door_05 = 13, axe_door_06 = 14, axe_door_08 = 15, axe_door_09 = 16, axe_door_10 = 17, axe_trap_01 = 18, axe_trap_02 = 19, axe_trap_03 = 20, axe_trap_04 = 21, axe_trap_05 = 22, axe_trap_06 = 23, axe_trap_08 = 24, axe_trap_09 = 25, axe_trap_10 = 26, doubleaxe_lower_trigger = 27, doubleaxe_upper_trigger = 28, elevator = 29, entrance_button = 30, entrance_gate = 31, exit_gate = 32, fake_lever_1 = 33, fake_lever_10 = 34, fake_lever_11 = 35, fake_lever_12 = 36, fake_lever_13 = 37, fake_lever_14 = 38, fake_lever_15 = 39, fake_lever_16 = 40, fake_lever_17 = 41, fake_lever_18 = 42, fake_lever_19 = 43, fake_lever_2 = 44, fake_lever_20 = 45, fake_lever_21 = 46, fake_lever_3 = 47, fake_lever_4 = 48, fake_lever_5 = 49, fake_lever_6 = 50, fake_lever_7 = 51, fake_lever_8 = 52, fake_lever_9 = 53, floor01 = 54, floor02 = 55, floor03 = 56, floor04 = 57, floor05 = 58, floor06 = 59, floor07 = 60, floor08 = 61, floor09 = 62, floor10 = 63, floor11 = 64, floor12 = 65, floor13 = 66, floor14 = 67, floor15 = 68, floor16 = 69, floor17 = 70, floor18 = 71, floor19 = 72, floor20 = 73, floor21 = 74, floor22 = 75, floor23 = 76, floor24 = 77, floor25 = 78, floor26 = 79, floor27 = 80, floor28 = 81, floor29 = 82, floor30 = 83, floor31 = 84, floor32 = 85, floor33 = 86, floor34 = 87, floor35 = 88, floor36 = 89, floor37 = 90, floor38 = 91, floor39 = 92, floor40 = 93, floor41 = 94, floor42 = 95, floor43 = 96, floor44 = 97, floor45 = 98, floor46 = 99, floor47 = 100, floor48 = 101, floor49 = 102, floor50 = 103, floor51 = 104, floor52 = 105, floor53 = 106, floor54 = 107, floor55 = 108, floor56 = 109, floor57 = 110, floor58 = 111, floor59 = 112, floor60 = 113, floor61 = 114, gplate1 = 115, gplate10 = 116, gplate2 = 117, gplate3 = 118, gplate4 = 119, gplate5 = 120, gplate6 = 121, gplate7 = 122, gplate8 = 123, gplate9 = 124, gtrap1 = 125, gtrap10 = 127, gtrap10_INV = 128, gtrap1_INV = 126, gtrap2 = 129, gtrap2_INV = 130, gtrap3 = 131, gtrap4 = 132, gtrap4_INV = 133, gtrap5 = 134, gtrap5_INV = 135, gtrap6 = 136, gtrap6_INV = 137, gtrap7a = 138, gtrap7b = 139, gtrap8a = 140, gtrap8b = 142, gtrap9 = 144, gtrap9_INV = 145, ratdoortrigger_INV = 147, saw8a = 141, saw8b = 143, saw9 = 146, timer_lever_01 = 148, timer_lever_02 = 149, timer_lever_03 = 150, timer_lever_03a = 151, timer_lever_04 = 152, timer_lever_05 = 153, timer_lever_06 = 154, timer_lever_08 = 155, timer_lever_09 = 156, timer_lever_10 = 157, water_grate = 158}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 900, 902}, onLeave = {}, timers = {}, openedChestIds = {}})

local function key(n) return (string.gsub(n, "[^%w]", "_")) end   -- a DAT name as a map variable name
local function hurt(amount) evt.DamagePlayer(Players.All, const.Damage.Physical, amount) end

-- MM9 Door / RotatingDoor data (overrides.yml groups): door ids, open and close seconds (MoveDist or
-- RotationAngles over Speed / ClosingSpeed), CloseWaitTime, Sticky, Locked, DoubleDoorName and Open/CloseTriggers.
local DOOR = {
    Axe_Mover = {ids = {1}, open = 0.293, close = 0.293, wait = 0.00, sticky = true, locked = false, double = nil, onOpen = {{"knockback11", "on"}, {"knockbackoff11", "trigger"}, {"Top Axe", "open"}}, onClose = {{"Side Door", "close"}}},   -- Axe Mover
    Blade = {ids = {2}, open = 1.200, close = 1.200, wait = 0.00, sticky = true, locked = false, double = nil, onOpen = {}, onClose = {}},   -- Blade
    Bottom_Axe = {ids = {3}, open = 0.300, close = 0.900, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- Bottom Axe
    Bottom_Door = {ids = {4}, open = 0.160, close = 0.160, wait = 0.00, sticky = true, locked = false, double = nil, onOpen = {{"Panel Mover", "open"}, {"Axe Mover", "open"}}, onClose = {}},   -- Bottom Door
    Panel_Mover = {ids = {}, open = 0.389, close = 0.389, wait = 0.00, sticky = true, locked = false, double = nil, onOpen = {}, onClose = {{"Top Door", "close"}}},   -- Panel Mover
    Side_Door = {ids = {5}, open = 0.514, close = 0.514, wait = 4.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {{"doubleaxe lower trigger", "unlock"}, {"doubleaxe upper trigger", "unlock"}, {"doubleaxe lower trigger", "close"}, {"doubleaxe upper trigger", "close"}}},   -- Side Door
    Sliding_Panels = {ids = {6}, open = 0.027, close = 0.027, wait = 4.00, sticky = false, locked = false, double = nil, onOpen = {{"Blade", "toggle"}, {"CHADWICK", "dotrap"}, {"knockbackon22", "trigger"}}, onClose = {}},   -- Sliding Panels
    Top_Axe = {ids = {7}, open = 0.300, close = 0.900, wait = 0.00, sticky = false, locked = false, double = "Bottom_Axe", onOpen = {}, onClose = {{"Axe Mover", "close"}, {"Panel Mover", "close"}}},   -- Top Axe
    Top_Door = {ids = {8}, open = 0.160, close = 0.160, wait = 0.00, sticky = true, locked = false, double = "Bottom_Door", onOpen = {}, onClose = {}},   -- Top Door
    axe_door_01 = {ids = {9}, open = 0.409, close = 1.385, wait = 4.00, sticky = false, locked = false, double = nil, onOpen = {{"axe trap 01", "open"}}, onClose = {}},   -- axe door 01
    axe_door_02 = {ids = {10}, open = 0.409, close = 1.385, wait = 4.00, sticky = false, locked = false, double = nil, onOpen = {{"axe trap 02", "open"}}, onClose = {}},   -- axe door 02
    axe_door_03 = {ids = {11}, open = 0.409, close = 1.385, wait = 4.00, sticky = false, locked = false, double = nil, onOpen = {{"axe trap 03", "open"}}, onClose = {}},   -- axe door 03
    axe_door_04 = {ids = {12}, open = 0.409, close = 1.385, wait = 4.00, sticky = false, locked = false, double = nil, onOpen = {{"axe trap 04", "open"}}, onClose = {}},   -- axe door 04
    axe_door_05 = {ids = {13}, open = 0.409, close = 1.385, wait = 4.00, sticky = false, locked = false, double = nil, onOpen = {{"axe trap 05", "open"}}, onClose = {}},   -- axe door 05
    axe_door_06 = {ids = {14}, open = 0.409, close = 1.385, wait = 4.00, sticky = false, locked = false, double = nil, onOpen = {{"axe trap 06", "open"}}, onClose = {}},   -- axe door 06
    axe_door_08 = {ids = {15}, open = 0.409, close = 1.385, wait = 4.00, sticky = false, locked = false, double = nil, onOpen = {{"axe trap 08", "open"}}, onClose = {}},   -- axe door 08
    axe_door_09 = {ids = {16}, open = 0.409, close = 1.385, wait = 4.00, sticky = false, locked = false, double = nil, onOpen = {{"axe trap 09", "open"}}, onClose = {}},   -- axe door 09
    axe_door_10 = {ids = {17}, open = 0.409, close = 1.385, wait = 4.00, sticky = false, locked = false, double = nil, onOpen = {{"axe trap 10", "open"}}, onClose = {{"entrance button", "unlock"}, {"entrance button", "close"}}},   -- axe door 10
    axe_trap_01 = {ids = {18}, open = 0.277, close = 1.895, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"CHADWICK", "dotrap"}, {"knockback01", "on"}, {"knockbackoff01", "trigger"}}, onClose = {}},   -- axe trap 01
    axe_trap_02 = {ids = {19}, open = 0.277, close = 1.895, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"CHADWICK", "dotrap"}, {"knockback02", "on"}, {"knockbackoff02", "trigger"}}, onClose = {}},   -- axe trap 02
    axe_trap_03 = {ids = {20}, open = 0.277, close = 1.895, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"CHADWICK", "dotrap"}, {"knockback03", "on"}, {"knockbackoff03", "trigger"}}, onClose = {}},   -- axe trap 03
    axe_trap_04 = {ids = {21}, open = 0.277, close = 1.895, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"CHADWICK", "dotrap"}, {"knockback04", "on"}, {"knockbackoff04", "trigger"}}, onClose = {}},   -- axe trap 04
    axe_trap_05 = {ids = {22}, open = 0.277, close = 1.895, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"CHADWICK", "dotrap"}, {"knockback05", "on"}, {"knockbackoff05", "trigger"}}, onClose = {}},   -- axe trap 05
    axe_trap_06 = {ids = {23}, open = 0.277, close = 1.895, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"CHADWICK", "dotrap"}, {"knockback06", "on"}, {"knockbackoff06", "trigger"}}, onClose = {}},   -- axe trap 06
    axe_trap_08 = {ids = {24}, open = 0.277, close = 1.895, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"CHADWICK", "dotrap"}, {"knockback08", "on"}, {"knockbackoff08", "trigger"}}, onClose = {}},   -- axe trap 08
    axe_trap_09 = {ids = {25}, open = 0.277, close = 1.895, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"CHADWICK", "dotrap"}, {"knockback09", "on"}, {"knockbackoff09", "trigger"}}, onClose = {}},   -- axe trap 09
    axe_trap_10 = {ids = {26}, open = 0.277, close = 1.895, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"CHADWICK", "dotrap"}, {"knockback10", "on"}, {"knockbackoff10", "trigger"}}, onClose = {}},   -- axe trap 10
    doubleaxe_lower_trigger = {ids = {27}, open = 0.229, close = 0.320, wait = 0.00, sticky = true, locked = false, double = nil, onOpen = {{"Double Axe Trap Trigger", "trigger"}, {"doubleaxe lower trigger", "lock"}, {"CHADWICK", "dotrap"}}, onClose = {}},   -- doubleaxe lower trigger
    doubleaxe_upper_trigger = {ids = {28}, open = 0.229, close = 0.320, wait = 0.00, sticky = true, locked = false, double = nil, onOpen = {{"Double Axe Trap Trigger", "trigger"}, {"doubleaxe upper trigger", "lock"}, {"CHADWICK", "dotrap"}}, onClose = {}},   -- doubleaxe upper trigger
    elevator = {ids = {29}, open = 9.143, close = 16.000, wait = 0.00, sticky = true, locked = false, double = nil, onOpen = {{"elevator", "lock"}}, onClose = {}},   -- elevator
    entrance_button = {ids = {30}, open = 1.200, close = 1.200, wait = 0.00, sticky = true, locked = false, double = nil, onOpen = {{"entrance gate", "open"}, {"entrance button", "lock"}, {"axe door 10", "unlock"}, {"CHADWICK", "removetrap"}}, onClose = {}},   -- entrance button
    entrance_gate = {ids = {31}, open = 3.600, close = 1.200, wait = 0.00, sticky = true, locked = false, double = nil, onOpen = {{"entrance gate", "lock"}}, onClose = {}},   -- entrance gate
    exit_gate = {ids = {32}, open = 1.385, close = 0.900, wait = 0.00, sticky = true, locked = false, double = nil, onOpen = {{"exit gate", "lock"}, {"CHADWICK", "done"}}, onClose = {{"exit gate", "lock"}}},   -- exit gate
    fake_lever_1 = {ids = {33}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 1
    fake_lever_10 = {ids = {34}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 10
    fake_lever_11 = {ids = {35}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 11
    fake_lever_12 = {ids = {36}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 12
    fake_lever_13 = {ids = {37}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 13
    fake_lever_14 = {ids = {38}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 14
    fake_lever_15 = {ids = {39}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 15
    fake_lever_16 = {ids = {40}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 16
    fake_lever_17 = {ids = {41}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 17
    fake_lever_18 = {ids = {42}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 18
    fake_lever_19 = {ids = {43}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 19
    fake_lever_2 = {ids = {44}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 2
    fake_lever_20 = {ids = {45}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 20
    fake_lever_21 = {ids = {46}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 21
    fake_lever_3 = {ids = {47}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 3
    fake_lever_4 = {ids = {48}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 4
    fake_lever_5 = {ids = {49}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 5
    fake_lever_6 = {ids = {50}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 6
    fake_lever_7 = {ids = {51}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 7
    fake_lever_8 = {ids = {52}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 8
    fake_lever_9 = {ids = {53}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- fake lever 9
    floor01 = {ids = {54}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter1", "on"}}, onClose = {{"shooter1", "off"}}},   -- floor01
    floor02 = {ids = {55}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter2", "on"}}, onClose = {{"shooter2", "off"}}},   -- floor02
    floor03 = {ids = {56}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter3R", "on"}, {"shooter3L", "on"}}, onClose = {{"shooter3R", "off"}, {"shooter3L", "off"}}},   -- floor03
    floor04 = {ids = {57}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter4", "on"}}, onClose = {{"shooter4", "off"}}},   -- floor04
    floor05 = {ids = {58}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter5", "on"}}, onClose = {{"shooter5", "off"}}},   -- floor05
    floor06 = {ids = {59}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter6", "on"}}, onClose = {{"shooter6", "off"}}},   -- floor06
    floor07 = {ids = {60}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter7", "on"}}, onClose = {{"shooter7", "off"}}},   -- floor07
    floor08 = {ids = {61}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter8", "on"}}, onClose = {{"shooter8", "off"}}},   -- floor08
    floor09 = {ids = {62}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter9", "on"}}, onClose = {{"shooter9", "off"}}},   -- floor09
    floor10 = {ids = {63}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter10L", "on"}, {"shooter10R", "on"}}, onClose = {{"shooter10L", "off"}, {"shooter10R", "off"}}},   -- floor10
    floor11 = {ids = {64}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter11", "on"}}, onClose = {{"shooter11", "off"}}},   -- floor11
    floor12 = {ids = {65}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter12", "on"}}, onClose = {{"shooter12", "off"}}},   -- floor12
    floor13 = {ids = {66}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter13", "on"}}, onClose = {{"shooter13", "off"}}},   -- floor13
    floor14 = {ids = {67}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter14", "on"}}, onClose = {{"shooter14", "off"}}},   -- floor14
    floor15 = {ids = {68}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter15", "on"}}, onClose = {{"shooter15", "off"}}},   -- floor15
    floor16 = {ids = {69}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter16", "on"}}, onClose = {{"shooter16", "off"}}},   -- floor16
    floor17 = {ids = {70}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter17R", "on"}, {"shooter17L", "on"}}, onClose = {{"shooter17R", "off"}, {"shooter17L", "off"}}},   -- floor17
    floor18 = {ids = {71}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter18", "on"}}, onClose = {{"shooter18", "off"}}},   -- floor18
    floor19 = {ids = {72}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter19", "on"}}, onClose = {{"shooter19", "off"}}},   -- floor19
    floor20 = {ids = {73}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter20", "on"}}, onClose = {{"shooter20", "off"}}},   -- floor20
    floor21 = {ids = {74}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter21", "on"}}, onClose = {{"shooter21", "off"}}},   -- floor21
    floor22 = {ids = {75}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter22", "on"}}, onClose = {{"shooter22", "off"}}},   -- floor22
    floor23 = {ids = {76}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter23", "on"}}, onClose = {{"shooter23", "off"}}},   -- floor23
    floor24 = {ids = {77}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter24R", "on"}, {"shooter24L", "on"}}, onClose = {{"shooter24R", "off"}, {"shooter24L", "off"}}},   -- floor24
    floor25 = {ids = {78}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter25", "on"}}, onClose = {{"shooter25", "off"}}},   -- floor25
    floor26 = {ids = {79}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter26", "on"}}, onClose = {{"shooter26", "off"}}},   -- floor26
    floor27 = {ids = {80}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter27", "on"}}, onClose = {{"shooter27", "off"}}},   -- floor27
    floor28 = {ids = {81}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter28", "on"}}, onClose = {{"shooter28", "off"}}},   -- floor28
    floor29 = {ids = {82}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter29", "on"}}, onClose = {{"shooter29", "off"}}},   -- floor29
    floor30 = {ids = {83}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter30", "on"}}, onClose = {{"shooter30", "off"}}},   -- floor30
    floor31 = {ids = {84}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter31R", "on"}, {"shooter31L", "on"}}, onClose = {{"shooter31R", "off"}, {"shooter31L", "off"}}},   -- floor31
    floor32 = {ids = {85}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter32", "on"}}, onClose = {{"shooter32", "off"}}},   -- floor32
    floor33 = {ids = {86}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter33", "on"}}, onClose = {{"shooter33", "off"}}},   -- floor33
    floor34 = {ids = {87}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter34", "on"}}, onClose = {{"shooter34", "off"}}},   -- floor34
    floor35 = {ids = {88}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter35", "on"}}, onClose = {{"shooter35", "off"}}},   -- floor35
    floor36 = {ids = {89}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter36", "on"}}, onClose = {{"shooter36", "off"}}},   -- floor36
    floor37 = {ids = {90}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter37", "on"}}, onClose = {{"shooter37", "off"}}},   -- floor37
    floor38 = {ids = {91}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter38L", "on"}, {"shooter38R", "on"}}, onClose = {{"shooter38L", "off"}, {"shooter38R", "off"}}},   -- floor38
    floor39 = {ids = {92}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter39", "on"}}, onClose = {{"shooter39", "off"}}},   -- floor39
    floor40 = {ids = {93}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter40", "on"}}, onClose = {{"shooter40", "off"}}},   -- floor40
    floor41 = {ids = {94}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter41", "on"}}, onClose = {{"shooter41", "off"}}},   -- floor41
    floor42 = {ids = {95}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter42", "on"}}, onClose = {{"shooter42", "off"}}},   -- floor42
    floor43 = {ids = {96}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter43", "on"}}, onClose = {{"shooter43", "off"}}},   -- floor43
    floor44 = {ids = {97}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter44", "on"}}, onClose = {{"shooter44", "off"}}},   -- floor44
    floor45 = {ids = {98}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter45R", "on"}, {"shooter45L", "on"}}, onClose = {{"shooter45R", "off"}, {"shooter45L", "off"}}},   -- floor45
    floor46 = {ids = {99}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter46", "on"}}, onClose = {{"shooter46", "off"}}},   -- floor46
    floor47 = {ids = {100}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter47", "on"}}, onClose = {{"shooter47", "off"}}},   -- floor47
    floor48 = {ids = {101}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter48", "on"}}, onClose = {{"shooter48", "off"}}},   -- floor48
    floor49 = {ids = {102}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter49", "on"}}, onClose = {{"shooter49", "off"}}},   -- floor49
    floor50 = {ids = {103}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter50", "on"}}, onClose = {{"shooter50", "off"}}},   -- floor50
    floor51 = {ids = {104}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter51", "on"}}, onClose = {{"shooter51", "off"}}},   -- floor51
    floor52 = {ids = {105}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter52R", "on"}, {"shooter52L", "on"}}, onClose = {{"shooter52R", "off"}, {"shooter52L", "off"}}},   -- floor52
    floor53 = {ids = {106}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter53", "on"}}, onClose = {{"shooter53", "off"}}},   -- floor53
    floor54 = {ids = {107}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter54", "on"}}, onClose = {{"shooter54", "off"}}},   -- floor54
    floor55 = {ids = {108}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter55", "on"}}, onClose = {{"shooter55", "off"}}},   -- floor55
    floor56 = {ids = {109}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter56", "on"}}, onClose = {{"shooter56", "off"}}},   -- floor56
    floor57 = {ids = {110}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter57", "on"}}, onClose = {{"shooter57", "off"}}},   -- floor57
    floor58 = {ids = {111}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter58", "on"}}, onClose = {{"shooter58", "off"}}},   -- floor58
    floor59 = {ids = {112}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter59R", "on"}, {"shooter59L", "on"}}, onClose = {{"shooter59R", "off"}, {"shooter59L", "off"}}},   -- floor59
    floor60 = {ids = {113}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter60", "on"}}, onClose = {{"shooter60", "off"}}},   -- floor60
    floor61 = {ids = {114}, open = 0.171, close = 0.300, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"shooter61", "on"}}, onClose = {{"shooter61", "off"}}},   -- floor61
    gplate1 = {ids = {115}, open = 0.200, close = 0.200, wait = 0.00, sticky = true, locked = false, double = nil, onOpen = {{"gtrap1", "open"}, {"gplate1", "lock"}, {"knockback12", "on"}, {"knockbackoff12", "trigger"}}, onClose = {}},   -- gplate1
    gplate10 = {ids = {116}, open = 0.200, close = 0.200, wait = 0.50, sticky = false, locked = false, double = nil, onOpen = {{"gtrap10", "open"}, {"gplate10", "lock"}, {"knockback18", "on"}, {"knockbackoff18", "trigger"}}, onClose = {}},   -- gplate10
    gplate2 = {ids = {117}, open = 0.200, close = 0.200, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"gtrap2", "open"}, {"gplate2", "lock"}, {"knockback13", "on"}, {"knockbackoff13", "trigger"}}, onClose = {}},   -- gplate2
    gplate3 = {ids = {118}, open = 0.200, close = 0.200, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"gtrap3", "open"}, {"gplate3", "lock"}}, onClose = {}},   -- gplate3
    gplate4 = {ids = {119}, open = 0.200, close = 0.200, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"gtrap4", "open"}, {"gplate4", "lock"}, {"knockback15", "on"}, {"knockbackoff15", "trigger"}}, onClose = {}},   -- gplate4
    gplate5 = {ids = {120}, open = 0.200, close = 0.200, wait = 0.50, sticky = false, locked = false, double = nil, onOpen = {{"gtrap5", "open"}, {"gplate5", "lock"}, {"knockback16", "on"}, {"knockbackoff16", "trigger"}}, onClose = {}},   -- gplate5
    gplate6 = {ids = {121}, open = 0.200, close = 0.200, wait = 0.50, sticky = false, locked = false, double = nil, onOpen = {{"gtrap6", "open"}, {"gplate6", "lock"}, {"knockback17", "on"}, {"knockbackoff17", "trigger"}}, onClose = {}},   -- gplate6
    gplate7 = {ids = {122}, open = 0.200, close = 0.200, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"gtrap7a", "open"}, {"gtrap7b", "open"}, {"gplate7", "lock"}, {"knockbackoff19", "trigger"}}, onClose = {}},   -- gplate7
    gplate8 = {ids = {123}, open = 0.200, close = 0.200, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"saw8a", "on"}, {"saw8b", "on"}, {"gtrap8trigger", "trigger"}}, onClose = {}},   -- gplate8
    gplate9 = {ids = {124}, open = 0.200, close = 0.200, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {{"gtrap9", "open"}, {"saw9", "on"}, {"gplate9", "lock"}, {"knockback21", "on"}}, onClose = {}},   -- gplate9
    gtrap1 = {ids = {125, 126}, open = 0.133, close = 1.200, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {{"gplate1", "unlock"}, {"gplate1", "close"}}},   -- gtrap1
    gtrap10 = {ids = {127, 128}, open = 0.375, close = 1.154, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {{"gplate10", "unlock"}, {"gplate10", "close"}}},   -- gtrap10
    gtrap2 = {ids = {129, 130}, open = 0.133, close = 1.200, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {{"gplate2", "unlock"}, {"gplate2", "close"}}},   -- gtrap2
    gtrap3 = {ids = {131}, open = 0.133, close = 0.400, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {{"knockback14", "on"}}, onClose = {{"gplate3", "unlock"}, {"gplate3", "close"}, {"knockback14", "off"}}},   -- gtrap3
    gtrap4 = {ids = {132, 133}, open = 0.160, close = 0.600, wait = 1.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {{"gplate4", "unlock"}, {"gplate4", "close"}}},   -- gtrap4
    gtrap5 = {ids = {134, 135}, open = 0.375, close = 1.154, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {{"gplate5", "unlock"}, {"gplate5", "close"}}},   -- gtrap5
    gtrap6 = {ids = {136, 137}, open = 0.375, close = 1.154, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {{"gplate6", "unlock"}, {"gplate6", "close"}}},   -- gtrap6
    gtrap7a = {ids = {138}, open = 0.900, close = 0.900, wait = 0.00, sticky = true, locked = false, double = nil, onOpen = {{"gplate7", "unlock"}, {"gplate7", "close"}}, onClose = {{"gplate7", "unlock"}, {"gplate7", "close"}}},   -- gtrap7a
    gtrap7b = {ids = {139}, open = 0.900, close = 0.900, wait = 0.00, sticky = true, locked = false, double = nil, onOpen = {{"gplate7", "unlock"}, {"gplate7", "close"}, {"knockback19", "off"}}, onClose = {{"gplate7", "unlock"}, {"gplate7", "close"}, {"knockback19", "off"}}},   -- gtrap7b
    gtrap8a = {ids = {140, 141}, open = 0.400, close = 2.963, wait = 3.00, sticky = false, locked = false, double = nil, onOpen = {{"gtrap8timertrigger", "trigger"}}, onClose = {{"gplate8", "unlock"}, {"gplate8", "close"}}},   -- gtrap8a
    gtrap8b = {ids = {142, 143}, open = 0.400, close = 2.963, wait = 3.00, sticky = false, locked = false, double = nil, onOpen = {}, onClose = {}},   -- gtrap8b
    gtrap9 = {ids = {144, 145, 146}, open = 0.300, close = 4.737, wait = 4.00, sticky = false, locked = false, double = nil, onOpen = {{"gtrap9timertrigger", "trigger"}, {"knockback20", "on"}, {"knockbackoff20", "trigger"}}, onClose = {{"gplate9", "unlock"}, {"gplate9", "close"}}},   -- gtrap9
    ratdoortrigger = {ids = {147}, open = 0.020, close = 0.020, wait = 0.00, sticky = true, locked = false, double = nil, onOpen = {{"ratnormal", "on"}, {"shoottrigger01", "trigger"}, {"rat door", "lock"}}, onClose = {}},   -- ratdoortrigger
    timer_lever_01 = {ids = {148}, open = 0.900, close = 8.571, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {{"axe trap 01", "lock"}}, onClose = {{"axe trap 01", "unlock"}}},   -- timer lever 01
    timer_lever_02 = {ids = {149}, open = 0.900, close = 9.000, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {{"axe trap 02", "lock"}}, onClose = {{"axe trap 02", "unlock"}}},   -- timer lever 02
    timer_lever_03 = {ids = {150}, open = 0.900, close = 2.118, wait = 0.00, sticky = false, locked = false, double = "timer_lever_03a", onOpen = {{"axe trap 03", "lock"}}, onClose = {{"axe trap 03", "unlock"}}},   -- timer lever 03
    timer_lever_03a = {ids = {151}, open = 0.900, close = 2.000, wait = 0.00, sticky = false, locked = false, double = "timer_lever_03", onOpen = {{"axe trap 03", "lock"}}, onClose = {{"axe trap 03", "unlock"}}},   -- timer lever 03a
    timer_lever_04 = {ids = {152}, open = 0.900, close = 4.500, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {{"axe trap 04", "lock"}}, onClose = {{"axe trap 04", "unlock"}}},   -- timer lever 04
    timer_lever_05 = {ids = {153}, open = 0.900, close = 2.250, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {{"axe trap 05", "lock"}}, onClose = {{"axe trap 05", "unlock"}}},   -- timer lever 05
    timer_lever_06 = {ids = {154}, open = 0.900, close = 9.000, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {{"axe trap 06", "lock"}}, onClose = {{"axe trap 06", "unlock"}}},   -- timer lever 06
    timer_lever_08 = {ids = {155}, open = 0.900, close = 4.500, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {{"axe trap 08", "lock"}}, onClose = {{"axe trap 08", "unlock"}}},   -- timer lever 08
    timer_lever_09 = {ids = {156}, open = 0.900, close = 2.571, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {{"axe trap 09", "lock"}}, onClose = {{"axe trap 09", "unlock"}}},   -- timer lever 09
    timer_lever_10 = {ids = {157}, open = 0.900, close = 2.250, wait = 0.00, sticky = false, locked = false, double = nil, onOpen = {{"axe trap 10", "lock"}}, onClose = {{"axe trap 10", "unlock"}}},   -- timer lever 10
    water_grate = {ids = {158}, open = 3.000, close = 0.900, wait = 0.00, sticky = true, locked = false, double = "water_grate_opener", onOpen = {{"water grate", "lock"}}, onClose = {}},   -- water grate
    water_grate_opener = {ids = {}, open = 3.600, close = 3.600, wait = 0.00, sticky = false, locked = false, double = "water_grate", onOpen = {{"water grate opener", "lock"}}, onClose = {}},   -- water grate opener
}
local MODEL_GROUP = {["Axe Mover"] = "Axe_Mover", ["Blade"] = "Blade", ["Bottom Axe"] = "Bottom_Axe", ["Bottom Door"] = "Bottom_Door", ["Panel Mover"] = "Panel_Mover", ["Side Door"] = "Side_Door", ["Sliding Panels"] = "Sliding_Panels", ["Top Axe"] = "Top_Axe", ["Top Door"] = "Top_Door", ["axe door 01"] = "axe_door_01", ["axe door 02"] = "axe_door_02", ["axe door 03"] = "axe_door_03", ["axe door 04"] = "axe_door_04", ["axe door 05"] = "axe_door_05", ["axe door 06"] = "axe_door_06", ["axe door 08"] = "axe_door_08", ["axe door 09"] = "axe_door_09", ["axe door 10"] = "axe_door_10", ["axe trap 01"] = "axe_trap_01", ["axe trap 02"] = "axe_trap_02", ["axe trap 03"] = "axe_trap_03", ["axe trap 04"] = "axe_trap_04", ["axe trap 05"] = "axe_trap_05", ["axe trap 06"] = "axe_trap_06", ["axe trap 08"] = "axe_trap_08", ["axe trap 09"] = "axe_trap_09", ["axe trap 10"] = "axe_trap_10", ["doubleaxe lower trigger"] = "doubleaxe_lower_trigger", ["doubleaxe upper trigger"] = "doubleaxe_upper_trigger", ["elevator"] = "elevator", ["entrance button"] = "entrance_button", ["entrance gate"] = "entrance_gate", ["exit gate"] = "exit_gate", ["fake lever 1"] = "fake_lever_1", ["fake lever 10"] = "fake_lever_10", ["fake lever 11"] = "fake_lever_11", ["fake lever 12"] = "fake_lever_12", ["fake lever 13"] = "fake_lever_13", ["fake lever 14"] = "fake_lever_14", ["fake lever 15"] = "fake_lever_15", ["fake lever 16"] = "fake_lever_16", ["fake lever 17"] = "fake_lever_17", ["fake lever 18"] = "fake_lever_18", ["fake lever 19"] = "fake_lever_19", ["fake lever 2"] = "fake_lever_2", ["fake lever 20"] = "fake_lever_20", ["fake lever 21"] = "fake_lever_21", ["fake lever 3"] = "fake_lever_3", ["fake lever 4"] = "fake_lever_4", ["fake lever 5"] = "fake_lever_5", ["fake lever 6"] = "fake_lever_6", ["fake lever 7"] = "fake_lever_7", ["fake lever 8"] = "fake_lever_8", ["fake lever 9"] = "fake_lever_9", ["floor01"] = "floor01", ["floor02"] = "floor02", ["floor03"] = "floor03", ["floor04"] = "floor04", ["floor05"] = "floor05", ["floor06"] = "floor06", ["floor07"] = "floor07", ["floor08"] = "floor08", ["floor09"] = "floor09", ["floor10"] = "floor10", ["floor11"] = "floor11", ["floor12"] = "floor12", ["floor13"] = "floor13", ["floor14"] = "floor14", ["floor15"] = "floor15", ["floor16"] = "floor16", ["floor17"] = "floor17", ["floor18"] = "floor18", ["floor19"] = "floor19", ["floor20"] = "floor20", ["floor21"] = "floor21", ["floor22"] = "floor22", ["floor23"] = "floor23", ["floor24"] = "floor24", ["floor25"] = "floor25", ["floor26"] = "floor26", ["floor27"] = "floor27", ["floor28"] = "floor28", ["floor29"] = "floor29", ["floor30"] = "floor30", ["floor31"] = "floor31", ["floor32"] = "floor32", ["floor33"] = "floor33", ["floor34"] = "floor34", ["floor35"] = "floor35", ["floor36"] = "floor36", ["floor37"] = "floor37", ["floor38"] = "floor38", ["floor39"] = "floor39", ["floor40"] = "floor40", ["floor41"] = "floor41", ["floor42"] = "floor42", ["floor43"] = "floor43", ["floor44"] = "floor44", ["floor45"] = "floor45", ["floor46"] = "floor46", ["floor47"] = "floor47", ["floor48"] = "floor48", ["floor49"] = "floor49", ["floor50"] = "floor50", ["floor51"] = "floor51", ["floor52"] = "floor52", ["floor53"] = "floor53", ["floor54"] = "floor54", ["floor55"] = "floor55", ["floor56"] = "floor56", ["floor57"] = "floor57", ["floor58"] = "floor58", ["floor59"] = "floor59", ["floor60"] = "floor60", ["floor61"] = "floor61", ["gplate1"] = "gplate1", ["gplate10"] = "gplate10", ["gplate2"] = "gplate2", ["gplate3"] = "gplate3", ["gplate4"] = "gplate4", ["gplate5"] = "gplate5", ["gplate6"] = "gplate6", ["gplate7"] = "gplate7", ["gplate8"] = "gplate8", ["gplate9"] = "gplate9", ["gtrap1"] = "gtrap1", ["gtrap10"] = "gtrap10", ["gtrap2"] = "gtrap2", ["gtrap3"] = "gtrap3", ["gtrap4"] = "gtrap4", ["gtrap5"] = "gtrap5", ["gtrap6"] = "gtrap6", ["gtrap7a"] = "gtrap7a", ["gtrap7b"] = "gtrap7b", ["gtrap8a"] = "gtrap8a", ["gtrap8b"] = "gtrap8b", ["gtrap9"] = "gtrap9", ["ratdoortrigger"] = "ratdoortrigger", ["timer lever 01"] = "timer_lever_01", ["timer lever 02"] = "timer_lever_02", ["timer lever 03"] = "timer_lever_03", ["timer lever 03a"] = "timer_lever_03a", ["timer lever 04"] = "timer_lever_04", ["timer lever 05"] = "timer_lever_05", ["timer lever 06"] = "timer_lever_06", ["timer lever 08"] = "timer_lever_08", ["timer lever 09"] = "timer_lever_09", ["timer lever 10"] = "timer_lever_10", ["water grate"] = "water_grate", ["water grate opener"] = "water_grate_opener"}
local KIND = {["Axe Mover"] = "door", ["Blade"] = "door", ["Bottom Axe"] = "door", ["Bottom Door"] = "door", ["CHADWICK"] = "npc", ["Double Axe Trap Trigger"] = "trigger", ["Panel Mover"] = "door", ["Side Door"] = "door", ["Sliding Panels"] = "door", ["Timer (BUS)"] = "trigger", ["Timer (DAT)"] = "trigger", ["Top Axe"] = "door", ["Top Door"] = "door", ["Trigger (BUS)"] = "trigger", ["axe door 01"] = "door", ["axe door 02"] = "door", ["axe door 03"] = "door", ["axe door 04"] = "door", ["axe door 05"] = "door", ["axe door 06"] = "door", ["axe door 08"] = "door", ["axe door 09"] = "door", ["axe door 10"] = "door", ["axe trap 01"] = "door", ["axe trap 02"] = "door", ["axe trap 03"] = "door", ["axe trap 04"] = "door", ["axe trap 05"] = "door", ["axe trap 06"] = "door", ["axe trap 08"] = "door", ["axe trap 09"] = "door", ["axe trap 10"] = "door", ["doubleaxe lower trigger"] = "door", ["doubleaxe upper trigger"] = "door", ["elevator"] = "door", ["entrance button"] = "door", ["entrance gate"] = "door", ["entrance gate close trigger"] = "trigger", ["entrance gate close trigger0"] = "trigger", ["entrance gate close trigger1"] = "trigger", ["exit gate"] = "door", ["exit gate close trigger"] = "trigger", ["exit gate open trigger"] = "trigger", ["fake lever 1"] = "door", ["fake lever 10"] = "door", ["fake lever 11"] = "door", ["fake lever 12"] = "door", ["fake lever 13"] = "door", ["fake lever 14"] = "door", ["fake lever 15"] = "door", ["fake lever 16"] = "door", ["fake lever 17"] = "door", ["fake lever 18"] = "door", ["fake lever 19"] = "door", ["fake lever 2"] = "door", ["fake lever 20"] = "door", ["fake lever 21"] = "door", ["fake lever 3"] = "door", ["fake lever 4"] = "door", ["fake lever 5"] = "door", ["fake lever 6"] = "door", ["fake lever 7"] = "door", ["fake lever 8"] = "door", ["fake lever 9"] = "door", ["floor01"] = "door", ["floor02"] = "door", ["floor03"] = "door", ["floor04"] = "door", ["floor05"] = "door", ["floor06"] = "door", ["floor07"] = "door", ["floor08"] = "door", ["floor09"] = "door", ["floor10"] = "door", ["floor11"] = "door", ["floor12"] = "door", ["floor13"] = "door", ["floor14"] = "door", ["floor15"] = "door", ["floor16"] = "door", ["floor17"] = "door", ["floor18"] = "door", ["floor19"] = "door", ["floor20"] = "door", ["floor21"] = "door", ["floor22"] = "door", ["floor23"] = "door", ["floor24"] = "door", ["floor25"] = "door", ["floor26"] = "door", ["floor27"] = "door", ["floor28"] = "door", ["floor29"] = "door", ["floor30"] = "door", ["floor31"] = "door", ["floor32"] = "door", ["floor33"] = "door", ["floor34"] = "door", ["floor35"] = "door", ["floor36"] = "door", ["floor37"] = "door", ["floor38"] = "door", ["floor39"] = "door", ["floor40"] = "door", ["floor41"] = "door", ["floor42"] = "door", ["floor43"] = "door", ["floor44"] = "door", ["floor45"] = "door", ["floor46"] = "door", ["floor47"] = "door", ["floor48"] = "door", ["floor49"] = "door", ["floor50"] = "door", ["floor51"] = "door", ["floor52"] = "door", ["floor53"] = "door", ["floor54"] = "door", ["floor55"] = "door", ["floor56"] = "door", ["floor57"] = "door", ["floor58"] = "door", ["floor59"] = "door", ["floor60"] = "door", ["floor61"] = "door", ["gplate1"] = "door", ["gplate10"] = "door", ["gplate2"] = "door", ["gplate3"] = "door", ["gplate4"] = "door", ["gplate5"] = "door", ["gplate6"] = "door", ["gplate7"] = "door", ["gplate8"] = "door", ["gplate9"] = "door", ["gtrap1"] = "door", ["gtrap10"] = "door", ["gtrap2"] = "door", ["gtrap3"] = "door", ["gtrap4"] = "door", ["gtrap5"] = "door", ["gtrap6"] = "door", ["gtrap7a"] = "door", ["gtrap7b"] = "door", ["gtrap8a"] = "door", ["gtrap8b"] = "door", ["gtrap8timertrigger"] = "trigger", ["gtrap8trigger"] = "trigger", ["gtrap9"] = "door", ["gtrap9timertrigger"] = "trigger", ["gtrigger1"] = "trigger", ["gtrigger10"] = "trigger", ["gtrigger2"] = "trigger", ["gtrigger3a"] = "trigger", ["gtrigger3b"] = "trigger", ["gtrigger4"] = "trigger", ["gtrigger5"] = "trigger", ["gtrigger6"] = "trigger", ["gtrigger7"] = "trigger", ["gtrigger8a"] = "trigger", ["gtrigger8b"] = "trigger", ["gtrigger9"] = "trigger", ["knockback off"] = "trigger", ["knockback off0"] = "trigger", ["knockback off1"] = "trigger", ["knockback01"] = "damage", ["knockback02"] = "damage", ["knockback03"] = "damage", ["knockback04"] = "damage", ["knockback05"] = "damage", ["knockback06"] = "damage", ["knockback08"] = "damage", ["knockback09"] = "damage", ["knockback10"] = "damage", ["knockback11"] = "damage", ["knockback12"] = "damage", ["knockback13"] = "damage", ["knockback14"] = "damage", ["knockback15"] = "damage", ["knockback16"] = "damage", ["knockback17"] = "damage", ["knockback18"] = "damage", ["knockback19"] = "damage", ["knockback20"] = "damage", ["knockback21"] = "damage", ["knockback22"] = "damage", ["knockback23"] = "damage", ["knockback24"] = "damage", ["knockbackoff01"] = "trigger", ["knockbackoff02"] = "trigger", ["knockbackoff03"] = "trigger", ["knockbackoff04"] = "trigger", ["knockbackoff05"] = "trigger", ["knockbackoff06"] = "trigger", ["knockbackoff08"] = "trigger", ["knockbackoff09"] = "trigger", ["knockbackoff10"] = "trigger", ["knockbackoff11"] = "trigger", ["knockbackoff12"] = "trigger", ["knockbackoff13"] = "trigger", ["knockbackoff15"] = "trigger", ["knockbackoff16"] = "trigger", ["knockbackoff17"] = "trigger", ["knockbackoff18"] = "trigger", ["knockbackoff19"] = "trigger", ["knockbackoff20"] = "trigger", ["knockbackoff22"] = "trigger", ["knockbackoff23"] = "trigger", ["knockbackoff24"] = "trigger", ["knockbackon22"] = "trigger", ["rat death start"] = "trigger", ["ratdoortrigger"] = "door", ["ratshooter01"] = "shooter", ["ratshooter02"] = "shooter", ["ratshooter03"] = "shooter", ["ratshooter04"] = "shooter", ["ratshooter05"] = "shooter", ["ratshooter06"] = "shooter", ["ratshooter07"] = "shooter", ["ratshooter08a"] = "shooter", ["ratshooter08b"] = "shooter", ["rattrigger01"] = "trigger", ["rattrigger02"] = "trigger", ["rattrigger03"] = "trigger", ["saw8a"] = "saw", ["saw8b"] = "saw", ["saw9"] = "saw", ["shooter0"] = "shooter", ["shooter1"] = "shooter", ["shooter10L"] = "shooter", ["shooter10R"] = "shooter", ["shooter11"] = "shooter", ["shooter12"] = "shooter", ["shooter13"] = "shooter", ["shooter14"] = "shooter", ["shooter15"] = "shooter", ["shooter16"] = "shooter", ["shooter17L"] = "shooter", ["shooter17R"] = "shooter", ["shooter18"] = "shooter", ["shooter19"] = "shooter", ["shooter2"] = "shooter", ["shooter20"] = "shooter", ["shooter21"] = "shooter", ["shooter22"] = "shooter", ["shooter23"] = "shooter", ["shooter24L"] = "shooter", ["shooter24R"] = "shooter", ["shooter25"] = "shooter", ["shooter26"] = "shooter", ["shooter27"] = "shooter", ["shooter28"] = "shooter", ["shooter29"] = "shooter", ["shooter30"] = "shooter", ["shooter31L"] = "shooter", ["shooter31R"] = "shooter", ["shooter32"] = "shooter", ["shooter33"] = "shooter", ["shooter34"] = "shooter", ["shooter35"] = "shooter", ["shooter36"] = "shooter", ["shooter37"] = "shooter", ["shooter38L"] = "shooter", ["shooter38R"] = "shooter", ["shooter39"] = "shooter", ["shooter3L"] = "shooter", ["shooter3R"] = "shooter", ["shooter4"] = "shooter", ["shooter40"] = "shooter", ["shooter41"] = "shooter", ["shooter42"] = "shooter", ["shooter43"] = "shooter", ["shooter44"] = "shooter", ["shooter45L"] = "shooter", ["shooter45R"] = "shooter", ["shooter46"] = "shooter", ["shooter47"] = "shooter", ["shooter48"] = "shooter", ["shooter49"] = "shooter", ["shooter5"] = "shooter", ["shooter50"] = "shooter", ["shooter51"] = "shooter", ["shooter52L"] = "shooter", ["shooter52R"] = "shooter", ["shooter53"] = "shooter", ["shooter54"] = "shooter", ["shooter55"] = "shooter", ["shooter56"] = "shooter", ["shooter57"] = "shooter", ["shooter58"] = "shooter", ["shooter59L"] = "shooter", ["shooter59R"] = "shooter", ["shooter6"] = "shooter", ["shooter60"] = "shooter", ["shooter61"] = "shooter", ["shooter7"] = "shooter", ["shooter8"] = "shooter", ["shooter9"] = "shooter", ["shoottrigger01"] = "trigger", ["shoottrigger02"] = "trigger", ["shoottrigger03"] = "trigger", ["shoottrigger04"] = "trigger", ["shoottrigger05"] = "trigger", ["shoottrigger06"] = "trigger", ["shoottrigger07"] = "trigger", ["shoottrigger08"] = "trigger", ["timer lever 01"] = "door", ["timer lever 02"] = "door", ["timer lever 03"] = "door", ["timer lever 03a"] = "door", ["timer lever 04"] = "door", ["timer lever 05"] = "door", ["timer lever 06"] = "door", ["timer lever 08"] = "door", ["timer lever 09"] = "door", ["timer lever 10"] = "door", ["trigger01"] = "trigger", ["trigger02"] = "trigger", ["trigger03"] = "trigger", ["trigger04"] = "trigger", ["trigger05"] = "trigger", ["trigger06"] = "trigger", ["trigger07"] = "trigger", ["trigger08"] = "trigger", ["trigger09"] = "trigger", ["trigger10"] = "trigger", ["trigger11"] = "trigger", ["trigger12"] = "trigger", ["trigger13"] = "trigger", ["trigger14"] = "trigger", ["trigger15"] = "trigger", ["trigger16"] = "trigger", ["trigger17"] = "trigger", ["trigger18"] = "trigger", ["trigger19"] = "trigger", ["trigger20"] = "trigger", ["trigger21"] = "trigger", ["trigger22"] = "trigger", ["trigger23"] = "trigger", ["trigger24"] = "trigger", ["trigger25"] = "trigger", ["trigger26"] = "trigger", ["trigger27"] = "trigger", ["trigger28"] = "trigger", ["trigger29"] = "trigger", ["trigger30"] = "trigger", ["trigger31"] = "trigger", ["trigger32"] = "trigger", ["trigger33"] = "trigger", ["trigger34"] = "trigger", ["trigger35"] = "trigger", ["trigger36"] = "trigger", ["trigger37"] = "trigger", ["trigger38"] = "trigger", ["trigger39"] = "trigger", ["trigger40"] = "trigger", ["trigger41"] = "trigger", ["trigger42"] = "trigger", ["trigger43"] = "trigger", ["trigger44"] = "trigger", ["trigger45"] = "trigger", ["trigger46"] = "trigger", ["trigger47"] = "trigger", ["trigger48"] = "trigger", ["trigger49"] = "trigger", ["trigger50"] = "trigger", ["trigger51"] = "trigger", ["trigger52"] = "trigger", ["trigger53"] = "trigger", ["trigger54"] = "trigger", ["trigger55"] = "trigger", ["trigger56"] = "trigger", ["trigger57"] = "trigger", ["trigger58"] = "trigger", ["trigger59"] = "trigger", ["trigger60"] = "trigger", ["trigger61"] = "trigger", ["water grate"] = "door", ["water grate close trigger"] = "trigger", ["water grate opener"] = "door"}
local TRIGGER = {
    ["Timer (BUS)"] = {box = {{-676, 3625, 225}, {-635, 3666, 266}}, on = true, touch = true, delay = 10.00, count = 1, msgs = {{"Trigger (BUS)", "on"}}},
    ["Trigger (BUS)"] = {box = {{-1024, 3564, 189}, {-287, 4301, 271}}, on = true, touch = true, delay = 1.50, count = 1, msgs = {{"Timer (BUS)", "trigger"}, {"Sliding Panels", "open"}, {"Trigger (BUS)", "off"}}},
    ["knockbackoff22"] = {box = {{-1085, 4137, 61}, {-1044, 4178, 102}}, on = true, touch = true, delay = 0.25, count = 0, msgs = {{"knockback22", "off"}}},
    ["knockbackon22"] = {box = {{-1085, 4198, 61}, {-1044, 4239, 102}}, on = true, touch = true, delay = 1.55, count = 0, msgs = {{"knockback22", "on"}, {"knockbackoff22", "trigger"}}},
    ["Double Axe Trap Trigger"] = {box = {{205, 983, 328}, {287, 1065, 410}}, on = true, touch = true, delay = 0.00, count = 1, msgs = {{"Side Door", "open"}, {"Top Door", "open"}, {"Double Axe Trap Trigger", "off"}, {"Timer (DAT)", "trigger"}}},
    ["Timer (DAT)"] = {box = {{92, 1198, 584}, {113, 1219, 604}}, on = true, touch = false, delay = 5.00, count = 1, msgs = {{"Double Axe Trap Trigger", "on"}}},
    ["knockbackoff11"] = {box = {{143, 1413, 881}, {184, 1454, 922}}, on = true, touch = true, delay = 0.35, count = 0, msgs = {{"knockback11", "off"}}},
    ["knockbackoff10"] = {box = {{4055, -143, -20}, {4096, -102, 20}}, on = true, touch = true, delay = 0.35, count = 0, msgs = {{"knockback10", "off"}}},
    ["knockbackoff09"] = {box = {{3256, -717, -20}, {3297, -676, 20}}, on = true, touch = true, delay = 0.35, count = 0, msgs = {{"knockback09", "off"}}},
    ["knockbackoff08"] = {box = {{1802, -225, -20}, {1843, -184, 20}}, on = true, touch = true, delay = 0.35, count = 0, msgs = {{"knockback08", "off"}}},
    ["knockbackoff06"] = {box = {{2683, -2007, 20}, {2724, -1966, 61}}, on = true, touch = true, delay = 0.35, count = 0, msgs = {{"knockback06", "off"}}},
    ["knockbackoff05"] = {box = {{-2048, -1434, 20}, {-2007, -1393, 61}}, on = true, touch = true, delay = 0.35, count = 0, msgs = {{"knockback05", "off"}}},
    ["knockbackoff04"] = {box = {{-1638, 1516, 758}, {-1597, 1556, 799}}, on = true, touch = true, delay = 0.35, count = 0, msgs = {{"knockback04", "off"}}},
    ["knockbackoff03"] = {box = {{1884, 1884, 758}, {1925, 1925, 799}}, on = true, touch = true, delay = 0.35, count = 0, msgs = {{"knockback03", "off"}}},
    ["knockbackoff02"] = {box = {{-1085, 3994, 676}, {-1044, 4035, 717}}, on = true, touch = true, delay = 0.35, count = 0, msgs = {{"knockback02", "off"}}},
    ["knockbackoff01"] = {box = {{-2847, 4669, 20}, {-2806, 4710, 61}}, on = true, touch = true, delay = 0.35, count = 0, msgs = {{"knockback01", "off"}}},
    ["trigger51"] = {box = {{-2504, 2729, -10}, {-2493, 2739, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor51", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger37"] = {box = {{-2504, 3036, -10}, {-2493, 3046, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor37", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger45"] = {box = {{-2391, 2867, -10}, {-2381, 2908, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor45", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger44"] = {box = {{-2616, 2867, -10}, {-2606, 2908, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor44", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger36"] = {box = {{-2632, 3021, -10}, {-2591, 3062, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor36", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger38"] = {box = {{-2406, 3021, -10}, {-2365, 3062, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor38", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger52"] = {box = {{-2406, 2714, -10}, {-2365, 2755, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor52", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger50"] = {box = {{-2632, 2714, -10}, {-2591, 2755, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor50", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger23"] = {box = {{-2504, 3343, -10}, {-2493, 3354, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor23", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger30"] = {box = {{-2616, 3174, -10}, {-2606, 3215, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor30", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger22"] = {box = {{-2632, 3328, -10}, {-2591, 3369, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor22", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger31"] = {box = {{-2391, 3174, -10}, {-2381, 3215, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor31", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger24"] = {box = {{-2406, 3328, -10}, {-2365, 3369, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor24", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger16"] = {box = {{-2616, 3482, -10}, {-2606, 3523, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor16", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger17"] = {box = {{-2391, 3482, -10}, {-2381, 3523, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor17", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger58"] = {box = {{-2616, 2560, -10}, {-2606, 2601, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor58", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger59"] = {box = {{-2391, 2560, -10}, {-2381, 2601, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor59", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger49"] = {box = {{-2729, 2729, -10}, {-2719, 2739, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor49", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger35"] = {box = {{-2729, 3036, -10}, {-2719, 3046, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor35", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger43"] = {box = {{-2842, 2867, -10}, {-2831, 2908, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor43", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger34"] = {box = {{-2857, 3021, -10}, {-2816, 3062, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor34", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger48"] = {box = {{-2857, 2714, -10}, {-2816, 2755, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor48", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger21"] = {box = {{-2729, 3343, -10}, {-2719, 3354, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor21", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger29"] = {box = {{-2842, 3174, -10}, {-2831, 3215, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor29", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger20"] = {box = {{-2857, 3328, -10}, {-2816, 3369, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor20", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger15"] = {box = {{-2842, 3482, -10}, {-2831, 3523, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor15", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger57"] = {box = {{-2842, 2560, -10}, {-2831, 2601, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor57", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger55"] = {box = {{-2053, 2729, -10}, {-2043, 2739, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor55", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger41"] = {box = {{-2053, 3036, -10}, {-2043, 3046, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor41", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger47"] = {box = {{-1940, 2867, -10}, {-1930, 2908, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor47", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger46"] = {box = {{-2166, 2867, -10}, {-2156, 2908, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor46", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger40"] = {box = {{-2181, 3021, -10}, {-2140, 3062, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor40", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger42"] = {box = {{-1956, 3021, -10}, {-1915, 3062, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor42", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger56"] = {box = {{-1956, 2714, -10}, {-1915, 2755, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor56", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger54"] = {box = {{-2181, 2714, -10}, {-2140, 2755, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor54", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger27"] = {box = {{-2053, 3343, -10}, {-2043, 3354, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor27", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger32"] = {box = {{-2166, 3174, -10}, {-2156, 3215, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor32", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger26"] = {box = {{-2181, 3328, -10}, {-2140, 3369, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor26", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger33"] = {box = {{-1940, 3174, -10}, {-1930, 3215, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor33", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger28"] = {box = {{-1956, 3328, -10}, {-1915, 3369, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor28", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger18"] = {box = {{-2166, 3482, -10}, {-2156, 3523, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor18", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger19"] = {box = {{-1940, 3482, -10}, {-1930, 3523, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor19", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger61"] = {box = {{-1940, 2560, -10}, {-1930, 2601, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor61", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger53"] = {box = {{-2278, 2729, -10}, {-2268, 2739, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor53", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger39"] = {box = {{-2278, 3036, -10}, {-2268, 3046, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor39", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger25"] = {box = {{-2278, 3343, -10}, {-2268, 3354, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor25", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger09"] = {box = {{-2504, 3651, -10}, {-2493, 3661, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor09", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger08"] = {box = {{-2632, 3635, -10}, {-2591, 3676, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor08", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger10"] = {box = {{-2406, 3635, -10}, {-2365, 3676, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor10", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger02"] = {box = {{-2616, 3789, -10}, {-2606, 3830, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor02", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger03"] = {box = {{-2391, 3789, -10}, {-2381, 3830, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor03", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger07"] = {box = {{-2729, 3651, -10}, {-2719, 3661, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor07", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger06"] = {box = {{-2857, 3635, -10}, {-2816, 3676, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor06", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger01"] = {box = {{-2842, 3789, -10}, {-2831, 3830, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor01", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger13"] = {box = {{-2053, 3651, -10}, {-2043, 3661, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor13", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger12"] = {box = {{-2181, 3635, -10}, {-2140, 3676, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor12", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger14"] = {box = {{-1956, 3635, -10}, {-1915, 3676, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor14", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger04"] = {box = {{-2166, 3789, -10}, {-2156, 3830, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor04", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger05"] = {box = {{-1940, 3789, -10}, {-1930, 3830, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor05", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger11"] = {box = {{-2278, 3651, -10}, {-2268, 3661, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor11", "open"}, {"CHADWICK", "dotrap"}}},
    ["trigger60"] = {box = {{-2166, 2560, -10}, {-2156, 2601, 10}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"floor60", "open"}, {"CHADWICK", "dotrap"}}},
    ["gtrigger1"] = {box = {{-1106, -1925, -51}, {-1024, -1843, -31}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"gplate1", "open"}, {"CHADWICK", "dotrap"}}},
    ["gtrigger2"] = {box = {{-778, -1597, -51}, {-696, -1516, -31}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"gplate2", "open"}, {"CHADWICK", "dotrap"}}},
    ["gtrigger3a"] = {box = {{-410, -1741, -51}, {-246, -1700, -31}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"gplate3", "open"}, {"CHADWICK", "dotrap"}}},
    ["gtrigger3b"] = {box = {{-266, -1925, -51}, {-225, -1761, -31}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"gplate3", "open"}, {"CHADWICK", "dotrap"}}},
    ["gtrigger4"] = {box = {{61, -1731, -51}, {102, -1546, -31}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"gplate4", "open"}, {"CHADWICK", "dotrap"}}},
    ["gtrigger5"] = {box = {{379, -1915, -51}, {440, -1853, -31}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"gplate5", "open"}, {"CHADWICK", "dotrap"}}},
    ["gtrigger6"] = {box = {{543, -1587, -51}, {604, -1526, -31}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"gplate6", "open"}, {"CHADWICK", "dotrap"}}},
    ["gtrigger10"] = {box = {{707, -1915, -51}, {768, -1853, -31}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"gplate10", "open"}, {"CHADWICK", "dotrap"}}},
    ["gtrigger7"] = {box = {{881, -1884, -51}, {922, -1556, -31}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"gplate7", "open"}, {"CHADWICK", "dotrap"}}},
    ["gtrigger8a"] = {box = {{1249, -1700, -51}, {1372, -1577, -31}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"gplate8", "open"}, {"CHADWICK", "dotrap"}}},
    ["gtrigger8b"] = {box = {{1413, -1864, -51}, {1536, -1741, -31}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"gplate8", "open"}, {"CHADWICK", "dotrap"}}},
    ["gtrigger9"] = {box = {{1889, -1884, -51}, {2043, -1556, -31}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"gplate9", "open"}, {"CHADWICK", "dotrap"}}},
    ["gtrap8trigger"] = {box = {{1085, -2294, 61}, {1167, -2212, 143}}, on = true, touch = false, delay = 0.00, count = 1, msgs = {{"gtrap8a", "open"}, {"gtrap8b", "open"}, {"gplate8", "lock"}, {"knockback24", "on"}, {"knockbackoff24", "trigger"}, {"knockback23", "on"}, {"knockbackoff23", "trigger"}}},
    ["gtrap8timertrigger"] = {box = {{1085, -2437, 61}, {1167, -2355, 143}}, on = true, touch = true, delay = 2.00, count = 1, msgs = {{"saw8a", "off"}, {"saw8b", "off"}}},
    ["gtrap9timertrigger"] = {box = {{1925, -2150, 61}, {2007, -2068, 143}}, on = true, touch = true, delay = 4.00, count = 1, msgs = {{"saw9", "off"}}},
    ["knockbackoff12"] = {box = {{-1147, -2109, -20}, {-1106, -2068, 20}}, on = true, touch = true, delay = 0.15, count = 0, msgs = {{"knockback12", "off"}}},
    ["knockbackoff13"] = {box = {{-922, -1352, -20}, {-881, -1311, 20}}, on = true, touch = true, delay = 0.15, count = 0, msgs = {{"knockback13", "off"}}},
    ["knockbackoff15"] = {box = {{61, -2109, -20}, {102, -2068, 20}}, on = true, touch = true, delay = 0.50, count = 0, msgs = {{"knockback15", "off"}}},
    ["knockbackoff16"] = {box = {{328, -2109, 41}, {369, -2068, 82}}, on = true, touch = true, delay = 0.50, count = 0, msgs = {{"knockback16", "off"}}},
    ["knockbackoff17"] = {box = {{492, -1352, 41}, {532, -1311, 82}}, on = true, touch = true, delay = 0.50, count = 0, msgs = {{"knockback17", "off"}}},
    ["knockbackoff18"] = {box = {{655, -2109, 41}, {696, -2068, 82}}, on = true, touch = true, delay = 0.50, count = 0, msgs = {{"knockback18", "off"}}},
    ["knockbackoff19"] = {box = {{881, -2109, 41}, {922, -2068, 82}}, on = true, touch = true, delay = 0.10, count = 0, msgs = {{"knockback19", "on"}}},
    ["knockbackoff20"] = {box = {{1823, -2109, 41}, {1864, -2068, 82}}, on = true, touch = true, delay = 4.50, count = 0, msgs = {{"knockback20", "off"}, {"knockback21", "off"}}},
    ["knockbackoff23"] = {box = {{1208, -2109, -102}, {1249, -2068, -61}}, on = true, touch = true, delay = 4.20, count = 0, msgs = {{"knockback23", "off"}}},
    ["knockbackoff24"] = {box = {{1536, -1372, -102}, {1577, -1331, -61}}, on = true, touch = true, delay = 4.20, count = 0, msgs = {{"knockback24", "off"}}},
    ["knockback off0"] = {box = {{4403, -143, 113}, {4444, -102, 154}}, on = true, touch = true, delay = 0.00, count = 1, msgs = {{"knockback11", "off"}, {"knockback12", "off"}, {"knockback13", "off"}, {"knockback14", "off"}, {"knockback15", "off"}, {"knockback16", "off"}, {"knockback17", "off"}, {"knockback18", "off"}, {"knockback19", "off"}, {"knockback off1", "trigger"}}},
    ["knockback off1"] = {box = {{4485, -143, 113}, {4526, -102, 154}}, on = true, touch = true, delay = 0.00, count = 1, msgs = {{"knockback21", "off"}, {"knockback22", "off"}, {"knockback23", "off"}, {"knockback24", "off"}, {"knockback25", "off"}, {"knockback26", "off"}, {"knockback27", "off"}, {"knockback28", "off"}, {"knockback29", "off"}, {"knockback20", "off"}}},
    ["exit gate close trigger"] = {box = {{4280, -1940, -46}, {4403, -1172, 210}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"exit gate", "unlock"}, {"exit gate", "close"}, {"elevator", "unlock"}, {"elevator", "close"}, {"exit gate open trigger", "on"}}},
    ["exit gate open trigger"] = {box = {{2944, -1848, -46}, {2954, -1592, 210}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"exit gate", "unlock"}, {"exit gate", "open"}, {"axe door 10", "unlock"}, {"exit gate open trigger", "off"}}},
    ["entrance gate close trigger"] = {box = {{2739, -1111, 15}, {2995, -855, 271}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"entrance button", "unlock"}, {"entrance button", "close"}, {"axe door 10", "close"}, {"axe door 10", "lock"}}},
    ["entrance gate close trigger0"] = {box = {{3395, -538, 15}, {3651, -282, 271}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"entrance gate", "unlock"}, {"entrance gate", "close"}}},
    ["water grate close trigger"] = {box = {{-1398, 1080, -82}, {-1347, 1336, 573}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"water grate", "unlock"}, {"water grate opener", "unlock"}, {"water grate", "close"}, {"water grate opener", "close"}}},
    ["rat death start"] = {box = {{-2888, 1940, -5}, {-1864, 1992, 251}}, on = true, touch = true, delay = 0.00, count = 1, msgs = {{"ratdoortrigger", "open"}, {"rat", "off"}, {"rat0", "off"}, {"rat1", "off"}, {"rat2", "off"}}},
    ["shoottrigger01"] = {box = {{-3052, 2601, 61}, {-3011, 2642, 102}}, on = true, touch = false, delay = 2.00, count = 1, msgs = {{"ratshooter01", "on"}, {"rattrigger01", "trigger"}, {"ratshooter01", "off"}}},
    ["rattrigger01"] = {box = {{-3052, 2683, 61}, {-3011, 2724, 102}}, on = true, touch = false, delay = 1.00, count = 1, msgs = {{"ratmocking", "on"}, {"shoottrigger02", "trigger"}}},
    ["shoottrigger02"] = {box = {{-3052, 2765, 61}, {-3011, 2806, 102}}, on = true, touch = false, delay = 2.00, count = 1, msgs = {{"ratshooter02", "on"}, {"shoottrigger03", "trigger"}, {"ratshooter02", "off"}}},
    ["shoottrigger03"] = {box = {{-3052, 2847, 61}, {-3011, 2888, 102}}, on = true, touch = false, delay = 0.80, count = 1, msgs = {{"ratshooter03", "on"}, {"rattrigger02", "trigger"}, {"ratshooter03", "off"}}},
    ["rattrigger02"] = {box = {{-3052, 2929, 61}, {-3011, 2970, 102}}, on = true, touch = false, delay = 1.00, count = 1, msgs = {{"ratscared", "on"}, {"shoottrigger04", "trigger"}}},
    ["shoottrigger04"] = {box = {{-3052, 3011, 61}, {-3011, 3052, 102}}, on = true, touch = false, delay = 1.75, count = 1, msgs = {{"ratshooter04", "on"}, {"shoottrigger05", "trigger"}, {"ratshooter04", "off"}}},
    ["shoottrigger05"] = {box = {{-3052, 3092, 61}, {-3011, 3133, 102}}, on = true, touch = false, delay = 0.75, count = 1, msgs = {{"ratshooter05", "on"}, {"shoottrigger06", "trigger"}, {"ratshooter05", "off"}}},
    ["shoottrigger06"] = {box = {{-3052, 3174, 61}, {-3011, 3215, 102}}, on = true, touch = false, delay = 0.50, count = 1, msgs = {{"ratshooter06", "on"}, {"shoottrigger07", "trigger"}, {"ratshooter06", "off"}}},
    ["shoottrigger07"] = {box = {{-3052, 3256, 61}, {-3011, 3297, 102}}, on = true, touch = false, delay = 0.35, count = 1, msgs = {{"ratshooter07", "on"}, {"shoottrigger08", "trigger"}, {"ratshooter07", "off"}}},
    ["shoottrigger08"] = {box = {{-3052, 3338, 61}, {-3011, 3379, 102}}, on = true, touch = false, delay = 0.25, count = 1, msgs = {{"ratshooter08a", "on"}, {"ratshooter08b", "on"}, {"ratshooter08a", "off"}, {"ratshooter08b", "off"}, {"rattrigger03", "trigger"}}},
    ["rattrigger03"] = {box = {{-3052, 3420, 61}, {-3011, 3461, 102}}, on = true, touch = false, delay = 0.75, count = 1, msgs = {{"ratdead", "on"}}},
    ["knockback off"] = {box = {{4275, -456, -36}, {4531, -200, 220}}, on = true, touch = true, delay = 0.00, count = 1, msgs = {{"knockback01", "off"}, {"knockback02", "off"}, {"knockback03", "off"}, {"knockback04", "off"}, {"knockback05", "off"}, {"knockback06", "off"}, {"knockback off0", "trigger"}, {"knockback08", "off"}, {"knockback09", "off"}, {"knockback10", "off"}}},
    ["entrance gate close trigger1"] = {box = {{3983, -650, -184}, {5294, -599, 471}}, on = true, touch = true, delay = 0.00, count = 0, msgs = {{"entrance gate", "unlock"}, {"entrance gate", "close"}, {"entrance button", "unlock"}, {"entrance button", "close"}}},
}
local SHOOTER = {
    ["ratshooter01"] = {at = {-2847, 2888, 369}, to = {237, 2176, -1806}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["ratshooter02"] = {at = {-1925, 2888, 246}, to = {-5625, 2888, -780}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["ratshooter03"] = {at = {-1925, 3195, 369}, to = {-4953, 2263, -1801}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["ratshooter04"] = {at = {-1925, 3809, 369}, to = {-4953, 2878, -1801}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["ratshooter05"] = {at = {-1925, 3502, 246}, to = {-5625, 3502, -780}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["ratshooter06"] = {at = {-1925, 3502, 369}, to = {-4814, 2674, -2022}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["ratshooter07"] = {at = {-1925, 3502, 369}, to = {-4953, 2570, -1801}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["ratshooter08a"] = {at = {-2847, 3502, 369}, to = {-103, 2503, -2125}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["ratshooter08b"] = {at = {-1925, 3502, 369}, to = {-4669, 2503, -2125}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter0"] = {at = {-2847, 3809, 369}, to = {-2847, 3769, -3471}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter1"] = {at = {-1925, 3809, 246}, to = {-5677, 3809, -572}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter10L"] = {at = {-2847, 3809, 369}, to = {-103, 2811, -2125}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter10R"] = {at = {-1925, 3809, 369}, to = {-4669, 2811, -2125}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter11"] = {at = {-2847, 3809, 369}, to = {72, 2922, -1964}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter12"] = {at = {-2847, 3809, 369}, to = {237, 3097, -1806}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter13"] = {at = {-2847, 3809, 246}, to = {814, 3164, -716}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter14"] = {at = {-2847, 3809, 246}, to = {880, 3286, -520}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter15"] = {at = {-1925, 3502, 246}, to = {-5677, 3502, -572}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter16"] = {at = {-1925, 3502, 246}, to = {-5625, 3502, -780}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter17L"] = {at = {-2847, 3502, 369}, to = {73, 3502, -2125}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter17R"] = {at = {-1925, 3502, 369}, to = {-4849, 3502, -2120}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter18"] = {at = {-2847, 3502, 246}, to = {854, 3502, -780}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter19"] = {at = {-2847, 3502, 246}, to = {905, 3502, -572}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter2"] = {at = {-1925, 3809, 246}, to = {-5625, 3809, -780}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter20"] = {at = {-1925, 3502, 246}, to = {-5661, 3043, -513}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter21"] = {at = {-1925, 3502, 246}, to = {-5586, 2857, -716}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter22"] = {at = {-1925, 3502, 369}, to = {-4953, 2570, -1801}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter23"] = {at = {-1925, 3502, 369}, to = {-4814, 2674, -2022}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter24L"] = {at = {-2847, 3502, 369}, to = {-103, 2503, -2125}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter24R"] = {at = {-1925, 3502, 369}, to = {-4669, 2503, -2125}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter25"] = {at = {-2847, 3502, 369}, to = {72, 2615, -1964}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter26"] = {at = {-2847, 3502, 369}, to = {237, 2790, -1806}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter27"] = {at = {-2847, 3502, 246}, to = {814, 2857, -716}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter28"] = {at = {-2847, 3502, 246}, to = {880, 2978, -520}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter29"] = {at = {-1925, 3195, 246}, to = {-5677, 3195, -572}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter30"] = {at = {-1925, 3195, 246}, to = {-5625, 3195, -780}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter31L"] = {at = {-2847, 3195, 369}, to = {73, 3195, -2125}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter31R"] = {at = {-1925, 3195, 369}, to = {-4849, 3195, -2120}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter32"] = {at = {-2847, 3195, 246}, to = {854, 3195, -780}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter33"] = {at = {-2847, 3195, 246}, to = {905, 3195, -572}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter34"] = {at = {-1925, 3195, 246}, to = {-5661, 2736, -513}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter35"] = {at = {-1925, 3195, 246}, to = {-5586, 2549, -716}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter36"] = {at = {-1925, 3195, 369}, to = {-4953, 2263, -1801}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter37"] = {at = {-1925, 3195, 369}, to = {-4814, 2367, -2022}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter38L"] = {at = {-2847, 3195, 369}, to = {-103, 2196, -2125}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter38R"] = {at = {-1925, 3195, 369}, to = {-4669, 2196, -2125}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter39"] = {at = {-2847, 3195, 369}, to = {72, 2308, -1964}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter3L"] = {at = {-2847, 3809, 369}, to = {73, 3809, -2125}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter3R"] = {at = {-1925, 3809, 369}, to = {-4849, 3809, -2120}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter4"] = {at = {-2847, 3809, 246}, to = {854, 3809, -780}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter40"] = {at = {-2847, 3195, 369}, to = {237, 2483, -1806}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter41"] = {at = {-2847, 3195, 246}, to = {814, 2549, -716}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter42"] = {at = {-2847, 3195, 246}, to = {880, 2671, -520}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter43"] = {at = {-1925, 2888, 246}, to = {-5677, 2888, -572}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter44"] = {at = {-1925, 2888, 246}, to = {-5625, 2888, -780}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter45L"] = {at = {-2847, 2888, 369}, to = {73, 2888, -2125}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter45R"] = {at = {-1925, 2888, 369}, to = {-4849, 2888, -2120}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter46"] = {at = {-2847, 2888, 246}, to = {854, 2888, -780}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter47"] = {at = {-2847, 2888, 246}, to = {905, 2888, -572}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter48"] = {at = {-1925, 2888, 246}, to = {-5661, 2429, -513}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter49"] = {at = {-1925, 2888, 246}, to = {-5586, 2242, -716}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter5"] = {at = {-2847, 3809, 246}, to = {905, 3809, -572}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter50"] = {at = {-1925, 2888, 369}, to = {-4953, 1956, -1801}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter51"] = {at = {-1925, 2888, 369}, to = {-4814, 2059, -2022}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter52L"] = {at = {-2847, 2888, 369}, to = {-103, 1889, -2125}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter52R"] = {at = {-1925, 2888, 369}, to = {-4669, 1889, -2125}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter53"] = {at = {-2847, 2888, 369}, to = {72, 2001, -1964}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter54"] = {at = {-2847, 2888, 369}, to = {237, 2176, -1806}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter55"] = {at = {-2847, 2888, 246}, to = {814, 2242, -716}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter56"] = {at = {-2847, 2888, 246}, to = {880, 2364, -520}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter57"] = {at = {-1925, 2580, 246}, to = {-5677, 2580, -572}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter58"] = {at = {-1925, 2580, 246}, to = {-5625, 2580, -780}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter59L"] = {at = {-2847, 2580, 369}, to = {73, 2580, -2125}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter59R"] = {at = {-1925, 2580, 369}, to = {-4849, 2580, -2120}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter6"] = {at = {-1925, 3809, 246}, to = {-5661, 3351, -513}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter60"] = {at = {-2847, 2580, 246}, to = {854, 2580, -780}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter61"] = {at = {-2847, 2580, 246}, to = {905, 2580, -572}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter7"] = {at = {-1925, 3809, 246}, to = {-5586, 3164, -716}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter8"] = {at = {-1925, 3809, 369}, to = {-4953, 2878, -1801}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
    ["shooter9"] = {at = {-1925, 3809, 369}, to = {-4814, 2981, -2022}, damage = 5, every = 4.00, missile = "Fire", projectile = "FireBolt"},
}
local DAMAGE = {
    ["knockback01"] = {box = {{-2478, 4239, 0}, {-2273, 4669, 246}}, on = true, damage = 5, push = {0, -2048}},
    ["knockback02"] = {box = {{-758, 3830, 655}, {-553, 4157, 901}}, on = true, damage = 5, push = {0, -2048}},
    ["knockback03"] = {box = {{1434, 1946, 737}, {1638, 2273, 983}}, on = true, damage = 5, push = {0, 2048}},
    ["knockback04"] = {box = {{-1495, 1106, 737}, {-1167, 1311, 983}}, on = true, damage = 5, push = {2048, 0}},
    ["knockback05"] = {box = {{-1864, -1495, 0}, {-1659, -1147, 246}}, on = true, damage = 5, push = {0, 2048}},
    ["knockback06"] = {box = {{2478, -1823, 0}, {2806, -1618, 246}}, on = true, damage = 5, push = {-2048, 0}},
    ["knockback08"] = {box = {{1434, -614, -41}, {1638, -123, 205}}, on = true, damage = 5, push = {0, -2048}},
    ["knockback09"] = {box = {{3031, -1085, -41}, {3359, -881, 205}}, on = true, damage = 5, push = {2048, 0}},
    ["knockback10"] = {box = {{3830, -512, -41}, {4157, -307, 205}}, on = true, damage = 5, push = {2048, 0}},
    ["knockback11"] = {box = {{-164, 1106, 0}, {307, 1311, 901}}, on = true, damage = 10, push = {2560, 0}},
    ["knockback12"] = {box = {{-1208, -1966, -41}, {-819, -1700, 205}}, on = true, damage = 5, push = {0, 0}},
    ["knockback13"] = {box = {{-881, -1741, -41}, {-492, -1475, 205}}, on = true, damage = 5, push = {0, 0}},
    ["knockback14"] = {box = {{-512, -1966, -41}, {-143, -1618, 205}}, on = true, damage = 10, push = {0, 0}},
    ["knockback15"] = {box = {{41, -1966, -41}, {143, -1475, 205}}, on = true, damage = 10, push = {0, -1792}},
    ["knockback16"] = {box = {{348, -1946, 20}, {471, -1638, 266}}, on = true, damage = 5, push = {0, -1280}},
    ["knockback17"] = {box = {{512, -1782, 20}, {635, -1475, 266}}, on = true, damage = 5, push = {0, 1280}},
    ["knockback18"] = {box = {{676, -1946, 20}, {799, -1638, 266}}, on = true, damage = 5, push = {0, -1280}},
    ["knockback19"] = {box = {{840, -1966, 20}, {963, -1475, 266}}, on = true, damage = 10, push = {0, 0}},
    ["knockback20"] = {box = {{1741, -1966, -82}, {1925, -1475, -20}}, on = true, damage = 10, push = {-128, 0}},
    ["knockback21"] = {box = {{1966, -1966, 20}, {2150, -1475, 266}}, on = true, damage = 10, push = {2048, 0}},
    ["knockback22"] = {box = {{-1024, 3543, 0}, {-287, 4321, 287}}, on = true, damage = 10, push = {0, 0}},
    ["knockback23"] = {box = {{1311, -1966, 20}, {1638, -1638, 123}}, on = true, damage = 5, push = {0, 0}},
    ["knockback24"] = {box = {{1147, -1802, 20}, {1475, -1475, 123}}, on = true, damage = 5, push = {0, 0}},
}
local TOUCH = {
    ["doubleaxe_lower_trigger"] = {{164, 1106, -67}, {492, 1311, -36}},   -- doubleaxe lower trigger
    ["doubleaxe_upper_trigger"] = {{287, 1106, 650}, {410, 1311, 681}},   -- doubleaxe upper trigger
    ["elevator"] = {{-1864, -594, 850}, {-1659, -389, 881}},   -- elevator
}
local HINTS = {
    {cog = 300, need = 17},
    {cog = 301, need = 17},
    {cog = 302, need = 17},
    {cog = 303, need = 17},
    {cog = 304, need = 17},
    {cog = 305, need = 17},
    {cog = 306, need = 17},
    {cog = 307, need = 17},
    {cog = 308, need = 17},
    {cog = 309, need = 17},
    {cog = 310, need = 17},
    {cog = 311, need = 17},
    {cog = 312, need = 17},
    {cog = 313, need = 17},
    {cog = 314, need = 17},
    {cog = 315, need = 17},
    {cog = 316, need = 17},
}
local TUNNEL = {{-883, 1088, -768}, {883, 1331, -205}}
local SURFACE_WEST, SURFACE_EAST = {-768, 1024, -59}, {758, 1434, -59}

-- A scheduler on the poll (MM9's delays): after(seconds, fn). The poll re-arms itself every 0.1 s and
-- keeps that period (a timer's restart of itself counts from its alarm), so the clock is its ticks.
local tick, tasks, clock, nextHints = 0, {}, 0, 3
local function after(seconds, fn)
    table.insert(tasks, {at = clock + math.max(0.05, seconds), fn = fn})
end
local send
local function run(list) if list then for _, m in ipairs(list) do send(m[1], m[2]) end end end

-- Doors (MM9 DoorBase): state 0 shut, 1 opening, 2 open, 3 closing (map variables S<group>), locks L<group>.
-- A locked door ignores open and close (from messages and clicks alike: a timer lever's lock holds its axe
-- trap). Open/CloseTriggers go out when the door has finished moving; a door that is not Sticky closes
-- CloseWaitTime after it opened (unless locked then); a DoubleDoorName partner moves with it.
local seq = {}
local function state(g) return var("S" .. g) end
local function locked(g) return var("L" .. g) == 1 end
local doorOpen, doorClose
doorOpen = function(g, partner)
    local d = DOOR[g]
    if d == nil or locked(g) then return end
    local s = state(g)
    if s == 1 or s == 2 then return end
    for _, id in ipairs(d.ids) do evt.SetDoorState(id, DoorAction.Open) end
    set("S" .. g, 1)
    seq[g] = (seq[g] or 0) + 1
    local mine = seq[g]
    after(d.open, function()
        if seq[g] ~= mine then return end
        set("S" .. g, 2)
        set("Opened" .. g, var("Opened" .. g) + 1)
        run(d.onOpen)
        if not d.sticky then after(d.wait, function() if seq[g] == mine then doorClose(g) end end) end
    end)
    if d.double ~= nil and not partner then doorOpen(d.double, true) end
end
doorClose = function(g, partner)
    local d = DOOR[g]
    if d == nil or locked(g) then return end
    local s = state(g)
    if s == 0 or s == 3 then return end
    for _, id in ipairs(d.ids) do evt.SetDoorState(id, DoorAction.Close) end
    set("S" .. g, 3)
    seq[g] = (seq[g] or 0) + 1
    local mine = seq[g]
    after(d.close, function()
        if seq[g] ~= mine then return end
        set("S" .. g, 0)
        run(d.onClose)
    end)
    if d.double ~= nil and not partner then doorClose(d.double, true) end
end
local function toggle(g) local s = state(g) if s == 0 or s == 3 then doorOpen(g) else doorClose(g) end end
-- A click (MM9 PushOpen): a locked door jiggles; an open lever or door that is not Sticky closes again.
local function use(g)
    if locked(g) then evt.StatusText("Locked") return end
    set("Used" .. g, var("Used" .. g) + 1)
    toggle(g)
end

-- Shooters (MM9 Shooter: ProjectileName, DamageAmt, ShootInterval, aimed along the object's rotation): on, a
-- shot at once and one every ShootInterval until off; a shot strikes the party in its path (strikesParty).
local firing = {}
local function fire(name)
    local s = SHOOTER[name]
    if evt.FireMissile(s.missile, s.at[1], s.at[2], s.at[3], s.to[1], s.to[2], s.to[3], s.damage, s.missile, 0, 0, true) then
        MM9.launchSound(s.projectile, s.at[1], s.at[2], s.at[3])
    end
    set("Shots", var("Shots") + 1)
    set("Shot" .. key(name), var("Shot" .. key(name)) + 1)
end

-- DamageBrush knockbacks (Damage, Current): while on, the party in the box takes Damage once and is thrown
-- along Current (evt.PushParty: Current's speed, at most 1200, for 0.25 s).
local hitBy = {}
local function damageOn(name) return var("D" .. key(name)) == 1 or (var("D" .. key(name)) == 0 and DAMAGE[name].on) end

-- Chadwick (NPC417.scr): DoTrap (key 244 while the trial runs, key 243), RemoveTrap (the entrance button:
-- the trap mark goes), done (the exit gate: with no trap, key 245 and the quest sound).
local function chadwick(msg)
    if MM9.hasKey(243) == 0 then return end
    if msg == "dotrap" then set("Trap", 1) set("Traps", var("Traps") + 1) MM9.giveKey(244)
    elseif msg == "removetrap" then set("Trap", 0) MM9.takeKey(244)
    elseif msg == "done" and var("Trap") == 0 then MM9.giveKey(245) MM9.playSound("sounds/events/quest.wav") end
end

-- Triggers (MM9 Trigger): enabled from StartOn (T<name>: 1 on, 2 off); a touch (any part of the party in the box,
-- PlayerTriggerable) or a 'trigger' message fires an enabled trigger with no activation pending; SendDelay
-- delays the messages; ActivationCount limits touches (on and trigger reset the count).
local pending = {}
local function triggerOn(name)
    local s = var("T" .. key(name))
    if s == 0 then return TRIGGER[name].on end
    return s == 1
end
local function fireTrigger(name, touched)
    local t = TRIGGER[name]
    if t == nil or not triggerOn(name) or pending[name] then return end
    if touched and t.count > 0 and var("C" .. key(name)) >= t.count then return end
    if not touched then set("C" .. key(name), 0) end
    pending[name] = true
    after(t.delay, function()
        pending[name] = nil
        set("C" .. key(name), var("C" .. key(name)) + 1)
        set("Fired" .. key(name), var("Fired" .. key(name)) + 1)
        run(t.msgs)
    end)
end

-- The dispatcher: MM9's object messages (target, message) as the DAT links them; targets the DAT does not have
-- (rat, ratnormal ... the cut rat cameo, knockback25-29) are ignored, as MM9 ignores them.
send = function(target, msg)
    local kind = KIND[target]
    msg = string.lower(msg)
    if kind == "trigger" then
        if msg == "on" then set("T" .. key(target), 1) set("C" .. key(target), 0)
        elseif msg == "off" then set("T" .. key(target), 2)
        elseif msg == "trigger" then fireTrigger(target, false) end
    elseif kind == "door" then
        local g = MODEL_GROUP[target]
        if msg == "open" then doorOpen(g)
        elseif msg == "close" then doorClose(g)
        elseif msg == "toggle" or msg == "use" or msg == "trigger" then toggle(g)
        elseif msg == "lock" then set("L" .. g, 1)
        elseif msg == "unlock" then set("L" .. g, 0) end
    elseif kind == "shooter" then
        if msg == "on" then if firing[target] == nil then fire(target) firing[target] = clock + SHOOTER[target].every end
        elseif msg == "off" then firing[target] = nil end
    elseif kind == "damage" then
        if msg == "on" then set("D" .. key(target), 1) hitBy[target] = nil
        elseif msg == "off" then set("D" .. key(target), 2) end
    elseif kind == "saw" then   -- RotatingBrush: its mover's spin (scene mover.spin)
        if msg == "on" then set("Saw" .. key(target), 1) elseif msg == "off" then set("Saw" .. key(target), 0) end
        if DOORS[target] ~= nil and (msg == "on" or msg == "off" or msg == "toggle" or msg == "reverse") then
            evt.SpinMover(DOORS[target], msg)
        end
    elseif kind == "npc" then
        if MM9.receives("dungeonofsecrets", target, msg, 0) then chadwick(msg) end
    end
end

-- Clicks: MM9 PushOpen doors and levers (axe doors, timer levers, the fake levers, the entrance button, the
-- water grate).
handlers[200] = function() use("axe_door_01") end
handlers[201] = function() use("axe_door_02") end
handlers[202] = function() use("axe_door_03") end
handlers[203] = function() use("axe_door_04") end
handlers[204] = function() use("axe_door_05") end
handlers[205] = function() use("axe_door_06") end
handlers[206] = function() use("axe_door_08") end
handlers[207] = function() use("axe_door_09") end
handlers[208] = function() use("axe_door_10") end
handlers[209] = function() use("timer_lever_01") end
handlers[210] = function() use("timer_lever_02") end
handlers[211] = function() use("timer_lever_03") end
handlers[212] = function() use("timer_lever_03a") end
handlers[213] = function() use("timer_lever_04") end
handlers[214] = function() use("timer_lever_05") end
handlers[215] = function() use("timer_lever_06") end
handlers[216] = function() use("timer_lever_08") end
handlers[217] = function() use("timer_lever_09") end
handlers[218] = function() use("timer_lever_10") end
handlers[219] = function() use("fake_lever_1") end
handlers[220] = function() use("fake_lever_2") end
handlers[221] = function() use("fake_lever_3") end
handlers[222] = function() use("fake_lever_4") end
handlers[223] = function() use("fake_lever_5") end
handlers[224] = function() use("fake_lever_6") end
handlers[225] = function() use("fake_lever_7") end
handlers[226] = function() use("fake_lever_8") end
handlers[227] = function() use("fake_lever_9") end
handlers[228] = function() use("fake_lever_10") end
handlers[229] = function() use("fake_lever_11") end
handlers[230] = function() use("fake_lever_12") end
handlers[231] = function() use("fake_lever_13") end
handlers[232] = function() use("fake_lever_14") end
handlers[233] = function() use("fake_lever_15") end
handlers[234] = function() use("fake_lever_16") end
handlers[235] = function() use("fake_lever_17") end
handlers[236] = function() use("fake_lever_18") end
handlers[237] = function() use("fake_lever_19") end
handlers[238] = function() use("fake_lever_20") end
handlers[239] = function() use("fake_lever_21") end
handlers[240] = function() use("entrance_button") end
handlers[241] = function() use("water_grate") end

-- Chadwick's dialogue exit (NPC417.scr :OnRude, RUDE 417): with key 246 (the reward topic) and no key 247, 10000 experience,
-- the quest sound and key 247.
handlers[50636] = function()
    if MM9.hasKey(247) == 0 and MM9.hasKey(246) == 1 then
        MM9.giveExperience(10000)
        MM9.playSound("sounds/events/quest.wav")
        MM9.giveKey(247)
    end
end

-- Perception hints (PerceptionBrush, PerceptionValue): shown to a party with that Perception (checked every
-- 3 s, Dark Passageway's route).
local function showHints()
    for _, h in ipairs(HINTS) do
        local want = evt.CheckSkill(29, 0, h.need) and 2 or 1
        if var("Hint" .. h.cog) ~= want then
            set("Hint" .. h.cog, want)
            evt.SetFacetBit(h.cog, FacetBits.Invisible, want == 1)
        end
    end
end

-- The poll (ten times a second): MM9's touch volumes against the party's path since the last poll (a fast
-- party crosses a 4-unit plate trigger in one step), TouchToOpen doors, knockbacks, shooters, waits.
local function crosses(b, ax, ay, az, bx, by, bz)
    local lo = {b[1][1] - 37, b[1][2] - 37, b[1][3] - 170}
    local hi = {b[2][1] + 37, b[2][2] + 37, b[2][3]}
    local a, d = {ax, ay, az}, {bx - ax, by - ay, bz - az}
    local t0, t1 = 0, 1
    for i = 1, 3 do
        if math.abs(d[i]) < 0.001 then
            if a[i] < lo[i] or a[i] > hi[i] then return false end
        else
            local u, v = (lo[i] - a[i]) / d[i], (hi[i] - a[i]) / d[i]
            if u > v then u, v = v, u end
            if u > t0 then t0 = u end
            if v < t1 then t1 = v end
            if t0 > t1 then return false end
        end
    end
    return true
end
local sunk = false
local last, inside = nil, {}   -- a touch fires when the party comes into a box (MM9 touches while it moves)
handlers[380] = function()
    evt.StartTimer(380, seconds(0.1))
    tick = tick + 1
    clock = tick * 0.1
    set("Clock10", math.floor(clock * 10))
    local x, y, z = evt.GetPartyPosition()
    local px, py, pz = x, y, z
    if last ~= nil and math.abs(last[1] - x) + math.abs(last[2] - y) + math.abs(last[3] - z) < 600 then
        px, py, pz = last[1], last[2], last[3]
    end
    last = {x, y, z}
    for name, t in pairs(TRIGGER) do
        if t.touch then
            local now = crosses(t.box, px, py, pz, x, y, z)
            if now and not inside[name] then fireTrigger(name, true) end
            inside[name] = now
        end
    end
    for g, b in pairs(TOUCH) do
        if state(g) == 0 and not locked(g) and crosses(b, px, py, pz, x, y, z) then doorOpen(g) end
    end
    for name, d in pairs(DAMAGE) do
        if damageOn(name) and not hitBy[name] and crosses(d.box, px, py, pz, x, y, z) then
            hitBy[name] = true
            hurt(d.damage)
            set("Knocked" .. key(name), var("Knocked" .. key(name)) + 1)
            local speed = math.sqrt(d.push[1] * d.push[1] + d.push[2] * d.push[2])
            if speed > 1 then
                evt.PushParty(d.push[1], d.push[2], math.min(speed, 1200) * 0.25)
            end
        elseif not damageOn(name) then hitBy[name] = nil end
    end
    for name, at in pairs(firing) do
        if clock >= at then fire(name) firing[name] = clock + SHOOTER[name].every end
    end
    local due = {}
    for i = #tasks, 1, -1 do if tasks[i].at <= clock then table.insert(due, 1, tasks[i].fn) table.remove(tasks, i) end end
    for _, fn in ipairs(due) do fn() end
    if clock >= nextHints then nextHints = clock + 3 showHints() end
end

-- Map load: the doors' DAT locks once; doors caught moving by a save end where they were going; NPC417.scr :Init
-- (a fresh trial on every visit: keys 243 and 244 go); the hints; the poll.
handlers[1] = function()
    if var("Loaded") == 0 then
        set("Loaded", 1)
        for g, d in pairs(DOOR) do if d.locked then set("L" .. g, 1) end end
    end
    for g, _ in pairs(DOOR) do
        if state(g) == 1 then set("S" .. g, 2) elseif state(g) == 3 then set("S" .. g, 0) end
        if state(g) == 2 and not DOOR[g].sticky and not locked(g) then doorClose(g) end
    end
    MM9.takeKey(243)
    MM9.takeKey(244)
    set("Trap", 0)
    for _, h in ipairs(HINTS) do set("Hint" .. h.cog, 0) end
    showHints()
    evt.StartTimer(380, seconds(0.1))
end
-- MM9's TouchToOpen doors: walking into one opens it (a 4 Hz poll of the party's position).
local TOUCH_DOORS = {
    {door = 27, box = {{127, 1069, -129}, {529, 1348, -56}}},   -- doubleaxe lower trigger
    {door = 28, box = {{250, 1069, 577}, {447, 1348, 660}}},   -- doubleaxe upper trigger
    {door = 29, box = {{-1901, -631, -78}, {-1622, -352, 860}}},   -- elevator
}
handlers[900] = function()
    local x, y, z = evt.GetPartyPosition()
    for _, t in ipairs(TOUCH_DOORS) do
        local b = t.box
        if x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2]
                and z >= b[1][3] and z <= b[2][3] then
            evt.SetDoorState(t.door, DoorAction.Open)   -- an open door ignores it; a closing one reopens
        end
    end
    evt.StartTimer(900, seconds(0.25))
end

-- MM9's greeting voices (dungeon/voices.py): a click on these people plays their GreetingSound or the
-- voice their script's :OnUse plays, then opens their dialogue (or runs the map's own click).
handlers[53636] = function() MM9.playSound("voices/npc/npc_189.wav"); MM9.openRude(417) end   -- CHADWICK

-- MM9's touch Triggers switching AmbientSounds (dungeon/objects.py): entering one sends its On / Off / Toggle
-- (the scene sound's map variable AmbientSound<key>: 1 on, 2 off); ActivationCount limits the uses.
local SOUND_TRIGGERS = {
    {name = "rat death start", box = {{-2925, 1903, -175}, {-1827, 2029, 251}}, uses = 1, switches = {{602, "off", true}, {603, "off", true}, {604, "off", true}, {605, "off", true}}},
}
local soundInside = {}
handlers[903] = function()
    local x, y, z = evt.GetPartyPosition()
    for _, t in ipairs(SOUND_TRIGGERS) do
        local b = t.box
        local now = x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] and z >= b[1][3] and z <= b[2][3]
        if now and not soundInside[t.name] and (t.uses == 0 or var("SoundUses" .. t.name) < t.uses) then
            set("SoundUses" .. t.name, var("SoundUses" .. t.name) + 1)
            for _, s in ipairs(t.switches) do
                local name = "AmbientSound" .. s[1]
                local on = var(name) == 1 or (var(name) == 0 and s[3])
                local want = (s[2] == "on" or (s[2] == "toggle" and not on)) and 1 or 2
                set(name, want)
            end
        end
        soundInside[t.name] = now
    end
    evt.StartTimer(903, seconds(0.25))
end
handlers[902] = function()   -- map load: the shared objects
    handlers[903]()
end

RegisterEvent(200, "Door", handlers[200], "Door")
RegisterEvent(201, "Door", handlers[201], "Door")
RegisterEvent(202, "Door", handlers[202], "Door")
RegisterEvent(203, "Door", handlers[203], "Door")
RegisterEvent(204, "Door", handlers[204], "Door")
RegisterEvent(205, "Door", handlers[205], "Door")
RegisterEvent(206, "Door", handlers[206], "Door")
RegisterEvent(207, "Door", handlers[207], "Door")
RegisterEvent(208, "Door", handlers[208], "Door")
RegisterEvent(209, "Lever", handlers[209], "Lever")
RegisterEvent(210, "Lever", handlers[210], "Lever")
RegisterEvent(211, "Lever", handlers[211], "Lever")
RegisterEvent(212, "Lever", handlers[212], "Lever")
RegisterEvent(213, "Lever", handlers[213], "Lever")
RegisterEvent(214, "Lever", handlers[214], "Lever")
RegisterEvent(215, "Lever", handlers[215], "Lever")
RegisterEvent(216, "Lever", handlers[216], "Lever")
RegisterEvent(217, "Lever", handlers[217], "Lever")
RegisterEvent(218, "Lever", handlers[218], "Lever")
RegisterEvent(219, "Lever", handlers[219], "Lever")
RegisterEvent(220, "Lever", handlers[220], "Lever")
RegisterEvent(221, "Lever", handlers[221], "Lever")
RegisterEvent(222, "Lever", handlers[222], "Lever")
RegisterEvent(223, "Lever", handlers[223], "Lever")
RegisterEvent(224, "Lever", handlers[224], "Lever")
RegisterEvent(225, "Lever", handlers[225], "Lever")
RegisterEvent(226, "Lever", handlers[226], "Lever")
RegisterEvent(227, "Lever", handlers[227], "Lever")
RegisterEvent(228, "Lever", handlers[228], "Lever")
RegisterEvent(229, "Lever", handlers[229], "Lever")
RegisterEvent(230, "Lever", handlers[230], "Lever")
RegisterEvent(231, "Lever", handlers[231], "Lever")
RegisterEvent(232, "Lever", handlers[232], "Lever")
RegisterEvent(233, "Lever", handlers[233], "Lever")
RegisterEvent(234, "Lever", handlers[234], "Lever")
RegisterEvent(235, "Lever", handlers[235], "Lever")
RegisterEvent(236, "Lever", handlers[236], "Lever")
RegisterEvent(237, "Lever", handlers[237], "Lever")
RegisterEvent(238, "Lever", handlers[238], "Lever")
RegisterEvent(239, "Lever", handlers[239], "Lever")
RegisterEvent(240, "Lever", handlers[240], "Lever")
RegisterEvent(241, "Door", handlers[241], "Door")
RegisterEvent(1, "Map load", handlers[1])
RegisterMapTimerEvent(380, seconds(3), handlers[380], "Poll", "", seconds(3))
RegisterEvent(50636, "Chadwick", handlers[50636])
RegisterMapTimerEvent(900, seconds(3), handlers[900], "Touch doors", "", seconds(3))
RegisterEvent(53636, "Chadwick Boorsley", handlers[53636])
RegisterMapTimerEvent(903, seconds(3), handlers[903], "Ambient triggers", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
