;--------------------------------------------------
;svenshowtake.inc
;1/5/02
; timmy
; handles model removal for battlefield cutscene

;--------------------------------------------------

#include globals.inc

; flag variables
#number							Visible = 1
#number							Solid   = 8192
#number							Gravity = 131072

#number		ShowAll


;----------------------------------------------
:RemoveAll
;----------------------------------------------

getobjecthandle guard g_hobject
	gosub ClearSword
getobjecthandle Kira g_hobject
	gosub ClearSword
getobjecthandle Kira0 g_hobject
	gosub ClearSword
getobjecthandle Sword0 g_hobject
	gosub ClearSword
getobjecthandle Sword1 g_hobject
	gosub ClearSword
getobjecthandle Sword2 g_hobject
	gosub ClearSword
getobjecthandle Sword3 g_hobject
	gosub ClearSword
getobjecthandle Sword4 g_hobject
	gosub ClearSword
getobjecthandle Sword5 g_hobject
	gosub ClearSword
getobjecthandle Sword6 g_hobject
	gosub ClearSword
getobjecthandle Sword7 g_hobject
	gosub ClearSword
getobjecthandle Sword8 g_hobject
	gosub ClearSword
getobjecthandle Sword9 g_hobject
	gosub ClearSword
getobjecthandle Sword10 g_hobject
	gosub ClearSword
getobjecthandle Sword11 g_hobject
	gosub ClearSword
getobjecthandle Sword12 g_hobject
	gosub ClearSword
getobjecthandle Sword13 g_hobject
	gosub ClearSword
getobjecthandle Sword14 g_hobject
	gosub ClearSword
getobjecthandle Sword15 g_hobject
	gosub ClearSword
getobjecthandle Sword16 g_hobject
	gosub ClearSword
getobjecthandle Sword17 g_hobject
	gosub ClearSword
getobjecthandle Sword18 g_hobject
	gosub ClearSword
getobjecthandle Sword19 g_hobject
	gosub ClearSword
getobjecthandle Sword20 g_hobject
	gosub ClearSword
getobjecthandle Sword21 g_hobject
	gosub ClearSword
getobjecthandle Sword22 g_hobject
	gosub ClearSword
getobjecthandle Sword23 g_hobject
	gosub ClearSword
getobjecthandle Sword24 g_hobject
	gosub ClearSword
getobjecthandle Sword25 g_hobject
	gosub ClearSword
getobjecthandle Sword26 g_hobject
	gosub ClearSword
getobjecthandle Sword27 g_hobject
	gosub ClearSword
getobjecthandle Sword28 g_hobject
	gosub ClearSword
getobjecthandle Sword29 g_hobject
	gosub ClearSword
getobjecthandle Sword30 g_hobject
	gosub ClearSword
getobjecthandle Sword31 g_hobject
	gosub ClearSword
getobjecthandle Sword32 g_hobject
	gosub ClearSword
getobjecthandle Sword33 g_hobject
	gosub ClearSword
getobjecthandle Sword34 g_hobject
	gosub ClearSword
getobjecthandle Sword35 g_hobject
	gosub ClearSword
getobjecthandle Sword36 g_hobject
	gosub ClearSword
getobjecthandle Sword37 g_hobject
	gosub ClearSword
getobjecthandle Sword38 g_hobject
	gosub ClearSword
getobjecthandle Sword39 g_hobject
	gosub ClearSword
getobjecthandle Sword40 g_hobject
	gosub ClearSword
getobjecthandle Sword41 g_hobject
	gosub ClearSword

getobjecthandle Sven g_hobject
	gosub Clear
getobjecthandle Sven0 g_hobject
	gosub Clear
getobjecthandle Sven1 g_hobject
	gosub Clear
getobjecthandle Sven2 g_hobject
	gosub Clear
getobjecthandle Sven3 g_hobject
	gosub Clear
getobjecthandle Sven4 g_hobject
	gosub Clear
getobjecthandle Sven5 g_hobject
	gosub Clear
getobjecthandle Sven6 g_hobject
	gosub Clear
getobjecthandle Sven7 g_hobject
	gosub Clear
getobjecthandle Sven8 g_hobject
	gosub Clear
getobjecthandle Sven9 g_hobject
	gosub Clear
getobjecthandle Sven10 g_hobject
	gosub Clear
getobjecthandle Sven11 g_hobject
	gosub Clear
getobjecthandle Sven12 g_hobject
	gosub Clear
getobjecthandle Sven13 g_hobject
	gosub Clear
getobjecthandle Sven14 g_hobject
	gosub Clear
getobjecthandle Sven15 g_hobject
	gosub Clear
getobjecthandle Sven16 g_hobject
	gosub Clear
getobjecthandle Sven17 g_hobject
	gosub Clear
getobjecthandle Sven18 g_hobject
	gosub Clear

getobjecthandle Sven20 g_hobject
	gosub Clear
getobjecthandle Sven21 g_hobject
	gosub Clear
getobjecthandle Sven22 g_hobject
	gosub Clear
getobjecthandle Sven23 g_hobject
	gosub Clear
getobjecthandle Sven24 g_hobject
	gosub Clear
getobjecthandle Sven25 g_hobject
	gosub Clear
getobjecthandle Sven26 g_hobject
	gosub Clear

getobjecthandle Sigmund g_hobject
	gosub Clear

getobjecthandle Thjorad g_hobject
	gosub Clear

getobjecthandle Tryygva g_hobject
	gosub Clear

exit

;----------------------------------------------
:Clear
;----------------------------------------------

if (g_hobject==NULL)
	exit
endif

if (ShowAll==FALSE)
	clearflag g_hobject, visible
	clearflag g_hobject, solid
	clearflag g_hobject, gravity
	exit
else
	setflag g_hobject, visible
	setflag g_hobject, solid
	setflag g_hobject, gravity
	exit
endif


;----------------------------------------------
:ClearSword
;----------------------------------------------

if (g_hobject==NULL)
	exit
endif

if (ShowAll==FALSE)
	clearflag g_hobject, visible
	exit
else
	setflag g_hobject, visible
	exit
endif

