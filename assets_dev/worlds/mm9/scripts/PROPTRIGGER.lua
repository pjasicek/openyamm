-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PROPTRIGGER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- SkillBook.scr
-- 10/4
-- timmy
-- Triggers one prop with another
-- Parameters
-- P0 The object name of the target
-- P1 the trigger message to send
script.labels["OnUse"] = function(ctx)
    -- PROPTRIGGER.scr:24
    if ctx:condition("nLinked==FALSE") then -- PROPTRIGGER.scr:27
        do return ctx:exit("") end -- PROPTRIGGER.scr:28
    end -- PROPTRIGGER.scr:29
    ctx:state().g_hobject = ctx:objectOrNil("Target") -- PROPTRIGGER.scr:31
    if ctx:condition("g_hobject!=null") then -- PROPTRIGGER.scr:32
        ctx:trigger("g_hobject", "message") -- PROPTRIGGER.scr:33
        do return ctx:exit("") end -- PROPTRIGGER.scr:34
    end -- PROPTRIGGER.scr:35
    do return ctx:exit("") end -- PROPTRIGGER.scr:36
end

script.labels["Init"] = function(ctx)
    -- PROPTRIGGER.scr:39
    ctx:state().g_hobject = ctx:objectOrNil("Target") -- PROPTRIGGER.scr:42
    if ctx:condition("g_hobject!=NULL") then -- PROPTRIGGER.scr:43
        ctx:self():link(ctx:object("g_hobject")) -- PROPTRIGGER.scr:44
        ctx:onEvent("OnObjectLinkBroken", "BreakLink") -- PROPTRIGGER.scr:45
        ctx:state().nLinked = true -- PROPTRIGGER.scr:46
        do return ctx:exit("") end -- PROPTRIGGER.scr:47
    end -- PROPTRIGGER.scr:48
    do return ctx:exit("") end -- PROPTRIGGER.scr:49
end

script.labels["BreakLink"] = function(ctx)
    -- PROPTRIGGER.scr:52
    ctx:state().nLinked = false -- PROPTRIGGER.scr:55
    do return ctx:exit("") end -- PROPTRIGGER.scr:56
end

script.labels["Main"] = function(ctx)
    -- PROPTRIGGER.scr:59
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Use", "OnUse") -- PROPTRIGGER.scr:64
    ctx:onEvent("OnTouchNotify", "OnUse") -- PROPTRIGGER.scr:65
    ctx:getParam(0, "Target") -- PROPTRIGGER.scr:66
    ctx:getParam(1, "Message") -- PROPTRIGGER.scr:67
    ctx:onEvent("OnPostStartWorld", "Init") -- PROPTRIGGER.scr:68
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- PROPTRIGGER.scr:69
    ctx:onEvent("OnPostSaveLoad", "Init") -- PROPTRIGGER.scr:70
    ctx:wait(1, .1, "Init") -- PROPTRIGGER.scr:71
    do return ctx:exit("") end -- PROPTRIGGER.scr:72
end

return script
