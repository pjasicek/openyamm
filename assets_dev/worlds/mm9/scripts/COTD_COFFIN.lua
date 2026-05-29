-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "COTD_COFFIN.scr"
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
    -- COTD_COFFIN.scr:24
    if ctx:condition("nOpened==False") then -- COTD_COFFIN.scr:27
        ctx:self():playAnimation("Open", "DoNothing") -- COTD_COFFIN.scr:28
        ctx:state().nOpened = true -- COTD_COFFIN.scr:29
        do return ctx:exit("") end -- COTD_COFFIN.scr:30
    end -- COTD_COFFIN.scr:31
    ctx:state().g_hobject = ctx:objectOrNil("Target") -- COTD_COFFIN.scr:33
    if ctx:condition("g_hobject!=null") then -- COTD_COFFIN.scr:34
        ctx:trigger("g_hobject", "message") -- COTD_COFFIN.scr:35
        do return ctx:exit("") end -- COTD_COFFIN.scr:36
    end -- COTD_COFFIN.scr:37
    do return ctx:exit("") end -- COTD_COFFIN.scr:38
end

script.labels["Main"] = function(ctx)
    -- COTD_COFFIN.scr:42
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Use", "OnUse") -- COTD_COFFIN.scr:47
    ctx:getParam(0, "Target") -- COTD_COFFIN.scr:48
    ctx:getParam(1, "Message") -- COTD_COFFIN.scr:49
    do return ctx:exit("") end -- COTD_COFFIN.scr:51
end

return script
