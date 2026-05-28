-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DAMAGECALC.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "TestingStuff.inc" }

script.labels["InitDamageCalc"] = function(ctx)
    -- DAMAGECALC.inc:13
    ctx:command("ondamage", "OnDamage") -- DAMAGECALC.inc:15
    ctx:addTrigger("use", "OnUse") -- DAMAGECALC.inc:16
    do return ctx:exit(1) end -- DAMAGECALC.inc:17
end

script.labels["OnDamage"] = function(ctx)
    -- DAMAGECALC.inc:20
    ctx:getParam(1, "nCurDamage") -- DAMAGECALC.inc:22
    ctx:command("cprint", "*************************") -- DAMAGECALC.inc:23
    mm9.gosub(script, ctx, "DisplayAttackRange") -- DAMAGECALC.inc:24
    mm9.gosub(script, ctx, "DisplayDamageValue") -- DAMAGECALC.inc:25
    do return ctx:exit(1) end -- DAMAGECALC.inc:26
end

script.labels["OnUse"] = function(ctx)
    -- DAMAGECALC.inc:29
    do return ctx:exit(1) end -- DAMAGECALC.inc:31
end

script.labels["DisplayAttackRange"] = function(ctx)
    -- DAMAGECALC.inc:34
    ctx:command("range_output", "= RANGE + nAttackMin + DASH + nAttackMax") -- DAMAGECALC.inc:36
    ctx:command("cprint", "RANGE_OUTPUT") -- DAMAGECALC.inc:37
    do return ctx:exit(1) end -- DAMAGECALC.inc:38
end

script.labels["DisplayDamageValue"] = function(ctx)
    -- DAMAGECALC.inc:41
    ctx:command("dmg_output", "= DMG + nCurDamage") -- DAMAGECALC.inc:43
    ctx:command("cprint", "DMG_OUTPUT") -- DAMAGECALC.inc:44
    do return ctx:exit(1) end -- DAMAGECALC.inc:45
end

return script
