-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LEFFERY.scr"
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
    -- LEFFERY.scr:26
    ctx:self():setNumberProperty("DoRude", "False") -- LEFFERY.scr:28
    ctx:state().g_hobject = ctx:objectOrNil("Leffery1") -- LEFFERY.scr:29
    ctx:self():walkTo(ctx:object("g_hobject"), 2, "OnArrive") -- LEFFERY.scr:30
    do return ctx:exit("") end -- LEFFERY.scr:31
end

script.labels["OnArrive"] = function(ctx)
    -- LEFFERY.scr:34
    ctx:state().g_hobject = ctx:objectOrNil("ralof") -- LEFFERY.scr:38
    ctx:self():setTarget(ctx:object("g_hobject")) -- LEFFERY.scr:39
    do return ctx:exit("") end -- LEFFERY.scr:40
end

script.labels["OnSpeak12"] = function(ctx)
    -- LEFFERY.scr:43
    -- start speaking
    ctx:self():loopAnimation("conv2", 0, "DoNothing") -- LEFFERY.scr:47
    ctx:playSound("voices\\cinema\\guberlandplay\\12.wav", "DoNothing", 100, 512, "FALSE", 100) -- LEFFERY.scr:48
    ctx:wait(2, 1.3, "Trigger13") -- LEFFERY.scr:49
    do return ctx:exit("") end -- LEFFERY.scr:50
end

script.labels["Trigger13"] = function(ctx)
    -- LEFFERY.scr:53
    ctx:self():stop() -- LEFFERY.scr:56
    ctx:self():loopAnimation("stand", 0, "Donothing") -- LEFFERY.scr:57
    ctx:object("Ralof"):trigger("Speak13") -- LEFFERY.scr:58-59
    do return ctx:exit("") end -- LEFFERY.scr:60
end

script.labels["OnSpeak14"] = function(ctx)
    -- LEFFERY.scr:63
    -- start speaking
    ctx:self():loopAnimation("Aware", 0, "DoNothing") -- LEFFERY.scr:67
    ctx:playSound("voices\\cinema\\guberlandplay\\14.wav", "DoNothing", 100, 512, "FALSE", 100) -- LEFFERY.scr:68
    do return ctx:exit("") end -- LEFFERY.scr:70
end

script.labels["OnTarget"] = function(ctx)
    -- LEFFERY.scr:73
    ctx:getParam(0, "g_hobject") -- LEFFERY.scr:75
    ctx:self():setTarget(ctx:object("g_hobject")) -- LEFFERY.scr:76
    do return ctx:exit("") end -- LEFFERY.scr:77
end

script.labels["OnExit"] = function(ctx)
    -- LEFFERY.scr:80
    ctx:self():setNumberProperty("DoRude", "TRUE") -- LEFFERY.scr:82
    ctx:self():setTarget(nil) -- LEFFERY.scr:83
    ctx:state().g_hobject = ctx:objectOrNil("Leffery2") -- LEFFERY.scr:84
    ctx:self():walkTo(ctx:object("g_hobject"), 1, "FaceStage") -- LEFFERY.scr:85
    do return ctx:exit("") end -- LEFFERY.scr:86
end

script.labels["FaceStage"] = function(ctx)
    -- LEFFERY.scr:90
    ctx:state().g_hobject = ctx:objectOrNil("trislan") -- LEFFERY.scr:93
    ctx:self():setTarget(ctx:object("g_hobject")) -- LEFFERY.scr:94
    do return ctx:exit("") end -- LEFFERY.scr:95
end

script.labels["OnWalk2"] = function(ctx)
    -- LEFFERY.scr:98
    ctx:state().g_hobject = ctx:objectOrNil("trislan") -- LEFFERY.scr:100
    ctx:self():setTarget(ctx:object("g_hobject")) -- LEFFERY.scr:101
    ctx:state().g_hobject = ctx:objectOrNil("Wilam2") -- LEFFERY.scr:102
    ctx:self():walkTo(ctx:object("g_hobject"), 1, "DoNothing") -- LEFFERY.scr:103
    do return ctx:exit("") end -- LEFFERY.scr:104
end

script.labels["OnCastCall"] = function(ctx)
    -- LEFFERY.scr:109
    ctx:state().g_hobject = ctx:objectOrNil("Leffery3") -- LEFFERY.scr:112
    ctx:self():walkTo(ctx:object("g_hobject"), 1, "FaceDoor") -- LEFFERY.scr:113
    do return ctx:exit("") end -- LEFFERY.scr:114
end

script.labels["FaceDoor"] = function(ctx)
    -- LEFFERY.scr:117
    ctx:state().g_hobject = ctx:objectOrNil("peasant2") -- LEFFERY.scr:120
    ctx:self():setTarget(ctx:object("g_hobject")) -- LEFFERY.scr:121
    do return ctx:exit("") end -- LEFFERY.scr:122
end

script.labels["OnBow"] = function(ctx)
    -- LEFFERY.scr:125
    ctx:self():playAnimation("Bow", "DoNothing") -- LEFFERY.scr:128
    do return ctx:exit("") end -- LEFFERY.scr:129
end

script.labels["Main"] = function(ctx)
    -- LEFFERY.scr:132
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Start", "OnStart") -- LEFFERY.scr:137
    ctx:addTrigger("Speak12", "OnSpeak12") -- LEFFERY.scr:138
    ctx:addTrigger("speak14", "OnSpeak14") -- LEFFERY.scr:139
    ctx:addTrigger("target", "OnTarget") -- LEFFERY.scr:140
    ctx:addTrigger("Exit", "OnExit") -- LEFFERY.scr:141
    ctx:addTrigger("Walk2", "OnWalk2") -- LEFFERY.scr:142
    ctx:addTrigger("CastCall", "OnCastCall") -- LEFFERY.scr:143
    ctx:addTrigger("Bow", "OnBow") -- LEFFERY.scr:144
    do return ctx:exit("") end -- LEFFERY.scr:145
end

return script
