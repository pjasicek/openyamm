-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LISTMAKER.inc"
script.includes = {}
script.labels = {}


-- ListMaker.inc
-- by SJR
-- 10-31-01
-- Purpose:manager for a circular list of
-- strings\objects for use with
-- long marker paths etc
-- Notes:
-- These must be set by the parent script
-- LISTNAME = base name of item list
-- LISTFIRST= index of first marker
-- LISTLAST = index of last marker
-- outputs
-- contains the requested object
-- TRUE when at the ends of the list
-- index of objectname
-- inputs
-- base name of object list, ie Marker of Marker[x]
-- index of last one, ie 0 of Marker0
-- index of first one, ie 9 of Marker9
-- *** 4 steps (gosubs) on each of these ***
-- 1.	adjust index of string
-- 2.	check for ends of list
-- 3. make string name from index
-- 4. get hobject with above stringname
script.labels["GetLastObject"] = function(ctx)
    -- LISTMAKER.inc:42
    -- gets the object with the last index
    mm9.gosub(script, ctx, "list_SuffixMax") -- LISTMAKER.inc:45
    mm9.gosub(script, ctx, "list_CheckPos") -- LISTMAKER.inc:46
    mm9.gosub(script, ctx, "list_MakeName") -- LISTMAKER.inc:47
    mm9.gosub(script, ctx, "list_MakeObject") -- LISTMAKER.inc:48
    do return ctx:exit(1) end -- LISTMAKER.inc:49
end

script.labels["GetFirstObject"] = function(ctx)
    -- LISTMAKER.inc:52
    -- gets the object with the first index
    mm9.gosub(script, ctx, "list_SuffixMin") -- LISTMAKER.inc:55
    mm9.gosub(script, ctx, "list_CheckPos") -- LISTMAKER.inc:56
    mm9.gosub(script, ctx, "list_MakeName") -- LISTMAKER.inc:57
    mm9.gosub(script, ctx, "list_MakeObject") -- LISTMAKER.inc:58
    do return ctx:exit(1) end -- LISTMAKER.inc:59
end

script.labels["GetNextObject"] = function(ctx)
    -- LISTMAKER.inc:62
    -- gets the next object numerically
    mm9.gosub(script, ctx, "list_SuffixAdd") -- LISTMAKER.inc:65
    mm9.gosub(script, ctx, "list_CheckPos") -- LISTMAKER.inc:66
    mm9.gosub(script, ctx, "list_MakeName") -- LISTMAKER.inc:67
    mm9.gosub(script, ctx, "list_MakeObject") -- LISTMAKER.inc:68
    do return ctx:exit(1) end -- LISTMAKER.inc:69
end

script.labels["GetPreviousObject"] = function(ctx)
    -- LISTMAKER.inc:72
    -- gets the previous object numerically
    mm9.gosub(script, ctx, "list_SuffixSub") -- LISTMAKER.inc:75
    mm9.gosub(script, ctx, "list_CheckPos") -- LISTMAKER.inc:76
    mm9.gosub(script, ctx, "list_MakeName") -- LISTMAKER.inc:77
    mm9.gosub(script, ctx, "list_MakeObject") -- LISTMAKER.inc:78
    do return ctx:exit(1) end -- LISTMAKER.inc:79
end

script.labels["GetCurrentObject"] = function(ctx)
    -- LISTMAKER.inc:82
    -- gets the current object numerically
    -- used for manually setting LISTINDEX
    -- and for changing between lists
    mm9.gosub(script, ctx, "list_MakeName") -- LISTMAKER.inc:87
    mm9.gosub(script, ctx, "list_MakeObject") -- LISTMAKER.inc:88
    do return ctx:exit(1) end -- LISTMAKER.inc:89
end

-- private
-- keep out! do not screw with these.
script.labels["list_SuffixMin"] = function(ctx)
    -- LISTMAKER.inc:96
    ctx:command("listindex", "= LISTFIRST") -- LISTMAKER.inc:97
    do return ctx:exit(1) end -- LISTMAKER.inc:98
end

script.labels["list_SuffixMax"] = function(ctx)
    -- LISTMAKER.inc:100
    ctx:command("listindex", "= LISTLAST") -- LISTMAKER.inc:101
    do return ctx:exit(1) end -- LISTMAKER.inc:102
end

script.labels["list_SuffixAdd"] = function(ctx)
    -- LISTMAKER.inc:104
    if ctx:condition("LISTINDEX==LISTLAST") then -- LISTMAKER.inc:105
        ctx:command("listindex", "= LISTFIRST") -- LISTMAKER.inc:106
    else -- LISTMAKER.inc:107
        ctx:command("listindex", "= LISTINDEX + 1") -- LISTMAKER.inc:108
    end -- LISTMAKER.inc:109
    do return ctx:exit(1) end -- LISTMAKER.inc:110
end

script.labels["list_SuffixSub"] = function(ctx)
    -- LISTMAKER.inc:112
    if ctx:condition("LISTINDEX == 0") then -- LISTMAKER.inc:113
        ctx:command("listindex", "= LISTLAST") -- LISTMAKER.inc:114
    else -- LISTMAKER.inc:115
        ctx:command("listindex", "= LISTINDEX - 1") -- LISTMAKER.inc:116
    end -- LISTMAKER.inc:117
    do return ctx:exit(1) end -- LISTMAKER.inc:118
end

script.labels["list_MakeName"] = function(ctx)
    -- LISTMAKER.inc:120
    ctx:command("finalname", "= LISTNAME + LISTINDEX") -- LISTMAKER.inc:121
    do return ctx:exit(1) end -- LISTMAKER.inc:122
end

script.labels["list_MakeObject"] = function(ctx)
    -- LISTMAKER.inc:124
    ctx:command("getobjecthandle", "FINALNAME, LISTOBJECT") -- LISTMAKER.inc:125
    if ctx:condition("LISTOBJECT==0") then -- LISTMAKER.inc:126
        -- cprint "ListMaker.inc retrieved NULL handle for:"
        -- cprint FINALNAME
    end -- LISTMAKER.inc:129
    do return ctx:exit(1) end -- LISTMAKER.inc:130
end

script.labels["list_CheckPos"] = function(ctx)
    -- LISTMAKER.inc:132
    ctx:command("arrivedlast", "= 0") -- LISTMAKER.inc:133
    ctx:command("arrivedfirst", "= 0") -- LISTMAKER.inc:134
    if ctx:condition("LISTINDEX==LISTLAST") then -- LISTMAKER.inc:135
        ctx:command("arrivedlast", "= 1") -- LISTMAKER.inc:136
    end -- LISTMAKER.inc:137
    if ctx:condition("LISTINDEX==LISTFIRST") then -- LISTMAKER.inc:138
        ctx:command("arrivedfirst", "= 1") -- LISTMAKER.inc:139
    end -- LISTMAKER.inc:140
    do return ctx:exit(1) end -- LISTMAKER.inc:141
end

return script
