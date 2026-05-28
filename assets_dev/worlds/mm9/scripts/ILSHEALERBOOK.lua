-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ILSHEALERBOOK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "healer.inc" }

-- ILSHealerbook.scr
-- Timmy
-- This script Handles the healing book animations
-- Parameters:
-- p0	- Amount to heal players by (default=10)
-- p1  - Amount of times you can heal from this fountain
script.labels["Onclickon"] = function(ctx)
    -- ILSHEALERBOOK.scr:20
    if ctx:condition("counter==0") then -- ILSHEALERBOOK.scr:23
        ctx:command("playanim", "OpenBook") -- ILSHEALERBOOK.scr:25
        ctx:command("add", "counter, 1") -- ILSHEALERBOOK.scr:26
        do return ctx:exit("") end -- ILSHEALERBOOK.scr:27
    end -- ILSHEALERBOOK.scr:28
    if ctx:condition("counter==1") then -- ILSHEALERBOOK.scr:30
        ctx:command("playanim", "TurnPage") -- ILSHEALERBOOK.scr:31
        ctx:command("add", "counter, 1") -- ILSHEALERBOOK.scr:32
        mm9.gosub(script, ctx, "HealerOnUse") -- ILSHEALERBOOK.scr:33
        do return ctx:exit("") end -- ILSHEALERBOOK.scr:34
    end -- ILSHEALERBOOK.scr:35
    if ctx:condition("counter==2") then -- ILSHEALERBOOK.scr:37
        ctx:command("playanim", "CloseBook") -- ILSHEALERBOOK.scr:38
        ctx:command("set", "counter, 0") -- ILSHEALERBOOK.scr:39
        do return ctx:exit("") end -- ILSHEALERBOOK.scr:40
    end -- ILSHEALERBOOK.scr:41
    do return ctx:exit("") end -- ILSHEALERBOOK.scr:43
    do return ctx:exit("") end -- ILSHEALERBOOK.scr:46
end

script.labels["Main"] = function(ctx)
    -- ILSHEALERBOOK.scr:49
    ctx:getParam(0, "g_nTemp") -- ILSHEALERBOOK.scr:55
    if ctx:condition("g_nTemp!=0") then -- ILSHEALERBOOK.scr:57
        ctx:command("set", "g_nHealAmt, g_nTemp") -- ILSHEALERBOOK.scr:58
    end -- ILSHEALERBOOK.scr:59
    ctx:getParam(1, "g_nTemp") -- ILSHEALERBOOK.scr:61
    if ctx:condition("g_nTemp!=0") then -- ILSHEALERBOOK.scr:63
        ctx:command("set", "g_nHealCount, g_nTemp") -- ILSHEALERBOOK.scr:64
    end -- ILSHEALERBOOK.scr:65
    ctx:addTrigger("use", "Onclickon") -- ILSHEALERBOOK.scr:69
    do return ctx:exit("") end -- ILSHEALERBOOK.scr:71
end

return script
