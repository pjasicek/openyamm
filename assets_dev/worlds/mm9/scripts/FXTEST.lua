-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FXTEST.scr"
script.includes = {}
script.labels = {}


-- FXTest.Scr
-- Attach this to a guy that you want
-- to test the FX system...
script.labels["Main"] = function(ctx)
    -- FXTEST.scr:9
    -- For now, just don't do anything....
    do return ctx:exit("") end -- FXTEST.scr:17
end

return script
