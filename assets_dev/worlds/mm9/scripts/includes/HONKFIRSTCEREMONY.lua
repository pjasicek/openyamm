-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HONKFIRSTCEREMONY.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "HonkHostility.inc" }

-- HonkFirstCeremony.inc
-- by SJR
-- 01-10-02
-- Purpose:
script.labels["InitHonkFirstCeremony"] = function(ctx)
    -- HONKFIRSTCEREMONY.inc:12
    if ctx:condition("first_hHONK_CEREMONY==0") then -- HONKFIRSTCEREMONY.inc:14
        ctx:command("getobjecthandle", "HONK_CEREMONY, first_hHONK_CEREMONY") -- HONKFIRSTCEREMONY.inc:15
        if ctx:condition("first_hHONK_CEREMONY==0") then -- HONKFIRSTCEREMONY.inc:16
            ctx:command("wait", "0, 1, InitHonkFirstCeremony") -- HONKFIRSTCEREMONY.inc:17
        end -- HONKFIRSTCEREMONY.inc:18
    end -- HONKFIRSTCEREMONY.inc:19
    ctx:command("createobjectlink", "first_hHONK_CEREMONY") -- HONKFIRSTCEREMONY.inc:21
    ctx:command("onobjectlinkbroken", "first_CheckObject") -- HONKFIRSTCEREMONY.inc:22
    do return ctx:exit(1) end -- HONKFIRSTCEREMONY.inc:24
end

script.labels["first_CheckObject"] = function(ctx)
    -- HONKFIRSTCEREMONY.inc:27
    ctx:getParam(0, "g_hObject") -- HONKFIRSTCEREMONY.inc:29
    if ctx:condition("g_hObject==first_hHONK_CEREMONY") then -- HONKFIRSTCEREMONY.inc:30
        mm9.gosub(script, ctx, "OnFirstCeremony") -- HONKFIRSTCEREMONY.inc:31
    else -- HONKFIRSTCEREMONY.inc:32
        mm9.gosub(script, ctx, "BecomeHostile") -- HONKFIRSTCEREMONY.inc:33
    end -- HONKFIRSTCEREMONY.inc:34
    do return ctx:exit(1) end -- HONKFIRSTCEREMONY.inc:36
end

script.labels["OnFirstCeremony"] = function(ctx)
    -- HONKFIRSTCEREMONY.inc:39
    do return ctx:exit(1) end -- HONKFIRSTCEREMONY.inc:41
end

return script
