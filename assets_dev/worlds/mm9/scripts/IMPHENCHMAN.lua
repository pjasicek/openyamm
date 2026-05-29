-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "IMPHENCHMAN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "baseMelee.inc" }

-- ImpHenchman.scr
-- by SJR
-- 10/12/01
-- Purpose:wrapper for base.scr
-- with one extra feature
script.labels["Main"] = function(ctx)
    -- IMPHENCHMAN.scr:11
    -- OnPostStartWorld InitImpHenchman
    ctx:wait(0, 5, "InitImpHenchman") -- IMPHENCHMAN.scr:14
    do return ctx:exit("TRUE") end -- IMPHENCHMAN.scr:16
end

script.labels["InitImpHenchman"] = function(ctx)
    -- IMPHENCHMAN.scr:19
    ctx:addTrigger("Help", "DefendImp") -- IMPHENCHMAN.scr:21
    mm9.gosub(script, ctx, "BaseInit") -- IMPHENCHMAN.scr:23
    mm9.gosub(script, ctx, "BaseWanderStartup") -- IMPHENCHMAN.scr:24
    do return ctx:exit("TRUE") end -- IMPHENCHMAN.scr:26
end

script.labels["DefendImp"] = function(ctx)
    -- IMPHENCHMAN.scr:29
    mm9.gosub(script, ctx, "BaseWanderStop") -- IMPHENCHMAN.scr:31
    ctx:state().g_hTarget = ctx:player() -- IMPHENCHMAN.scr:32
    mm9.gosub(script, ctx, "SetupTarget") -- IMPHENCHMAN.scr:33
    ctx:self():runTo(ctx:player(), 10, "AggressiveStart") -- IMPHENCHMAN.scr:34
    do return ctx:exit("TRUE") end -- IMPHENCHMAN.scr:36
end

return script
