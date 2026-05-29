-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC214.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "globals.inc" }

-- NPC214.scr
-- timmy
-- handles Douglas's speech
-- flag variables
script.labels["OnStart"] = function(ctx)
    -- NPC214.scr:19
    ctx:hasKey(111, "bSpeak") -- NPC214.scr:22
    if ctx:condition("bSpeak==TRUE") then -- NPC214.scr:23
        do return ctx:exit("") end -- NPC214.scr:24
    end -- NPC214.scr:25
    ctx:state().g_hobject = ctx:objectOrNil("Robert") -- NPC214.scr:27
    ctx:self():setTarget(ctx:object("g_hobject")) -- NPC214.scr:28
    ctx:trigger("g_hobject", "Target") -- NPC214.scr:29
    ctx:giveKey(111) -- NPC214.scr:31
    ctx:self():loopAnimation("conv2", 0, "DoNothing") -- NPC214.scr:32
    ctx:playSound("voices\\cinema\\BobandDoug\\01.wav", "DoNothing", 100, 2400, "FALSE", 100) -- NPC214.scr:33
    ctx:wait(1, 2, "Trigger2") -- NPC214.scr:34
    do return ctx:exit("") end -- NPC214.scr:35
end

script.labels["Trigger2"] = function(ctx)
    -- NPC214.scr:39
    mm9.gosub(script, ctx, "Onstop") -- NPC214.scr:42
    ctx:object("Robert"):trigger("Speak2") -- NPC214.scr:43-44
    do return ctx:exit("") end -- NPC214.scr:45
end

script.labels["OnSpeak3"] = function(ctx)
    -- NPC214.scr:49
    ctx:self():loopAnimation("conv2", 0, "DoNothing") -- NPC214.scr:52
    ctx:playSound("voices\\cinema\\BobandDoug\\03.wav", "DoNothing", 100, 2400, "FALSE", 100) -- NPC214.scr:53
    ctx:wait(1, 7.8, "Trigger4") -- NPC214.scr:54
    do return ctx:exit("") end -- NPC214.scr:55
end

script.labels["Trigger4"] = function(ctx)
    -- NPC214.scr:59
    mm9.gosub(script, ctx, "Onstop") -- NPC214.scr:62
    ctx:object("Robert"):trigger("Speak4") -- NPC214.scr:63-64
    do return ctx:exit("") end -- NPC214.scr:65
end

script.labels["OnSpeak5"] = function(ctx)
    -- NPC214.scr:69
    ctx:self():loopAnimation("conv5", 0, "DoNothing") -- NPC214.scr:72
    ctx:playSound("voices\\cinema\\BobandDoug\\05.wav", "DoNothing", 100, 2400, "FALSE", 100) -- NPC214.scr:73
    ctx:wait(1, 6.5, "Trigger6") -- NPC214.scr:74
    do return ctx:exit("") end -- NPC214.scr:75
end

script.labels["Trigger6"] = function(ctx)
    -- NPC214.scr:79
    mm9.gosub(script, ctx, "Onstop") -- NPC214.scr:82
    ctx:object("Robert"):trigger("Speak6") -- NPC214.scr:83-84
    do return ctx:exit("") end -- NPC214.scr:85
end

script.labels["OnSpeak7"] = function(ctx)
    -- NPC214.scr:89
    ctx:self():loopAnimation("conv4", 0, "DoNothing") -- NPC214.scr:92
    ctx:playSound("voices\\cinema\\BobandDoug\\07.wav", "DoNothing", 100, 2400, "FALSE", 100) -- NPC214.scr:93
    ctx:wait(1, 3, "Trigger8") -- NPC214.scr:94
    do return ctx:exit("") end -- NPC214.scr:95
end

script.labels["Trigger8"] = function(ctx)
    -- NPC214.scr:99
    mm9.gosub(script, ctx, "Onstop") -- NPC214.scr:102
    ctx:object("Robert"):trigger("Speak8") -- NPC214.scr:103-104
    do return ctx:exit("") end -- NPC214.scr:105
end

script.labels["OnSpeak9"] = function(ctx)
    -- NPC214.scr:109
    ctx:self():loopAnimation("conv5", 0, "DoNothing") -- NPC214.scr:112
    ctx:playSound("voices\\cinema\\BobandDoug\\09.wav", "DoNothing", 100, 2400, "FALSE", 100) -- NPC214.scr:113
    ctx:wait(1, 3, "OnStop") -- NPC214.scr:114
    do return ctx:exit("") end -- NPC214.scr:115
end

script.labels["OnLost"] = function(ctx)
    -- NPC214.scr:120
    do return ctx:exit("TRUE") end -- NPC214.scr:123
end

script.labels["Init"] = function(ctx)
    -- NPC214.scr:126
    ctx:onEvent("OnFoundPlayer", "OnStart") -- NPC214.scr:129
    ctx:onEvent("OnLostTarget", "ONLost") -- NPC214.scr:130
    do return ctx:exit("TRUE") end -- NPC214.scr:131
end

script.labels["OnStop"] = function(ctx)
    -- NPC214.scr:134
    ctx:self():stop() -- NPC214.scr:136
    ctx:self():loopAnimation("stand", 0, "DoNothing") -- NPC214.scr:137
    do return ctx:exit("") end -- NPC214.scr:138
end

script.labels["Main"] = function(ctx)
    -- NPC214.scr:141
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Start", "OnStart") -- NPC214.scr:146
    ctx:addTrigger("Speak3", "OnSpeak3") -- NPC214.scr:147
    ctx:addTrigger("Speak5", "OnSpeak5") -- NPC214.scr:148
    ctx:addTrigger("Speak7", "OnSpeak7") -- NPC214.scr:149
    ctx:addTrigger("Speak9", "OnSpeak9") -- NPC214.scr:150
    mm9.gosub(script, ctx, "Init") -- NPC214.scr:151
    do return ctx:exit("") end -- NPC214.scr:153
end

return script
