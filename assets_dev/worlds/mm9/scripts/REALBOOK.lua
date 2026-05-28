-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "REALBOOK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- realbook.scr
-- By Timmy
-- gives the player verhoffin's real book.
-- and the related key
-- real book is item 243
script.labels["Onuse"] = function(ctx)
    -- REALBOOK.scr:15
    mm9.gosub(script, ctx, "haskey") -- REALBOOK.scr:18
end

script.labels["haskey"] = function(ctx)
    -- REALBOOK.scr:24
    if not ctx:hasKey(283) then -- REALBOOK.scr:27-28
        if ctx:hasItem(244) then -- REALBOOK.scr:29-30
            ctx:giveItem(347) -- REALBOOK.scr:31
            ctx:giveItem(560) -- REALBOOK.scr:32
            ctx:giveKey(283) -- REALBOOK.scr:33
            ctx:giveKey(290) -- REALBOOK.scr:34
            ctx:command("getmyhandle", "g_hmyobject") -- REALBOOK.scr:35
            ctx:command("removeobject", "g_hmyobject") -- REALBOOK.scr:36
            do return ctx:exit("") end -- REALBOOK.scr:37
        end -- REALBOOK.scr:38
    end -- REALBOOK.scr:39
    do return ctx:exit("") end -- REALBOOK.scr:40
end

script.labels["deletecheck"] = function(ctx)
    -- REALBOOK.scr:44
    if ctx:hasKey(284) then -- REALBOOK.scr:47-48
        ctx:command("getmyhandle", "g_hmyobject") -- REALBOOK.scr:49
        ctx:command("removeobject", "g_hmyobject") -- REALBOOK.scr:50
        do return ctx:exit("") end -- REALBOOK.scr:51
    end -- REALBOOK.scr:52
    if ctx:hasKey(283) then -- REALBOOK.scr:54-55
        ctx:command("getmyhandle", "g_hmyobject") -- REALBOOK.scr:56
        ctx:command("removeobject", "g_hmyobject") -- REALBOOK.scr:57
        do return ctx:exit("") end -- REALBOOK.scr:58
    end -- REALBOOK.scr:59
    do return ctx:exit("") end -- REALBOOK.scr:60
end

script.labels["Main"] = function(ctx)
    -- REALBOOK.scr:64
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- REALBOOK.scr:68
    mm9.gosub(script, ctx, "deletecheck") -- REALBOOK.scr:69
    do return ctx:exit("") end -- REALBOOK.scr:71
end

return script
