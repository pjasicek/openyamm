-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FAKEBOOK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- fakebook.scr
-- By Timmy
-- gives the player the fake Verhoffin book
-- and the related key
-- fake book is item 242
script.labels["Onuse"] = function(ctx)
    -- FAKEBOOK.scr:15
    mm9.gosub(script, ctx, "haskey") -- FAKEBOOK.scr:18
end

-- haskey 4 g_ntemp
-- if (g_ntemp==1)
-- gosub haskey
-- exit
-- else
-- gosub nokey
-- exit
-- endif
script.labels["haskey"] = function(ctx)
    -- FAKEBOOK.scr:31
    if not ctx:hasKey(281) then -- FAKEBOOK.scr:33-34
        ctx:giveKey(281) -- FAKEBOOK.scr:35
        ctx:giveKey(290) -- FAKEBOOK.scr:36
        ctx:giveItem(242) -- FAKEBOOK.scr:37
        ctx:command("getmyhandle", "g_hmyobject") -- FAKEBOOK.scr:38
        ctx:command("removeobject", "g_hmyobject") -- FAKEBOOK.scr:39
        do return ctx:exit("") end -- FAKEBOOK.scr:40
    end -- FAKEBOOK.scr:41
    do return ctx:exit("") end -- FAKEBOOK.scr:42
end

script.labels["deletecheck"] = function(ctx)
    -- FAKEBOOK.scr:46
    if ctx:hasKey(282) then -- FAKEBOOK.scr:49-50
        ctx:command("getmyhandle", "g_hmyobject") -- FAKEBOOK.scr:51
        ctx:command("removeobject", "g_hmyobject") -- FAKEBOOK.scr:52
        do return ctx:exit("") end -- FAKEBOOK.scr:53
    end -- FAKEBOOK.scr:54
    if ctx:hasKey(281) then -- FAKEBOOK.scr:56-57
        ctx:command("getmyhandle", "g_hmyobject") -- FAKEBOOK.scr:58
        ctx:command("removeobject", "g_hmyobject") -- FAKEBOOK.scr:59
        do return ctx:exit("") end -- FAKEBOOK.scr:60
    end -- FAKEBOOK.scr:61
    do return ctx:exit("") end -- FAKEBOOK.scr:62
end

script.labels["Main"] = function(ctx)
    -- FAKEBOOK.scr:66
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- FAKEBOOK.scr:70
    mm9.gosub(script, ctx, "deletecheck") -- FAKEBOOK.scr:71
    do return ctx:exit("") end -- FAKEBOOK.scr:73
end

return script
