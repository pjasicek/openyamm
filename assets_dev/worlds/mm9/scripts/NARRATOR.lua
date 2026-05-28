-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NARRATOR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "globals.inc" }

-- givetake.scr
-- 10/4
-- timmy
-- narrator's actions for GCity play
-- edited by Bones -- 6/12/03
-- TELP Patch 1.3 -- corrects playing of 02.wav
-- Parameters
-- P0 Item number of item to give
script.labels["OnStart"] = function(ctx)
    -- NARRATOR.scr:28
    ctx:setPropNumber("DoRude", "False") -- NARRATOR.scr:30
    ctx:command("getobjecthandle", "curtain g_hobject") -- NARRATOR.scr:31
    ctx:trigger("g_hobject", "open") -- NARRATOR.scr:32
    ctx:command("wait", "1 2 OnStart2") -- NARRATOR.scr:33
    do return ctx:exit("") end -- NARRATOR.scr:34
end

script.labels["OnStart2"] = function(ctx)
    -- NARRATOR.scr:38
    ctx:command("loopanim", "conv2 0 DoNothing") -- NARRATOR.scr:40
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\01.wav, DoNothing, 100, 512, FALSE, 100") -- NARRATOR.scr:41
    ctx:command("wait", "1 6, TriggerStart") -- NARRATOR.scr:42
    do return ctx:exit("") end -- NARRATOR.scr:43
end

script.labels["TriggerStart"] = function(ctx)
    -- NARRATOR.scr:47
    ctx:command("getobjecthandle", "Trislan g_hobject") -- NARRATOR.scr:52
    ctx:trigger("g_hobject", "Walk1") -- NARRATOR.scr:53
    ctx:command("getobjecthandle", "Abriel g_hobject") -- NARRATOR.scr:55
    ctx:trigger("g_hobject", "Walk1") -- NARRATOR.scr:56
    ctx:command("loopanim", "conv3 0 DoNothing") -- NARRATOR.scr:58
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\02.wav, DoNothing, 100, 512, FALSE, 100") -- NARRATOR.scr:59
    ctx:command("getobjecthandle", "Abriel1 g_hobject") -- NARRATOR.scr:61
    ctx:command("faceobject", "g_hobject 200 DoNothing") -- NARRATOR.scr:62
    do return ctx:exit("") end -- NARRATOR.scr:63
end

script.labels["OnSpeak9"] = function(ctx)
    -- NARRATOR.scr:66
    ctx:command("getobjecthandle", "Abriel g_hobject") -- NARRATOR.scr:69
    ctx:trigger("g_hobject", "Exit") -- NARRATOR.scr:70
    ctx:command("getobjecthandle", "Trislan g_hobject") -- NARRATOR.scr:71
    ctx:trigger("g_hobject", "Exit") -- NARRATOR.scr:72
    ctx:command("getobjecthandle", "Leffery g_hobject") -- NARRATOR.scr:75
    ctx:trigger("g_hobject", "Start") -- NARRATOR.scr:76
    ctx:command("getobjecthandle", "Ralof g_hobject") -- NARRATOR.scr:77
    ctx:trigger("g_hobject", "Start") -- NARRATOR.scr:78
    ctx:command("getobjecthandle", "Wilam g_hobject") -- NARRATOR.scr:79
    ctx:trigger("g_hobject", "Start") -- NARRATOR.scr:80
    ctx:command("loopanim", "conv3 0 DoNothing") -- NARRATOR.scr:82
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\09.wav, DoNothing, 100, 512, FALSE, 100") -- NARRATOR.scr:83
    ctx:command("wait", "1 4 Trigger9") -- NARRATOR.scr:84
    do return ctx:exit("") end -- NARRATOR.scr:85
end

script.labels["Trigger9"] = function(ctx)
    -- NARRATOR.scr:88
    mm9.gosub(script, ctx, "Onstop") -- NARRATOR.scr:91
    ctx:command("getobjecthandle", "Wilam g_hobject") -- NARRATOR.scr:92
    ctx:trigger("g_hobject", "Speak9") -- NARRATOR.scr:93
    do return ctx:exit("") end -- NARRATOR.scr:94
end

script.labels["OnStop"] = function(ctx)
    -- NARRATOR.scr:97
    ctx:command("stop", "") -- NARRATOR.scr:99
    ctx:command("loopanim", "stand 0 DoNothing") -- NARRATOR.scr:100
    do return ctx:exit("") end -- NARRATOR.scr:101
end

script.labels["OnSpeak21"] = function(ctx)
    -- NARRATOR.scr:105
    ctx:command("loopanim", "conv1 0 DoNothing") -- NARRATOR.scr:108
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\21.wav, DoNothing, 100, 512, FALSE, 100") -- NARRATOR.scr:109
    ctx:command("wait", "1 4 Trigger22") -- NARRATOR.scr:110
    do return ctx:exit("") end -- NARRATOR.scr:111
end

script.labels["Trigger22"] = function(ctx)
    -- NARRATOR.scr:116
    ctx:command("stop", "") -- NARRATOR.scr:119
    ctx:command("loopanim", "stand 0 DoNothing") -- NARRATOR.scr:120
    ctx:command("getobjecthandle", "Abriel g_hobject") -- NARRATOR.scr:121
    ctx:trigger("g_hobject", "exit") -- NARRATOR.scr:122
    ctx:command("getobjecthandle", "Ralof g_hobject") -- NARRATOR.scr:123
    ctx:trigger("g_hobject", "exit") -- NARRATOR.scr:124
    ctx:command("getobjecthandle", "Wilam g_hobject") -- NARRATOR.scr:125
    ctx:trigger("g_hobject", "exit") -- NARRATOR.scr:126
    ctx:command("getobjecthandle", "Leffery g_hobject") -- NARRATOR.scr:127
    ctx:trigger("g_hobject", "exit") -- NARRATOR.scr:128
    do return ctx:exit("") end -- NARRATOR.scr:129
end

script.labels["OnSpeak22"] = function(ctx)
    -- NARRATOR.scr:132
    ctx:command("getobjecthandle", "Trislan g_hobject") -- NARRATOR.scr:135
    ctx:trigger("g_hobject", "Walk2") -- NARRATOR.scr:136
    ctx:command("loopanim", "conv1 0 DoNothing") -- NARRATOR.scr:137
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\22.wav, DoNothing, 100, 512, FALSE, 100") -- NARRATOR.scr:138
    ctx:command("wait", "2 1 Abrielwalk") -- NARRATOR.scr:139
    ctx:command("wait", "1 5.5 Trigger23") -- NARRATOR.scr:140
    do return ctx:exit("") end -- NARRATOR.scr:141
end

script.labels["Abrielwalk"] = function(ctx)
    -- NARRATOR.scr:144
    ctx:command("getobjecthandle", "Abriel g_hobject") -- NARRATOR.scr:147
    ctx:trigger("g_hobject", "Walk2") -- NARRATOR.scr:148
    do return ctx:exit("") end -- NARRATOR.scr:149
end

script.labels["Trigger23"] = function(ctx)
    -- NARRATOR.scr:152
    ctx:command("getobjecthandle", "ralof g_hobject") -- NARRATOR.scr:155
    ctx:trigger("g_hobject", "Walk2") -- NARRATOR.scr:156
    ctx:command("wait", "1 1 GuardWalk") -- NARRATOR.scr:157
    do return ctx:exit("") end -- NARRATOR.scr:158
end

script.labels["Guardwalk"] = function(ctx)
    -- NARRATOR.scr:161
    ctx:command("getobjecthandle", "Leffery g_hobject") -- NARRATOR.scr:163
    ctx:trigger("g_hobject", "Walk2") -- NARRATOR.scr:164
    ctx:command("getobjecthandle", "Wilam g_hobject") -- NARRATOR.scr:165
    ctx:trigger("g_hobject", "Walk2") -- NARRATOR.scr:166
    do return ctx:exit("") end -- NARRATOR.scr:167
end

script.labels["OnSpeak27"] = function(ctx)
    -- NARRATOR.scr:170
    ctx:command("getobjecthandle", "peasant2 g_hobject") -- NARRATOR.scr:173
    ctx:command("target", "g_hobject") -- NARRATOR.scr:174
    ctx:command("loopanim", "conv3 0 DoNothing") -- NARRATOR.scr:175
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\27.wav, DoNothing, 100, 512, FALSE, 100") -- NARRATOR.scr:176
    ctx:command("wait", "1 13 Trigger28") -- NARRATOR.scr:177
    do return ctx:exit("") end -- NARRATOR.scr:178
end

script.labels["Trigger28"] = function(ctx)
    -- NARRATOR.scr:181
    ctx:command("getobjecthandle", "Ralof g_hobject") -- NARRATOR.scr:184
    ctx:trigger("g_hobject", "CastCall") -- NARRATOR.scr:185
    ctx:command("getobjecthandle", "Wilam g_hobject") -- NARRATOR.scr:186
    ctx:trigger("g_hobject", "CastCall") -- NARRATOR.scr:187
    ctx:command("getobjecthandle", "Leffery g_hobject") -- NARRATOR.scr:188
    ctx:trigger("g_hobject", "CastCall") -- NARRATOR.scr:189
    ctx:command("getobjecthandle", "Abriel g_hobject") -- NARRATOR.scr:190
    ctx:trigger("g_hobject", "CastCall") -- NARRATOR.scr:191
    ctx:command("getobjecthandle", "Trislan g_hobject") -- NARRATOR.scr:192
    ctx:trigger("g_hobject", "CastCall") -- NARRATOR.scr:193
    ctx:command("wait", "1 3 Bow") -- NARRATOR.scr:194
    do return ctx:exit("") end -- NARRATOR.scr:195
end

script.labels["Bow"] = function(ctx)
    -- NARRATOR.scr:199
    ctx:command("loopanim", "conv3 0 DoNothing") -- NARRATOR.scr:203
    ctx:command("playsound", "voices\\cinema\\guberlandplay\\28.wav, DoNothing, 100, 512, FALSE, 100") -- NARRATOR.scr:204
    ctx:command("wait", "1 1 OnBow") -- NARRATOR.scr:205
    do return ctx:exit("") end -- NARRATOR.scr:206
end

script.labels["OnBow"] = function(ctx)
    -- NARRATOR.scr:209
    ctx:command("stop", "") -- NARRATOR.scr:212
    ctx:command("loopanim", "stand 0 DoNothing") -- NARRATOR.scr:213
    ctx:command("getobjecthandle", "Ralof g_hobject") -- NARRATOR.scr:214
    ctx:trigger("g_hobject", "Bow") -- NARRATOR.scr:215
    ctx:command("getobjecthandle", "Wilam g_hobject") -- NARRATOR.scr:216
    ctx:trigger("g_hobject", "Bow") -- NARRATOR.scr:217
    ctx:command("getobjecthandle", "Leffery g_hobject") -- NARRATOR.scr:218
    ctx:trigger("g_hobject", "Bow") -- NARRATOR.scr:219
    ctx:command("getobjecthandle", "Abriel g_hobject") -- NARRATOR.scr:220
    ctx:trigger("g_hobject", "Bow") -- NARRATOR.scr:221
    ctx:command("getobjecthandle", "Trislan g_hobject") -- NARRATOR.scr:222
    ctx:trigger("g_hobject", "Bow") -- NARRATOR.scr:223
    ctx:command("wait", "1 5 Exit") -- NARRATOR.scr:224
    do return ctx:exit("") end -- NARRATOR.scr:225
end

script.labels["Exit"] = function(ctx)
    -- NARRATOR.scr:228
    ctx:command("getobjecthandle", "curtain g_hobject") -- NARRATOR.scr:230
    ctx:trigger("g_hobject", "close") -- NARRATOR.scr:231
    ctx:command("getobjecthandle", "Ralof g_hobject") -- NARRATOR.scr:232
    ctx:trigger("g_hobject", "Exit") -- NARRATOR.scr:233
    ctx:command("getobjecthandle", "Wilam g_hobject") -- NARRATOR.scr:234
    ctx:trigger("g_hobject", "Exit") -- NARRATOR.scr:235
    ctx:command("getobjecthandle", "Leffery g_hobject") -- NARRATOR.scr:236
    ctx:trigger("g_hobject", "Exit") -- NARRATOR.scr:237
    ctx:command("getobjecthandle", "Abriel g_hobject") -- NARRATOR.scr:238
    ctx:trigger("g_hobject", "Exit") -- NARRATOR.scr:239
    ctx:command("getobjecthandle", "Trislan g_hobject") -- NARRATOR.scr:240
    ctx:trigger("g_hobject", "Exit") -- NARRATOR.scr:241
    ctx:setPropNumber("DoRude", "TRUE") -- NARRATOR.scr:242
    do return ctx:exit("") end -- NARRATOR.scr:243
end

script.labels["Main"] = function(ctx)
    -- NARRATOR.scr:246
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("start", "Onstart") -- NARRATOR.scr:251
    ctx:addTrigger("stop", "OnStop") -- NARRATOR.scr:252
    ctx:addTrigger("Speak9", "OnSpeak9") -- NARRATOR.scr:253
    ctx:addTrigger("Speak21", "OnSpeak21") -- NARRATOR.scr:254
    ctx:addTrigger("Speak22", "OnSpeak22") -- NARRATOR.scr:255
    ctx:addTrigger("Speak27", "OnSpeak27") -- NARRATOR.scr:256
    ctx:command("@m", "14 : 30 OnStart") -- NARRATOR.scr:257
    ctx:command("@m", "16 : 30 OnStart") -- NARRATOR.scr:258
    do return ctx:exit("") end -- NARRATOR.scr:259
end

return script
