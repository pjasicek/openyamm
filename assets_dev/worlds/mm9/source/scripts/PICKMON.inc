;----------------------------------------------
;PickiMon.inc
; By Timmy
; Picks a random monster from the list
; 11/29/01
;----------------------------------------------

#include globals.inc




#string							sMonster_temp
#number                         nMonster_Level


#number							nMonTemp






;-------------------------------------
:PickMonster
;-------------------------------------

if (g_ntemp>=1)
	if g_ntemp<=4)
		gosub Group1
		exit
	endif
endif

if (g_ntemp>=5)
	if (g_ntemp<=8)
		gosub Group2
		exit
	endif
endif

if (g_ntemp>=9)
	if (g_ntemp<=11)
		gosub Group3
		exit
	endif
endif

if (g_ntemp>=12)
	if (g_ntemp<=14)
		gosub Group4
		exit
	endif
endif

if (g_ntemp>=15)
	if (g_ntemp<=16)
		gosub Group5
		exit
	endif
endif

if (g_ntemp>=17)
	if (g_ntemp<=19)
		gosub Group6
		exit
	endif
endif

if (g_ntemp>=20)
	if (g_ntemp<=21)
		gosub Group7
		exit
	endif
endif

if (g_ntemp>=22)
	if (g_ntemp<=23)
		gosub Group8
		exit
	endif
endif

if (g_ntemp>=24)
	if (g_ntemp<=26)
		gosub Group9
		exit
	endif
endif

if (g_ntemp>=27)
	if (g_ntemp<=29)
		gosub Group10
		exit
	endif
endif

if (g_ntemp>=30)
	if (g_ntemp<=32)
		gosub Group11
		exit
	endif
endif

if (g_ntemp==33)
		gosub Group12
		exit
endif

if (g_ntemp>=34)
	if (g_ntemp<=37)
		gosub Group13
		exit
	endif
endif

if (g_ntemp>=38)
	if (g_ntemp<=39)
		gosub Group14
		exit
	endif
endif

if (g_ntemp>=40)
	if (g_ntemp<=43)
		gosub Group15
		exit
	endif
endif

if (g_ntemp>=44)
	if (g_ntemp<=47)
		gosub Group16
		exit
	endif
endif

if (g_ntemp>=48)
	if (g_ntemp<=53)
		gosub Group17
		exit
	endif
endif

if (g_ntemp>=54)
	if (g_ntemp<=58)
		gosub Group18
		exit
	endif
endif
if (g_ntemp>=59)
	if (g_ntemp<=64)
		gosub Group19
		exit
	endif
endif

if (g_ntemp>=65)
	if (g_ntemp<=74)
		gosub Group20
		exit
	endif
endif

if (g_ntemp>75)
		gosub Group21
		exit

endif



exit

;-------------------------------------
:Group1
; levels 1 - 4
;-------------------------------------

getrandomint 1, 4 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp DragonFlyMite
	set nMonster_Level 2
	exit
endif

if (nMonTemp==3)
	set sMonster_Temp DragonFly
	set nMonster_Level 3
	exit
endif

if (nMonTemp==2)
	set sMonster_Temp Imply
	set nMonster_Level 4
	exit
endif



if (nMonTemp==4)
	set sMonster_Temp Skeletoid
	set nMonster_Level 4
	exit
endif
exit

;-------------------------------------
:Group2
; levels 5 - 8
;-------------------------------------

getrandomint 1, 6 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp FireDragonFly
	set nMonster_Level 5
	exit
endif

if (nMonTemp==2)
	set sMonster_Temp NagateHatchling
	set nMonster_Level 6
	exit
endif

if (nMonTemp==3)
	set sMonster_Temp Imp
	set nMonster_Level 6
	exit
endif

if (nMonTemp==4)
	set sMonster_Temp BoneThrasher
	set nMonster_Level 8
	exit
endif

if (nMonTemp==5)
	set sMonster_Temp FieldThrall
	set nMonster_Level 8
	exit
endif

if (nMonTemp==6)
	set sMonster_Temp Cutpurse
	set nMonster_Level 8
	exit
endif
exit


;-------------------------------------
:Group3
; levels 9 - 11
;-------------------------------------

getrandomint 1, 5 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp Rotter
	set nMonster_Level 9
	exit
endif

if (nMonTemp==2)
	set sMonster_Temp Nagate
	set nMonster_Level 10
	exit
endif


if (nMonTemp==3)
	set sMonster_Temp ImpElder
	set nMonster_Level 10
	exit
endif



if (nMonTemp==4)
	set sMonster_Temp Troglodyte
	set nMonster_Level 10
	exit
endif

if (nMonTemp==5)
	set sMonster_Temp DwarvenGuard
	set nMonster_Level 10
	exit
endif
exit

;-------------------------------------
:Group4
; levels 12 - 14
;-------------------------------------

getrandomint 1, 5 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp Troglodyte

	set nMonster_Level 12
	exit
endif

if (nMonTemp==2)
	set sMonster_Temp Thrall
	set nMonster_Level 12
	exit
endif

if (nMonTemp==3)
	set sMonster_Temp Dripper
	set nMonster_Level 13
	exit
endif



if (nMonTemp==4)
	set sMonster_Temp HalfOrcRecruit
	set nMonster_Level 14
	exit
endif


if (nMonTemp==5)
	set sMonster_Temp Burgler
	set nMonster_Level 14
	exit
endif
exit

;-------------------------------------
:Group5
; levels 15 - 16
;-------------------------------------

getrandomint 1, 4 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp Gezzamptling
	set nMonster_Level 15
	exit
endif
if (nMonTemp==2)
	set sMonster_Temp Basilisk
	set nMonster_Level 15
	exit
endif


if (nMonTemp==3)
	set sMonster_Temp Skeleton
	set nMonster_Level 16
	exit
endif

if (nMonTemp==4)
	set sMonster_Temp Skeleton
	set nMonster_Level 16
	exit
endif
exit


;-------------------------------------
:Group6
; levels 17 - 19
;-------------------------------------

getrandomint 1, 4 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp TroglodyteWren
	set nMonster_Level 17
	exit
endif

if (nMonTemp==2)
	set sMonster_Temp Zombie
	set nMonster_Level 17
	exit
endif

if (nMonTemp==3)
	set sMonster_Temp ThrallMaster
	set nMonster_Level 18
	exit
endif

if (nMonTemp==4)
	set sMonster_Temp Bigfoot
	set nMonster_Level 18
	exit
endif
exit


;-------------------------------------
:Group7
;levels 20 -21
;-------------------------------------

getrandomint 1, 9 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp PoorTownGuard2
	set nMonster_Level 20
	exit
endif

if (nMonTemp==2)
	set sMonster_Temp Gezzampt
	set nMonster_Level 20
	exit
endif

if (nMonTemp==3)
	set sMonster_Temp PoorTownGuard1
	set nMonster_Level 20
	exit
endif

if (nMonTemp==4)
	set sMonster_Temp Guard
	set nMonster_Level 20
	exit
endif

if (nMonTemp==5)
	set sMonster_Temp GreyWolf
	set nMonster_Level 20
	exit
endif

if (nMonTemp==6)
	set sMonster_Temp DwarvenSoldier
	set nMonster_Level 20
	exit
endif

if (nMonTemp==7)
	set sMonster_Temp CanopicMummy
	set nMonster_Level 20
	exit
endif
if (nMonTemp==8)
	set sMonster_Temp Ghast
	set nMonster_Level 20
	exit
endif

if (nMonTemp==9)
	set sMonster_Temp Bloodsucker
	set nMonster_Level 20
	exit
endif
exit

;-------------------------------------
:Group8
; levels 22 - 23
;-------------------------------------

getrandomint 1, 5 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp Trellborg
	set nMonster_Level 22
	exit
endif
if (nMonTemp==2)
	set sMonster_Temp Bandit
	set nMonster_Level 22
	exit
endif

if (nMonTemp==3)
	set sMonster_Temp Magreeb
	set nMonster_Level 22
	exit
endif


if (nMonTemp==4)
	set sMonster_Temp SkeletonWarrior
	set nMonster_Level 22
	exit
endif

if (nMonTemp==5)
	set sMonster_Temp FibraseBasilisk
	set nMonster_Level 23
	exit
endif
exit

;-------------------------------------
:Group9
; levels 24 - 26
;-------------------------------------

getrandomint 1, 3 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp TroglodyteGnoll
	set nMonster_Level 24
	exit
endif


if (nMonTemp==2)
	set sMonster_Temp HalfOrcSoldier
	set nMonster_Level 24
	exit
endif

if (nMonTemp==3)
	set sMonster_Temp TroglodyteGnoll
	set nMonster_Level 24
	exit
endif
exit

;-------------------------------------
:Group10
; levels 27 -29
;-------------------------------------

getrandomint 1, 6 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp WingedOddity
	set nMonster_Level 27
	exit
endif


if (nMonTemp==2)
	set sMonster_Temp Ghoul
	set nMonster_Level 27
	exit
endif

if (nMonTemp==3)
	set sMonster_Temp GuardSegeant
	set nMonster_Level 28
	exit
endif

if (nMonTemp==4)
	set sMonster_Temp Sasquatch
	set nMonster_Level 28
	exit
endif

if (nMonTemp==5)
	set sMonster_Temp Sasquatch
	set nMonster_Level 28
	exit
endif


if (nMonTemp==6)
	set sMonster_Temp GezzamptElder
	set nMonster_Level 28
	exit
endif
exit

;-------------------------------------
:Group11
; levels 30 - 32
;-------------------------------------

getrandomint 1, 5 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp RedWolf
	set nMonster_Level 30
	exit
endif
if (nMonTemp==2)
	set sMonster_Temp EmbalmedMummy
	set nMonster_Level 30
	exit
endif

if (nMonTemp==3)
	set sMonster_Temp DwarvenCommander
	set nMonster_Level 30
	exit
endif

if (nMonTemp==4)
	set sMonster_Temp KingBasilisk
	set nMonster_Level 30
	exit
endif

if (nMonTemp==5)
	set sMonster_Temp KingBasilisk
	set nMonster_Level 30
	exit
endif
exit

;-------------------------------------
:Group12
;levels 33-33
;-------------------------------------

getrandomint 1, 6 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp SkeletonMaster
	set nMonster_Level 33
	exit
endif

if (nMonTemp==2)
	set sMonster_Temp Magreeb2
	set nMonster_Level 33
	exit
endif


if (nMonTemp==3)
	set sMonster_Temp Annelid
	set nMonster_Level 33
	exit
endif

if (nMonTemp==4)
	set sMonster_Temp GuardCaptain
	set nMonster_Level 33
	exit
endif


if (nMonTemp==5)
	set sMonster_Temp GuardCaptain
	set nMonster_Level 33
	exit
endif

if (nMonTemp==6)
	set sMonster_Temp Magreeb2
	set nMonster_Level 33
	exit
endif
exit

;-------------------------------------
:Group13
;levels 34-37
;-------------------------------------

getrandomint 1, 5 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp ClanSoldier
	set nMonster_Level 34
	exit
endif

if (nMonTemp==2)
	set sMonster_Temp Fright
	set nMonster_Level 35
	exit
endif

if (nMonTemp==3)
	set sMonster_Temp HalfOrcCaptain
	set nMonster_Level 35
	exit
endif

if (nMonTemp==4)
	set sMonster_Temp HalfOrcCaptain
	set nMonster_Level 35
	exit
endif

if (nMonTemp==5)
	set sMonster_Temp KinTrellborg
	set nMonster_Level 35
	exit
endif
exit

;-------------------------------------
:Group14
;levels 38-39
;-------------------------------------

getrandomint 1, 4 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp Revenant
	set nMonster_Level 38
	exit
endif

if (nMonTemp==2)
	set sMonster_Temp Yeti
	set nMonster_Level 38
	exit
endif


if (nMonTemp==3)
	set sMonster_Temp Dagrell
	set nMonster_Level 39
	exit
endif

if (nMonTemp==4)
	set sMonster_Temp WingedMutant
	set nMonster_Level 39
	exit
endif
exit

;-------------------------------------
:Group15
; levels 40 - 43
;-------------------------------------

getrandomint 1, 4 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp LizardOrc
	set nMonster_Level 40
	exit
endif


if (nMonTemp==2)
	set sMonster_Temp BlackWolf
	set nMonster_Level 40
	exit
endif

if (nMonTemp==3)
	set sMonster_Temp PetrifiedMummy
	set nMonster_Level 40
	exit
endif

if (nMonTemp==4)
	set sMonster_Temp LizardOrc
	set nMonster_Level 40
	exit
endif
exit

;-------------------------------------
:Group16
; levels 44-47
;-------------------------------------

getrandomint 1, 2 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp ClanCorporal
	set nMonster_Level 44
	exit
endif

if (nMonTemp==2)
	set sMonster_Temp Lich
	set nMonster_Level 45
	exit
endif
exit

;-------------------------------------
:Group17
; levels 48-53
;-------------------------------------

getrandomint 1, 3 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp Vampir
	set nMonster_Level 48
	exit
endif


if (nMonTemp==2)
	set sMonster_Temp AncientTrellborg
	set nMonster_Level 50
	exit
endif

if (nMonTemp==3)
	set sMonster_Temp WingedAberration
	set nMonster_Level 51
	exit
endif
exit


;-------------------------------------
:Group18
; levels 54 - 58
;-------------------------------------

getrandomint 1, 3 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp ClanSergeant
	set nMonster_Level 54
	exit
endif

if (nMonTemp==2)
	set sMonster_Temp Dread
	set nMonster_Level 55
	exit
endif

if (nMonTemp==3)
	set sMonster_Temp PowerLich
	set nMonster_Level 55
	exit
endif
exit

;-------------------------------------
:Group19
; levels 59 - 64
;-------------------------------------

getrandomint 1, 2 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp VenomousDagrell
	set nMonster_Level 59
	exit
endif


if (nMonTemp==2)
	set sMonster_Temp LizardOrcWarrior
	set nMonster_Level 60
	exit
endif
exit

;-------------------------------------
:Group20
; levels 65-74
;-------------------------------------

getrandomint 1, 2 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp Terror
	set nMonster_Level 65
	exit
endif

if (nMonTemp==2)
	set sMonster_Temp LichKing
	set nMonster_Level 65
	exit
endif
exit

;-------------------------------------
:Group21
; levels 75 - 89
;-------------------------------------

getrandomint 1, 2 nMonTemp

if (nMonTemp==1)
	set sMonster_Temp SpectreDagrell
	set nMonster_Level 79
	exit
endif


if (nMonTemp==2)
	set sMonster_Temp LizardOrcMage
	set nMonster_Level 80
	exit
endif

exit