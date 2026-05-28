;----------------------------------
;	DookHostility.scr
;	by SJR
;	01-01-02
;	Purpose:refrain from attacking player
;			until they go through the tunnel
;----------------------------------
#include baseMelee.inc

#hobject	hostile_hDOOK_HOSTILITY = 0

;----------------------------------
:InitDookHostility
;----------------------------------
	AddFriend Player

	GetObjectHandle DOOK_HOSTILITY, hostile_hDOOK_HOSTILITY
	if( hostile_hDOOK_HOSTILITY!=0 )
		CreateObjectLink hostile_hDOOK_HOSTILITY
		OnObjectLinkBroken BecomeHostile

		OnDamage	_OnDamage
		OnDeath		_OnDeath
		OnAlert		_OnDamage
	else
		gosub BecomeHostile
	endif

	Exit TRUE

;----------------------------------
:BecomeHostile
;----------------------------------
	hostile_hDOOK_HOSTILITY = NULL

	AddTrigger use, BlockRude

	AddEnemy Player

	gosub BaseInit

	Exit TRUE

;----------------------------------
:_OnDamage
;----------------------------------
	GetParam 0, g_hPlayer
	IsPlayer g_hPlayer, g_bTemp
	if( g_bTemp==TRUE )
		OnDamage DoNothing
		OnDeath  DoNothing
		gosub TurnHostilityOn
	endif

	gosub OnDamage

	Exit TRUE

;----------------------------------
:_OnDeath
;----------------------------------
	GetParam 0, g_hPlayer
	IsPlayer g_hPlayer, g_bTemp
	if( g_bTemp==TRUE )
		OnDamage DoNothing
		OnDeath  DoNothing

		gosub TurnHostilityOn
	endif

	gosub OnDeath

	Exit TRUE

;----------------------------------
:TurnHostilityOn
;----------------------------------
	if( hostile_hDOOK_HOSTILITY!=0 )
		PlaySound "sounds\events\alarmbell.wav", DoNothing, 1, 5000, FALSE, 100
		RemoveObject hostile_hDOOK_HOSTILITY
	endif

	Exit TRUE

;----------------------------------
:BlockRude
;----------------------------------
	Exit TRUE