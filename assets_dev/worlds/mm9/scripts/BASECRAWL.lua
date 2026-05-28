-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BASECRAWL.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "BaseCrawl.inc" }

-- BaseCrawl.inc
-- Jeff Leggett
-- 10/03/2001
-- Script for our 4-legged friends.....
script.labels["Main"] = function(ctx)
    -- BASECRAWL.scr:15
    mm9.gosub(script, ctx, "BaseCrawlInit") -- BASECRAWL.scr:18
    do return ctx:exit("") end -- BASECRAWL.scr:20
end

return script
