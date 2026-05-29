-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GIVETAKE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- givetake.scr
-- 10/4
-- timmy
-- gives party specific item
-- Parameters
-- P0 Item number of item to give
script.labels["OnUse"] = function(ctx)
    -- GIVETAKE.scr:26
    if ctx:condition("nGiveOnce==TRUE") then -- GIVETAKE.scr:29
        if not ctx:hasItem("Item_ID") then -- GIVETAKE.scr:30-31
            ctx:giveItem("item_ID") -- GIVETAKE.scr:32
            ctx:self():remove() -- GIVETAKE.scr:34
            do return ctx:exit("") end -- GIVETAKE.scr:35
        end -- GIVETAKE.scr:36
    else -- GIVETAKE.scr:37
        ctx:giveItem("Item_ID") -- GIVETAKE.scr:38
        ctx:self():remove() -- GIVETAKE.scr:40
        do return ctx:exit("") end -- GIVETAKE.scr:41
    end -- GIVETAKE.scr:42
    do return ctx:exit("") end -- GIVETAKE.scr:43
end

script.labels["Init"] = function(ctx)
    -- GIVETAKE.scr:47
    if ctx:condition("nGiveOnce==FALSE") then -- GIVETAKE.scr:52
        do return ctx:exit("") end -- GIVETAKE.scr:53
    end -- GIVETAKE.scr:54
    if ctx:hasItem("Item_ID") then -- GIVETAKE.scr:56-57
        ctx:self():remove() -- GIVETAKE.scr:59
        do return ctx:exit("") end -- GIVETAKE.scr:60
    end -- GIVETAKE.scr:61
    do return ctx:exit("") end -- GIVETAKE.scr:62
end

script.labels["Main"] = function(ctx)
    -- GIVETAKE.scr:65
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Use", "OnUse") -- GIVETAKE.scr:70
    ctx:getParam(0, "Item_Id") -- GIVETAKE.scr:71
    ctx:getParam(1, "nGiveOnce") -- GIVETAKE.scr:72
    ctx:wait(1, 1, "Init") -- GIVETAKE.scr:73
    do return ctx:exit("") end -- GIVETAKE.scr:75
end

return script
