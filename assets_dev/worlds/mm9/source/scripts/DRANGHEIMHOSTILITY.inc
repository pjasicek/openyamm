;-----------------------------------
;	DrangheimHostility.inc
;	by SJR
;	Purpose:routine for checking
;			the visitor's pass at
;			DrangheimPrison.
;			must gosub CheckPassInit
;-----------------------------------
#include	baseMelee.inc

#number		DP_PASS_FRIENDLY = 5007
#number		DP_PASS_HOSTILE	 = 5006

#number		checkpass_bAttackOk = 0
#number		checkpass_bIsPlayer = 0
#number		checkpass_bIsVisitor = 0
#number		checkpass_bIsFriendly = 0

#number		checkpass_bHostile = 0

;-----------------------------------
:InitDrangheimHostility
;	set up handlers etc
;-----------------------------------
	gosub BaseInit

	checkpass_bHostile = FALSE

	OnFoundPlayer	OnFoundPlayer
	OnDamage		OnDamage
	OnDeath			OnDeath

	AddFriend Player

	AddTrigger hostile, TurnHostilityOn

	Exit TRUE

;-----------------------------------
:OnFoundPlayer
;	override baseMelee handlers everywhere
;-----------------------------------
	HasKey DP_PASS_FRIENDLY, checkpass_bIsVisitor
	HasKey DP_PASS_HOSTILE,  checkpass_bIsFriendly
	checkpass_bIsFriendly = 1 - checkpass_bIsFriendly

	checkpass_bAttackOk = checkpass_bIsVisitor * checkpass_bIsFriendly

	if( checkpass_bAttackOk==0 )
		checkpass_bHostile = TRUE
		OnFoundPlayer DoNothing
		GetPlayerHandle g_hTarget
		gosub SetupTarget
		gosub AggressiveStart
	endif

	Exit TRUE

;-----------------------------------
:OnDamage
;	override baseMelee handlers everywhere
;-----------------------------------
	if( checkpass_bHostile==FALSE )
		GetParam 0, g_hTarget
		IsPlayer g_hTarget, checkpass_bIsPlayer

		if( checkpass_bIsPlayer==TRUE )
			gosub TurnHostilityOn
		endif
	endif

	gosub OnDamage,1

	Exit TRUE

;-----------------------------------
:OnDeath
;	override baseMelee handlers everywhere
;-----------------------------------
	if( checkpass_bHostile==FALSE )
		GetParam 0, g_hTarget
		IsPlayer g_hTarget, checkpass_bIsPlayer

		if( checkpass_bIsPlayer==TRUE )
			gosub TurnHostilityOn
		endif
	endif

	gosub OnDeath,2

	Exit TRUE

;-----------------------------------
:TurnHostilityOn
;-----------------------------------
	AddEnemy Player

	AddTrigger use, BlockRude

	GiveKey DP_PASS_HOSTILE

	PlaySound "sounds\events\alarmbell.wav", DoNothing, 1, 5000, FALSE, 100

	Exit TRUE

;----------------------------------
:BlockRude
;----------------------------------
	Exit TRUE
