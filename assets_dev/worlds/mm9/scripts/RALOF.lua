-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "RALOF.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- givetake.scr
-- 10/4
-- timmy
-- gives party specific item
-- Parameters
-- P0 Item number of item to give
script.labels["OnStart"] = function(ctx)
    -- RALOF.scr:26
    ctx:setPropNumber("DoRude", "False") -- RALOF.scr:28
    ctx:command("getobjecthandle", "Ralof1 g_hobject") -- RALOF.scr:29
    ctx:command("walkto", "g_hobject 1 OnArrive") -- RALOF.scr:30
    do return ctx:exit("") end -- RALOF.scr:31
end

script.labels["OnArrive"] = function(ctx)
    -- RALOF.scr:34
    ctx:command("getobjecthandle", "Wilam g_hobject") -- RALOF.scr:38
    ctx:command("target", "g_hobject") -- RALOF.scr:39
    do return ctx:exit("") end -- RALOF.scr:40
end

script.labels["OnSpeak11"] = function(ctx)
    -- RALOF.scr:43
    -- start speaking
    ctx:command("loopanim", "conv1 0 DoNothing") -- RALOF.scr:47
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\11.wav, DoNothing, 100, 512, FALSE, 100") -- RALOF.scr:48
    ctx:command("wait", "2 9.3 Trigger12") -- RALOF.scr:49
    do return ctx:exit("") end -- RALOF.scr:50
end

script.labels["Trigger12"] = function(ctx)
    -- RALOF.scr:53
    ctx:command("stop", "") -- RALOF.scr:56
    ctx:command("loopanim", "stand 0 Donothing") -- RALOF.scr:57
    ctx:command("getobjecthandle", "Leffery g_hobject") -- RALOF.scr:58
    ctx:trigger("g_hobject", "Speak12") -- RALOF.scr:59
    do return ctx:exit("") end -- RALOF.scr:60
end

script.labels["OnSpeak13"] = function(ctx)
    -- RALOF.scr:63
    -- start speaking
    ctx:command("getobjecthandle", "leffery g_hobject") -- RALOF.scr:67
    ctx:command("target", "g_hobject") -- RALOF.scr:68
    ctx:command("loopanim", "conv1 0 DoNothing") -- RALOF.scr:69
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\13b.wav, DoNothing, 100, 512, FALSE, 100") -- RALOF.scr:70
    ctx:command("wait", "1 5 FaceWilam") -- RALOF.scr:71
    ctx:command("wait", "2 20 Trigger14") -- RALOF.scr:72
    do return ctx:exit("") end -- RALOF.scr:73
end

script.labels["FaceWilam"] = function(ctx)
    -- RALOF.scr:76
    ctx:command("stop", "") -- RALOF.scr:79
    ctx:command("getobjecthandle", "Wilam g_hobject") -- RALOF.scr:80
    ctx:command("target", "g_hobject") -- RALOF.scr:81
    ctx:command("wait", "1 .1 converse") -- RALOF.scr:82
    do return ctx:exit("") end -- RALOF.scr:83
end

script.labels["converse"] = function(ctx)
    -- RALOF.scr:86
    ctx:command("loopanim", "conv2 0 DoNothing") -- RALOF.scr:88
    do return ctx:exit("") end -- RALOF.scr:89
end

script.labels["Trigger14"] = function(ctx)
    -- RALOF.scr:92
    ctx:command("stop", "") -- RALOF.scr:95
    ctx:command("loopanim", "stand 0 Donothing") -- RALOF.scr:96
    ctx:command("getobjecthandle", "Leffery g_hobject") -- RALOF.scr:97
    ctx:trigger("g_hobject", "Speak14") -- RALOF.scr:98
    ctx:command("getobjecthandle", "abriel g_hobject") -- RALOF.scr:99
    ctx:command("target", "g_hobject") -- RALOF.scr:100
    ctx:trigger("g_hobject", "Speak14") -- RALOF.scr:101
    ctx:command("getobjecthandle", "wilam g_hobject") -- RALOF.scr:102
    ctx:trigger("g_hobject", "attention") -- RALOF.scr:103
    do return ctx:exit("") end -- RALOF.scr:104
end

script.labels["OnSpeak16"] = function(ctx)
    -- RALOF.scr:107
    -- start speaking
    -- LoopAnim conv1 0 DoNothing
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\16.wav, DoNothing, 100, 512, FALSE, 100") -- RALOF.scr:112
    ctx:command("wait", "2 1.5 Trigger17") -- RALOF.scr:113
    do return ctx:exit("") end -- RALOF.scr:114
end

script.labels["Trigger17"] = function(ctx)
    -- RALOF.scr:117
    ctx:command("stop", "") -- RALOF.scr:120
    ctx:command("loopanim", "stand 0 Donothing") -- RALOF.scr:121
    ctx:command("getobjecthandle", "Abriel g_hobject") -- RALOF.scr:122
    ctx:trigger("g_hobject", "Speak17") -- RALOF.scr:123
    do return ctx:exit("") end -- RALOF.scr:124
end

script.labels["OnSpeak18"] = function(ctx)
    -- RALOF.scr:128
    -- start speaking
    -- LoopAnim conv1 0 DoNothing
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\18.wav, DoNothing, 100, 512, FALSE, 100") -- RALOF.scr:133
    ctx:command("wait", "2 1.5 Trigger19") -- RALOF.scr:134
    do return ctx:exit("") end -- RALOF.scr:135
end

script.labels["Trigger19"] = function(ctx)
    -- RALOF.scr:138
    ctx:command("stop", "") -- RALOF.scr:141
    ctx:command("loopanim", "stand 0 Donothing") -- RALOF.scr:142
    ctx:command("getobjecthandle", "Abriel g_hobject") -- RALOF.scr:143
    ctx:trigger("g_hobject", "Speak19") -- RALOF.scr:144
    do return ctx:exit("") end -- RALOF.scr:145
end

script.labels["OnSpeak20"] = function(ctx)
    -- RALOF.scr:148
    -- start speaking
    ctx:command("loopanim", "conv1 0 DoNothing") -- RALOF.scr:152
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\20.wav, DoNothing, 100, 512, FALSE, 100") -- RALOF.scr:153
    ctx:command("wait", "2 3.5 Trigger21") -- RALOF.scr:154
    do return ctx:exit("") end -- RALOF.scr:155
end

script.labels["Trigger21"] = function(ctx)
    -- RALOF.scr:158
    ctx:command("stop", "") -- RALOF.scr:161
    ctx:command("loopanim", "stand 0 Donothing") -- RALOF.scr:162
    ctx:command("getobjecthandle", "Narrator g_hobject") -- RALOF.scr:163
    ctx:trigger("g_hobject", "Speak21") -- RALOF.scr:164
    do return ctx:exit("") end -- RALOF.scr:165
end

script.labels["OnExit"] = function(ctx)
    -- RALOF.scr:168
    ctx:setPropNumber("DoRude", "TRUE") -- RALOF.scr:170
    ctx:command("target", "NULL") -- RALOF.scr:171
    ctx:command("getobjecthandle", "Ralof2 g_hobject") -- RALOF.scr:172
    ctx:command("walkto", "g_hobject 1 FaceStage") -- RALOF.scr:173
    do return ctx:exit("") end -- RALOF.scr:174
end

script.labels["FaceStage"] = function(ctx)
    -- RALOF.scr:178
    ctx:command("getobjecthandle", "trislan g_hobject") -- RALOF.scr:181
    ctx:command("target", "g_hobject") -- RALOF.scr:182
    do return ctx:exit("") end -- RALOF.scr:183
end

script.labels["OnWalk2"] = function(ctx)
    -- RALOF.scr:187
    ctx:command("getobjecthandle", "trislan g_hobject") -- RALOF.scr:189
    ctx:command("target", "g_hobject") -- RALOF.scr:190
    ctx:command("walkto", "g_hobject 1 Trigger23") -- RALOF.scr:191
    do return ctx:exit("") end -- RALOF.scr:192
end

script.labels["Trigger23"] = function(ctx)
    -- RALOF.scr:195
    ctx:command("stop", "") -- RALOF.scr:198
    ctx:command("loopanim", "stand 0 Donothing") -- RALOF.scr:199
    ctx:command("getobjecthandle", "Trislan g_hobject") -- RALOF.scr:200
    ctx:trigger("g_hobject", "Speak23") -- RALOF.scr:201
    do return ctx:exit("") end -- RALOF.scr:202
end

script.labels["OnSpeak24"] = function(ctx)
    -- RALOF.scr:206
    -- start speaking
    ctx:command("loopanim", "conv4 0 DoNothing") -- RALOF.scr:210
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\24.wav, DoNothing, 100, 512, FALSE, 100") -- RALOF.scr:211
    ctx:command("wait", "2 5.4 Trigger25") -- RALOF.scr:212
    do return ctx:exit("") end -- RALOF.scr:213
end

script.labels["Trigger25"] = function(ctx)
    -- RALOF.scr:216
    ctx:command("stop", "") -- RALOF.scr:219
    ctx:command("loopanim", "stand 0 Donothing") -- RALOF.scr:220
    ctx:command("getobjecthandle", "Trislan g_hobject") -- RALOF.scr:221
    ctx:trigger("g_hobject", "Speak25") -- RALOF.scr:222
    do return ctx:exit("") end -- RALOF.scr:223
end

script.labels["OnSpeak26"] = function(ctx)
    -- RALOF.scr:226
    -- start speaking
    ctx:command("loopanim", "conv3 0 DoNothing") -- RALOF.scr:230
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\26.wav, DoNothing, 100, 512, FALSE, 100") -- RALOF.scr:231
    ctx:command("wait", "2 3.4 Attack") -- RALOF.scr:232
    do return ctx:exit("") end -- RALOF.scr:233
end

script.labels["Attack"] = function(ctx)
    -- RALOF.scr:236
    ctx:command("attack", "OnStop") -- RALOF.scr:239
    ctx:command("wait", "1 .75 Slapsound") -- RALOF.scr:240
    do return ctx:exit("") end -- RALOF.scr:242
end

script.labels["Slapsound"] = function(ctx)
    -- RALOF.scr:245
    ctx:command("playsound", "Sounds\\Weapons\\FleshHit04.wav, DoNothing, 100, 512, FALSE, 100") -- RALOF.scr:248
    do return ctx:exit("") end -- RALOF.scr:249
end

script.labels["OnStop"] = function(ctx)
    -- RALOF.scr:252
    ctx:command("stop", "") -- RALOF.scr:255
    ctx:command("loopanim", "stand 0 Donothing") -- RALOF.scr:256
    ctx:command("getobjecthandle", "Trislan g_hobject") -- RALOF.scr:257
    ctx:trigger("g_hobject", "Die") -- RALOF.scr:258
    do return ctx:exit("") end -- RALOF.scr:259
end

script.labels["OnCastCall"] = function(ctx)
    -- RALOF.scr:262
    ctx:command("getobjecthandle", "Ralof3 g_hobject") -- RALOF.scr:265
    ctx:command("walkto", "g_hobject 1 FaceDoor") -- RALOF.scr:266
    do return ctx:exit("") end -- RALOF.scr:267
end

script.labels["FaceDoor"] = function(ctx)
    -- RALOF.scr:270
    ctx:command("getobjecthandle", "peasant2 g_hobject") -- RALOF.scr:273
    ctx:command("target", "g_hobject") -- RALOF.scr:274
    do return ctx:exit("") end -- RALOF.scr:275
end

script.labels["OnBow"] = function(ctx)
    -- RALOF.scr:278
    ctx:command("playanim", "Bow DoNothing") -- RALOF.scr:281
    do return ctx:exit("") end -- RALOF.scr:282
end

script.labels["OnWince"] = function(ctx)
    -- RALOF.scr:285
    ctx:command("playanim", "Wince1 DoNothing") -- RALOF.scr:288
    do return ctx:exit("") end -- RALOF.scr:289
end

script.labels["Main"] = function(ctx)
    -- RALOF.scr:292
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("start", "OnStart") -- RALOF.scr:297
    ctx:addTrigger("Speak11", "OnSpeak11") -- RALOF.scr:298
    ctx:addTrigger("Speak13", "OnSpeak13") -- RALOF.scr:299
    ctx:addTrigger("Speak16", "OnSpeak16") -- RALOF.scr:300
    ctx:addTrigger("Speak18", "OnSpeak18") -- RALOF.scr:301
    ctx:addTrigger("Speak20", "OnSpeak20") -- RALOF.scr:302
    ctx:addTrigger("Exit", "OnExit") -- RALOF.scr:303
    ctx:addTrigger("Walk2", "OnWalk2") -- RALOF.scr:304
    ctx:addTrigger("Speak24", "OnSpeak24") -- RALOF.scr:305
    ctx:addTrigger("Speak26", "OnSpeak26") -- RALOF.scr:306
    ctx:addTrigger("CastCall", "OnCastCall") -- RALOF.scr:307
    ctx:addTrigger("Bow", "OnBow") -- RALOF.scr:308
    ctx:addTrigger("Wince", "OnWince") -- RALOF.scr:309
    do return ctx:exit("") end -- RALOF.scr:310
end

return script
