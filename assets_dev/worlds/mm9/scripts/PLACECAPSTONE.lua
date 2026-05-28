-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PLACECAPSTONE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- placeCapstone.scr
-- By Timmy
-- Places capstone of order onto the block
-- and the related key
-- Igrid's RudeID is 338
-- capstone is item 396
script.labels["Onuse"] = function(ctx)
    -- PLACECAPSTONE.scr:16
    mm9.gosub(script, ctx, "use1") -- PLACECAPSTONE.scr:19
    do return ctx:exit("") end -- PLACECAPSTONE.scr:20
end

script.labels["Use1"] = function(ctx)
    -- PLACECAPSTONE.scr:24
    if ctx:hasKey(98) then -- PLACECAPSTONE.scr:29-30
        if ctx:hasItem(396) then -- PLACECAPSTONE.scr:33-34
            ctx:command("getobjecthandle", "capstone g_hobject") -- PLACECAPSTONE.scr:35
            ctx:trigger("g_hobject", "place") -- PLACECAPSTONE.scr:36
            do return ctx:exit("") end -- PLACECAPSTONE.scr:37
        end -- PLACECAPSTONE.scr:38
    end -- PLACECAPSTONE.scr:39
    do return ctx:exit("") end -- PLACECAPSTONE.scr:40
end

script.labels["Main"] = function(ctx)
    -- PLACECAPSTONE.scr:44
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- PLACECAPSTONE.scr:48
    do return ctx:exit("") end -- PLACECAPSTONE.scr:50
end

return script
