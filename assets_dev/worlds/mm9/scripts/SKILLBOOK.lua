-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SKILLBOOK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- SkillBook.scr
-- 9/21
-- timmy
-- Gives the Player a SkillBook
-- Parameters
-- P0 the NAME of the skill book to give
script.labels["OnUse"] = function(ctx)
    -- SKILLBOOK.scr:19
    -- this opens the book
    ctx:giveItem("Item_Id") -- SKILLBOOK.scr:24
    ctx:self():remove() -- SKILLBOOK.scr:26
    do return ctx:exit("") end -- SKILLBOOK.scr:27
end

script.labels["SkillInit"] = function(ctx)
    -- SKILLBOOK.scr:32
    -- This assigns the Item_ID based on Skill_Name
    -- ItemID	ItemName
    -- 285	Blade Skill
    -- 286	Bow Skill
    -- 287	Cudgel Skill
    -- 288	Spear Skill
    -- 289	Armsmaster Skill
    -- 290	Unarmed Skill
    -- 291	Armor Skill
    -- 292	Shield Skill
    -- 293	Dodge Skill
    -- 294	Elemental Skill
    -- 295	Light Skill
    -- 296	Dark Skill
    -- 297	Spirit Skill
    -- 298	Disarm Trap Skill
    -- 299	Merchant Skill
    -- 300	Perception Skill
    -- 301	Repair Item Skill
    -- 302	Identify Item Skill
    -- 303	Identify Monster Skill
    -- 304	Body Building Skill
    -- 305	Learning Skill
    -- 306	Meditation Skill
    if ctx:condition("Skill_Name==0") then -- SKILLBOOK.scr:62
        ctx:randomInt(285, 306, "g_ntemp") -- SKILLBOOK.scr:63
        ctx:set("Item_ID", "g_ntemp") -- SKILLBOOK.scr:64
        do return ctx:exit("") end -- SKILLBOOK.scr:65
    end -- SKILLBOOK.scr:66
    if ctx:condition("Skill_Name==Random") then -- SKILLBOOK.scr:68
        ctx:randomInt(285, 306, "g_ntemp") -- SKILLBOOK.scr:69
        ctx:set("Item_ID", "g_ntemp") -- SKILLBOOK.scr:70
        do return ctx:exit("") end -- SKILLBOOK.scr:71
    end -- SKILLBOOK.scr:72
    if ctx:condition("Skill_Name==Blade") then -- SKILLBOOK.scr:75
        ctx:state().Item_Id = 285 -- SKILLBOOK.scr:76
        do return ctx:exit("") end -- SKILLBOOK.scr:77
    end -- SKILLBOOK.scr:78
    if ctx:condition("Skill_Name==Bow") then -- SKILLBOOK.scr:80
        ctx:state().Item_Id = 286 -- SKILLBOOK.scr:81
        do return ctx:exit("") end -- SKILLBOOK.scr:82
    end -- SKILLBOOK.scr:83
    if ctx:condition("Skill_Name==Cudgel") then -- SKILLBOOK.scr:85
        ctx:state().Item_Id = 287 -- SKILLBOOK.scr:86
        do return ctx:exit("") end -- SKILLBOOK.scr:87
    end -- SKILLBOOK.scr:88
    if ctx:condition("Skill_Name==Spear") then -- SKILLBOOK.scr:90
        ctx:state().Item_Id = 288 -- SKILLBOOK.scr:91
        do return ctx:exit("") end -- SKILLBOOK.scr:92
    end -- SKILLBOOK.scr:93
    if ctx:condition("Skill_Name==Armsmaster") then -- SKILLBOOK.scr:95
        ctx:state().Item_Id = 289 -- SKILLBOOK.scr:96
        do return ctx:exit("") end -- SKILLBOOK.scr:97
    end -- SKILLBOOK.scr:98
    if ctx:condition("Skill_Name==Unarmed") then -- SKILLBOOK.scr:100
        ctx:state().Item_Id = 290 -- SKILLBOOK.scr:101
        do return ctx:exit("") end -- SKILLBOOK.scr:102
    end -- SKILLBOOK.scr:103
    if ctx:condition("Skill_Name==Armor") then -- SKILLBOOK.scr:105
        ctx:state().Item_Id = 291 -- SKILLBOOK.scr:106
        do return ctx:exit("") end -- SKILLBOOK.scr:107
    end -- SKILLBOOK.scr:108
    if ctx:condition("Skill_Name==Shield") then -- SKILLBOOK.scr:110
        ctx:state().Item_Id = 292 -- SKILLBOOK.scr:111
        do return ctx:exit("") end -- SKILLBOOK.scr:112
    end -- SKILLBOOK.scr:113
    if ctx:condition("Skill_Name==Dodge") then -- SKILLBOOK.scr:115
        ctx:state().Item_Id = 293 -- SKILLBOOK.scr:116
        do return ctx:exit("") end -- SKILLBOOK.scr:117
    end -- SKILLBOOK.scr:118
    if ctx:condition("Skill_Name==Elemental") then -- SKILLBOOK.scr:120
        ctx:state().Item_Id = 294 -- SKILLBOOK.scr:121
        do return ctx:exit("") end -- SKILLBOOK.scr:122
    end -- SKILLBOOK.scr:123
    if ctx:condition("Skill_Name==Light") then -- SKILLBOOK.scr:125
        ctx:state().Item_Id = 295 -- SKILLBOOK.scr:126
        do return ctx:exit("") end -- SKILLBOOK.scr:127
    end -- SKILLBOOK.scr:128
    if ctx:condition("Skill_Name==Dark") then -- SKILLBOOK.scr:130
        ctx:state().Item_Id = 296 -- SKILLBOOK.scr:131
        do return ctx:exit("") end -- SKILLBOOK.scr:132
    end -- SKILLBOOK.scr:133
    if ctx:condition("Skill_Name==Sprit") then -- SKILLBOOK.scr:135
        ctx:state().Item_Id = 297 -- SKILLBOOK.scr:136
        do return ctx:exit("") end -- SKILLBOOK.scr:137
    end -- SKILLBOOK.scr:138
    if ctx:condition("Skill_Name==Disarm") then -- SKILLBOOK.scr:140
        ctx:state().Item_Id = 298 -- SKILLBOOK.scr:141
        do return ctx:exit("") end -- SKILLBOOK.scr:142
    end -- SKILLBOOK.scr:143
    if ctx:condition("Skill_Name==Merchant") then -- SKILLBOOK.scr:145
        ctx:state().Item_Id = 299 -- SKILLBOOK.scr:146
        do return ctx:exit("") end -- SKILLBOOK.scr:147
    end -- SKILLBOOK.scr:148
    if ctx:condition("Skill_Name==Perception") then -- SKILLBOOK.scr:150
        ctx:state().Item_Id = 300 -- SKILLBOOK.scr:151
        do return ctx:exit("") end -- SKILLBOOK.scr:152
    end -- SKILLBOOK.scr:153
    if ctx:condition("Skill_Name==Repair") then -- SKILLBOOK.scr:155
        ctx:state().Item_Id = 301 -- SKILLBOOK.scr:156
        do return ctx:exit("") end -- SKILLBOOK.scr:157
    end -- SKILLBOOK.scr:158
    if ctx:condition("Skill_Name==ID_Item") then -- SKILLBOOK.scr:160
        ctx:state().Item_Id = 302 -- SKILLBOOK.scr:161
        do return ctx:exit("") end -- SKILLBOOK.scr:162
    end -- SKILLBOOK.scr:163
    if ctx:condition("Skill_Name==ID_Monster") then -- SKILLBOOK.scr:165
        ctx:state().Item_Id = 303 -- SKILLBOOK.scr:166
        do return ctx:exit("") end -- SKILLBOOK.scr:167
    end -- SKILLBOOK.scr:168
    if ctx:condition("Skill_Name==Body") then -- SKILLBOOK.scr:170
        ctx:state().Item_Id = 304 -- SKILLBOOK.scr:171
        do return ctx:exit("") end -- SKILLBOOK.scr:172
    end -- SKILLBOOK.scr:173
    if ctx:condition("Skill_Name==Learning") then -- SKILLBOOK.scr:175
        ctx:state().Item_Id = 305 -- SKILLBOOK.scr:176
        do return ctx:exit("") end -- SKILLBOOK.scr:177
    end -- SKILLBOOK.scr:178
    if ctx:condition("Skill_Name==Meditation") then -- SKILLBOOK.scr:180
        ctx:state().Item_Id = 306 -- SKILLBOOK.scr:181
        do return ctx:exit("") end -- SKILLBOOK.scr:182
    end -- SKILLBOOK.scr:183
    do return ctx:exit("") end -- SKILLBOOK.scr:185
end

script.labels["Main"] = function(ctx)
    -- SKILLBOOK.scr:190
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Use", "OnUse") -- SKILLBOOK.scr:195
    ctx:getParam(0, "Skill_Name") -- SKILLBOOK.scr:196
    mm9.gosub(script, ctx, "SkillInit") -- SKILLBOOK.scr:197
    do return ctx:exit("") end -- SKILLBOOK.scr:199
end

return script
