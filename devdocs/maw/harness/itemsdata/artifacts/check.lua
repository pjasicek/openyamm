local mt={__index=function(t,k) return k end}
const={Stats=setmetatable({},mt), Skills=setmetatable({},mt)}
dofile(arg[1])
local ids={} for k in pairs(artifactPower) do ids[#ids+1]=k end table.sort(ids)
for _,id in ipairs(ids) do
  local p=artifactPower[id]; local parts={}
  for k,v in pairs(p) do
    if type(v)=="table" then for k2,v2 in pairs(v) do parts[#parts+1]=k.."."..k2.."="..tostring(v2) end
    else parts[#parts+1]=k.."="..tostring(v) end
  end
  table.sort(parts); print(id, table.concat(parts," "))
end
