-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WILAM.scr"
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
    -- WILAM.scr:26
    ctx:self():setNumberProperty("DoRude", "False") -- WILAM.scr:28
    ctx:state().g_hobject = ctx:objectOrNil("Wilam1") -- WILAM.scr:29
    ctx:self():walkTo(ctx:object("g_hobject"), 2, "DoNothing") -- WILAM.scr:30
    do return ctx:exit("") end -- WILAM.scr:31
end

script.labels["OnSpeak9"] = function(ctx)
    -- WILAM.scr:34
    -- start speaking
    ctx:self():loopAnimation("conv2", 0, "DoNothing") -- WILAM.scr:38
    ctx:playSound("voices\\cinema\\guberlandplay\\10.wav", "DoNothing", 100, 512, "FALSE", 100) -- WILAM.scr:39
    ctx:wait(1, 1, "WalkTo") -- WILAM.scr:40
    ctx:wait(2, 6.4, "Trigger11") -- WILAM.scr:41
    do return ctx:exit("") end -- WILAM.scr:42
end

script.labels["Walkto"] = function(ctx)
    -- WILAM.scr:47
    ctx:self():blendAnimation("Conv1", "Donothing") -- WILAM.scr:49
    ctx:state().g_hobject = ctx:objectOrNil("Wilam2") -- WILAM.scr:50
    ctx:self():walkTo(ctx:object("g_hobject"), 1, "LoopAnim") -- WILAM.scr:51
    do return ctx:exit("") end -- WILAM.scr:52
end

script.labels["LoopAnim"] = function(ctx)
    -- WILAM.scr:55
    ctx:state().g_hobject = ctx:objectOrNil("ralof") -- WILAM.scr:58
    ctx:self():setTarget(ctx:object("g_hobject")) -- WILAM.scr:59
    ctx:wait(1, .1, "Animate") -- WILAM.scr:60
    do return ctx:exit("") end -- WILAM.scr:61
end

script.labels["Animate"] = function(ctx)
    -- WILAM.scr:64
    ctx:self():loopAnimation("conv3", 0, "DoNothing") -- WILAM.scr:66
    do return ctx:exit("") end -- WILAM.scr:67
end

script.labels["Trigger11"] = function(ctx)
    -- WILAM.scr:72
    ctx:self():stop() -- WILAM.scr:75
    ctx:self():loopAnimation("stand", 0, "DoNothing") -- WILAM.scr:76
    ctx:object("ralof"):trigger("speak11") -- WILAM.scr:77-78
    do return ctx:exit("") end -- WILAM.scr:79
end

script.labels["OnTarget"] = function(ctx)
    -- WILAM.scr:82
    ctx:getParam(0, "g_hobject") -- WILAM.scr:84
    ctx:self():setTarget(ctx:object("g_hobject")) -- WILAM.scr:85
    do return ctx:exit("") end -- WILAM.scr:86
end

script.labels["OnAttention"] = function(ctx)
    -- WILAM.scr:89
    ctx:self():stop() -- WILAM.scr:91
    ctx:self():loopAnimation("stand", 0, "DoNothing") -- WILAM.scr:92
    do return ctx:exit("") end -- WILAM.scr:93
end

script.labels["OnExit"] = function(ctx)
    -- WILAM.scr:97
    ctx:self():setNumberProperty("DoRude", "TRUE") -- WILAM.scr:99
    ctx:self():setTarget(nil) -- WILAM.scr:100
    ctx:state().g_hobject = ctx:objectOrNil("Wilam3") -- WILAM.scr:101
    ctx:self():walkTo(ctx:object("g_hobject"), 1, "FaceStage") -- WILAM.scr:102
    do return ctx:exit("") end -- WILAM.scr:103
end

script.labels["FaceStage"] = function(ctx)
    -- WILAM.scr:107
    ctx:state().g_hobject = ctx:objectOrNil("trislan") -- WILAM.scr:110
    ctx:self():setTarget(ctx:object("g_hobject")) -- WILAM.scr:111
    do return ctx:exit("") end -- WILAM.scr:112
end

script.labels["OnWalk2"] = function(ctx)
    -- WILAM.scr:116
    ctx:state().g_hobject = ctx:objectOrNil("trislan") -- WILAM.scr:118
    ctx:self():setTarget(ctx:object("g_hobject")) -- WILAM.scr:119
    ctx:state().g_hobject = ctx:objectOrNil("Ralof1") -- WILAM.scr:120
    ctx:self():walkTo(ctx:object("g_hobject"), 1, "DoNothing") -- WILAM.scr:121
    do return ctx:exit("") end -- WILAM.scr:122
end

script.labels["OnCastCall"] = function(ctx)
    -- WILAM.scr:125
    ctx:state().g_hobject = ctx:objectOrNil("Wilam4") -- WILAM.scr:128
    ctx:self():walkTo(ctx:object("g_hobject"), 1, "FaceDoor") -- WILAM.scr:129
    do return ctx:exit("") end -- WILAM.scr:130
end

script.labels["FaceDoor"] = function(ctx)
    -- WILAM.scr:133
    ctx:state().g_hobject = ctx:objectOrNil("peasant2") -- WILAM.scr:136
    ctx:self():setTarget(ctx:object("g_hobject")) -- WILAM.scr:137
    do return ctx:exit("") end -- WILAM.scr:138
end

script.labels["OnBow"] = function(ctx)
    -- WILAM.scr:141
    ctx:self():playAnimation("Bow", "DoNothing") -- WILAM.scr:144
    do return ctx:exit("") end -- WILAM.scr:145
end

script.labels["Main"] = function(ctx)
    -- WILAM.scr:148
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Start", "OnStart") -- WILAM.scr:153
    ctx:addTrigger("Speak9", "OnSpeak9") -- WILAM.scr:154
    ctx:addTrigger("target", "OnTarget") -- WILAM.scr:155
    ctx:addTrigger("Attention", "OnAttention") -- WILAM.scr:156
    ctx:addTrigger("Exit", "OnExit") -- WILAM.scr:157
    ctx:addTrigger("walk2", "OnWalk2") -- WILAM.scr:158
    ctx:addTrigger("CastCall", "OnCastCall") -- WILAM.scr:159
    ctx:addTrigger("Bow", "OnBow") -- WILAM.scr:160
    do return ctx:exit("") end -- WILAM.scr:161
end

return script
