-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ABRIEL.scr"
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
    -- ABRIEL.scr:28
    ctx:setPropNumber("DoRude", "False") -- ABRIEL.scr:30
    ctx:command("getobjecthandle", "trislan g_hobject") -- ABRIEL.scr:31
    ctx:command("target", "g_hobject") -- ABRIEL.scr:32
    ctx:command("getobjecthandle", "Abriel1 g_hobject") -- ABRIEL.scr:34
    ctx:command("walkto", "g_hobject 1 DoNothing") -- ABRIEL.scr:35
    do return ctx:exit("") end -- ABRIEL.scr:36
end

script.labels["OnSpeak4"] = function(ctx)
    -- ABRIEL.scr:39
    ctx:command("loopanim", "conv2 0 DoNothing") -- ABRIEL.scr:42
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\04.wav, DoNothing, 100, 512, FALSE, 100") -- ABRIEL.scr:43
    ctx:command("wait", "1 13 Trigger5") -- ABRIEL.scr:44
    do return ctx:exit("") end -- ABRIEL.scr:45
end

script.labels["Trigger5"] = function(ctx)
    -- ABRIEL.scr:49
    ctx:command("stop", "") -- ABRIEL.scr:52
    ctx:command("loopanim", "stand 0 DoNothing") -- ABRIEL.scr:53
    ctx:command("getobjecthandle", "trislan g_hobject") -- ABRIEL.scr:54
    ctx:trigger("g_hobject", "Speak5") -- ABRIEL.scr:55
    do return ctx:exit("") end -- ABRIEL.scr:56
end

script.labels["OnSpeak6"] = function(ctx)
    -- ABRIEL.scr:59
    ctx:command("loopanim", "conv2 0 DoNothing") -- ABRIEL.scr:62
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\06.wav, DoNothing, 100, 512, FALSE, 100") -- ABRIEL.scr:63
    ctx:command("wait", "1 9.85 Trigger7") -- ABRIEL.scr:64
    do return ctx:exit("") end -- ABRIEL.scr:65
end

script.labels["Trigger7"] = function(ctx)
    -- ABRIEL.scr:68
    ctx:command("stop", "") -- ABRIEL.scr:71
    ctx:command("loopanim", "stand 0 DoNothing") -- ABRIEL.scr:72
    ctx:command("getobjecthandle", "trislan g_hobject") -- ABRIEL.scr:73
    ctx:trigger("g_hobject", "Speak7") -- ABRIEL.scr:74
    do return ctx:exit("") end -- ABRIEL.scr:75
end

script.labels["OnSpeak8"] = function(ctx)
    -- ABRIEL.scr:78
    ctx:command("loopanim", "conv2 0 DoNothing") -- ABRIEL.scr:81
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\08.wav, DoNothing, 100, 512, FALSE, 100") -- ABRIEL.scr:82
    ctx:command("wait", "1 3 Trigger9") -- ABRIEL.scr:83
    do return ctx:exit("") end -- ABRIEL.scr:84
end

script.labels["Trigger9"] = function(ctx)
    -- ABRIEL.scr:87
    ctx:command("stop", "") -- ABRIEL.scr:90
    ctx:command("loopanim", "stand 0 DoNothing") -- ABRIEL.scr:91
    ctx:command("getobjecthandle", "Narrator g_hobject") -- ABRIEL.scr:92
    ctx:trigger("g_hobject", "Speak9") -- ABRIEL.scr:93
    do return ctx:exit("") end -- ABRIEL.scr:94
end

script.labels["OnExit"] = function(ctx)
    -- ABRIEL.scr:98
    ctx:setPropNumber("DoRude", "TRUE") -- ABRIEL.scr:100
    ctx:command("target", "NULL") -- ABRIEL.scr:101
    ctx:command("getobjecthandle", "Abriel2 g_hobject") -- ABRIEL.scr:102
    ctx:command("walkto", "g_hobject 1 FaceStage") -- ABRIEL.scr:103
    do return ctx:exit("") end -- ABRIEL.scr:104
end

script.labels["FaceStage"] = function(ctx)
    -- ABRIEL.scr:107
    ctx:command("getobjecthandle", "Wilam g_hobject") -- ABRIEL.scr:110
    ctx:command("target", "g_hobject") -- ABRIEL.scr:111
    if ctx:condition("bACTIII==TRUE") then -- ABRIEL.scr:112
        ctx:command("getobjecthandle", "Narrator g_hobject") -- ABRIEL.scr:113
        ctx:trigger("g_hobject", "Speak22") -- ABRIEL.scr:114
        ctx:command("set", "bACTIII FALSE") -- ABRIEL.scr:115
        do return ctx:exit("") end -- ABRIEL.scr:116
    end -- ABRIEL.scr:117
    do return ctx:exit("") end -- ABRIEL.scr:119
end

script.labels["OnSpeak14"] = function(ctx)
    -- ABRIEL.scr:122
    ctx:command("getobjecthandle", "Ralof g_hobject") -- ABRIEL.scr:125
    ctx:command("target", "g_hobject") -- ABRIEL.scr:126
    -- getobjecthandle abriel3 g_hobject
    ctx:command("walkto", "g_hobject 1 OnSlap") -- ABRIEL.scr:128
    do return ctx:exit("") end -- ABRIEL.scr:129
end

script.labels["OnSlap"] = function(ctx)
    -- ABRIEL.scr:133
    ctx:command("attack", "OnStop") -- ABRIEL.scr:136
    ctx:command("wait", "1 .75 Slapsound") -- ABRIEL.scr:137
    do return ctx:exit("") end -- ABRIEL.scr:139
end

script.labels["Slapsound"] = function(ctx)
    -- ABRIEL.scr:142
    ctx:command("getobjecthandle", "ralof g_hobject") -- ABRIEL.scr:144
    ctx:trigger("g_hobject", "wince") -- ABRIEL.scr:145
    ctx:command("playsound", "Sounds\\Weapons\\FleshHit03.wav, DoNothing, 100, 512, FALSE, 100") -- ABRIEL.scr:146
    do return ctx:exit("") end -- ABRIEL.scr:147
end

script.labels["OnStop"] = function(ctx)
    -- ABRIEL.scr:150
    ctx:command("getobjecthandle", "leffery g_hobject") -- ABRIEL.scr:153
    ctx:trigger("g_hobject", "target") -- ABRIEL.scr:154
    ctx:command("getobjecthandle", "wilam g_hobject") -- ABRIEL.scr:155
    ctx:trigger("g_hobject", "target") -- ABRIEL.scr:156
    ctx:command("wait", "1 .1 speak15") -- ABRIEL.scr:157
    do return ctx:exit("") end -- ABRIEL.scr:158
end

script.labels["speak15"] = function(ctx)
    -- ABRIEL.scr:161
    ctx:command("loopanim", "conv2 0 DoNothing") -- ABRIEL.scr:163
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\15.wav, DoNothing, 100, 512, FALSE, 100") -- ABRIEL.scr:164
    ctx:command("wait", "1 3.4 Trigger16") -- ABRIEL.scr:165
    do return ctx:exit("") end -- ABRIEL.scr:166
end

script.labels["Trigger16"] = function(ctx)
    -- ABRIEL.scr:169
    ctx:command("getobjecthandle", "Ralof g_hobject") -- ABRIEL.scr:173
    ctx:trigger("g_hobject", "Speak16") -- ABRIEL.scr:174
    do return ctx:exit("") end -- ABRIEL.scr:175
end

script.labels["Onspeak17"] = function(ctx)
    -- ABRIEL.scr:178
    -- Loopanim conv2 0 DoNothing
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\17.wav, DoNothing, 100, 512, FALSE, 100") -- ABRIEL.scr:182
    ctx:command("wait", "1 6.4 Trigger18") -- ABRIEL.scr:183
    do return ctx:exit("") end -- ABRIEL.scr:184
end

script.labels["Trigger18"] = function(ctx)
    -- ABRIEL.scr:187
    ctx:command("getobjecthandle", "Ralof g_hobject") -- ABRIEL.scr:191
    ctx:trigger("g_hobject", "Speak18") -- ABRIEL.scr:192
    do return ctx:exit("") end -- ABRIEL.scr:193
end

script.labels["Onspeak19"] = function(ctx)
    -- ABRIEL.scr:196
    -- Loopanim conv2 0 DoNothing
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\19.wav, DoNothing, 100, 512, FALSE, 100") -- ABRIEL.scr:200
    ctx:command("wait", "1 6.6 Trigger20") -- ABRIEL.scr:201
    do return ctx:exit("") end -- ABRIEL.scr:202
end

script.labels["Trigger20"] = function(ctx)
    -- ABRIEL.scr:205
    ctx:command("stop", "") -- ABRIEL.scr:208
    ctx:command("loopanim", "Stand 0 DoNothing") -- ABRIEL.scr:209
    ctx:command("getobjecthandle", "Ralof g_hobject") -- ABRIEL.scr:210
    ctx:trigger("g_hobject", "Speak20") -- ABRIEL.scr:211
    ctx:command("set", "bACTIII true") -- ABRIEL.scr:212
    do return ctx:exit("") end -- ABRIEL.scr:213
end

script.labels["OnWalk2"] = function(ctx)
    -- ABRIEL.scr:216
    ctx:command("getobjecthandle", "Ralof g_hobject") -- ABRIEL.scr:219
    ctx:command("target", "g_hobject") -- ABRIEL.scr:220
    ctx:command("getobjecthandle", "Abriel3 g_hobject") -- ABRIEL.scr:221
    ctx:command("walkto", "g_hobject 1 DoNothing") -- ABRIEL.scr:222
    do return ctx:exit("") end -- ABRIEL.scr:223
end

script.labels["OnCastCall"] = function(ctx)
    -- ABRIEL.scr:226
    ctx:command("getobjecthandle", "Abriel4 g_hobject") -- ABRIEL.scr:229
    ctx:command("walkto", "g_hobject 1 FaceDoor") -- ABRIEL.scr:230
    do return ctx:exit("") end -- ABRIEL.scr:231
end

script.labels["FaceDoor"] = function(ctx)
    -- ABRIEL.scr:234
    ctx:command("getobjecthandle", "peasant2 g_hobject") -- ABRIEL.scr:237
    ctx:command("target", "g_hobject") -- ABRIEL.scr:238
    do return ctx:exit("") end -- ABRIEL.scr:239
end

script.labels["OnBow"] = function(ctx)
    -- ABRIEL.scr:242
    ctx:command("playanim", "Bow DoNothing") -- ABRIEL.scr:245
    do return ctx:exit("") end -- ABRIEL.scr:246
end

script.labels["Main"] = function(ctx)
    -- ABRIEL.scr:249
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("walk1", "OnWalk1") -- ABRIEL.scr:254
    ctx:addTrigger("speak4", "OnSpeak4") -- ABRIEL.scr:255
    ctx:addTrigger("speak6", "OnSpeak6") -- ABRIEL.scr:256
    ctx:addTrigger("speak8", "OnSpeak8") -- ABRIEL.scr:257
    ctx:addTrigger("Speak14", "OnSpeak14") -- ABRIEL.scr:258
    ctx:addTrigger("Speak17", "OnSpeak17") -- ABRIEL.scr:259
    ctx:addTrigger("Speak19", "OnSpeak19") -- ABRIEL.scr:260
    ctx:addTrigger("Exit", "OnExit") -- ABRIEL.scr:261
    ctx:addTrigger("Walk2", "OnWalk2") -- ABRIEL.scr:262
    ctx:addTrigger("CastCall", "OnCastCall") -- ABRIEL.scr:263
    ctx:addTrigger("Bow", "OnBow") -- ABRIEL.scr:264
    do return ctx:exit("") end -- ABRIEL.scr:265
end

return script
