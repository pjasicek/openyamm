;------------------------------------------
;	botbase.inc
;	Jeff Leggett
;
;	Base functionality for bots...
;
;------------------------------------------


#include botglobals.inc
#include botMove.inc
#include botMission.Inc


;------------------------------------------
:BB_AttackTarget
;
;	Decide what to do, and do it...
;
;		- Find target
;		- If can attack, shoot at him
;		- Decide what mode to go into
;		- 
;
;------------------------------------------

	Set g_hObject, g_hTarget
	GetTarget g_hTarget

	if ( g_hTarget==NULL )
		if ( g_hObject!=NULL )
			BreakPoint
		endif
		Exit FALSE
	endif

	IsAttacking g_bAttacking

	if ( g_bAttacking==TRUE )
		Exit FALSE
	endif

	IsTargetInRange g_bInAttackRange
	CanAttack g_bCanAttack

	if ( g_bInAttackRange==TRUE )
		
	endif

	Exit



;------------------------------------------
:BB_OnDamage
;
;	p0	- hDamager
;------------------------------------------

	GetParam 0, g_hAttacker
	FaceObject g_hAttacker

	Exit

;------------------------------------------
:BB_OnProjectile
;
;	p0 - hProjectile
;	p1 - hLaunchedFrom
;------------------------------------------

	GetParam 0, hProjectile

	if ( g_hTarget==NULL )
		GetParam 1, g_hTarget
		Target g_hTarget, TRUE
		gosub BB_SetupAttack
	endif

;	IsHeadingToward hProjectile, g_hMyObject, bHeadingToward

;	if ( bHeadingToward==TRUE )
;		gosub BE_AvoidProjectile
;	endif

	Exit

;------------------------------------------
:BB_AttackDone
;
;	Return TRUE so we don't go into idle
;	mode...
;------------------------------------------

	Exit TRUE

;------------------------------------------
:BB_AttackTick
;
;
;------------------------------------------

	if ( g_hTarget==NULL )
		gosub BB_ClearTarget
		Exit
	endif

	Attack BB_AttackDone

	Add attackCount, 1

	if ( attackCount < 5 )
		Set attackTime, 0.5
	else
		Set attackTime 0.8
		Set attackCount, 0
	endif

	Wait ATTACK_WAIT, attackTime, BB_AttackTick	

	Exit



;------------------------------------------
:BB_SetupAttack
;------------------------------------------

	gosub BB_AttackTick
	gosub BM_SetupEvade

	Exit

;------------------------------------------
:BB_FoundTarget
;
;	We didn't have a target set, and a target
;	appeared.....
;------------------------------------------

	GetParam 0, g_hTarget
	Target g_hTarget, TRUE

	gosub BB_SetupAttack

	Exit

;------------------------------------------
:BB_LostTarget
;------------------------------------------

	gosub BB_ClearTarget

	Exit TRUE


;------------------------------------------
:BB_CancelAttack
;
; Clear out are target, etc..
;
;------------------------------------------
	
	Wait ATTACK_WAIT, 0, DoNothing

	Exit

;------------------------------------------
:BB_ClearTarget
;
;	No more target, now maybe we want to
;	continue on our current objective/mission
;
;------------------------------------------
	Stop
	Target NULL
	Set g_hTarget, NULL
	gosub BB_CancelAttack
	gosub BM_CancelEvade

	Exit

;------------------------------------------
:BB_TargetDead
;------------------------------------------

	gosub BB_ClearTarget

	Exit

;------------------------------------------
:BB_MaybeSwitchTarget
;
;
;------------------------------------------

	if ( hLastAttacker!=g_hTarget )
		Set g_hTarget, hLastAttacker
		Target g_hTarget, TRUE
		gosub BB_SetupAttack
	endif

	Exit

;------------------------------------------
:BB_OnDamage
;------------------------------------------
	GetParam 0, hLastAttacker

	gosub BB_MaybeSwitchTarget
	

	Exit FALSE

;------------------------------------------
:BotBaseInit
;
;	You must call this in your :main routine...
;
;------------------------------------------

	OnFoundTarget		BB_FoundTarget
	OnLostTarget		BB_LostTarget
	OnTargetDead		BB_TargetDead
	OnDamage			BB_OnDamage

	OnProjectile		BB_OnProjectile, 200


	GetTarget g_hTarget

	GetMyHandle g_hMyObject

	gosub BotMissInit

	;;TraceON

	Exit

