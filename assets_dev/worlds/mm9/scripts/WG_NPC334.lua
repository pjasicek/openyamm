-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WG_NPC334.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- WG_NPC336.scr
-- timmy
-- handles Hanndl acting for cutscene
-- flag variables
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["Loop"] = function(ctx)
    -- WG_NPC334.scr:26
    ctx:command("getmyhandle", "g_hobject") -- WG_NPC334.scr:30
    ctx:command("clearflag", "g_hobject, visible") -- WG_NPC334.scr:31
    ctx:command("clearflag", "g_hobject, solid") -- WG_NPC334.scr:32
    ctx:command("clearflag", "g_hobject, gravity") -- WG_NPC334.scr:33
    ctx:command("getobjecthandle", "WyrdeoftheKnown0 g_hobject") -- WG_NPC334.scr:35
    ctx:command("clearflag", "g_hobject, visible") -- WG_NPC334.scr:36
    ctx:command("clearflag", "g_hobject, solid") -- WG_NPC334.scr:37
    ctx:command("clearflag", "g_hobject, gravity") -- WG_NPC334.scr:38
    ctx:command("getobjecthandle", "WyrdeoftheKnown1 g_hobject") -- WG_NPC334.scr:40
    ctx:command("clearflag", "g_hobject, visible") -- WG_NPC334.scr:41
    ctx:command("clearflag", "g_hobject, solid") -- WG_NPC334.scr:42
    ctx:command("clearflag", "g_hobject, gravity") -- WG_NPC334.scr:43
    ctx:command("getobjecthandle", "WyrdeoftheKnowing0 g_hobject") -- WG_NPC334.scr:45
    ctx:command("clearflag", "g_hobject, visible") -- WG_NPC334.scr:46
    ctx:command("clearflag", "g_hobject, solid") -- WG_NPC334.scr:47
    ctx:command("clearflag", "g_hobject, gravity") -- WG_NPC334.scr:48
    do return ctx:exit("") end -- WG_NPC334.scr:49
end

script.labels["OnStart"] = function(ctx)
    -- WG_NPC334.scr:52
    ctx:command("getmyhandle", "g_hobject") -- WG_NPC334.scr:55
    ctx:command("setflag", "g_hobject, visible") -- WG_NPC334.scr:56
    ctx:command("setflag", "g_hobject, solid") -- WG_NPC334.scr:57
    ctx:command("setflag", "g_hobject, gravity") -- WG_NPC334.scr:58
    ctx:command("getobjecthandle", "WyrdeoftheKnown0 g_hobject") -- WG_NPC334.scr:60
    ctx:command("setflag", "g_hobject, visible") -- WG_NPC334.scr:61
    ctx:command("setflag", "g_hobject, solid") -- WG_NPC334.scr:62
    ctx:command("setflag", "g_hobject, gravity") -- WG_NPC334.scr:63
    ctx:command("getobjecthandle", "WyrdeoftheKnown1 g_hobject") -- WG_NPC334.scr:65
    ctx:command("setflag", "g_hobject, visible") -- WG_NPC334.scr:66
    ctx:command("setflag", "g_hobject, solid") -- WG_NPC334.scr:67
    ctx:command("setflag", "g_hobject, gravity") -- WG_NPC334.scr:68
    ctx:command("getobjecthandle", "WyrdeoftheKnowing0 g_hobject") -- WG_NPC334.scr:70
    ctx:command("setflag", "g_hobject, visible") -- WG_NPC334.scr:71
    ctx:command("setflag", "g_hobject, solid") -- WG_NPC334.scr:72
    ctx:command("setflag", "g_hobject, gravity") -- WG_NPC334.scr:73
    do return ctx:exit("") end -- WG_NPC334.scr:74
end

script.labels["OnAction"] = function(ctx)
    -- WG_NPC334.scr:77
    ctx:command("getobjecthandle", "HanndlMarker g_hobject") -- WG_NPC334.scr:80
    ctx:command("walkto", "g_hobject 0 OnKrohn") -- WG_NPC334.scr:81
    do return ctx:exit("") end -- WG_NPC334.scr:82
end

script.labels["OnKrohn"] = function(ctx)
    -- WG_NPC334.scr:85
    ctx:command("getobjecthandle", "krohn g_hobject") -- WG_NPC334.scr:88
    ctx:trigger("g_hobject", "Arrive") -- WG_NPC334.scr:89
    do return ctx:exit("") end -- WG_NPC334.scr:90
end

script.labels["OnHanndl1"] = function(ctx)
    -- WG_NPC334.scr:93
    ctx:command("playanim", "Hanndl01 DoNothing") -- WG_NPC334.scr:96
    -- "They were successful"
    ctx:command("wait", "1 5 Krohn1") -- WG_NPC334.scr:98
    do return ctx:exit("") end -- WG_NPC334.scr:99
end

script.labels["OnVoice1"] = function(ctx)
    -- WG_NPC334.scr:104
    ctx:command("playsound", "voices\\cinema\\wingame\\Hanndl01.wav, DoNothing, 100, 240000, FALSE, 100") -- WG_NPC334.scr:107
    -- "They were successful"
    do return ctx:exit("") end -- WG_NPC334.scr:109
end

script.labels["OnHanndl2"] = function(ctx)
    -- WG_NPC334.scr:113
    ctx:command("wait", "1 1 Speak02") -- WG_NPC334.scr:116
    do return ctx:exit("") end -- WG_NPC334.scr:117
end

script.labels["Speak02"] = function(ctx)
    -- WG_NPC334.scr:120
    ctx:command("playanim", "Hanndl02 DoNothing") -- WG_NPC334.scr:123
    -- "I wanted to talk to you about that"
    ctx:command("wait", "1 2.5 Krohn2") -- WG_NPC334.scr:125
    do return ctx:exit("") end -- WG_NPC334.scr:126
end

script.labels["OnVoice2"] = function(ctx)
    -- WG_NPC334.scr:129
    ctx:command("playsound", "voices\\cinema\\wingame\\Hanndl02.wav, DoNothing, 100, 240000, FALSE, 100") -- WG_NPC334.scr:132
    -- "I wanted to talk to you about that"
    do return ctx:exit("") end -- WG_NPC334.scr:134
end

script.labels["OnHanndl3"] = function(ctx)
    -- WG_NPC334.scr:138
    ctx:command("playanim", "Hanndl03 DoNothing") -- WG_NPC334.scr:141
    -- ".You played them..."
    ctx:command("wait", "1 6 Krohn3") -- WG_NPC334.scr:143
    do return ctx:exit("") end -- WG_NPC334.scr:144
end

script.labels["OnVoice3"] = function(ctx)
    -- WG_NPC334.scr:147
    ctx:command("playsound", "voices\\cinema\\wingame\\Hanndl03.wav, DoNothing, 100, 240000, FALSE, 100") -- WG_NPC334.scr:150
    -- ".You played them..."
    do return ctx:exit("") end -- WG_NPC334.scr:152
end

script.labels["OnHanndl4"] = function(ctx)
    -- WG_NPC334.scr:155
    ctx:command("playanim", "Hanndl04 DoNothing") -- WG_NPC334.scr:158
    -- "They gave up everything to serve you..."
    ctx:command("wait", "1 19 Krohn4") -- WG_NPC334.scr:160
    do return ctx:exit("") end -- WG_NPC334.scr:161
end

script.labels["OnVoice4"] = function(ctx)
    -- WG_NPC334.scr:164
    ctx:command("playsound", "voices\\cinema\\wingame\\Hanndl04.wav, DoNothing, 100, 240000, FALSE, 100") -- WG_NPC334.scr:167
    -- "They gave up everything to serve you..."
    do return ctx:exit("") end -- WG_NPC334.scr:169
end

script.labels["OnHanndl5"] = function(ctx)
    -- WG_NPC334.scr:173
    ctx:command("playanim", "Hanndl05 Krohn5") -- WG_NPC334.scr:176
    -- "I think that will suffice..."
    -- wait 1 3 Krohn5
    do return ctx:exit("") end -- WG_NPC334.scr:179
end

script.labels["OnVoice5"] = function(ctx)
    -- WG_NPC334.scr:182
    ctx:command("playsound", "voices\\cinema\\wingame\\Hanndl05.wav, DoNothing, 100, 240000, FALSE, 100") -- WG_NPC334.scr:185
    -- "I think that will suffice..."
    do return ctx:exit("") end -- WG_NPC334.scr:187
end

script.labels["OnHanndl6"] = function(ctx)
    -- WG_NPC334.scr:190
    ctx:command("playsound", "voices\\cinema\\wingame\\Hanndl06.wav, DoNothing, 100, 240000, FALSE, 100") -- WG_NPC334.scr:193
    -- PlayAnim Hanndl06 DoNothing
    -- "What is this?"
    ctx:command("wait", "1 2 Krohn6") -- WG_NPC334.scr:196
    do return ctx:exit("") end -- WG_NPC334.scr:197
end

script.labels["OnVoice6"] = function(ctx)
    -- WG_NPC334.scr:200
    ctx:command("playsound", "voices\\cinema\\wingame\\Hanndl06.wav, DoNothing, 100, 240000, FALSE, 100") -- WG_NPC334.scr:203
    -- "What is this?"
    do return ctx:exit("") end -- WG_NPC334.scr:205
end

script.labels["Krohn1"] = function(ctx)
    -- WG_NPC334.scr:208
    ctx:command("getobjecthandle", "winman g_hobject") -- WG_NPC334.scr:211
    ctx:trigger("g_hobject", "Krohn1") -- WG_NPC334.scr:212
    do return ctx:exit("") end -- WG_NPC334.scr:213
end

script.labels["Krohn2"] = function(ctx)
    -- WG_NPC334.scr:217
    ctx:command("getobjecthandle", "winman g_hobject") -- WG_NPC334.scr:220
    ctx:trigger("g_hobject", "Krohn2") -- WG_NPC334.scr:221
    do return ctx:exit("") end -- WG_NPC334.scr:222
end

script.labels["Krohn3"] = function(ctx)
    -- WG_NPC334.scr:225
    ctx:command("getobjecthandle", "winman g_hobject") -- WG_NPC334.scr:228
    ctx:trigger("g_hobject", "Krohn3") -- WG_NPC334.scr:229
    do return ctx:exit("") end -- WG_NPC334.scr:230
end

script.labels["Krohn4"] = function(ctx)
    -- WG_NPC334.scr:232
    ctx:command("getobjecthandle", "winman g_hobject") -- WG_NPC334.scr:235
    ctx:trigger("g_hobject", "Krohn4") -- WG_NPC334.scr:236
    do return ctx:exit("") end -- WG_NPC334.scr:237
end

script.labels["Krohn5"] = function(ctx)
    -- WG_NPC334.scr:240
    ctx:command("getobjecthandle", "krohn g_hobject") -- WG_NPC334.scr:242
    ctx:command("walkto", "g_hobject 16 ReachOut") -- WG_NPC334.scr:243
    ctx:command("getobjecthandle", "winman g_hobject") -- WG_NPC334.scr:244
    ctx:trigger("g_hobject", "Krohn5") -- WG_NPC334.scr:245
    do return ctx:exit("") end -- WG_NPC334.scr:246
end

script.labels["ReachOut"] = function(ctx)
    -- WG_NPC334.scr:249
    ctx:command("playanim", "Hanndl06 DoNothing") -- WG_NPC334.scr:251
    do return ctx:exit("") end -- WG_NPC334.scr:252
end

script.labels["Krohn6"] = function(ctx)
    -- WG_NPC334.scr:254
    ctx:command("getobjecthandle", "winman g_hobject") -- WG_NPC334.scr:257
    ctx:trigger("g_hobject", "Krohn6") -- WG_NPC334.scr:258
    do return ctx:exit("") end -- WG_NPC334.scr:259
end

script.labels["Main"] = function(ctx)
    -- WG_NPC334.scr:262
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Start", "OnStart") -- WG_NPC334.scr:267
    ctx:addTrigger("Stop", "Loop") -- WG_NPC334.scr:268
    ctx:addTrigger("Action", "OnAction") -- WG_NPC334.scr:269
    ctx:addTrigger("Hanndl1", "OnHanndl1") -- WG_NPC334.scr:270
    ctx:addTrigger("Hanndl2", "OnHanndl2") -- WG_NPC334.scr:271
    ctx:addTrigger("Hanndl3", "OnHanndl3") -- WG_NPC334.scr:272
    ctx:addTrigger("Hanndl4", "OnHanndl4") -- WG_NPC334.scr:273
    ctx:addTrigger("Hanndl5", "OnHanndl5") -- WG_NPC334.scr:274
    ctx:addTrigger("Hanndl6", "OnHanndl6") -- WG_NPC334.scr:275
    ctx:command("addmodelkey", "Voice1 OnVoice1") -- WG_NPC334.scr:277
    ctx:command("addmodelkey", "Voice2 OnVoice2") -- WG_NPC334.scr:278
    ctx:command("addmodelkey", "Voice3 OnVoice3") -- WG_NPC334.scr:279
    ctx:command("addmodelkey", "Voice4 OnVoice4") -- WG_NPC334.scr:280
    ctx:command("addmodelkey", "Voice5 OnVoice5") -- WG_NPC334.scr:281
    -- AddModelKey Voice6 OnVoice6
    ctx:command("wait", "1 .1 Loop") -- WG_NPC334.scr:283
    do return ctx:exit("") end -- WG_NPC334.scr:284
end

return script
