-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "THEIT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "TheIt.inc" }

-- TheIt.scr (stephen king's)
-- by SJR
-- 11-04-01
-- Purpose:turn into a weirdo lookin
-- spiky skeleton mutant
-- thing with big pointy teeth
script.labels["Main"] = function(ctx)
    -- THEIT.scr:12
    -- OnPostStartWorld InitTheIt
    ctx:wait(0, 5, "InitTheIt") -- THEIT.scr:15
    do return ctx:exit(1) end -- THEIT.scr:17
end

return script
