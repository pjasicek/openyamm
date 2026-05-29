-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARGUECAM1.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- BattleCam1.scr
-- 1/5/02
-- timmy
-- does battlefield camera
script.labels["OnPlay"] = function(ctx)
    -- ARGUECAM1.scr:27
    ctx:state().g_hobject = ctx:objectOrNil("kira") -- ARGUECAM1.scr:30
    ctx:self():setTarget(ctx:object("g_hobject")) -- ARGUECAM1.scr:31
    ctx:state().Xpos, ctx:state().Ypos, ctx:state().Zpos = ctx:object("sMarker"):pos() -- ARGUECAM1.scr:33-34
    ctx:self():moveToPos("xpos", "Ypos", "Zpos", "nSpeed", "OnArrive") -- ARGUECAM1.scr:35
    do return ctx:exit("") end -- ARGUECAM1.scr:36
end

script.labels["OnArrive"] = function(ctx)
    -- ARGUECAM1.scr:39
    if ctx:condition("nBook==1") then -- ARGUECAM1.scr:42
        do return ctx:exit("") end -- ARGUECAM1.scr:43
    end -- ARGUECAM1.scr:44
    ctx:object("Argueman"):trigger("Done") -- ARGUECAM1.scr:46-47
    do return ctx:exit("") end -- ARGUECAM1.scr:48
end

script.labels["Main"] = function(ctx)
    -- ARGUECAM1.scr:50
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Play", "OnPlay") -- ARGUECAM1.scr:55
    ctx:getParam(0, "sMarker") -- ARGUECAM1.scr:56
    ctx:getParam(1, "nSpeed") -- ARGUECAM1.scr:57
    ctx:getParam(2, "nBook") -- ARGUECAM1.scr:58
    do return ctx:exit("") end -- ARGUECAM1.scr:59
end

return script
