-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TRISLAN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- givetake.scr
-- 10/4
-- timmy
-- gives party specific item
-- Parameters
-- P0 Item number of item to give
script.labels["OnWalk1"] = function(ctx)
    -- TRISLAN.scr:27
    ctx:setPropNumber("DoRude", "False") -- TRISLAN.scr:29
    ctx:command("getobjecthandle", "abriel g_hobject") -- TRISLAN.scr:30
    ctx:command("target", "g_hobject") -- TRISLAN.scr:31
    ctx:command("getobjecthandle", "Trislan1 g_hobject") -- TRISLAN.scr:33
    ctx:command("walkto", "g_hobject 1 Speak1") -- TRISLAN.scr:34
    do return ctx:exit("") end -- TRISLAN.scr:35
end

script.labels["Speak1"] = function(ctx)
    -- TRISLAN.scr:39
    ctx:command("wait", "1 4, OnSpeak1") -- TRISLAN.scr:42
    do return ctx:exit("") end -- TRISLAN.scr:43
end

script.labels["OnSpeak1"] = function(ctx)
    -- TRISLAN.scr:46
    ctx:command("getobjecthandle", "narrator g_hobject") -- TRISLAN.scr:49
    ctx:trigger("g_hobject", "stop") -- TRISLAN.scr:50
    ctx:command("loopanim", "conv1 0 DoNothing") -- TRISLAN.scr:51
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\03.wav, DoNothing, 100, 512, FALSE, 100") -- TRISLAN.scr:52
    ctx:command("wait", "1 6 Trigger4") -- TRISLAN.scr:53
    do return ctx:exit("") end -- TRISLAN.scr:54
end

script.labels["Trigger4"] = function(ctx)
    -- TRISLAN.scr:57
    ctx:command("stop", "") -- TRISLAN.scr:60
    ctx:command("loopanim", "stand 0 DoNothing") -- TRISLAN.scr:61
    ctx:command("getobjecthandle", "abriel g_hobject") -- TRISLAN.scr:62
    ctx:trigger("g_hobject", "Speak4") -- TRISLAN.scr:63
    do return ctx:exit("") end -- TRISLAN.scr:64
end

script.labels["OnSpeak5"] = function(ctx)
    -- TRISLAN.scr:67
    ctx:command("loopanim", "conv3 0 DoNothing") -- TRISLAN.scr:70
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\05.wav, DoNothing, 100, 512, FALSE, 100") -- TRISLAN.scr:71
    ctx:command("wait", "1 4 Trigger6") -- TRISLAN.scr:72
    do return ctx:exit("") end -- TRISLAN.scr:73
end

script.labels["Trigger6"] = function(ctx)
    -- TRISLAN.scr:76
    ctx:command("stop", "") -- TRISLAN.scr:79
    ctx:command("loopanim", "stand 0 DoNothing") -- TRISLAN.scr:80
    ctx:command("getobjecthandle", "abriel g_hobject") -- TRISLAN.scr:81
    ctx:trigger("g_hobject", "Speak6") -- TRISLAN.scr:82
    do return ctx:exit("") end -- TRISLAN.scr:83
end

script.labels["OnSpeak7"] = function(ctx)
    -- TRISLAN.scr:86
    ctx:command("loopanim", "conv3 0 DoNothing") -- TRISLAN.scr:89
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\07.wav, DoNothing, 100, 512, FALSE, 100") -- TRISLAN.scr:90
    ctx:command("wait", "1 3 Trigger8") -- TRISLAN.scr:91
    do return ctx:exit("") end -- TRISLAN.scr:92
end

script.labels["Trigger8"] = function(ctx)
    -- TRISLAN.scr:95
    ctx:command("stop", "") -- TRISLAN.scr:98
    ctx:command("loopanim", "stand 0 DoNothing") -- TRISLAN.scr:99
    ctx:command("getobjecthandle", "abriel g_hobject") -- TRISLAN.scr:100
    ctx:trigger("g_hobject", "Speak8") -- TRISLAN.scr:101
    do return ctx:exit("") end -- TRISLAN.scr:102
end

script.labels["OnExit"] = function(ctx)
    -- TRISLAN.scr:106
    ctx:setPropNumber("DoRude", "TRUE") -- TRISLAN.scr:108
    ctx:command("target", "NULL") -- TRISLAN.scr:109
    ctx:command("getobjecthandle", "Trislan2 g_hobject") -- TRISLAN.scr:110
    ctx:command("walkto", "g_hobject 1 FaceStage") -- TRISLAN.scr:111
    do return ctx:exit("") end -- TRISLAN.scr:112
end

script.labels["FaceStage"] = function(ctx)
    -- TRISLAN.scr:115
    ctx:command("getobjecthandle", "Wilam g_hobject") -- TRISLAN.scr:118
    ctx:command("target", "g_hobject") -- TRISLAN.scr:119
    do return ctx:exit("") end -- TRISLAN.scr:120
end

script.labels["OnWalk2"] = function(ctx)
    -- TRISLAN.scr:123
    ctx:command("getobjecthandle", "Ralof g_hobject") -- TRISLAN.scr:126
    ctx:command("target", "g_hobject") -- TRISLAN.scr:127
    ctx:command("getobjecthandle", "Trislan1 g_hobject") -- TRISLAN.scr:128
    ctx:command("walkto", "g_hobject 1 DoNothing") -- TRISLAN.scr:129
    do return ctx:exit("") end -- TRISLAN.scr:130
end

script.labels["OnSpeak23"] = function(ctx)
    -- TRISLAN.scr:133
    ctx:command("loopanim", "conv2 0 DoNothing") -- TRISLAN.scr:136
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\23.wav, DoNothing, 100, 512, FALSE, 100") -- TRISLAN.scr:137
    ctx:command("wait", "1 3.4 Trigger24") -- TRISLAN.scr:138
    do return ctx:exit("") end -- TRISLAN.scr:139
end

script.labels["Trigger24"] = function(ctx)
    -- TRISLAN.scr:142
    ctx:command("stop", "") -- TRISLAN.scr:145
    ctx:command("loopanim", "stand 0 DoNothing") -- TRISLAN.scr:146
    ctx:command("getobjecthandle", "Ralof g_hobject") -- TRISLAN.scr:147
    ctx:trigger("g_hobject", "Speak24") -- TRISLAN.scr:148
    do return ctx:exit("") end -- TRISLAN.scr:149
end

script.labels["OnSpeak25"] = function(ctx)
    -- TRISLAN.scr:152
    ctx:command("loopanim", "conv2 0 DoNothing") -- TRISLAN.scr:155
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\25.wav, DoNothing, 100, 512, FALSE, 100") -- TRISLAN.scr:156
    ctx:command("wait", "1 4.5 Trigger26") -- TRISLAN.scr:157
    do return ctx:exit("") end -- TRISLAN.scr:158
end

script.labels["Trigger26"] = function(ctx)
    -- TRISLAN.scr:161
    ctx:command("stop", "") -- TRISLAN.scr:164
    ctx:command("loopanim", "stand 0 DoNothing") -- TRISLAN.scr:165
    ctx:command("getobjecthandle", "Ralof g_hobject") -- TRISLAN.scr:166
    ctx:trigger("g_hobject", "Speak26") -- TRISLAN.scr:167
    do return ctx:exit("") end -- TRISLAN.scr:168
end

script.labels["OnDie"] = function(ctx)
    -- TRISLAN.scr:171
    -- Playanim Die1 DoNothing
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\27a.wav, DoNothing, 100, 512, FALSE, 100") -- TRISLAN.scr:176
    ctx:command("wait", "1 4 Trigger27") -- TRISLAN.scr:177
    ctx:command("playanim", "Play_Death GetUp") -- TRISLAN.scr:178
    do return ctx:exit("") end -- TRISLAN.scr:179
end

script.labels["GetUp"] = function(ctx)
    -- TRISLAN.scr:182
    ctx:command("playanim", "Play_getup DoNothing") -- TRISLAN.scr:185
    do return ctx:exit("") end -- TRISLAN.scr:186
end

script.labels["Stop"] = function(ctx)
    -- TRISLAN.scr:189
    ctx:command("stop", "") -- TRISLAN.scr:192
    do return ctx:exit("") end -- TRISLAN.scr:193
end

script.labels["Trigger27"] = function(ctx)
    -- TRISLAN.scr:195
    -- stop
    -- Loopanim stand 0 DoNothing
    ctx:command("getobjecthandle", "Narrator g_hobject") -- TRISLAN.scr:200
    ctx:trigger("g_hobject", "Speak27") -- TRISLAN.scr:201
    do return ctx:exit("") end -- TRISLAN.scr:202
end

script.labels["OnCastCall"] = function(ctx)
    -- TRISLAN.scr:205
    ctx:command("getobjecthandle", "Trislan3 g_hobject") -- TRISLAN.scr:210
    ctx:command("walkto", "g_hobject 1 FaceDoor") -- TRISLAN.scr:211
    do return ctx:exit("") end -- TRISLAN.scr:212
end

script.labels["FaceDoor"] = function(ctx)
    -- TRISLAN.scr:215
    ctx:command("getobjecthandle", "peasant2 g_hobject") -- TRISLAN.scr:218
    ctx:command("target", "g_hobject") -- TRISLAN.scr:219
    do return ctx:exit("") end -- TRISLAN.scr:220
end

script.labels["OnBow"] = function(ctx)
    -- TRISLAN.scr:223
    ctx:command("playanim", "Bow DoNothing") -- TRISLAN.scr:226
    do return ctx:exit("") end -- TRISLAN.scr:227
end

script.labels["Main"] = function(ctx)
    -- TRISLAN.scr:230
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Walk1", "OnWalk1") -- TRISLAN.scr:235
    ctx:addTrigger("Speak5", "OnSpeak5") -- TRISLAN.scr:236
    ctx:addTrigger("Speak7", "OnSpeak7") -- TRISLAN.scr:237
    ctx:addTrigger("Walk2", "OnWalk2") -- TRISLAN.scr:238
    ctx:addTrigger("exit", "Onexit") -- TRISLAN.scr:239
    ctx:addTrigger("Speak23", "OnSpeak23") -- TRISLAN.scr:240
    ctx:addTrigger("Speak25", "OnSpeak25") -- TRISLAN.scr:241
    ctx:addTrigger("Die", "OnDie") -- TRISLAN.scr:242
    ctx:addTrigger("CastCall", "OnCastCall") -- TRISLAN.scr:243
    ctx:addTrigger("Bow", "OnBow") -- TRISLAN.scr:244
    do return ctx:exit("") end -- TRISLAN.scr:245
end

return script
