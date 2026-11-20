import json,sys
m=int(sys.argv[1]); kind=sys.argv[2]
T='/home/pjasicek/github/OpenYAMM/output/studio_cal/mm6_6d18/t1/'
th=[{"id":"theme:a","wall":{"texture":"vlcwl1","size":[128,128]},"floor":{"texture":"vlcflora","size":[128,128]},"ceiling":{"texture":"vlctrm3","size":[128,128]}}]
if kind=='outline':
    pl=[{"outline":[[1024+m,0],[1152,0],[1152,640],[1024+m,640]],"rise":32,"base":0},
        {"outline":[[1024+m,600],[1152,600],[1152,1024-m],[1024+m,1024-m]],"rise":32,"base":0},
        {"outline":[[1100,896],[2048-m,896],[2048-m,1024-m],[1100,1024-m]],"rise":32,"base":0}]
else:
    pl=[{"at":[1088+m/2,320],"size":[128-m,640],"rise":32,"base":0},
        {"at":[1088+m/2,812-m/2],"size":[128-m,424-m],"rise":32,"base":0},
        {"at":[1574-m/2,960-m/2],"size":[948-m,128-m],"rise":32,"base":0}]
rooms=[{"id":"room:up","outline":[[0,0],[1024,0],[1024,512],[0,512]],"floor":0,"ceiling":256},
 {"id":"room:tower","outline":[[1024,-512],[2048,-512],[2048,1024],[1024,1024]],"floor":-512,"ceiling":1024,
  "levels":[{"outline":[[1024,-512],[1280,-512],[1280,-256],[1024,-256]],"floor":-400},{"outline":[[1280,-512],[1536,-512],[1536,-256],[1280,-256]],"floor":-300}],
  "platforms":pl},
 {"id":"room:low","outline":[[2048,0],[2560,0],[2560,1024],[2048,1024]],"floor":32,"ceiling":512}]
op=[{"id":"open:a","from":"room:up","to":"room:tower","width":"full","height":"full"},{"id":"open:b","from":"room:tower","to":"room:low","width":120,"height":200,"along":0.9}]
json.dump({"format":0,"themes":th,"defaults":{"theme":"theme:a","ambient":16},"rooms":rooms,"openings":op},open(T+'rooms.yml','w'))
