-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC110.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "basemelee.inc" }

-- NPC110.scr
-- timmy
-- handles Hrolf Anfarssen's speech
-- flag variables
script.labels["OnStart"] = function(ctx)
    -- NPC110.scr:25
    if ctx:condition("bTargetDead==TRUE") then -- NPC110.scr:29
        do return ctx:exit("") end -- NPC110.scr:30
    end -- NPC110.scr:31
    ctx:self():setNumberProperty("DoRude", "False") -- NPC110.scr:33
    ctx:hasKey(5010, "bSpeak") -- NPC110.scr:35
    if ctx:condition("bSpeak==TRUE") then -- NPC110.scr:36
        do return ctx:exit("") end -- NPC110.scr:37
    end -- NPC110.scr:38
    ctx:state().g_hobject = ctx:objectOrNil("Alfrigg") -- NPC110.scr:40
    ctx:self():setTarget(ctx:object("g_hobject")) -- NPC110.scr:41
    ctx:trigger("g_hobject", "Target") -- NPC110.scr:42
    ctx:giveKey(5010) -- NPC110.scr:44
    ctx:self():loopAnimation("conv2", 0, "DoNothing") -- NPC110.scr:45
    ctx:playSound("\\voices\\cinema\\dwarvesandhumans\\01.wav", "DoNothing", 100, 2400, "FALSE", 100) -- NPC110.scr:46
    ctx:wait(1, 5.5, "Trigger2") -- NPC110.scr:47
    do return ctx:exit("") end -- NPC110.scr:48
end

script.labels["Trigger2"] = function(ctx)
    -- NPC110.scr:52
    mm9.gosub(script, ctx, "Onstop") -- NPC110.scr:55
    ctx:object("Alfrigg"):trigger("Speak2") -- NPC110.scr:56-57
    do return ctx:exit("") end -- NPC110.scr:58
end

script.labels["OnSpeak3"] = function(ctx)
    -- NPC110.scr:62
    if ctx:condition("bTargetDead==TRUE") then -- NPC110.scr:64
        do return ctx:exit("") end -- NPC110.scr:65
    end -- NPC110.scr:66
    ctx:self():loopAnimation("conv2", 0, "DoNothing") -- NPC110.scr:67
    ctx:playSound("voices\\cinema\\dwarvesandhumans\\03.wav", "DoNothing", 100, 2400, "FALSE", 100) -- NPC110.scr:68
    ctx:wait(1, 13.3, "Trigger4") -- NPC110.scr:69
    do return ctx:exit("") end -- NPC110.scr:70
end

script.labels["Trigger4"] = function(ctx)
    -- NPC110.scr:74
    mm9.gosub(script, ctx, "Onstop") -- NPC110.scr:77
    ctx:object("Alfrigg"):trigger("Speak4") -- NPC110.scr:78-79
    do return ctx:exit("") end -- NPC110.scr:80
end

script.labels["OnSpeak5"] = function(ctx)
    -- NPC110.scr:84
    if ctx:condition("bTargetDead==TRUE") then -- NPC110.scr:86
        do return ctx:exit("") end -- NPC110.scr:87
    end -- NPC110.scr:88
    ctx:self():loopAnimation("conv5", 0, "DoNothing") -- NPC110.scr:89
    ctx:playSound("voices\\cinema\\dwarvesandhumans\\05.wav", "DoNothing", 100, 2400, "FALSE", 100) -- NPC110.scr:90
    ctx:wait(1, 4.5, "Trigger6") -- NPC110.scr:91
    do return ctx:exit("") end -- NPC110.scr:92
end

script.labels["Trigger6"] = function(ctx)
    -- NPC110.scr:96
    mm9.gosub(script, ctx, "Onstop") -- NPC110.scr:99
    ctx:object("Alfrigg"):trigger("Speak6") -- NPC110.scr:100-101
    do return ctx:exit("") end -- NPC110.scr:102
end

script.labels["OnSpeak7"] = function(ctx)
    -- NPC110.scr:106
    if ctx:condition("bTargetDead==TRUE") then -- NPC110.scr:108
        do return ctx:exit("") end -- NPC110.scr:109
    end -- NPC110.scr:110
    ctx:self():loopAnimation("conv4", 0, "DoNothing") -- NPC110.scr:111
    ctx:playSound("voices\\cinema\\dwarvesandhumans\\07.wav", "DoNothing", 100, 2400, "FALSE", 100) -- NPC110.scr:112
    ctx:wait(1, 3, "Trigger8") -- NPC110.scr:113
    do return ctx:exit("") end -- NPC110.scr:114
end

script.labels["Trigger8"] = function(ctx)
    -- NPC110.scr:118
    mm9.gosub(script, ctx, "Onstop") -- NPC110.scr:121
    local object = ctx:object("Alfrigg") -- NPC110.scr:122
    object:trigger("target") -- NPC110.scr:123
    object:trigger("Fight") -- NPC110.scr:124
    ctx:self():setTarget(ctx:object("g_hobject")) -- NPC110.scr:125
    ctx:self():addEnemy("commonerdwarfmaleA") -- NPC110.scr:126
    mm9.gosub(script, ctx, "baseinit") -- NPC110.scr:127
    do return ctx:exit("") end -- NPC110.scr:128
end

script.labels["OnTargetDead"] = function(ctx)
    -- NPC110.scr:132
    ctx:self():setNumberProperty("DoRude", "True") -- NPC110.scr:135
    ctx:self():removeEnemy("commonerdwarfmaleA") -- NPC110.scr:136
    ctx:state().bTargetDead = true -- NPC110.scr:137
    ctx:exitScript() -- NPC110.scr:138
    do return ctx:exit("TRUE") end -- NPC110.scr:140
end

script.labels["OnLost"] = function(ctx)
    -- NPC110.scr:143
    do return ctx:exit("TRUE") end -- NPC110.scr:146
end

script.labels["Init"] = function(ctx)
    -- NPC110.scr:149
    if ctx:hasKey(5010) then -- NPC110.scr:152-153
        ctx:state().xPos, ctx:state().Ypos, ctx:state().Zpos = ctx:object("HrolfMarker"):pos() -- NPC110.scr:154-155
        ctx:self():setPos("xPos", "yPos", "zPos") -- NPC110.scr:157
        do return ctx:exit("") end -- NPC110.scr:158
    end -- NPC110.scr:159
    ctx:onEvent("OnFoundPlayer", "OnStart") -- NPC110.scr:161
    ctx:onEvent("OnLostTarget", "ONLost") -- NPC110.scr:162
    do return ctx:exit("TRUE") end -- NPC110.scr:163
end

script.labels["OnStop"] = function(ctx)
    -- NPC110.scr:166
    ctx:self():stop() -- NPC110.scr:169
    ctx:self():loopAnimation("stand", 0, "DoNothing") -- NPC110.scr:170
    do return ctx:exit("") end -- NPC110.scr:171
end

script.labels["Main"] = function(ctx)
    -- NPC110.scr:174
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Start", "OnStart") -- NPC110.scr:179
    ctx:addTrigger("Speak3", "OnSpeak3") -- NPC110.scr:180
    ctx:addTrigger("Speak5", "OnSpeak5") -- NPC110.scr:181
    ctx:addTrigger("Speak7", "OnSpeak7") -- NPC110.scr:182
    mm9.gosub(script, ctx, "Init") -- NPC110.scr:184
    do return ctx:exit("") end -- NPC110.scr:186
end

return script
