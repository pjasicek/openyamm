-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC151.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "basewander.inc" }

-- NPC150.scr
-- timmy
-- handles Broccan A'Norta's speech
-- flag variables
script.labels["OnStop"] = function(ctx)
    -- NPC151.scr:19
    ctx:self():stop() -- NPC151.scr:21
    -- Loopanim stand 0 DoNothing
    do return ctx:exit("") end -- NPC151.scr:23
end

script.labels["OnSpeak2"] = function(ctx)
    -- NPC151.scr:26
    ctx:self():setNumberProperty("DoRude", "False") -- NPC151.scr:29
    ctx:self():loopAnimation("conv1", 0, "DoNothing") -- NPC151.scr:30
    ctx:playSound("voices\\cinema\\NewGame\\02.wav", "DoNothing", 100, 768, "FALSE", 100) -- NPC151.scr:31
    ctx:wait(1, .5, "Trigger3") -- NPC151.scr:32
    do return ctx:exit("") end -- NPC151.scr:33
end

script.labels["Trigger3"] = function(ctx)
    -- NPC151.scr:37
    mm9.gosub(script, ctx, "Onstop") -- NPC151.scr:40
    ctx:object("Scandlan"):trigger("Speak3") -- NPC151.scr:41-42
    do return ctx:exit("") end -- NPC151.scr:43
end

script.labels["OnSpeak4"] = function(ctx)
    -- NPC151.scr:47
    ctx:self():loopAnimation("conv1", 0, "DoNothing") -- NPC151.scr:50
    ctx:playSound("voices\\cinema\\NewGame\\04.wav", "DoNothing", 100, 768, "FALSE", 100) -- NPC151.scr:51
    ctx:wait(1, .5, "Trigger5") -- NPC151.scr:52
    do return ctx:exit("") end -- NPC151.scr:53
end

script.labels["Trigger5"] = function(ctx)
    -- NPC151.scr:57
    mm9.gosub(script, ctx, "Onstop") -- NPC151.scr:60
    ctx:object("Scandlan"):trigger("Speak5") -- NPC151.scr:61-62
    do return ctx:exit("") end -- NPC151.scr:63
end

script.labels["OnSpeak6"] = function(ctx)
    -- NPC151.scr:68
    ctx:self():loopAnimation("conv1", 0, "DoNothing") -- NPC151.scr:71
    ctx:playSound("voices\\cinema\\NewGame\\06.wav", "DoNothing", 100, 768, "FALSE", 100) -- NPC151.scr:72
    ctx:wait(1, 1, "Trigger7") -- NPC151.scr:73
    do return ctx:exit("") end -- NPC151.scr:74
end

script.labels["Trigger7"] = function(ctx)
    -- NPC151.scr:78
    mm9.gosub(script, ctx, "Onstop") -- NPC151.scr:81
    ctx:object("Scandlan"):trigger("Speak7") -- NPC151.scr:82-83
    do return ctx:exit("") end -- NPC151.scr:84
end

script.labels["OnSpeak8"] = function(ctx)
    -- NPC151.scr:87
    ctx:self():loopAnimation("conv1", 0, "DoNothing") -- NPC151.scr:90
    ctx:playSound("voices\\cinema\\NewGame\\08.wav", "DoNothing", 100, 768, "FALSE", 100) -- NPC151.scr:91
    ctx:wait(1, .5, "Trigger9") -- NPC151.scr:92
    do return ctx:exit("") end -- NPC151.scr:93
end

script.labels["Trigger9"] = function(ctx)
    -- NPC151.scr:97
    mm9.gosub(script, ctx, "Onstop") -- NPC151.scr:100
    ctx:object("Scandlan"):trigger("Speak9") -- NPC151.scr:101-102
    do return ctx:exit("") end -- NPC151.scr:103
end

script.labels["OnSpeak10"] = function(ctx)
    -- NPC151.scr:106
    ctx:self():loopAnimation("conv1", 0, "DoNothing") -- NPC151.scr:109
    ctx:playSound("voices\\cinema\\NewGame\\10.wav", "DoNothing", 100, 768, "FALSE", 100) -- NPC151.scr:110
    ctx:wait(1, 1, "Trigger11") -- NPC151.scr:111
    do return ctx:exit("") end -- NPC151.scr:112
end

script.labels["Trigger11"] = function(ctx)
    -- NPC151.scr:116
    mm9.gosub(script, ctx, "Onstop") -- NPC151.scr:119
    ctx:object("Scandlan"):trigger("Speak11") -- NPC151.scr:120-121
    do return ctx:exit("") end -- NPC151.scr:122
end

script.labels["OnWalkAway"] = function(ctx)
    -- NPC151.scr:125
    ctx:self():setNumberProperty("DoRude", "TRUE") -- NPC151.scr:127
    ctx:self():setTarget(nil) -- NPC151.scr:128
    ctx:state().g_hobject = ctx:objectOrNil("CommonerHalfOrcMaleA0") -- NPC151.scr:129
    ctx:self():walkTo(ctx:object("g_hobject"), 10, "OnWander") -- NPC151.scr:130
    do return ctx:exit("") end -- NPC151.scr:131
end

script.labels["OnWander"] = function(ctx)
    -- NPC151.scr:134
    if ctx:hasKey(5020) then -- NPC151.scr:137-138
        mm9.gosub(script, ctx, "BasewanderInit") -- NPC151.scr:139
        do return ctx:exit("") end -- NPC151.scr:140
    end -- NPC151.scr:141
    do return ctx:exit("") end -- NPC151.scr:142
end

script.labels["OnTarget"] = function(ctx)
    -- NPC151.scr:145
    ctx:self():setNumberProperty("DoRude", "False") -- NPC151.scr:147
    ctx:getParam(0, "g_hTarget") -- NPC151.scr:148
    ctx:self():setTarget(ctx:object("g_htarget")) -- NPC151.scr:149
    do return ctx:exit("") end -- NPC151.scr:150
end

script.labels["Main"] = function(ctx)
    -- NPC151.scr:153
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Speak2", "OnSpeak2") -- NPC151.scr:160
    ctx:addTrigger("Speak4", "OnSpeak4") -- NPC151.scr:161
    ctx:addTrigger("Speak6", "OnSpeak6") -- NPC151.scr:162
    ctx:addTrigger("Speak8", "OnSpeak8") -- NPC151.scr:163
    ctx:addTrigger("Speak10", "OnSpeak10") -- NPC151.scr:164
    ctx:addTrigger("Speak12", "OnWalkAway") -- NPC151.scr:165
    ctx:addTrigger("Target", "OnTarget") -- NPC151.scr:166
    mm9.gosub(script, ctx, "OnWander") -- NPC151.scr:167
    do return ctx:exit("") end -- NPC151.scr:168
end

return script
