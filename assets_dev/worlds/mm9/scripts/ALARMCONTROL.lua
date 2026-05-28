-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ALARMCONTROL.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "Globals.inc" }

-- AlarmControl.scr
-- Timmy
-- triggers all the front room guards to go hostile.
script.labels["OnAlarm"] = function(ctx)
    -- ALARMCONTROL.scr:13
    -- player screwed up!
    -- time to make the guards hostile
    if not ctx:hasKey(5006) then -- ALARMCONTROL.scr:18-19
        ctx:giveKey(5006) -- ALARMCONTROL.scr:20
    end -- ALARMCONTROL.scr:21
    ctx:command("getobjecthandle", "guard0 g_hobject") -- ALARMCONTROL.scr:23
    ctx:trigger("g_hobject", "Alarm") -- ALARMCONTROL.scr:24
    ctx:command("getobjecthandle", "guard1 g_hobject") -- ALARMCONTROL.scr:26
    ctx:trigger("g_hobject", "Alarm") -- ALARMCONTROL.scr:27
    ctx:command("getobjecthandle", "guard2 g_hobject") -- ALARMCONTROL.scr:29
    ctx:trigger("g_hobject", "Alarm") -- ALARMCONTROL.scr:30
    do return ctx:exit("") end -- ALARMCONTROL.scr:31
end

script.labels["Main"] = function(ctx)
    -- ALARMCONTROL.scr:35
    -- traceon
    ctx:addTrigger("Alarm", "OnAlarm") -- ALARMCONTROL.scr:40
    do return ctx:exit(1) end -- ALARMCONTROL.scr:42
end

return script
