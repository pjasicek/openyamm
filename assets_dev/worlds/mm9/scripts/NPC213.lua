-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC213.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "basewander.inc" }

-- NPC213.scr
-- timmy
-- handles Robert's speech
-- flag variables
script.labels["OnStop"] = function(ctx)
    -- NPC213.scr:23
    ctx:self():stop() -- NPC213.scr:25
    ctx:self():loopAnimation("stand", 0, "DoNothing") -- NPC213.scr:26
    do return ctx:exit("") end -- NPC213.scr:27
end

script.labels["OnSpeak2"] = function(ctx)
    -- NPC213.scr:30
    ctx:self():loopAnimation("conv1", 0, "DoNothing") -- NPC213.scr:33
    ctx:playSound("voices\\cinema\\BobandDoug\\02.wav", "DoNothing", 100, 2400, "FALSE", 100) -- NPC213.scr:34
    ctx:wait(1, 3, "Trigger3") -- NPC213.scr:35
    do return ctx:exit("") end -- NPC213.scr:36
end

script.labels["Trigger3"] = function(ctx)
    -- NPC213.scr:40
    mm9.gosub(script, ctx, "Onstop") -- NPC213.scr:43
    ctx:object("Douglas"):trigger("Speak3") -- NPC213.scr:44-45
    do return ctx:exit("") end -- NPC213.scr:46
end

script.labels["OnSpeak4"] = function(ctx)
    -- NPC213.scr:50
    ctx:self():loopAnimation("conv1", 0, "DoNothing") -- NPC213.scr:53
    ctx:playSound("voices\\cinema\\BobandDoug\\04.wav", "DoNothing", 100, 2400, "FALSE", 100) -- NPC213.scr:54
    ctx:wait(1, 3.8, "Trigger5") -- NPC213.scr:55
    do return ctx:exit("") end -- NPC213.scr:56
end

script.labels["Trigger5"] = function(ctx)
    -- NPC213.scr:60
    mm9.gosub(script, ctx, "Onstop") -- NPC213.scr:63
    ctx:object("Douglas"):trigger("Speak5") -- NPC213.scr:64-65
    do return ctx:exit("") end -- NPC213.scr:66
end

script.labels["OnSpeak6"] = function(ctx)
    -- NPC213.scr:71
    ctx:self():loopAnimation("conv1", 0, "DoNothing") -- NPC213.scr:74
    ctx:playSound("voices\\cinema\\BobandDoug\\06.wav", "DoNothing", 100, 2400, "FALSE", 100) -- NPC213.scr:75
    ctx:wait(1, 2, "Trigger7") -- NPC213.scr:76
    do return ctx:exit("") end -- NPC213.scr:77
end

script.labels["Trigger7"] = function(ctx)
    -- NPC213.scr:81
    mm9.gosub(script, ctx, "Onstop") -- NPC213.scr:84
    ctx:object("Douglas"):trigger("Speak7") -- NPC213.scr:85-86
    do return ctx:exit("") end -- NPC213.scr:87
end

script.labels["OnSpeak8"] = function(ctx)
    -- NPC213.scr:90
    ctx:self():loopAnimation("conv1", 0, "DoNothing") -- NPC213.scr:93
    ctx:playSound("voices\\cinema\\BobandDoug\\08.wav", "DoNothing", 100, 2400, "FALSE", 100) -- NPC213.scr:94
    ctx:wait(1, 4, "Trigger9") -- NPC213.scr:95
    do return ctx:exit("") end -- NPC213.scr:96
end

script.labels["Trigger9"] = function(ctx)
    -- NPC213.scr:100
    mm9.gosub(script, ctx, "Onstop") -- NPC213.scr:103
    ctx:object("Douglas"):trigger("Speak9") -- NPC213.scr:104-105
    do return ctx:exit("") end -- NPC213.scr:106
end

script.labels["OnTarget"] = function(ctx)
    -- NPC213.scr:109
    ctx:getParam(0, "g_hTarget") -- NPC213.scr:112
    ctx:self():setTarget(ctx:object("g_htarget")) -- NPC213.scr:113
    do return ctx:exit("") end -- NPC213.scr:114
end

script.labels["Main"] = function(ctx)
    -- NPC213.scr:117
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Speak2", "OnSpeak2") -- NPC213.scr:124
    ctx:addTrigger("Speak4", "OnSpeak4") -- NPC213.scr:125
    ctx:addTrigger("Speak6", "OnSpeak6") -- NPC213.scr:126
    ctx:addTrigger("Speak8", "OnSpeak8") -- NPC213.scr:127
    ctx:addTrigger("Target", "OnTarget") -- NPC213.scr:128
    do return ctx:exit("") end -- NPC213.scr:130
end

return script
