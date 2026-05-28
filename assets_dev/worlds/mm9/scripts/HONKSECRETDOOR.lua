-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HONKSECRETDOOR.scr"
script.includes = {}
script.labels = {}


-- Honksecretdoor.scr
-- Brett Yagi
-- 10/09/2001
script.labels["dn"] = function(ctx)
    -- HONKSECRETDOOR.scr:27
    do return ctx:exit(1) end -- HONKSECRETDOOR.scr:28
end

script.labels["OpenDoor"] = function(ctx)
    -- HONKSECRETDOOR.scr:33
    ctx:trigger("hSecretDoor", "open") -- HONKSECRETDOOR.scr:36
    ctx:command("wait", "0 20 resetbuttons") -- HONKSECRETDOOR.scr:37
    do return ctx:exit(1) end -- HONKSECRETDOOR.scr:39
end

script.labels["resetButtons"] = function(ctx)
    -- HONKSECRETDOOR.scr:42
    ctx:command("noksoofar", "= 0") -- HONKSECRETDOOR.scr:45
    ctx:command("count", "= 0") -- HONKSECRETDOOR.scr:46
    -- trigger hHButton unlock
    ctx:trigger("hHColumn", "close") -- HONKSECRETDOOR.scr:48
    -- trigger hOButton unlock
    ctx:trigger("hOColumn", "close") -- HONKSECRETDOOR.scr:50
    -- trigger hNButton unlock
    ctx:trigger("hNColumn", "close") -- HONKSECRETDOOR.scr:52
    -- trigger hKButton unlock
    ctx:trigger("hKColumn", "close") -- HONKSECRETDOOR.scr:54
    do return ctx:exit(1) end -- HONKSECRETDOOR.scr:56
end

script.labels["hpressed"] = function(ctx)
    -- HONKSECRETDOOR.scr:59
    ctx:command("count", "= count + 1") -- HONKSECRETDOOR.scr:63
    if ctx:condition("count != 1") then -- HONKSECRETDOOR.scr:64
        ctx:command("noksoofar", "= 1") -- HONKSECRETDOOR.scr:65
        if ctx:condition("count == 4") then -- HONKSECRETDOOR.scr:66
            mm9.gosub(script, ctx, "resetButtons") -- HONKSECRETDOOR.scr:67
        end -- HONKSECRETDOOR.scr:68
    end -- HONKSECRETDOOR.scr:69
    do return ctx:exit(1) end -- HONKSECRETDOOR.scr:70
end

script.labels["opressed"] = function(ctx)
    -- HONKSECRETDOOR.scr:73
    ctx:command("count", "= count + 1") -- HONKSECRETDOOR.scr:77
    if ctx:condition("count != 2") then -- HONKSECRETDOOR.scr:78
        ctx:command("noksoofar", "= 1") -- HONKSECRETDOOR.scr:79
        if ctx:condition("count == 4") then -- HONKSECRETDOOR.scr:80
            mm9.gosub(script, ctx, "resetButtons") -- HONKSECRETDOOR.scr:81
        end -- HONKSECRETDOOR.scr:82
    end -- HONKSECRETDOOR.scr:83
    do return ctx:exit(1) end -- HONKSECRETDOOR.scr:84
end

script.labels["npressed"] = function(ctx)
    -- HONKSECRETDOOR.scr:87
    ctx:command("count", "= count + 1") -- HONKSECRETDOOR.scr:91
    if ctx:condition("count != 3") then -- HONKSECRETDOOR.scr:92
        ctx:command("noksoofar", "= 1") -- HONKSECRETDOOR.scr:93
        if ctx:condition("count == 4") then -- HONKSECRETDOOR.scr:94
            mm9.gosub(script, ctx, "resetButtons") -- HONKSECRETDOOR.scr:95
        end -- HONKSECRETDOOR.scr:96
    end -- HONKSECRETDOOR.scr:97
    do return ctx:exit(1) end -- HONKSECRETDOOR.scr:98
end

script.labels["kpressed"] = function(ctx)
    -- HONKSECRETDOOR.scr:101
    ctx:command("count", "= count + 1") -- HONKSECRETDOOR.scr:105
    if ctx:condition("count != 4") then -- HONKSECRETDOOR.scr:106
        ctx:command("noksoofar", "= 1") -- HONKSECRETDOOR.scr:107
    else -- HONKSECRETDOOR.scr:108
        if ctx:condition("nOkSooFar == 1") then -- HONKSECRETDOOR.scr:109
            mm9.gosub(script, ctx, "resetButtons") -- HONKSECRETDOOR.scr:110
        else -- HONKSECRETDOOR.scr:112
            ctx:hasKey("nKeyNumber", "nHasKey") -- HONKSECRETDOOR.scr:113
            if ctx:condition("nHasKey = 1") then -- HONKSECRETDOOR.scr:114
                mm9.gosub(script, ctx, "OpenDoor") -- HONKSECRETDOOR.scr:115
            else -- HONKSECRETDOOR.scr:116
                ctx:command("wait", "0 2 resetButtons") -- HONKSECRETDOOR.scr:117
            end -- HONKSECRETDOOR.scr:118
        end -- HONKSECRETDOOR.scr:121
    end -- HONKSECRETDOOR.scr:123
    do return ctx:exit(1) end -- HONKSECRETDOOR.scr:125
end

script.labels["UnlockButtons"] = function(ctx)
    -- HONKSECRETDOOR.scr:128
    ctx:trigger("hHButton", "unlock") -- HONKSECRETDOOR.scr:131
    ctx:trigger("hOButton", "unlock") -- HONKSECRETDOOR.scr:132
    ctx:trigger("hNButton", "unlock") -- HONKSECRETDOOR.scr:133
    ctx:trigger("hKButton", "unlock") -- HONKSECRETDOOR.scr:134
    do return ctx:exit(1) end -- HONKSECRETDOOR.scr:137
end

script.labels["Main2"] = function(ctx)
    -- HONKSECRETDOOR.scr:141
    ctx:command("getobjecthandle", "HButton hHButton") -- HONKSECRETDOOR.scr:144
    ctx:command("getobjecthandle", "OButton hOButton") -- HONKSECRETDOOR.scr:145
    ctx:command("getobjecthandle", "NButton hNButton") -- HONKSECRETDOOR.scr:146
    ctx:command("getobjecthandle", "KButton hKButton") -- HONKSECRETDOOR.scr:147
    ctx:command("getobjecthandle", "HCornerStone hHColumn") -- HONKSECRETDOOR.scr:148
    ctx:command("getobjecthandle", "OCornerStone hOColumn") -- HONKSECRETDOOR.scr:149
    ctx:command("getobjecthandle", "NCornerStone hNColumn") -- HONKSECRETDOOR.scr:150
    ctx:command("getobjecthandle", "KCornerStone hKColumn") -- HONKSECRETDOOR.scr:151
    ctx:command("getobjecthandle", "secretdoor hSecretDoor") -- HONKSECRETDOOR.scr:153
    ctx:hasKey("nKeyNumber", "nHasKey") -- HONKSECRETDOOR.scr:154
    if ctx:condition("nHasKey = 1") then -- HONKSECRETDOOR.scr:155
        ctx:trigger("hHButton", "unlock") -- HONKSECRETDOOR.scr:156
        ctx:trigger("hOButton", "unlock") -- HONKSECRETDOOR.scr:157
        ctx:trigger("hNButton", "unlock") -- HONKSECRETDOOR.scr:158
        ctx:trigger("hKButton", "unlock") -- HONKSECRETDOOR.scr:159
    end -- HONKSECRETDOOR.scr:160
    do return ctx:exit(1) end -- HONKSECRETDOOR.scr:163
end

script.labels["Main"] = function(ctx)
    -- HONKSECRETDOOR.scr:167
    ctx:addTrigger("reset", "resetButtons") -- HONKSECRETDOOR.scr:170
    ctx:addTrigger("UnlockButtons", "UnlockButtons") -- HONKSECRETDOOR.scr:172
    ctx:addTrigger("hPressed", "hPressed") -- HONKSECRETDOOR.scr:173
    ctx:addTrigger("oPressed", "oPressed") -- HONKSECRETDOOR.scr:174
    ctx:addTrigger("nPressed", "nPressed") -- HONKSECRETDOOR.scr:175
    ctx:addTrigger("kPressed", "kPressed") -- HONKSECRETDOOR.scr:176
    ctx:command("wait", "0 .1 Main2") -- HONKSECRETDOOR.scr:177
    do return ctx:exit(1) end -- HONKSECRETDOOR.scr:181
end

return script
