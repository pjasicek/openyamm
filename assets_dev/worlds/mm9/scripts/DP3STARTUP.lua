-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DP3STARTUP.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "globals.inc" }

script.topLevel = function(ctx)
    -- DP3startup.scr
    -- timmy
    do return ctx:exit("") end -- DP3STARTUP.scr:13
end

script.labels["Init"] = function(ctx)
    -- DP3STARTUP.scr:17
    -- starts animation
    ctx:command("getobjecthandle", "Shoot1, g_hObject") -- DP3STARTUP.scr:22
    if ctx:condition("g_hObject!=NULL") then -- DP3STARTUP.scr:23
        ctx:trigger("g_hObject", "on") -- DP3STARTUP.scr:24
    end -- DP3STARTUP.scr:25
    ctx:command("getobjecthandle", "Shoot2, g_hObject") -- DP3STARTUP.scr:26
    if ctx:condition("g_hObject!=NULL") then -- DP3STARTUP.scr:27
        ctx:trigger("g_hObject", "on") -- DP3STARTUP.scr:28
    end -- DP3STARTUP.scr:29
    ctx:command("getobjecthandle", "Shoot3, g_hObject") -- DP3STARTUP.scr:30
    if ctx:condition("g_hObject!=NULL") then -- DP3STARTUP.scr:31
        ctx:trigger("g_hObject", "on") -- DP3STARTUP.scr:32
    end -- DP3STARTUP.scr:33
    ctx:command("getobjecthandle", "Shoot4, g_hObject") -- DP3STARTUP.scr:34
    if ctx:condition("g_hObject!=NULL") then -- DP3STARTUP.scr:35
        ctx:trigger("g_hObject", "on") -- DP3STARTUP.scr:36
    end -- DP3STARTUP.scr:37
    ctx:command("getobjecthandle", "Shoot5, g_hObject") -- DP3STARTUP.scr:38
    if ctx:condition("g_hObject!=NULL") then -- DP3STARTUP.scr:39
        ctx:trigger("g_hObject", "on") -- DP3STARTUP.scr:40
    end -- DP3STARTUP.scr:41
    ctx:command("getobjecthandle", "Shoot6, g_hObject") -- DP3STARTUP.scr:42
    if ctx:condition("g_hObject!=NULL") then -- DP3STARTUP.scr:43
        ctx:trigger("g_hObject", "on") -- DP3STARTUP.scr:44
    end -- DP3STARTUP.scr:45
    ctx:command("getobjecthandle", "Shoot7, g_hObject") -- DP3STARTUP.scr:46
    if ctx:condition("g_hObject!=NULL") then -- DP3STARTUP.scr:47
        ctx:trigger("g_hObject", "on") -- DP3STARTUP.scr:48
    end -- DP3STARTUP.scr:49
    ctx:command("getobjecthandle", "Shoot8, g_hObject") -- DP3STARTUP.scr:50
    if ctx:condition("g_hObject!=NULL") then -- DP3STARTUP.scr:51
        ctx:trigger("g_hObject", "on") -- DP3STARTUP.scr:52
    end -- DP3STARTUP.scr:55
    -- turns on first shooter
    ctx:command("set", "g_stemp,loopanim") -- DP3STARTUP.scr:57
    ctx:command("add", "g_stemp,idle") -- DP3STARTUP.scr:58
    ctx:command("getobjecthandle", "fountain, g_hObject") -- DP3STARTUP.scr:59
    ctx:trigger("g_hObject", "g_stemp") -- DP3STARTUP.scr:60
    ctx:command("set", "g_stemp,loopanim") -- DP3STARTUP.scr:61
    ctx:command("add", "g_stemp,Operate") -- DP3STARTUP.scr:62
    ctx:command("getobjecthandle", "shooter, g_hObject") -- DP3STARTUP.scr:63
    ctx:trigger("g_hObject", "g_stemp") -- DP3STARTUP.scr:64
    do return ctx:exit("") end -- DP3STARTUP.scr:65
end

script.labels["Main"] = function(ctx)
    -- DP3STARTUP.scr:68
    -- traceon
    -- wait 0.5, Init
    -- getmyhandle g_hObject
    -- trigger g_hObject on
    do return mm9.gotoLabel(script, ctx, "Init") end -- DP3STARTUP.scr:75
    do return ctx:exit("") end -- DP3STARTUP.scr:76
end

return script
