-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CRAWLRANGE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "BaseCrawl.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "Range.inc" }

-- CrawlRange.inc
-- Jeff Leggett
-- 10/22/2001
-- Script for our 4-legged friends that shoot....
script.labels["Main"] = function(ctx)
    -- CRAWLRANGE.scr:15
    mm9.gosub(script, ctx, "BaseCrawlInit") -- CRAWLRANGE.scr:18
    mm9.gosub(script, ctx, "RangeInit") -- CRAWLRANGE.scr:19
    do return ctx:exit("") end -- CRAWLRANGE.scr:21
end

return script
