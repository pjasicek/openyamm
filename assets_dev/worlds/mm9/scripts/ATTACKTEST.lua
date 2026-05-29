-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ATTACKTEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "aiglobals.inc" }

-- AttackTest.scr
-- Jeff Leggett
-- This script makes for a good way to test monster attacks
script.labels["AttackDone"] = function(ctx)
    -- ATTACKTEST.scr:11
end

script.labels["AttackReady"] = function(ctx)
    -- ATTACKTEST.scr:12
    ctx:self():attack("AttackDone") -- ATTACKTEST.scr:14
    do return ctx:exit("") end -- ATTACKTEST.scr:15
end

script.labels["FoundPlayer"] = function(ctx)
    -- ATTACKTEST.scr:18
    ctx:getParam(0, "g_hTarget") -- ATTACKTEST.scr:19
    ctx:self():faceObject(ctx:object("g_hTarget")) -- ATTACKTEST.scr:20
    ctx:onEvent("OnFoundPlayer") -- ATTACKTEST.scr:21
    ctx:self():attack("AttackDone") -- ATTACKTEST.scr:23
    do return ctx:exit("") end -- ATTACKTEST.scr:24
end

script.labels["Main"] = function(ctx)
    -- ATTACKTEST.scr:26
    ctx:onEvent("OnFoundPlayer", "FoundPlayer") -- ATTACKTEST.scr:27
    ctx:onEvent("OnAttackReady", "AttackReady") -- ATTACKTEST.scr:28
    do return ctx:exit("") end -- ATTACKTEST.scr:30
end

return script
