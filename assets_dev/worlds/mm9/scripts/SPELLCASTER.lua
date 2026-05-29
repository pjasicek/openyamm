-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SPELLCASTER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 13, path = "range.inc" }

-- spellcaster.scr
-- Jeff Leggett
-- 12/13/2001
-- This script is used by monsters that
-- can cast defensive spells on itself
-- and others....
script.labels["Main"] = function(ctx)
    -- SPELLCASTER.scr:17
    -- This routine is automatically run
    -- at script startup...
    -- Make sure we are setup as a type 2 guy...
    ctx:self():setStat("RangeAttackType", "RANGE_TYPE2") -- SPELLCASTER.scr:27
    mm9.gosub(script, ctx, "BaseInit") -- SPELLCASTER.scr:29
    mm9.gosub(script, ctx, "RangeInit") -- SPELLCASTER.scr:30
    do return ctx:exit("") end -- SPELLCASTER.scr:32
end

return script
