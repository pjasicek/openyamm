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
    ctx:command("getobjecthandle", "guard g_hobject") -- SVENSHOWTAKE.inc:23
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:24
    ctx:command("getobjecthandle", "Kira g_hobject") -- SVENSHOWTAKE.inc:25
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:26
    ctx:command("getobjecthandle", "Kira0 g_hobject") -- SVENSHOWTAKE.inc:27
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:28
    ctx:command("getobjecthandle", "Sword0 g_hobject") -- SVENSHOWTAKE.inc:29
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:30
    ctx:command("getobjecthandle", "Sword1 g_hobject") -- SVENSHOWTAKE.inc:31
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:32
    ctx:command("getobjecthandle", "Sword2 g_hobject") -- SVENSHOWTAKE.inc:33
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:34
    ctx:command("getobjecthandle", "Sword3 g_hobject") -- SVENSHOWTAKE.inc:35
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:36
    ctx:command("getobjecthandle", "Sword4 g_hobject") -- SVENSHOWTAKE.inc:37
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:38
    ctx:command("getobjecthandle", "Sword5 g_hobject") -- SVENSHOWTAKE.inc:39
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:40
    ctx:command("getobjecthandle", "Sword6 g_hobject") -- SVENSHOWTAKE.inc:41
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:42
    ctx:command("getobjecthandle", "Sword7 g_hobject") -- SVENSHOWTAKE.inc:43
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:44
    ctx:command("getobjecthandle", "Sword8 g_hobject") -- SVENSHOWTAKE.inc:45
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:46
    ctx:command("getobjecthandle", "Sword9 g_hobject") -- SVENSHOWTAKE.inc:47
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:48
    ctx:command("getobjecthandle", "Sword10 g_hobject") -- SVENSHOWTAKE.inc:49
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:50
    ctx:command("getobjecthandle", "Sword11 g_hobject") -- SVENSHOWTAKE.inc:51
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:52
    ctx:command("getobjecthandle", "Sword12 g_hobject") -- SVENSHOWTAKE.inc:53
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:54
    ctx:command("getobjecthandle", "Sword13 g_hobject") -- SVENSHOWTAKE.inc:55
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:56
    ctx:command("getobjecthandle", "Sword14 g_hobject") -- SVENSHOWTAKE.inc:57
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:58
    ctx:command("getobjecthandle", "Sword15 g_hobject") -- SVENSHOWTAKE.inc:59
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:60
    ctx:command("getobjecthandle", "Sword16 g_hobject") -- SVENSHOWTAKE.inc:61
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:62
    ctx:command("getobjecthandle", "Sword17 g_hobject") -- SVENSHOWTAKE.inc:63
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:64
    ctx:command("getobjecthandle", "Sword18 g_hobject") -- SVENSHOWTAKE.inc:65
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:66
    ctx:command("getobjecthandle", "Sword19 g_hobject") -- SVENSHOWTAKE.inc:67
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:68
    ctx:command("getobjecthandle", "Sword20 g_hobject") -- SVENSHOWTAKE.inc:69
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:70
    ctx:command("getobjecthandle", "Sword21 g_hobject") -- SVENSHOWTAKE.inc:71
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:72
    ctx:command("getobjecthandle", "Sword22 g_hobject") -- SVENSHOWTAKE.inc:73
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:74
    ctx:command("getobjecthandle", "Sword23 g_hobject") -- SVENSHOWTAKE.inc:75
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:76
    ctx:command("getobjecthandle", "Sword24 g_hobject") -- SVENSHOWTAKE.inc:77
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:78
    ctx:command("getobjecthandle", "Sword25 g_hobject") -- SVENSHOWTAKE.inc:79
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:80
    ctx:command("getobjecthandle", "Sword26 g_hobject") -- SVENSHOWTAKE.inc:81
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:82
    ctx:command("getobjecthandle", "Sword27 g_hobject") -- SVENSHOWTAKE.inc:83
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:84
    ctx:command("getobjecthandle", "Sword28 g_hobject") -- SVENSHOWTAKE.inc:85
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:86
    ctx:command("getobjecthandle", "Sword29 g_hobject") -- SVENSHOWTAKE.inc:87
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:88
    ctx:command("getobjecthandle", "Sword30 g_hobject") -- SVENSHOWTAKE.inc:89
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:90
    ctx:command("getobjecthandle", "Sword31 g_hobject") -- SVENSHOWTAKE.inc:91
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:92
    ctx:command("getobjecthandle", "Sword32 g_hobject") -- SVENSHOWTAKE.inc:93
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:94
    ctx:command("getobjecthandle", "Sword33 g_hobject") -- SVENSHOWTAKE.inc:95
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:96
    ctx:command("getobjecthandle", "Sword34 g_hobject") -- SVENSHOWTAKE.inc:97
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:98
    ctx:command("getobjecthandle", "Sword35 g_hobject") -- SVENSHOWTAKE.inc:99
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:100
    ctx:command("getobjecthandle", "Sword36 g_hobject") -- SVENSHOWTAKE.inc:101
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:102
    ctx:command("getobjecthandle", "Sword37 g_hobject") -- SVENSHOWTAKE.inc:103
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:104
    ctx:command("getobjecthandle", "Sword38 g_hobject") -- SVENSHOWTAKE.inc:105
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:106
    ctx:command("getobjecthandle", "Sword39 g_hobject") -- SVENSHOWTAKE.inc:107
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:108
    ctx:command("getobjecthandle", "Sword40 g_hobject") -- SVENSHOWTAKE.inc:109
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:110
    ctx:command("getobjecthandle", "Sword41 g_hobject") -- SVENSHOWTAKE.inc:111
    mm9.gosub(script, ctx, "ClearSword") -- SVENSHOWTAKE.inc:112
    ctx:command("getobjecthandle", "Sven g_hobject") -- SVENSHOWTAKE.inc:114
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:115
    ctx:command("getobjecthandle", "Sven0 g_hobject") -- SVENSHOWTAKE.inc:116
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:117
    ctx:command("getobjecthandle", "Sven1 g_hobject") -- SVENSHOWTAKE.inc:118
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:119
    ctx:command("getobjecthandle", "Sven2 g_hobject") -- SVENSHOWTAKE.inc:120
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:121
    ctx:command("getobjecthandle", "Sven3 g_hobject") -- SVENSHOWTAKE.inc:122
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:123
    ctx:command("getobjecthandle", "Sven4 g_hobject") -- SVENSHOWTAKE.inc:124
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:125
    ctx:command("getobjecthandle", "Sven5 g_hobject") -- SVENSHOWTAKE.inc:126
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:127
    ctx:command("getobjecthandle", "Sven6 g_hobject") -- SVENSHOWTAKE.inc:128
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:129
    ctx:command("getobjecthandle", "Sven7 g_hobject") -- SVENSHOWTAKE.inc:130
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:131
    ctx:command("getobjecthandle", "Sven8 g_hobject") -- SVENSHOWTAKE.inc:132
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:133
    ctx:command("getobjecthandle", "Sven9 g_hobject") -- SVENSHOWTAKE.inc:134
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:135
    ctx:command("getobjecthandle", "Sven10 g_hobject") -- SVENSHOWTAKE.inc:136
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:137
    ctx:command("getobjecthandle", "Sven11 g_hobject") -- SVENSHOWTAKE.inc:138
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:139
    ctx:command("getobjecthandle", "Sven12 g_hobject") -- SVENSHOWTAKE.inc:140
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:141
    ctx:command("getobjecthandle", "Sven13 g_hobject") -- SVENSHOWTAKE.inc:142
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:143
    ctx:command("getobjecthandle", "Sven14 g_hobject") -- SVENSHOWTAKE.inc:144
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:145
    ctx:command("getobjecthandle", "Sven15 g_hobject") -- SVENSHOWTAKE.inc:146
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:147
    ctx:command("getobjecthandle", "Sven16 g_hobject") -- SVENSHOWTAKE.inc:148
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:149
    ctx:command("getobjecthandle", "Sven17 g_hobject") -- SVENSHOWTAKE.inc:150
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:151
    ctx:command("getobjecthandle", "Sven18 g_hobject") -- SVENSHOWTAKE.inc:152
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:153
    ctx:command("getobjecthandle", "Sven20 g_hobject") -- SVENSHOWTAKE.inc:155
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:156
    ctx:command("getobjecthandle", "Sven21 g_hobject") -- SVENSHOWTAKE.inc:157
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:158
    ctx:command("getobjecthandle", "Sven22 g_hobject") -- SVENSHOWTAKE.inc:159
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:160
    ctx:command("getobjecthandle", "Sven23 g_hobject") -- SVENSHOWTAKE.inc:161
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:162
    ctx:command("getobjecthandle", "Sven24 g_hobject") -- SVENSHOWTAKE.inc:163
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:164
    ctx:command("getobjecthandle", "Sven25 g_hobject") -- SVENSHOWTAKE.inc:165
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:166
    ctx:command("getobjecthandle", "Sven26 g_hobject") -- SVENSHOWTAKE.inc:167
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:168
    ctx:command("getobjecthandle", "Sigmund g_hobject") -- SVENSHOWTAKE.inc:170
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:171
    ctx:command("getobjecthandle", "Thjorad g_hobject") -- SVENSHOWTAKE.inc:173
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:174
    ctx:command("getobjecthandle", "Tryygva g_hobject") -- SVENSHOWTAKE.inc:176
    mm9.gosub(script, ctx, "Clear") -- SVENSHOWTAKE.inc:177
    do return ctx:exit("") end -- SVENSHOWTAKE.inc:179
end

script.labels["Clear"] = function(ctx)
    -- SVENSHOWTAKE.inc:182
    if ctx:condition("g_hobject==NULL") then -- SVENSHOWTAKE.inc:185
        do return ctx:exit("") end -- SVENSHOWTAKE.inc:186
    end -- SVENSHOWTAKE.inc:187
    if ctx:condition("ShowAll==FALSE") then -- SVENSHOWTAKE.inc:189
        ctx:command("clearflag", "g_hobject, visible") -- SVENSHOWTAKE.inc:190
        ctx:command("clearflag", "g_hobject, solid") -- SVENSHOWTAKE.inc:191
        ctx:command("clearflag", "g_hobject, gravity") -- SVENSHOWTAKE.inc:192
        do return ctx:exit("") end -- SVENSHOWTAKE.inc:193
    else -- SVENSHOWTAKE.inc:194
        ctx:command("setflag", "g_hobject, visible") -- SVENSHOWTAKE.inc:195
        ctx:command("setflag", "g_hobject, solid") -- SVENSHOWTAKE.inc:196
        ctx:command("setflag", "g_hobject, gravity") -- SVENSHOWTAKE.inc:197
        do return ctx:exit("") end -- SVENSHOWTAKE.inc:198
    end -- SVENSHOWTAKE.inc:199
end

script.labels["ClearSword"] = function(ctx)
    -- SVENSHOWTAKE.inc:203
    if ctx:condition("g_hobject==NULL") then -- SVENSHOWTAKE.inc:206
        do return ctx:exit("") end -- SVENSHOWTAKE.inc:207
    end -- SVENSHOWTAKE.inc:208
    if ctx:condition("ShowAll==FALSE") then -- SVENSHOWTAKE.inc:210
        ctx:command("clearflag", "g_hobject, visible") -- SVENSHOWTAKE.inc:211
        do return ctx:exit("") end -- SVENSHOWTAKE.inc:212
    else -- SVENSHOWTAKE.inc:213
        ctx:command("setflag", "g_hobject, visible") -- SVENSHOWTAKE.inc:214
        do return ctx:exit("") end -- SVENSHOWTAKE.inc:215
    end -- SVENSHOWTAKE.inc:216
end

return script
