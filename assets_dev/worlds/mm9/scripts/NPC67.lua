-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC67.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC67.scr
-- timmy
-- tells a prop to run it's animation
-- about to go to bed
-- designates which callback onobstacle uses
-- Parameters
-- P1  # of times animation runs
script.labels["Onexit"] = function(ctx)
    -- NPC67.scr:21
    do return ctx:exit("") end -- NPC67.scr:24
end

script.labels["GotoBed"] = function(ctx)
    -- NPC67.scr:27
    ctx:set("callback", "onexit") -- NPC67.scr:31
    ctx:state().sleepy = 1 -- NPC67.scr:32
    ctx:state().G_hobject = ctx:objectOrNil("NPC67M3") -- NPC67.scr:33
    ctx:self():walkTo(ctx:object("g_hobject"), "g_ntemp", "Onexit") -- NPC67.scr:34
    do return ctx:exit("") end -- NPC67.scr:36
end

script.labels["GotoBar"] = function(ctx)
    -- NPC67.scr:39
    ctx:set("callback", "bartender") -- NPC67.scr:42
    ctx:state().G_hobject = ctx:objectOrNil("NPC67M1") -- NPC67.scr:43
    ctx:self():walkTo(ctx:object("g_hobject"), "g_ntemp", "Onexit") -- NPC67.scr:44
    do return ctx:exit("") end -- NPC67.scr:46
end

script.labels["bartender"] = function(ctx)
    -- NPC67.scr:49
    ctx:state().G_hobject = ctx:objectOrNil("Bartender") -- NPC67.scr:52
    ctx:self():faceObject(ctx:object("g_hobject"), 160, "Onexit") -- NPC67.scr:53
    do return ctx:exit("") end -- NPC67.scr:54
end

script.labels["Gotowork"] = function(ctx)
    -- NPC67.scr:58
    ctx:set("callback", "onexit") -- NPC67.scr:61
    ctx:state().sleepy = 0 -- NPC67.scr:62
    ctx:state().G_hobject = ctx:objectOrNil("NPC67M2") -- NPC67.scr:64
    ctx:self():walkTo(ctx:object("g_hobject"), "g_ntemp", "Onexit") -- NPC67.scr:65
    do return ctx:exit("") end -- NPC67.scr:67
end

script.labels["Obstacle"] = function(ctx)
    -- NPC67.scr:72
    if ctx:condition("callback==bartender") then -- NPC67.scr:75
        ctx:self():walkTo(ctx:object("g_hobject"), "g_ntemp", "Bartender") -- NPC67.scr:76
        do return ctx:exit("") end -- NPC67.scr:77
    end -- NPC67.scr:78
    ctx:self():walkTo(ctx:object("g_hobject"), "g_ntemp", "Onexit") -- NPC67.scr:80
    do return ctx:exit("") end -- NPC67.scr:81
end

script.labels["MissedBed"] = function(ctx)
    -- NPC67.scr:84
    ctx:state().G_hobject = ctx:objectOrNil("Marker2") -- NPC67.scr:87
    ctx:state().PosX, ctx:state().PosY, ctx:state().PosZ = ctx:object("g_hobject"):pos() -- NPC67.scr:88
    ctx:state().g_hobject = ctx:self() -- NPC67.scr:89
    ctx:self():setPos("PosX", "PosY", "PosZ") -- NPC67.scr:90
    do return ctx:exit("") end -- NPC67.scr:91
end

script.labels["MissedBar"] = function(ctx)
    -- NPC67.scr:94
    ctx:state().G_hobject = ctx:objectOrNil("Marker0") -- NPC67.scr:97
    ctx:state().PosX, ctx:state().PosY, ctx:state().PosZ = ctx:object("g_hobject"):pos() -- NPC67.scr:98
    ctx:state().g_hobject = ctx:self() -- NPC67.scr:99
    ctx:self():setPos("PosX", "PosY", "PosZ") -- NPC67.scr:100
    do return ctx:exit("") end -- NPC67.scr:102
end

script.labels["MissedWork"] = function(ctx)
    -- NPC67.scr:105
    ctx:state().G_hobject = ctx:objectOrNil("Marker3") -- NPC67.scr:108
    ctx:state().PosX, ctx:state().PosY, ctx:state().PosZ = ctx:object("g_hobject"):pos() -- NPC67.scr:109
    ctx:state().g_hobject = ctx:self() -- NPC67.scr:110
    ctx:self():setPos("PosX", "PosY", "PosZ") -- NPC67.scr:111
    do return ctx:exit("") end -- NPC67.scr:112
end

script.labels["Main"] = function(ctx)
    -- NPC67.scr:115
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "params") -- NPC67.scr:121
    ctx:getParam(1, "times") -- NPC67.scr:122
    ctx:getParam(2, "g_ntemp") -- NPC67.scr:123
    ctx:self():loopAnimation("Params", "times", "Onexit") -- NPC67.scr:124
    ctx:atTime(0, 45, "GotoBed", "Missedbed") -- NPC67.scr:125
    ctx:atTime(0, 15, "GoToBar", "Missedbar") -- NPC67.scr:126
    ctx:atTime(1, 0, "Gotowork", "Missedwork") -- NPC67.scr:127
    -- @M 20 : 15 GotoBed Missedbed
    -- @M 15 : 00 GoToBar Missedbar
    -- @M 06 : 00 Gotowork Missedwork
    ctx:onEvent("OnObstacle", "obstacle") -- NPC67.scr:135
    -- Temp test triggers-----------
    ctx:addTrigger("Missbed", "Missedbed") -- NPC67.scr:140
    ctx:addTrigger("Missbar", "Missedbar") -- NPC67.scr:141
    ctx:addTrigger("Misswork", "Missedwork") -- NPC67.scr:142
    ctx:addTrigger("Bed", "GotoBed") -- NPC67.scr:144
    ctx:addTrigger("Bar", "GotoBar") -- NPC67.scr:145
    ctx:addTrigger("Work", "GotoWork") -- NPC67.scr:146
    do return ctx:exit("") end -- NPC67.scr:147
end

return script
