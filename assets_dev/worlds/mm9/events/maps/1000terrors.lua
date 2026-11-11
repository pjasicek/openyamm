-- Thousand Terrors, MM9 rework (level_generation/projects/mm9r_1000terrors/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {CoffinGate1 = 1, CoffinGate2 = 2, Door0 = 3, Door1 = 4, EDoor3 = 5, EDoor4 = 6, ElevatorGear1 = 12, ElevatorGear2 = 13, FireballPlate = 7, FireballPlate2 = 8, FoyerDoorSouth1 = 9, FoyerDoorSouth2 = 10, FoyerShooterPlate = 11, GearElevator = 14, HiddenButton1 = 15, IronDoor0 = 16, LowerDoor10 = 33, LowerDoor13 = 20, LowerDoor14 = 21, LowerDoor15 = 22, LowerDoor16 = 23, LowerDoor17 = 24, LowerDoor18 = 25, LowerDoor3 = 26, LowerDoor4 = 27, LowerDoor5 = 28, LowerDoor6 = 29, LowerDoor7 = 30, LowerDoor8 = 31, LowerDoor9 = 32, LowerLever = 34, LowerLever0 = 35, MiddleDoor4 = 36, MiddleDoor5 = 37, Pull1 = 38, Pull2 = 39, Pull3 = 40, PuzzleDoor0 = 41, PuzzleDoor1 = 42, PuzzleDoor10 = 43, PuzzleDoor11 = 44, PuzzleDoor12 = 45, PuzzleDoor13 = 46, PuzzleDoor14 = 47, PuzzleDoor15 = 48, PuzzleDoor2 = 49, PuzzleDoor3 = 50, PuzzleDoor4 = 51, PuzzleDoor5 = 52, PuzzleDoor6 = 53, PuzzleDoor7 = 54, PuzzleDoor8 = 55, PuzzleDoor9 = 56, PuzzleDoorB0 = 57, PuzzleDoorB1 = 58, PuzzleDoorB10 = 59, PuzzleDoorB11 = 60, PuzzleDoorB12 = 61, PuzzleDoorB13 = 62, PuzzleDoorB14 = 63, PuzzleDoorB15 = 64, PuzzleDoorB2 = 65, PuzzleDoorB3 = 66, PuzzleDoorB4 = 67, PuzzleDoorB5 = 68, PuzzleDoorB6 = 69, PuzzleDoorB7 = 70, PuzzleDoorB8 = 71, PuzzleDoorB9 = 72, PuzzleDoorC0 = 73, PuzzleDoorC1 = 74, PuzzleDoorC10 = 75, PuzzleDoorC11 = 76, PuzzleDoorC12 = 77, PuzzleDoorC13 = 78, PuzzleDoorC14 = 79, PuzzleDoorC15 = 80, PuzzleDoorC2 = 81, PuzzleDoorC3 = 82, PuzzleDoorC4 = 83, PuzzleDoorC5 = 84, PuzzleDoorC6 = 85, PuzzleDoorC7 = 86, PuzzleDoorC8 = 87, PuzzleDoorC9 = 88, RotatingDoor0 = 89, RotatingDoor1 = 90, Rotating_Lever_16 = 17, Rotating_Lever_17 = 18, Rotating_Lever_18 = 19, SBrick0 = 91, SBrick1 = 92, SecretDoor2 = 93, ShooterPlate1 = 94, ShooterPlate10 = 95, ShooterPlate11 = 96, ShooterPlate12 = 97, ShooterPlate14 = 98, ShooterPlate2 = 99, ShooterPlate3 = 100, ShooterPlate4 = 101, ShooterPlate5 = 102, ShooterPlate6 = 103, ShooterPlate7 = 104, ShooterPlate8 = 105, ShooterPlate9 = 106, StairGate = 107, StairGate0 = 108, ToLowerTombGate = 109, ToWindMazeGate = 110, TrapDoor1 = 112, TrapDoor2 = 111, TrapTrigger0 = 113, TrapTrigger1 = 114, TrapTrigger2 = 115, TrapTrigger3 = 116, TrapTrigger4 = 117, TrapTrigger5 = 118, TreasureDoor = 119, TreasureDoor0 = 120, WaterGate0 = 121, WaterGate1 = 122, WaterGate2 = 123, WeightedLift0 = 124, WeightedLift1 = 125, WeightedLift10 = 126, WeightedLift11 = 127, WeightedLift13 = 128, WeightedLift14 = 129, WeightedLift15 = 130, WeightedLift3 = 131, WeightedLift4 = 132, WeightedLift5 = 133, WeightedLift6 = 134, WeightedLift7 = 135, WeightedLift8 = 136, WeightedLift9 = 137}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 902}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}, [44] = {3}, [45] = {4}, [46] = {5}, [47] = {6}, [48] = {7}, [49] = {8}, [50] = {9}, [51] = {10}, [52] = {11}, [53] = {12}, [54] = {13}}})

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest4
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest5
handlers[43] = function() evt.OpenChest(2) end   -- TreasureChest6
handlers[44] = function() evt.OpenChest(3) end   -- TreasureChest11
handlers[45] = function() evt.OpenChest(4) end   -- TreasureChest12
handlers[46] = function() evt.OpenChest(5) end   -- TreasureChest7
handlers[47] = function() evt.OpenChest(6) end   -- TreasureChest8
handlers[48] = function() evt.OpenChest(7) end   -- TreasureChest9
handlers[49] = function() evt.OpenChest(8) end   -- TreasureChest10
handlers[50] = function() evt.OpenChest(9) end   -- TreasureChest1
handlers[51] = function() evt.OpenChest(10) end   -- TreasureChest0
handlers[52] = function() evt.OpenChest(11) end   -- TreasureChest2
handlers[53] = function() evt.OpenChest(12) end   -- KeyChest3
handlers[54] = function() evt.OpenChest(13) end   -- TreasureChest3

local function inBox(b, x, y, z) return x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] and z + 170 >= b[1][3] and z <= b[2][3] end
local function give(raw, source)
    local item = MM9.ItemIds[raw]
    if item ~= nil and evt.GivePartyMemberItem(math.max(0, evt.GetCurrentPlayerIndex()), item) then return true end
    return MM9.giveItem(raw, source)
end
local function hurt(amount) evt.DamagePlayer(Players.All, const.Damage.Physical, amount) end

-- Door groups (overrides.yml) by DAT model, and their MM9 Open/CloseTrigger messages.
local GROUPS = {CoffinGate1 = {1}, CoffinGate2 = {2}, Door0 = {3}, Door1 = {4}, EDoor = {5, 6}, FireballPlate = {7}, FireballPlate2 = {8}, FoyerDoorSouth = {9, 10}, FoyerShooterPlate = {11}, GearElevator = {12, 13, 14}, HiddenButton1 = {15}, IronDoor0 = {16}, Lever16 = {17}, Lever17 = {18}, Lever18 = {19}, LowerDoor13 = {20, 21}, LowerDoor15 = {22, 23}, LowerDoor17 = {24, 25}, LowerDoor3 = {26, 27}, LowerDoor5 = {28, 29}, LowerDoor7 = {30, 31}, LowerDoor9 = {32, 33}, LowerLever = {34}, LowerLever0 = {35}, MiddleDoor4 = {36}, MiddleDoor5 = {37}, Pull1 = {38}, Pull2 = {39}, Pull3 = {40}, PuzzleDoor0 = {41}, PuzzleDoor1 = {42}, PuzzleDoor10 = {43}, PuzzleDoor11 = {44}, PuzzleDoor12 = {45}, PuzzleDoor13 = {46}, PuzzleDoor14 = {47}, PuzzleDoor15 = {48}, PuzzleDoor2 = {49}, PuzzleDoor3 = {50}, PuzzleDoor4 = {51}, PuzzleDoor5 = {52}, PuzzleDoor6 = {53}, PuzzleDoor7 = {54}, PuzzleDoor8 = {55}, PuzzleDoor9 = {56}, PuzzleDoorB0 = {57}, PuzzleDoorB1 = {58}, PuzzleDoorB10 = {59}, PuzzleDoorB11 = {60}, PuzzleDoorB12 = {61}, PuzzleDoorB13 = {62}, PuzzleDoorB14 = {63}, PuzzleDoorB15 = {64}, PuzzleDoorB2 = {65}, PuzzleDoorB3 = {66}, PuzzleDoorB4 = {67}, PuzzleDoorB5 = {68}, PuzzleDoorB6 = {69}, PuzzleDoorB7 = {70}, PuzzleDoorB8 = {71}, PuzzleDoorB9 = {72}, PuzzleDoorC0 = {73}, PuzzleDoorC1 = {74}, PuzzleDoorC10 = {75}, PuzzleDoorC11 = {76}, PuzzleDoorC12 = {77}, PuzzleDoorC13 = {78}, PuzzleDoorC14 = {79}, PuzzleDoorC15 = {80}, PuzzleDoorC2 = {81}, PuzzleDoorC3 = {82}, PuzzleDoorC4 = {83}, PuzzleDoorC5 = {84}, PuzzleDoorC6 = {85}, PuzzleDoorC7 = {86}, PuzzleDoorC8 = {87}, PuzzleDoorC9 = {88}, RotatingDoor0 = {89}, RotatingDoor1 = {90}, SBrick = {91, 92}, SecretDoor2 = {93}, ShooterPlate1 = {94}, ShooterPlate10 = {95}, ShooterPlate11 = {96}, ShooterPlate12 = {97}, ShooterPlate14 = {98}, ShooterPlate2 = {99}, ShooterPlate3 = {100}, ShooterPlate4 = {101}, ShooterPlate5 = {102}, ShooterPlate6 = {103}, ShooterPlate7 = {104}, ShooterPlate8 = {105}, ShooterPlate9 = {106}, StairGate = {107}, StairGate0 = {108}, ToLowerTombGate = {109}, ToWindMazeGate = {110}, TrapDoor = {111, 112}, TrapTrigger0 = {113}, TrapTrigger1 = {114}, TrapTrigger2 = {115}, TrapTrigger3 = {116}, TrapTrigger4 = {117}, TrapTrigger5 = {118}, TreasureDoor = {119}, TreasureDoor0 = {120}, WaterGate0 = {121}, WaterGate1 = {122}, WaterGate2 = {123}, WeightedLift0 = {124}, WeightedLift1 = {125}, WeightedLift10 = {126}, WeightedLift11 = {127}, WeightedLift13 = {128}, WeightedLift14 = {129}, WeightedLift15 = {130}, WeightedLift3 = {131}, WeightedLift4 = {132}, WeightedLift5 = {133}, WeightedLift6 = {134}, WeightedLift7 = {135}, WeightedLift8 = {136}, WeightedLift9 = {137}}
local MODEL_GROUP = {["CoffinGate1"] = "CoffinGate1", ["CoffinGate2"] = "CoffinGate2", ["Door0"] = "Door0", ["Door1"] = "Door1", ["EDoor3"] = "EDoor", ["EDoor4"] = "EDoor", ["ElevatorGear1"] = "GearElevator", ["ElevatorGear2"] = "GearElevator", ["FireballPlate"] = "FireballPlate", ["FireballPlate2"] = "FireballPlate2", ["FoyerDoorSouth1"] = "FoyerDoorSouth", ["FoyerDoorSouth2"] = "FoyerDoorSouth", ["FoyerShooterPlate"] = "FoyerShooterPlate", ["GearElevator"] = "GearElevator", ["HiddenButton1"] = "HiddenButton1", ["IronDoor0"] = "IronDoor0", ["LowerDoor10"] = "LowerDoor9", ["LowerDoor13"] = "LowerDoor13", ["LowerDoor14"] = "LowerDoor13", ["LowerDoor15"] = "LowerDoor15", ["LowerDoor16"] = "LowerDoor15", ["LowerDoor17"] = "LowerDoor17", ["LowerDoor18"] = "LowerDoor17", ["LowerDoor3"] = "LowerDoor3", ["LowerDoor4"] = "LowerDoor3", ["LowerDoor5"] = "LowerDoor5", ["LowerDoor6"] = "LowerDoor5", ["LowerDoor7"] = "LowerDoor7", ["LowerDoor8"] = "LowerDoor7", ["LowerDoor9"] = "LowerDoor9", ["LowerLever"] = "LowerLever", ["LowerLever0"] = "LowerLever0", ["MiddleDoor4"] = "MiddleDoor4", ["MiddleDoor5"] = "MiddleDoor5", ["Pull1"] = "Pull1", ["Pull2"] = "Pull2", ["Pull3"] = "Pull3", ["PuzzleDoor0"] = "PuzzleDoor0", ["PuzzleDoor1"] = "PuzzleDoor1", ["PuzzleDoor10"] = "PuzzleDoor10", ["PuzzleDoor11"] = "PuzzleDoor11", ["PuzzleDoor12"] = "PuzzleDoor12", ["PuzzleDoor13"] = "PuzzleDoor13", ["PuzzleDoor14"] = "PuzzleDoor14", ["PuzzleDoor15"] = "PuzzleDoor15", ["PuzzleDoor2"] = "PuzzleDoor2", ["PuzzleDoor3"] = "PuzzleDoor3", ["PuzzleDoor4"] = "PuzzleDoor4", ["PuzzleDoor5"] = "PuzzleDoor5", ["PuzzleDoor6"] = "PuzzleDoor6", ["PuzzleDoor7"] = "PuzzleDoor7", ["PuzzleDoor8"] = "PuzzleDoor8", ["PuzzleDoor9"] = "PuzzleDoor9", ["PuzzleDoorB0"] = "PuzzleDoorB0", ["PuzzleDoorB1"] = "PuzzleDoorB1", ["PuzzleDoorB10"] = "PuzzleDoorB10", ["PuzzleDoorB11"] = "PuzzleDoorB11", ["PuzzleDoorB12"] = "PuzzleDoorB12", ["PuzzleDoorB13"] = "PuzzleDoorB13", ["PuzzleDoorB14"] = "PuzzleDoorB14", ["PuzzleDoorB15"] = "PuzzleDoorB15", ["PuzzleDoorB2"] = "PuzzleDoorB2", ["PuzzleDoorB3"] = "PuzzleDoorB3", ["PuzzleDoorB4"] = "PuzzleDoorB4", ["PuzzleDoorB5"] = "PuzzleDoorB5", ["PuzzleDoorB6"] = "PuzzleDoorB6", ["PuzzleDoorB7"] = "PuzzleDoorB7", ["PuzzleDoorB8"] = "PuzzleDoorB8", ["PuzzleDoorB9"] = "PuzzleDoorB9", ["PuzzleDoorC0"] = "PuzzleDoorC0", ["PuzzleDoorC1"] = "PuzzleDoorC1", ["PuzzleDoorC10"] = "PuzzleDoorC10", ["PuzzleDoorC11"] = "PuzzleDoorC11", ["PuzzleDoorC12"] = "PuzzleDoorC12", ["PuzzleDoorC13"] = "PuzzleDoorC13", ["PuzzleDoorC14"] = "PuzzleDoorC14", ["PuzzleDoorC15"] = "PuzzleDoorC15", ["PuzzleDoorC2"] = "PuzzleDoorC2", ["PuzzleDoorC3"] = "PuzzleDoorC3", ["PuzzleDoorC4"] = "PuzzleDoorC4", ["PuzzleDoorC5"] = "PuzzleDoorC5", ["PuzzleDoorC6"] = "PuzzleDoorC6", ["PuzzleDoorC7"] = "PuzzleDoorC7", ["PuzzleDoorC8"] = "PuzzleDoorC8", ["PuzzleDoorC9"] = "PuzzleDoorC9", ["Rotating Lever 16"] = "Lever16", ["Rotating Lever 17"] = "Lever17", ["Rotating Lever 18"] = "Lever18", ["RotatingDoor0"] = "RotatingDoor0", ["RotatingDoor1"] = "RotatingDoor1", ["SBrick0"] = "SBrick", ["SBrick1"] = "SBrick", ["SecretDoor2"] = "SecretDoor2", ["ShooterPlate1"] = "ShooterPlate1", ["ShooterPlate10"] = "ShooterPlate10", ["ShooterPlate11"] = "ShooterPlate11", ["ShooterPlate12"] = "ShooterPlate12", ["ShooterPlate14"] = "ShooterPlate14", ["ShooterPlate2"] = "ShooterPlate2", ["ShooterPlate3"] = "ShooterPlate3", ["ShooterPlate4"] = "ShooterPlate4", ["ShooterPlate5"] = "ShooterPlate5", ["ShooterPlate6"] = "ShooterPlate6", ["ShooterPlate7"] = "ShooterPlate7", ["ShooterPlate8"] = "ShooterPlate8", ["ShooterPlate9"] = "ShooterPlate9", ["StairGate"] = "StairGate", ["StairGate0"] = "StairGate0", ["ToLowerTombGate"] = "ToLowerTombGate", ["ToWindMazeGate"] = "ToWindMazeGate", ["TrapDoor1"] = "TrapDoor", ["TrapDoor2"] = "TrapDoor", ["TrapTrigger0"] = "TrapTrigger0", ["TrapTrigger1"] = "TrapTrigger1", ["TrapTrigger2"] = "TrapTrigger2", ["TrapTrigger3"] = "TrapTrigger3", ["TrapTrigger4"] = "TrapTrigger4", ["TrapTrigger5"] = "TrapTrigger5", ["TreasureDoor"] = "TreasureDoor", ["TreasureDoor0"] = "TreasureDoor0", ["WaterGate0"] = "WaterGate0", ["WaterGate1"] = "WaterGate1", ["WaterGate2"] = "WaterGate2", ["WeightedLift0"] = "WeightedLift0", ["WeightedLift1"] = "WeightedLift1", ["WeightedLift10"] = "WeightedLift10", ["WeightedLift11"] = "WeightedLift11", ["WeightedLift13"] = "WeightedLift13", ["WeightedLift14"] = "WeightedLift14", ["WeightedLift15"] = "WeightedLift15", ["WeightedLift3"] = "WeightedLift3", ["WeightedLift4"] = "WeightedLift4", ["WeightedLift5"] = "WeightedLift5", ["WeightedLift6"] = "WeightedLift6", ["WeightedLift7"] = "WeightedLift7", ["WeightedLift8"] = "WeightedLift8", ["WeightedLift9"] = "WeightedLift9"}
local ON_OPEN = {GearElevator = {{"ElevatorGear1", "reverse"}, {"ElevatorGear1", "toggle"}, {"ElevatorGear2", "reverse"}, {"ElevatorGear2", "toggle"}}, HiddenButton1 = {{"HiddenButton1", "lock"}, {"TreasureDoor", "open"}, {"TreasureDoor0", "open"}, {"AITrk86", "on"}}, Lever16 = {{"Upper Chomper 2", "open"}}, Lever17 = {{"TrapDoor1", "open"}}, Lever18 = {{"Upper Chomper 1", "open"}}, LowerLever = {{"ElevatorGear1", "toggle"}, {"ElevatorGear2", "toggle"}, {"GearElevator", "toggle"}}, MiddleDoor4 = {{"MiddleDoor4", "lock"}}, MiddleDoor5 = {{"SorceressStatue6", "go"}, {"SorceressStatue7", "go"}, {"MiddleDoor5", "lock"}}, Pull1 = {{"ButtonTrigger", "reset"}}, Pull2 = {{"ButtonTrigger0", "reset"}}, Pull3 = {{"ButtonTrigger1", "reset"}}, StairGate = {{"AITrk57", "on"}}, TrapTrigger0 = {{"SorceressStatue0", "go"}, {"SorceressStatue1", "go"}}, TrapTrigger2 = {{"SorceressStatue2", "go"}, {"SorceressStatue3", "go"}}, TrapTrigger4 = {{"SorceressStatue4", "go"}}, TrapTrigger5 = {{"SorceressStatue5", "go"}}}
local ON_CLOSE = {FireballPlate = {{"Shooter18", "off"}, {"Shooter19", "off"}, {"Shooter20", "off"}, {"Trigger3", "on"}}, FireballPlate2 = {{"Shooter21", "off"}, {"Shooter22", "off"}, {"Shooter23", "off"}, {"Trigger4", "on"}}, FoyerShooterPlate = {{"FoyerShooterTrigger2", "trigger"}, {"FoyerShooterTrigger", "on"}}, GearElevator = {{"ElevatorGear1", "reverse"}, {"ElevatorGear2", "reverse"}, {"ElevatorGear1", "off"}, {"ElevatorGear2", "off"}}, LowerLever = {{"ElevatorGear1", "toggle"}, {"ElevatorGear2", "toggle"}, {"GearElevator", "toggle"}}, MiddleDoor4 = {{"MiddleDoor4", "lock"}}, MiddleDoor5 = {{"MiddleDoor5", "lock"}}, ShooterPlate1 = {{"Shooter5", "off"}, {"Shooter6", "off"}, {"Trigger5", "on"}}, ShooterPlate10 = {{"Shooter5", "off"}, {"Shooter6", "off"}, {"Trigger14", "on"}}, ShooterPlate11 = {{"Shooter3", "off"}, {"Shooter4", "off"}, {"Trigger15", "on"}}, ShooterPlate12 = {{"Shooter1", "off"}, {"Shooter2", "off"}, {"Trigger16", "on"}}, ShooterPlate14 = {{"Shooter3", "off"}, {"Shooter4", "off"}, {"Trigger17", "on"}}, ShooterPlate2 = {{"Shooter3", "off"}, {"Shooter4", "off"}, {"Trigger6", "on"}}, ShooterPlate3 = {{"Shooter1", "off"}, {"Shooter2", "off"}, {"Trigger7", "on"}}, ShooterPlate4 = {{"Shooter5", "off"}, {"Shooter6", "off"}, {"Trigger8", "on"}}, ShooterPlate5 = {{"Shooter3", "off"}, {"Shooter4", "off"}, {"Trigger9", "on"}}, ShooterPlate6 = {{"Shooter1", "off"}, {"Shooter2", "off"}, {"Trigger10", "on"}}, ShooterPlate7 = {{"Shooter5", "off"}, {"Shooter6", "off"}, {"Trigger11", "on"}}, ShooterPlate8 = {{"Shooter3", "off"}, {"Shooter4", "off"}, {"Trigger12", "on"}}, ShooterPlate9 = {{"Shooter1", "off"}, {"Shooter2", "off"}, {"Trigger13", "on"}}}
local KIND = {["AmphibiousTerror0"] = "actor", ["ButtonTrigger"] = "script", ["ButtonTrigger0"] = "script", ["ButtonTrigger1"] = "script", ["CoffinGate1"] = "door", ["CoffinGate2"] = "door", ["DesertTerror0"] = "actor", ["DesertTerror1"] = "actor", ["DesertTerror2"] = "actor", ["DesertTerror3"] = "actor", ["DesertTerror4"] = "actor", ["DesertTerror5"] = "actor", ["DesertTerror6"] = "actor", ["Door0"] = "door", ["Door1"] = "door", ["EDoor3"] = "door", ["EDoor4"] = "door", ["ElevatorGear1"] = "spinner", ["ElevatorGear2"] = "spinner", ["EndCount"] = "script", ["Eye0"] = "actor", ["Eye10"] = "actor", ["Eye11"] = "actor", ["Eye12"] = "actor", ["Eye13"] = "actor", ["Eye14"] = "actor", ["Eye15"] = "actor", ["Eye16"] = "actor", ["Eye17"] = "actor", ["Eye18"] = "actor", ["Eye19"] = "actor", ["Eye2"] = "actor", ["Eye20"] = "actor", ["Eye21"] = "actor", ["Eye22"] = "actor", ["Eye23"] = "actor", ["Eye24"] = "actor", ["Eye25"] = "actor", ["Eye26"] = "actor", ["Eye27"] = "actor", ["Eye4"] = "actor", ["Eye6"] = "actor", ["Eye7"] = "actor", ["Eye9"] = "actor", ["FireballPlate"] = "door", ["FireballPlate2"] = "door", ["FlyingCritter0"] = "actor", ["FlyingCritter1"] = "actor", ["FlyingCritter10"] = "actor", ["FlyingCritter11"] = "actor", ["FlyingCritter12"] = "actor", ["FlyingCritter13"] = "actor", ["FlyingCritter14"] = "actor", ["FlyingCritter15"] = "actor", ["FlyingCritter16"] = "actor", ["FlyingCritter17"] = "actor", ["FlyingCritter18"] = "actor", ["FlyingCritter2"] = "actor", ["FlyingCritter3"] = "actor", ["FlyingCritter4"] = "actor", ["FlyingCritter5"] = "actor", ["FlyingCritter6"] = "actor", ["FlyingCritter7"] = "actor", ["FlyingCritter8"] = "actor", ["FlyingCritter9"] = "actor", ["FoyerDoorSouth1"] = "door", ["FoyerDoorSouth2"] = "door", ["FoyerShooter1"] = "shooter", ["FoyerShooter2"] = "shooter", ["FoyerShooter3"] = "shooter", ["FoyerShooter4"] = "shooter", ["FoyerShooter5"] = "shooter", ["FoyerShooterPlate"] = "door", ["FoyerShooterTrigger"] = "trigger", ["FoyerShooterTrigger2"] = "trigger", ["GearElevator"] = "door", ["GreaterDemon1"] = "actor", ["HiddenButton1"] = "door", ["IronDoor0"] = "door", ["LesserDemon0"] = "actor", ["LesserDemon1"] = "actor", ["LesserDemon10"] = "actor", ["LesserDemon11"] = "actor", ["LesserDemon12"] = "actor", ["LesserDemon13"] = "actor", ["LesserDemon14"] = "actor", ["LesserDemon15"] = "actor", ["LesserDemon3"] = "actor", ["LesserDemon4"] = "actor", ["LesserDemon5"] = "actor", ["LesserDemon6"] = "actor", ["LesserDemon7"] = "actor", ["LesserDemon8"] = "actor", ["LesserDemon9"] = "actor", ["LowerDoor10"] = "door", ["LowerDoor13"] = "door", ["LowerDoor14"] = "door", ["LowerDoor15"] = "door", ["LowerDoor16"] = "door", ["LowerDoor17"] = "door", ["LowerDoor18"] = "door", ["LowerDoor3"] = "door", ["LowerDoor4"] = "door", ["LowerDoor5"] = "door", ["LowerDoor6"] = "door", ["LowerDoor7"] = "door", ["LowerDoor8"] = "door", ["LowerDoor9"] = "door", ["LowerLever"] = "door", ["LowerLever0"] = "door", ["MiddleDoor4"] = "door", ["MiddleDoor5"] = "door", ["Njam"] = "actor", ["NjamSpawnMarker0"] = "script", ["NjamSpawnMarker1"] = "script", ["NjamSpawnMarker2"] = "script", ["NjamSpawnMarker3"] = "script", ["NjamSpawnMarker4"] = "script", ["NjamSpawnMarker5"] = "script", ["NjamSpawnMarker6"] = "script", ["NjamSpawnMarker7"] = "script", ["NjamtheMeddler0"] = "actor", ["Oculus0"] = "actor", ["Oculus1"] = "actor", ["Oculus10"] = "actor", ["Oculus11"] = "actor", ["Oculus12"] = "actor", ["Oculus2"] = "actor", ["Oculus3"] = "actor", ["Oculus4"] = "actor", ["Oculus5"] = "actor", ["Oculus6"] = "actor", ["Oculus7"] = "actor", ["Oculus8"] = "actor", ["Oculus9"] = "actor", ["Orbus0"] = "actor", ["Orbus1"] = "actor", ["Orbus10"] = "actor", ["Orbus11"] = "actor", ["Orbus12"] = "actor", ["Orbus13"] = "actor", ["Orbus14"] = "actor", ["Orbus15"] = "actor", ["Orbus16"] = "actor", ["Orbus17"] = "actor", ["Orbus18"] = "actor", ["Orbus19"] = "actor", ["Orbus2"] = "actor", ["Orbus20"] = "actor", ["Orbus21"] = "actor", ["Orbus22"] = "actor", ["Orbus23"] = "actor", ["Orbus24"] = "actor", ["Orbus3"] = "actor", ["Orbus4"] = "actor", ["Orbus5"] = "actor", ["Orbus6"] = "actor", ["Orbus7"] = "actor", ["Orbus8"] = "actor", ["Orbus9"] = "actor", ["Pull1"] = "door", ["Pull2"] = "door", ["Pull3"] = "door", ["PuzzleDoor0"] = "door", ["PuzzleDoor1"] = "door", ["PuzzleDoor10"] = "door", ["PuzzleDoor11"] = "door", ["PuzzleDoor12"] = "door", ["PuzzleDoor13"] = "door", ["PuzzleDoor14"] = "door", ["PuzzleDoor15"] = "door", ["PuzzleDoor2"] = "door", ["PuzzleDoor3"] = "door", ["PuzzleDoor4"] = "door", ["PuzzleDoor5"] = "door", ["PuzzleDoor6"] = "door", ["PuzzleDoor7"] = "door", ["PuzzleDoor8"] = "door", ["PuzzleDoor9"] = "door", ["PuzzleDoorB0"] = "door", ["PuzzleDoorB1"] = "door", ["PuzzleDoorB10"] = "door", ["PuzzleDoorB11"] = "door", ["PuzzleDoorB12"] = "door", ["PuzzleDoorB13"] = "door", ["PuzzleDoorB14"] = "door", ["PuzzleDoorB15"] = "door", ["PuzzleDoorB2"] = "door", ["PuzzleDoorB3"] = "door", ["PuzzleDoorB4"] = "door", ["PuzzleDoorB5"] = "door", ["PuzzleDoorB6"] = "door", ["PuzzleDoorB7"] = "door", ["PuzzleDoorB8"] = "door", ["PuzzleDoorB9"] = "door", ["PuzzleDoorC0"] = "door", ["PuzzleDoorC1"] = "door", ["PuzzleDoorC10"] = "door", ["PuzzleDoorC11"] = "door", ["PuzzleDoorC12"] = "door", ["PuzzleDoorC13"] = "door", ["PuzzleDoorC14"] = "door", ["PuzzleDoorC15"] = "door", ["PuzzleDoorC2"] = "door", ["PuzzleDoorC3"] = "door", ["PuzzleDoorC4"] = "door", ["PuzzleDoorC5"] = "door", ["PuzzleDoorC6"] = "door", ["PuzzleDoorC7"] = "door", ["PuzzleDoorC8"] = "door", ["PuzzleDoorC9"] = "door", ["ReptilianTerror0"] = "actor", ["ReptilianTerror1"] = "actor", ["ReptilianTerror2"] = "actor", ["ReptilianTerror3"] = "actor", ["ReptilianTerror4"] = "actor", ["Rotating Lever 16"] = "door", ["Rotating Lever 17"] = "door", ["Rotating Lever 18"] = "door", ["RotatingDoor0"] = "door", ["RotatingDoor1"] = "door", ["SBrick0"] = "door", ["SBrick1"] = "door", ["SeaMonsterMale0"] = "actor", ["SeaMonsterMale1"] = "actor", ["SecretDoor2"] = "door", ["Shooter1"] = "shooter", ["Shooter18"] = "shooter", ["Shooter19"] = "shooter", ["Shooter2"] = "shooter", ["Shooter20"] = "shooter", ["Shooter21"] = "shooter", ["Shooter22"] = "shooter", ["Shooter23"] = "shooter", ["Shooter3"] = "shooter", ["Shooter4"] = "shooter", ["Shooter5"] = "shooter", ["Shooter6"] = "shooter", ["ShooterPlate1"] = "door", ["ShooterPlate10"] = "door", ["ShooterPlate11"] = "door", ["ShooterPlate12"] = "door", ["ShooterPlate14"] = "door", ["ShooterPlate2"] = "door", ["ShooterPlate3"] = "door", ["ShooterPlate4"] = "door", ["ShooterPlate5"] = "door", ["ShooterPlate6"] = "door", ["ShooterPlate7"] = "door", ["ShooterPlate8"] = "door", ["ShooterPlate9"] = "door", ["SkelHeadShooter0"] = "shooter", ["SkelHeadShooter1"] = "shooter", ["SkelHeadShooter2"] = "shooter", ["SkelHeadShooter3"] = "shooter", ["SkeletonHead"] = "skull", ["Sorc0Shooter"] = "shooter", ["Sorc0Shooter0"] = "shooter", ["Sorc0Shooter1"] = "shooter", ["Sorc1Shooter"] = "shooter", ["Sorc1Shooter0"] = "shooter", ["Sorc1Shooter1"] = "shooter", ["Sorc1Shooter2"] = "shooter", ["Sorc1Shooter3"] = "shooter", ["SorceressStatue0"] = "statue", ["SorceressStatue1"] = "statue", ["SorceressStatue2"] = "statue", ["SorceressStatue3"] = "statue", ["SorceressStatue4"] = "statue", ["SorceressStatue5"] = "statue", ["SorceressStatue6"] = "statue", ["SorceressStatue7"] = "statue", ["SpawnLoc0"] = "script", ["SpawnLoc1"] = "script", ["SpawnLoc2"] = "script", ["SpawnLoc3"] = "script", ["SpawnMgr"] = "script", ["SpawnTrigger0"] = "trigger", ["SpawnTrigger1"] = "trigger", ["SpawnTrigger2"] = "trigger", ["SpawnTrigger3"] = "trigger", ["Spawner0"] = "spawner", ["Spawner1"] = "spawner", ["Spawner10"] = "spawner", ["Spawner11"] = "spawner", ["Spawner12"] = "spawner", ["Spawner13"] = "spawner", ["Spawner2"] = "spawner", ["Spawner3"] = "spawner", ["Spawner4"] = "spawner", ["Spawner5"] = "spawner", ["Spawner6"] = "spawner", ["Spawner7"] = "spawner", ["Spawner8"] = "spawner", ["Spawner9"] = "spawner", ["StairGate"] = "door", ["StairGate0"] = "door", ["TP0"] = "script", ["TP1"] = "script", ["TP2"] = "script", ["TP3"] = "script", ["TP4"] = "script", ["TP5"] = "script", ["TauntMan"] = "script", ["ToLowerTombGate"] = "door", ["ToWindMazeGate"] = "door", ["TrapDoor1"] = "door", ["TrapDoor2"] = "door", ["TrapTrigger0"] = "door", ["TrapTrigger1"] = "door", ["TrapTrigger2"] = "door", ["TrapTrigger3"] = "door", ["TrapTrigger4"] = "door", ["TrapTrigger5"] = "door", ["TreasureDoor"] = "door", ["TreasureDoor0"] = "door", ["TrigSkelHeadOn0"] = "trigger", ["TrigSkelHeadOn1"] = "trigger", ["TrigSkelHeadOn2"] = "trigger", ["TrigSorcStatueOff"] = "trigger", ["TrigSorcStatueOff0"] = "trigger", ["TrigSorcStatueOff1"] = "trigger", ["TrigSorcStatueOff2"] = "trigger", ["TrigSorcStatueOff3"] = "trigger", ["TrigSorcStatueOn"] = "trigger", ["TrigSorcStatueOn0"] = "trigger", ["TrigSorcStatueOn1"] = "trigger", ["TrigSorcStatueOn2"] = "trigger", ["TrigSorcStatueOn3"] = "trigger", ["Trigger0"] = "trigger", ["Trigger1"] = "trigger", ["Trigger10"] = "trigger", ["Trigger11"] = "trigger", ["Trigger12"] = "trigger", ["Trigger13"] = "trigger", ["Trigger14"] = "trigger", ["Trigger15"] = "trigger", ["Trigger16"] = "trigger", ["Trigger17"] = "trigger", ["Trigger18"] = "trigger", ["Trigger19"] = "trigger", ["Trigger19Close"] = "trigger", ["Trigger19Open"] = "trigger", ["Trigger2"] = "trigger", ["Trigger3"] = "trigger", ["Trigger4"] = "trigger", ["Trigger5"] = "trigger", ["Trigger6"] = "trigger", ["Trigger7"] = "trigger", ["Trigger8"] = "trigger", ["Trigger9"] = "trigger", ["TriggerFlyingCritters"] = "trigger", ["TriggerFlyingCritters0"] = "trigger", ["TriggerNjam0"] = "trigger", ["TriggerNjam1"] = "trigger", ["TriggerNjam2"] = "trigger", ["TriggerNjam3"] = "trigger", ["TriggerNjam4"] = "trigger", ["TriggerNjam6"] = "trigger", ["TriggerNjam7"] = "trigger", ["TriggerPuzzleDoor0"] = "trigger", ["TriggerPuzzleDoor1"] = "trigger", ["TriggerPuzzleDoor2"] = "trigger", ["TriggerSmokeOff"] = "trigger", ["TriggerSmokeOn"] = "trigger", ["WaterGate0"] = "door", ["WaterGate1"] = "door", ["WaterGate2"] = "door", ["WeightedLift0"] = "door", ["WeightedLift1"] = "door", ["WeightedLift10"] = "door", ["WeightedLift11"] = "door", ["WeightedLift13"] = "door", ["WeightedLift14"] = "door", ["WeightedLift15"] = "door", ["WeightedLift3"] = "door", ["WeightedLift4"] = "door", ["WeightedLift5"] = "door", ["WeightedLift6"] = "door", ["WeightedLift7"] = "door", ["WeightedLift8"] = "door", ["WeightedLift9"] = "door"}
local ACTOR = {["AmphibiousTerror0"] = 78, ["DesertTerror0"] = 74, ["DesertTerror1"] = 75, ["DesertTerror2"] = 33, ["DesertTerror3"] = 19, ["DesertTerror4"] = 64, ["DesertTerror5"] = 81, ["DesertTerror6"] = 112, ["Eye0"] = 104, ["Eye10"] = 55, ["Eye11"] = 56, ["Eye12"] = 92, ["Eye13"] = 88, ["Eye14"] = 89, ["Eye15"] = 102, ["Eye16"] = 93, ["Eye17"] = 85, ["Eye18"] = 105, ["Eye19"] = 106, ["Eye2"] = 84, ["Eye20"] = 37, ["Eye21"] = 38, ["Eye22"] = 99, ["Eye23"] = 97, ["Eye24"] = 108, ["Eye25"] = 36, ["Eye26"] = 45, ["Eye27"] = 57, ["Eye4"] = 90, ["Eye6"] = 58, ["Eye7"] = 59, ["Eye9"] = 60, ["FlyingCritter0"] = 0, ["FlyingCritter1"] = 10, ["FlyingCritter10"] = 1, ["FlyingCritter11"] = 11, ["FlyingCritter12"] = 2, ["FlyingCritter13"] = 12, ["FlyingCritter14"] = 3, ["FlyingCritter15"] = 13, ["FlyingCritter16"] = 4, ["FlyingCritter17"] = 14, ["FlyingCritter18"] = 5, ["FlyingCritter2"] = 6, ["FlyingCritter3"] = 15, ["FlyingCritter4"] = 7, ["FlyingCritter5"] = 18, ["FlyingCritter6"] = 8, ["FlyingCritter7"] = 16, ["FlyingCritter8"] = 9, ["FlyingCritter9"] = 17, ["GreaterDemon1"] = 68, ["LesserDemon0"] = 76, ["LesserDemon1"] = 80, ["LesserDemon10"] = 20, ["LesserDemon11"] = 65, ["LesserDemon12"] = 77, ["LesserDemon13"] = 71, ["LesserDemon14"] = 72, ["LesserDemon15"] = 32, ["LesserDemon3"] = 21, ["LesserDemon4"] = 39, ["LesserDemon5"] = 40, ["LesserDemon6"] = 22, ["LesserDemon7"] = 23, ["LesserDemon8"] = 24, ["LesserDemon9"] = 25, ["Njam"] = 111, ["NjamtheMeddler0"] = 113, ["Oculus0"] = 86, ["Oculus1"] = 96, ["Oculus10"] = 62, ["Oculus11"] = 61, ["Oculus12"] = 73, ["Oculus2"] = 51, ["Oculus3"] = 26, ["Oculus4"] = 27, ["Oculus5"] = 52, ["Oculus6"] = 66, ["Oculus7"] = 69, ["Oculus8"] = 44, ["Oculus9"] = 70, ["Orbus0"] = 28, ["Orbus1"] = 29, ["Orbus10"] = 79, ["Orbus11"] = 98, ["Orbus12"] = 95, ["Orbus13"] = 35, ["Orbus14"] = 43, ["Orbus15"] = 46, ["Orbus16"] = 47, ["Orbus17"] = 48, ["Orbus18"] = 110, ["Orbus19"] = 101, ["Orbus2"] = 53, ["Orbus20"] = 103, ["Orbus21"] = 109, ["Orbus22"] = 50, ["Orbus23"] = 63, ["Orbus24"] = 54, ["Orbus3"] = 30, ["Orbus4"] = 67, ["Orbus5"] = 91, ["Orbus6"] = 87, ["Orbus7"] = 94, ["Orbus8"] = 100, ["Orbus9"] = 107, ["ReptilianTerror0"] = 31, ["ReptilianTerror1"] = 49, ["ReptilianTerror2"] = 82, ["ReptilianTerror3"] = 83, ["ReptilianTerror4"] = 34, ["SeaMonsterMale0"] = 42, ["SeaMonsterMale1"] = 41}
for name, index in pairs({["DesertTerror3_grow1"] = 114, ["DesertTerror6_grow1"] = 115, ["LesserDemon10_grow1"] = 116, ["LesserDemon10_grow2"] = 191, ["LesserDemon3_grow1"] = 117, ["Eye6_grow1"] = 118, ["LesserDemon6_grow1"] = 119, ["LesserDemon6_grow2"] = 120, ["LesserDemon6_grow3"] = 194, ["LesserDemon7_grow1"] = 121, ["LesserDemon7_grow2"] = 122, ["LesserDemon7_grow3"] = 195, ["LesserDemon8_grow1"] = 123, ["LesserDemon8_grow2"] = 124, ["LesserDemon8_grow3"] = 197, ["LesserDemon9_grow1"] = 125, ["LesserDemon9_grow2"] = 126, ["Orbus0_grow1"] = 127, ["Orbus0_grow2"] = 128, ["Orbus0_grow3"] = 182, ["Orbus0_grow4"] = 189, ["ReptilianTerror0_grow1"] = 129, ["LesserDemon15_grow1"] = 130, ["LesserDemon15_grow2"] = 131, ["Eye20_grow1"] = 132, ["LesserDemon4_grow1"] = 133, ["LesserDemon5_grow1"] = 134, ["Orbus24_grow1"] = 135, ["Eye7_grow1"] = 136, ["Eye7_grow2"] = 170, ["Eye7_grow3"] = 183, ["Eye7_grow4"] = 202, ["Oculus10_grow1"] = 137, ["Orbus23_grow1"] = 138, ["DesertTerror4_grow1"] = 139, ["LesserDemon11_grow1"] = 140, ["Oculus6_grow1"] = 141, ["Oculus12_grow1"] = 142, ["Oculus6_grow2"] = 180, ["Oculus12_grow2"] = 190, ["Oculus6_grow3"] = 201, ["Orbus4_grow1"] = 143, ["DesertTerror0_grow1"] = 144, ["Eye15_grow1"] = 145, ["DesertTerror1_grow1"] = 146, ["DesertTerror1_grow2"] = 174, ["LesserDemon12_grow1"] = 147, ["Orbus19_grow1"] = 148, ["Orbus10_grow1"] = 149, ["Orbus10_grow2"] = 172, ["Orbus10_grow3"] = 184, ["Orbus10_grow4"] = 204, ["DesertTerror5_grow1"] = 150, ["DesertTerror5_grow2"] = 177, ["ReptilianTerror2_grow1"] = 151, ["Eye23_grow1"] = 152, ["Orbus11_grow1"] = 153, ["ReptilianTerror3_grow1"] = 154, ["ReptilianTerror3_grow2"] = 155, ["ReptilianTerror3_grow3"] = 175, ["ReptilianTerror3_grow4"] = 185, ["Eye14_grow1"] = 156, ["Eye14_grow2"] = 176, ["Eye14_grow3"] = 199, ["Eye4_grow1"] = 157, ["Eye4_grow2"] = 178, ["Eye4_grow3"] = 200, ["Eye16_grow1"] = 158, ["Orbus7_grow1"] = 159, ["Oculus1_grow1"] = 160, ["Oculus1_grow2"] = 169, ["Oculus1_grow3"] = 171, ["Oculus1_grow4"] = 187, ["Oculus1_grow5"] = 193, ["Orbus8_grow1"] = 161, ["Orbus20_grow1"] = 162, ["Orbus20_grow2"] = 173, ["Orbus20_grow3"] = 186, ["Orbus20_grow4"] = 206, ["Eye0_grow1"] = 163, ["Eye0_grow2"] = 181, ["Eye0_grow3"] = 203, ["Eye18_grow1"] = 164, ["Eye18_grow2"] = 192, ["Eye18_grow3"] = 205, ["Eye19_grow1"] = 165, ["Eye19_grow2"] = 196, ["Orbus9_grow1"] = 166, ["Orbus9_grow2"] = 179, ["Orbus9_grow3"] = 188, ["Eye24_grow1"] = 167, ["Eye24_grow2"] = 198, ["Orbus21_grow1"] = 168}) do ACTOR[name] = index end   -- pack growth (density.py)
local SHOOTERS = {
    Sorc0Shooter = {at = {5939, -7823, 123}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 4, burst = 5, target = nil, stop = "TrigSorcStatueOff"},
    Sorc1Shooter = {at = {5939, -10772, 123}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 4, burst = 5, target = nil, stop = "TrigSorcStatueOff"},
    Sorc0Shooter0 = {at = {9994, -7823, 123}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 4, burst = 5, target = nil, stop = "TrigSorcStatueOff0"},
    Sorc1Shooter0 = {at = {9994, -10772, 123}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 4, burst = 5, target = nil, stop = "TrigSorcStatueOff0"},
    Sorc1Shooter1 = {at = {9830, -13885, 82}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 4, burst = 5, target = nil, stop = "TrigSorcStatueOff1"},
    Sorc1Shooter2 = {at = {9421, -12206, 41}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 4, burst = 5, target = nil, stop = "TrigSorcStatueOff2"},
    SkelHeadShooter1 = {at = {8387, -10568, -1761}, missile = "Fire", projectile = "ScreamingSkull", kind = "Fire", damage = 50, every = 4, burst = 5, target = nil, stop = nil},
    SkelHeadShooter0 = {at = {8233, -10568, -1761}, missile = "Fire", projectile = "ScreamingSkull", kind = "Fire", damage = 50, every = 4, burst = 5, target = nil, stop = nil},
    SkelHeadShooter2 = {at = {5120, -11510, -2048}, missile = "Fire", projectile = "DragonBreath2", kind = "Fire", damage = 50, every = 4, burst = nil, target = nil, stop = nil},
    SkelHeadShooter3 = {at = {3604, -12288, -2212}, missile = "Fire", projectile = "DragonBreath2", kind = "Fire", damage = 50, every = 4, burst = nil, target = nil, stop = nil},
    Sorc0Shooter1 = {at = {18104, -10527, 123}, missile = "Air", projectile = "Lightning", kind = "Air", damage = 50, every = 3, burst = nil, target = {18104, -13681, -95}, stop = nil},
    Sorc1Shooter3 = {at = {18104, -13804, 123}, missile = "Air", projectile = "Lightning", kind = "Air", damage = 50, every = 4, burst = nil, target = {18104, -10732, -95}, stop = nil},
    Shooter6 = {at = {15613, -22211, 0}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 4, burst = nil, target = nil, stop = nil},
    Shooter5 = {at = {15613, -22436, 0}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 4, burst = nil, target = nil, stop = nil},
    Shooter4 = {at = {15613, -22661, 0}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 4, burst = nil, target = nil, stop = nil},
    Shooter3 = {at = {15613, -22886, 0}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 4, burst = nil, target = nil, stop = nil},
    Shooter2 = {at = {15613, -23112, 0}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 4, burst = nil, target = nil, stop = nil},
    Shooter1 = {at = {15613, -23337, 0}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 4, burst = nil, target = nil, stop = nil},
    Shooter18 = {at = {102, -8589, -61}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 12, burst = nil, target = nil, stop = nil},
    Shooter19 = {at = {264, -8589, 0}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 12, burst = nil, target = nil, stop = nil},
    Shooter20 = {at = {425, -8589, -61}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 12, burst = nil, target = nil, stop = nil},
    Shooter21 = {at = {3374, -8184, -61}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 12, burst = nil, target = nil, stop = nil},
    Shooter22 = {at = {3213, -8184, 0}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 12, burst = nil, target = nil, stop = nil},
    Shooter23 = {at = {3052, -8184, -61}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 12, burst = nil, target = nil, stop = nil},
    FoyerShooter5 = {at = {4004, -17068, 2376}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 4, burst = nil, target = nil, stop = nil},
    FoyerShooter4 = {at = {3799, -17068, 2376}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 4, burst = nil, target = nil, stop = nil},
    FoyerShooter3 = {at = {3594, -17068, 2376}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 4, burst = nil, target = nil, stop = nil},
    FoyerShooter2 = {at = {3389, -17068, 2376}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 4, burst = nil, target = nil, stop = nil},
    FoyerShooter1 = {at = {3185, -17068, 2376}, missile = "Fire", projectile = "FireBolt", kind = "Fire", damage = 50, every = 4, burst = nil, target = nil, stop = nil},
}
local STATUES = {
    SorceressStatue0 = {shooter = "Sorc0Shooter", cog = 1390},
    SorceressStatue1 = {shooter = "Sorc1Shooter", cog = 1391},
    SorceressStatue2 = {shooter = "Sorc0Shooter0", cog = 1392},
    SorceressStatue3 = {shooter = "Sorc1Shooter0", cog = 1393},
    SorceressStatue4 = {shooter = "Sorc1Shooter1", cog = 1394},
    SorceressStatue5 = {shooter = "Sorc1Shooter2", cog = 1395},
    SorceressStatue6 = {shooter = "Sorc1Shooter3", cog = 1396},
    SorceressStatue7 = {shooter = "Sorc0Shooter1", cog = 1397},
}
local SKULLS = {["SkeletonHead"] = {cog = 1380, shooters = {"SkelHeadShooter0", "SkelHeadShooter1"}}}
local SPAWNS = {
    SpawnLoc0 = {monster = 9241, at = {3718, -11837, 2306}},   -- LesserDemon
    SpawnLoc1 = {monster = 9241, at = {3265, -11344, 2472}},   -- LesserDemon
    SpawnLoc2 = {monster = 9242, at = {4384, -11117, 2506}},   -- GreaterDemon
    SpawnLoc3 = {monster = 9241, at = {3272, -12093, 2522}},   -- LesserDemon
    Spawner9 = {monster = 9229, at = {983, -14254, -2294}},   -- Orbus
    Spawner7 = {monster = 9241, at = {-164, -11919, -3244}},   -- LesserDemon
    Spawner10 = {monster = 9241, at = {-737, -8520, -2568}},   -- LesserDemon
    Spawner11 = {monster = 9241, at = {-1393, -8520, -2568}},   -- LesserDemon
    Spawner12 = {monster = 9239, at = {0, -4096, -3060}},   -- ReptilianTerror
    Spawner6 = {monster = 9239, at = {1802, -18350, 2255}},   -- ReptilianTerror
    TP4 = {monster = 9230, at = {8929, -12698, 2777}, effect = "mm9:GreaterDemon"},   -- Oculus
    TP5 = {monster = 9230, at = {9503, -9748, 3441}, effect = "mm9:GreaterDemon"},   -- Oculus
    Spawner8 = {monster = 9241, at = {8929, -9830, 2777}},   -- LesserDemon
    Spawner13 = {monster = 9241, at = {10158, -11796, 2777}},   -- LesserDemon
    Spawner0 = {monster = 9237, at = {8929, -13271, -126}},   -- AmphibiousTerror
    Spawner1 = {monster = 9229, at = {7455, -13844, -126}},   -- Orbus
    TP0 = {monster = 9230, at = {7864, -8520, -141}, effect = "mm9:GreaterDemon"},   -- Oculus
    Spawner3 = {monster = 9229, at = {11796, -12780, -618}},   -- Orbus
    Spawner2 = {monster = 9229, at = {11796, -11633, -618}},   -- Orbus
    Spawner4 = {monster = 9239, at = {8806, -9298, -141}},   -- ReptilianTerror
    TP1 = {monster = 9230, at = {8356, -21463, -126}, effect = "mm9:GreaterDemon"},   -- Oculus
    TP2 = {monster = 9241, at = {8028, -21955, -65}, effect = "mm9:GreaterDemon"},   -- LesserDemon
    TP3 = {monster = 9241, at = {8028, -23593, -65}, effect = "mm9:GreaterDemon"},   -- LesserDemon
    Spawner5 = {monster = 9239, at = {15401, -22446, -126}},   -- ReptilianTerror
}
local COUNTS = {["TP5"] = true, ["Spawner8"] = true, ["Spawner13"] = true}
local DEATH = {[45] = {"Spawner9", "default"}, [49] = {"Spawner12", "default"}, [68] = {"Spawner8", "default"}, [69] = {"TP5", "spawn"}, [70] = {"Spawner13", "default"}, [71] = {"TP4", "spawn"}, [76] = {"StairGate", "open"}, [78] = {"Spawner4", "default"}, [80] = {"TP3", "spawn"}, [84] = {"Spawner3", "default"}, [85] = {"Spawner2", "default"}, [87] = {"Spawner0", "default"}, [88] = {"TP0", "spawn"}, [91] = {"Spawner0", "default"}, [92] = {"Spawner1", "default"}, [99] = {"TP1", "spawn"}}
local GREATER_ON_DEATH = {[71] = true, [72] = true}
local GREATER_SPAWNS = {["SpawnLoc0"] = true, ["SpawnLoc1"] = true, ["SpawnLoc3"] = true, ["Spawner8"] = true, ["Spawner13"] = true}
local PADS = {
    ButtonTrigger = {doors = {41, 42, 49, 50, 51, 52, 53, 54, 55, 56, 43, 44, 45, 46, 47, 48}, faces = {18119, 18120, 18121, 18122, 18123, 18124, 18125, 18126, 18127, 18128, 18129, 18130, 18131, 18132, 18133, 18134, 18135, 18136, 18137, 18138, 18139, 18140, 18141, 18142, 18143, 18144, 18145, 18146, 18147, 18148, 18149, 18150, 18151, 18152, 18153, 18154, 18155, 18156, 18157, 18158, 18159, 18160, 18161, 18162, 18163, 18164, 18165, 18166, 18167, 18168, 18169, 18170, 18171, 18172, 18173, 18174, 18175, 18176, 18177, 18178, 18179, 18180, 18181, 18182, 18183, 18184, 18185, 18186, 18187, 18188, 18189, 18190, 18191, 18192, 18193, 18194, 18195, 18196, 18197, 18198, 18199, 18200, 18201, 18202, 18203, 18204, 18205, 18206, 18207, 18208, 18209, 18210, 18211, 18212, 18213, 18214}, locked = false},
    ButtonTrigger0 = {doors = {57, 58, 65, 66, 67, 68, 69, 70, 71, 72, 59, 60, 61, 62, 63, 64}, faces = {18215, 18216, 18217, 18218, 18219, 18220, 18221, 18222, 18223, 18224, 18225, 18226, 18227, 18228, 18229, 18230, 18231, 18232, 18233, 18234, 18235, 18236, 18237, 18238, 18239, 18240, 18241, 18242, 18243, 18244, 18245, 18246, 18247, 18248, 18249, 18250, 18251, 18252, 18253, 18254, 18255, 18256, 18257, 18258, 18259, 18260, 18261, 18262, 18263, 18264, 18265, 18266, 18267, 18268, 18269, 18270, 18271, 18272, 18273, 18274, 18275, 18276, 18277, 18278, 18279, 18280, 18281, 18282, 18283, 18284, 18285, 18286, 18287, 18288, 18289, 18290, 18291, 18292, 18293, 18294, 18295, 18296, 18297, 18298, 18299, 18300, 18301, 18302, 18303, 18304, 18305, 18306, 18307, 18308, 18309, 18310}, locked = true},
    ButtonTrigger1 = {doors = {73, 74, 81, 82, 83, 84, 85, 86, 87, 88, 75, 76, 77, 78, 79, 80}, faces = {18311, 18312, 18313, 18314, 18315, 18316, 18317, 18318, 18319, 18320, 18321, 18322, 18323, 18324, 18325, 18326, 18327, 18328, 18329, 18330, 18331, 18332, 18333, 18334, 18335, 18336, 18337, 18338, 18339, 18340, 18341, 18342, 18343, 18344, 18345, 18346, 18347, 18348, 18349, 18350, 18351, 18352, 18353, 18354, 18355, 18356, 18357, 18358, 18359, 18360, 18361, 18362, 18363, 18364, 18365, 18366, 18367, 18368, 18369, 18370, 18371, 18372, 18373, 18374, 18375, 18376, 18377, 18378, 18379, 18380, 18381, 18382, 18383, 18384, 18385, 18386, 18387, 18388, 18389, 18390, 18391, 18392, 18393, 18394, 18395, 18396, 18397, 18398, 18399, 18400, 18401, 18402, 18403, 18404, 18405, 18406}, locked = true},
}
-- MM9's WeightedLift objects (the water hall's stones; TouchToOpen): a touch (standing on it, or swimming
-- against it) starts it after MoveDelay; it sinks MoveDist at Speed, waits OpenWaitTime and rises again at
-- ClosingSpeed (the mover's auto-close), carrying what stands on it. A touched lift takes no new touch until
-- it is back up (busy seconds).
local LIFTS = {
    WeightedLift0 = {box = {{12914, -11744, -738}, {13485, -11173, -118}}, delay = 1, busy = 13.7},
    WeightedLift1 = {box = {{12422, -12482, -738}, {12994, -11910, -118}}, delay = 1, busy = 13.7},
    WeightedLift10 = {box = {{15207, -13956, -738}, {15779, -13385, -118}}, delay = 1, busy = 13.7},
    WeightedLift11 = {box = {{14880, -13219, -738}, {15451, -12647, -118}}, delay = 1, busy = 13.7},
    WeightedLift13 = {box = {{15371, -12482, -738}, {15943, -11910, -118}}, delay = 1, busy = 13.7},
    WeightedLift14 = {box = {{14880, -11744, -738}, {15451, -11173, -118}}, delay = 1, busy = 13.7},
    WeightedLift15 = {box = {{13866, -12809, -446}, {14499, -11746, -72}}, delay = 1, busy = 7.3},
    WeightedLift3 = {box = {{12914, -13219, -738}, {13485, -12647, -118}}, delay = 1, busy = 13.7},
    WeightedLift4 = {box = {{12668, -13956, -738}, {13239, -13385, -118}}, delay = 1, busy = 13.7},
    WeightedLift5 = {box = {{13405, -14693, -738}, {13977, -14122, -118}}, delay = 1, busy = 13.7},
    WeightedLift6 = {box = {{12422, -14693, -738}, {12994, -14122, -118}}, delay = 1, busy = 13.7},
    WeightedLift7 = {box = {{13897, -15431, -738}, {14468, -14859, -118}}, delay = 1, busy = 13.7},
    WeightedLift8 = {box = {{14388, -14693, -738}, {14960, -14122, -118}}, delay = 1, busy = 13.7},
    WeightedLift9 = {box = {{15289, -14693, -738}, {15861, -14122, -118}}, delay = 1, busy = 13.7},
}
local PIECES = {SpawnPiece0 = {15286, 15287, 15288, 15289, 15290, 15291, 15292, 15293, 15294, 15295, 15296, 15297, 15298, 15299, 15300, 15301, 15302, 15303, 15304, 15305, 15306, 15307, 15308, 15309, 15310, 15311, 15312, 15313, 15314, 15315, 15316, 15317, 15318, 15319, 15320, 15321, 15322, 15323, 15324, 15325, 15326, 15327, 15328, 15329, 15330, 15331, 15332, 15333, 15334, 15335, 15336, 15337, 15338, 15339, 15340, 15341, 15342, 15343, 15344, 15345, 15346, 15347, 15348, 15349, 15350, 15351, 15352, 15353, 15354, 15355, 15356, 15357, 15358, 15359, 15360, 15361, 15362, 15363, 15364, 15365, 15366, 15367, 15368, 15369, 15370, 15371, 15372, 15373, 15374, 15375, 15376, 15377, 15378, 15379, 15380, 15381, 15382, 15383, 15384, 15385, 15386, 15387, 15388, 15389, 15390, 15391, 15392}, SpawnPiece1 = {15393, 15394, 15395, 15396, 15397, 15398, 15399, 15400, 15401, 15402, 15403, 15404, 15405, 15406, 15407, 15408, 15409, 15410, 15411, 15412, 15413, 15414, 15415, 15416, 15417, 15418, 15419, 15420, 15421, 15422, 15423, 15424, 15425, 15426, 15427, 15428, 15429, 15430, 15431, 15432, 15433, 15434, 15435, 15436, 15437, 15438, 15439, 15440, 15441, 15442, 15443, 15444, 15445, 15446, 15447, 15448, 15449, 15450, 15451, 15452, 15453, 15454, 15455, 15456, 15457, 15458, 15459, 15460, 15461, 15462, 15463, 15464, 15465, 15466, 15467, 15468, 15469, 15470, 15471, 15472, 15473, 15474, 15475, 15476, 15477, 15478, 15479, 15480, 15481, 15482, 15483, 15484, 15485, 15486, 15487, 15488, 15489, 15490, 15491, 15492, 15493, 15494, 15495, 15496, 15497, 15498, 15499}, SpawnPiece2 = {15165, 15166, 15167, 15168, 15169, 15170, 15171, 15172, 15173, 15174, 15175, 15176, 15177, 15178, 15179, 15180, 15181, 15182, 15183, 15184, 15185, 15186, 15187, 15188, 15189, 15190, 15191, 15192, 15193, 15194, 15195, 15196, 15197, 15198, 15199, 15200, 15201, 15202, 15203, 15204, 15205, 15206, 15207, 15208, 15209, 15210, 15211, 15212, 15213, 15214, 15215, 15216, 15217, 15218, 15219, 15220, 15221, 15222, 15223, 15224, 15225, 15226, 15227, 15228, 15229, 15230, 15231, 15232, 15233, 15234, 15235, 15236, 15237, 15238, 15239, 15240, 15241, 15242, 15243, 15244, 15245, 15246, 15247, 15248, 15249, 15250, 15251, 15252, 15253, 15254, 15255, 15256, 15257, 15258, 15259, 15260, 15261, 15262, 15263, 15264, 15265, 15266, 15267, 15268, 15269, 15270, 15271, 15272, 15273, 15274, 15275, 15276, 15277, 15278, 15279, 15280, 15281, 15282, 15283, 15284, 15285}, SpawnPiece3 = {15058, 15059, 15060, 15061, 15062, 15063, 15064, 15065, 15066, 15067, 15068, 15069, 15070, 15071, 15072, 15073, 15074, 15075, 15076, 15077, 15078, 15079, 15080, 15081, 15082, 15083, 15084, 15085, 15086, 15087, 15088, 15089, 15090, 15091, 15092, 15093, 15094, 15095, 15096, 15097, 15098, 15099, 15100, 15101, 15102, 15103, 15104, 15105, 15106, 15107, 15108, 15109, 15110, 15111, 15112, 15113, 15114, 15115, 15116, 15117, 15118, 15119, 15120, 15121, 15122, 15123, 15124, 15125, 15126, 15127, 15128, 15129, 15130, 15131, 15132, 15133, 15134, 15135, 15136, 15137, 15138, 15139, 15140, 15141, 15142, 15143, 15144, 15145, 15146, 15147, 15148, 15149, 15150, 15151, 15152, 15153, 15154, 15155, 15156, 15157, 15158, 15159, 15160, 15161, 15162, 15163, 15164}}
local PAWN_FACES = {ChessPiece1 = {1962, 1963, 1964, 1965, 1966, 1967, 1968, 1969, 1970, 1971, 1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035, 2036, 2037, 2038, 2039, 2040, 2041, 2042, 2804, 2805, 2806, 2807, 2808, 2809, 16022, 16023, 16024, 16025, 16026, 16027, 16028, 16029, 16030, 16031, 16032, 16033, 16034, 16035, 16036, 16037, 16038, 16039, 16040, 16041, 16042, 16043, 16044, 16045, 16046, 16047, 16048, 16049}}
local TRIGGERS = {
    {name = "SpawnTrigger0", box = {{3850, -12616, 2311}, {4506, -12288, 2393}}, on = true, msgs = {{"SpawnLoc0", "spawn"}, {"SpawnLoc3", "spawn"}, {"Rumble0", "on"}, {"SpawnTrigger0", "off"}, {"SpawnPiece0", "destroy"}, {"SpawnPiece3", "destroy"}, {"SpawnLoc0", "off"}, {"SpawnLoc3", "off"}, {"SpawnSmoke3", "on"}, {"SpawnSmoke0", "on"}}},
    {name = "SpawnTrigger1", box = {{4014, -12104, 2311}, {4669, -11776, 2393}}, on = true, msgs = {{"SpawnLoc0", "spawn"}, {"SpawnLoc2", "spawn"}, {"Rumble0", "on"}, {"SpawnTrigger1", "off"}, {"SpawnPiece0", "destroy"}, {"SpawnPiece2", "destroy"}, {"SpawnLoc0", "off"}, {"SpawnLoc2", "off"}, {"SpawnSmoke2", "on"}, {"SpawnSmoke0", "on"}}},
    {name = "SpawnTrigger2", box = {{2693, -11960, 2311}, {3615, -11633, 2393}}, on = true, msgs = {{"SpawnLoc1", "spawn"}, {"SpawnLoc3", "spawn"}, {"Rumble0", "on"}, {"SpawnTrigger2", "off"}, {"SpawnPiece1", "destroy"}, {"SpawnPiece3", "destroy"}, {"SpawnLoc1", "off"}, {"SpawnLoc3", "off"}, {"SpawnSmoke3", "on"}, {"SpawnSmoke1", "on"}}},
    {name = "SpawnTrigger3", box = {{3379, -11387, 2311}, {4035, -10732, 2393}}, on = true, msgs = {{"SpawnLoc1", "spawn"}, {"SpawnLoc2", "spawn"}, {"Rumble0", "on"}, {"SpawnTrigger3", "off"}, {"SpawnPiece1", "destroy"}, {"SpawnPiece2", "destroy"}, {"SpawnLoc1", "off"}, {"SpawnLoc2", "off"}, {"SpawnSmoke2", "on"}, {"SpawnSmoke1", "on"}}},
    {name = "TrigSorcStatueOn", box = {{5238, -10834, -128}, {5494, -7762, 128}}, on = true, msgs = {{"TrapTrigger0", "use"}, {"TrigSorcStatueOn", "off"}}},
    {name = "TrigSorcStatueOff", box = {{5770, -10040, 445}, {6026, -9784, 701}}, on = true, msgs = {{"SorceressStatue0", "stop"}, {"SorceressStatue1", "stop"}, {"TrigSorcStatueOn", "on"}}},
    {name = "TrigSorcStatueOn0", box = {{8924, -10834, -128}, {9180, -7762, 128}}, on = true, msgs = {{"TrapTrigger2", "use"}, {"TrigSorcStatueOn0", "off"}}},
    {name = "TrigSorcStatueOff0", box = {{9825, -10040, 445}, {10081, -9784, 701}}, on = true, msgs = {{"SorceressStatue2", "stop"}, {"SorceressStatue3", "stop"}, {"TrigSorcStatueOn0", "on"}}},
    {name = "TrigSorcStatueOff1", box = {{9702, -13972, 445}, {9958, -13716, 701}}, on = true, msgs = {{"SorceressStatue4", "stop"}, {"TrigSorcStatueOn1", "on"}}},
    {name = "TrigSorcStatueOn1", box = {{9446, -12826, -128}, {10214, -12570, 128}}, on = false, msgs = {{"TrapTrigger4", "use"}, {"TrigSorcStatueOn1", "off"}}},
    {name = "TrigSorcStatueOn2", box = {{10890, -12590, -128}, {11146, -11822, 128}}, on = false, msgs = {{"TrapTrigger5", "use"}, {"TrigSorcStatueOn2", "off"}}},
    {name = "TrigSorcStatueOff2", box = {{9293, -12334, 282}, {9549, -12078, 538}}, on = true, msgs = {{"SorceressStatue5", "stop"}, {"TrigSorcStatueOn1", "on"}, {"TrigSorcStatueOn2", "on"}}},
    {name = "TrigSkelHeadOn0", box = {{8187, -8975, -2053}, {8443, -8719, -1797}}, on = true, msgs = {{"SkeletonHead", "go"}, {"TrigSkelHeadOn1", "on"}, {"TrigSkelHeadOn0", "off"}}},
    {name = "TrigSkelHeadOn1", box = {{6426, -12083, -2053}, {6682, -11725, -1797}}, on = true, msgs = {{"SkelHeadShooter2", "on"}, {"SkelHeadShooter3", "on"}, {"TrigSkelHeadOn1", "off"}, {"TrigSkelHeadOn2", "on"}}},
    {name = "TrigSkelHeadOn2", box = {{2534, -12262, -2524}, {2790, -11494, -2268}}, on = false, msgs = {{"SkelHeadShooter2", "off"}, {"SkelHeadShooter3", "off"}, {"TrigSkelHeadOn1", "on"}, {"TrigSkelHeadOn2", "off"}}},
    {name = "TrigSorcStatueOn3", box = {{17362, -12718, -128}, {17618, -11694, 128}}, on = true, msgs = {{"TrigSorcStatueOn3", "off"}, {"TrigSorcStatueOff3", "on"}, {"MiddleDoor4", "unlock"}, {"MiddleDoor4", "use"}, {"MiddleDoor5", "unlock"}, {"MiddleDoor5", "use"}}},
    {name = "TrigSorcStatueOff3", box = {{16788, -12718, -128}, {17044, -11694, 128}}, on = false, msgs = {{"SorceressStatue2", "stop"}, {"SorceressStatue3", "stop"}, {"TrigSorcStatueOff3", "off"}, {"TrigSorcStatueOn3", "on"}, {"MiddleDoor4", "unlock"}, {"MiddleDoor4", "use"}, {"MiddleDoor5", "unlock"}, {"MiddleDoor5", "use"}, {"Sorc0Shooter1", "stop"}, {"Sorc1Shooter3", "stop"}}},
    {name = "TriggerSmokeOff", box = {{-2460, -13110, -2296}, {-2455, -13105, -2291}}, on = true, msgs = {{"GenieSmoke", "off"}}},
    {name = "TriggerSmokeOn", box = {{-2460, -13110, -2296}, {-2455, -13105, -2291}}, on = true, msgs = {{"GenieSmoke", "on"}, {"TriggerSmokeOff", "trigger"}}},
    {name = "TriggerFlyingCritters", box = {{4511, -16389, -128}, {5893, -16133, 128}}, on = true, msgs = {{"FlyingCritter0", "go"}, {"FlyingCritter1", "go"}, {"FlyingCritter2", "go"}, {"FlyingCritter3", "go"}, {"FlyingCritter4", "go"}, {"FlyingCritter5", "go"}, {"FlyingCritter6", "go"}, {"FlyingCritter7", "go"}, {"FlyingCritter8", "go"}, {"TriggerFlyingCritters0", "trigger"}}},
    {name = "TriggerFlyingCritters0", box = {{6303, -16266, -26}, {6559, -16010, 230}}, on = true, msgs = {{"FlyingCritter9", "go"}, {"FlyingCritter10", "go"}, {"FlyingCritter11", "go"}, {"FlyingCritter12", "go"}, {"FlyingCritter13", "go"}, {"FlyingCritter14", "go"}, {"FlyingCritter15", "go"}, {"FlyingCritter16", "go"}, {"FlyingCritter17", "go"}, {"FlyingCritter18", "go"}}},
    {name = "Trigger2", box = {{-1516, -7987, -3072}, {-614, -7741, -2744}}, on = true, msgs = {{"Trigger2", "off"}, {"Spawner7", "default"}, {"Spawner11", "default"}, {"Spawner10", "default"}}},
    {name = "Trigger18", box = {{4588, -12534, 2376}, {4751, -10895, 2540}}, on = true, msgs = {{"SpawnTrigger0", "trigger"}, {"SpawnTrigger1", "trigger"}, {"SpawnTrigger2", "trigger"}, {"SpawnTrigger3", "trigger"}, {"Trigger18", "off"}}},
    {name = "Trigger1", box = {{1884, -17285, 2253}, {2048, -15974, 2580}}, on = true, msgs = {{"Spawner6", "default"}, {"Trigger1", "off"}}},
    {name = "Trigger0", box = {{13681, -18186, -128}, {14664, -17859, 128}}, on = true, msgs = {{"Spawner5", "default"}, {"Trigger0", "off"}}},
    {name = "TriggerNjam0", box = {{7306, -9370, -158}, {8689, -9114, 98}}, on = true, msgs = {{"NjamSpawnMarker0", "spawn"}}},
    {name = "TriggerNjam1", box = {{-9047, -14710, -2545}, {-7665, -14454, -2289}}, on = true, msgs = {{"NjamSpawnMarker1", "spawn"}}},
    {name = "TriggerNjam2", box = {{-7409, -7337, -2561}, {-6026, -7081, -2305}}, on = true, msgs = {{"NjamSpawnMarker2", "spawn"}}},
    {name = "TriggerNjam4", box = {{7883, -15579, -2695}, {9265, -15323, -2439}}, on = true, msgs = {{"NjamSpawnMarker4", "spawn"}}},
    {name = "TriggerNjam6", box = {{-1510, -7828, -3074}, {-128, -7572, -2818}}, on = true, msgs = {{"NjamSpawnMarker6", "spawn"}}},
    {name = "TriggerNjam7", box = {{783, -8320, -218}, {2166, -8064, 38}}, on = true, msgs = {{"NjamSpawnMarker7", "spawn"}}},
    {name = "TriggerPuzzleDoor0", box = {{9426, -23168, -128}, {9682, -22400, 128}}, on = true, msgs = {{"ButtonTrigger", "settrap"}, {"TriggerPuzzleDoor0", "off"}, {"TrigSorcStatueOn2", "on"}, {"AITrk151", "off"}, {"TP2", "spawn"}, {"TP3", "spawn"}, {"TriggerPuzzleDoor0", "off"}, {"NjamSpawnMarker5", "spawn"}}},
    {name = "TriggerPuzzleDoor1", box = {{14740, -19564, -128}, {14996, -18591, 128}}, on = true, msgs = {{"ButtonTrigger0", "settrap"}, {"TriggerPuzzleDoor1", "off"}}},
    {name = "TriggerPuzzleDoor2", box = {{14894, -19564, -128}, {15150, -18591, 128}}, on = true, msgs = {{"ButtonTrigger1", "settrap"}, {"TriggerPuzzleDoor2", "off"}}},
    {name = "TriggerNjam3", box = {{3241, -9303, -2561}, {4623, -9047, -2305}}, on = true, msgs = {{"NjamSpawnMarker3", "spawn"}}},
    {name = "Trigger5", box = {{11246, -22520, -179}, {11738, -22029, -97}}, on = true, msgs = {{"ShooterPlate1", "toggle"}, {"Trigger5", "off"}, {"Shooter5", "on"}, {"Shooter6", "on"}}},
    {name = "Trigger6", box = {{11246, -23014, -179}, {11738, -22523, -97}}, on = true, msgs = {{"ShooterPlate2", "toggle"}, {"Trigger6", "off"}, {"Shooter3", "on"}, {"Shooter4", "on"}}},
    {name = "Trigger7", box = {{11246, -23503, -179}, {11738, -23012, -97}}, on = true, msgs = {{"ShooterPlate3", "toggle"}, {"Trigger7", "off"}, {"Shooter1", "on"}, {"Shooter2", "on"}}},
    {name = "Trigger8", box = {{11740, -22520, -179}, {12232, -22029, -97}}, on = true, msgs = {{"ShooterPlate4", "toggle"}, {"Trigger8", "off"}, {"Shooter5", "on"}, {"Shooter6", "on"}}},
    {name = "Trigger9", box = {{11740, -23014, -179}, {12232, -22523, -97}}, on = true, msgs = {{"ShooterPlate5", "toggle"}, {"Trigger9", "off"}, {"Shooter3", "on"}, {"Shooter4", "on"}}},
    {name = "Trigger10", box = {{11740, -23503, -179}, {12232, -23012, -97}}, on = true, msgs = {{"ShooterPlate6", "toggle"}, {"Trigger10", "off"}, {"Shooter1", "on"}, {"Shooter2", "on"}}},
    {name = "Trigger11", box = {{12234, -22520, -179}, {12726, -22029, -97}}, on = true, msgs = {{"ShooterPlate7", "toggle"}, {"Trigger11", "off"}, {"Shooter5", "on"}, {"Shooter6", "on"}}},
    {name = "Trigger12", box = {{12234, -23014, -179}, {12726, -22523, -97}}, on = true, msgs = {{"ShooterPlate8", "toggle"}, {"Trigger12", "off"}, {"Shooter3", "on"}, {"Shooter4", "on"}}},
    {name = "Trigger13", box = {{12234, -23503, -179}, {12726, -23012, -97}}, on = true, msgs = {{"ShooterPlate9", "toggle"}, {"Trigger13", "off"}, {"Shooter1", "on"}, {"Shooter2", "on"}}},
    {name = "Trigger14", box = {{12728, -22520, -179}, {13220, -22029, -97}}, on = true, msgs = {{"ShooterPlate10", "toggle"}, {"Trigger14", "off"}, {"Shooter5", "on"}, {"Shooter6", "on"}}},
    {name = "Trigger15", box = {{12728, -23014, -179}, {13220, -22523, -97}}, on = true, msgs = {{"ShooterPlate11", "toggle"}, {"Trigger15", "off"}, {"Shooter3", "on"}, {"Shooter4", "on"}}},
    {name = "Trigger16", box = {{12728, -23503, -179}, {13220, -23012, -97}}, on = true, msgs = {{"ShooterPlate12", "toggle"}, {"Trigger16", "off"}, {"Shooter1", "on"}, {"Shooter2", "on"}}},
    {name = "Trigger17", box = {{13222, -23014, -179}, {13714, -22523, -97}}, on = true, msgs = {{"ShooterPlate14", "toggle"}, {"Trigger17", "off"}, {"Shooter3", "on"}, {"Shooter4", "on"}}},
    {name = "Trigger3", box = {{41, -5571, -236}, {512, -5243, -51}}, on = true, msgs = {{"FireballPlate", "toggle"}, {"Trigger3", "off"}, {"Shooter18", "on"}, {"Shooter19", "on"}, {"Shooter20", "on"}}},
    {name = "Trigger4", box = {{3098, -8968, -271}, {3354, -8712, -15}}, on = true, msgs = {{"FireballPlate2", "toggle"}, {"Trigger4", "off"}, {"Shooter21", "on"}, {"Shooter22", "on"}, {"Shooter23", "on"}}},
    {name = "FoyerShooterTrigger2", box = nil, on = true, msgs = {{"FoyerShooter1", "off"}, {"FoyerShooter2", "off"}, {"FoyerShooter3", "off"}, {"FoyerShooter4", "off"}, {"FoyerShooter5", "off"}}},
    {name = "FoyerShooterTrigger", box = {{3267, -13486, 2207}, {3922, -13240, 2289}}, on = true, msgs = {{"FoyerShooter1", "on"}, {"FoyerShooter2", "on"}, {"FoyerShooter3", "on"}, {"FoyerShooter4", "on"}, {"FoyerShooter5", "on"}, {"FoyerShooterPlate", "toggle"}, {"FoyerShooterTrigger", "off"}}},
    {name = "Trigger19Close", box = nil, on = true, msgs = {{"Fan15", "on"}, {"Wind15", "on"}, {"Fan18", "on"}, {"Wind18", "on"}, {"Fan21", "on"}, {"Wind21", "on"}, {"Fan23", "on"}, {"Wind23", "on"}}},
    {name = "Trigger19Open", box = nil, on = true, msgs = {{"Fan15", "off"}, {"Wind15", "off"}, {"Fan18", "off"}, {"Wind18", "off"}, {"Fan21", "off"}, {"Wind21", "off"}, {"Fan23", "off"}, {"Wind23", "off"}}},
    {name = "Trigger19", box = {{1720, -17285, 2253}, {1884, -15974, 2580}}, on = true, msgs = {{"TauntMan", "start"}}},
}
local TRIGGER = {}
for _, t in ipairs(TRIGGERS) do TRIGGER[t.name] = t end
local CHESS = {{box = {{8200, -15245, -2749}, {8425, -15000, -2545}}, pieces = {"ChessPiece2"}}, {box = {{8200, -15737, -2749}, {8425, -15491, -2545}}, pieces = {"ChessPiece2", "ChessPiece5"}}, {box = {{8200, -15983, -2749}, {8425, -15737, -2545}}, pieces = {"ChessPiece4"}}, {box = {{7974, -14754, -2749}, {8200, -14508, -2545}}, pieces = {"ChessPiece4"}}, {box = {{7974, -15000, -2749}, {8200, -14754, -2545}}, pieces = {"ChessPiece2"}}, {box = {{7974, -15737, -2749}, {8200, -15491, -2545}}, pieces = {"ChessPiece4"}}, {box = {{7974, -15983, -2749}, {8200, -15737, -2545}}, pieces = {"ChessPiece2", "ChessPiece5"}}, {box = {{7974, -16474, -2749}, {8200, -16228, -2545}}, pieces = {"ChessPiece5"}}, {box = {{7749, -15000, -2749}, {7974, -14754, -2545}}, pieces = {"ChessPiece4"}}, {box = {{7749, -15491, -2749}, {7974, -15245, -2545}}, pieces = {"ChessPiece4"}}, {box = {{7524, -15000, -2749}, {7749, -14754, -2545}}, pieces = {"ChessPiece2", "ChessPiece3"}}, {box = {{7524, -15983, -2749}, {7749, -15737, -2545}}, pieces = {"ChessPiece2", "ChessPiece5"}}, {box = {{7524, -16474, -2749}, {7749, -16228, -2545}}, pieces = {"ChessPiece5"}}, {box = {{7298, -15000, -2749}, {7524, -14754, -2545}}, pieces = {"ChessPiece4"}}, {box = {{7298, -15245, -2749}, {7524, -15000, -2545}}, pieces = {"ChessPiece2", "ChessPiece3"}}, {box = {{7298, -15491, -2749}, {7524, -15245, -2545}}, pieces = {"ChessPiece4"}}, {box = {{7298, -15737, -2749}, {7524, -15491, -2545}}, pieces = {"ChessPiece2", "ChessPiece5"}}, {box = {{7073, -14754, -2749}, {7298, -14508, -2545}}, pieces = {"ChessPiece4"}}, {box = {{7073, -15245, -2749}, {7298, -15000, -2545}}, pieces = {"ChessPiece0"}}, {box = {{7073, -15491, -2749}, {7298, -15245, -2545}}, pieces = {"ChessPiece5"}}, {box = {{7073, -15737, -2749}, {7298, -15491, -2545}}, pieces = {"ChessPiece4", "ChessPiece0"}}, {box = {{6848, -15245, -2749}, {7073, -15000, -2545}}, pieces = {"ChessPiece5", "ChessPiece3"}}, {box = {{6848, -15983, -2749}, {7073, -15737, -2545}}, pieces = {"ChessPiece4"}}, {box = {{6623, -15000, -2749}, {6848, -14754, -2545}}, pieces = {"ChessPiece5", "ChessPiece3"}}, {box = {{6623, -15245, -2749}, {6848, -15000, -2545}}, pieces = {"ChessPiece1"}, queen = "ChessPiece1", at = {6735, -15122, -2698}}, {box = {{6623, -15737, -2749}, {6848, -15491, -2545}}, pieces = {"ChessPiece1"}, queen = "ChessPiece1", at = {6735, -15614, -2698}}, {box = {{6623, -16228, -2749}, {6848, -15983, -2545}}, pieces = {"ChessPiece4"}}}
local NJAM_MARKERS = {["NjamSpawnMarker0"] = {7937, -8545, -141}, ["NjamSpawnMarker1"] = {-8192, -13107, -2522}, ["NjamSpawnMarker2"] = {-6676, -4956, -2445}, ["NjamSpawnMarker4"] = {9721, -15451, -2660}, ["NjamSpawnMarker5"] = {7700, -22774, -65}, ["NjamSpawnMarker6"] = {-655, -4342, -2568}, ["NjamSpawnMarker7"] = {1802, -9830, -136}, ["NjamSpawnMarker3"] = {4628, -9175, -2522}}
local END_DEMON = {8929, -11674, 2777}
local GATE0, GATE0_REACH = {8090, -7004, 59}, 300
local FLY_LEAVE = {["FlyingCritter0"] = 4.8, ["FlyingCritter1"] = 4.4, ["FlyingCritter10"] = 5.5, ["FlyingCritter11"] = 5.2, ["FlyingCritter12"] = 5.4, ["FlyingCritter13"] = 5.1, ["FlyingCritter14"] = 5.2, ["FlyingCritter15"] = 3.9, ["FlyingCritter16"] = 4.2, ["FlyingCritter17"] = 4.0, ["FlyingCritter18"] = 4.4, ["FlyingCritter2"] = 4.6, ["FlyingCritter3"] = 4.3, ["FlyingCritter4"] = 4.9, ["FlyingCritter5"] = 4.9, ["FlyingCritter6"] = 5.1, ["FlyingCritter7"] = 4.8, ["FlyingCritter8"] = 5.0, ["FlyingCritter9"] = 4.6}

-- A scheduler on the 0.25 s poll (MM9's Wait): after(seconds, fn).
local tick, tasks = 0, {}
local function after(seconds, fn) table.insert(tasks, {at = tick + math.max(1, math.floor(seconds * 4 + 0.5)), fn = fn}) end
-- 1000T_SorcStatues.scr: :Main2 plays fidget2 once (each statue holds its end); Go (:Start) sets bIsCasting
-- (StatueCasting<name>), its shooter Go and :StartSequence: fidget2, then :Continue Taunt, then fidget2 ...
-- while it casts; Stop (:TurnOff) clears it and the clip playing finishes. The clips (mm9_sorcererstatue's
-- skinned copy) chain on the poll, each held until the tick after its end; the chains are runtime only, so
-- map load starts them again. Its CastingSmoke (a Fire object) is not carried.
local STATUE_CLIPS = {fidget2 = 2.366, taunt = 1.000}
local statueChain = {}
local function statueSequence(name, clip, chain)
    if statueChain[name] ~= chain or var("StatueCasting" .. name) ~= 1 then return end
    evt.PlayDecorationClip(STATUES[name].cog, clip)
    after(STATUE_CLIPS[clip] + 0.125, function()
        statueSequence(name, clip == "fidget2" and "taunt" or "fidget2", chain)
    end)
end
local function statueCasting(name)
    statueChain[name] = (statueChain[name] or 0) + 1
    statueSequence(name, "fidget2", statueChain[name])
end
-- A weighted lift's touch: it starts after its MoveDelay and takes no new touch until it is back up.
local liftIdleAt = {}
local function touchLift(name)
    local lift = LIFTS[name]
    liftIdleAt[name] = tick + math.floor(lift.busy * 4 + 0.5)
    set("Touched" .. name, var("Touched" .. name) + 1)
    after(lift.delay, function()
        for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Open) end
    end)
end
local send

-- Doors: MM9's Door / RotatingDoor / Button / Lift messages. A group's open state is kept in a map variable
-- for the groups with Open/CloseTriggers; locks are map variables (MM9 Lock/Unlock, Locked).
local function locked(group) return var("Lock" .. group) == 1 end
local function isOpen(group) return var("Open" .. group) == 1 end
local function run(list) if list then for _, m in ipairs(list) do send(m[1], m[2]) end end end
local function openGroup(group)
    for _, id in ipairs(GROUPS[group]) do evt.SetDoorState(id, DoorAction.Open) end
    if not isOpen(group) then set("Open" .. group, 1) run(ON_OPEN[group]) end
end
local function closeGroup(group)
    for _, id in ipairs(GROUPS[group]) do evt.SetDoorState(id, DoorAction.Close) end
    if isOpen(group) then set("Open" .. group, 0) run(ON_CLOSE[group]) end
end
local function useGroup(group) if isOpen(group) then closeGroup(group) else openGroup(group) end end

-- Shooters (MM9 Shooter: ProjectileName, DamageAmt, ShootInterval): on, they fire at the party (a lightning
-- shooter at its marker); a burst shooter (1000T_CircleShooter.scr, 1000T_SkHeadShooter.scr) fires its count
-- and stops, a circle shooter then triggers its stop trigger. A shot strikes the party in its path
-- (FireMissile's strikesParty).
local firing = {}
local function fire(name)
    local s = SHOOTERS[name]
    local x, y, z = evt.GetPartyPosition()
    z = z + 100
    if s.target ~= nil then x, y, z = s.target[1], s.target[2], s.target[3] + 60 end
    local dx, dy, dz = x - s.at[1], y - s.at[2], z - s.at[3]
    local length = math.max(1, math.sqrt(dx * dx + dy * dy + dz * dz))
    if s.target == nil and length > 4000 then return end
    local k = math.min(64 / length, 0.33)
    local shot = evt.FireMissile(s.missile, s.at[1] + dx * k, s.at[2] + dy * k, s.at[3] + dz * k, x, y, z, s.damage, s.kind, 0, 0, true)
    if shot then MM9.launchSound(s.projectile, s.at[1], s.at[2], s.at[3]) end
    set("ShotsFired", var("ShotsFired") + (shot and 1 or 0))
end
local function shooterOn(name)
    local s = SHOOTERS[name]
    if s == nil then return end
    firing[name] = {next = tick, left = s.burst}
end
local function shooterOff(name) firing[name] = nil end

-- Spawns (Spawner DefaultSpawn, SpawnLoc.scr, SpawnGeneric.scr): the monster appears at the object; EndCount.scr
-- counts the end hall's spawns and, at the third, a Greater Demon appears at EndDemonMarker.
local function spawn(name)
    local s = SPAWNS[name]
    if s == nil then return end
    local _, made = evt.SummonMonstersById({monster = s.monster, x = s.at[1], y = s.at[2], z = s.at[3], radius = 48, count = 1, effect = s.effect})
    set("Spawned", var("Spawned") + 1)
    -- "LesserDemon ScriptParams 1" (Spawner8/13's DefaultSpawn; SpawnMgr.scr's LESSERDEMON for SpawnLoc's
    -- LesserDemon): LesserDemon.scr p0 1, a Greater Demon from the body at death (the kill hook)
    if GREATER_SPAWNS[name] and made ~= nil then for _, i in ipairs(made) do set("Greater" .. i, 1) end end
    set("Spawn" .. name, var("Spawn" .. name) + 1)
    if COUNTS[name] then
        set("EndCount", var("EndCount") + 1)
        if var("EndCount") == 3 then
            -- EndDemon.scr :Main forces its spawn-in (g_bTemp = TRUE): hidden, :SpawnIn DoClientFX GreaterDemon,
            -- the Spawn clip made visible, then Aware (the summon's mm9 script_params "1": the engine's spawn-in);
            -- its :OnDeath opens the double gate Door0/Door1 before the win switch (the kill hook, EndDemon<index>)
            evt.SpawnWorldEffect("mm9:GreaterDemon", END_DEMON[1], END_DEMON[2], END_DEMON[3], 1)
            local _, demons = evt.SummonMonstersById({monster = 9242, x = END_DEMON[1], y = END_DEMON[2], z = END_DEMON[3], radius = 48, count = 1, mm9 = {script_params = "1"}})
            if demons ~= nil then for _, i in ipairs(demons) do set("EndDemon" .. i, 1) end end
        end
    end
end

-- Njam (SpawnNjam.scr, with key 108): at a marker he appears for 20-60 s and vanishes (one at a time).
local function njamAppear(marker)
    if MM9.hasKey(108) == 0 or MM9.hasKey(109) == 1 then return end
    local p = NJAM_MARKERS[marker]
    evt.SetMapActorPosition(ACTOR.NjamtheMeddler0, p[1], p[2], p[3])
    -- Njam1000.scr: AddEnemy Player (hostile; CanDamage FALSE: njam.lua's hunt mode, no physical blow hurts him)
    evt.SetMonGroupBit(1, MonsterBits.Invisible, false)
    evt.SetMonGroupBit(1, MonsterBits.Hostile, true)
    -- his BaseMelee + Range loop walks at the party (the placement holds him still for the taunt cinematic)
    evt.SetActorImmobile(ACTOR.NjamtheMeddler0, false)
    MM9.playSound("sounds/spells/townportal.wav")
    evt.SpawnWorldEffect("mm9:GreaterDemon", p[1], p[2], p[3], 1)   -- :Onspawn2: DoClientFX g_hMyObject, GreaterDemon
    set("NjamShown", var("NjamShown") + 1)
    local shown = var("NjamShown")
    after(math.random(20, 60), function()
        if var("NjamShown") == shown then
            MM9.clientFx(ACTOR.NjamtheMeddler0, "mm9:GreaterDemon")   -- :Vanish2: DoClientFX hNjam, GreaterDemon
            evt.SetMonGroupBit(1, MonsterBits.Invisible, true)
            evt.SetMonGroupBit(1, MonsterBits.Hostile, false)
            evt.SetActorImmobile(ACTOR.NjamtheMeddler0, true)
        end
    end)
end

-- The button puzzles (ButtonPad.scr, ButtonPuzzle.scr): 16 blocks in a 4 x 4 wall, hidden in the ceiling
-- (Main2) until the party springs the trap (SetTrap: the wall comes down, every block shut); a click pushes a
-- block and its four neighbours in or out (ButtonPushed); all 16 in opens the wall for good (MoveAway); the
-- pull (Reset) shuts them all. Hidden = faces invisible and untouchable (evt.SetFacetBit by face index).
local function showPad(pad, shown)
    for _, f in ipairs(PADS[pad].faces) do
        evt.SetFacetBit(-f, 536879104, not shown)
    end
end
local function pressed(pad, k) return var(pad .. "_" .. k) == 1 end
local function setBlock(pad, k, inward)
    set(pad .. "_" .. k, inward and 1 or 0)
    evt.SetDoorState(PADS[pad].doors[k + 1], inward and DoorAction.Open or DoorAction.Close)
end
local function resetPad(pad)
    for k = 0, 15 do setBlock(pad, k, false) end
end
local function setTrap(pad)
    if var(pad .. "State") ~= 0 then return end
    set(pad .. "State", 1)
    resetPad(pad)
    showPad(pad, true)
    MM9.playSound("sounds/door/stonedoorslam.wav")
end
local function pushBlock(pad, k)
    if var(pad .. "State") ~= 1 then return end
    local col, row = k % 4, math.floor(k / 4)
    setBlock(pad, k, not pressed(pad, k))
    if col > 0 then setBlock(pad, k - 1, not pressed(pad, k - 1)) end
    if col < 3 then setBlock(pad, k + 1, not pressed(pad, k + 1)) end
    if row > 0 then setBlock(pad, k - 4, not pressed(pad, k - 4)) end
    if row < 3 then setBlock(pad, k + 4, not pressed(pad, k + 4)) end
    for j = 0, 15 do if not pressed(pad, j) then return end end
    set(pad .. "State", 2)
    MM9.playSound("sounds/door/doorlatch02.wav")   -- ButtonPuzzle.scr :MoveDoor, then :EndDoor 0.8 s later
    after(0.8, function()
        MM9.playSound("sounds/door/stonedoorslide02.wav")
        showPad(pad, false)
    end)
end

-- The dispatcher: MM9's Trigger messages (target, message), as the DAT links them.
local function fireTrigger(name)
    local t = TRIGGER[name]
    if t == nil then return end
    set("Fired" .. name, var("Fired" .. name) + 1)
    run(t.msgs)
end
local function triggerOn(name)
    local state = var("Trig" .. name)
    if state == 0 then return TRIGGER[name] ~= nil and TRIGGER[name].on end
    return state == 1
end
send = function(target, msg)
    if not MM9.receives("1000terrors", target, msg, ACTOR[target]) then return end   -- a dead AI takes none
    local kind = KIND[target]
    if kind == "trigger" then
        if msg == "on" then set("Trig" .. target, 1)
        elseif msg == "off" then set("Trig" .. target, 2)
        elseif msg == "trigger" then fireTrigger(target) end
    elseif kind == "door" then
        local group = MODEL_GROUP[target]
        if msg == "open" then openGroup(group)
        elseif msg == "close" then closeGroup(group)
        elseif msg == "use" or msg == "toggle" then useGroup(group)
        elseif msg == "lock" then set("Lock" .. group, 1)
        elseif msg == "unlock" then set("Lock" .. group, 0) end
    elseif kind == "shooter" then
        if msg == "on" or msg == "go" then shooterOn(target) elseif msg == "off" or msg == "stop" then shooterOff(target) end
    elseif kind == "statue" then
        if msg == "go" then
            shooterOn(STATUES[target].shooter)
            set("StatueCasting" .. target, 1)
            statueCasting(target)
        elseif msg == "stop" then
            shooterOff(STATUES[target].shooter)
            set("StatueCasting" .. target, 0)
        end
    elseif kind == "skull" then
        -- 1000T_SkeletonHead.scr: Go turns the skull about (:Start Rotate 0, 1, 0, 180, 180: half a turn
        -- clockwise from above at 180/s, evt.AimDecoration; ignored while it turns), then :TurnOff sends both
        -- shooters Go (1000T_SkHeadShooter.scr: ScriptParams' count of shots, one a second); Stop runs :TurnOff
        -- at once. SkullTurns counts the half turns (aims are runtime only: map load puts it back).
        if (msg == "go" or msg == "stop") and var("SkullTurning" .. target) == 0 then
            set("SkullTurning" .. target, 1)
            if msg == "go" then
                set("SkullTurns" .. target, var("SkullTurns" .. target) + 1)
                evt.AimDecoration(SKULLS[target].cog, -180 * var("SkullTurns" .. target), 180)
            end
            after(msg == "go" and 1 or 0, function()
                set("SkullTurning" .. target, 0)
                for _, s in ipairs(SKULLS[target].shooters) do shooterOn(s) end
                set("SkullGo" .. target, var("SkullGo" .. target) + 1)
            end)
        end
    elseif kind == "spawner" then
        if msg == "default" or msg == "spawn" then spawn(target) end
    elseif kind == "script" then
        if PADS[target] ~= nil then
            if msg == "settrap" then setTrap(target) elseif msg == "reset" and var(target .. "State") == 1 then resetPad(target) end
        elseif NJAM_MARKERS[target] ~= nil then
            if msg == "spawn" then njamAppear(target) end
        elseif msg == "spawn" then
            if not (var("Off" .. target) == 1) then spawn(target) end
        elseif msg == "off" then set("Off" .. target, 1)
        elseif msg == "start" and target == "TauntMan" then handlers[379]() end
    elseif kind == "actor" then
        if msg == "go" and ACTOR[target] ~= nil then
            evt.WakeActor(ACTOR[target])
            -- 1000T_FlyingCreature_.scr :OnTraverseDone: RemoveObject at the last marker (the flight's time)
            if FLY_LEAVE[target] ~= nil and var("Flown" .. target) == 0 then
                set("Flown" .. target, 1)
                after(FLY_LEAVE[target], function() MM9.removeActor(ACTOR[target]) end)
            end
        end
    elseif target:sub(1, 10) == "SpawnPiece" then
        if msg == "destroy" and PIECES[target] ~= nil then
            for _, f in ipairs(PIECES[target]) do evt.SetFacetBit(-f, 536879104, true) end
            set("Destroyed" .. target, 1)
            MM9.playSound("sounds/events/stonecrumble.wav")
        end
    elseif target == "Rumble0" then MM9.playSound("sounds/events/rubblecrash.wav")
    end
end

-- Plates (ShooterPlate, FireballPlate, FoyerShooterPlate): a trigger toggles the plate down; it rises after its
-- CloseWaitTime and its CloseTriggers turn the shooters off and the trigger on again.
local PLATE_WAIT = {FireballPlate = 3.0, FireballPlate2 = 3.0, FoyerShooterPlate = 3.0, ShooterPlate1 = 4.0, ShooterPlate10 = 4.0, ShooterPlate11 = 4.0, ShooterPlate12 = 4.0, ShooterPlate14 = 4.0, ShooterPlate2 = 4.0, ShooterPlate3 = 4.0, ShooterPlate4 = 4.0, ShooterPlate5 = 4.0, ShooterPlate6 = 4.0, ShooterPlate7 = 4.0, ShooterPlate8 = 4.0, ShooterPlate9 = 4.0}
local plainOpen = openGroup
openGroup = function(group)
    plainOpen(group)
    if PLATE_WAIT[group] ~= nil then after(PLATE_WAIT[group], function() closeGroup(group) end) end
end

-- Doors: a click toggles a group (MM9 Use); locked groups say so (MM9 LockJiggle).
handlers[101] = function() if locked("CoffinGate1") then evt.StatusText("Locked") return end if ON_OPEN.CoffinGate1 or ON_CLOSE.CoffinGate1 then useGroup("CoffinGate1") else evt.SetDoorState(1, DoorAction.Trigger) end end   -- CoffinGate1
handlers[102] = function() if locked("CoffinGate2") then evt.StatusText("Locked") return end if ON_OPEN.CoffinGate2 or ON_CLOSE.CoffinGate2 then useGroup("CoffinGate2") else evt.SetDoorState(2, DoorAction.Trigger) end end   -- CoffinGate2
handlers[103] = function() if locked("LowerDoor13") then evt.StatusText("Locked") return end if ON_OPEN.LowerDoor13 or ON_CLOSE.LowerDoor13 then useGroup("LowerDoor13") else evt.SetDoorState(20, DoorAction.Trigger) evt.SetDoorState(21, DoorAction.Trigger) end end   -- LowerDoor13
handlers[104] = function() if locked("LowerDoor15") then evt.StatusText("Locked") return end if ON_OPEN.LowerDoor15 or ON_CLOSE.LowerDoor15 then useGroup("LowerDoor15") else evt.SetDoorState(22, DoorAction.Trigger) evt.SetDoorState(23, DoorAction.Trigger) end end   -- LowerDoor15
handlers[105] = function() if locked("LowerDoor17") then evt.StatusText("Locked") return end if ON_OPEN.LowerDoor17 or ON_CLOSE.LowerDoor17 then useGroup("LowerDoor17") else evt.SetDoorState(24, DoorAction.Trigger) evt.SetDoorState(25, DoorAction.Trigger) end end   -- LowerDoor17
handlers[106] = function() if locked("LowerDoor3") then evt.StatusText("Locked") return end if ON_OPEN.LowerDoor3 or ON_CLOSE.LowerDoor3 then useGroup("LowerDoor3") else evt.SetDoorState(26, DoorAction.Trigger) evt.SetDoorState(27, DoorAction.Trigger) end end   -- LowerDoor3
handlers[107] = function() if locked("LowerDoor5") then evt.StatusText("Locked") return end if ON_OPEN.LowerDoor5 or ON_CLOSE.LowerDoor5 then useGroup("LowerDoor5") else evt.SetDoorState(28, DoorAction.Trigger) evt.SetDoorState(29, DoorAction.Trigger) end end   -- LowerDoor5
handlers[108] = function() if locked("LowerDoor7") then evt.StatusText("Locked") return end if ON_OPEN.LowerDoor7 or ON_CLOSE.LowerDoor7 then useGroup("LowerDoor7") else evt.SetDoorState(30, DoorAction.Trigger) evt.SetDoorState(31, DoorAction.Trigger) end end   -- LowerDoor7
handlers[109] = function() if locked("LowerDoor9") then evt.StatusText("Locked") return end if ON_OPEN.LowerDoor9 or ON_CLOSE.LowerDoor9 then useGroup("LowerDoor9") else evt.SetDoorState(32, DoorAction.Trigger) evt.SetDoorState(33, DoorAction.Trigger) end end   -- LowerDoor9
handlers[110] = function() if locked("MiddleDoor4") then evt.StatusText("Locked") return end if ON_OPEN.MiddleDoor4 or ON_CLOSE.MiddleDoor4 then useGroup("MiddleDoor4") else evt.SetDoorState(36, DoorAction.Trigger) end end   -- MiddleDoor4
handlers[111] = function() if locked("MiddleDoor5") then evt.StatusText("Locked") return end if ON_OPEN.MiddleDoor5 or ON_CLOSE.MiddleDoor5 then useGroup("MiddleDoor5") else evt.SetDoorState(37, DoorAction.Trigger) end end   -- MiddleDoor5
handlers[112] = function() if locked("RotatingDoor0") then evt.StatusText("Locked") return end if ON_OPEN.RotatingDoor0 or ON_CLOSE.RotatingDoor0 then useGroup("RotatingDoor0") else evt.SetDoorState(89, DoorAction.Trigger) end end   -- RotatingDoor0
handlers[113] = function() if locked("RotatingDoor1") then evt.StatusText("Locked") return end if ON_OPEN.RotatingDoor1 or ON_CLOSE.RotatingDoor1 then useGroup("RotatingDoor1") else evt.SetDoorState(90, DoorAction.Trigger) end end   -- RotatingDoor1
handlers[114] = function() if locked("SBrick") then evt.StatusText("Locked") return end if ON_OPEN.SBrick or ON_CLOSE.SBrick then useGroup("SBrick") else evt.SetDoorState(91, DoorAction.Trigger) evt.SetDoorState(92, DoorAction.Trigger) end end   -- SBrick
handlers[115] = function() if locked("StairGate") then evt.StatusText("Locked") return end if ON_OPEN.StairGate or ON_CLOSE.StairGate then useGroup("StairGate") else evt.SetDoorState(107, DoorAction.Trigger) end end   -- StairGate
handlers[116] = function() if locked("ToWindMazeGate") then evt.StatusText("Locked") return end if ON_OPEN.ToWindMazeGate or ON_CLOSE.ToWindMazeGate then useGroup("ToWindMazeGate") else evt.SetDoorState(110, DoorAction.Trigger) end end   -- ToWindMazeGate
handlers[117] = function() if locked("WaterGate0") then evt.StatusText("Locked") return end if ON_OPEN.WaterGate0 or ON_CLOSE.WaterGate0 then useGroup("WaterGate0") else evt.SetDoorState(121, DoorAction.Trigger) end end   -- WaterGate0
handlers[118] = function() if locked("WaterGate1") then evt.StatusText("Locked") return end if ON_OPEN.WaterGate1 or ON_CLOSE.WaterGate1 then useGroup("WaterGate1") else evt.SetDoorState(122, DoorAction.Trigger) end end   -- WaterGate1
handlers[119] = function() if locked("EDoor") then evt.StatusText("Locked") return end if ON_OPEN.EDoor or ON_CLOSE.EDoor then useGroup("EDoor") else evt.SetDoorState(5, DoorAction.Trigger) evt.SetDoorState(6, DoorAction.Trigger) end end   -- EDoor
handlers[120] = function() if locked("Lever16") then evt.StatusText("Locked") return end if ON_OPEN.Lever16 or ON_CLOSE.Lever16 then useGroup("Lever16") else evt.SetDoorState(17, DoorAction.Trigger) end end   -- Lever16
handlers[121] = function() if locked("Lever18") then evt.StatusText("Locked") return end if ON_OPEN.Lever18 or ON_CLOSE.Lever18 then useGroup("Lever18") else evt.SetDoorState(19, DoorAction.Trigger) end end   -- Lever18
handlers[122] = function() if locked("SecretDoor2") then evt.StatusText("Locked") return end if ON_OPEN.SecretDoor2 or ON_CLOSE.SecretDoor2 then useGroup("SecretDoor2") else evt.SetDoorState(93, DoorAction.Trigger) end end   -- SecretDoor2
handlers[123] = function() if locked("WaterGate2") then evt.StatusText("Locked") return end if ON_OPEN.WaterGate2 or ON_CLOSE.WaterGate2 then useGroup("WaterGate2") else evt.SetDoorState(123, DoorAction.Trigger) end end   -- WaterGate2

-- Button puzzle blocks (ButtonPuzzle.scr :UseMe -> ButtonPad.scr :Button<k>), pulls (Pull1-3: Reset).
handlers[300] = function() pushBlock("ButtonTrigger", 0) end   -- PuzzleDoor0
handlers[301] = function() pushBlock("ButtonTrigger", 1) end   -- PuzzleDoor1
handlers[302] = function() pushBlock("ButtonTrigger", 2) end   -- PuzzleDoor2
handlers[303] = function() pushBlock("ButtonTrigger", 3) end   -- PuzzleDoor3
handlers[304] = function() pushBlock("ButtonTrigger", 4) end   -- PuzzleDoor4
handlers[305] = function() pushBlock("ButtonTrigger", 5) end   -- PuzzleDoor5
handlers[306] = function() pushBlock("ButtonTrigger", 6) end   -- PuzzleDoor6
handlers[307] = function() pushBlock("ButtonTrigger", 7) end   -- PuzzleDoor7
handlers[308] = function() pushBlock("ButtonTrigger", 8) end   -- PuzzleDoor8
handlers[309] = function() pushBlock("ButtonTrigger", 9) end   -- PuzzleDoor9
handlers[310] = function() pushBlock("ButtonTrigger", 10) end   -- PuzzleDoor10
handlers[311] = function() pushBlock("ButtonTrigger", 11) end   -- PuzzleDoor11
handlers[312] = function() pushBlock("ButtonTrigger", 12) end   -- PuzzleDoor12
handlers[313] = function() pushBlock("ButtonTrigger", 13) end   -- PuzzleDoor13
handlers[314] = function() pushBlock("ButtonTrigger", 14) end   -- PuzzleDoor14
handlers[315] = function() pushBlock("ButtonTrigger", 15) end   -- PuzzleDoor15
handlers[316] = function() pushBlock("ButtonTrigger0", 0) end   -- PuzzleDoorB0
handlers[317] = function() pushBlock("ButtonTrigger0", 1) end   -- PuzzleDoorB1
handlers[318] = function() pushBlock("ButtonTrigger0", 2) end   -- PuzzleDoorB2
handlers[319] = function() pushBlock("ButtonTrigger0", 3) end   -- PuzzleDoorB3
handlers[320] = function() pushBlock("ButtonTrigger0", 4) end   -- PuzzleDoorB4
handlers[321] = function() pushBlock("ButtonTrigger0", 5) end   -- PuzzleDoorB5
handlers[322] = function() pushBlock("ButtonTrigger0", 6) end   -- PuzzleDoorB6
handlers[323] = function() pushBlock("ButtonTrigger0", 7) end   -- PuzzleDoorB7
handlers[324] = function() pushBlock("ButtonTrigger0", 8) end   -- PuzzleDoorB8
handlers[325] = function() pushBlock("ButtonTrigger0", 9) end   -- PuzzleDoorB9
handlers[326] = function() pushBlock("ButtonTrigger0", 10) end   -- PuzzleDoorB10
handlers[327] = function() pushBlock("ButtonTrigger0", 11) end   -- PuzzleDoorB11
handlers[328] = function() pushBlock("ButtonTrigger0", 12) end   -- PuzzleDoorB12
handlers[329] = function() pushBlock("ButtonTrigger0", 13) end   -- PuzzleDoorB13
handlers[330] = function() pushBlock("ButtonTrigger0", 14) end   -- PuzzleDoorB14
handlers[331] = function() pushBlock("ButtonTrigger0", 15) end   -- PuzzleDoorB15
handlers[332] = function() pushBlock("ButtonTrigger1", 0) end   -- PuzzleDoorC0
handlers[333] = function() pushBlock("ButtonTrigger1", 1) end   -- PuzzleDoorC1
handlers[334] = function() pushBlock("ButtonTrigger1", 2) end   -- PuzzleDoorC2
handlers[335] = function() pushBlock("ButtonTrigger1", 3) end   -- PuzzleDoorC3
handlers[336] = function() pushBlock("ButtonTrigger1", 4) end   -- PuzzleDoorC4
handlers[337] = function() pushBlock("ButtonTrigger1", 5) end   -- PuzzleDoorC5
handlers[338] = function() pushBlock("ButtonTrigger1", 6) end   -- PuzzleDoorC6
handlers[339] = function() pushBlock("ButtonTrigger1", 7) end   -- PuzzleDoorC7
handlers[340] = function() pushBlock("ButtonTrigger1", 8) end   -- PuzzleDoorC8
handlers[341] = function() pushBlock("ButtonTrigger1", 9) end   -- PuzzleDoorC9
handlers[342] = function() pushBlock("ButtonTrigger1", 10) end   -- PuzzleDoorC10
handlers[343] = function() pushBlock("ButtonTrigger1", 11) end   -- PuzzleDoorC11
handlers[344] = function() pushBlock("ButtonTrigger1", 12) end   -- PuzzleDoorC12
handlers[345] = function() pushBlock("ButtonTrigger1", 13) end   -- PuzzleDoorC13
handlers[346] = function() pushBlock("ButtonTrigger1", 14) end   -- PuzzleDoorC14
handlers[347] = function() pushBlock("ButtonTrigger1", 15) end   -- PuzzleDoorC15
handlers[360] = function() useGroup("Pull1") after(1, function() closeGroup("Pull1") end) end   -- Pull1: OpenTrigger0 ButtonTrigger Reset
handlers[361] = function() useGroup("Pull2") after(1, function() closeGroup("Pull2") end) end   -- Pull2: OpenTrigger0 ButtonTrigger0 Reset
handlers[362] = function() useGroup("Pull3") after(1, function() closeGroup("Pull3") end) end   -- Pull3: OpenTrigger0 ButtonTrigger1 Reset

-- Rotating Lever 17 (OpenTrigger0 TrapDoor1 open): the trap doors drop into the water pit; Levers 16/18 name
-- 'Upper Chomper 1/2', which the DAT does not have (they only swing).
handlers[363] = function() useGroup("Lever17") end
-- The gear elevator (LowerLever, LowerLever0: Open/CloseTrigger GearElevator toggle; Lift 912 LT up). Its
-- gears (ElevatorGear1/2, RotatingBrush AttachTo GearElevator: they ride the lift) spin while it moves: the
-- levers toggle them on, the lift's Open/CloseTriggers reverse them and turn them off as it arrives (912 LT
-- at 200 LT/s).
local function lift()
    useGroup("GearElevator")
    MM9.playSound("sounds/door/elestart.wav")
    for _, gear in ipairs({DOORS.ElevatorGear1, DOORS.ElevatorGear2}) do evt.SpinMover(gear, "on") end
    after(912 / 200, function()
        for _, gear in ipairs({DOORS.ElevatorGear1, DOORS.ElevatorGear2}) do
            evt.SpinMover(gear, "reverse"); evt.SpinMover(gear, "off")
        end
    end)
end
handlers[364] = function() for _, id in ipairs(GROUPS.LowerLever) do evt.SetDoorState(id, DoorAction.Trigger) end lift() end
handlers[365] = function() for _, id in ipairs(GROUPS.LowerLever0) do evt.SetDoorState(id, DoorAction.Trigger) end lift() end
-- HiddenButton1 (Button, OpenTriggers: lock itself, TreasureDoor and TreasureDoor0 open).
handlers[366] = function() if not locked("HiddenButton1") then openGroup("HiddenButton1") end end
-- ToLowerTombGate (DoorLock.scr "599"): opens for a party with item 599. The gate has no Open or
-- CloseTriggers and shuts by itself (CloseWaitTime), so a click toggles the gate itself, not the script's open
-- flag (which its auto-close never cleared: a click after it shut did nothing).
handlers[367] = function()
    if MM9.hasItem(599, "1000terrors:DoorLock") == 1 or MM9.hasItem(599, "1000terrors:DoorLock") == true then
        for _, id in ipairs(GROUPS.ToLowerTombGate) do evt.SetDoorState(id, DoorAction.Trigger) end
    else evt.StatusText("Locked") end
end
-- StairGate0 (Door, PushOpen, AITriggerable, CloseWaitTime 10; DoorLock.scr "600; 1"):
-- DoorLock's :OnUse, with the stairs key (600, TreasureChest5) in the packs, unlocks the gate and
-- takes the key (bTakeKey), then exits FALSE: the door's own use goes on. The DAT leaves the gate unlocked, so a
-- use opens it with or without the key. MM9's monsters push it open (AITriggerable): the poll opens it for a
-- hostile monster beside it (on the landing, or south of it once StairGate is open). The gate shuts by itself
-- (its CloseWaitTime), so a use always opens it and its open flag clears when it has shut again.
local gate0Opens = 0
local function openGate0()
    for _, id in ipairs(GROUPS.StairGate0) do evt.SetDoorState(id, DoorAction.Open) end
    set("OpenStairGate0", 1)
    gate0Opens = gate0Opens + 1
    local this = gate0Opens
    after(25.4, function() if gate0Opens == this then set("OpenStairGate0", 0) end end)
end
handlers[369] = function()
    if MM9.hasItem(600, "1000terrors:DoorLock") == 1 then MM9.takeItem(600, "1000terrors:DoorLock") end
    openGate0()
end
-- FoyerDoorSouth1/2 (WinMan.scr :Init, TELP): shut and locked until the party holds key 108.
handlers[368] = function()
    if MM9.hasKey(108) == 0 then evt.StatusText("Locked") return end
    for _, id in ipairs(GROUPS.FoyerDoorSouth) do evt.SetDoorState(id, DoorAction.Trigger) end
end

-- WinMan.scr :onSwitch, on each use and on WG_Shot2Cam's switch in the cinematic: PlayAnim up while bUp is
-- FALSE, else Down, and bUp flips. bUp starts FALSE on a wheel at rest (up), so the first use shows only up's
-- 200 ms blend, a twitch: nothing here. WinWheel: 0 never used, 1 up (bUp TRUE), 2 down (bUp FALSE); the
-- clips are runtime only, so map load shows a wheel left down at the end of down.
local function winSwitch()
    if var("WinWheel") == 1 then
        set("WinWheel", 2)
        evt.PlayDecorationClip(1370, "down")
    else
        if var("WinWheel") == 2 then evt.PlayDecorationClip(1370, "up") end
        set("WinWheel", 1)
    end
end
-- The win switch (WinMan.scr :OnUse): nothing from beyond the wall (LT z below -3680); without key 108 it only
-- throws the lightning (Lightning1/2, 7 s); with it the cinematic njam_freeze_win (cinematics_1000t.py).
WIN_EXPERIENCE = 22500 -- MM9 GiveExp 234000, mm9_quest_xp_profile.yml
handlers[370] = function()
    local _, py = evt.GetPartyPosition()
    if py < -9421 then return end
    winSwitch()
    if MM9.hasKey(108) == 0 then
        MM9.playSound("sounds\\door\\cell_door_close.wav")
        MM9.playSound("sounds\\ambient\\thunder\\thunder01.wav")
        evt.Beam("Lightning1", "openyamm:fx/arc_beam", 8765, -11611, 4142, 8776, -11704, 3016, 7)
        evt.Beam("Lightning2", "openyamm:fx/arc_beam", 9247, -11858, 4142, 8776, -11704, 3016, 7)
        set("SwitchThrown", var("SwitchThrown") + 1)
        return
    end
    MM9Cinematic.start("njam_freeze_win")
end

-- The genie lamp (GiveRandom.scr, once): gold 100-1000, experience 100-1000, an item of its list, healing
-- 100-1000 or (as MM9's GiveAttribute 1-2) experience again; TriggerSmokeOn is only smoke.
local GENIE_ITEMS = {2, 359, 81, 86, 285, 71, 96, 97, 26, 76, 87, 61, 36, 18, 41, 297, 296, 295, 2, 56, 66, 292, 291, 290, 288, 287, 294, 155, 150, 547, 142, 160, 548, 134, 133, 126, 127}
handlers[371] = function()
    if var("GenieUsed") == 1 then return end
    set("GenieUsed", 1)
    local roll = math.random(0, 4)
    if roll == 0 then MM9.giveGold(math.random(100, 1000))
    elseif roll == 2 then give(GENIE_ITEMS[math.random(1, #GENIE_ITEMS)], "1000terrors:GiveRandom")
    elseif roll == 3 then AddValue(HP, math.random(100, 1000))
    else MM9.giveExperience(math.random(100, 1000)) end
    MM9.playSound("sounds/magic/windup10.wav")
end

-- TauntMan.scr (Trigger19 Start; key 108 without 497): the cinematic njam_taunt (cinematics_1000t.py:
-- key 497, Door0, Njam's walk to TauntMarker and his vanishing).
handlers[379] = function()
    if MM9.hasKey(108) == 0 or MM9.hasKey(497) == 1 then return end
    MM9Cinematic.start("njam_taunt")
end

-- Monsters' DeathTriggerTarget (GreaterDemon1 -> Spawner8, Oculus7 -> TP5, LesserDemon13/14 -> TP4 ...).
handlers[382] = function(context)
    local d = context.actorIndex ~= nil and DEATH[context.actorIndex] or nil
    if d ~= nil then send(d[1], d[2]) end
    -- EndDemon.scr :OnDeath (lines 25-33): sDoorA Open (declared Door1, then Door0): the double gate before the
    -- win switch, both leaves
    if context.actorIndex ~= nil and var("EndDemon" .. context.actorIndex) == 1 then
        set("EndDemon" .. context.actorIndex, 0)
        set("EndDemonDead", 1)
        openGroup("Door0")
        openGroup("Door1")
    end
    -- LesserDemon.scr p0 1 (the placed LesserDemon13/14, and the spawned "LesserDemon ScriptParams 1" spawn()
    -- marks): :OnDeathDone spawns a Greater Demon at the body (sSpawnCmd "GreaterDemon ScriptParams 1": it
    -- spawns in, the summon's mm9 script_params).
    if context.actorIndex ~= nil and (GREATER_ON_DEATH[context.actorIndex]
            or var("Greater" .. context.actorIndex) == 1) then
        set("Greater" .. context.actorIndex, 0)
        local x, y, z = evt.GetMapActorPosition(context.actorIndex)
        if x ~= nil then evt.SummonMonstersById({monster = 9242, x = x, y = y, z = z, radius = 32, count = 1, mm9 = {script_params = "1"}, effect = "mm9:GreaterDemon"}) end   -- GreaterDemon.scr :SpawnIn: DoClientFX GreaterDemon
    end
end

-- ChessBase.inc :PawnToQueen: a pawn whose attack ends on the last rank (ChessPiece1 from square 51) becomes a
-- Terror at that square once its slide is done (2 s): the piece is gone (RemoveObject), the Terror (HitPoints 1069, its fireblue
-- effect) is the party's enemy. The other pieces stay on their squares here (MM9 slides each onto the square it
-- attacks), so the pawn on square 35 never reaches the last rank; a square only a queened pawn attacked is safe.
local queening = {}
local function chessAttacked(c)
    for _, piece in ipairs(c.pieces) do if var("Queened" .. piece) == 0 then return true end end
    return false
end
local function hidePawn(pawn)
    for _, f in ipairs(PAWN_FACES[pawn] or {}) do evt.SetFacetBit(-f, 536879104, true) end
end
local function queen(c)
    if c.queen == nil or var("Queened" .. c.queen) == 1 or queening[c.queen] then return end
    queening[c.queen] = true
    after(2.0, function()
        set("Queened" .. c.queen, 1)
        hidePawn(c.queen)
        evt.SummonMonstersById({monster = 9164, x = c.at[1], y = c.at[2], z = c.at[3], radius = 64, count = 1, hpScale = 1.2895})
        evt.SpawnWorldEffect("mm9:fireblue", c.at[1], c.at[2], c.at[3], 1)
    end)
end

-- The poll (four times a second): MM9's Trigger volumes (any part of the party in the box; StartOn, on/off
-- messages), the chess squares, the shooters and the scheduled waits.
local inside, onSquare = {}, false
handlers[380] = function()
    evt.StartTimer(380, seconds(0.25))
    tick = tick + 1
    local x, y, z = evt.GetPartyPosition()
    for _, t in ipairs(TRIGGERS) do
        if t.box ~= nil then
            local now = inBox(t.box, x, y, z)
            if now and not inside[t.name] and triggerOn(t.name) then fireTrigger(t.name) end
            inside[t.name] = now
        end
    end
    for name, lift in pairs(LIFTS) do
        if inBox(lift.box, x, y, z) and tick >= (liftIdleAt[name] or 0) then touchLift(name) end
    end
    local square = nil
    for _, c in ipairs(CHESS) do if inBox(c.box, x, y, z) and chessAttacked(c) then square = c end end
    if square ~= nil and not onSquare then
        MM9.playSound("sounds/door/doorslidestone.wav")
        hurt(60)
        set("ChessHits", var("ChessHits") + 1)
        queen(square)
        MM9Cinematic.chessCapture(square)   -- ChessBase.inc :StartCamera (cinematics_1000t.py)
    end
    onSquare = square ~= nil
    if tick % 4 == 0 and not isOpen("StairGate0") then     -- every actor, the spawned ones too
        local scan = 0   -- not `index`: pack growth's Lua scan (density.py) takes every `index` for one
        while true do
            local ax, ay, az = evt.GetMapActorPosition(scan)
            if ax == nil then break end
            -- south of the gates a monster reaches StairGate0 only through an open StairGate
            if math.abs(ax - GATE0[1]) < GATE0_REACH and math.abs(ay - GATE0[2]) < GATE0_REACH
                    and math.abs(az - GATE0[3]) < GATE0_REACH and (ay > GATE0[2] or isOpen("StairGate"))
                    and evt.IsMapActorHostile(scan) then
                openGate0()
                set("Gate0ByMonster", 1)
                break
            end
            scan = scan + 1
        end
    end
    for name, f in pairs(firing) do
        if tick >= f.next then
            fire(name)
            f.next = tick + SHOOTERS[name].every
            if f.left ~= nil then
                f.left = f.left - 1
                if f.left <= 0 then
                    firing[name] = nil
                    if SHOOTERS[name].stop ~= nil then fireTrigger(SHOOTERS[name].stop) end
                end
            end
        end
    end
    local due = {}
    for i = #tasks, 1, -1 do if tasks[i].at <= tick then table.insert(due, tasks[i].fn) table.remove(tasks, i) end end
    for _, fn in ipairs(due) do fn() end
end

-- Map load: locks (Locked doors, the B and C puzzle walls), the puzzle walls hidden until their trap, destroyed
-- statues gone, Njam's triggers only with key 108 (SpawnNjam.scr :Init), the taken scroll, the poll.
handlers[1] = function()
    if var("Loaded") == 0 then
        set("Loaded", 1)
        set("LockToLowerTombGate", 0)
        for _, g in ipairs({"PuzzleDoorB0", "PuzzleDoorB1", "PuzzleDoorB2", "PuzzleDoorB3", "PuzzleDoorB4", "PuzzleDoorB5", "PuzzleDoorB6", "PuzzleDoorB7", "PuzzleDoorB8", "PuzzleDoorB9", "PuzzleDoorB10", "PuzzleDoorB11", "PuzzleDoorB12", "PuzzleDoorB13", "PuzzleDoorB14", "PuzzleDoorB15", "PuzzleDoorC0", "PuzzleDoorC1", "PuzzleDoorC2", "PuzzleDoorC3", "PuzzleDoorC4", "PuzzleDoorC5", "PuzzleDoorC6", "PuzzleDoorC7", "PuzzleDoorC8", "PuzzleDoorC9", "PuzzleDoorC10", "PuzzleDoorC11", "PuzzleDoorC12", "PuzzleDoorC13", "PuzzleDoorC14", "PuzzleDoorC15"}) do set("Lock" .. g, 1) end
    end
    -- StairGate (Door: no PushOpen, no lock in the DAT): no use opens it, only LesserDemon0's DeathTriggerTarget
    -- (StairGate open); the lock answers a click as MM9's LockJiggle (the death's open ignores it)
    if not isOpen("StairGate") then set("LockStairGate", 1) end
    for pad, _ in pairs(PADS) do showPad(pad, var(pad .. "State") == 1) end
    for pawn, _ in pairs(PAWN_FACES) do if var("Queened" .. pawn) == 1 then hidePawn(pawn) end end
    for name, skull in pairs(SKULLS) do evt.AimDecoration(skull.cog, -180 * var("SkullTurns" .. name)) end
    for name, statue in pairs(STATUES) do
        if var("StatueCasting" .. name) == 1 then statueCasting(name) else evt.PlayDecorationClip(statue.cog, "fidget2") end
    end
    if var("WinWheel") == 2 then evt.PlayDecorationClip(1370, "down", "end") end
    for name, faces in pairs(PIECES) do
        if var("Destroyed" .. name) == 1 then for _, f in ipairs(faces) do evt.SetFacetBit(-f, 536879104, true) end end
    end
    local njam = MM9.hasKey(108) == 1
    for marker, _ in pairs(NJAM_MARKERS) do end
    for _, t in ipairs({"TriggerNjam0", "TriggerNjam1", "TriggerNjam2", "TriggerNjam3", "TriggerNjam4", "TriggerNjam6", "TriggerNjam7"}) do set("Trig" .. t, njam and 1 or 2) end
    evt.StartTimer(380, seconds(0.25))
end
-- MM9's PerceptionBrushes (dungeon/perception.py): the red glow shows to a party whose Perception reaches the
-- brush's PerceptionValue, checked on load and every 3 s; map Lua turns one off for good with
-- set("HintOff<cog>", 1) (MM9's Off message to the brush).
local HINTS = {[23435] = 20, [23436] = 20, [23437] = 20, [23438] = 20, [23439] = 20, [23440] = 20, [23441] = 20}
handlers[901] = function()
    for cog, value in pairs(HINTS) do
        local want = (var("HintOff" .. cog) == 0 and evt.CheckSkill(29, 0, value)) and 2 or 1
        if var("Hint" .. cog) ~= want then
            set("Hint" .. cog, want)
            evt.SetFacetBit(cog, FacetBits.Invisible, want == 1)
        end
    end
end
-- MM9's touch Triggers switching AmbientSounds (dungeon/objects.py): entering one sends its On / Off / Toggle
-- (the scene sound's map variable AmbientSound<key>: 1 on, 2 off); ActivationCount limits the uses.
local SOUND_TRIGGERS = {
    {name = "SpawnTrigger0", box = {{3813, -12653, 2141}, {4543, -12251, 2393}}, uses = 1, switches = {{185, "on", false}}},
    {name = "SpawnTrigger1", box = {{3977, -12141, 2141}, {4706, -11739, 2393}}, uses = 1, switches = {{185, "on", false}}},
    {name = "SpawnTrigger2", box = {{2656, -11997, 2141}, {3652, -11596, 2393}}, uses = 1, switches = {{185, "on", false}}},
    {name = "SpawnTrigger3", box = {{3342, -11424, 2141}, {4072, -10695, 2393}}, uses = 1, switches = {{185, "on", false}}},
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
    for cog, _ in pairs(HINTS) do set("Hint" .. cog, 0) end
    handlers[901]()
    handlers[903]()
end

RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(43, "Chest", handlers[43], "Chest")
RegisterEvent(44, "Chest", handlers[44], "Chest")
RegisterEvent(45, "Chest", handlers[45], "Chest")
RegisterEvent(46, "Chest", handlers[46], "Chest")
RegisterEvent(47, "Chest", handlers[47], "Chest")
RegisterEvent(48, "Chest", handlers[48], "Chest")
RegisterEvent(49, "Chest", handlers[49], "Chest")
RegisterEvent(50, "Chest", handlers[50], "Chest")
RegisterEvent(51, "Chest", handlers[51], "Chest")
RegisterEvent(52, "Chest", handlers[52], "Chest")
RegisterEvent(53, "Chest", handlers[53], "Chest")
RegisterEvent(54, "Chest", handlers[54], "Chest")
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
RegisterEvent(121, "Door", handlers[121], "Door")
RegisterEvent(122, "Door", handlers[122], "Door")
RegisterEvent(123, "Door", handlers[123], "Door")
RegisterEvent(300, "Puzzle block", handlers[300], "Block")
RegisterEvent(301, "Puzzle block", handlers[301], "Block")
RegisterEvent(302, "Puzzle block", handlers[302], "Block")
RegisterEvent(303, "Puzzle block", handlers[303], "Block")
RegisterEvent(304, "Puzzle block", handlers[304], "Block")
RegisterEvent(305, "Puzzle block", handlers[305], "Block")
RegisterEvent(306, "Puzzle block", handlers[306], "Block")
RegisterEvent(307, "Puzzle block", handlers[307], "Block")
RegisterEvent(308, "Puzzle block", handlers[308], "Block")
RegisterEvent(309, "Puzzle block", handlers[309], "Block")
RegisterEvent(310, "Puzzle block", handlers[310], "Block")
RegisterEvent(311, "Puzzle block", handlers[311], "Block")
RegisterEvent(312, "Puzzle block", handlers[312], "Block")
RegisterEvent(313, "Puzzle block", handlers[313], "Block")
RegisterEvent(314, "Puzzle block", handlers[314], "Block")
RegisterEvent(315, "Puzzle block", handlers[315], "Block")
RegisterEvent(316, "Puzzle block", handlers[316], "Block")
RegisterEvent(317, "Puzzle block", handlers[317], "Block")
RegisterEvent(318, "Puzzle block", handlers[318], "Block")
RegisterEvent(319, "Puzzle block", handlers[319], "Block")
RegisterEvent(320, "Puzzle block", handlers[320], "Block")
RegisterEvent(321, "Puzzle block", handlers[321], "Block")
RegisterEvent(322, "Puzzle block", handlers[322], "Block")
RegisterEvent(323, "Puzzle block", handlers[323], "Block")
RegisterEvent(324, "Puzzle block", handlers[324], "Block")
RegisterEvent(325, "Puzzle block", handlers[325], "Block")
RegisterEvent(326, "Puzzle block", handlers[326], "Block")
RegisterEvent(327, "Puzzle block", handlers[327], "Block")
RegisterEvent(328, "Puzzle block", handlers[328], "Block")
RegisterEvent(329, "Puzzle block", handlers[329], "Block")
RegisterEvent(330, "Puzzle block", handlers[330], "Block")
RegisterEvent(331, "Puzzle block", handlers[331], "Block")
RegisterEvent(332, "Puzzle block", handlers[332], "Block")
RegisterEvent(333, "Puzzle block", handlers[333], "Block")
RegisterEvent(334, "Puzzle block", handlers[334], "Block")
RegisterEvent(335, "Puzzle block", handlers[335], "Block")
RegisterEvent(336, "Puzzle block", handlers[336], "Block")
RegisterEvent(337, "Puzzle block", handlers[337], "Block")
RegisterEvent(338, "Puzzle block", handlers[338], "Block")
RegisterEvent(339, "Puzzle block", handlers[339], "Block")
RegisterEvent(340, "Puzzle block", handlers[340], "Block")
RegisterEvent(341, "Puzzle block", handlers[341], "Block")
RegisterEvent(342, "Puzzle block", handlers[342], "Block")
RegisterEvent(343, "Puzzle block", handlers[343], "Block")
RegisterEvent(344, "Puzzle block", handlers[344], "Block")
RegisterEvent(345, "Puzzle block", handlers[345], "Block")
RegisterEvent(346, "Puzzle block", handlers[346], "Block")
RegisterEvent(347, "Puzzle block", handlers[347], "Block")
RegisterEvent(360, "Pull", handlers[360], "Lever")
RegisterEvent(361, "Pull", handlers[361], "Lever")
RegisterEvent(362, "Pull", handlers[362], "Lever")
RegisterEvent(1, "Map load", handlers[1])
RegisterMapTimerEvent(380, seconds(3), handlers[380], "Poll", "", seconds(3))
RegisterEvent(363, "Lever", handlers[363], "Lever")
RegisterEvent(364, "Lever", handlers[364], "Lever")
RegisterEvent(365, "Lever", handlers[365], "Lever")
RegisterEvent(366, "Button", handlers[366], "Button")
RegisterEvent(367, "Gate", handlers[367], "Gate")
RegisterEvent(369, "Gate", handlers[369], "Gate")
RegisterEvent(368, "Door", handlers[368], "Door")
RegisterEvent(370, "Switch", handlers[370], "Switch")
RegisterEvent(371, "Genie lamp", handlers[371], "Lamp")
RegisterEvent(379, "Taunt", handlers[379])
RegisterMapTimerEvent(901, seconds(3), handlers[901], "Perception hints", "", seconds(3))
RegisterMapTimerEvent(903, seconds(3), handlers[903], "Ambient triggers", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
RegisterMonsterKilledHook(382, "Death triggers", handlers[382])


-- MM9 cutscenes as in-engine cinematics (devdocs/mm9_rework/MM9_CUTSCENES.md; mm9r_common/cutscenes.py).
MM9Cinematic = MM9Cinematic or { steps = {}, play = {} }

function MM9Cinematic.runStep(id, index)
    local step = MM9Cinematic.steps[id][index]
    local name = "Cinema." .. id .. ".step." .. step[1]
    if evt.GetMapVar(name, 0) == 0 then
        evt.SetMapVar(name, 1)
        step[2]()
    end
end

function MM9Cinematic.finish(id)
    for index = 1, #MM9Cinematic.steps[id] do
        MM9Cinematic.runStep(id, index)
    end
end

-- Starts a cinematic once per map state (its started map var); a second start while or after it played does nothing.
function MM9Cinematic.start(id)
    local play = MM9Cinematic.play[id]
    if play ~= nil then
        play()
    end
end

-- Cinematic njam_freeze_win (WinMan.scr :OnUse..:ChangeLevel, WG_NjamCam/Shot2/Shot5/Shot7Cam.scr, NjamFreeze.scr, WG_hand.scr): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["njam_freeze_win"] = {
    { "win", function()
        if MM9.hasKey(109) == 0 then MM9.giveExperience(WIN_EXPERIENCE) end
        MM9.playSound("sounds/events/quest.wav")
        -- :DestroyMonsters: up to 10 monsters within 1024 LT of the switch, not Njam (`scan`, not
        -- `index`: pack growth's Lua scan, density.py, takes every `index` for one)
        local removed, scan = 0, 0
        while removed < 10 do
            local ax, ay, az = evt.GetMapActorPosition(scan)
            if ax == nil then break end
            if scan ~= ACTOR.Njam and scan ~= ACTOR.NjamtheMeddler0 and evt.IsMapActorHostile(scan)
                    and (ax - 8929) ^ 2 + (ay - -9364) ^ 2 + (az - 2908) ^ 2 < 2621 ^ 2 then
                MM9.removeActor(scan)
                removed = removed + 1
            end
            scan = scan + 1
        end
    end },
    { "ball", function()
        evt.SpawnWorldEffect("mm9:Njam_lightball_for_cutscene", 8776, -11704, 2937, 1)
    end },
    { "lightning", function()
        evt.Beam("Lightning1", "openyamm:fx/arc_beam", 8765, -11611, 4142, 8776, -11704, 3016, 7)
        evt.Beam("Lightning2", "openyamm:fx/arc_beam", 9247, -11858, 4142, 8776, -11704, 3016, 7)
    end },
    { "exit", function()
        MM9.giveKey(109)
        set("Won", 1)
        evt.MoveToMap(-7281, 2952, 1, 0, 0, 0, 0, 0, "hallofthegods.blv")
    end },
    { "switch", function()
        winSwitch()
    end },
}
RegisterEvent(36001, "Cinema njam_freeze_win: win", function() MM9Cinematic.runStep("njam_freeze_win", 1) end)
RegisterEvent(36002, "Cinema njam_freeze_win: ball", function() MM9Cinematic.runStep("njam_freeze_win", 2) end)
RegisterEvent(36003, "Cinema njam_freeze_win: lightning", function() MM9Cinematic.runStep("njam_freeze_win", 3) end)
RegisterEvent(36004, "Cinema njam_freeze_win: exit", function() MM9Cinematic.runStep("njam_freeze_win", 4) end)
RegisterEvent(36005, "Cinema njam_freeze_win: switch", function() MM9Cinematic.runStep("njam_freeze_win", 5) end)
RegisterEvent(36000, "Cinema njam_freeze_win: done", function() MM9Cinematic.finish("njam_freeze_win") end)
MM9Cinematic.play["njam_freeze_win"] = function()
    if evt.GetMapVar("Cinema.njam_freeze_win.started", 0) == 0 then
        evt.SetMapVar("Cinema.njam_freeze_win.started", 1)
        evt.PlayCinematic("njam_freeze_win", 36000)
    end
end

-- Cinematic njam_taunt (TauntMan.scr :OnStart..:FadeOut2, NjamTaunt.scr): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["njam_taunt"] = {
    { "key", function()
        MM9.giveKey(497) evt.SetMonGroupBit(1, MonsterBits.Hostile, false)
    end },
    { "door_open", function()
        openGroup("Door0")
    end },
    { "door_close", function()
        if var("EndDemonDead") ~= 1 then closeGroup("Door0") end
    end },
    { "vanish", function()
        evt.SpawnWorldEffect("mm9:GreaterDemon", 8151, -9748, 2808, 1)
    end },
}
RegisterEvent(36051, "Cinema njam_taunt: key", function() MM9Cinematic.runStep("njam_taunt", 1) end)
RegisterEvent(36052, "Cinema njam_taunt: door_open", function() MM9Cinematic.runStep("njam_taunt", 2) end)
RegisterEvent(36053, "Cinema njam_taunt: door_close", function() MM9Cinematic.runStep("njam_taunt", 3) end)
RegisterEvent(36054, "Cinema njam_taunt: vanish", function() MM9Cinematic.runStep("njam_taunt", 4) end)
RegisterEvent(36050, "Cinema njam_taunt: done", function() MM9Cinematic.finish("njam_taunt") end)
MM9Cinematic.play["njam_taunt"] = function()
    if evt.GetMapVar("Cinema.njam_taunt.started", 0) == 0 then
        evt.SetMapVar("Cinema.njam_taunt.started", 1)
        evt.PlayCinematic("njam_taunt", 36050)
    end
end

-- Cinematic chess_capture_2 (ChessCamera.scr :ViewChessPiece: square 2, ChessPiece2 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_2"] = {
}
RegisterEvent(36100, "Cinema chess_capture_2: done", function() MM9Cinematic.finish("chess_capture_2") end)
MM9Cinematic.play["chess_capture_2"] = function()
    if evt.GetMapVar("Cinema.chess_capture_2.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_2.started", 1)
        evt.PlayCinematic("chess_capture_2", 36100)
    end
end

-- Cinematic chess_capture_4 (ChessCamera.scr :ViewChessPiece: square 4, ChessPiece2 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_4"] = {
}
RegisterEvent(36101, "Cinema chess_capture_4: done", function() MM9Cinematic.finish("chess_capture_4") end)
MM9Cinematic.play["chess_capture_4"] = function()
    if evt.GetMapVar("Cinema.chess_capture_4.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_4.started", 1)
        evt.PlayCinematic("chess_capture_4", 36101)
    end
end

-- Cinematic chess_capture_5 (ChessCamera.scr :ViewChessPiece: square 5, ChessPiece4 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_5"] = {
}
RegisterEvent(36102, "Cinema chess_capture_5: done", function() MM9Cinematic.finish("chess_capture_5") end)
MM9Cinematic.play["chess_capture_5"] = function()
    if evt.GetMapVar("Cinema.chess_capture_5.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_5.started", 1)
        evt.PlayCinematic("chess_capture_5", 36102)
    end
end

-- Cinematic chess_capture_8 (ChessCamera.scr :ViewChessPiece: square 8, ChessPiece4 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_8"] = {
}
RegisterEvent(36103, "Cinema chess_capture_8: done", function() MM9Cinematic.finish("chess_capture_8") end)
MM9Cinematic.play["chess_capture_8"] = function()
    if evt.GetMapVar("Cinema.chess_capture_8.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_8.started", 1)
        evt.PlayCinematic("chess_capture_8", 36103)
    end
end

-- Cinematic chess_capture_9 (ChessCamera.scr :ViewChessPiece: square 9, ChessPiece2 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_9"] = {
}
RegisterEvent(36104, "Cinema chess_capture_9: done", function() MM9Cinematic.finish("chess_capture_9") end)
MM9Cinematic.play["chess_capture_9"] = function()
    if evt.GetMapVar("Cinema.chess_capture_9.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_9.started", 1)
        evt.PlayCinematic("chess_capture_9", 36104)
    end
end

-- Cinematic chess_capture_12 (ChessCamera.scr :ViewChessPiece: square 12, ChessPiece4 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_12"] = {
}
RegisterEvent(36105, "Cinema chess_capture_12: done", function() MM9Cinematic.finish("chess_capture_12") end)
MM9Cinematic.play["chess_capture_12"] = function()
    if evt.GetMapVar("Cinema.chess_capture_12.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_12.started", 1)
        evt.PlayCinematic("chess_capture_12", 36105)
    end
end

-- Cinematic chess_capture_13 (ChessCamera.scr :ViewChessPiece: square 13, ChessPiece2 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_13"] = {
}
RegisterEvent(36106, "Cinema chess_capture_13: done", function() MM9Cinematic.finish("chess_capture_13") end)
MM9Cinematic.play["chess_capture_13"] = function()
    if evt.GetMapVar("Cinema.chess_capture_13.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_13.started", 1)
        evt.PlayCinematic("chess_capture_13", 36106)
    end
end

-- Cinematic chess_capture_15 (ChessCamera.scr :ViewChessPiece: square 15, ChessPiece5 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_15"] = {
}
RegisterEvent(36107, "Cinema chess_capture_15: done", function() MM9Cinematic.finish("chess_capture_15") end)
MM9Cinematic.play["chess_capture_15"] = function()
    if evt.GetMapVar("Cinema.chess_capture_15.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_15.started", 1)
        evt.PlayCinematic("chess_capture_15", 36107)
    end
end

-- Cinematic chess_capture_17 (ChessCamera.scr :ViewChessPiece: square 17, ChessPiece4 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_17"] = {
}
RegisterEvent(36108, "Cinema chess_capture_17: done", function() MM9Cinematic.finish("chess_capture_17") end)
MM9Cinematic.play["chess_capture_17"] = function()
    if evt.GetMapVar("Cinema.chess_capture_17.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_17.started", 1)
        evt.PlayCinematic("chess_capture_17", 36108)
    end
end

-- Cinematic chess_capture_19 (ChessCamera.scr :ViewChessPiece: square 19, ChessPiece4 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_19"] = {
}
RegisterEvent(36109, "Cinema chess_capture_19: done", function() MM9Cinematic.finish("chess_capture_19") end)
MM9Cinematic.play["chess_capture_19"] = function()
    if evt.GetMapVar("Cinema.chess_capture_19.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_19.started", 1)
        evt.PlayCinematic("chess_capture_19", 36109)
    end
end

-- Cinematic chess_capture_25 (ChessCamera.scr :ViewChessPiece: square 25, ChessPiece2 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_25"] = {
}
RegisterEvent(36110, "Cinema chess_capture_25: done", function() MM9Cinematic.finish("chess_capture_25") end)
MM9Cinematic.play["chess_capture_25"] = function()
    if evt.GetMapVar("Cinema.chess_capture_25.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_25.started", 1)
        evt.PlayCinematic("chess_capture_25", 36110)
    end
end

-- Cinematic chess_capture_29 (ChessCamera.scr :ViewChessPiece: square 29, ChessPiece2 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_29"] = {
}
RegisterEvent(36111, "Cinema chess_capture_29: done", function() MM9Cinematic.finish("chess_capture_29") end)
MM9Cinematic.play["chess_capture_29"] = function()
    if evt.GetMapVar("Cinema.chess_capture_29.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_29.started", 1)
        evt.PlayCinematic("chess_capture_29", 36111)
    end
end

-- Cinematic chess_capture_31 (ChessCamera.scr :ViewChessPiece: square 31, ChessPiece5 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_31"] = {
}
RegisterEvent(36112, "Cinema chess_capture_31: done", function() MM9Cinematic.finish("chess_capture_31") end)
MM9Cinematic.play["chess_capture_31"] = function()
    if evt.GetMapVar("Cinema.chess_capture_31.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_31.started", 1)
        evt.PlayCinematic("chess_capture_31", 36112)
    end
end

-- Cinematic chess_capture_33 (ChessCamera.scr :ViewChessPiece: square 33, ChessPiece4 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_33"] = {
}
RegisterEvent(36113, "Cinema chess_capture_33: done", function() MM9Cinematic.finish("chess_capture_33") end)
MM9Cinematic.play["chess_capture_33"] = function()
    if evt.GetMapVar("Cinema.chess_capture_33.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_33.started", 1)
        evt.PlayCinematic("chess_capture_33", 36113)
    end
end

-- Cinematic chess_capture_34 (ChessCamera.scr :ViewChessPiece: square 34, ChessPiece2 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_34"] = {
}
RegisterEvent(36114, "Cinema chess_capture_34: done", function() MM9Cinematic.finish("chess_capture_34") end)
MM9Cinematic.play["chess_capture_34"] = function()
    if evt.GetMapVar("Cinema.chess_capture_34.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_34.started", 1)
        evt.PlayCinematic("chess_capture_34", 36114)
    end
end

-- Cinematic chess_capture_35 (ChessCamera.scr :ViewChessPiece: square 35, ChessPiece4 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_35"] = {
}
RegisterEvent(36115, "Cinema chess_capture_35: done", function() MM9Cinematic.finish("chess_capture_35") end)
MM9Cinematic.play["chess_capture_35"] = function()
    if evt.GetMapVar("Cinema.chess_capture_35.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_35.started", 1)
        evt.PlayCinematic("chess_capture_35", 36115)
    end
end

-- Cinematic chess_capture_36 (ChessCamera.scr :ViewChessPiece: square 36, ChessPiece2 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_36"] = {
}
RegisterEvent(36116, "Cinema chess_capture_36: done", function() MM9Cinematic.finish("chess_capture_36") end)
MM9Cinematic.play["chess_capture_36"] = function()
    if evt.GetMapVar("Cinema.chess_capture_36.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_36.started", 1)
        evt.PlayCinematic("chess_capture_36", 36116)
    end
end

-- Cinematic chess_capture_40 (ChessCamera.scr :ViewChessPiece: square 40, ChessPiece4 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_40"] = {
}
RegisterEvent(36117, "Cinema chess_capture_40: done", function() MM9Cinematic.finish("chess_capture_40") end)
MM9Cinematic.play["chess_capture_40"] = function()
    if evt.GetMapVar("Cinema.chess_capture_40.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_40.started", 1)
        evt.PlayCinematic("chess_capture_40", 36117)
    end
end

-- Cinematic chess_capture_42 (ChessCamera.scr :ViewChessPiece: square 42, ChessPiece0 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_42"] = {
}
RegisterEvent(36118, "Cinema chess_capture_42: done", function() MM9Cinematic.finish("chess_capture_42") end)
MM9Cinematic.play["chess_capture_42"] = function()
    if evt.GetMapVar("Cinema.chess_capture_42.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_42.started", 1)
        evt.PlayCinematic("chess_capture_42", 36118)
    end
end

-- Cinematic chess_capture_43 (ChessCamera.scr :ViewChessPiece: square 43, ChessPiece5 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_43"] = {
}
RegisterEvent(36119, "Cinema chess_capture_43: done", function() MM9Cinematic.finish("chess_capture_43") end)
MM9Cinematic.play["chess_capture_43"] = function()
    if evt.GetMapVar("Cinema.chess_capture_43.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_43.started", 1)
        evt.PlayCinematic("chess_capture_43", 36119)
    end
end

-- Cinematic chess_capture_44 (ChessCamera.scr :ViewChessPiece: square 44, ChessPiece4 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_44"] = {
}
RegisterEvent(36120, "Cinema chess_capture_44: done", function() MM9Cinematic.finish("chess_capture_44") end)
MM9Cinematic.play["chess_capture_44"] = function()
    if evt.GetMapVar("Cinema.chess_capture_44.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_44.started", 1)
        evt.PlayCinematic("chess_capture_44", 36120)
    end
end

-- Cinematic chess_capture_50 (ChessCamera.scr :ViewChessPiece: square 50, ChessPiece5 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_50"] = {
}
RegisterEvent(36121, "Cinema chess_capture_50: done", function() MM9Cinematic.finish("chess_capture_50") end)
MM9Cinematic.play["chess_capture_50"] = function()
    if evt.GetMapVar("Cinema.chess_capture_50.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_50.started", 1)
        evt.PlayCinematic("chess_capture_50", 36121)
    end
end

-- Cinematic chess_capture_53 (ChessCamera.scr :ViewChessPiece: square 53, ChessPiece4 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_53"] = {
}
RegisterEvent(36122, "Cinema chess_capture_53: done", function() MM9Cinematic.finish("chess_capture_53") end)
MM9Cinematic.play["chess_capture_53"] = function()
    if evt.GetMapVar("Cinema.chess_capture_53.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_53.started", 1)
        evt.PlayCinematic("chess_capture_53", 36122)
    end
end

-- Cinematic chess_capture_57 (ChessCamera.scr :ViewChessPiece: square 57, ChessPiece5 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_57"] = {
}
RegisterEvent(36123, "Cinema chess_capture_57: done", function() MM9Cinematic.finish("chess_capture_57") end)
MM9Cinematic.play["chess_capture_57"] = function()
    if evt.GetMapVar("Cinema.chess_capture_57.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_57.started", 1)
        evt.PlayCinematic("chess_capture_57", 36123)
    end
end

-- Cinematic chess_capture_58 (ChessCamera.scr :ViewChessPiece: square 58, ChessPiece1 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_58"] = {
}
RegisterEvent(36124, "Cinema chess_capture_58: done", function() MM9Cinematic.finish("chess_capture_58") end)
MM9Cinematic.play["chess_capture_58"] = function()
    if evt.GetMapVar("Cinema.chess_capture_58.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_58.started", 1)
        evt.PlayCinematic("chess_capture_58", 36124)
    end
end

-- Cinematic chess_capture_60 (ChessCamera.scr :ViewChessPiece: square 60, ChessPiece1 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_60"] = {
}
RegisterEvent(36125, "Cinema chess_capture_60: done", function() MM9Cinematic.finish("chess_capture_60") end)
MM9Cinematic.play["chess_capture_60"] = function()
    if evt.GetMapVar("Cinema.chess_capture_60.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_60.started", 1)
        evt.PlayCinematic("chess_capture_60", 36125)
    end
end

-- Cinematic chess_capture_62 (ChessCamera.scr :ViewChessPiece: square 62, ChessPiece4 attacks): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["chess_capture_62"] = {
}
RegisterEvent(36126, "Cinema chess_capture_62: done", function() MM9Cinematic.finish("chess_capture_62") end)
MM9Cinematic.play["chess_capture_62"] = function()
    if evt.GetMapVar("Cinema.chess_capture_62.started", 0) == 0 then
        evt.SetMapVar("Cinema.chess_capture_62.started", 1)
        evt.PlayCinematic("chess_capture_62", 36126)
    end
end

-- ChessBase.inc :StartCamera (the poll calls this when a piece attacks the party's square): the square's cinematic,
-- once per square (MM9 plays it on every attack: its pieces move, ours stand).
local CHESS_CAPTURE_SQUARES = {2, 4, 5, 8, 9, 12, 13, 15, 17, 19, 25, 29, 31, 33, 34, 35, 36, 40, 42, 43, 44, 50, 53, 57, 58, 60, 62}
function MM9Cinematic.chessCapture(c)
    for i, entry in ipairs(CHESS) do
        if entry == c then MM9Cinematic.start("chess_capture_" .. CHESS_CAPTURE_SQUARES[i]) return end
    end
end
