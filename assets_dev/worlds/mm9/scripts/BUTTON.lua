-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BUTTON.scr"
script.includes = {}
script.labels = {}


script.labels["TriggerMe"] = function(ctx)
    -- BUTTON.scr:12
    ctx:command("ntrig", "= 1") -- BUTTON.scr:15
    ctx:command("getmyhandle", "hHandle") -- BUTTON.scr:16
    ctx:trigger("hHandle", "Use") -- BUTTON.scr:17
    do return ctx:exit(1) end -- BUTTON.scr:19
end

script.labels["UseMe"] = function(ctx)
    -- BUTTON.scr:23
    if ctx:condition("nTrig == 0") then -- BUTTON.scr:26
        ctx:command("getobjecthandle", "sButtonPad hHandle") -- BUTTON.scr:27
        ctx:trigger("hHandle", "sButtonName") -- BUTTON.scr:28
    else -- BUTTON.scr:29
        ctx:command("ntrig", "= 0") -- BUTTON.scr:30
    end -- BUTTON.scr:31
    do return ctx:exit(1) end -- BUTTON.scr:34
end

script.labels["main"] = function(ctx)
    -- BUTTON.scr:39
    ctx:getParam(0, "sButtonName") -- BUTTON.scr:42
    ctx:getParam(1, "sButtonPad") -- BUTTON.scr:43
    ctx:addTrigger("TriggerMe", "TriggerMe") -- BUTTON.scr:45
    ctx:addTrigger("Use", "UseMe") -- BUTTON.scr:46
    do return ctx:exit("") end -- BUTTON.scr:48
end

return script
