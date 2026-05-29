-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARRAYMAKER.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 16, path = "ListMaker.inc" }

-- ArrayMaker.inc
-- by SJR
-- 10-31-01
-- Purpose:manager for a list of lists of
-- associative strings and objects
-- Notes:
-- These must be set by the parent script
-- ARRAYNAME   = base name of item list
-- ARRAYFIRST  = index of first marker
-- ARRAYSIZE   = number of objects per root name
-- ARRAYSTRIDE = number of objects in one association
script.labels["InitArrayMaker"] = function(ctx)
    -- ARRAYMAKER.inc:24
    ctx:set("LISTNAME", "ARRAYNAME") -- ARRAYMAKER.inc:26
    ctx:set("LISTFIRST", "ARRAYFIRST") -- ARRAYMAKER.inc:27
    ctx:set("LISTLAST", "ARRAYSIZE * ARRAYSTRIDE") -- ARRAYMAKER.inc:28
    do return ctx:exit(1) end -- ARRAYMAKER.inc:29
end

return script
