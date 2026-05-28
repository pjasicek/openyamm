;-------------------------------
;	HonkHostility.inc
;	by SJR
;	01-10-02
;	Purpose:if player kills honk,
;			hits honky, or steals,
;			attack mercilessly
;-------------------------------
#include baseMelee.inc
#include Range.inc

#hobject	hostile_hHONK_FRIENDLY = 0

;-------------------------------
:InitHonkHostility
;-------------------------------
	AddFriend Player

	GetObjectHandle HONK_FRIENDLY, hostile_hHONK_FRIENDLY
	if( hostile_hHONK_FRIENDLY!=0 )
		CreateObjectLink hostile_hHONK_FRIENDLY
		OnObjectLinkBroken BecomeHostile
		OnDamage	_OnDamage
		OnDeath		_OnDeath
		OnAlert		_OnDamage
	else
		gosub BecomeHostile
	endif

	Exit TRUE

;-------------------------------
:BecomeHostile
;-------------------------------
	hostile_hHONK_FRIENDLY = NULL

	AddTrigger use, BlockRude

	AddEnemy Player

	gosub BaseInit
	gosub RangeInit

	Exit TRUE

;-------------------------------
:_OnDamage
;-------------------------------
	GetParam 0, g_hObject
	IsPlayer g_hObject, g_bTemp
	if( g_bTemp==TRUE )
		OnDamage DoNothing
		OnDeath  DoNothing
		gosub TurnHostilityOn
	endif

	gosub OnDamage

	Exit TRUE

;-------------------------------
:_OnDeath
;-------------------------------
	GetParam 0, g_hObject
	IsPlayer g_hObject, g_bTemp
	if( g_bTemp==TRUE )
		OnDamage DoNothing
		OnDeath  DoNothing
		gosub TurnHostilityOn
	endif

	gosub OnDeath

	Exit TRUE

;-------------------------------
:TurnHostilityOn
;-------------------------------
	if( hostile_hHONK_FRIENDLY!=0 )
		PlaySound "sounds\ambient\birds\honkers.wav", DoNothing, 1, 5000, FALSE, 100
		RemoveObject hostile_hHONK_FRIENDLY
	endif

	Exit TRUE

;----------------------------------
:BlockRude
;----------------------------------
	Exit TRUE