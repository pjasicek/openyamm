-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ROTATETEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 2, path = "aiglobals.inc" }

script.labels["OnTest3"] = function(ctx)
    -- ROTATETEST.scr:4
    ctx:command("movedir", "-1,0,0,12,36") -- ROTATETEST.scr:5
    do return ctx:exit("") end -- ROTATETEST.scr:6
end

script.labels["OnTest2"] = function(ctx)
    -- ROTATETEST.scr:8
    ctx:command("movedir", "1,0,0,12,36") -- ROTATETEST.scr:9
    do return ctx:exit("") end -- ROTATETEST.scr:11
end

script.labels["OnTest"] = function(ctx)
    -- ROTATETEST.scr:13
    ctx:command("rotate", "0,1,0,90,90") -- ROTATETEST.scr:15
    do return ctx:exit("") end -- ROTATETEST.scr:16
end

script.labels["OnTest4"] = function(ctx)
    -- ROTATETEST.scr:19
    ctx:getParam(0, "g_hObject") -- ROTATETEST.scr:20
    ctx:command("getpos", "g_hObject, g_dirX, g_dirY, g_dirZ") -- ROTATETEST.scr:22
    ctx:command("getpos", "g_hMyObject, g_posX, g_posY, g_posZ") -- ROTATETEST.scr:23
    ctx:command("vecsub", "g_dirX, g_dirY, g_dirZ, g_posX, g_posY, g_posZ") -- ROTATETEST.scr:24
    ctx:command("vecnorm", "g_dirX, g_dirY, g_dirZ") -- ROTATETEST.scr:25
    -- g_dirY = 0.75
    ctx:command("facedir", "g_dirX, g_dirY, g_dirZ, 180") -- ROTATETEST.scr:29
    do return ctx:exit("") end -- ROTATETEST.scr:32
end

script.labels["main"] = function(ctx)
    -- ROTATETEST.scr:34
    ctx:command("getmyhandle", "g_hMyObject") -- ROTATETEST.scr:35
    ctx:addTrigger("Test", "OnTest") -- ROTATETEST.scr:37
    ctx:addTrigger("test2", "OnTest2") -- ROTATETEST.scr:38
    ctx:addTrigger("test3", "OnTest3") -- ROTATETEST.scr:39
    ctx:addTrigger("test4", "OnTest4") -- ROTATETEST.scr:41
    ctx:addTrigger("Use", "OnTest4") -- ROTATETEST.scr:42
    do return ctx:exit("") end -- ROTATETEST.scr:44
end

return script
