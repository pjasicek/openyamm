-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DAMAGECALC.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "DamageCalc.inc" }

script.labels["Main"] = function(ctx)
    -- DAMAGECALC.scr:4
    ctx:wait(0, 1, "InitDamageCalc") -- DAMAGECALC.scr:6
    do return ctx:exit(1) end -- DAMAGECALC.scr:7
end

return script
