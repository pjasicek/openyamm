-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BELL.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- bell.scr
-- timmy
-- rings bell
-- Parameters
-- P0  inner radius
-- p1  outer radius
script.labels["DoNothing"] = function(ctx)
    -- BELL.scr:20
    do return ctx:exit("") end -- BELL.scr:22
end

script.labels["StopDone"] = function(ctx)
    -- BELL.scr:25
    ctx:state().Counter = 0 -- BELL.scr:28
    do return ctx:exit("") end -- BELL.scr:30
end

script.labels["RingDone"] = function(ctx)
    -- BELL.scr:33
    ctx:self():playAnimation("Stop") -- BELL.scr:36
    ctx:wait(1, 3, "StopDone") -- BELL.scr:37
    do return ctx:exit("") end -- BELL.scr:38
end

script.labels["OnUse"] = function(ctx)
    -- BELL.scr:41
    if ctx:condition("counter==0") then -- BELL.scr:45
        ctx:state().Counter = (tonumber(ctx:state().Counter) or 0) + 1 -- BELL.scr:46
        ctx:self():playAnimation("Ring", "RingDone") -- BELL.scr:47
        ctx:wait(1, 3, "DoNothing") -- BELL.scr:48
        do return ctx:exit("") end -- BELL.scr:49
    end -- BELL.scr:50
    do return ctx:exit("") end -- BELL.scr:52
end

script.labels["OnBellBing"] = function(ctx)
    -- BELL.scr:55
    ctx:playSound("Sounds\\Ambient\\bellbing.wav", "DoNothing", "innerRadius", "outerRadius", "FALSE", 100) -- BELL.scr:57
    do return ctx:exit("") end -- BELL.scr:59
end

script.labels["OnBellBong"] = function(ctx)
    -- BELL.scr:62
    ctx:playSound("Sounds\\Ambient\\bellbing.wav", "DoNothing", "innerRadius", "outerRadius", "FALSE", 100) -- BELL.scr:64
    do return ctx:exit("") end -- BELL.scr:66
end

script.labels["Main"] = function(ctx)
    -- BELL.scr:70
    -- TraceON
    ctx:state().Counter = 0 -- BELL.scr:75
    ctx:getParam(0, "innerRadius") -- BELL.scr:76
    ctx:getParam(1, "outerRadius") -- BELL.scr:77
    ctx:addTrigger("Use", "Onuse") -- BELL.scr:79
    ctx:addModelKey("BellBing", "OnBellBing") -- BELL.scr:80
    ctx:addModelKey("BellBong", "OnBellBong") -- BELL.scr:81
    ctx:onEvent("OnDamage", "OnUse") -- BELL.scr:82
    ctx:cacheSound("Sounds\\Ambient\\bellbing.wav") -- BELL.scr:84
    ctx:cacheSound("Sounds\\Ambient\\bellbong.wav") -- BELL.scr:85
    -- ExitScript
    do return ctx:exit("") end -- BELL.scr:89
end

return script
