-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BASE2.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 19, path = "basecrawl.inc" }
script.includes[#script.includes + 1] = { line = 20, path = "baseevade.inc" }

-- Base2.inc
-- Jeff Leggett
-- 10/03/2001
-- New and improved base script.
-- Cleaner
-- More modular
-- Makes more use of function overloading...
-- Additions to basecrawl.inc:
-- strafe attacks
-- evasive maneuvers
script.labels["TargetMoving"] = function(ctx)
    -- BASE2.inc:25
    mm9.gosub(script, ctx, "TargetMoving") -- BASE2.inc:28
    do return ctx:exit("") end -- BASE2.inc:30
end

script.labels["TargetStill"] = function(ctx)
    -- BASE2.inc:33
    if ctx:condition("g_bStrafeAttack==FALSE") then -- BASE2.inc:36
        mm9.gosub(script, ctx, "TargetStill") -- BASE2.inc:37
    end -- BASE2.inc:38
    do return ctx:exit("") end -- BASE2.inc:40
end

script.labels["PostAttack"] = function(ctx)
    -- BASE2.inc:43
    -- overloaded to potentially do a strafe attack...
    ctx:command("g_bstrafeattack", "= FALSE") -- BASE2.inc:49
    mm9.gosub(script, ctx, "PostAttack") -- BASE2.inc:51
    mm9.gosub(script, ctx, "IsTargetMoving") -- BASE2.inc:52
    if ctx:condition("g_bTemp==FALSE") then -- BASE2.inc:54
        ctx:command("getrandomint", "0, 100, g_nRandom") -- BASE2.inc:56
        if ctx:condition("g_nRandom < g_nStrafeAttackPct") then -- BASE2.inc:58
            ctx:command("g_bpickdir", "= TRUE") -- BASE2.inc:59
            mm9.gosub(script, ctx, "BE_AttackStrafe") -- BASE2.inc:60
            ctx:command("g_bpickdir", "= TRUE") -- BASE2.inc:61
            ctx:command("g_bstrafeattack", "= TRUE") -- BASE2.inc:62
        end -- BASE2.inc:63
    end -- BASE2.inc:64
    ctx:command("traceoff", "") -- BASE2.inc:66
    do return ctx:exit("") end -- BASE2.inc:68
end

script.labels["BaseInit"] = function(ctx)
    -- BASE2.inc:72
    mm9.gosub(script, ctx, "BaseCrawlInit") -- BASE2.inc:75
    do return ctx:exit("") end -- BASE2.inc:77
end

return script
