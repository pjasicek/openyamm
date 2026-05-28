-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DRAGONPHARAOH2FLAME.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "globals.inc" }

-- DragonPharaoh2flame.scr
-- timmy
script.labels["OnUse"] = function(ctx)
    -- DRAGONPHARAOH2FLAME.scr:13
    if ctx:condition("B_Enable==true") then -- DRAGONPHARAOH2FLAME.scr:16
        ctx:command("getobjecthandle", "FlameBoss, g_hObject") -- DRAGONPHARAOH2FLAME.scr:20
        if ctx:condition("g_hObject==NULL") then -- DRAGONPHARAOH2FLAME.scr:22
            ctx:command("debugout", "Error!  No FlameBoss????") -- DRAGONPHARAOH2FLAME.scr:23
            do return ctx:exit("") end -- DRAGONPHARAOH2FLAME.scr:24
        end -- DRAGONPHARAOH2FLAME.scr:25
        -- set g_ntemp, FlameId
        -- Set g_stemp,g_ntemp
        ctx:command("set", "g_stemp,FlameId") -- DRAGONPHARAOH2FLAME.scr:29
        ctx:command("set", "g_sout, FlameOn") -- DRAGONPHARAOH2FLAME.scr:30
        ctx:command("add", "g_sout, g_stemp") -- DRAGONPHARAOH2FLAME.scr:31
        ctx:trigger("g_hMyObject", "On") -- DRAGONPHARAOH2FLAME.scr:33
        ctx:trigger("g_hObject", "g_sout") -- DRAGONPHARAOH2FLAME.scr:34
        ctx:command("debugout", "g_sout") -- DRAGONPHARAOH2FLAME.scr:35
    end -- DRAGONPHARAOH2FLAME.scr:37
    do return ctx:exit("") end -- DRAGONPHARAOH2FLAME.scr:40
end

script.labels["Enable"] = function(ctx)
    -- DRAGONPHARAOH2FLAME.scr:43
    ctx:command("set", "B_Enable, true") -- DRAGONPHARAOH2FLAME.scr:46
    do return ctx:exit("") end -- DRAGONPHARAOH2FLAME.scr:47
end

script.labels["Disable"] = function(ctx)
    -- DRAGONPHARAOH2FLAME.scr:50
    ctx:command("set", "B_Enable, false") -- DRAGONPHARAOH2FLAME.scr:53
    do return ctx:exit("") end -- DRAGONPHARAOH2FLAME.scr:55
end

script.labels["Main"] = function(ctx)
    -- DRAGONPHARAOH2FLAME.scr:58
    ctx:addTrigger("use", "OnUse") -- DRAGONPHARAOH2FLAME.scr:61
    ctx:addTrigger("enable", "Enable") -- DRAGONPHARAOH2FLAME.scr:62
    ctx:addTrigger("disable", "disable") -- DRAGONPHARAOH2FLAME.scr:63
    ctx:command("getmyhandle", "g_hMyObject") -- DRAGONPHARAOH2FLAME.scr:64
    ctx:getParam(0, "FlameId") -- DRAGONPHARAOH2FLAME.scr:65
    do return ctx:exit("") end -- DRAGONPHARAOH2FLAME.scr:67
end

return script
