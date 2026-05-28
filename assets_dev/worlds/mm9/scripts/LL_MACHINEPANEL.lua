-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LL_MACHINEPANEL.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "BaseGlobals.inc" }

-- LL_MachinePanel.scr
-- by SJR
-- 01-02-02
-- Purpose:blow up cage, trigger Its
script.labels["Main"] = function(ctx)
    -- LL_MACHINEPANEL.scr:13
    ctx:getParam(0, "sTriggerName") -- LL_MACHINEPANEL.scr:15
    ctx:command("wait", "0, 1, InitMachinePanel") -- LL_MACHINEPANEL.scr:17
    do return ctx:exit("TRUE") end -- LL_MACHINEPANEL.scr:19
end

script.labels["InitMachinePanel"] = function(ctx)
    -- LL_MACHINEPANEL.scr:22
    ctx:addTrigger("explode", "Malfunction") -- LL_MACHINEPANEL.scr:24
    do return ctx:exit("TRUE") end -- LL_MACHINEPANEL.scr:26
end

script.labels["Malfunction"] = function(ctx)
    -- LL_MACHINEPANEL.scr:29
    if ctx:condition("hTrigger==0") then -- LL_MACHINEPANEL.scr:31
        ctx:command("getobjecthandle", "sTriggerName, hTrigger") -- LL_MACHINEPANEL.scr:32
        if ctx:condition("hTrigger==0") then -- LL_MACHINEPANEL.scr:33
            -- cprint "No panel trigger!"
            do return ctx:exit("TRUE") end -- LL_MACHINEPANEL.scr:35
        end -- LL_MACHINEPANEL.scr:36
    end -- LL_MACHINEPANEL.scr:37
    ctx:command("playsound", "sounds\\default.wav, BlowUp, 1, 500, 0, 100") -- LL_MACHINEPANEL.scr:39
    do return ctx:exit("TRUE") end -- LL_MACHINEPANEL.scr:41
end

script.labels["BlowUp"] = function(ctx)
    -- LL_MACHINEPANEL.scr:44
    ctx:trigger("hTrigger", "trigger") -- LL_MACHINEPANEL.scr:46
    ctx:command("getmyhandle", "hTrigger") -- LL_MACHINEPANEL.scr:48
    ctx:trigger("hTrigger", "destroy") -- LL_MACHINEPANEL.scr:49
    do return ctx:exit("TRUE") end -- LL_MACHINEPANEL.scr:51
end

return script
