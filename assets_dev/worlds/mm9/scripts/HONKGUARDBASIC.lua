-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HONKGUARDBASIC.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "HonkHostility.inc" }

-- HONKGuardBasic.scr
-- by SJR
-- Purpose:standard HONK, but with
-- checking for acts of
-- aggression (stealing, hitting etc.)
-- type 0=none,1=pamphlet
script.labels["Main"] = function(ctx)
    -- HONKGUARDBASIC.scr:16
    ctx:getParam(0, "HONK_TYPE") -- HONKGUARDBASIC.scr:18
    ctx:command("onpoststartworld", "InitHonkGuardBasic") -- HONKGUARDBASIC.scr:20
    ctx:command("onpostminisaveload", "InitHonkGuardBasic") -- HONKGUARDBASIC.scr:21
    do return ctx:exit("TRUE") end -- HONKGUARDBASIC.scr:23
end

script.labels["InitHonkGuardBasic"] = function(ctx)
    -- HONKGUARDBASIC.scr:26
    mm9.gosub(script, ctx, "BaseWanderInit") -- HONKGUARDBASIC.scr:28
    mm9.gosub(script, ctx, "BaseWanderStartup") -- HONKGUARDBASIC.scr:29
    mm9.gosub(script, ctx, "AttachTool") -- HONKGUARDBASIC.scr:30
    mm9.gosub(script, ctx, "InitHonkHostility") -- HONKGUARDBASIC.scr:31
    do return ctx:exit("TRUE") end -- HONKGUARDBASIC.scr:33
end

script.labels["AttachTool"] = function(ctx)
    -- HONKGUARDBASIC.scr:36
    if ctx:condition("HONK_TYPE==1") then -- HONKGUARDBASIC.scr:38
        ctx:command("attachprop", "\"HonkPamphlet.ABC\",\"Pamphlet.DTX\",\"Pamphlet\",hProp") -- HONKGUARDBASIC.scr:39
    end -- HONKGUARDBASIC.scr:40
    do return ctx:exit("TRUE") end -- HONKGUARDBASIC.scr:42
end

return script
