-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ILSSHOOTINGBOOK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- ILSshootingbook.scr
-- timmy
-- fires a shooter at player
-- Parameters
-- P0 which shooter book is using
script.labels["OnUse"] = function(ctx)
    -- ILSSHOOTINGBOOK.scr:19
    if ctx:condition("Stopped==false") then -- ILSSHOOTINGBOOK.scr:22
        if ctx:condition("Done==false") then -- ILSSHOOTINGBOOK.scr:24
            if ctx:condition("open==false") then -- ILSSHOOTINGBOOK.scr:26
                ctx:self():playAnimation("OpenBook") -- ILSSHOOTINGBOOK.scr:27
                ctx:object("Params"):trigger("On") -- ILSSHOOTINGBOOK.scr:28-29
                ctx:state().open = true -- ILSSHOOTINGBOOK.scr:30
                do return ctx:exit("") end -- ILSSHOOTINGBOOK.scr:31
            end -- ILSSHOOTINGBOOK.scr:32
            ctx:trigger("g_hobject", "Off") -- ILSSHOOTINGBOOK.scr:35
            ctx:trigger("g_hobject", "On") -- ILSSHOOTINGBOOK.scr:36
            do return ctx:exit("") end -- ILSSHOOTINGBOOK.scr:37
        end -- ILSSHOOTINGBOOK.scr:38
        ctx:self():playAnimation("CloseBook") -- ILSSHOOTINGBOOK.scr:41
        ctx:state().Stopped = true -- ILSSHOOTINGBOOK.scr:42
    end -- ILSSHOOTINGBOOK.scr:44
    do return ctx:exit("") end -- ILSSHOOTINGBOOK.scr:46
end

script.labels["OnDone"] = function(ctx)
    -- ILSSHOOTINGBOOK.scr:50
    if ctx:condition("open==true") then -- ILSSHOOTINGBOOK.scr:53
        ctx:state().Done = true -- ILSSHOOTINGBOOK.scr:54
        do return ctx:exit("") end -- ILSSHOOTINGBOOK.scr:55
    end -- ILSSHOOTINGBOOK.scr:56
end

script.labels["Main"] = function(ctx)
    -- ILSSHOOTINGBOOK.scr:62
    ctx:getParam(0, "Params") -- ILSSHOOTINGBOOK.scr:67
    ctx:state().open = false -- ILSSHOOTINGBOOK.scr:68
    ctx:addTrigger("Use", "OnUse") -- ILSSHOOTINGBOOK.scr:69
    ctx:addTrigger("Done", "OnDone") -- ILSSHOOTINGBOOK.scr:70
    do return ctx:exit("") end -- ILSSHOOTINGBOOK.scr:72
end

return script
