-- MAW content of this map (devdocs/maw/MM9_BALANCE_DESIGN.md): loaded after the world's events, for MAW games only.

-- The prison's alarm (key 5006, the map's alarm(): the bell, the guards turned) calls the garrison: guards of every
-- rank come out at the posts farthest from the party, never within 1500 of it, so the party is not swarmed where it
-- stands (the user, 2026-11-09). Its packs are the map Lua's own and take no density copies; this is MAW's density
-- for it. The posts are guards' places in the scene, spread over the prison.
local POSTS = {
    {-1434, 164, -81}, {-2396, -6963, -2231}, {2755, -2683, -1904},
    {-4639, 840, -1576}, {-5888, -4628, -1904}, {-328, -4342, -2231},
}
local POSTS_CALLED = 4
local GUARDS = 9111   -- MM9 Guard A; the tiers draw Sergeants (B) and Captains (C)

local function guardsPerPost()
    local info = evt.RulesetInfo()
    if info.challengeMode == "doom" or info.challengeMode == "road_to_insanity"
        or info.challengeMode == "beyond_madness" then
        return 5
    end
    return info.difficulty >= 4 and 4 or 3   -- Hell and Nightmare 4, the others 3
end

RegisterMapTimerEvent(60101, 1, function()
    if evt.GetMapVar("MawPrisonGarrison", 0) ~= 0 or MM9.hasKey(5006) ~= 1 then
        return
    end
    evt.SetMapVar("MawPrisonGarrison", 1)
    local px, py, pz = evt.GetPartyPosition()
    local posts = {}
    for _, post in ipairs(POSTS) do
        local dx, dy, dz = post[1] - px, post[2] - py, (post[3] - pz) * 2
        local distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        if distance >= 1500 then
            posts[#posts + 1] = {post = post, distance = distance}
        end
    end
    table.sort(posts, function(a, b) return a.distance > b.distance end)
    for index = 1, math.min(POSTS_CALLED, #posts) do
        local post = posts[index].post
        evt.SummonMonstersById{monster = GUARDS, x = post[1], y = post[2], z = post[3], count = guardsPerPost(),
            tiers = {50, 35, 15}, radius = 256, group = 2, hostile = true}
    end
    evt.StatusText("The garrison answers the bell!")
end, "MAW prison garrison")
