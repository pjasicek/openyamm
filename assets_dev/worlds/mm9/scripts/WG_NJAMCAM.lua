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
    ctx:state().Xpos, ctx:state().Ypos, ctx:state().Zpos = ctx:object("NjamCamMk1"):pos() -- WG_NJAMCAM.scr:38-39
    ctx:self():moveToPos("xpos", "Ypos", "Zpos", 100, "OnArrive1") -- WG_NJAMCAM.scr:40
    do return ctx:exit("") end -- WG_NJAMCAM.scr:41
end

script.labels["OnArrive1"] = function(ctx)
    -- WG_NJAMCAM.scr:44
    ctx:state().MyX, ctx:state().MyY, ctx:state().MyZ = ctx:self():pos() -- WG_NJAMCAM.scr:48
    ctx:state().Xpos, ctx:state().Ypos, ctx:state().Zpos = ctx:object("NjamCamMk2"):pos() -- WG_NJAMCAM.scr:49-50
    ctx:self():faceDir("Xpos", "Ypos", "Zpos", 70, "DoNothing") -- WG_NJAMCAM.scr:51
    ctx:self():moveToPos("xpos", "Ypos", "Zpos", 130, "OnArrive2") -- WG_NJAMCAM.scr:52
    do return ctx:exit("") end -- WG_NJAMCAM.scr:53
end

script.labels["OnArrive2"] = function(ctx)
    -- WG_NJAMCAM.scr:56
    ctx:state().g_hobject = ctx:objectOrNil("WinMan") -- WG_NJAMCAM.scr:61
    ctx:screenFadeOut(1) -- WG_NJAMCAM.scr:62
    ctx:trigger("g_hobject", "NjamCamDone") -- WG_NJAMCAM.scr:63
    do return ctx:exit("") end -- WG_NJAMCAM.scr:64
end

script.labels["OnMove"] = function(ctx)
    -- WG_NJAMCAM.scr:67
    do return ctx:exit("") end -- WG_NJAMCAM.scr:70
end

script.labels["StartFilm"] = function(ctx)
    -- WG_NJAMCAM.scr:73
    ctx:letterBox("True") -- WG_NJAMCAM.scr:76
    ctx:giveKey(109) -- WG_NJAMCAM.scr:77
    ctx:trigger("g_hmyobject", "On") -- WG_NJAMCAM.scr:79
    ctx:screenFadeIn(1) -- WG_NJAMCAM.scr:80
    ctx:state().g_htarget = ctx:objectOrNil("Njam") -- WG_NJAMCAM.scr:81
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
