-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "EVILSORCERER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "range.inc" }

-- EvilSorcerer.Scr
-- Jeff Leggett
script.labels["BaseCrawlGetHim"] = function(ctx)
    -- EVILSORCERER.scr:11
    do return ctx:exit("") end -- EVILSORCERER.scr:13
end

script.labels["TargetStill"] = function(ctx)
    -- EVILSORCERER.scr:16
    do return ctx:exit("") end -- EVILSORCERER.scr:18
end

script.labels["TargetMoving"] = function(ctx)
    -- EVILSORCERER.scr:21
    do return ctx:exit("") end -- EVILSORCERER.scr:24
end

script.labels["ShouldRunAfter"] = function(ctx)
    -- EVILSORCERER.scr:26
    -- we never run after our targets...
    ctx:state().g_bTemp = false -- EVILSORCERER.scr:31
    do return ctx:exit("") end -- EVILSORCERER.scr:33
end

script.labels["Main"] = function(ctx)
    -- EVILSORCERER.scr:36
    mm9.gosub(script, ctx, "BaseInit") -- EVILSORCERER.scr:40
    mm9.gosub(script, ctx, "RangeInit") -- EVILSORCERER.scr:41
    ctx:set("g_rangeAttackType", "RANGE_TYPE2") -- EVILSORCERER.scr:43
    mm9.gosub(script, ctx, "SetupRangeAttackType") -- EVILSORCERER.scr:44
    do return ctx:exit("") end -- EVILSORCERER.scr:46
end

return script
