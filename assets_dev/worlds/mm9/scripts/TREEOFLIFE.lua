-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TREEOFLIFE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- TreeofLife.scr
-- By Timmy
-- gives the player the Tree of Life
-- and the related key
-- tree of life is item 241
script.labels["Onuse"] = function(ctx)
    -- TREEOFLIFE.scr:15
    if not ctx:hasKey(256) then -- TREEOFLIFE.scr:19-20
        ctx:giveItem(241) -- TREEOFLIFE.scr:21
        ctx:giveKey(256) -- TREEOFLIFE.scr:22
        ctx:command("getmyhandle", "g_hmyobject") -- TREEOFLIFE.scr:23
        ctx:command("removeobject", "g_hmyobject") -- TREEOFLIFE.scr:24
        ctx:command("getobjecthandle", "TriggerCaveIn1 g_hobject") -- TREEOFLIFE.scr:25
        ctx:trigger("g_hobject", "on") -- TREEOFLIFE.scr:26
        do return ctx:exit("") end -- TREEOFLIFE.scr:27
    end -- TREEOFLIFE.scr:28
end

script.labels["Main"] = function(ctx)
    -- TREEOFLIFE.scr:34
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- TREEOFLIFE.scr:38
    -- SJR
    ctx:command("getobjecthandle", "TriggerCaveIn1 g_hobject") -- TREEOFLIFE.scr:41
    ctx:trigger("g_hobject", "off") -- TREEOFLIFE.scr:42
    -- endSJR
    ctx:hasKey(256, "keycheck") -- TREEOFLIFE.scr:45
    if ctx:condition("g_ntemp==1") then -- TREEOFLIFE.scr:46
        ctx:command("getmyhandle", "g_hmyobject") -- TREEOFLIFE.scr:47
        ctx:command("removeobject", "g_hmyobject") -- TREEOFLIFE.scr:48
        ctx:command("exitscript", "") -- TREEOFLIFE.scr:49
        do return ctx:exit("") end -- TREEOFLIFE.scr:50
    end -- TREEOFLIFE.scr:51
    do return ctx:exit("") end -- TREEOFLIFE.scr:53
end

return script
