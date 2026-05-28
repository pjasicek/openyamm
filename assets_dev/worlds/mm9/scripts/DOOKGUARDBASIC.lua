-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DOOKGUARDBASIC.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "DookHostility.inc" }

-- DookGuardBasic.scr
-- by SJR
-- 01-01-02
-- Purpose:basic script for all guards.
-- Refrain from attacking player
-- until they go through the tunnel.
script.labels["Main"] = function(ctx)
    -- DOOKGUARDBASIC.scr:12
    ctx:command("onpoststartworld", "InitDookGuardBasic") -- DOOKGUARDBASIC.scr:14
    ctx:command("onpostminisaveload", "InitDookGuardBasic") -- DOOKGUARDBASIC.scr:15
    do return ctx:exit("TRUE") end -- DOOKGUARDBASIC.scr:17
end

script.labels["InitDookGuardBasic"] = function(ctx)
    -- DOOKGUARDBASIC.scr:20
    mm9.gosub(script, ctx, "BaseWanderInit") -- DOOKGUARDBASIC.scr:22
    mm9.gosub(script, ctx, "BaseWanderStartup") -- DOOKGUARDBASIC.scr:23
    mm9.gosub(script, ctx, "InitDookHostility") -- DOOKGUARDBASIC.scr:24
    do return ctx:exit("TRUE") end -- DOOKGUARDBASIC.scr:26
end

return script
