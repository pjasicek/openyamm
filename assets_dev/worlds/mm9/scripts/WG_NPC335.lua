-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WG_NPC335.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- WG_NPC335.scr
-- timmy
-- handles Krohn acting for cutscene
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
-- flag variables
script.labels["Loop"] = function(ctx)
    -- WG_NPC335.scr:25
    ctx:state().g_hobject = ctx:self() -- WG_NPC335.scr:29
    ctx:hidePiece("spear") -- WG_NPC335.scr:30
    ctx:self():setFlag("visible", false) -- WG_NPC335.scr:31
    ctx:self():setFlag("solid", false) -- WG_NPC335.scr:32
    ctx:self():setFlag("gravity", false) -- WG_NPC335.scr:33
    do return ctx:exit("") end -- WG_NPC335.scr:34
end

script.labels["OnStart"] = function(ctx)
    -- WG_NPC335.scr:37
    ctx:state().g_hobject = ctx:self() -- WG_NPC335.scr:40
    ctx:self():setFlag("visible", true) -- WG_NPC335.scr:41
    ctx:self():setFlag("solid", true) -- WG_NPC335.scr:42
    ctx:self():setFlag("gravity", true) -- WG_NPC335.scr:43
    ctx:self():loopAnimation("stand", 0, "DoNothing") -- WG_NPC335.scr:44
    do return ctx:exit("") end -- WG_NPC335.scr:45
end

script.labels["OnArrive"] = function(ctx)
    -- WG_NPC335.scr:48
    ctx:getParam(0, "g_hobject") -- WG_NPC335.scr:50
    ctx:self():setTarget(ctx:object("g_hobject")) -- WG_NPC335.scr:51
    ctx:wait(1, 1, "StartTalk") -- WG_NPC335.scr:52
    do return ctx:exit("") end -- WG_NPC335.scr:53
end

script.labels["StartTalk"] = function(ctx)
    -- WG_NPC335.scr:56
    ctx:object("WinMan"):trigger("Hanndl1") -- WG_NPC335.scr:59-60
    do return ctx:exit("") end -- WG_NPC335.scr:61
end

script.labels["OnKrohn1"] = function(ctx)
    -- WG_NPC335.scr:64
    ctx:self():playAnimation("Krohn01", "DoNothing") -- WG_NPC335.scr:67
    -- "Excellent.  They will hold..."
    ctx:wait(1, 4, "Hanndl2") -- WG_NPC335.scr:69
    do return ctx:exit("") end -- WG_NPC335.scr:70
end

script.labels["OnVoice1"] = function(ctx)
    -- WG_NPC335.scr:73
    ctx:playSound("voices\\cinema\\wingame\\Krohn01.wav", "DoNothing", 100, 240000, "FALSE", 100) -- WG_NPC335.scr:76
    do return ctx:exit("") end -- WG_NPC335.scr:77
end

script.labels["OnKrohn2"] = function(ctx)
    -- WG_NPC335.scr:80
    ctx:wait(1, 1, "Speak02") -- WG_NPC335.scr:82
    do return ctx:exit("") end -- WG_NPC335.scr:83
end

script.labels["Speak02"] = function(ctx)
    -- WG_NPC335.scr:86
    ctx:self():playAnimation("Krohn02", "DoNothing") -- WG_NPC335.scr:89
    -- "And What is it you wanted to say?"
    ctx:wait(1, 2, "Hanndl3") -- WG_NPC335.scr:91
    do return ctx:exit("") end -- WG_NPC335.scr:92
end

script.labels["OnVoice2"] = function(ctx)
    -- WG_NPC335.scr:95
    ctx:playSound("voices\\cinema\\wingame\\Krohn02.wav", "DoNothing", 100, 240000, "FALSE", 100) -- WG_NPC335.scr:98
    do return ctx:exit("") end -- WG_NPC335.scr:99
end

script.labels["OnKrohn3"] = function(ctx)
    -- WG_NPC335.scr:102
    ctx:wait(1, 1, "Speak03") -- WG_NPC335.scr:104
    do return ctx:exit("") end -- WG_NPC335.scr:105
end

script.labels["Speak03"] = function(ctx)
    -- WG_NPC335.scr:108
    ctx:self():playAnimation("Krohn03", "DoNothing") -- WG_NPC335.scr:111
    -- "You begin to overstep you lattitude..."
    ctx:wait(1, 3, "hanndl4") -- WG_NPC335.scr:113
    do return ctx:exit("") end -- WG_NPC335.scr:114
end

script.labels["OnVoice3"] = function(ctx)
    -- WG_NPC335.scr:117
    ctx:playSound("voices\\cinema\\wingame\\Krohn03.wav", "DoNothing", 100, 240000, "FALSE", 100) -- WG_NPC335.scr:120
    do return ctx:exit("") end -- WG_NPC335.scr:121
end

script.labels["OnKrohn4"] = function(ctx)
    -- WG_NPC335.scr:124
    ctx:wait(1, 3, "speak04") -- WG_NPC335.scr:127
    do return ctx:exit("") end -- WG_NPC335.scr:128
end

script.labels["Speak04"] = function(ctx)
    -- WG_NPC335.scr:131
    ctx:self():playAnimation("Krohn04", "DoNothing") -- WG_NPC335.scr:134
    -- "I think you've grown..."
    ctx:wait(1, 3, "Speak04b") -- WG_NPC335.scr:136
    do return ctx:exit("") end -- WG_NPC335.scr:137
end

script.labels["OnVoice4"] = function(ctx)
    -- WG_NPC335.scr:140
    ctx:playSound("voices\\cinema\\wingame\\Krohn04.wav", "DoNothing", 100, 240000, "FALSE", 100) -- WG_NPC335.scr:143
    do return ctx:exit("") end -- WG_NPC335.scr:144
end

script.labels["Speak04b"] = function(ctx)
    -- WG_NPC335.scr:147
    ctx:object("winman"):trigger("HanndlClose") -- WG_NPC335.scr:150-151
    ctx:wait(1, 2.5, "Speak04c") -- WG_NPC335.scr:152
    do return ctx:exit("") end -- WG_NPC335.scr:153
end

script.labels["Speak04c"] = function(ctx)
    -- WG_NPC335.scr:155
    ctx:object("winman"):trigger("KrohnClose") -- WG_NPC335.scr:159-160
    ctx:self():playAnimation("Krohn05", "DoNothing") -- WG_NPC335.scr:161
    -- "..Perhaps though you are right..."
    ctx:wait(1, 21, "Hanndl5") -- WG_NPC335.scr:163
    ctx:wait(2, 18.5, "KrohnEver") -- WG_NPC335.scr:164
    do return ctx:exit("") end -- WG_NPC335.scr:165
end

script.labels["OnVoice5"] = function(ctx)
    -- WG_NPC335.scr:168
    ctx:playSound("voices\\cinema\\wingame\\Krohn05.wav", "DoNothing", 100, 240000, "FALSE", 100) -- WG_NPC335.scr:171
    do return ctx:exit("") end -- WG_NPC335.scr:172
end

script.labels["KrohnEver"] = function(ctx)
    -- WG_NPC335.scr:176
    ctx:object("winman"):trigger("Ever") -- WG_NPC335.scr:179-180
    do return ctx:exit("") end -- WG_NPC335.scr:181
end

script.labels["OnKrohn5"] = function(ctx)
    -- WG_NPC335.scr:184
    -- PlayAnim Krohn06 DoNothing
    ctx:self():playAnimation("SC7_22_Krohn", "DoNothing") -- WG_NPC335.scr:189
    -- "The next time they return, gatekeeper..."
    ctx:wait(1, 4, "Hanndl6") -- WG_NPC335.scr:191
    do return ctx:exit("") end -- WG_NPC335.scr:192
end

script.labels["OnVoice6"] = function(ctx)
    -- WG_NPC335.scr:195
    ctx:playSound("voices\\cinema\\wingame\\Krohn06.wav", "DoNothing", 100, 240000, "FALSE", 100) -- WG_NPC335.scr:198
    do return ctx:exit("") end -- WG_NPC335.scr:199
end

script.labels["OnKrohn6"] = function(ctx)
    -- WG_NPC335.scr:203
    ctx:playSound("voices\\cinema\\wingame\\Krohn07.wav", "DoNothing", 100, 240000, "FALSE", 100) -- WG_NPC335.scr:206
    -- "It is their true Writ of Fate"
    ctx:wait(1, 5, "OnKrohn7") -- WG_NPC335.scr:208
    do return ctx:exit("") end -- WG_NPC335.scr:209
end

script.labels["OnKrohn7"] = function(ctx)
    -- WG_NPC335.scr:214
    ctx:object("winman"):trigger("End") -- WG_NPC335.scr:218-219
    do return ctx:exit("") end -- WG_NPC335.scr:220
end

script.labels["Hanndl2"] = function(ctx)
    -- WG_NPC335.scr:223
    ctx:object("WinMan"):trigger("Hanndl2") -- WG_NPC335.scr:226-227
    do return ctx:exit("") end -- WG_NPC335.scr:228
end

script.labels["Hanndl3"] = function(ctx)
    -- WG_NPC335.scr:232
    ctx:object("WinMan"):trigger("Hanndl3") -- WG_NPC335.scr:235-236
    do return ctx:exit("") end -- WG_NPC335.scr:237
end

script.labels["Hanndl4"] = function(ctx)
    -- WG_NPC335.scr:241
    ctx:object("WinMan"):trigger("Hanndl4") -- WG_NPC335.scr:244-245
    do return ctx:exit("") end -- WG_NPC335.scr:246
end

script.labels["Hanndl5"] = function(ctx)
    -- WG_NPC335.scr:249
    ctx:object("WinMan"):trigger("Hanndl5") -- WG_NPC335.scr:252-253
    do return ctx:exit("") end -- WG_NPC335.scr:254
end

script.labels["Hanndl6"] = function(ctx)
    -- WG_NPC335.scr:257
    ctx:object("WinMan"):trigger("Hanndl6") -- WG_NPC335.scr:260-261
    do return ctx:exit("") end -- WG_NPC335.scr:262
end

script.labels["Main"] = function(ctx)
    -- WG_NPC335.scr:265
    -- traceon
    -- Don't Forget to Delete this!
    mm9.gosub(script, ctx, "Loop") -- WG_NPC335.scr:271
    ctx:addTrigger("Arrive", "OnArrive") -- WG_NPC335.scr:272
    ctx:addTrigger("Start", "OnStart") -- WG_NPC335.scr:273
    ctx:addTrigger("Stop", "Loop") -- WG_NPC335.scr:274
    ctx:addTrigger("krohn1", "OnKrohn1") -- WG_NPC335.scr:275
    ctx:addTrigger("Krohn2", "OnKrohn2") -- WG_NPC335.scr:276
    ctx:addTrigger("krohn3", "OnKrohn3") -- WG_NPC335.scr:277
    ctx:addTrigger("Krohn4", "OnKrohn4") -- WG_NPC335.scr:278
    ctx:addTrigger("krohn5", "OnKrohn5") -- WG_NPC335.scr:279
    ctx:addTrigger("Krohn6", "OnKrohn6") -- WG_NPC335.scr:280
    ctx:addTrigger("krohn7", "OnKrohn7") -- WG_NPC335.scr:281
    ctx:addModelKey("Voice1", "OnVoice1") -- WG_NPC335.scr:283
    ctx:addModelKey("Voice2", "OnVoice2") -- WG_NPC335.scr:284
    ctx:addModelKey("Voice3", "OnVoice3") -- WG_NPC335.scr:285
    ctx:addModelKey("Voice4", "OnVoice4") -- WG_NPC335.scr:286
    ctx:addModelKey("Voice5", "OnVoice5") -- WG_NPC335.scr:287
    ctx:addModelKey("Voice6", "OnVoice6") -- WG_NPC335.scr:288
    -- AddModelKey Voice7 OnVoice7
    do return ctx:exit("") end -- WG_NPC335.scr:290
end

return script
