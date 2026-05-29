-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WG_SCENE7CAM3.scr"
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
    -- WG_SCENE7CAM3.scr:33
    ctx:state().g_hobject = ctx:objectOrNil("Krohn") -- WG_SCENE7CAM3.scr:37
    ctx:self():setTarget(ctx:object("g_hobject")) -- WG_SCENE7CAM3.scr:38
    -- wait 1 .2 OnPan
    do return ctx:exit("") end -- WG_SCENE7CAM3.scr:40
end

script.labels["OnPan"] = function(ctx)
    -- WG_SCENE7CAM3.scr:43
    ctx:state().Xpos, ctx:state().Ypos, ctx:state().Zpos = ctx:object("cam3marker"):pos() -- WG_SCENE7CAM3.scr:46-47
    ctx:self():moveToPos("xpos", "Ypos", "Zpos", 150, "OnArrive") -- WG_SCENE7CAM3.scr:48
    do return ctx:exit("") end -- WG_SCENE7CAM3.scr:49
end

script.labels["OnArrive"] = function(ctx)
    -- WG_SCENE7CAM3.scr:54
    ctx:state().g_hobject = ctx:objectOrNil("Winman") -- WG_SCENE7CAM3.scr:57
    -- Trigger g_hobject CutToKrohn
    do return ctx:exit("") end -- WG_SCENE7CAM3.scr:59
end

script.labels["Main"] = function(ctx)
    -- WG_SCENE7CAM3.scr:61
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Play", "OnPlay") -- WG_SCENE7CAM3.scr:67
    do return ctx:exit("") end -- WG_SCENE7CAM3.scr:71
end

return script
