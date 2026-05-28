;----------------------------
;	LichSceneTransition.inc
;	by SJR
;	Purpose:remove the creatures
;			already there and
;			restore them later.
;----------------------------
#include BaseGlobals.inc
#include flags.inc

#hobject	hCreature = 0

;----------------------------
:RemoveCreatures
;----------------------------
	GetObjectHandle LichKing1, hCreature
	SetStat hCreature, gravity, FALSE
	ClearFlag hCreature, FLAG_SOLID
	ClearFlag hCreature, FLAG_VISIBLE

	GetObjectHandle LichKing2, hCreature
	SetStat hCreature, gravity, FALSE
	ClearFlag hCreature, FLAG_SOLID
	ClearFlag hCreature, FLAG_VISIBLE

	GetObjectHandle LichKing3, hCreature
	SetStat hCreature, gravity, FALSE
	ClearFlag hCreature, FLAG_SOLID
	ClearFlag hCreature, FLAG_VISIBLE

	GetObjectHandle Oculus0, hCreature
	SetStat hCreature, gravity, FALSE
	ClearFlag hCreature, FLAG_SOLID
	ClearFlag hCreature, FLAG_VISIBLE

	GetObjectHandle Oculus1, hCreature
	SetStat hCreature, gravity, FALSE
	ClearFlag hCreature, FLAG_SOLID
	ClearFlag hCreature, FLAG_VISIBLE

	GetObjectHandle Oculus2, hCreature
	SetStat hCreature, gravity, FALSE
	ClearFlag hCreature, FLAG_SOLID
	ClearFlag hCreature, FLAG_VISIBLE

	GetObjectHandle Oculus3, hCreature
	SetStat hCreature, gravity, FALSE
	ClearFlag hCreature, FLAG_SOLID
	ClearFlag hCreature, FLAG_VISIBLE

	GetObjectHandle Oculus4, hCreature
	SetStat hCreature, gravity, FALSE
	ClearFlag hCreature, FLAG_SOLID
	ClearFlag hCreature, FLAG_VISIBLE

	GetObjectHandle SkeletonMaster0, hCreature
	SetStat hCreature, gravity, FALSE
	ClearFlag hCreature, FLAG_SOLID
	ClearFlag hCreature, FLAG_VISIBLE

	GetObjectHandle SkeletonMaster1, hCreature
	SetStat hCreature, gravity, FALSE
	ClearFlag hCreature, FLAG_SOLID
	ClearFlag hCreature, FLAG_VISIBLE

	GetObjectHandle SkeletonMaster4, hCreature
	SetStat hCreature, gravity, FALSE
	ClearFlag hCreature, FLAG_SOLID
	ClearFlag hCreature, FLAG_VISIBLE

	GetObjectHandle SkeletonMaster5, hCreature
	SetStat hCreature, gravity, FALSE
	ClearFlag hCreature, FLAG_SOLID
	ClearFlag hCreature, FLAG_VISIBLE

	GetObjectHandle SkeletonMaster6, hCreature
	SetStat hCreature, gravity, FALSE
	ClearFlag hCreature, FLAG_SOLID
	ClearFlag hCreature, FLAG_VISIBLE

	Exit TRUE

;----------------------------
:ReplaceCreatures
;----------------------------
	GetObjectHandle LichKing1, hCreature
	SetStat hCreature, gravity, TRUE
	SetFlag hCreature, FLAG_SOLID
	SetFlag hCreature, FLAG_VISIBLE

	GetObjectHandle LichKing2, hCreature
	SetStat hCreature, gravity, TRUE
	SetFlag hCreature, FLAG_SOLID
	SetFlag hCreature, FLAG_VISIBLE

	GetObjectHandle LichKing3, hCreature
	SetStat hCreature, gravity, TRUE
	SetFlag hCreature, FLAG_SOLID
	SetFlag hCreature, FLAG_VISIBLE

	GetObjectHandle Oculus0, hCreature
	SetStat hCreature, gravity, TRUE
	SetFlag hCreature, FLAG_SOLID
	SetFlag hCreature, FLAG_VISIBLE

	GetObjectHandle Oculus1, hCreature
	SetStat hCreature, gravity, TRUE
	SetFlag hCreature, FLAG_SOLID
	SetFlag hCreature, FLAG_VISIBLE

	GetObjectHandle Oculus2, hCreature
	SetStat hCreature, gravity, TRUE
	SetFlag hCreature, FLAG_SOLID
	SetFlag hCreature, FLAG_VISIBLE

	GetObjectHandle Oculus3, hCreature
	SetStat hCreature, gravity, TRUE
	SetFlag hCreature, FLAG_SOLID
	SetFlag hCreature, FLAG_VISIBLE

	GetObjectHandle Oculus4, hCreature
	SetStat hCreature, gravity, TRUE
	SetFlag hCreature, FLAG_SOLID
	SetFlag hCreature, FLAG_VISIBLE

	GetObjectHandle SkeletonMaster0, hCreature
	SetStat hCreature, gravity, TRUE
	SetFlag hCreature, FLAG_SOLID
	SetFlag hCreature, FLAG_VISIBLE

	GetObjectHandle SkeletonMaster1, hCreature
	SetStat hCreature, gravity, TRUE
	SetFlag hCreature, FLAG_SOLID
	SetFlag hCreature, FLAG_VISIBLE

	GetObjectHandle SkeletonMaster4, hCreature
	SetStat hCreature, gravity, TRUE
	SetFlag hCreature, FLAG_SOLID
	SetFlag hCreature, FLAG_VISIBLE

	GetObjectHandle SkeletonMaster5, hCreature
	SetStat hCreature, gravity, TRUE
	SetFlag hCreature, FLAG_SOLID
	SetFlag hCreature, FLAG_VISIBLE

	GetObjectHandle SkeletonMaster6, hCreature
	SetStat hCreature, gravity, TRUE
	SetFlag hCreature, FLAG_SOLID
	SetFlag hCreature, FLAG_VISIBLE

	Exit TRUE

;----------------------------
:RemoveActors
;----------------------------
	GetObjectHandle LichSorcerer, hCreature
	if( hCreature!=0 )
		RemoveObject hCreature
	endif

	GetObjectHandle LichSorcererNew, hCreature
	RemoveObject hCreature

	GetObjectHandle EscortLich0, hCreature
	RemoveObject hCreature

	GetObjectHandle EscortLich1, hCreature
	RemoveObject hCreature

	GetObjectHandle EscortLich2, hCreature
	RemoveObject hCreature

	GetObjectHandle EscortLich3, hCreature
	RemoveObject hCreature

	GetObjectHandle KiddieSacrifice0, hCreature
	RemoveObject hCreature

	GetObjectHandle KiddieSacrifice1, hCreature
	RemoveObject hCreature

	GetObjectHandle KiddieSacrifice2, hCreature
	RemoveObject hCreature

	GetObjectHandle KiddieSacrifice3, hCreature
	RemoveObject hCreature

	GetObjectHandle KiddieSacrifice4, hCreature
	RemoveObject hCreature

	GetObjectHandle KiddieSacrifice5, hCreature
	RemoveObject hCreature

	GetObjectHandle KiddieSacrifice6, hCreature
	RemoveObject hCreature

	GetObjectHandle KiddieSacrifice7, hCreature
	RemoveObject hCreature

	Exit TRUE