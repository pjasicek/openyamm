-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GUNGNIR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- Gungnir.scr
-- By Timmy
-- gives the player the Golden Honk
-- item 369
script.labels["Onuse"] = function(ctx)
    -- GUNGNIR.scr:11
    if ctx:hasKey(353) then -- GUNGNIR.scr:14-15
        if not ctx:hasKey(354) then -- GUNGNIR.scr:16-17
            ctx:giveItem(189) -- GUNGNIR.scr:18
            ctx:giveKey(354) -- GUNGNIR.scr:19
            ctx:self():remove() -- GUNGNIR.scr:21
            do return ctx:exit("") end -- GUNGNIR.scr:22
        end -- GUNGNIR.scr:23
    else -- GUNGNIR.scr:24
        if not ctx:hasKey(355) then -- GUNGNIR.scr:25-26
            ctx:giveItem(189) -- GUNGNIR.scr:27
            ctx:giveKey(355) -- GUNGNIR.scr:28
            ctx:self():remove() -- GUNGNIR.scr:30
            do return ctx:exit("") end -- GUNGNIR.scr:31
        end -- GUNGNIR.scr:32
    end -- GUNGNIR.scr:33
    do return ctx:exit("") end -- GUNGNIR.scr:35
end

script.labels["DeleteCheck"] = function(ctx)
    -- GUNGNIR.scr:38
    if ctx:hasKey(354) then -- GUNGNIR.scr:41-42
        ctx:self():remove() -- GUNGNIR.scr:44
        do return ctx:exit("") end -- GUNGNIR.scr:45
    end -- GUNGNIR.scr:46
    if ctx:hasKey(355) then -- GUNGNIR.scr:48-49
        ctx:self():remove() -- GUNGNIR.scr:51
        do return ctx:exit("") end -- GUNGNIR.scr:52
    end -- GUNGNIR.scr:53
    do return ctx:exit("") end -- GUNGNIR.scr:54
end

script.labels["Main"] = function(ctx)
    -- GUNGNIR.scr:58
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- GUNGNIR.scr:62
    mm9.gosub(script, ctx, "DeleteCheck") -- GUNGNIR.scr:63
    do return ctx:exit("") end -- GUNGNIR.scr:64
end

return script
