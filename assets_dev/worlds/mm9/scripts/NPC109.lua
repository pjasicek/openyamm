-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC109.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "basemelee.inc" }

-- NPC109.scr
-- timmy
-- handles Alfrigg's speech
-- flag variables
script.labels["OnStop"] = function(ctx)
    -- NPC109.scr:21
    ctx:self():stop() -- NPC109.scr:23
    ctx:self():loopAnimation("stand", 0, "DoNothing") -- NPC109.scr:24
    do return ctx:exit("") end -- NPC109.scr:25
end

script.labels["OnSpeak2"] = function(ctx)
    -- NPC109.scr:28
    if ctx:condition("bTargetDead==TRUE") then -- NPC109.scr:31
        do return ctx:exit("") end -- NPC109.scr:32
    end -- NPC109.scr:33
    ctx:self():setNumberProperty("DoRude", "False") -- NPC109.scr:34
    ctx:self():loopAnimation("conv1", 0, "DoNothing") -- NPC109.scr:35
    ctx:playSound("voices\\cinema\\dwarvesandhumans\\02.wav", "DoNothing", 100, 2400, "FALSE", 100) -- NPC109.scr:36
    ctx:wait(1, 7.3, "Trigger3") -- NPC109.scr:37
    do return ctx:exit("") end -- NPC109.scr:38
end

script.labels["Trigger3"] = function(ctx)
    -- NPC109.scr:42
    mm9.gosub(script, ctx, "Onstop") -- NPC109.scr:45
    ctx:object("Hrolf"):trigger("Speak3") -- NPC109.scr:46-47
    do return ctx:exit("") end -- NPC109.scr:48
end

script.labels["OnSpeak4"] = function(ctx)
    -- NPC109.scr:52
    if ctx:condition("bTargetDead==TRUE") then -- NPC109.scr:55
        do return ctx:exit("") end -- NPC109.scr:56
    end -- NPC109.scr:57
    ctx:self():loopAnimation("conv1", 0, "DoNothing") -- NPC109.scr:58
    ctx:playSound("voices\\cinema\\dwarvesandhumans\\04c.wav", "DoNothing", 100, 2400, "FALSE", 100) -- NPC109.scr:59
    ctx:wait(1, 3.2, "Trigger5") -- NPC109.scr:60
    do return ctx:exit("") end -- NPC109.scr:61
end

script.labels["Trigger5"] = function(ctx)
    -- NPC109.scr:65
    mm9.gosub(script, ctx, "Onstop") -- NPC109.scr:68
    ctx:object("Hrolf"):trigger("Speak5") -- NPC109.scr:69-70
    do return ctx:exit("") end -- NPC109.scr:71
end

script.labels["OnSpeak6"] = function(ctx)
    -- NPC109.scr:76
    if ctx:condition("bTargetDead==TRUE") then -- NPC109.scr:78
        do return ctx:exit("") end -- NPC109.scr:79
    end -- NPC109.scr:80
    ctx:self():loopAnimation("conv1", 0, "DoNothing") -- NPC109.scr:81
    ctx:playSound("voices\\cinema\\dwarvesandhumans\\06.wav", "DoNothing", 100, 2400, "FALSE", 100) -- NPC109.scr:82
    ctx:wait(1, 1, "Trigger7") -- NPC109.scr:83
    do return ctx:exit("") end -- NPC109.scr:84
end

script.labels["Trigger7"] = function(ctx)
    -- NPC109.scr:88
    mm9.gosub(script, ctx, "Onstop") -- NPC109.scr:91
    ctx:object("Hrolf"):trigger("Speak7") -- NPC109.scr:92-93
    do return ctx:exit("") end -- NPC109.scr:94
end

script.labels["OnFight"] = function(ctx)
    -- NPC109.scr:98
    ctx:state().g_hobject = ctx:objectOrNil("Hrolf") -- NPC109.scr:101
    ctx:self():setTarget(ctx:object("g_hobject")) -- NPC109.scr:102
    ctx:self():addEnemy("commonerhuman2maleB") -- NPC109.scr:103
    mm9.gosub(script, ctx, "baseinit") -- NPC109.scr:104
    do return ctx:exit("") end -- NPC109.scr:105
end

script.labels["OnTargetDead"] = function(ctx)
    -- NPC109.scr:108
    ctx:self():setNumberProperty("DoRude", "True") -- NPC109.scr:110
    ctx:self():removeEnemy("commonerhuman2maleB") -- NPC109.scr:111
    ctx:state().bTargetDead = true -- NPC109.scr:112
    ctx:exitScript() -- NPC109.scr:113
    do return ctx:exit("TRUE") end -- NPC109.scr:115
end

script.labels["OnTarget"] = function(ctx)
    -- NPC109.scr:119
    ctx:getParam(0, "g_hTarget") -- NPC109.scr:122
    ctx:self():setTarget(ctx:object("g_htarget")) -- NPC109.scr:123
    do return ctx:exit("") end -- NPC109.scr:124
end

script.labels["OnLost"] = function(ctx)
    -- NPC109.scr:127
    do return ctx:exit("TRUE") end -- NPC109.scr:130
end

script.labels["Main"] = function(ctx)
    -- NPC109.scr:134
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onEvent("OnLostTarget", "ONLost") -- NPC109.scr:139
    ctx:addTrigger("Speak2", "OnSpeak2") -- NPC109.scr:141
    ctx:addTrigger("Speak4", "OnSpeak4") -- NPC109.scr:142
    ctx:addTrigger("Speak6", "OnSpeak6") -- NPC109.scr:143
    ctx:addTrigger("Fight", "OnFight") -- NPC109.scr:144
    ctx:addTrigger("Target", "OnTarget") -- NPC109.scr:145
    do return ctx:exit("") end -- NPC109.scr:147
end

return script
