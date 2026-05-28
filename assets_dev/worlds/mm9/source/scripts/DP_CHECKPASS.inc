;------------------------------
;	DP_CheckPass.inc
;	by SJR
;	Purpose:routine for checking
;			the visitor's pass at
;			DrangheimPrison.
;			must gosub CheckPassInit
;------------------------------
#include	baseMelee.inc

#number		DP_PASS_FRIENDLY = 5007
#number		DP_PASS_HOSTILE	 = 5006

#hobject	checkpass_hObject = 0

#number		checkpass_bAttackOk = 0
#number		checkpass_bIsPlayer = 0
#number		checkpass_bIsVisitor = 0
#number		checkpass_bIsFriendly = 0

;--------------------
:InitCheckPass
;	set up handlers etc
;--------------------
	gosub BaseInit

	;;gotta override BaseMelee.inc for these
	OnFoundTarget OnFoundTarget
	OnDamage OnDamage

	Exit 1

;--------------------
:OnFoundTarget
;	override baseMelee handlers everywhere
;--------------------
	GetParam 0, checkpass_hObject
	IsPlayer checkpass_hObject, checkpass_bIsPlayer

	HasKey DP_PASS_FRIENDLY, checkpass_bIsVisitor

	;;IsFriendly actually used as IsHostile
	HasKey DP_PASS_HOSTILE, checkpass_bIsFriendly

	;;change to IsFriendly with IsFriendly=!IsHostile
	checkpass_bIsFriendly = 1 - checkpass_bIsFriendly

	;; == 0 if notplayer OR notvisitor OR notfriendly
	checkpass_bAttackOk = checkpass_bIsPlayer * checkpass_bIsVisitor * checkpass_bIsFriendly

	;; if == 0, attack
	if( checkpass_bAttackOk == 0 )
		gosub LinkToBaseMelee
	endif

	Exit 1

;--------------------
:OnDamage
;	override baseMelee handlers everywhere
;--------------------
	GetParam 0, checkpass_hObject
	IsPlayer checkpass_hObject, checkpass_bIsPlayer

	;;if player damages us, give them the hostile key
	if( checkpass_bIsPlayer==1 )
		GiveKey DP_PASS_HOSTILE
		gosub LinkToBaseMelee
	endif

	HasKey DP_PASS_FRIENDLY, checkpass_bIsVisitor

	;;IsFriendly actually used as IsHostile
	HasKey DP_PASS_HOSTILE, checkpass_bIsFriendly

	;;change to IsFriendly with IsFriendly=!IsHostile
	checkpass_bIsFriendly = 1 - checkpass_bIsFriendly

	;; == 0 if notplayer OR notvisitor OR notfriendly
	checkpass_bAttackOk = checkpass_bIsPlayer * checkpass_bIsVisitor * checkpass_bIsFriendly

	;; if == 0, attack
	if( checkpass_bAttackOk == 0 )
		gosub LinkToBaseMelee
	endif

	Exit 1

;--------------------
:LinkToBaseMelee
;	transfer control to baseMelee
;--------------------
	;;baseMelee needs this, since removed GetParam
	g_hTarget = checkpass_hObject

	gosub SetupTarget
	gosub AggressiveStop

	GetRandomInt 0, 100, g_nRandom

	if ( g_nRandom < AWARE_CHANCE )
		Aware AwareDone
	else
		gosub AggressiveStart
	endif

	Exit 1