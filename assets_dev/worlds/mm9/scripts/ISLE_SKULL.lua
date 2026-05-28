-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ISLE_SKULL.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "PropLauncher.inc" }

-- Isle_Skull.scr
-- Jeff Leggett
-- 12/06/2001
-- Skulls that are thrown at the player at the beginning
-- of IsleOfAshes...
script.labels["Main"] = function(ctx)
    -- ISLE_SKULL.scr:15
    -- Just use all the defaults...
    mm9.gosub(script, ctx, "PropLauncherInit") -- ISLE_SKULL.scr:22
    do return ctx:exit("") end -- ISLE_SKULL.scr:24
end

return script
