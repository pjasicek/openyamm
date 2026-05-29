-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LINDISFARNEBELL.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- LLindisfarneBell.scr
-- timmy
-- rings bell for Lindisfarne Bells
-- Parameters
-- P0  inner radius
-- p1  outer radius
script.labels["DoNothing"] = function(ctx)
    -- LINDISFARNEBELL.scr:23
    do return ctx:exit("") end -- LINDISFARNEBELL.scr:25
end

script.labels["StopDone"] = function(ctx)
    -- LINDISFARNEBELL.scr:28
    ctx:state().Counter = 0 -- LINDISFARNEBELL.scr:31
    if not ctx:hasKey(9507) then -- LINDISFARNEBELL.scr:32-33
        ctx:trigger("g_hobject", "Bell_Trigger") -- LINDISFARNEBELL.scr:34
        do return ctx:exit("") end -- LINDISFARNEBELL.scr:35
    end -- LINDISFARNEBELL.scr:36
    do return ctx:exit("") end -- LINDISFARNEBELL.scr:37
end

script.labels["RingDone"] = function(ctx)
    -- LINDISFARNEBELL.scr:40
    ctx:self():playAnimation("Stop") -- LINDISFARNEBELL.scr:43
    ctx:wait(1, 3, "StopDone") -- LINDISFARNEBELL.scr:44
    do return ctx:exit("") end -- LINDISFARNEBELL.scr:45
end

script.labels["OnUse"] = function(ctx)
    -- LINDISFARNEBELL.scr:48
    if ctx:condition("counter==0") then -- LINDISFARNEBELL.scr:52
        ctx:state().Counter = (tonumber(ctx:state().Counter) or 0) + 1 -- LINDISFARNEBELL.scr:53
        ctx:self():playAnimation("Ring", "RingDone") -- LINDISFARNEBELL.scr:54
        ctx:state().g_hobject = ctx:objectOrNil("BellControl") -- LINDISFARNEBELL.scr:55
        ctx:wait(1, 3, "DoNothing") -- LINDISFARNEBELL.scr:57
        do return ctx:exit("") end -- LINDISFARNEBELL.scr:58
    end -- LINDISFARNEBELL.scr:59
    -- endif
    do return ctx:exit("") end -- LINDISFARNEBELL.scr:62
end

script.labels["OnBellBing"] = function(ctx)
    -- LINDISFARNEBELL.scr:66
    ctx:playSound("Bell_Note", "DoNothing", "innerRadius", "outerRadius", "FALSE", 100) -- LINDISFARNEBELL.scr:68
    do return ctx:exit("") end -- LINDISFARNEBELL.scr:70
end

script.labels["OnBellBong"] = function(ctx)
    -- LINDISFARNEBELL.scr:73
    ctx:playSound("Bell_Note", "DoNothing", "innerRadius", "outerRadius", "FALSE", 100) -- LINDISFARNEBELL.scr:75
    do return ctx:exit("") end -- LINDISFARNEBELL.scr:77
end

script.labels["BellSound"] = function(ctx)
    -- LINDISFARNEBELL.scr:80
    if ctx:condition("BellSound==1") then -- LINDISFARNEBELL.scr:83
        ctx:set("Bell_Note", "Sounds\\Events\\churchbellring.wav") -- LINDISFARNEBELL.scr:84
        ctx:set("Bell_Trigger", "Bell1") -- LINDISFARNEBELL.scr:85
        do return ctx:exit("") end -- LINDISFARNEBELL.scr:86
    end -- LINDISFARNEBELL.scr:87
    if ctx:condition("BellSound==2") then -- LINDISFARNEBELL.scr:89
        ctx:set("Bell_Note", "Sounds\\Events\\churchbellring2.wav") -- LINDISFARNEBELL.scr:90
        ctx:set("Bell_Trigger", "Bell2") -- LINDISFARNEBELL.scr:91
        do return ctx:exit("") end -- LINDISFARNEBELL.scr:92
    end -- LINDISFARNEBELL.scr:93
    if ctx:condition("BellSound==3") then -- LINDISFARNEBELL.scr:96
        ctx:set("Bell_Note", "Sounds\\Events\\churchbellring3.wav") -- LINDISFARNEBELL.scr:97
        ctx:set("Bell_Trigger", "Bell3") -- LINDISFARNEBELL.scr:98
        do return ctx:exit("") end -- LINDISFARNEBELL.scr:99
    end -- LINDISFARNEBELL.scr:100
    if ctx:condition("BellSound==4") then -- LINDISFARNEBELL.scr:103
        ctx:set("Bell_Note", "Sounds\\Events\\churchbellring4.wav") -- LINDISFARNEBELL.scr:104
        ctx:set("Bell_Trigger", "Bell4") -- LINDISFARNEBELL.scr:105
        do return ctx:exit("") end -- LINDISFARNEBELL.scr:106
    end -- LINDISFARNEBELL.scr:107
    if ctx:condition("BellSound==5") then -- LINDISFARNEBELL.scr:110
        ctx:set("Bell_Note", "Sounds\\Events\\churchbellring5.wav") -- LINDISFARNEBELL.scr:111
        ctx:set("Bell_Trigger", "Bell5") -- LINDISFARNEBELL.scr:112
        do return ctx:exit("") end -- LINDISFARNEBELL.scr:113
    end -- LINDISFARNEBELL.scr:114
    do return ctx:exit("") end -- LINDISFARNEBELL.scr:116
end

script.labels["Main"] = function(ctx)
    -- LINDISFARNEBELL.scr:119
    -- TraceON
    ctx:state().Counter = 0 -- LINDISFARNEBELL.scr:124
    ctx:getParam(0, "innerRadius") -- LINDISFARNEBELL.scr:125
    ctx:getParam(1, "outerRadius") -- LINDISFARNEBELL.scr:126
    ctx:getParam(2, "BellSound") -- LINDISFARNEBELL.scr:127
    ctx:addTrigger("Use", "Onuse") -- LINDISFARNEBELL.scr:129
    ctx:addModelKey("BellBing", "OnBellBing") -- LINDISFARNEBELL.scr:130
    ctx:addModelKey("BellBong", "OnBellBong") -- LINDISFARNEBELL.scr:131
    ctx:onEvent("OnDamage", "OnUse") -- LINDISFARNEBELL.scr:132
    mm9.gosub(script, ctx, "BellSound") -- LINDISFARNEBELL.scr:134
    -- CacheSound Sounds\Events\churchbellring.wav
    -- CacheSound Sounds\Ambient\bellbong.wav
    -- ExitScript
    do return ctx:exit("") end -- LINDISFARNEBELL.scr:140
end

return script
