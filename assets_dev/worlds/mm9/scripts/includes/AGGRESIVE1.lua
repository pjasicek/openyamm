-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "AGGRESIVE1.inc"
script.includes = {}
script.labels = {}


-- Agressive1.inc
-- Aggresively go after target....
-- NOTE: this include is dependent on base.inc....
script.labels["Aggresive1Tick"] = function(ctx)
    -- AGGRESIVE1.inc:15
    do return ctx:exit("") end -- AGGRESIVE1.inc:19
end

script.labels["Aggresive1Start"] = function(ctx)
    -- AGGRESIVE1.inc:22
    ctx:wait("AGGRESIVE_WAIT", "AGGRESIVE_TICK", "Aggresive1Tick") -- AGGRESIVE1.inc:25
    do return ctx:exit("") end -- AGGRESIVE1.inc:27
end

return script
