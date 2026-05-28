-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GUARDBASE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "Basemelee.scr" }
script.includes[#script.includes + 1] = { line = 10, path = "guardsounds.inc" }

-- Guardsounds.scr
-- timmy
-- 10/30
-- randomizes guard idle sounds.
script.labels["Main"] = function(ctx)
    -- GUARDBASE.scr:15
    mm9.gosub(script, ctx, "BaseInit") -- GUARDBASE.scr:20
    mm9.gosub(script, ctx, "GS_Init") -- GUARDBASE.scr:21
    do return ctx:exit("") end -- GUARDBASE.scr:24
end

return script
