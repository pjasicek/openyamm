-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ILSSKELETONSTOP.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- ILSskeletonstop.scr
-- timmy
-- turns skeletons into monsters
script.labels["OnUse"] = function(ctx)
    -- ILSSKELETONSTOP.scr:14
    if ctx:condition("On==true") then -- ILSSKELETONSTOP.scr:18
        ctx:state().g_hObject = ctx:objectOrNil("skeletonlight") -- ILSSKELETONSTOP.scr:20
        if ctx:condition("g_hObject!=NULL") then -- ILSSKELETONSTOP.scr:21
            ctx:trigger("g_hObject", "On") -- ILSSKELETONSTOP.scr:22
        end -- ILSSKELETONSTOP.scr:23
        ctx:state().g_hObject = ctx:objectOrNil("steam1") -- ILSSKELETONSTOP.scr:26
        if ctx:condition("g_hObject!=NULL") then -- ILSSKELETONSTOP.scr:27
            ctx:trigger("g_hObject", "On") -- ILSSKELETONSTOP.scr:28
        end -- ILSSKELETONSTOP.scr:29
        ctx:state().g_hObject = ctx:objectOrNil("steam2") -- ILSSKELETONSTOP.scr:32
        if ctx:condition("g_hObject!=NULL") then -- ILSSKELETONSTOP.scr:33
            ctx:trigger("g_hObject", "On") -- ILSSKELETONSTOP.scr:34
        end -- ILSSKELETONSTOP.scr:35
        ctx:state().g_hObject = ctx:objectOrNil("steam3") -- ILSSKELETONSTOP.scr:37
        if ctx:condition("g_hObject!=NULL") then -- ILSSKELETONSTOP.scr:38
            ctx:trigger("g_hObject", "On") -- ILSSKELETONSTOP.scr:39
        end -- ILSSKELETONSTOP.scr:40
        ctx:state().g_hobject = ctx:objectOrNil("skeletona") -- ILSSKELETONSTOP.scr:42
        if ctx:condition("g_hobject (!=NULL)") then -- ILSSKELETONSTOP.scr:44
            ctx:object("g_hobject"):remove() -- ILSSKELETONSTOP.scr:45
            ctx:state().g_hobject = ctx:objectOrNil("skeletonb") -- ILSSKELETONSTOP.scr:48
            if ctx:condition("g_hobject (!=NULL)") then -- ILSSKELETONSTOP.scr:50
                ctx:object("g_hobject"):remove() -- ILSSKELETONSTOP.scr:51
                ctx:state().g_hobject = ctx:objectOrNil("skeletonc") -- ILSSKELETONSTOP.scr:54
                if ctx:condition("g_hobject (!=NULL)") then -- ILSSKELETONSTOP.scr:56
                    ctx:object("g_hobject"):remove() -- ILSSKELETONSTOP.scr:57
                    ctx:state().g_hobject = ctx:objectOrNil("skeletond") -- ILSSKELETONSTOP.scr:59
                    if ctx:condition("g_hobject (!=NULL)") then -- ILSSKELETONSTOP.scr:60
                        ctx:object("g_hobject"):remove() -- ILSSKELETONSTOP.scr:61
                        ctx:state().g_hobject = ctx:objectOrNil("skeletonlever1") -- ILSSKELETONSTOP.scr:64
                        if ctx:condition("g_hobject (!=NULL)") then -- ILSSKELETONSTOP.scr:65
                            ctx:trigger("G_hobject", "TurnOn") -- ILSSKELETONSTOP.scr:66
                            ctx:state().On = false -- ILSSKELETONSTOP.scr:67
                            mm9.gosub(script, ctx, "Spawn") -- ILSSKELETONSTOP.scr:68
                            ctx:wait(4, 4, "OnDone") -- ILSSKELETONSTOP.scr:69
                        end -- ILSSKELETONSTOP.scr:71
                    end -- ILSSKELETONSTOP.scr:73
                end -- ILSSKELETONSTOP.scr:74
            end -- ILSSKELETONSTOP.scr:75
        end -- ILSSKELETONSTOP.scr:76
        do return ctx:exit("") end -- ILSSKELETONSTOP.scr:77
    end -- ILSSKELETONSTOP.scr:79
    do return ctx:exit("") end -- ILSSKELETONSTOP.scr:81
end

script.labels["Spawn"] = function(ctx)
    -- ILSSKELETONSTOP.scr:84
    -- ------------------Replace Nobleman with Skeleton!!!!!!!!!!________________________
    ctx:state().g_hobject = ctx:objectOrNil("spawnskeleton") -- ILSSKELETONSTOP.scr:90
    if ctx:condition("g_hobject (!=NULL)") then -- ILSSKELETONSTOP.scr:92
        ctx:trigger("g_hobject", "Nobleman") -- ILSSKELETONSTOP.scr:93
        ctx:state().g_hobject = ctx:objectOrNil("spawnskeleton1") -- ILSSKELETONSTOP.scr:95
        if ctx:condition("g_hobject (!=NULL)") then -- ILSSKELETONSTOP.scr:96
            ctx:trigger("g_hobject", "Nobleman") -- ILSSKELETONSTOP.scr:97
            ctx:state().g_hobject = ctx:objectOrNil("spawnskeleton2") -- ILSSKELETONSTOP.scr:99
            if ctx:condition("g_hobject (!=NULL)") then -- ILSSKELETONSTOP.scr:100
                ctx:trigger("g_hobject", "Nobleman") -- ILSSKELETONSTOP.scr:101
                ctx:state().g_hobject = ctx:objectOrNil("spawnskeleton3") -- ILSSKELETONSTOP.scr:103
                if ctx:condition("g_hobject (!=NULL)") then -- ILSSKELETONSTOP.scr:104
                    ctx:trigger("g_hobject", "Nobleman") -- ILSSKELETONSTOP.scr:105
                end -- ILSSKELETONSTOP.scr:106
            end -- ILSSKELETONSTOP.scr:107
        end -- ILSSKELETONSTOP.scr:108
    end -- ILSSKELETONSTOP.scr:109
    do return ctx:exit("") end -- ILSSKELETONSTOP.scr:111
end

script.labels["OnDone"] = function(ctx)
    -- ILSSKELETONSTOP.scr:113
    ctx:object("skeletondoora"):trigger("Use") -- ILSSKELETONSTOP.scr:117-118
    -- GetObjecthandle steam1, g_hobject
    -- trigger g_hobject, Off
    -- GetObjecthandle steam2, g_hobject
    -- trigger g_hobject, Off
    -- GetObjecthandle steam3, g_hobject
    -- trigger g_hobject, Off
    ctx:state().g_hObject = ctx:objectOrNil("skeletonlight") -- ILSSKELETONSTOP.scr:130
    if ctx:condition("g_hObject!=NULL") then -- ILSSKELETONSTOP.scr:131
        ctx:trigger("g_hObject", "Off") -- ILSSKELETONSTOP.scr:132
    end -- ILSSKELETONSTOP.scr:133
    do return ctx:exit("") end -- ILSSKELETONSTOP.scr:135
end

script.labels["OnTurnOn"] = function(ctx)
    -- ILSSKELETONSTOP.scr:137
    ctx:state().On = true -- ILSSKELETONSTOP.scr:140
    do return ctx:exit("") end -- ILSSKELETONSTOP.scr:141
end

script.labels["Main"] = function(ctx)
    -- ILSSKELETONSTOP.scr:145
    -- traceon
    -- don't ferget to delete me
    ctx:addTrigger("Use", "OnUse") -- ILSSKELETONSTOP.scr:153
    ctx:addTrigger("TurnOn", "OnTurnOn") -- ILSSKELETONSTOP.scr:154
    ctx:state().On = false -- ILSSKELETONSTOP.scr:155
    do return ctx:exit("") end -- ILSSKELETONSTOP.scr:157
end

return script
