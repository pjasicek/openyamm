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
    ctx:state().hDummy = ctx:objectOrNil("FallingWallTorch0") -- TM_TORCHFLAME.scr:24
    ctx:object("hDummy"):remove() -- TM_TORCHFLAME.scr:25
    ctx:state().hFire = ctx:self() -- TM_TORCHFLAME.scr:26
    ctx:trigger("hFire", "Off") -- TM_TORCHFLAME.scr:27
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:28
end

script.labels["Barrel8"] = function(ctx)
    -- TM_TORCHFLAME.scr:30
    ctx:state().hBlocker = nil -- TM_TORCHFLAME.scr:32
    ctx:trigger("hFire", "Off") -- TM_TORCHFLAME.scr:33
    ctx:state().hFire = nil -- TM_TORCHFLAME.scr:34
    ctx:object("DustObject14"):trigger("On") -- TM_TORCHFLAME.scr:35-36
    ctx:playSound("Sounds\\Weapons\\EQHammerImpact.wav", "DoNothing", 500, 2000, "FALSE", 100) -- TM_TORCHFLAME.scr:37
    ctx:playSound("Sounds\\Events\\crate_smash.wav", "DoNothing", 500, 2000, "FALSE", 100) -- TM_TORCHFLAME.scr:38
    ctx:object("DB_Barrel8"):trigger("Destroy") -- TM_TORCHFLAME.scr:39-40
    ctx:wait(0, .1, "TurnMeOff") -- TM_TORCHFLAME.scr:41
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:42
end

script.labels["Barrel7"] = function(ctx)
    -- TM_TORCHFLAME.scr:44
    ctx:state().hBlocker = nil -- TM_TORCHFLAME.scr:46
    ctx:trigger("hFire", "Off") -- TM_TORCHFLAME.scr:47
    ctx:state().hFire = nil -- TM_TORCHFLAME.scr:48
    ctx:object("DustObject13"):trigger("On") -- TM_TORCHFLAME.scr:49-50
    ctx:playSound("Sounds\\Weapons\\EQHammerImpact.wav", "DoNothing", 500, 2000, "FALSE", 100) -- TM_TORCHFLAME.scr:51
    ctx:playSound("Sounds\\Events\\crate_smash.wav", "DoNothing", 500, 2000, "FALSE", 100) -- TM_TORCHFLAME.scr:52
    ctx:object("DB_Barrel7"):trigger("Destroy") -- TM_TORCHFLAME.scr:53-54
    ctx:wait(0, .1, "Barrel8") -- TM_TORCHFLAME.scr:55
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:56
end

script.labels["Barrel6"] = function(ctx)
    -- TM_TORCHFLAME.scr:58
    ctx:state().hBlocker = nil -- TM_TORCHFLAME.scr:60
    ctx:trigger("hFire", "Off") -- TM_TORCHFLAME.scr:61
    ctx:state().hFire = nil -- TM_TORCHFLAME.scr:62
    ctx:object("DustObject12"):trigger("On") -- TM_TORCHFLAME.scr:63-64
    ctx:playSound("Sounds\\Weapons\\EQHammerImpact.wav", "DoNothing", 500, 2000, "FALSE", 100) -- TM_TORCHFLAME.scr:65
    ctx:playSound("Sounds\\Events\\crate_smash.wav", "DoNothing", 500, 2000, "FALSE", 100) -- TM_TORCHFLAME.scr:66
    ctx:object("DB_Barrel6"):trigger("Destroy") -- TM_TORCHFLAME.scr:67-68
    ctx:wait(0, .2, "Barrel7") -- TM_TORCHFLAME.scr:69
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:70
end

script.labels["Barrel5"] = function(ctx)
    -- TM_TORCHFLAME.scr:72
    ctx:state().hBlocker = nil -- TM_TORCHFLAME.scr:74
    ctx:trigger("hFire", "Off") -- TM_TORCHFLAME.scr:75
    ctx:state().hFire = nil -- TM_TORCHFLAME.scr:76
    ctx:object("DustObject11"):trigger("On") -- TM_TORCHFLAME.scr:77-78
    ctx:playSound("Sounds\\Weapons\\EQHammerImpact.wav", "DoNothing", 500, 2000, "FALSE", 100) -- TM_TORCHFLAME.scr:79
    ctx:playSound("Sounds\\Events\\crate_smash.wav", "DoNothing", 500, 2000, "FALSE", 100) -- TM_TORCHFLAME.scr:80
    ctx:object("DB_Barrel5"):trigger("Destroy") -- TM_TORCHFLAME.scr:81-82
    ctx:wait(0, .2, "Barrel6") -- TM_TORCHFLAME.scr:83
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:84
end

script.labels["Barrel4"] = function(ctx)
    -- TM_TORCHFLAME.scr:86
    ctx:state().hBlocker = nil -- TM_TORCHFLAME.scr:88
    ctx:trigger("hFire", "Off") -- TM_TORCHFLAME.scr:89
    ctx:state().hFire = nil -- TM_TORCHFLAME.scr:90
    ctx:object("DustObject10"):trigger("On") -- TM_TORCHFLAME.scr:91-92
    ctx:playSound("Sounds\\Weapons\\EQHammerImpact.wav", "DoNothing", 500, 2000, "FALSE", 100) -- TM_TORCHFLAME.scr:93
    ctx:playSound("Sounds\\Events\\crate_smash.wav", "DoNothing", 500, 2000, "FALSE", 100) -- TM_TORCHFLAME.scr:94
    ctx:object("DB_Barrel4"):trigger("Destroy") -- TM_TORCHFLAME.scr:95-96
    ctx:wait(0, .3, "Barrel5") -- TM_TORCHFLAME.scr:97
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:98
end

script.labels["Barrel3"] = function(ctx)
    -- TM_TORCHFLAME.scr:100
    ctx:state().hBlocker = nil -- TM_TORCHFLAME.scr:102
    ctx:trigger("hFire", "Off") -- TM_TORCHFLAME.scr:103
    ctx:state().hFire = nil -- TM_TORCHFLAME.scr:104
    ctx:object("DustObject9"):trigger("On") -- TM_TORCHFLAME.scr:105-106
    ctx:playSound("Sounds\\Weapons\\EQHammerImpact.wav", "DoNothing", 500, 2000, "FALSE", 100) -- TM_TORCHFLAME.scr:107
    ctx:playSound("Sounds\\Events\\crate_smash.wav", "DoNothing", 500, 2000, "FALSE", 100) -- TM_TORCHFLAME.scr:108
    ctx:object("DB_Barrel3"):trigger("Destroy") -- TM_TORCHFLAME.scr:109-110
    ctx:wait(0, .4, "Barrel4") -- TM_TORCHFLAME.scr:111
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:112
end

script.labels["Barrel2"] = function(ctx)
    -- TM_TORCHFLAME.scr:114
    ctx:state().hBlocker = nil -- TM_TORCHFLAME.scr:116
    ctx:trigger("hFire", "Off") -- TM_TORCHFLAME.scr:117
    ctx:state().hFire = nil -- TM_TORCHFLAME.scr:118
    ctx:object("DustObject8"):trigger("On") -- TM_TORCHFLAME.scr:119-120
    ctx:playSound("Sounds\\Weapons\\EQHammerImpact.wav", "DoNothing", 500, 2000, "FALSE", 100) -- TM_TORCHFLAME.scr:121
    ctx:playSound("Sounds\\Events\\crate_smash.wav", "DoNothing", 500, 2000, "FALSE", 100) -- TM_TORCHFLAME.scr:122
    ctx:object("DB_Barrel2"):trigger("Destroy") -- TM_TORCHFLAME.scr:123-124
    ctx:wait(0, .5, "Barrel3") -- TM_TORCHFLAME.scr:125
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:126
end

script.labels["Barrel1"] = function(ctx)
    -- TM_TORCHFLAME.scr:128
    ctx:state().hBlocker = nil -- TM_TORCHFLAME.scr:130
    ctx:trigger("hFire", "Off") -- TM_TORCHFLAME.scr:131
    ctx:state().hFire = nil -- TM_TORCHFLAME.scr:132
    ctx:object("DustObject7"):trigger("On") -- TM_TORCHFLAME.scr:133-134
    ctx:playSound("Sounds\\Weapons\\EQHammerImpact.wav", "DoNothing", 500, 2000, "FALSE", 100) -- TM_TORCHFLAME.scr:135
    ctx:playSound("Sounds\\Events\\crate_smash.wav", "DoNothing", 500, 2000, "FALSE", 100) -- TM_TORCHFLAME.scr:136
    ctx:object("DB_Barrel1"):trigger("Destroy") -- TM_TORCHFLAME.scr:137-138
    ctx:wait(0, .5, "Barrel2") -- TM_TORCHFLAME.scr:139
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:140
end

script.labels["StartSequence"] = function(ctx)
    -- TM_TORCHFLAME.scr:142
    ctx:state().hBlocker = nil -- TM_TORCHFLAME.scr:144
    ctx:object("DustObject6"):trigger("On") -- TM_TORCHFLAME.scr:145-146
    ctx:state().hBlocker = ctx:objectOrNil("DB_Barrel0") -- TM_TORCHFLAME.scr:147
    ctx:playSound("Sounds\\Events\\steam_burst04.wav", "DoNothing", 500, 2000, "FALSE", 100) -- TM_TORCHFLAME.scr:148
    ctx:playSound("Sounds\\Weapons\\EQHammerImpact.wav", "DoNothing", 500, 2000, "FALSE", 100) -- TM_TORCHFLAME.scr:149
    ctx:playSound("Sounds\\Events\\crate_smash.wav", "DoNothing", 500, 2000, "FALSE", 100) -- TM_TORCHFLAME.scr:150
    ctx:trigger("hBlocker", "Destroy") -- TM_TORCHFLAME.scr:151
    ctx:wait(0, 1, "Barrel1") -- TM_TORCHFLAME.scr:152
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:153
end

script.labels["StopHere"] = function(ctx)
    -- TM_TORCHFLAME.scr:155
    ctx:playSound("Sounds\\Events\\steam_burst04.wav", "DoNothing", 100, 2000, "FALSE", 100) -- TM_TORCHFLAME.scr:157
    ctx:wait(0, 3, "StartSequence") -- TM_TORCHFLAME.scr:158
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:159
end

script.labels["MoveToMarker"] = function(ctx)
    -- TM_TORCHFLAME.scr:161
    ctx:self():moveToPos("nVarX", "nVarY", "nVarZ", 250, "StopHere") -- TM_TORCHFLAME.scr:163
    do return ctx:exit("") end -- TM_TORCHFLAME.scr:164
end

script.labels["Main2"] = function(ctx)
    -- TM_TORCHFLAME.scr:166
    ctx:state().nVarX, ctx:state().nVarY, ctx:state().nVarZ = ctx:object("FallingTorchMarker0"):pos() -- TM_TORCHFLAME.scr:168-169
    ctx:addTrigger("Fall", "MoveToMarker") -- TM_TORCHFLAME.scr:170
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:171
end

script.labels["Main"] = function(ctx)
    -- TM_TORCHFLAME.scr:173
    ctx:wait(0, .1, "main2") -- TM_TORCHFLAME.scr:175
    do return ctx:exit("TRUE") end -- TM_TORCHFLAME.scr:176
end

return script
