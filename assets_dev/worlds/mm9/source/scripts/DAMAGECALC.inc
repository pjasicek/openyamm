#include TestingStuff.inc

#number		nCurDamage = 0
#number		nAttackMin = 0
#number		nAttackMax = 0
#string		RANGE = "Attack range: "
#string		DASH = " - "
#string		RANGE_OUTPUT = ""
#string		DMG = "Damage inflicted: "
#string		DMG_OUTPUT = ""

;----------------------------
:InitDamageCalc
;----------------------------
	OnDamage OnDamage
	AddTrigger use, OnUse
	Exit 1

;----------------------------
:OnDamage
;----------------------------
	GetParam 1, nCurDamage
	cprint *************************
	gosub DisplayAttackRange
	gosub DisplayDamageValue
	Exit 1

;----------------------------
:OnUse
;----------------------------
	Exit 1

;----------------------------
:DisplayAttackRange
;----------------------------
	RANGE_OUTPUT = RANGE + nAttackMin + DASH + nAttackMax
	cprint RANGE_OUTPUT
	Exit 1

;----------------------------
:DisplayDamageValue
;----------------------------
	DMG_OUTPUT = DMG + nCurDamage
	cprint DMG_OUTPUT
	Exit 1
