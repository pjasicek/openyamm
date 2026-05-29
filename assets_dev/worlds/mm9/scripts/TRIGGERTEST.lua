-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TRIGGERTEST.scr"
script.includes = {}
script.labels = {}


script.labels["Main"] = function(ctx)
    -- TRIGGERTEST.scr:2
    ctx:addTrigger("Message", "OnMessage") -- TRIGGERTEST.scr:3
    do return ctx:exit(1) end -- TRIGGERTEST.scr:4
end

script.labels["OnMessage"] = function(ctx)
    -- TRIGGERTEST.scr:6
    ctx:state().h = ctx:objectOrNil("TriggerB") -- TRIGGERTEST.scr:7
    ctx:cprint("Real", "TriggerB", "=") -- TRIGGERTEST.scr:8
    ctx:cprint("h") -- TRIGGERTEST.scr:9
    ctx:getParam(0, "h") -- TRIGGERTEST.scr:10
    ctx:cprint("GetParam", "=") -- TRIGGERTEST.scr:11
    ctx:cprint("h") -- TRIGGERTEST.scr:12
    do return ctx:exit(1) end -- TRIGGERTEST.scr:13
end

return script
