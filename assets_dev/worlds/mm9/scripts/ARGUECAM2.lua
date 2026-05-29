-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARGUECAM2.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- BattleCam1.scr
-- 1/5/02
-- timmy
-- does battlefield camera
script.labels["OnPlay"] = function(ctx)
    -- ARGUECAM2.scr:27
    -- getobjecthandle kira g_hobject
    -- target g_hobject
    ctx:state().Xpos, ctx:state().Ypos, ctx:state().Zpos = ctx:object("sMarker"):pos() -- ARGUECAM2.scr:33-34
    ctx:self():moveToPos("xpos", "Ypos", "Zpos", "nSpeed", "OnArrive") -- ARGUECAM2.scr:35
    do return ctx:exit("") end -- ARGUECAM2.scr:36
end

script.labels["OnArrive"] = function(ctx)
    -- ARGUECAM2.scr:39
    if ctx:condition("nBook==1") then -- ARGUECAM2.scr:42
        do return ctx:exit("") end -- ARGUECAM2.scr:43
    end -- ARGUECAM2.scr:44
    ctx:object("Argueman"):trigger("Done") -- ARGUECAM2.scr:46-47
    do return ctx:exit("") end -- ARGUECAM2.scr:48
end

script.labels["Main"] = function(ctx)
    -- ARGUECAM2.scr:50
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Play", "OnPlay") -- ARGUECAM2.scr:55
    ctx:getParam(0, "sMarker") -- ARGUECAM2.scr:56
    ctx:getParam(1, "nSpeed") -- ARGUECAM2.scr:57
    ctx:getParam(2, "nBook") -- ARGUECAM2.scr:58
    do return ctx:exit("") end -- ARGUECAM2.scr:59
end

return script
