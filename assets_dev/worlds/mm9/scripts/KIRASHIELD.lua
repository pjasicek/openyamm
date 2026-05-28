-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "KIRASHIELD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Kirashield.scr
-- By Timmy
-- gives the player ludwig's manuscript
-- and the related key
-- Kira's Shield is item 375
script.labels["Onuse"] = function(ctx)
    -- KIRASHIELD.scr:15
    if not ctx:hasKey(216) then -- KIRASHIELD.scr:18-19
        if ctx:hasKey(214) then -- KIRASHIELD.scr:20-21
            ctx:giveKey(216) -- KIRASHIELD.scr:22
            ctx:giveItem(375) -- KIRASHIELD.scr:23
            ctx:command("getmyhandle", "g_hmyobject") -- KIRASHIELD.scr:24
            ctx:command("removeobject", "g_hmyobject") -- KIRASHIELD.scr:25
            do return ctx:exit("") end -- KIRASHIELD.scr:26
        end -- KIRASHIELD.scr:27
    end -- KIRASHIELD.scr:28
    do return ctx:exit("") end -- KIRASHIELD.scr:29
end

script.labels["OnDelete"] = function(ctx)
    -- KIRASHIELD.scr:33
    if ctx:hasKey(216) then -- KIRASHIELD.scr:36-37
        ctx:command("getmyhandle", "g_hmyobject") -- KIRASHIELD.scr:38
        ctx:command("removeobject", "g_hmyobject") -- KIRASHIELD.scr:39
        do return ctx:exit("") end -- KIRASHIELD.scr:40
    end -- KIRASHIELD.scr:41
    do return ctx:exit("") end -- KIRASHIELD.scr:42
end

script.labels["Main"] = function(ctx)
    -- KIRASHIELD.scr:45
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- KIRASHIELD.scr:49
    mm9.gosub(script, ctx, "OnDelete") -- KIRASHIELD.scr:50
    do return ctx:exit("") end -- KIRASHIELD.scr:51
end

return script
