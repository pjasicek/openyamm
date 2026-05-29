-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DP3LAVASHOOTER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "globals.inc" }

-- DP3Lavashooter.scr
-- timmy
script.labels["shutoff"] = function(ctx)
    -- DP3LAVASHOOTER.scr:9
    ctx:getParam(0, "g_hObject") -- DP3LAVASHOOTER.scr:12
    ctx:state().g_ntemp = ctx:object("g_hObject"):isPlayer() -- DP3LAVASHOOTER.scr:13
    if ctx:condition("g_ntemp==true") then -- DP3LAVASHOOTER.scr:15
        ctx:self():setModelFilenames("models\\props\\LavaFountain.abc", "skins\\props\\LavaFountain.dtx") -- DP3LAVASHOOTER.scr:18
        ctx:wait(.5, .5, "anim") -- DP3LAVASHOOTER.scr:19
        do return mm9.gotoLabel(script, ctx, "anim") end -- DP3LAVASHOOTER.scr:20
    end -- DP3LAVASHOOTER.scr:21
    do return ctx:exit("") end -- DP3LAVASHOOTER.scr:23
end

script.labels["anim"] = function(ctx)
    -- DP3LAVASHOOTER.scr:25
    ctx:set("g_stemp", "off") -- DP3LAVASHOOTER.scr:28
    ctx:state().g_hObject = ctx:objectOrNil("Shoot1") -- DP3LAVASHOOTER.scr:29
    if ctx:condition("g_hObject!=NULL") then -- DP3LAVASHOOTER.scr:30
        ctx:trigger("g_hObject", "g_stemp") -- DP3LAVASHOOTER.scr:32
    end -- DP3LAVASHOOTER.scr:33
    ctx:state().g_hObject = ctx:objectOrNil("Shoot2") -- DP3LAVASHOOTER.scr:35
    if ctx:condition("g_hObject!=NULL") then -- DP3LAVASHOOTER.scr:36
        ctx:trigger("g_hObject", "g_stemp") -- DP3LAVASHOOTER.scr:37
    end -- DP3LAVASHOOTER.scr:38
    ctx:state().g_hObject = ctx:objectOrNil("Shoot3") -- DP3LAVASHOOTER.scr:40
    if ctx:condition("g_hObject!=NULL") then -- DP3LAVASHOOTER.scr:41
        ctx:trigger("g_hObject", "g_stemp") -- DP3LAVASHOOTER.scr:42
    end -- DP3LAVASHOOTER.scr:43
    ctx:state().g_hObject = ctx:objectOrNil("Shoot4") -- DP3LAVASHOOTER.scr:45
    if ctx:condition("g_hObject!=NULL") then -- DP3LAVASHOOTER.scr:46
        ctx:trigger("g_hObject", "g_stemp") -- DP3LAVASHOOTER.scr:47
    end -- DP3LAVASHOOTER.scr:48
    ctx:state().g_hObject = ctx:objectOrNil("Shoot5") -- DP3LAVASHOOTER.scr:50
    if ctx:condition("g_hObject!=NULL") then -- DP3LAVASHOOTER.scr:51
        ctx:trigger("g_hObject", "g_stemp") -- DP3LAVASHOOTER.scr:52
    end -- DP3LAVASHOOTER.scr:53
    ctx:state().g_hObject = ctx:objectOrNil("Shoot6") -- DP3LAVASHOOTER.scr:55
    if ctx:condition("g_hObject!=NULL") then -- DP3LAVASHOOTER.scr:56
        ctx:trigger("g_hObject", "g_stemp") -- DP3LAVASHOOTER.scr:57
    end -- DP3LAVASHOOTER.scr:58
    ctx:state().g_hObject = ctx:objectOrNil("Shoot7") -- DP3LAVASHOOTER.scr:60
    if ctx:condition("g_hObject!=NULL") then -- DP3LAVASHOOTER.scr:61
        ctx:trigger("g_hObject", "g_stemp") -- DP3LAVASHOOTER.scr:62
    end -- DP3LAVASHOOTER.scr:63
    ctx:state().g_hObject = ctx:objectOrNil("Shoot8") -- DP3LAVASHOOTER.scr:65
    if ctx:condition("g_hObject!=NULL") then -- DP3LAVASHOOTER.scr:66
        ctx:trigger("g_hObject", "g_stemp") -- DP3LAVASHOOTER.scr:67
    end -- DP3LAVASHOOTER.scr:68
    ctx:set("g_stemp", "loopanim") -- DP3LAVASHOOTER.scr:74
    ctx:add("g_stemp", "idle") -- DP3LAVASHOOTER.scr:75
    ctx:state().g_hObject = ctx:self() -- DP3LAVASHOOTER.scr:76
    ctx:trigger("g_hObject", "g_stemp") -- DP3LAVASHOOTER.scr:77
    ctx:wait(3, 3, "OpenDoor") -- DP3LAVASHOOTER.scr:79
    ctx:onEvent("OnDamage") -- DP3LAVASHOOTER.scr:81
    do return ctx:exit("") end -- DP3LAVASHOOTER.scr:83
end

script.labels["OpenDoor"] = function(ctx)
    -- DP3LAVASHOOTER.scr:87
    local object = ctx:object("Door6") -- DP3LAVASHOOTER.scr:91
    object:trigger("unlock") -- DP3LAVASHOOTER.scr:92
    object:trigger("use") -- DP3LAVASHOOTER.scr:93
    do return ctx:exit("") end -- DP3LAVASHOOTER.scr:95
end

script.labels["Main"] = function(ctx)
    -- DP3LAVASHOOTER.scr:97
    -- TRACEON
    ctx:onEvent("OnDamage", "shutoff") -- DP3LAVASHOOTER.scr:101
    do return ctx:exit("") end -- DP3LAVASHOOTER.scr:102
end

return script
