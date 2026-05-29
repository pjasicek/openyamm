-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HIDEMODEL.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "pledge.inc" }

-- ChangeModel.scr
-- timmy
-- Hides or Unhides model based on player key
-- flag variables
-- parameters:
-- p0 The key to check for
-- p1 Hide or Unhide
script.labels["Init"] = function(ctx)
    -- HIDEMODEL.scr:26
    if ctx:condition("sHideStatus==Hide") then -- HIDEMODEL.scr:29
        mm9.gosub(script, ctx, "Hide") -- HIDEMODEL.scr:30
    else -- HIDEMODEL.scr:31
        mm9.gosub(script, ctx, "Unhide") -- HIDEMODEL.scr:32
    end -- HIDEMODEL.scr:33
    do return ctx:exit("") end -- HIDEMODEL.scr:34
end

script.labels["Hide"] = function(ctx)
    -- HIDEMODEL.scr:37
    if ctx:hasKey("nKey") then -- HIDEMODEL.scr:40-41
        ctx:state().g_hobject = ctx:self() -- HIDEMODEL.scr:42
        ctx:self():setFlag("visible", false) -- HIDEMODEL.scr:43
        ctx:self():setFlag("solid", false) -- HIDEMODEL.scr:44
        ctx:self():setFlag("gravity", false) -- HIDEMODEL.scr:45
    else -- HIDEMODEL.scr:46
        ctx:state().g_hobject = ctx:self() -- HIDEMODEL.scr:47
        ctx:self():setFlag("visible", true) -- HIDEMODEL.scr:48
        ctx:self():setFlag("solid", true) -- HIDEMODEL.scr:49
        ctx:self():setFlag("gravity", true) -- HIDEMODEL.scr:50
    end -- HIDEMODEL.scr:51
    do return ctx:exit("") end -- HIDEMODEL.scr:52
end

script.labels["Unhide"] = function(ctx)
    -- HIDEMODEL.scr:55
    if ctx:hasKey("nKey") then -- HIDEMODEL.scr:58-59
        ctx:state().g_hobject = ctx:self() -- HIDEMODEL.scr:60
        ctx:self():setFlag("visible", true) -- HIDEMODEL.scr:61
        ctx:self():setFlag("solid", true) -- HIDEMODEL.scr:62
        ctx:self():setFlag("gravity", true) -- HIDEMODEL.scr:63
    else -- HIDEMODEL.scr:64
        ctx:state().g_hobject = ctx:self() -- HIDEMODEL.scr:65
        ctx:self():setFlag("visible", false) -- HIDEMODEL.scr:66
        ctx:self():setFlag("solid", false) -- HIDEMODEL.scr:67
        ctx:self():setFlag("gravity", false) -- HIDEMODEL.scr:68
    end -- HIDEMODEL.scr:69
    do return ctx:exit("") end -- HIDEMODEL.scr:70
end

script.labels["Main"] = function(ctx)
    -- HIDEMODEL.scr:73
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "nKey") -- HIDEMODEL.scr:79
    ctx:getParam(1, "sHideStatus") -- HIDEMODEL.scr:80
    ctx:wait(1, 1, "Init") -- HIDEMODEL.scr:81
    ctx:onEvent("OnPostStartWorld", "Init") -- HIDEMODEL.scr:82
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- HIDEMODEL.scr:83
    ctx:onEvent("OnPostSaveLoad", "Init") -- HIDEMODEL.scr:84
    do return ctx:exit("") end -- HIDEMODEL.scr:85
end

return script
