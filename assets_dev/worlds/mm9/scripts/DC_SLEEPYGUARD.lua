-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DC_SLEEPYGUARD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "DookHostility.inc" }

-- DC_sleepyguard.scr
-- Brett Yagi
-- Parameters
-- SJR( added all hostility stuff)
-- endSJR
script.labels["dn"] = function(ctx)
    -- DC_SLEEPYGUARD.scr:20
    do return ctx:exit(1) end -- DC_SLEEPYGUARD.scr:22
end

script.labels["Sleep"] = function(ctx)
    -- DC_SLEEPYGUARD.scr:26
    ctx:command("setstat", "hMe VisibleRange 1") -- DC_SLEEPYGUARD.scr:28
    ctx:command("setstat", "hMe HearingRange 1") -- DC_SLEEPYGUARD.scr:29
    ctx:command("loopanim", "sleep 0 dn") -- DC_SLEEPYGUARD.scr:30
    do return ctx:exit(1) end -- DC_SLEEPYGUARD.scr:32
end

script.labels["WakeUp4"] = function(ctx)
    -- DC_SLEEPYGUARD.scr:37
    ctx:command("wait", "1 5 sleep") -- DC_SLEEPYGUARD.scr:39
    do return ctx:exit(1) end -- DC_SLEEPYGUARD.scr:41
end

script.labels["WakeUp3"] = function(ctx)
    -- DC_SLEEPYGUARD.scr:44
    ctx:command("playanim", "fidget2 wakeup4") -- DC_SLEEPYGUARD.scr:46
    do return ctx:exit(1) end -- DC_SLEEPYGUARD.scr:48
end

script.labels["WakeUp2"] = function(ctx)
    -- DC_SLEEPYGUARD.scr:51
    ctx:command("playanim", "fidget1 wakeup3") -- DC_SLEEPYGUARD.scr:53
    do return ctx:exit(1) end -- DC_SLEEPYGUARD.scr:55
end

script.labels["WakeUp"] = function(ctx)
    -- DC_SLEEPYGUARD.scr:60
    ctx:command("playanim", "stand wakeup2") -- DC_SLEEPYGUARD.scr:62
    ctx:command("setstat", "hMe VisibleRange 151") -- DC_SLEEPYGUARD.scr:64
    ctx:command("setstat", "hMe HearingRange 151") -- DC_SLEEPYGUARD.scr:65
    ctx:command("getstat", "hMe VisibleRange nVisRange") -- DC_SLEEPYGUARD.scr:67
    do return ctx:exit(1) end -- DC_SLEEPYGUARD.scr:69
end

script.labels["Main2"] = function(ctx)
    -- DC_SLEEPYGUARD.scr:73
    mm9.gosub(script, ctx, "InitDookHostility") -- DC_SLEEPYGUARD.scr:75
    ctx:command("getmyhandle", "hMe") -- DC_SLEEPYGUARD.scr:77
    ctx:command("getstat", "hMe VisibleRange nVisRange") -- DC_SLEEPYGUARD.scr:78
    ctx:command("getstat", "hMe HearingRange nHearRange") -- DC_SLEEPYGUARD.scr:79
    ctx:command("nvisrange", "= 200") -- DC_SLEEPYGUARD.scr:81
    ctx:command("nhearrange", "= 200") -- DC_SLEEPYGUARD.scr:82
    mm9.gosub(script, ctx, "sleep") -- DC_SLEEPYGUARD.scr:84
    do return ctx:exit(1) end -- DC_SLEEPYGUARD.scr:86
end

script.labels["Main"] = function(ctx)
    -- DC_SLEEPYGUARD.scr:90
    ctx:addTrigger("WakeUp", "WakeUp") -- DC_SLEEPYGUARD.scr:92
    ctx:command("onpoststartworld", "main2") -- DC_SLEEPYGUARD.scr:94
    do return ctx:exit(1) end -- DC_SLEEPYGUARD.scr:96
end

return script
