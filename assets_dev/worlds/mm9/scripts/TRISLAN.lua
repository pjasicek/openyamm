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
    ctx:self():setNumberProperty("DoRude", "False") -- TRISLAN.scr:29
    ctx:state().g_hobject = ctx:objectOrNil("abriel") -- TRISLAN.scr:30
    ctx:self():setTarget(ctx:object("g_hobject")) -- TRISLAN.scr:31
    ctx:state().g_hobject = ctx:objectOrNil("Trislan1") -- TRISLAN.scr:33
    ctx:self():walkTo(ctx:object("g_hobject"), 1, "Speak1") -- TRISLAN.scr:34
    do return ctx:exit("") end -- TRISLAN.scr:35
end

script.labels["Speak1"] = function(ctx)
    -- TRISLAN.scr:39
    ctx:wait(1, 4, "OnSpeak1") -- TRISLAN.scr:42
    do return ctx:exit("") end -- TRISLAN.scr:43
end

script.labels["OnSpeak1"] = function(ctx)
    -- TRISLAN.scr:46
    ctx:object("narrator"):trigger("stop") -- TRISLAN.scr:49-50
    ctx:self():loopAnimation("conv1", 0, "DoNothing") -- TRISLAN.scr:51
    ctx:playSound("voices\\cinema\\guberlandplay\\03.wav", "DoNothing", 100, 512, "FALSE", 100) -- TRISLAN.scr:52
    ctx:wait(1, 6, "Trigger4") -- TRISLAN.scr:53
    do return ctx:exit("") end -- TRISLAN.scr:54
end

script.labels["Trigger4"] = function(ctx)
    -- TRISLAN.scr:57
    ctx:self():stop() -- TRISLAN.scr:60
    ctx:self():loopAnimation("stand", 0, "DoNothing") -- TRISLAN.scr:61
    ctx:object("abriel"):trigger("Speak4") -- TRISLAN.scr:62-63
    do return ctx:exit("") end -- TRISLAN.scr:64
end

script.labels["OnSpeak5"] = function(ctx)
    -- TRISLAN.scr:67
    ctx:self():loopAnimation("conv3", 0, "DoNothing") -- TRISLAN.scr:70
    ctx:playSound("voices\\cinema\\guberlandplay\\05.wav", "DoNothing", 100, 512, "FALSE", 100) -- TRISLAN.scr:71
    ctx:wait(1, 4, "Trigger6") -- TRISLAN.scr:72
    do return ctx:exit("") end -- TRISLAN.scr:73
end

script.labels["Trigger6"] = function(ctx)
    -- TRISLAN.scr:76
    ctx:self():stop() -- TRISLAN.scr:79
    ctx:self():loopAnimation("stand", 0, "DoNothing") -- TRISLAN.scr:80
    ctx:object("abriel"):trigger("Speak6") -- TRISLAN.scr:81-82
    do return ctx:exit("") end -- TRISLAN.scr:83
end

script.labels["OnSpeak7"] = function(ctx)
    -- TRISLAN.scr:86
    ctx:self():loopAnimation("conv3", 0, "DoNothing") -- TRISLAN.scr:89
    ctx:playSound("voices\\cinema\\guberlandplay\\07.wav", "DoNothing", 100, 512, "FALSE", 100) -- TRISLAN.scr:90
    ctx:wait(1, 3, "Trigger8") -- TRISLAN.scr:91
    do return ctx:exit("") end -- TRISLAN.scr:92
end

script.labels["Trigger8"] = function(ctx)
    -- TRISLAN.scr:95
    ctx:self():stop() -- TRISLAN.scr:98
    ctx:self():loopAnimation("stand", 0, "DoNothing") -- TRISLAN.scr:99
    ctx:object("abriel"):trigger("Speak8") -- TRISLAN.scr:100-101
    do return ctx:exit("") end -- TRISLAN.scr:102
end

script.labels["OnExit"] = function(ctx)
    -- TRISLAN.scr:106
    ctx:self():setNumberProperty("DoRude", "TRUE") -- TRISLAN.scr:108
    ctx:self():setTarget(nil) -- TRISLAN.scr:109
    ctx:state().g_hobject = ctx:objectOrNil("Trislan2") -- TRISLAN.scr:110
    ctx:self():walkTo(ctx:object("g_hobject"), 1, "FaceStage") -- TRISLAN.scr:111
    do return ctx:exit("") end -- TRISLAN.scr:112
end

script.labels["FaceStage"] = function(ctx)
    -- TRISLAN.scr:115
    ctx:state().g_hobject = ctx:objectOrNil("Wilam") -- TRISLAN.scr:118
    ctx:self():setTarget(ctx:object("g_hobject")) -- TRISLAN.scr:119
    do return ctx:exit("") end -- TRISLAN.scr:120
end

script.labels["OnWalk2"] = function(ctx)
    -- TRISLAN.scr:123
    ctx:state().g_hobject = ctx:objectOrNil("Ralof") -- TRISLAN.scr:126
    ctx:self():setTarget(ctx:object("g_hobject")) -- TRISLAN.scr:127
    ctx:state().g_hobject = ctx:objectOrNil("Trislan1") -- TRISLAN.scr:128
    ctx:self():walkTo(ctx:object("g_hobject"), 1, "DoNothing") -- TRISLAN.scr:129
    do return ctx:exit("") end -- TRISLAN.scr:130
end

script.labels["OnSpeak23"] = function(ctx)
    -- TRISLAN.scr:133
    ctx:self():loopAnimation("conv2", 0, "DoNothing") -- TRISLAN.scr:136
    ctx:playSound("voices\\cinema\\guberlandplay\\23.wav", "DoNothing", 100, 512, "FALSE", 100) -- TRISLAN.scr:137
    ctx:wait(1, 3.4, "Trigger24") -- TRISLAN.scr:138
    do return ctx:exit("") end -- TRISLAN.scr:139
end

script.labels["Trigger24"] = function(ctx)
    -- TRISLAN.scr:142
    ctx:self():stop() -- TRISLAN.scr:145
    ctx:self():loopAnimation("stand", 0, "DoNothing") -- TRISLAN.scr:146
    ctx:object("Ralof"):trigger("Speak24") -- TRISLAN.scr:147-148
    do return ctx:exit("") end -- TRISLAN.scr:149
end

script.labels["OnSpeak25"] = function(ctx)
    -- TRISLAN.scr:152
    ctx:self():loopAnimation("conv2", 0, "DoNothing") -- TRISLAN.scr:155
    ctx:playSound("voices\\cinema\\guberlandplay\\25.wav", "DoNothing", 100, 512, "FALSE", 100) -- TRISLAN.scr:156
    ctx:wait(1, 4.5, "Trigger26") -- TRISLAN.scr:157
    do return ctx:exit("") end -- TRISLAN.scr:158
end

script.labels["Trigger26"] = function(ctx)
    -- TRISLAN.scr:161
    ctx:self():stop() -- TRISLAN.scr:164
    ctx:self():loopAnimation("stand", 0, "DoNothing") -- TRISLAN.scr:165
    ctx:object("Ralof"):trigger("Speak26") -- TRISLAN.scr:166-167
    do return ctx:exit("") end -- TRISLAN.scr:168
end

script.labels["OnDie"] = function(ctx)
    -- TRISLAN.scr:171
    -- Playanim Die1 DoNothing
    ctx:playSound("voices\\cinema\\guberlandplay\\27a.wav", "DoNothing", 100, 512, "FALSE", 100) -- TRISLAN.scr:176
    ctx:wait(1, 4, "Trigger27") -- TRISLAN.scr:177
    ctx:self():playAnimation("Play_Death", "GetUp") -- TRISLAN.scr:178
    do return ctx:exit("") end -- TRISLAN.scr:179
end

script.labels["GetUp"] = function(ctx)
    -- TRISLAN.scr:182
    ctx:self():playAnimation("Play_getup", "DoNothing") -- TRISLAN.scr:185
    do return ctx:exit("") end -- TRISLAN.scr:186
end

script.labels["Stop"] = function(ctx)
    -- TRISLAN.scr:189
    ctx:self():stop() -- TRISLAN.scr:192
    do return ctx:exit("") end -- TRISLAN.scr:193
end

script.labels["Trigger27"] = function(ctx)
    -- TRISLAN.scr:195
    -- stop
    -- Loopanim stand 0 DoNothing
    ctx:object("Narrator"):trigger("Speak27") -- TRISLAN.scr:200-201
    do return ctx:exit("") end -- TRISLAN.scr:202
end

script.labels["OnCastCall"] = function(ctx)
    -- TRISLAN.scr:205
    ctx:state().g_hobject = ctx:objectOrNil("Trislan3") -- TRISLAN.scr:210
    ctx:self():walkTo(ctx:object("g_hobject"), 1, "FaceDoor") -- TRISLAN.scr:211
    do return ctx:exit("") end -- TRISLAN.scr:212
end

script.labels["FaceDoor"] = function(ctx)
    -- TRISLAN.scr:215
    ctx:state().g_hobject = ctx:objectOrNil("peasant2") -- TRISLAN.scr:218
    ctx:self():setTarget(ctx:object("g_hobject")) -- TRISLAN.scr:219
    do return ctx:exit("") end -- TRISLAN.scr:220
end

script.labels["OnBow"] = function(ctx)
    -- TRISLAN.scr:223
    ctx:self():playAnimation("Bow", "DoNothing") -- TRISLAN.scr:226
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
