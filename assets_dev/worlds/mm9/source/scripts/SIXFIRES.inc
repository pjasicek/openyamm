;--------------------------------------------------
;SixFires.inc
; timmy
; handles the Six Fires of Penance stuff
;--------------------------------------------------

#include globals.inc
#include Svenshowtake.inc

#number		nKeycheck

#string					sMonsterA = HordeGrunt
#string					sMonsterB = HordeLeader
#string					sMonsterC = HordeWarrior


#string					sGoodGuyA = ClanSoldier
#string					sGoodGuyB = ClanCorporal
#string					sGoodGuyC = ClanSergeant

#String					sBadGuys
#String					sGoodGuys

#hObject				hMonsterA
#hObject				hMonsterB
#hObject				hMonsterC
#hObject				hMonsterD


#hObject				hGoodGuyA
#hObject				hGoodGuyB
#hObject				hGoodGuyC

#hObject				hKira
#string					sKira = KiratheCold


#number							XPos
#number							YPos
#number							ZPos


#string							SCRIPT 

; flag variables
#number							Visible = 1
#number							Solid   = 8192
#number							Gravity = 131072

;--------------------------------------------------
:Guilt
;--------------------------------------------------

haskey 381 g_ntemp
if (g_ntemp==TRUE)
	exit
endif
screenfadeout 1
wait 1 1 FadeIn

exit




;--------------------------------------------------
:Spawn
;--------------------------------------------------







getobjecthandle sBadGuys g_hobject
getpos g_hobject XPos YPos ZPos
Spawn hMonsterA Xpos YPos ZPos sMonsterB
Spawn hMonsterB Xpos YPos ZPos sMonsterB
Spawn hMonsterC Xpos YPos ZPos sMonsterC
Spawn hMonsterD Xpos YPos ZPos sMonsterC
;Spawn hMonsterB Xpos YPos ZPos sMonsterB


getobjecthandle sGoodGuys g_hobject
getpos g_hobject XPos YPos ZPos


Spawn hGoodGuyA Xpos YPos ZPos sGoodGuyA
Spawn hGoodGuyB Xpos YPos ZPos sGoodGuya


exit



;-------------------------------------
:FadeIn
;-------------------------------------

letterbox true
getobjecthandle Camera9 g_hobject
trigger g_hobject On
trigger g_hobject play
screenfadein 1

exit

;-------------------------------------
:GoodGuys
;-------------------------------------

set SCRIPT " ScriptName Hate.scr"

sGoodGuyA = sGoodGuyA + Script
sGoodGuyB = sGoodGuyB + Script
sGoodGuyC = sGoodGuyc + Script



getobjecthandle sGoodGuys g_hobject
getpos g_hobject XPos YPos ZPos

;Spawn hMonsterC Xpos YPos ZPos sKira
Spawn hMonsterA Xpos YPos ZPos sGoodGuyA
Spawn hMonsterB Xpos YPos ZPos sGoodGuyB
Spawn hMonsterB Xpos YPos ZPos sGoodGuyB
Spawn hMonsterB Xpos YPos ZPos sGoodGuyC

wait 1 5 End
exit

;--------------------------------------------------
:End
;--------------------------------------------------



screenfadeout 2
wait 1 2 FadeIn2
exit

;-------------------------------------
:FadeIn2
;-------------------------------------

letterbox false
getobjecthandle Camera9 g_hobject
trigger g_hobject Off
screenfadein 1
OnFoundPlayer DoRude
exit

;-------------------------------------
:Confession
;-------------------------------------

haskey 383 g_ntemp
if (g_ntemp==TRUE)
	getobjecthandle BjarniThorvaldssen0 g_hobject
	Clearflag g_hobject visible
	getobjecthandle KiratheCold0 g_hobject
	Clearflag g_hobject visible
	getobjecthandle MarkeltheGreat0 g_hobject
	Clearflag g_hobject visible
	getobjecthandle SigmundtheStressed0 g_hobject
	Clearflag g_hobject visible
	getobjecthandle SvenSvenssen0 g_hobject
	Clearflag g_hobject visible
	getobjecthandle TryggvaRavenlocks0 g_hobject
	Clearflag g_hobject visible
	exit
	exit
endif

getobjecthandle BjarniThorvaldssen0 g_hobject
setflag g_hobject visible
getobjecthandle KiratheCold0 g_hobject
setflag g_hobject visible
getobjecthandle MarkeltheGreat0 g_hobject
setflag g_hobject visible
getobjecthandle SigmundtheStressed0 g_hobject
setflag g_hobject visible
getobjecthandle SvenSvenssen0 g_hobject
setflag g_hobject visible
getobjecthandle TryggvaRavenlocks0 g_hobject
setflag g_hobject visible
exit

;-------------------------------------
:Suffering
;-------------------------------------

haskey 491 g_ntemp
if (g_ntemp==TRUE)
	exit
endif


Haskey 385 g_ntemp
if (g_ntemp==TRUE)
	haskey 491 g_ntemp
	if (g_ntemp==false)
		GiveExp 52000
	endif
	givekey 491
	;take poisoning and disease away
	clearcondition 13
	getobjecthandle sufferingFire g_hobject
	trigger g_hobject On

	Playsound sounds\events\quest.wav, DoNothing, 100, 240, FALSE, 100
	exit
endif

wait 1 5 Questioner

exit

;-------------------------------------
:Questioner
;-------------------------------------

; poison and disease player

SetCondition 13
DoRude 432
exit


;-------------------------------------
:Retribution
;-------------------------------------

haskey 387 g_ntemp
if (g_ntemp==TRUE)
	exit
endif

haskey 5021 g_ntemp
if (g_ntemp==TRUE)
	exit
endif

givekey 5021

getobjecthandle ForadDarre0 g_hobject
setflag g_hobject visible

set sBadGuys BadGuys0

getobjecthandle sBadGuys g_hobject
getpos g_hobject XPos YPos ZPos
Spawn hMonsterA Xpos YPos ZPos sMonsterB
Spawn hMonsterB Xpos YPos ZPos sMonsterB
Spawn hMonsterC Xpos YPos ZPos sMonsterC
Spawn hMonsterD Xpos YPos ZPos sMonsterC
Spawn hMonsterB Xpos YPos ZPos sMonsterB

set sBadGuys BadGuys1

getobjecthandle sBadGuys g_hobject
getpos g_hobject XPos YPos ZPos
Spawn hMonsterA Xpos YPos ZPos sMonsterB
Spawn hMonsterB Xpos YPos ZPos sMonsterB
Spawn hMonsterC Xpos YPos ZPos sMonsterC
Spawn hMonsterD Xpos YPos ZPos sMonsterC
Spawn hMonsterB Xpos YPos ZPos sMonsterB
Spawn hMonsterA Xpos YPos ZPos sMonsterB
Spawn hMonsterB Xpos YPos ZPos sMonsterB
exit

;-------------------------------------
:Absolution
;-------------------------------------

getobjecthandle retributionFire g_hobject
trigger g_hobject On


haskey 492 g_ntemp
if (g_ntemp==TRUE)
	exit
endif

GiveExp 52000
givekey 492

Playsound sounds\events\quest.wav, DoNothing, 100, 240, FALSE, 100

set ShowAll, TRUE
gosub removeall

getobjecthandle svensword g_hobject
setflag g_hobject visible

getobjecthandle Bjarnisword g_hobject
setflag g_hobject visible

getobjecthandle Sigmundsword g_hobject
setflag g_hobject visible

getobjecthandle TryygvaSword g_hobject
setflag g_hobject visible

getobjecthandle Kirasword g_hobject
setflag g_hobject visible

set sMonsterA Zombie
set sMonsterB Ghast
set sMonsterC Fright

getobjecthandle Badguys0 g_hobject
getpos g_hobject XPos YPos ZPos
Spawn hMonsterA Xpos YPos ZPos sMonsterA


getobjecthandle BadGuys1 g_hobject
getpos g_hobject XPos YPos ZPos
Spawn hMonsterA Xpos YPos ZPos sMonsterB


getobjecthandle GoodGuys0 g_hobject
getpos g_hobject XPos YPos ZPos
Spawn hMonsterA Xpos YPos ZPos sMonsterC
Spawn hMonsterA Xpos YPos ZPos sMonsterC
Spawn hMonsterA Xpos YPos ZPos sMonsterC
Spawn hMonsterA Xpos YPos ZPos sMonsterC
Spawn hMonsterA Xpos YPos ZPos sMonsterC

exit
;-------------------------------------
:Rebirth
;-------------------------------------

getobjecthandle ExitTrigger1 g_hobject
trigger g_hobject On

set sMonsterA Zombie
set sMonsterB Ghast
set sMonsterC Fright

getobjecthandle Badguys0 g_hobject
getpos g_hobject XPos YPos ZPos
Spawn hMonsterA Xpos YPos ZPos sMonsterA


getobjecthandle BadGuys1 g_hobject
getpos g_hobject XPos YPos ZPos
Spawn hMonsterA Xpos YPos ZPos sMonsterB


getobjecthandle GoodGuys0 g_hobject
getpos g_hobject XPos YPos ZPos
Spawn hMonsterA Xpos YPos ZPos sMonsterC
Spawn hMonsterA Xpos YPos ZPos sMonsterC
Spawn hMonsterA Xpos YPos ZPos sMonsterC
Spawn hMonsterA Xpos YPos ZPos sMonsterC
Spawn hMonsterA Xpos YPos ZPos sMonsterC

exit
