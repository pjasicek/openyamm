-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GLOBALS.inc"
script.includes = {}
script.labels = {}


-- GLOBALS.INC
-- Put commonly used global variables here....
-- I start these all with g_ so we know that they are (global) from
-- an include file...
-- for booleans...
-- Use this string for debugOut statements
-- These are here for padding only.  This will help to prevent save-game breakage
-- for minor script bug fixes.
script.labels["DoNothing"] = function(ctx)
    -- GLOBALS.inc:73
    -- This function is true to its name.  Useful for canceling
    -- callbacks...
    do return ctx:exit("") end -- GLOBALS.inc:77
end

return script
