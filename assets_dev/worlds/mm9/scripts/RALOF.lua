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
    ctx:self():setNumberProperty("DoRude", "False") -- RALOF.scr:28
    ctx:state().g_hobject = ctx:objectOrNil("Ralof1") -- RALOF.scr:29
    ctx:self():walkTo(ctx:object("g_hobject"), 1, "OnArrive") -- RALOF.scr:30
    do return ctx:exit("") end -- RALOF.scr:31
end

script.labels["OnArrive"] = function(ctx)
    -- RALOF.scr:34
    ctx:state().g_hobject = ctx:objectOrNil("Wilam") -- RALOF.scr:38
    ctx:self():setTarget(ctx:object("g_hobject")) -- RALOF.scr:39
    do return ctx:exit("") end -- RALOF.scr:40
end

script.labels["OnSpeak11"] = function(ctx)
    -- RALOF.scr:43
    -- start speaking
    ctx:self():loopAnimation("conv1", 0, "DoNothing") -- RALOF.scr:47
    ctx:playSound("voices\\cinema\\guberlandplay\\11.wav", "DoNothing", 100, 512, "FALSE", 100) -- RALOF.scr:48
    ctx:wait(2, 9.3, "Trigger12") -- RALOF.scr:49
    do return ctx:exit("") end -- RALOF.scr:50
end

script.labels["Trigger12"] = function(ctx)
    -- RALOF.scr:53
    ctx:self():stop() -- RALOF.scr:56
    ctx:self():loopAnimation("stand", 0, "Donothing") -- RALOF.scr:57
    ctx:object("Leffery"):trigger("Speak12") -- RALOF.scr:58-59
    do return ctx:exit("") end -- RALOF.scr:60
end

script.labels["OnSpeak13"] = function(ctx)
    -- RALOF.scr:63
    -- start speaking
    ctx:state().g_hobject = ctx:objectOrNil("leffery") -- RALOF.scr:67
    ctx:self():setTarget(ctx:object("g_hobject")) -- RALOF.scr:68
    ctx:self():loopAnimation("conv1", 0, "DoNothing") -- RALOF.scr:69
    ctx:playSound("voices\\cinema\\guberlandplay\\13b.wav", "DoNothing", 100, 512, "FALSE", 100) -- RALOF.scr:70
    ctx:wait(1, 5, "FaceWilam") -- RALOF.scr:71
    ctx:wait(2, 20, "Trigger14") -- RALOF.scr:72
    do return ctx:exit("") end -- RALOF.scr:73
end

script.labels["FaceWilam"] = function(ctx)
    -- RALOF.scr:76
    ctx:self():stop() -- RALOF.scr:79
    ctx:state().g_hobject = ctx:objectOrNil("Wilam") -- RALOF.scr:80
    ctx:self():setTarget(ctx:object("g_hobject")) -- RALOF.scr:81
    ctx:wait(1, .1, "converse") -- RALOF.scr:82
    do return ctx:exit("") end -- RALOF.scr:83
end

script.labels["converse"] = function(ctx)
    -- RALOF.scr:86
    ctx:self():loopAnimation("conv2", 0, "DoNothing") -- RALOF.scr:88
    do return ctx:exit("") end -- RALOF.scr:89
end

script.labels["Trigger14"] = function(ctx)
    -- RALOF.scr:92
    ctx:self():stop() -- RALOF.scr:95
    ctx:self():loopAnimation("stand", 0, "Donothing") -- RALOF.scr:96
    ctx:object("Leffery"):trigger("Speak14") -- RALOF.scr:97-98
    ctx:state().g_hobject = ctx:objectOrNil("abriel") -- RALOF.scr:99
    ctx:self():setTarget(ctx:object("g_hobject")) -- RALOF.scr:100
    ctx:trigger("g_hobject", "Speak14") -- RALOF.scr:101
    ctx:object("wilam"):trigger("attention") -- RALOF.scr:102-103
    do return ctx:exit("") end -- RALOF.scr:104
end

script.labels["OnSpeak16"] = function(ctx)
    -- RALOF.scr:107
    -- start speaking
    -- LoopAnim conv1 0 DoNothing
    ctx:playSound("voices\\cinema\\guberlandplay\\16.wav", "DoNothing", 100, 512, "FALSE", 100) -- RALOF.scr:112
    ctx:wait(2, 1.5, "Trigger17") -- RALOF.scr:113
    do return ctx:exit("") end -- RALOF.scr:114
end

script.labels["Trigger17"] = function(ctx)
    -- RALOF.scr:117
    ctx:self():stop() -- RALOF.scr:120
    ctx:self():loopAnimation("stand", 0, "Donothing") -- RALOF.scr:121
    ctx:object("Abriel"):trigger("Speak17") -- RALOF.scr:122-123
    do return ctx:exit("") end -- RALOF.scr:124
end

script.labels["OnSpeak18"] = function(ctx)
    -- RALOF.scr:128
    -- start speaking
    -- LoopAnim conv1 0 DoNothing
    ctx:playSound("voices\\cinema\\guberlandplay\\18.wav", "DoNothing", 100, 512, "FALSE", 100) -- RALOF.scr:133
    ctx:wait(2, 1.5, "Trigger19") -- RALOF.scr:134
    do return ctx:exit("") end -- RALOF.scr:135
end

script.labels["Trigger19"] = function(ctx)
    -- RALOF.scr:138
    ctx:self():stop() -- RALOF.scr:141
    ctx:self():loopAnimation("stand", 0, "Donothing") -- RALOF.scr:142
    ctx:object("Abriel"):trigger("Speak19") -- RALOF.scr:143-144
    do return ctx:exit("") end -- RALOF.scr:145
end

script.labels["OnSpeak20"] = function(ctx)
    -- RALOF.scr:148
    -- start speaking
    ctx:self():loopAnimation("conv1", 0, "DoNothing") -- RALOF.scr:152
    ctx:playSound("voices\\cinema\\guberlandplay\\20.wav", "DoNothing", 100, 512, "FALSE", 100) -- RALOF.scr:153
    ctx:wait(2, 3.5, "Trigger21") -- RALOF.scr:154
    do return ctx:exit("") end -- RALOF.scr:155
end

script.labels["Trigger21"] = function(ctx)
    -- RALOF.scr:158
    ctx:self():stop() -- RALOF.scr:161
    ctx:self():loopAnimation("stand", 0, "Donothing") -- RALOF.scr:162
    ctx:object("Narrator"):trigger("Speak21") -- RALOF.scr:163-164
    do return ctx:exit("") end -- RALOF.scr:165
end

script.labels["OnExit"] = function(ctx)
    -- RALOF.scr:168
    ctx:self():setNumberProperty("DoRude", "TRUE") -- RALOF.scr:170
    ctx:self():setTarget(nil) -- RALOF.scr:171
    ctx:state().g_hobject = ctx:objectOrNil("Ralof2") -- RALOF.scr:172
    ctx:self():walkTo(ctx:object("g_hobject"), 1, "FaceStage") -- RALOF.scr:173
    do return ctx:exit("") end -- RALOF.scr:174
end

script.labels["FaceStage"] = function(ctx)
    -- RALOF.scr:178
    ctx:state().g_hobject = ctx:objectOrNil("trislan") -- RALOF.scr:181
    ctx:self():setTarget(ctx:object("g_hobject")) -- RALOF.scr:182
    do return ctx:exit("") end -- RALOF.scr:183
end

script.labels["OnWalk2"] = function(ctx)
    -- RALOF.scr:187
    ctx:state().g_hobject = ctx:objectOrNil("trislan") -- RALOF.scr:189
    ctx:self():setTarget(ctx:object("g_hobject")) -- RALOF.scr:190
    ctx:self():walkTo(ctx:object("g_hobject"), 1, "Trigger23") -- RALOF.scr:191
    do return ctx:exit("") end -- RALOF.scr:192
end

script.labels["Trigger23"] = function(ctx)
    -- RALOF.scr:195
    ctx:self():stop() -- RALOF.scr:198
    ctx:self():loopAnimation("stand", 0, "Donothing") -- RALOF.scr:199
    ctx:object("Trislan"):trigger("Speak23") -- RALOF.scr:200-201
    do return ctx:exit("") end -- RALOF.scr:202
end

script.labels["OnSpeak24"] = function(ctx)
    -- RALOF.scr:206
    -- start speaking
    ctx:self():loopAnimation("conv4", 0, "DoNothing") -- RALOF.scr:210
    ctx:playSound("voices\\cinema\\guberlandplay\\24.wav", "DoNothing", 100, 512, "FALSE", 100) -- RALOF.scr:211
    ctx:wait(2, 5.4, "Trigger25") -- RALOF.scr:212
    do return ctx:exit("") end -- RALOF.scr:213
end

script.labels["Trigger25"] = function(ctx)
    -- RALOF.scr:216
    ctx:self():stop() -- RALOF.scr:219
    ctx:self():loopAnimation("stand", 0, "Donothing") -- RALOF.scr:220
    ctx:object("Trislan"):trigger("Speak25") -- RALOF.scr:221-222
    do return ctx:exit("") end -- RALOF.scr:223
end

script.labels["OnSpeak26"] = function(ctx)
    -- RALOF.scr:226
    -- start speaking
    ctx:self():loopAnimation("conv3", 0, "DoNothing") -- RALOF.scr:230
    ctx:playSound("voices\\cinema\\guberlandplay\\26.wav", "DoNothing", 100, 512, "FALSE", 100) -- RALOF.scr:231
    ctx:wait(2, 3.4, "Attack") -- RALOF.scr:232
    do return ctx:exit("") end -- RALOF.scr:233
end

script.labels["Attack"] = function(ctx)
    -- RALOF.scr:236
    ctx:self():attack("OnStop") -- RALOF.scr:239
    ctx:wait(1, .75, "Slapsound") -- RALOF.scr:240
    do return ctx:exit("") end -- RALOF.scr:242
end

script.labels["Slapsound"] = function(ctx)
    -- RALOF.scr:245
    ctx:playSound("Sounds\\Weapons\\FleshHit04.wav", "DoNothing", 100, 512, "FALSE", 100) -- RALOF.scr:248
    do return ctx:exit("") end -- RALOF.scr:249
end

script.labels["OnStop"] = function(ctx)
    -- RALOF.scr:252
    ctx:self():stop() -- RALOF.scr:255
    ctx:self():loopAnimation("stand", 0, "Donothing") -- RALOF.scr:256
    ctx:object("Trislan"):trigger("Die") -- RALOF.scr:257-258
    do return ctx:exit("") end -- RALOF.scr:259
end

script.labels["OnCastCall"] = function(ctx)
    -- RALOF.scr:262
    ctx:state().g_hobject = ctx:objectOrNil("Ralof3") -- RALOF.scr:265
    ctx:self():walkTo(ctx:object("g_hobject"), 1, "FaceDoor") -- RALOF.scr:266
    do return ctx:exit("") end -- RALOF.scr:267
end

script.labels["FaceDoor"] = function(ctx)
    -- RALOF.scr:270
    ctx:state().g_hobject = ctx:objectOrNil("peasant2") -- RALOF.scr:273
    ctx:self():setTarget(ctx:object("g_hobject")) -- RALOF.scr:274
    do return ctx:exit("") end -- RALOF.scr:275
end

script.labels["OnBow"] = function(ctx)
    -- RALOF.scr:278
    ctx:self():playAnimation("Bow", "DoNothing") -- RALOF.scr:281
    do return ctx:exit("") end -- RALOF.scr:282
end

script.labels["OnWince"] = function(ctx)
    -- RALOF.scr:285
    ctx:self():playAnimation("Wince1", "DoNothing") -- RALOF.scr:288
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
