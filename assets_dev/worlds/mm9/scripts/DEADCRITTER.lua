-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DEADCRITTER.scr"
script.includes = {}
script.labels = {}


-- DeadCritter.scr
-- Karl
-- 10-15-01
-- Purpose: simply kill creatures at
-- level launch. "Corpse" prop.
script.labels["Main"] = function(ctx)
    -- DEADCRITTER.scr:10
    -- make sure we don't fade or bury
    ctx:self():setNumberProperty("FadeOnDeath", 0) -- DEADCRITTER.scr:13
    ctx:self():setNumberProperty("BuryOnDeath", 0) -- DEADCRITTER.scr:14
    ctx:self():die() -- DEADCRITTER.scr:16
    do return ctx:exit(1) end -- DEADCRITTER.scr:18
end

return script
