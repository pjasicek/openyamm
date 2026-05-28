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
    ctx:command("getobjecthandle", "skeletondoora, g_hobject") -- ILSSKELETONSTART.scr:19
    ctx:trigger("g_hobject", "Close") -- ILSSKELETONSTART.scr:20
    ctx:command("wait", "3, Spawn") -- ILSSKELETONSTART.scr:22
    do return ctx:exit("") end -- ILSSKELETONSTART.scr:23
end

script.labels["Spawn"] = function(ctx)
    -- ILSSKELETONSTART.scr:26
    if ctx:condition("On==true") then -- ILSSKELETONSTART.scr:29
        ctx:command("getobjecthandle", "spawnskeleton, g_hobject") -- ILSSKELETONSTART.scr:32
        if ctx:condition("g_hobject (!=NULL)") then -- ILSSKELETONSTART.scr:34
            ctx:trigger("g_hobject", "default") -- ILSSKELETONSTART.scr:35
            ctx:command("getobjecthandle", "spawnskeleton1, g_hobject") -- ILSSKELETONSTART.scr:38
            if ctx:condition("g_hobject (!=NULL)") then -- ILSSKELETONSTART.scr:40
                ctx:trigger("g_hobject", "default") -- ILSSKELETONSTART.scr:41
                ctx:command("getobjecthandle", "spawnskeleton2, g_hobject") -- ILSSKELETONSTART.scr:44
                if ctx:condition("g_hobject (!=NULL)") then -- ILSSKELETONSTART.scr:46
                    ctx:trigger("g_hobject", "default") -- ILSSKELETONSTART.scr:47
                    ctx:command("getobjecthandle", "spawnskeleton3, g_hobject") -- ILSSKELETONSTART.scr:49
                    if ctx:condition("g_hobject (!=NULL)") then -- ILSSKELETONSTART.scr:50
                        ctx:trigger("g_hobject", "default") -- ILSSKELETONSTART.scr:51
                        ctx:command("getobjecthandle", "skeletonlever2, g_hobject") -- ILSSKELETONSTART.scr:53
                        if ctx:condition("g_hobject (!=NULL)") then -- ILSSKELETONSTART.scr:54
                            ctx:trigger("G_hobject", "TurnOn") -- ILSSKELETONSTART.scr:55
                            ctx:command("set", "On, False") -- ILSSKELETONSTART.scr:56
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
    ctx:command("set", "On, True") -- ILSSKELETONSTART.scr:74
    do return ctx:exit("") end -- ILSSKELETONSTART.scr:76
end

script.labels["Main"] = function(ctx)
    -- ILSSKELETONSTART.scr:82
    -- traceon
    -- don't ferget to delete me
    ctx:addTrigger("Use", "OnUse") -- ILSSKELETONSTART.scr:90
    ctx:addTrigger("TurnOn", "OnTurnOn") -- ILSSKELETONSTART.scr:91
    ctx:command("set", "On, True") -- ILSSKELETONSTART.scr:92
    do return ctx:exit("") end -- ILSSKELETONSTART.scr:94
end

return script
