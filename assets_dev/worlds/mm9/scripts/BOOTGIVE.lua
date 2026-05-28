-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BOOTGIVE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Bootgive.scr
-- 10/4
-- timmy
-- gives party specific item on boot camp
-- Parameters
-- P0 Item number of item to give
script.labels["OnUse"] = function(ctx)
    -- BOOTGIVE.scr:26
    if ctx:condition("nGiveOnce==TRUE") then -- BOOTGIVE.scr:29
        if not ctx:hasItem("Item_ID") then -- BOOTGIVE.scr:30-31
            ctx:giveItem("item_ID") -- BOOTGIVE.scr:32
            ctx:command("getmyhandle", "g_hmyobject") -- BOOTGIVE.scr:33
            ctx:command("removeobject", "g_hmyobject") -- BOOTGIVE.scr:34
            do return ctx:exit("") end -- BOOTGIVE.scr:35
        end -- BOOTGIVE.scr:36
    else -- BOOTGIVE.scr:37
        ctx:giveItem("Item_ID") -- BOOTGIVE.scr:38
        ctx:command("getmyhandle", "g_hmyobject") -- BOOTGIVE.scr:39
        ctx:command("removeobject", "g_hmyobject") -- BOOTGIVE.scr:40
        do return ctx:exit("") end -- BOOTGIVE.scr:41
    end -- BOOTGIVE.scr:42
    do return ctx:exit("") end -- BOOTGIVE.scr:43
end

script.labels["Init"] = function(ctx)
    -- BOOTGIVE.scr:47
    ctx:command("loopanim", "Down 0 DoNothing") -- BOOTGIVE.scr:50
    if ctx:condition("nGiveOnce==FALSE") then -- BOOTGIVE.scr:52
        do return ctx:exit("") end -- BOOTGIVE.scr:53
    end -- BOOTGIVE.scr:54
    if ctx:hasItem("Item_ID") then -- BOOTGIVE.scr:56-57
        ctx:command("getmyhandle", "g_hmyobject") -- BOOTGIVE.scr:58
        ctx:command("removeobject", "g_hmyobject") -- BOOTGIVE.scr:59
        do return ctx:exit("") end -- BOOTGIVE.scr:60
    end -- BOOTGIVE.scr:61
    do return ctx:exit("") end -- BOOTGIVE.scr:62
end

script.labels["Main"] = function(ctx)
    -- BOOTGIVE.scr:65
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Use", "OnUse") -- BOOTGIVE.scr:70
    ctx:getParam(0, "Item_Id") -- BOOTGIVE.scr:71
    ctx:getParam(1, "nGiveOnce") -- BOOTGIVE.scr:72
    ctx:command("wait", "1 1 Init") -- BOOTGIVE.scr:73
    do return ctx:exit("") end -- BOOTGIVE.scr:75
end

return script
