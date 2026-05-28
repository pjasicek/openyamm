-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "dragonstadium"
map.scripts = {}


function map.register(ctx)
    if ctx == nil or ctx.registerMm9MapEvents == nil then
        return
    end
    ctx:registerMm9MapEvents(map)
end

return map
