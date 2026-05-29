-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TASARTABLE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- TaSarTable.scr
-- 10/5
-- timmy
-- handles Books and scrolls doing Letter interface
-- flag variables
script.labels["OnUse"] = function(ctx)
    -- TASARTABLE.scr:27
    -- This adds the item to inventory
    if ctx:hasItem("Book") then -- TASARTABLE.scr:32-33
        ctx:giveKey("Book_key") -- TASARTABLE.scr:34
        ctx:giveKey("nPlacedKey") -- TASARTABLE.scr:35
    end -- TASARTABLE.scr:36
    ctx:state().Counter = 0 -- TASARTABLE.scr:39
    while ctx:condition("Counter<4") do -- TASARTABLE.scr:40
        ctx:hasItem("Item_ID", "g_ntemp") -- TASARTABLE.scr:42
        ctx:debugOut("Item_ID") -- TASARTABLE.scr:43
        if ctx:condition("G_ntemp==1") then -- TASARTABLE.scr:44
            ctx:state().g_hobject = ctx:objectOrNil("Item_name") -- TASARTABLE.scr:46
            ctx:takeItem("Item_ID") -- TASARTABLE.scr:47
            -- Setflag g_hobject, visible
            -- Setflag g_hobject, solid
            -- Setflag g_hobject, gravity
            ctx:trigger("g_hobject", "Visible1") -- TASARTABLE.scr:51
        end -- TASARTABLE.scr:52
        ctx:state().Item_Id = (tonumber(ctx:state().Item_Id) or 0) + 1 -- TASARTABLE.scr:54
        ctx:set("Item_Name", "Location + Item_ID") -- TASARTABLE.scr:55
        ctx:state().Counter = (tonumber(ctx:state().Counter) or 0) + 1 -- TASARTABLE.scr:56
    end -- TASARTABLE.scr:57
    ctx:state().Item_Id = 435 -- TASARTABLE.scr:59
    mm9.gosub(script, ctx, "CompleteCheck") -- TASARTABLE.scr:60
    do return ctx:exit("") end -- TASARTABLE.scr:61
end

script.labels["CompleteCheck"] = function(ctx)
    -- TASARTABLE.scr:66
    -- This puts the keys into an array
    if ctx:hasKey(9501) then -- TASARTABLE.scr:70-71
        ctx:arrayPut("KeyArray", 0, 1) -- TASARTABLE.scr:72
    end -- TASARTABLE.scr:73
    if ctx:hasKey(9502) then -- TASARTABLE.scr:75-76
        ctx:arrayPut("KeyArray", 1, 1) -- TASARTABLE.scr:77
    end -- TASARTABLE.scr:78
    if ctx:hasKey(9503) then -- TASARTABLE.scr:80-81
        ctx:arrayPut("KeyArray", 2, 1) -- TASARTABLE.scr:82
    end -- TASARTABLE.scr:83
    if ctx:hasKey(9504) then -- TASARTABLE.scr:85-86
        ctx:arrayPut("KeyArray", 3, 1) -- TASARTABLE.scr:87
    end -- TASARTABLE.scr:88
    mm9.gosub(script, ctx, "CheckAllKeys") -- TASARTABLE.scr:90
    do return ctx:exit("") end -- TASARTABLE.scr:91
end

script.labels["CheckAllKeys"] = function(ctx)
    -- TASARTABLE.scr:94
    -- This checks the keys in the array
    ctx:state().Counter = 0 -- TASARTABLE.scr:98
    while ctx:condition("counter!=4") do -- TASARTABLE.scr:100
        ctx:arrayGet("KeyArray", "Counter", "g_ntemp") -- TASARTABLE.scr:101
        if ctx:condition("g_ntemp==0") then -- TASARTABLE.scr:102
            do return ctx:exit("") end -- TASARTABLE.scr:103
        end -- TASARTABLE.scr:104
        ctx:state().Counter = (tonumber(ctx:state().Counter) or 0) + 1 -- TASARTABLE.scr:106
    end -- TASARTABLE.scr:108
    -- ........success.........
    ctx:giveKey(9516) -- TASARTABLE.scr:112
    local object = ctx:object("LibraryDoor") -- TASARTABLE.scr:113
    object:trigger("unlock") -- TASARTABLE.scr:114
    object:trigger("use") -- TASARTABLE.scr:115
    object:trigger("lock") -- TASARTABLE.scr:116
    do return ctx:exit("") end -- TASARTABLE.scr:117
end

script.labels["ItemInit"] = function(ctx)
    -- TASARTABLE.scr:120
    -- This inits the variables
    ctx:set("Item_Name", "Location + Item_ID") -- TASARTABLE.scr:124
    if ctx:condition("Location==Offense") then -- TASARTABLE.scr:126
        ctx:state().Book_Key = 9501 -- TASARTABLE.scr:127
        ctx:state().Book = 435 -- TASARTABLE.scr:128
        ctx:state().nPlacedKey = 9517 -- TASARTABLE.scr:129
        do return ctx:exit("") end -- TASARTABLE.scr:130
    end -- TASARTABLE.scr:131
    if ctx:condition("Location==Strategy") then -- TASARTABLE.scr:133
        ctx:state().Book_Key = 9502 -- TASARTABLE.scr:134
        ctx:state().Book = 436 -- TASARTABLE.scr:135
        ctx:state().nPlacedKey = 9518 -- TASARTABLE.scr:136
        do return ctx:exit("") end -- TASARTABLE.scr:137
    end -- TASARTABLE.scr:138
    if ctx:condition("Location==Defense") then -- TASARTABLE.scr:140
        ctx:state().Book_Key = 9503 -- TASARTABLE.scr:141
        ctx:state().Book = 437 -- TASARTABLE.scr:142
        ctx:state().nPlacedKey = 9519 -- TASARTABLE.scr:143
        do return ctx:exit("") end -- TASARTABLE.scr:144
    end -- TASARTABLE.scr:145
    if ctx:condition("Location==Intelligence") then -- TASARTABLE.scr:147
        ctx:state().Book_Key = 9504 -- TASARTABLE.scr:148
        ctx:state().Book = 438 -- TASARTABLE.scr:149
        ctx:state().nPlacedKey = 9520 -- TASARTABLE.scr:150
        do return ctx:exit("") end -- TASARTABLE.scr:151
    end -- TASARTABLE.scr:152
    do return ctx:exit("") end -- TASARTABLE.scr:154
end

script.labels["Main"] = function(ctx)
    -- TASARTABLE.scr:158
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "Location") -- TASARTABLE.scr:163
    ctx:addTrigger("Use", "OnUse") -- TASARTABLE.scr:164
    mm9.gosub(script, ctx, "ItemInit") -- TASARTABLE.scr:165
    do return ctx:exit("") end -- TASARTABLE.scr:167
end

return script
