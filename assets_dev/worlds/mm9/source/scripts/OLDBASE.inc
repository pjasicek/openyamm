;------------------------------------------
; base.inc
;
;
;	This include file contains base monster
;	handling.  Basically, the monster sees
;	the player.  Runs after him and keeps
;	attacking.  Nothing fancy here.
;	
;	NOTE: Be sure to gosub InitBase in your
;	:main routine.
;------------------------------------------


#include aiglobals.inc


#number				g_nDist1
#number				g_nDist2

#number				g_bChasing=0
#number				g_bRunning=0

;------------------------------------------
:BaseChaseTick
;------------------------------------------
	
	if ( g_bChasing==FALSE )
		Exit
	endif

	if ( g_hTarget==NULL )
		Exit
	endif

	GetDistance g_hTarget, g_nDist1

	if ( g_bRunning==TRUE )
		if ( g_nDist1 < 120.0 )
			Set g_sOut, g_nDist1
			DebugOut g_sOut
			; Time to Walk!
			Set g_bRunning, FALSE
			WalkTo g_hTarget
		endif
	else
		if ( g_nDist1 > 200.0 )
			Set g_sOut, g_nDist1
			Set g_bRunning, TRUE
			RunTo g_hTarget
		endif
	endif

	Wait 0.1, BaseChaseTick

	Exit

;------------------------------------------
:BaseGoGetHim
;------------------------------------------
	Target g_hTarget

	;	 
	;	Run after him. Don't need a callback because
	;	we have OnAttackReady call BaseAttackReady
	;	when we are close enough...
	;

	Set g_bRunning, TRUE
	Set g_bChasing, TRUE
	RunTo g_hTarget

	Wait 0.1, BaseChaseTick

	Exit 1

;------------------------------------------
:BaseRotationDone
;------------------------------------------
	Target g_hTarget
	PlayAnimation Threat, FALSE, BaseGoGetHim

	Exit
;------------------------------------------
:BaseFoundPlayer
;
;	Found a player, set it as our current
;	target and run after him!
;------------------------------------------

	if ( g_hTarget!=0 )
		Exit
	Endif

	GetPlayerHandle g_hTarget
	
	if g_hTarget == 0
;
;		This shouldn't happen, but you can't be too careful!
;
		Exit
	Endif

	Set g_bInAttackRange, 0

	; Turn and face target before running after him!
	FaceObject g_hTarget, 360, BaseRotationDone

	Exit

;------------------------------------------
:BaseAttackReady
;
;	We are now in attack range (for our
;	currently selected weapon) and ready
;	to attack.  So let's do it!
;------------------------------------------

	Set g_bChasing, FALSE
;
; No callback is necessary here, AttackReady
; will get called when our attack is done
; If the player goes out of range while
; we were attacking, BaseTargetOutOfRange
; will get called...
;
	Set g_bInAttackRange, 1

	Attack

	Exit

;------------------------------------------
:BaseTargetOutOfRange
;
;	Target moved out of our weapon range.
;	Go after him!
;	
;------------------------------------------

	DebugOut Base Target Out Of Range

	Set g_bInAttackRange, 0

	gosub BaseGoGetHim

	Exit

;------------------------------------------
:BaseLostTarget
;
;	We've lost the target, so let's go idle.
;------------------------------------------

	Set g_hTarget, 0
	SetIdle

	Exit

;------------------------------------------
:BaseStuckDone
;
;	This is called when a stuck animation
;	has finished... We'll just re-attempt
;	to run after our target...
;------------------------------------------
	
	if ( g_hTarget!=0 )
		gosub BaseGoGetHim
	endif

	Exit

;------------------------------------------
:BaseDamageDone
;
;	We were attacked, now we want to run
;	after whoever attacked us!
;	
;------------------------------------------

	if ( g_hTarget==0 )
		Set g_hTarget, g_hAttacker
	else
		if ( g_hAttacker!=0 )
		if ( g_hAttacker!=g_hTarget )
			; 70% chance we'll switch to the damager
			Set g_nTemp, 70
			if ( g_bInAttackRange==1 )
				; we're already in attack range of our current target
				; so lower chances of switching
				Set g_nTemp, 10
			endif

			GetDistance g_hTarget, g_nDist1
			GetDistance g_hAttacker, g_nDist2

			if ( g_nDist2 > g_nDist1 )
				; reduce odds even further...
				Divide g_nTemp, 2
			endif

			GetRandomInt 0, 100, g_nRandom
			if ( g_nRandom < g_nTemp )
				; 
				; Okay, we decided to switch our current target to the 
				; attacker!
				;
				Set g_hTarget, g_hAttacker
			endif
		endif
		endif
	endif

	if ( g_hTarget==0 )
		Exit 0		; 0 means have the AI do it's default handling of this event.
	endif

	; Go after the Target...

	gosub BaseGoGetHim

	Exit

;------------------------------------------
:BaseDamage
;
;	p1 = hAttacker
;	p2 = HitPoints
;
;------------------------------------------

	GetParam 0, g_hAttacker

	Exit FALSE

;------------------------------------------
:InitBase
;
;	Main intialization code.
;
;	This should be called by the actual
;	script file..
;------------------------------------------

	;;TraceOn
	GetMyHandle g_hMyObject

;
; Setup our event handlers...
;
	OnFoundPlayer				BaseFoundPlayer
	OnLostTarget				BaseLostTarget
	OnTargetOutOfRange			BaseTargetOutOfRange
	OnAttackReady				BaseAttackReady
	OnStuckDone					BaseStuckDone
	OnDamageDone				BaseDamageDone
	OnDamage					BaseDamage

	Exit
