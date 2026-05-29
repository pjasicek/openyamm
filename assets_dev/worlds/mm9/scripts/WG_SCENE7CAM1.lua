-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WG_SCENE7CAM1.scr"
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
    -- WG_SCENE7CAM1.scr:33
    ctx:state().g_hobject = ctx:objectOrNil("Krohn") -- WG_SCENE7CAM1.scr:37
    ctx:self():setTarget(ctx:object("g_hobject")) -- WG_SCENE7CAM1.scr:38
    if ctx:condition("g_stemp!=cam2") then -- WG_SCENE7CAM1.scr:39
        ctx:wait(1, 1, "OnPan") -- WG_SCENE7CAM1.scr:40
    end -- WG_SCENE7CAM1.scr:41
    do return ctx:exit("") end -- WG_SCENE7CAM1.scr:42
end

script.labels["OnPan"] = function(ctx)
    -- WG_SCENE7CAM1.scr:45
    ctx:state().Xpos, ctx:state().Ypos, ctx:state().Zpos = ctx:object("sMarker"):pos() -- WG_SCENE7CAM1.scr:48-49
    ctx:self():moveToPos("xpos", "Ypos", "Zpos", 150, "OnArrive") -- WG_SCENE7CAM1.scr:50
    do return ctx:exit("") end -- WG_SCENE7CAM1.scr:51
end

script.labels["OnArrive"] = function(ctx)
    -- WG_SCENE7CAM1.scr:56
    ctx:object("Winman"):trigger("CutToKrohn") -- WG_SCENE7CAM1.scr:59-60
    do return ctx:exit("") end -- WG_SCENE7CAM1.scr:61
end

script.labels["Main"] = function(ctx)
    -- WG_SCENE7CAM1.scr:63
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "G_stemp") -- WG_SCENE7CAM1.scr:68
    ctx:getParam(1, "sMarker") -- WG_SCENE7CAM1.scr:69
    ctx:addTrigger("Play", "OnPlay") -- WG_SCENE7CAM1.scr:70
    do return ctx:exit("") end -- WG_SCENE7CAM1.scr:74
end

return script
