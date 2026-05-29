-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARG_UNHIDE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "pledge.inc" }

-- Arg_Unhide.scr
-- timmy
-- Hides or Unhides model based on player key
-- flag variables
-- parameters:
-- p0 The key to check for
-- p1 Hide or Unhide
script.labels["Init"] = function(ctx)
    -- ARG_UNHIDE.scr:26
    ctx:state().g_ncounter = 0 -- ARG_UNHIDE.scr:29
    if ctx:hasKey(94) then -- ARG_UNHIDE.scr:31-32
        mm9.gosub(script, ctx, "hide") -- ARG_UNHIDE.scr:33
        do return ctx:exit("") end -- ARG_UNHIDE.scr:34
    end -- ARG_UNHIDE.scr:35
    if ctx:hasKey(90) then -- ARG_UNHIDE.scr:37-38
        ctx:state().g_ncounter = (tonumber(ctx:state().g_ncounter) or 0) + 1 -- ARG_UNHIDE.scr:39
    end -- ARG_UNHIDE.scr:40
    if ctx:hasKey(91) then -- ARG_UNHIDE.scr:42-43
        ctx:state().g_nCounter = (tonumber(ctx:state().g_nCounter) or 0) + 1 -- ARG_UNHIDE.scr:44
    end -- ARG_UNHIDE.scr:45
    if ctx:condition("g_nCounter==2") then -- ARG_UNHIDE.scr:47
        mm9.gosub(script, ctx, "Unhide") -- ARG_UNHIDE.scr:48
    end -- ARG_UNHIDE.scr:49
    do return ctx:exit("") end -- ARG_UNHIDE.scr:50
end

script.labels["Unhide"] = function(ctx)
    -- ARG_UNHIDE.scr:55
    ctx:object("SvenProp"):setFlag("visible", true) -- ARG_UNHIDE.scr:58-59
    ctx:object("TryygvaProp"):setFlag("visible", true) -- ARG_UNHIDE.scr:61-62
    ctx:object("MarkeProp"):setFlag("visible", true) -- ARG_UNHIDE.scr:64-65
    ctx:object("BookProp"):setFlag("visible", true) -- ARG_UNHIDE.scr:67-68
    ctx:object("ForadProp"):setFlag("visible", true) -- ARG_UNHIDE.scr:70-71
    ctx:object("SigmundProp"):setFlag("visible", true) -- ARG_UNHIDE.scr:73-74
    ctx:object("TreatyProp"):setFlag("visible", true) -- ARG_UNHIDE.scr:76-77
    ctx:object("BjarniProp"):setFlag("visible", true) -- ARG_UNHIDE.scr:79-80
    do return ctx:exit("") end -- ARG_UNHIDE.scr:82
end

script.labels["Hide"] = function(ctx)
    -- ARG_UNHIDE.scr:87
    ctx:object("SvenProp"):setFlag("visible", false) -- ARG_UNHIDE.scr:90-91
    ctx:object("TryygvaProp"):setFlag("visible", false) -- ARG_UNHIDE.scr:93-94
    ctx:object("MarkeProp"):setFlag("visible", false) -- ARG_UNHIDE.scr:96-97
    ctx:object("BookProp"):setFlag("visible", false) -- ARG_UNHIDE.scr:99-100
    ctx:object("ForadProp"):setFlag("visible", false) -- ARG_UNHIDE.scr:102-103
    ctx:object("SigmundProp"):setFlag("visible", false) -- ARG_UNHIDE.scr:105-106
    ctx:object("TreatyProp"):setFlag("visible", false) -- ARG_UNHIDE.scr:108-109
    ctx:object("BjarniProp"):setFlag("visible", false) -- ARG_UNHIDE.scr:111-112
    do return ctx:exit("") end -- ARG_UNHIDE.scr:114
end

script.labels["Main"] = function(ctx)
    -- ARG_UNHIDE.scr:117
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onEvent("OnPostStartWorld", "Init") -- ARG_UNHIDE.scr:123
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- ARG_UNHIDE.scr:124
    ctx:onEvent("OnPostSaveLoad", "Init") -- ARG_UNHIDE.scr:125
    ctx:wait(1, 1, "Init") -- ARG_UNHIDE.scr:126
    do return ctx:exit("") end -- ARG_UNHIDE.scr:127
end

return script
