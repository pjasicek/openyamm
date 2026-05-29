-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ILSSKELETONSTART.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- ILSskeletonstart.scr
-- timmy
-- drops 4 skeletons into the skeleton pit
script.labels["OnUse"] = function(ctx)
    -- ILSSKELETONSTART.scr:16
    ctx:object("skeletondoora"):trigger("Close") -- ILSSKELETONSTART.scr:19-20
    ctx:wait(3, 3, "Spawn") -- ILSSKELETONSTART.scr:22
    do return ctx:exit("") end -- ILSSKELETONSTART.scr:23
end

script.labels["Spawn"] = function(ctx)
    -- ILSSKELETONSTART.scr:26
    if ctx:condition("On==true") then -- ILSSKELETONSTART.scr:29
        ctx:state().g_hobject = ctx:objectOrNil("spawnskeleton") -- ILSSKELETONSTART.scr:32
        if ctx:condition("g_hobject (!=NULL)") then -- ILSSKELETONSTART.scr:34
            ctx:trigger("g_hobject", "default") -- ILSSKELETONSTART.scr:35
            ctx:state().g_hobject = ctx:objectOrNil("spawnskeleton1") -- ILSSKELETONSTART.scr:38
            if ctx:condition("g_hobject (!=NULL)") then -- ILSSKELETONSTART.scr:40
                ctx:trigger("g_hobject", "default") -- ILSSKELETONSTART.scr:41
                ctx:state().g_hobject = ctx:objectOrNil("spawnskeleton2") -- ILSSKELETONSTART.scr:44
                if ctx:condition("g_hobject (!=NULL)") then -- ILSSKELETONSTART.scr:46
                    ctx:trigger("g_hobject", "default") -- ILSSKELETONSTART.scr:47
                    ctx:state().g_hobject = ctx:objectOrNil("spawnskeleton3") -- ILSSKELETONSTART.scr:49
                    if ctx:condition("g_hobject (!=NULL)") then -- ILSSKELETONSTART.scr:50
                        ctx:trigger("g_hobject", "default") -- ILSSKELETONSTART.scr:51
                        ctx:state().g_hobject = ctx:objectOrNil("skeletonlever2") -- ILSSKELETONSTART.scr:53
                        if ctx:condition("g_hobject (!=NULL)") then -- ILSSKELETONSTART.scr:54
                            ctx:trigger("G_hobject", "TurnOn") -- ILSSKELETONSTART.scr:55
                            ctx:state().On = false -- ILSSKELETONSTART.scr:56
                        end -- ILSSKELETONSTART.scr:59
                    end -- ILSSKELETONSTART.scr:60
                end -- ILSSKELETONSTART.scr:61
            end -- ILSSKELETONSTART.scr:62
        end -- ILSSKELETONSTART.scr:63
        do return ctx:exit("") end -- ILSSKELETONSTART.scr:64
    end -- ILSSKELETONSTART.scr:66
    do return ctx:exit("") end -- ILSSKELETONSTART.scr:68
end

script.labels["OnTurnOn"] = function(ctx)
    -- ILSSKELETONSTART.scr:71
    ctx:state().On = true -- ILSSKELETONSTART.scr:74
    do return ctx:exit("") end -- ILSSKELETONSTART.scr:76
end

script.labels["Main"] = function(ctx)
    -- ILSSKELETONSTART.scr:82
    -- traceon
    -- don't ferget to delete me
    ctx:addTrigger("Use", "OnUse") -- ILSSKELETONSTART.scr:90
    ctx:addTrigger("TurnOn", "OnTurnOn") -- ILSSKELETONSTART.scr:91
    ctx:state().On = true -- ILSSKELETONSTART.scr:92
    do return ctx:exit("") end -- ILSSKELETONSTART.scr:94
end

return script
