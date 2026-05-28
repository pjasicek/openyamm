-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TITAN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "BaseCrawl.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "Range.inc" }

-- Titan.Scr
-- Jeff Leggett
-- Big Bad Ass Dude!
script.labels["Main"] = function(ctx)
    -- TITAN.scr:13
    mm9.gosub(script, ctx, "BaseCrawlInit") -- TITAN.scr:16
    mm9.gosub(script, ctx, "RangeInit") -- TITAN.scr:17
    do return ctx:exit("") end -- TITAN.scr:19
end

return script
