-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WG_SHOT7CAM.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "globals.inc" }

-- Wg_Shot7Cam.scr
-- timmy
-- tells a prop to run it's animation
-- Note: if the first parameter is the word
-- OnUse, the second parameter becomes
-- the animation name and the script will wait until being used
-- to play the animation.  Otherwise it will just
-- loop an anim for time specified
-- flag variables
script.labels["OnPlay"] = function(ctx)
    -- WG_SHOT7CAM.scr:30
    ctx:state().g_hobject = ctx:objectOrNil("Njam") -- WG_SHOT7CAM.scr:34
    ctx:self():setTarget(ctx:object("g_hobject")) -- WG_SHOT7CAM.scr:35
    ctx:wait(1, .2, "OnFinish2") -- WG_SHOT7CAM.scr:36
    do return ctx:exit("") end -- WG_SHOT7CAM.scr:37
end

script.labels["OnFinish2"] = function(ctx)
    -- WG_SHOT7CAM.scr:40
    ctx:screenFadeIn(1) -- WG_SHOT7CAM.scr:43
    ctx:wait(1, 2, "OnPan") -- WG_SHOT7CAM.scr:44
    do return ctx:exit("") end -- WG_SHOT7CAM.scr:45
end

script.labels["OnPan"] = function(ctx)
    -- WG_SHOT7CAM.scr:48
    ctx:state().Xpos, ctx:state().Ypos, ctx:state().Zpos = ctx:object("Shot7Mk0"):pos() -- WG_SHOT7CAM.scr:51-52
    ctx:self():moveToPos("xpos", "Ypos", "Zpos", 75, "OnArrive1") -- WG_SHOT7CAM.scr:53
    do return ctx:exit("") end -- WG_SHOT7CAM.scr:54
end

script.labels["OnArrive1"] = function(ctx)
    -- WG_SHOT7CAM.scr:58
    ctx:state().Xpos, ctx:state().Ypos, ctx:state().Zpos = ctx:object("Shot7Mk1"):pos() -- WG_SHOT7CAM.scr:61-62
    ctx:self():moveToPos("xpos", "Ypos", "Zpos", 75, "OnArrive2") -- WG_SHOT7CAM.scr:63
    do return ctx:exit("") end -- WG_SHOT7CAM.scr:64
end

script.labels["OnArrive2"] = function(ctx)
    -- WG_SHOT7CAM.scr:67
    ctx:state().Xpos, ctx:state().Ypos, ctx:state().Zpos = ctx:object("Shot7Mk2"):pos() -- WG_SHOT7CAM.scr:70-71
    ctx:self():moveToPos("xpos", "Ypos", "Zpos", 75, "OnArrive3") -- WG_SHOT7CAM.scr:72
    do return ctx:exit("") end -- WG_SHOT7CAM.scr:73
end

script.labels["OnArrive3"] = function(ctx)
    -- WG_SHOT7CAM.scr:76
    ctx:state().Xpos, ctx:state().Ypos, ctx:state().Zpos = ctx:object("Shot7Mk3"):pos() -- WG_SHOT7CAM.scr:79-80
    ctx:self():moveToPos("xpos", "Ypos", "Zpos", 75, "CutTo") -- WG_SHOT7CAM.scr:81
    do return ctx:exit("") end -- WG_SHOT7CAM.scr:82
end

script.labels["CutTo"] = function(ctx)
    -- WG_SHOT7CAM.scr:85
    ctx:object("Winman"):trigger("CutTo") -- WG_SHOT7CAM.scr:88-89
    do return ctx:exit("") end -- WG_SHOT7CAM.scr:90
end

script.labels["Main"] = function(ctx)
    -- WG_SHOT7CAM.scr:94
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Play", "OnPlay") -- WG_SHOT7CAM.scr:99
    do return ctx:exit("") end -- WG_SHOT7CAM.scr:103
end

return script
