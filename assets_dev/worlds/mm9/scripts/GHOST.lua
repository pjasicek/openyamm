-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GHOST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "range.inc" }

-- Ghost.scr
-- Handles Ghost who doesn't have any animations!
script.labels["Main"] = function(ctx)
    -- GHOST.scr:12
    mm9.gosub(script, ctx, "BaseCrawlInit") -- GHOST.scr:15
    mm9.gosub(script, ctx, "RangeInit") -- GHOST.scr:16
    do return ctx:exit("") end -- GHOST.scr:18
end

return script
