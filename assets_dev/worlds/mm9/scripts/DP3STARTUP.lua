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
    ctx:state().g_hObject = ctx:objectOrNil("Shoot1") -- DP3STARTUP.scr:22
    if ctx:condition("g_hObject!=NULL") then -- DP3STARTUP.scr:23
        ctx:trigger("g_hObject", "on") -- DP3STARTUP.scr:24
    end -- DP3STARTUP.scr:25
    ctx:state().g_hObject = ctx:objectOrNil("Shoot2") -- DP3STARTUP.scr:26
    if ctx:condition("g_hObject!=NULL") then -- DP3STARTUP.scr:27
        ctx:trigger("g_hObject", "on") -- DP3STARTUP.scr:28
    end -- DP3STARTUP.scr:29
    ctx:state().g_hObject = ctx:objectOrNil("Shoot3") -- DP3STARTUP.scr:30
    if ctx:condition("g_hObject!=NULL") then -- DP3STARTUP.scr:31
        ctx:trigger("g_hObject", "on") -- DP3STARTUP.scr:32
    end -- DP3STARTUP.scr:33
    ctx:state().g_hObject = ctx:objectOrNil("Shoot4") -- DP3STARTUP.scr:34
    if ctx:condition("g_hObject!=NULL") then -- DP3STARTUP.scr:35
        ctx:trigger("g_hObject", "on") -- DP3STARTUP.scr:36
    end -- DP3STARTUP.scr:37
    ctx:state().g_hObject = ctx:objectOrNil("Shoot5") -- DP3STARTUP.scr:38
    if ctx:condition("g_hObject!=NULL") then -- DP3STARTUP.scr:39
        ctx:trigger("g_hObject", "on") -- DP3STARTUP.scr:40
    end -- DP3STARTUP.scr:41
    ctx:state().g_hObject = ctx:objectOrNil("Shoot6") -- DP3STARTUP.scr:42
    if ctx:condition("g_hObject!=NULL") then -- DP3STARTUP.scr:43
        ctx:trigger("g_hObject", "on") -- DP3STARTUP.scr:44
    end -- DP3STARTUP.scr:45
    ctx:state().g_hObject = ctx:objectOrNil("Shoot7") -- DP3STARTUP.scr:46
    if ctx:condition("g_hObject!=NULL") then -- DP3STARTUP.scr:47
        ctx:trigger("g_hObject", "on") -- DP3STARTUP.scr:48
    end -- DP3STARTUP.scr:49
    ctx:state().g_hObject = ctx:objectOrNil("Shoot8") -- DP3STARTUP.scr:50
    if ctx:condition("g_hObject!=NULL") then -- DP3STARTUP.scr:51
        ctx:trigger("g_hObject", "on") -- DP3STARTUP.scr:52
    end -- DP3STARTUP.scr:55
    -- turns on first shooter
    ctx:set("g_stemp", "loopanim") -- DP3STARTUP.scr:57
    ctx:add("g_stemp", "idle") -- DP3STARTUP.scr:58
    ctx:object("fountain"):trigger("g_stemp") -- DP3STARTUP.scr:59-60
    ctx:set("g_stemp", "loopanim") -- DP3STARTUP.scr:61
    ctx:add("g_stemp", "Operate") -- DP3STARTUP.scr:62
    ctx:object("shooter"):trigger("g_stemp") -- DP3STARTUP.scr:63-64
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
