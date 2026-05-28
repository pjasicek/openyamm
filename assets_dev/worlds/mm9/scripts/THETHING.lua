-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "THETHING.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "TheThing.inc" }

-- TheThing.scr (john carpenter's)
-- by SJR
-- 11-04-01
-- Purpose:turn into a weirdo lookin
-- rastafied evil terror eye
-- thing with big pointy teeth
script.labels["Main"] = function(ctx)
    -- THETHING.scr:12
    -- OnPostStartWorld InitTheThing
    ctx:command("wait", "0, 5, InitTheThing") -- THETHING.scr:15
    do return ctx:exit(1) end -- THETHING.scr:17
end

return script
