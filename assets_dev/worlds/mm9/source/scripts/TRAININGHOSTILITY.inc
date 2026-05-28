#include baseMelee.inc
#include range.inc

;-----------------------------------------------------
:InitTrainingHostility
;-----------------------------------------------------
	OnDeath			_OnDeath
	OnDamage		_OnDamage
	OnFoundTarget	_OnFoundTarget
	OnAlert			_OnDamage

	Exit TRUE

;-----------------------------------------------------
:_OnFoundTarget
;-----------------------------------------------------
	gosub _BaseInit
	gosub OnFoundTarget

	Exit TRUE

;-----------------------------------------------------
:_OnDeath
;-----------------------------------------------------
	gosub _BaseInit
	gosub OnDeath

	Exit TRUE

;-----------------------------------------------------
:_OnDamage
;-----------------------------------------------------
	gosub _BaseInit
	gosub OnDamage

	Exit TRUE

;-----------------------------------------------------
:_BaseInit
;-----------------------------------------------------
	GetParam 0, g_hTarget
	SendAlert g_hTarget

	gosub BaseInit
	gosub RangeInit

	gosub SetupTarget
	gosub AggressiveStart

	Exit TRUE
