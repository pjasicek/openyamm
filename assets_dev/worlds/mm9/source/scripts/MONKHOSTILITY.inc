;---------------------------------
;	MonkHostility.inc
;	by SJR
;	01-01-02
;	Purpose:if player kills honk,
;			hits honky, or steals,
;			attack mercilessly
;---------------------------------
#include baseMelee.inc
#include range.inc

#hobject	hostile_hMONK_HOSTILITY = 0

;---------------------------------
:InitMonkHostility
;---------------------------------
	AddFriend Player

	GetObjectHandle MONK_HOSTILITY, hostile_hMONK_HOSTILITY
	if( hostile_hMONK_HOSTILITY!=0 )
		CreateObjectLink hostile_hMONK_HOSTILITY
		OnObjectLinkBroken BecomeHostile
		OnDamage	_OnDamage
		OnDeath		_OnDeath
		OnAlert		_OnDamage
	else
		gosub BecomeHostile
	endif

	Exit TRUE

;---------------------------------
:BecomeHostile
;---------------------------------
	hostile_hMONK_HOSTILITY = NULL

	AddTrigger use, BlockRude

	AddEnemy Player

	gosub RangeInit
	gosub BaseInit

	Exit TRUE

;---------------------------------
:_OnDamage
;---------------------------------
	GetParam 0, g_hObject
	IsPlayer g_hObject, g_bTemp
	if( g_bTemp==TRUE )
		OnDamage DoNothing
		OnDeath  DoNothing
		gosub TurnHostilityOn
	endif

	gosub OnDamage

	Exit TRUE

;---------------------------------
:_OnDeath
;---------------------------------
	GetParam 0, g_hObject
	IsPlayer g_hObject, g_bTemp
	if( g_bTemp==TRUE )
		OnDamage DoNothing
		OnDeath  DoNothing
		gosub TurnHostilityOn
	endif

	gosub OnDeath

	Exit TRUE

;---------------------------------
:TurnHostilityOn
;---------------------------------
	if( hostile_hMONK_HOSTILITY!=0 )
		PlaySound "sounds\events\alarmbell.wav", DoNothing, 1, 5000, FALSE, 100
		RemoveObject hostile_hMONK_HOSTILITY
	endif

	Exit TRUE

;----------------------------------
:BlockRude
;----------------------------------
	Exit TRUE