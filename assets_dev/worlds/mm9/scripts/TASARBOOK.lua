-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TASARBOOK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- TaSarBook.scr
-- 10/4
-- timmy
-- handles Books and scrolls doing Letter interface
-- flag variables
script.labels["OnUse"] = function(ctx)
    -- TASARBOOK.scr:26
    -- This adds the item to inventory
    mm9.gosub(script, ctx, "Keycheck") -- TASARBOOK.scr:30
    mm9.gosub(script, ctx, "PlacedBook") -- TASARBOOK.scr:31
    if ctx:condition("bPlacedLastBook==FALSE") then -- TASARBOOK.scr:33
        do return ctx:exit("") end -- TASARBOOK.scr:34
    end -- TASARBOOK.scr:35
    if not ctx:hasKey(9516) then -- TASARBOOK.scr:37-38
        ctx:takeKey("Book_Key") -- TASARBOOK.scr:39
        ctx:state().g_hobject = ctx:self() -- TASARBOOK.scr:40
        ctx:self():setFlag("visible", false) -- TASARBOOK.scr:41
        ctx:self():setFlag("solid", false) -- TASARBOOK.scr:42
        ctx:self():setFlag("gravity", false) -- TASARBOOK.scr:43
        ctx:removeTrigger("Use") -- TASARBOOK.scr:44
        ctx:giveItem("item_ID") -- TASARBOOK.scr:45
        ctx:debugOut("Item_ID") -- TASARBOOK.scr:46
        do return ctx:exit("") end -- TASARBOOK.scr:47
    end -- TASARBOOK.scr:48
    do return ctx:exit("") end -- TASARBOOK.scr:49
end

script.labels["Init"] = function(ctx)
    -- TASARBOOK.scr:52
    -- This adds the item to inventory
    mm9.gosub(script, ctx, "KeyInit") -- TASARBOOK.scr:56
    if ctx:condition("Location!=Start") then -- TASARBOOK.scr:58
        ctx:state().g_hobject = ctx:self() -- TASARBOOK.scr:59
        ctx:self():setFlag("visible", false) -- TASARBOOK.scr:60
        ctx:self():setFlag("solid", false) -- TASARBOOK.scr:61
        ctx:self():setFlag("gravity", false) -- TASARBOOK.scr:62
        ctx:state().Invisible = 1 -- TASARBOOK.scr:63
        ctx:removeTrigger("use") -- TASARBOOK.scr:64
        do return ctx:exit("") end -- TASARBOOK.scr:65
    else -- TASARBOOK.scr:66
    end -- TASARBOOK.scr:67
    do return ctx:exit("") end -- TASARBOOK.scr:68
end

script.labels["PlacedBook"] = function(ctx)
    -- TASARBOOK.scr:71
    -- This checks to see if book is properly placed
    ctx:hasKey("Book_Key", "g_ntemp") -- TASARBOOK.scr:75
    if ctx:condition("g_ntemp==TRUE") then -- TASARBOOK.scr:77
        ctx:state().bPlacedLastBook = false -- TASARBOOK.scr:78
    end -- TASARBOOK.scr:79
    do return ctx:exit("") end -- TASARBOOK.scr:81
end

script.labels["KeyCheck"] = function(ctx)
    -- TASARBOOK.scr:85
    -- This adds the item to inventory
    if ctx:condition("nPlacedKey==0") then -- TASARBOOK.scr:89
        ctx:state().bPlacedLastBook = true -- TASARBOOK.scr:90
        do return ctx:exit("") end -- TASARBOOK.scr:91
    end -- TASARBOOK.scr:92
    if ctx:hasKey("nPlacedKey") then -- TASARBOOK.scr:94-95
        ctx:state().bPlacedLastBook = true -- TASARBOOK.scr:96
    end -- TASARBOOK.scr:97
    do return ctx:exit("") end -- TASARBOOK.scr:98
end

script.labels["KeyInit"] = function(ctx)
    -- TASARBOOK.scr:103
    -- This adds the item to inventory
    if ctx:condition("Item_ID==435") then -- TASARBOOK.scr:107
        ctx:state().Book_Key = 9501 -- TASARBOOK.scr:108
        ctx:state().nPlacedKey = 0 -- TASARBOOK.scr:109
        do return ctx:exit("") end -- TASARBOOK.scr:110
    end -- TASARBOOK.scr:111
    if ctx:condition("Item_ID==436") then -- TASARBOOK.scr:113
        ctx:state().Book_Key = 9502 -- TASARBOOK.scr:114
        ctx:state().nPlacedKey = 9517 -- TASARBOOK.scr:115
        do return ctx:exit("") end -- TASARBOOK.scr:116
    end -- TASARBOOK.scr:117
    if ctx:condition("Item_ID==437") then -- TASARBOOK.scr:119
        ctx:state().Book_Key = 9503 -- TASARBOOK.scr:120
        ctx:state().nPlacedKey = 9518 -- TASARBOOK.scr:121
        do return ctx:exit("") end -- TASARBOOK.scr:122
    end -- TASARBOOK.scr:123
    if ctx:condition("Item_ID==438") then -- TASARBOOK.scr:125
        ctx:state().Book_Key = 9504 -- TASARBOOK.scr:126
        ctx:state().nPlacedKey = 9519 -- TASARBOOK.scr:127
        do return ctx:exit("") end -- TASARBOOK.scr:128
    end -- TASARBOOK.scr:129
    do return ctx:exit("") end -- TASARBOOK.scr:131
end

script.labels["OnVisible"] = function(ctx)
    -- TASARBOOK.scr:134
    ctx:addTrigger("Use", "OnUse") -- TASARBOOK.scr:138
    ctx:state().g_hobject = ctx:self() -- TASARBOOK.scr:139
    ctx:self():setFlag("visible", true) -- TASARBOOK.scr:140
    ctx:self():setFlag("solid", true) -- TASARBOOK.scr:141
    ctx:self():setFlag("gravity", true) -- TASARBOOK.scr:142
    do return ctx:exit("") end -- TASARBOOK.scr:143
end

script.labels["Main"] = function(ctx)
    -- TASARBOOK.scr:146
    ctx:traceOn() -- TASARBOOK.scr:149
    -- Don't Forget to Delete this!
    ctx:getParam(0, "Item_ID") -- TASARBOOK.scr:151
    ctx:getParam(1, "Location") -- TASARBOOK.scr:152
    ctx:addTrigger("Use", "OnUse") -- TASARBOOK.scr:153
    ctx:addTrigger("Visible1", "OnVisible") -- TASARBOOK.scr:154
    ctx:onEvent("OnPostStartWorld", "Init") -- TASARBOOK.scr:156
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- TASARBOOK.scr:157
    ctx:onEvent("OnPostSaveLoad", "Init") -- TASARBOOK.scr:158
    ctx:wait(1, .1, "Init") -- TASARBOOK.scr:159
    do return ctx:exit("") end -- TASARBOOK.scr:160
end

return script
