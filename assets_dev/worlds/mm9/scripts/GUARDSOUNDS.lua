-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GUARDSOUNDS.scr"
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
    -- GUARDSOUNDS.scr:15
    mm9.gosub(script, ctx, "GS_Init") -- GUARDSOUNDS.scr:21
    ctx:command("loopanim", "sleep 0 DoNothing") -- GUARDSOUNDS.scr:22
    do return ctx:exit("") end -- GUARDSOUNDS.scr:24
end

return script
