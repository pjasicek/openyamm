-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "REMOVEBRUSH.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "BaseGlobals.inc" }

-- RemoveBrush.scr
-- by SJR
-- ScriptParams:
-- p0 = (0,1)-->(remove,kill)
script.labels["Main"] = function(ctx)
    -- REMOVEBRUSH.scr:16
    ctx:getParam(0, "bKillTarget") -- REMOVEBRUSH.scr:18
    ctx:command("ontouchnotify", "OnTouchNotify") -- REMOVEBRUSH.scr:20
    do return ctx:exit("TRUE") end -- REMOVEBRUSH.scr:22
end

script.labels["OnTouchNotify"] = function(ctx)
    -- REMOVEBRUSH.scr:25
    ctx:command("ontouchnotify", "DoNothing") -- REMOVEBRUSH.scr:27
    ctx:getParam(0, "hTouch") -- REMOVEBRUSH.scr:29
    ctx:command("isai", "hTouch, bType") -- REMOVEBRUSH.scr:31
    if ctx:condition("bType==TRUE") then -- REMOVEBRUSH.scr:32
        if ctx:condition("hTouch!=0") then -- REMOVEBRUSH.scr:33
            if ctx:condition("bKillTarget==TRUE") then -- REMOVEBRUSH.scr:34
                ctx:trigger("hTouch", "destroy") -- REMOVEBRUSH.scr:35
            else -- REMOVEBRUSH.scr:36
                ctx:command("removeobject", "hTouch") -- REMOVEBRUSH.scr:37
            end -- REMOVEBRUSH.scr:38
            ctx:command("htouch", "= NULL") -- REMOVEBRUSH.scr:40
        end -- REMOVEBRUSH.scr:41
    end -- REMOVEBRUSH.scr:42
    ctx:command("ontouchnotify", "OnTouchNotify") -- REMOVEBRUSH.scr:44
    do return ctx:exit("TRUE") end -- REMOVEBRUSH.scr:46
end

return script
