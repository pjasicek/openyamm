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
    ctx:self():setNumberProperty("DoRude", "False") -- NARRATOR.scr:30
    ctx:object("curtain"):trigger("open") -- NARRATOR.scr:31-32
    ctx:wait(1, 2, "OnStart2") -- NARRATOR.scr:33
    do return ctx:exit("") end -- NARRATOR.scr:34
end

script.labels["OnStart2"] = function(ctx)
    -- NARRATOR.scr:38
    ctx:self():loopAnimation("conv2", 0, "DoNothing") -- NARRATOR.scr:40
    ctx:playSound("voices\\cinema\\guberlandplay\\01.wav", "DoNothing", 100, 512, "FALSE", 100) -- NARRATOR.scr:41
    ctx:wait(1, 6, "TriggerStart") -- NARRATOR.scr:42
    do return ctx:exit("") end -- NARRATOR.scr:43
end

script.labels["TriggerStart"] = function(ctx)
    -- NARRATOR.scr:47
    ctx:object("Trislan"):trigger("Walk1") -- NARRATOR.scr:52-53
    ctx:object("Abriel"):trigger("Walk1") -- NARRATOR.scr:55-56
    ctx:self():loopAnimation("conv3", 0, "DoNothing") -- NARRATOR.scr:58
    ctx:playSound("voices\\cinema\\guberlandplay\\02.wav", "DoNothing", 100, 512, "FALSE", 100) -- NARRATOR.scr:59
    ctx:state().g_hobject = ctx:objectOrNil("Abriel1") -- NARRATOR.scr:61
    ctx:self():faceObject(ctx:object("g_hobject"), 200, "DoNothing") -- NARRATOR.scr:62
    do return ctx:exit("") end -- NARRATOR.scr:63
end

script.labels["OnSpeak9"] = function(ctx)
    -- NARRATOR.scr:66
    ctx:object("Abriel"):trigger("Exit") -- NARRATOR.scr:69-70
    ctx:object("Trislan"):trigger("Exit") -- NARRATOR.scr:71-72
    ctx:object("Leffery"):trigger("Start") -- NARRATOR.scr:75-76
    ctx:object("Ralof"):trigger("Start") -- NARRATOR.scr:77-78
    ctx:object("Wilam"):trigger("Start") -- NARRATOR.scr:79-80
    ctx:self():loopAnimation("conv3", 0, "DoNothing") -- NARRATOR.scr:82
    ctx:playSound("voices\\cinema\\guberlandplay\\09.wav", "DoNothing", 100, 512, "FALSE", 100) -- NARRATOR.scr:83
    ctx:wait(1, 4, "Trigger9") -- NARRATOR.scr:84
    do return ctx:exit("") end -- NARRATOR.scr:85
end

script.labels["Trigger9"] = function(ctx)
    -- NARRATOR.scr:88
    mm9.gosub(script, ctx, "Onstop") -- NARRATOR.scr:91
    ctx:object("Wilam"):trigger("Speak9") -- NARRATOR.scr:92-93
    do return ctx:exit("") end -- NARRATOR.scr:94
end

script.labels["OnStop"] = function(ctx)
    -- NARRATOR.scr:97
    ctx:self():stop() -- NARRATOR.scr:99
    ctx:self():loopAnimation("stand", 0, "DoNothing") -- NARRATOR.scr:100
    do return ctx:exit("") end -- NARRATOR.scr:101
end

script.labels["OnSpeak21"] = function(ctx)
    -- NARRATOR.scr:105
    ctx:self():loopAnimation("conv1", 0, "DoNothing") -- NARRATOR.scr:108
    ctx:playSound("voices\\cinema\\guberlandplay\\21.wav", "DoNothing", 100, 512, "FALSE", 100) -- NARRATOR.scr:109
    ctx:wait(1, 4, "Trigger22") -- NARRATOR.scr:110
    do return ctx:exit("") end -- NARRATOR.scr:111
end

script.labels["Trigger22"] = function(ctx)
    -- NARRATOR.scr:116
    ctx:self():stop() -- NARRATOR.scr:119
    ctx:self():loopAnimation("stand", 0, "DoNothing") -- NARRATOR.scr:120
    ctx:object("Abriel"):trigger("exit") -- NARRATOR.scr:121-122
    ctx:object("Ralof"):trigger("exit") -- NARRATOR.scr:123-124
    ctx:object("Wilam"):trigger("exit") -- NARRATOR.scr:125-126
    ctx:object("Leffery"):trigger("exit") -- NARRATOR.scr:127-128
    do return ctx:exit("") end -- NARRATOR.scr:129
end

script.labels["OnSpeak22"] = function(ctx)
    -- NARRATOR.scr:132
    ctx:object("Trislan"):trigger("Walk2") -- NARRATOR.scr:135-136
    ctx:self():loopAnimation("conv1", 0, "DoNothing") -- NARRATOR.scr:137
    ctx:playSound("voices\\cinema\\guberlandplay\\22.wav", "DoNothing", 100, 512, "FALSE", 100) -- NARRATOR.scr:138
    ctx:wait(2, 1, "Abrielwalk") -- NARRATOR.scr:139
    ctx:wait(1, 5.5, "Trigger23") -- NARRATOR.scr:140
    do return ctx:exit("") end -- NARRATOR.scr:141
end

script.labels["Abrielwalk"] = function(ctx)
    -- NARRATOR.scr:144
    ctx:object("Abriel"):trigger("Walk2") -- NARRATOR.scr:147-148
    do return ctx:exit("") end -- NARRATOR.scr:149
end

script.labels["Trigger23"] = function(ctx)
    -- NARRATOR.scr:152
    ctx:object("ralof"):trigger("Walk2") -- NARRATOR.scr:155-156
    ctx:wait(1, 1, "GuardWalk") -- NARRATOR.scr:157
    do return ctx:exit("") end -- NARRATOR.scr:158
end

script.labels["Guardwalk"] = function(ctx)
    -- NARRATOR.scr:161
    ctx:object("Leffery"):trigger("Walk2") -- NARRATOR.scr:163-164
    ctx:object("Wilam"):trigger("Walk2") -- NARRATOR.scr:165-166
    do return ctx:exit("") end -- NARRATOR.scr:167
end

script.labels["OnSpeak27"] = function(ctx)
    -- NARRATOR.scr:170
    ctx:state().g_hobject = ctx:objectOrNil("peasant2") -- NARRATOR.scr:173
    ctx:self():setTarget(ctx:object("g_hobject")) -- NARRATOR.scr:174
    ctx:self():loopAnimation("conv3", 0, "DoNothing") -- NARRATOR.scr:175
    ctx:playSound("voices\\cinema\\guberlandplay\\27.wav", "DoNothing", 100, 512, "FALSE", 100) -- NARRATOR.scr:176
    ctx:wait(1, 13, "Trigger28") -- NARRATOR.scr:177
    do return ctx:exit("") end -- NARRATOR.scr:178
end

script.labels["Trigger28"] = function(ctx)
    -- NARRATOR.scr:181
    ctx:object("Ralof"):trigger("CastCall") -- NARRATOR.scr:184-185
    ctx:object("Wilam"):trigger("CastCall") -- NARRATOR.scr:186-187
    ctx:object("Leffery"):trigger("CastCall") -- NARRATOR.scr:188-189
    ctx:object("Abriel"):trigger("CastCall") -- NARRATOR.scr:190-191
    ctx:object("Trislan"):trigger("CastCall") -- NARRATOR.scr:192-193
    ctx:wait(1, 3, "Bow") -- NARRATOR.scr:194
    do return ctx:exit("") end -- NARRATOR.scr:195
end

script.labels["Bow"] = function(ctx)
    -- NARRATOR.scr:199
    ctx:self():loopAnimation("conv3", 0, "DoNothing") -- NARRATOR.scr:203
    ctx:playSound("voices\\cinema\\guberlandplay\\28.wav", "DoNothing", 100, 512, "FALSE", 100) -- NARRATOR.scr:204
    ctx:wait(1, 1, "OnBow") -- NARRATOR.scr:205
    do return ctx:exit("") end -- NARRATOR.scr:206
end

script.labels["OnBow"] = function(ctx)
    -- NARRATOR.scr:209
    ctx:self():stop() -- NARRATOR.scr:212
    ctx:self():loopAnimation("stand", 0, "DoNothing") -- NARRATOR.scr:213
    ctx:object("Ralof"):trigger("Bow") -- NARRATOR.scr:214-215
    ctx:object("Wilam"):trigger("Bow") -- NARRATOR.scr:216-217
    ctx:object("Leffery"):trigger("Bow") -- NARRATOR.scr:218-219
    ctx:object("Abriel"):trigger("Bow") -- NARRATOR.scr:220-221
    ctx:object("Trislan"):trigger("Bow") -- NARRATOR.scr:222-223
    ctx:wait(1, 5, "Exit") -- NARRATOR.scr:224
    do return ctx:exit("") end -- NARRATOR.scr:225
end

script.labels["Exit"] = function(ctx)
    -- NARRATOR.scr:228
    ctx:object("curtain"):trigger("close") -- NARRATOR.scr:230-231
    ctx:object("Ralof"):trigger("Exit") -- NARRATOR.scr:232-233
    ctx:object("Wilam"):trigger("Exit") -- NARRATOR.scr:234-235
    ctx:object("Leffery"):trigger("Exit") -- NARRATOR.scr:236-237
    ctx:object("Abriel"):trigger("Exit") -- NARRATOR.scr:238-239
    ctx:object("Trislan"):trigger("Exit") -- NARRATOR.scr:240-241
    ctx:self():setNumberProperty("DoRude", "TRUE") -- NARRATOR.scr:242
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
    ctx:atTime(14, 30, "OnStart") -- NARRATOR.scr:257
    ctx:atTime(16, 30, "OnStart") -- NARRATOR.scr:258
    do return ctx:exit("") end -- NARRATOR.scr:259
end

return script
