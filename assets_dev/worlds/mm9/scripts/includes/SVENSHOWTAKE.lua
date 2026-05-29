-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SVENSHOWTAKE.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- svenshowtake.inc
-- 1/5/02
-- timmy
-- handles model removal for battlefield cutscene
-- flag variables
script.labels["RemoveAll"] = function(ctx)
    -- SVENSHOWTAKE.inc:20
    ctx:state().g_hobject = ctx:objectOrNil("guard") -- SVENSHOWTAKE.inc:23
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:24
    ctx:state().g_hobject = ctx:objectOrNil("Kira") -- SVENSHOWTAKE.inc:25
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:26
    ctx:state().g_hobject = ctx:objectOrNil("Kira0") -- SVENSHOWTAKE.inc:27
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:28
    ctx:state().g_hobject = ctx:objectOrNil("Sword0") -- SVENSHOWTAKE.inc:29
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:30
    ctx:state().g_hobject = ctx:objectOrNil("Sword1") -- SVENSHOWTAKE.inc:31
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:32
    ctx:state().g_hobject = ctx:objectOrNil("Sword2") -- SVENSHOWTAKE.inc:33
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:34
    ctx:state().g_hobject = ctx:objectOrNil("Sword3") -- SVENSHOWTAKE.inc:35
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:36
    ctx:state().g_hobject = ctx:objectOrNil("Sword4") -- SVENSHOWTAKE.inc:37
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:38
    ctx:state().g_hobject = ctx:objectOrNil("Sword5") -- SVENSHOWTAKE.inc:39
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:40
    ctx:state().g_hobject = ctx:objectOrNil("Sword6") -- SVENSHOWTAKE.inc:41
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:42
    ctx:state().g_hobject = ctx:objectOrNil("Sword7") -- SVENSHOWTAKE.inc:43
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:44
    ctx:state().g_hobject = ctx:objectOrNil("Sword8") -- SVENSHOWTAKE.inc:45
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:46
    ctx:state().g_hobject = ctx:objectOrNil("Sword9") -- SVENSHOWTAKE.inc:47
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:48
    ctx:state().g_hobject = ctx:objectOrNil("Sword10") -- SVENSHOWTAKE.inc:49
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:50
    ctx:state().g_hobject = ctx:objectOrNil("Sword11") -- SVENSHOWTAKE.inc:51
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:52
    ctx:state().g_hobject = ctx:objectOrNil("Sword12") -- SVENSHOWTAKE.inc:53
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:54
    ctx:state().g_hobject = ctx:objectOrNil("Sword13") -- SVENSHOWTAKE.inc:55
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:56
    ctx:state().g_hobject = ctx:objectOrNil("Sword14") -- SVENSHOWTAKE.inc:57
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:58
    ctx:state().g_hobject = ctx:objectOrNil("Sword15") -- SVENSHOWTAKE.inc:59
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:60
    ctx:state().g_hobject = ctx:objectOrNil("Sword16") -- SVENSHOWTAKE.inc:61
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:62
    ctx:state().g_hobject = ctx:objectOrNil("Sword17") -- SVENSHOWTAKE.inc:63
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:64
    ctx:state().g_hobject = ctx:objectOrNil("Sword18") -- SVENSHOWTAKE.inc:65
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:66
    ctx:state().g_hobject = ctx:objectOrNil("Sword19") -- SVENSHOWTAKE.inc:67
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:68
    ctx:state().g_hobject = ctx:objectOrNil("Sword20") -- SVENSHOWTAKE.inc:69
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:70
    ctx:state().g_hobject = ctx:objectOrNil("Sword21") -- SVENSHOWTAKE.inc:71
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:72
    ctx:state().g_hobject = ctx:objectOrNil("Sword22") -- SVENSHOWTAKE.inc:73
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:74
    ctx:state().g_hobject = ctx:objectOrNil("Sword23") -- SVENSHOWTAKE.inc:75
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:76
    ctx:state().g_hobject = ctx:objectOrNil("Sword24") -- SVENSHOWTAKE.inc:77
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:78
    ctx:state().g_hobject = ctx:objectOrNil("Sword25") -- SVENSHOWTAKE.inc:79
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:80
    ctx:state().g_hobject = ctx:objectOrNil("Sword26") -- SVENSHOWTAKE.inc:81
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:82
    ctx:state().g_hobject = ctx:objectOrNil("Sword27") -- SVENSHOWTAKE.inc:83
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:84
    ctx:state().g_hobject = ctx:objectOrNil("Sword28") -- SVENSHOWTAKE.inc:85
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:86
    ctx:state().g_hobject = ctx:objectOrNil("Sword29") -- SVENSHOWTAKE.inc:87
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:88
    ctx:state().g_hobject = ctx:objectOrNil("Sword30") -- SVENSHOWTAKE.inc:89
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:90
    ctx:state().g_hobject = ctx:objectOrNil("Sword31") -- SVENSHOWTAKE.inc:91
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:92
    ctx:state().g_hobject = ctx:objectOrNil("Sword32") -- SVENSHOWTAKE.inc:93
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:94
    ctx:state().g_hobject = ctx:objectOrNil("Sword33") -- SVENSHOWTAKE.inc:95
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:96
    ctx:state().g_hobject = ctx:objectOrNil("Sword34") -- SVENSHOWTAKE.inc:97
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:98
    ctx:state().g_hobject = ctx:objectOrNil("Sword35") -- SVENSHOWTAKE.inc:99
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:100
    ctx:state().g_hobject = ctx:objectOrNil("Sword36") -- SVENSHOWTAKE.inc:101
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:102
    ctx:state().g_hobject = ctx:objectOrNil("Sword37") -- SVENSHOWTAKE.inc:103
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:104
    ctx:state().g_hobject = ctx:objectOrNil("Sword38") -- SVENSHOWTAKE.inc:105
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:106
    ctx:state().g_hobject = ctx:objectOrNil("Sword39") -- SVENSHOWTAKE.inc:107
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:108
    ctx:state().g_hobject = ctx:objectOrNil("Sword40") -- SVENSHOWTAKE.inc:109
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:110
    ctx:state().g_hobject = ctx:objectOrNil("Sword41") -- SVENSHOWTAKE.inc:111
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:112
    ctx:state().g_hobject = ctx:objectOrNil("Sven") -- SVENSHOWTAKE.inc:114
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:115
    ctx:state().g_hobject = ctx:objectOrNil("Sven0") -- SVENSHOWTAKE.inc:116
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:117
    ctx:state().g_hobject = ctx:objectOrNil("Sven1") -- SVENSHOWTAKE.inc:118
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:119
    ctx:state().g_hobject = ctx:objectOrNil("Sven2") -- SVENSHOWTAKE.inc:120
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:121
    ctx:state().g_hobject = ctx:objectOrNil("Sven3") -- SVENSHOWTAKE.inc:122
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:123
    ctx:state().g_hobject = ctx:objectOrNil("Sven4") -- SVENSHOWTAKE.inc:124
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:125
    ctx:state().g_hobject = ctx:objectOrNil("Sven5") -- SVENSHOWTAKE.inc:126
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:127
    ctx:state().g_hobject = ctx:objectOrNil("Sven6") -- SVENSHOWTAKE.inc:128
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:129
    ctx:state().g_hobject = ctx:objectOrNil("Sven7") -- SVENSHOWTAKE.inc:130
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:131
    ctx:state().g_hobject = ctx:objectOrNil("Sven8") -- SVENSHOWTAKE.inc:132
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:133
    ctx:state().g_hobject = ctx:objectOrNil("Sven9") -- SVENSHOWTAKE.inc:134
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:135
    ctx:state().g_hobject = ctx:objectOrNil("Sven10") -- SVENSHOWTAKE.inc:136
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:137
    ctx:state().g_hobject = ctx:objectOrNil("Sven11") -- SVENSHOWTAKE.inc:138
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:139
    ctx:state().g_hobject = ctx:objectOrNil("Sven12") -- SVENSHOWTAKE.inc:140
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:141
    ctx:state().g_hobject = ctx:objectOrNil("Sven13") -- SVENSHOWTAKE.inc:142
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:143
    ctx:state().g_hobject = ctx:objectOrNil("Sven14") -- SVENSHOWTAKE.inc:144
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:145
    ctx:state().g_hobject = ctx:objectOrNil("Sven15") -- SVENSHOWTAKE.inc:146
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:147
    ctx:state().g_hobject = ctx:objectOrNil("Sven16") -- SVENSHOWTAKE.inc:148
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:149
    ctx:state().g_hobject = ctx:objectOrNil("Sven17") -- SVENSHOWTAKE.inc:150
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:151
    ctx:state().g_hobject = ctx:objectOrNil("Sven18") -- SVENSHOWTAKE.inc:152
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:153
    ctx:state().g_hobject = ctx:objectOrNil("Sven20") -- SVENSHOWTAKE.inc:155
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:156
    ctx:state().g_hobject = ctx:objectOrNil("Sven21") -- SVENSHOWTAKE.inc:157
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:158
    ctx:state().g_hobject = ctx:objectOrNil("Sven22") -- SVENSHOWTAKE.inc:159
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:160
    ctx:state().g_hobject = ctx:objectOrNil("Sven23") -- SVENSHOWTAKE.inc:161
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:162
    ctx:state().g_hobject = ctx:objectOrNil("Sven24") -- SVENSHOWTAKE.inc:163
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:164
    ctx:state().g_hobject = ctx:objectOrNil("Sven25") -- SVENSHOWTAKE.inc:165
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:166
    ctx:state().g_hobject = ctx:objectOrNil("Sven26") -- SVENSHOWTAKE.inc:167
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:168
    ctx:state().g_hobject = ctx:objectOrNil("Sigmund") -- SVENSHOWTAKE.inc:170
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:171
    ctx:state().g_hobject = ctx:objectOrNil("Thjorad") -- SVENSHOWTAKE.inc:173
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:174
    ctx:state().g_hobject = ctx:objectOrNil("Tryygva") -- SVENSHOWTAKE.inc:176
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:177
    do return ctx:exit("") end -- SVENSHOWTAKE.inc:179
end

script.labels["Clear"] = function(ctx)
    -- SVENSHOWTAKE.inc:182
    if ctx:condition("g_hobject==NULL") then -- SVENSHOWTAKE.inc:185
        do return ctx:exit("") end -- SVENSHOWTAKE.inc:186
    end -- SVENSHOWTAKE.inc:187
    if ctx:condition("ShowAll==FALSE") then -- SVENSHOWTAKE.inc:189
        ctx:object("g_hobject"):setFlag("visible", false) -- SVENSHOWTAKE.inc:190
        ctx:object("g_hobject"):setFlag("solid", false) -- SVENSHOWTAKE.inc:191
        ctx:object("g_hobject"):setFlag("gravity", false) -- SVENSHOWTAKE.inc:192
        do return ctx:exit("") end -- SVENSHOWTAKE.inc:193
    else -- SVENSHOWTAKE.inc:194
        ctx:object("g_hobject"):setFlag("visible", true) -- SVENSHOWTAKE.inc:195
        ctx:object("g_hobject"):setFlag("solid", true) -- SVENSHOWTAKE.inc:196
        ctx:object("g_hobject"):setFlag("gravity", true) -- SVENSHOWTAKE.inc:197
        do return ctx:exit("") end -- SVENSHOWTAKE.inc:198
    end -- SVENSHOWTAKE.inc:199
end

script.labels["ClearSword"] = function(ctx)
    -- SVENSHOWTAKE.inc:203
    if ctx:condition("g_hobject==NULL") then -- SVENSHOWTAKE.inc:206
        do return ctx:exit("") end -- SVENSHOWTAKE.inc:207
    end -- SVENSHOWTAKE.inc:208
    if ctx:condition("ShowAll==FALSE") then -- SVENSHOWTAKE.inc:210
        ctx:object("g_hobject"):setFlag("visible", false) -- SVENSHOWTAKE.inc:211
        do return ctx:exit("") end -- SVENSHOWTAKE.inc:212
    else -- SVENSHOWTAKE.inc:213
        ctx:object("g_hobject"):setFlag("visible", true) -- SVENSHOWTAKE.inc:214
        do return ctx:exit("") end -- SVENSHOWTAKE.inc:215
    end -- SVENSHOWTAKE.inc:216
end

return script
