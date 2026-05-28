-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WG_NJAMCAM.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 16, path = "globals.inc" }

-- WG_NjamCam.scr
-- timmy
-- tells a prop to run it's animation
-- Note: if the first parameter is the word
-- OnUse, the second parameter becomes
-- the animation name and the script will wait until being used
-- to play the animation.  Otherwise it will just
-- loop an anim for time specified
-- edited by Bones 9/10/02
-- TELP Patch 1.3 -- givekey 109 moved here from WINMAN.SCR
-- flag variables
script.labels["OnPlay"] = function(ctx)
    -- WG_NJAMCAM.scr:34
    mm9.gosub(script, ctx, "StartFilm") -- WG_NJAMCAM.scr:37
    ctx:command("getobjecthandle", "NjamCamMk1 g_hobject") -- WG_NJAMCAM.scr:38
    ctx:command("getpos", "g_hobject Xpos Ypos Zpos") -- WG_NJAMCAM.scr:39
    ctx:command("movetopos", "xpos Ypos Zpos 100 OnArrive1") -- WG_NJAMCAM.scr:40
    do return ctx:exit("") end -- WG_NJAMCAM.scr:41
end

script.labels["OnArrive1"] = function(ctx)
    -- WG_NJAMCAM.scr:44
    ctx:command("getmyhandle", "g_hmyobject") -- WG_NJAMCAM.scr:47
    ctx:command("getpos", "g_hmyobject MyX MyY MyZ") -- WG_NJAMCAM.scr:48
    ctx:command("getobjecthandle", "NjamCamMk2 g_hobject") -- WG_NJAMCAM.scr:49
    ctx:command("getpos", "g_hobject Xpos Ypos Zpos") -- WG_NJAMCAM.scr:50
    ctx:command("facedir", "Xpos Ypos Zpos 70 DoNothing") -- WG_NJAMCAM.scr:51
    ctx:command("movetopos", "xpos Ypos Zpos 130 OnArrive2") -- WG_NJAMCAM.scr:52
    do return ctx:exit("") end -- WG_NJAMCAM.scr:53
end

script.labels["OnArrive2"] = function(ctx)
    -- WG_NJAMCAM.scr:56
    ctx:command("getobjecthandle", "WinMan g_hobject") -- WG_NJAMCAM.scr:61
    ctx:command("screenfadeout", "1") -- WG_NJAMCAM.scr:62
    ctx:trigger("g_hobject", "NjamCamDone") -- WG_NJAMCAM.scr:63
    do return ctx:exit("") end -- WG_NJAMCAM.scr:64
end

script.labels["OnMove"] = function(ctx)
    -- WG_NJAMCAM.scr:67
    do return ctx:exit("") end -- WG_NJAMCAM.scr:70
end

script.labels["StartFilm"] = function(ctx)
    -- WG_NJAMCAM.scr:73
    ctx:command("letterbox", "True") -- WG_NJAMCAM.scr:76
    ctx:giveKey(109) -- WG_NJAMCAM.scr:77
    ctx:command("getmyhandle", "g_hmyobject") -- WG_NJAMCAM.scr:78
    ctx:trigger("g_hmyobject", "On") -- WG_NJAMCAM.scr:79
    ctx:command("screenfadein", "1") -- WG_NJAMCAM.scr:80
    ctx:command("getobjecthandle", "Njam g_htarget") -- WG_NJAMCAM.scr:81
    -- Target g_htarget
    do return ctx:exit("") end -- WG_NJAMCAM.scr:83
end

script.labels["Main"] = function(ctx)
    -- WG_NJAMCAM.scr:86
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Play", "OnPlay") -- WG_NJAMCAM.scr:91
    do return ctx:exit("") end -- WG_NJAMCAM.scr:95
end

return script
