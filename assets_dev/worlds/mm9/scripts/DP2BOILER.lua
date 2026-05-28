-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DP2BOILER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "damageType.inc" }

-- DP2Boiler.scr
-- By Timmy
-- works the boiler room puzzle
script.labels["OnUse"] = function(ctx)
    -- DP2BOILER.scr:13
    if ctx:condition("used!=true") then -- DP2BOILER.scr:16
        ctx:command("playanim", "open") -- DP2BOILER.scr:18
        ctx:command("getobjecthandle", "Deathwater1, g_hObject") -- DP2BOILER.scr:20
        if ctx:condition("g_hObject!=NULL") then -- DP2BOILER.scr:21
            ctx:trigger("g_hObject", "DamageOn") -- DP2BOILER.scr:22
        end -- DP2BOILER.scr:23
        ctx:command("getobjecthandle", "Deathwater2, g_hObject") -- DP2BOILER.scr:25
        if ctx:condition("g_hObject!=NULL") then -- DP2BOILER.scr:26
            ctx:trigger("g_hObject", "DamageOn") -- DP2BOILER.scr:27
        end -- DP2BOILER.scr:28
        ctx:command("getobjecthandle", "steam1, g_hObject") -- DP2BOILER.scr:30
        if ctx:condition("g_hObject!=NULL") then -- DP2BOILER.scr:31
            ctx:trigger("g_hObject", "On") -- DP2BOILER.scr:32
        end -- DP2BOILER.scr:33
        ctx:command("getobjecthandle", "steam2, g_hObject") -- DP2BOILER.scr:35
        if ctx:condition("g_hObject!=NULL") then -- DP2BOILER.scr:36
            ctx:trigger("g_hObject", "On") -- DP2BOILER.scr:37
        end -- DP2BOILER.scr:38
        ctx:command("getobjecthandle", "Fire0, g_hObject") -- DP2BOILER.scr:40
        if ctx:condition("g_hObject!=NULL") then -- DP2BOILER.scr:41
            ctx:trigger("g_hObject", "FireOn") -- DP2BOILER.scr:42
        end -- DP2BOILER.scr:43
        ctx:command("getobjecthandle", "Megahydra1, g_hObject") -- DP2BOILER.scr:45
        if ctx:condition("g_hObject!=NULL") then -- DP2BOILER.scr:46
            ctx:trigger("g_hObject", "DamageOn") -- DP2BOILER.scr:47
        end -- DP2BOILER.scr:48
        ctx:command("getobjecthandle", "Megahydra2, g_hObject") -- DP2BOILER.scr:50
        if ctx:condition("g_hObject!=NULL") then -- DP2BOILER.scr:51
            ctx:trigger("g_hObject", "DamageOn") -- DP2BOILER.scr:52
        end -- DP2BOILER.scr:53
        ctx:command("set", "used, True") -- DP2BOILER.scr:56
        do return ctx:exit("") end -- DP2BOILER.scr:57
    end -- DP2BOILER.scr:58
    ctx:command("playanim", "close") -- DP2BOILER.scr:62
    ctx:command("getobjecthandle", "Deathwater1, g_hObject") -- DP2BOILER.scr:64
    if ctx:condition("g_hObject!=NULL") then -- DP2BOILER.scr:65
        ctx:trigger("g_hObject", "DamageOff") -- DP2BOILER.scr:66
    end -- DP2BOILER.scr:67
    ctx:command("getobjecthandle", "Deathwater2, g_hObject") -- DP2BOILER.scr:68
    if ctx:condition("g_hObject!=NULL") then -- DP2BOILER.scr:69
        ctx:trigger("g_hObject", "DamageOff") -- DP2BOILER.scr:70
    end -- DP2BOILER.scr:71
    ctx:command("getobjecthandle", "steam1, g_hObject") -- DP2BOILER.scr:74
    if ctx:condition("g_hObject!=NULL") then -- DP2BOILER.scr:75
        ctx:trigger("g_hObject", "Off") -- DP2BOILER.scr:76
    end -- DP2BOILER.scr:77
    ctx:command("getobjecthandle", "steam2, g_hObject") -- DP2BOILER.scr:79
    if ctx:condition("g_hObject!=NULL") then -- DP2BOILER.scr:80
        ctx:trigger("g_hObject", "Off") -- DP2BOILER.scr:81
    end -- DP2BOILER.scr:82
    ctx:command("getobjecthandle", "Fire0, g_hObject") -- DP2BOILER.scr:84
    if ctx:condition("g_hObject!=NULL") then -- DP2BOILER.scr:85
        ctx:trigger("g_hObject", "FireOff") -- DP2BOILER.scr:86
    end -- DP2BOILER.scr:87
    ctx:command("set", "used, False") -- DP2BOILER.scr:88
    do return ctx:exit("") end -- DP2BOILER.scr:89
end

script.labels["Main"] = function(ctx)
    -- DP2BOILER.scr:93
    -- Traceon
    ctx:addTrigger("use", "OnUse") -- DP2BOILER.scr:97
    do return ctx:exit("") end -- DP2BOILER.scr:98
end

return script
