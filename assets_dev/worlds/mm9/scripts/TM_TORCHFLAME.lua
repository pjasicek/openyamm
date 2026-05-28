-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TM_TORCHFLAME.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "Globals.inc" }

-- TM_FallingTorch.scr
-- kd
-- 10-30-01
-- Makes the flame fall to the ground.
-- Then starts the barrel exploding sequence.
script.labels["TurnMeOff"] = function(ctx)
    -- TM_TORCHFLAME.scr:21
    ctx:command("getobjecthandle", "FallingWallTorch0, hDummy") -- TM_TORCHFLAME.scr:24
    ctx:command("removeobject", "hDummy") -- TM_TORCHFLAME.scr:25
    ctx:command("getmyhandle", "hFire") -- TM_TORCHFLAME.scr:26
    ctx:trigger("hFire", "Off") -- TM_TORCHFLAME.scr:27
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:28
end

script.labels["Barrel8"] = function(ctx)
    -- TM_TORCHFLAME.scr:30
    ctx:command("hblocker", "= NULL") -- TM_TORCHFLAME.scr:32
    ctx:trigger("hFire", "Off") -- TM_TORCHFLAME.scr:33
    ctx:command("hfire", "= NULL") -- TM_TORCHFLAME.scr:34
    ctx:command("getobjecthandle", "DustObject14, hFire") -- TM_TORCHFLAME.scr:35
    ctx:trigger("hFire", "On") -- TM_TORCHFLAME.scr:36
    ctx:command("playsound", "Sounds\\Weapons\\EQHammerImpact.wav DoNothing 500 2000 FALSE 100") -- TM_TORCHFLAME.scr:37
    ctx:command("playsound", "Sounds\\Events\\crate_smash.wav DoNothing 500 2000 FALSE 100") -- TM_TORCHFLAME.scr:38
    ctx:command("getobjecthandle", "DB_Barrel8, hBlocker") -- TM_TORCHFLAME.scr:39
    ctx:trigger("hBlocker", "Destroy") -- TM_TORCHFLAME.scr:40
    ctx:command("wait", "0, .1, TurnMeOff") -- TM_TORCHFLAME.scr:41
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:42
end

script.labels["Barrel7"] = function(ctx)
    -- TM_TORCHFLAME.scr:44
    ctx:command("hblocker", "= NULL") -- TM_TORCHFLAME.scr:46
    ctx:trigger("hFire", "Off") -- TM_TORCHFLAME.scr:47
    ctx:command("hfire", "= NULL") -- TM_TORCHFLAME.scr:48
    ctx:command("getobjecthandle", "DustObject13, hFire") -- TM_TORCHFLAME.scr:49
    ctx:trigger("hFire", "On") -- TM_TORCHFLAME.scr:50
    ctx:command("playsound", "Sounds\\Weapons\\EQHammerImpact.wav DoNothing 500 2000 FALSE 100") -- TM_TORCHFLAME.scr:51
    ctx:command("playsound", "Sounds\\Events\\crate_smash.wav DoNothing 500 2000 FALSE 100") -- TM_TORCHFLAME.scr:52
    ctx:command("getobjecthandle", "DB_Barrel7, hBlocker") -- TM_TORCHFLAME.scr:53
    ctx:trigger("hBlocker", "Destroy") -- TM_TORCHFLAME.scr:54
    ctx:command("wait", "0, .1, Barrel8") -- TM_TORCHFLAME.scr:55
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:56
end

script.labels["Barrel6"] = function(ctx)
    -- TM_TORCHFLAME.scr:58
    ctx:command("hblocker", "= NULL") -- TM_TORCHFLAME.scr:60
    ctx:trigger("hFire", "Off") -- TM_TORCHFLAME.scr:61
    ctx:command("hfire", "= NULL") -- TM_TORCHFLAME.scr:62
    ctx:command("getobjecthandle", "DustObject12, hFire") -- TM_TORCHFLAME.scr:63
    ctx:trigger("hFire", "On") -- TM_TORCHFLAME.scr:64
    ctx:command("playsound", "Sounds\\Weapons\\EQHammerImpact.wav DoNothing 500 2000 FALSE 100") -- TM_TORCHFLAME.scr:65
    ctx:command("playsound", "Sounds\\Events\\crate_smash.wav DoNothing 500 2000 FALSE 100") -- TM_TORCHFLAME.scr:66
    ctx:command("getobjecthandle", "DB_Barrel6, hBlocker") -- TM_TORCHFLAME.scr:67
    ctx:trigger("hBlocker", "Destroy") -- TM_TORCHFLAME.scr:68
    ctx:command("wait", "0, .2, Barrel7") -- TM_TORCHFLAME.scr:69
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:70
end

script.labels["Barrel5"] = function(ctx)
    -- TM_TORCHFLAME.scr:72
    ctx:command("hblocker", "= NULL") -- TM_TORCHFLAME.scr:74
    ctx:trigger("hFire", "Off") -- TM_TORCHFLAME.scr:75
    ctx:command("hfire", "= NULL") -- TM_TORCHFLAME.scr:76
    ctx:command("getobjecthandle", "DustObject11, hFire") -- TM_TORCHFLAME.scr:77
    ctx:trigger("hFire", "On") -- TM_TORCHFLAME.scr:78
    ctx:command("playsound", "Sounds\\Weapons\\EQHammerImpact.wav DoNothing 500 2000 FALSE 100") -- TM_TORCHFLAME.scr:79
    ctx:command("playsound", "Sounds\\Events\\crate_smash.wav DoNothing 500 2000 FALSE 100") -- TM_TORCHFLAME.scr:80
    ctx:command("getobjecthandle", "DB_Barrel5, hBlocker") -- TM_TORCHFLAME.scr:81
    ctx:trigger("hBlocker", "Destroy") -- TM_TORCHFLAME.scr:82
    ctx:command("wait", "0, .2, Barrel6") -- TM_TORCHFLAME.scr:83
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:84
end

script.labels["Barrel4"] = function(ctx)
    -- TM_TORCHFLAME.scr:86
    ctx:command("hblocker", "= NULL") -- TM_TORCHFLAME.scr:88
    ctx:trigger("hFire", "Off") -- TM_TORCHFLAME.scr:89
    ctx:command("hfire", "= NULL") -- TM_TORCHFLAME.scr:90
    ctx:command("getobjecthandle", "DustObject10, hFire") -- TM_TORCHFLAME.scr:91
    ctx:trigger("hFire", "On") -- TM_TORCHFLAME.scr:92
    ctx:command("playsound", "Sounds\\Weapons\\EQHammerImpact.wav DoNothing 500 2000 FALSE 100") -- TM_TORCHFLAME.scr:93
    ctx:command("playsound", "Sounds\\Events\\crate_smash.wav DoNothing 500 2000 FALSE 100") -- TM_TORCHFLAME.scr:94
    ctx:command("getobjecthandle", "DB_Barrel4, hBlocker") -- TM_TORCHFLAME.scr:95
    ctx:trigger("hBlocker", "Destroy") -- TM_TORCHFLAME.scr:96
    ctx:command("wait", "0, .3, Barrel5") -- TM_TORCHFLAME.scr:97
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:98
end

script.labels["Barrel3"] = function(ctx)
    -- TM_TORCHFLAME.scr:100
    ctx:command("hblocker", "= NULL") -- TM_TORCHFLAME.scr:102
    ctx:trigger("hFire", "Off") -- TM_TORCHFLAME.scr:103
    ctx:command("hfire", "= NULL") -- TM_TORCHFLAME.scr:104
    ctx:command("getobjecthandle", "DustObject9, hFire") -- TM_TORCHFLAME.scr:105
    ctx:trigger("hFire", "On") -- TM_TORCHFLAME.scr:106
    ctx:command("playsound", "Sounds\\Weapons\\EQHammerImpact.wav DoNothing 500 2000 FALSE 100") -- TM_TORCHFLAME.scr:107
    ctx:command("playsound", "Sounds\\Events\\crate_smash.wav DoNothing 500 2000 FALSE 100") -- TM_TORCHFLAME.scr:108
    ctx:command("getobjecthandle", "DB_Barrel3, hBlocker") -- TM_TORCHFLAME.scr:109
    ctx:trigger("hBlocker", "Destroy") -- TM_TORCHFLAME.scr:110
    ctx:command("wait", "0, .4, Barrel4") -- TM_TORCHFLAME.scr:111
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:112
end

script.labels["Barrel2"] = function(ctx)
    -- TM_TORCHFLAME.scr:114
    ctx:command("hblocker", "= NULL") -- TM_TORCHFLAME.scr:116
    ctx:trigger("hFire", "Off") -- TM_TORCHFLAME.scr:117
    ctx:command("hfire", "= NULL") -- TM_TORCHFLAME.scr:118
    ctx:command("getobjecthandle", "DustObject8, hFire") -- TM_TORCHFLAME.scr:119
    ctx:trigger("hFire", "On") -- TM_TORCHFLAME.scr:120
    ctx:command("playsound", "Sounds\\Weapons\\EQHammerImpact.wav DoNothing 500 2000 FALSE 100") -- TM_TORCHFLAME.scr:121
    ctx:command("playsound", "Sounds\\Events\\crate_smash.wav DoNothing 500 2000 FALSE 100") -- TM_TORCHFLAME.scr:122
    ctx:command("getobjecthandle", "DB_Barrel2, hBlocker") -- TM_TORCHFLAME.scr:123
    ctx:trigger("hBlocker", "Destroy") -- TM_TORCHFLAME.scr:124
    ctx:command("wait", "0, .5, Barrel3") -- TM_TORCHFLAME.scr:125
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:126
end

script.labels["Barrel1"] = function(ctx)
    -- TM_TORCHFLAME.scr:128
    ctx:command("hblocker", "= NULL") -- TM_TORCHFLAME.scr:130
    ctx:trigger("hFire", "Off") -- TM_TORCHFLAME.scr:131
    ctx:command("hfire", "= NULL") -- TM_TORCHFLAME.scr:132
    ctx:command("getobjecthandle", "DustObject7, hFire") -- TM_TORCHFLAME.scr:133
    ctx:trigger("hFire", "On") -- TM_TORCHFLAME.scr:134
    ctx:command("playsound", "Sounds\\Weapons\\EQHammerImpact.wav DoNothing 500 2000 FALSE 100") -- TM_TORCHFLAME.scr:135
    ctx:command("playsound", "Sounds\\Events\\crate_smash.wav DoNothing 500 2000 FALSE 100") -- TM_TORCHFLAME.scr:136
    ctx:command("getobjecthandle", "DB_Barrel1, hBlocker") -- TM_TORCHFLAME.scr:137
    ctx:trigger("hBlocker", "Destroy") -- TM_TORCHFLAME.scr:138
    ctx:command("wait", "0, .5, Barrel2") -- TM_TORCHFLAME.scr:139
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:140
end

script.labels["StartSequence"] = function(ctx)
    -- TM_TORCHFLAME.scr:142
    ctx:command("hblocker", "= NULL") -- TM_TORCHFLAME.scr:144
    ctx:command("getobjecthandle", "DustObject6, hFire") -- TM_TORCHFLAME.scr:145
    ctx:trigger("hFire", "On") -- TM_TORCHFLAME.scr:146
    ctx:command("getobjecthandle", "DB_Barrel0, hBlocker") -- TM_TORCHFLAME.scr:147
    ctx:command("playsound", "Sounds\\Events\\steam_burst04.wav DoNothing 500 2000 FALSE 100") -- TM_TORCHFLAME.scr:148
    ctx:command("playsound", "Sounds\\Weapons\\EQHammerImpact.wav DoNothing 500 2000 FALSE 100") -- TM_TORCHFLAME.scr:149
    ctx:command("playsound", "Sounds\\Events\\crate_smash.wav DoNothing 500 2000 FALSE 100") -- TM_TORCHFLAME.scr:150
    ctx:trigger("hBlocker", "Destroy") -- TM_TORCHFLAME.scr:151
    ctx:command("wait", "0, 1, Barrel1") -- TM_TORCHFLAME.scr:152
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:153
end

script.labels["StopHere"] = function(ctx)
    -- TM_TORCHFLAME.scr:155
    ctx:command("playsound", "Sounds\\Events\\steam_burst04.wav DoNothing 100 2000 FALSE 100") -- TM_TORCHFLAME.scr:157
    ctx:command("wait", "0, 3, StartSequence") -- TM_TORCHFLAME.scr:158
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:159
end

script.labels["MoveToMarker"] = function(ctx)
    -- TM_TORCHFLAME.scr:161
    ctx:command("movetopos", "nVarX, nVarY, nVarZ, 250, StopHere") -- TM_TORCHFLAME.scr:163
    do return ctx:exit("") end -- TM_TORCHFLAME.scr:164
end

script.labels["Main2"] = function(ctx)
    -- TM_TORCHFLAME.scr:166
    ctx:command("getobjecthandle", "FallingTorchMarker0, hFTMarker") -- TM_TORCHFLAME.scr:168
    ctx:command("getpos", "hFTMarker, nVarX, nVarY, nVarZ") -- TM_TORCHFLAME.scr:169
    ctx:addTrigger("Fall", "MoveToMarker") -- TM_TORCHFLAME.scr:170
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:171
end

script.labels["Main"] = function(ctx)
    -- TM_TORCHFLAME.scr:173
    ctx:command("wait", "0 .1 main2") -- TM_TORCHFLAME.scr:175
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:176
end

return script
