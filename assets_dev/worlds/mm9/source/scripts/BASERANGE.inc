;------------------------------------------
; BaseRange.inc
;
;	Default range attack implementation for
;	base monsters.... (that have a range attack)
;
;------------------------------------------

#include Base.Inc

#number				TARGET_HIT_WAIT_TIME = 4
#number				GO_AFTER_MIN_WAIT_TIME = 2


#number				lastAttackTime = 0
#number				lastTargetHit = 0

#numberArray		hTargetArray[16]


;------------------------------------------
:BaseRangeGoGetHim
;------------------------------------------

	GetTime g_nTemp
	lastAttackTime = 0

	CanReachTarget g_bTemp

	if ( g_bTemp==FALSE )
		Exit TRUE
	endif

	; Re-start the attack check clock so that we get some time to move a little...
	Wait ATTACK_CHECK_WAIT, GO_AFTER_MIN_WAIT_TIME, BaseRangeAttackCheck

	gosub BaseGoGetHim

	Exit

;------------------------------------------
:BaseRangeAttackDone
;
; If we haven't hit the target for a while,
; maybe try moving....
;
;------------------------------------------

	if ( g_hTarget==NULL )
		exit FALSE
	endif

	if ( lastAttackTime!=0 )
		GetTime g_nTemp
		Sub g_nTemp, TARGET_HIT_WAIT_TIME
		if ( g_nTemp > lastAttackTime )
			if ( g_nTemp > lastTargetHit )
				lastAttackTime = 0
				lastTargetHit = 0
				; Move after him....
				gosub BaseRangeGoGetHim
				Exit TRUE
			endif
		endif
	endif

	Exit FALSE

;------------------------------------------
:BaseDoRangeAttack
;
;	Launch our range attack!
;
;------------------------------------------

	g_bFighting = TRUE
	
	if ( lastAttackTime==0 )
		GetTime lastAttackTime
	endif

	RangeAttack BaseRangeAttackDone

	exit TRUE

;------------------------------------------
:BaseRotationDoneRangeAttack
;------------------------------------------
	
	gosub BaseDoRangeAttack

	exit TRUE

;------------------------------------------
:BaseRangeMaybeAttack
;
;	If we can range attack, we randomly 
;	decide to do so here...
;------------------------------------------

	CanAttack g_bCanAttack

	if ( g_bCanAttack==FALSE )
		exit FALSE
	endif

	g_nTemp = 0
	EstimateRangeAttackHit g_hObject
	if ( g_hObject==NULL )
		Add g_nTemp, 20
	else
		if ( g_hObject==g_hTarget )
			g_nTemp = 100
		else
			IsClass g_hObject,AIBase, g_bTemp
			if ( g_bTemp==TRUE )
				g_nTemp = 0
			endif
		endif
	endif

	if ( g_hObject!=g_hTarget )
		Exit TRUE
	endif

	GetRandomInt 0, 100, g_nRandom
	if ( g_nRandom <= g_nTemp )
		gosub BaseDoRangeAttack
	endif


	exit TRUE


;------------------------------------------
:BaseRangeAwareDone
;------------------------------------------

	gosub ChaseTargetTick


	Exit

;------------------------------------------
:BaseRangeFoundPlayer
;
;------------------------------------------

	GetParam 0, g_hTarget

	if ( g_hTarget==0 )
;		This shouldn't happen, but you can't be too careful!
		Exit FALSE
	Endif

	Target g_hTarget, false

	GetRandomInt 0, 100, g_nRandom

	Target g_hTarget, FALSE
	Aware BaseRangeAwareDone

	exit TRUE


;------------------------------------------
:BaseRangeOnProjectile
;	p0	- hProjectile
;	p1	- hLaunchedFrom
;	p2	- dist
;------------------------------------------
	GetParam 0, g_hObject
	GetParam 1, g_nTemp

	if ( g_hObject==g_nTemp )
	;
	; Don't take these seriously...
	;
		Exit
	endif

	if ( g_hAttacker!=NULL )
		BreakObjectLink g_hAttacker
	endif
	
	GetParam 1, g_hAttacker

	gosub BaseSetupAttacker
	gosub IsAttackerValidTarget

	if ( g_bTemp==FALSE )
		Exit
	endif

	; You're my new best friend!
	g_hTarget = g_hAttacker
	Target g_hTarget

	Exit


;------------------------------------------
:BaseRangeAttackCheck
;
;	If we have a target, see if it's time
;	to try to attack him....
;	If he's within hand attack range,
;	do that, otherwise shoot him!
;
;------------------------------------------

	if ( g_hTarget==NULL )
		goto BaseRangeAttackCheckDone
	endif

	gosub BaseRangeMaybeAttack

:BaseRangeAttackCheckDone
	GetRandomFloat 1.3, 2.0, g_nRandom
	Wait ATTACK_CHECK_WAIT, g_nRandom, BaseRangeAttackCheck

	Exit

;------------------------------------------
:ChaseTargetTick
;
;	Decide if we need to try to go after
;	the target...
;
;------------------------------------------

; If we have a clear shot, don't bother moving
; otherwize, randomly decide if we should go
; find him...

	if ( g_hTarget==NULL )
		goto ChaseTargetTickDone
	endif

	AIGetDistance g_hTarget, g_nDist1

	GetStat g_hMyObject, RangeAttackRange, g_nTemp

	if ( g_nDist1 > g_nTemp )
		gosub BaseRangeGoGetHim
		goto ChaseTargetTickDone
	endif

	EstimateRangeAttackHit g_hObject

	g_bTemp = 0

	if ( g_hObject!=NULL )
		if ( g_hObject!=g_hTarget )
			; Go after them
			gosub BaseRangeGoGetHim
			goto ChaseTargetTickDone
		endif
	endif

:ChaseTargetTickDone
	Wait CHASE_TARGET_WAIT, 1.0, ChaseTargetTick

	Exit

;------------------------------------------
:ChangeTargetWait
;------------------------------------------

	if ( g_hTarget==NULL )
		goto ChangeTargetWaitDone
	endif

	GetPos g_hMyObject, g_posX, g_posY, g_posZ
	AIGetDistance g_hTarget, g_nDist1

	FindTargets hTargetArray,16,g_nTemp,g_nDist1,0

	if ( g_nTemp==0 )
		goto ChangeTargetWaitDone
	endif

	ArrayGet hTargetArray, 0, g_hObject

	if ( g_hObject==g_hTarget )
		if ( g_nTemp==1 )
			goto ChangeTargetWaitDone
		endif
		ArrayGet hTargetArray, 1, g_hObject
	endif

	g_hTarget = g_hObject
	Target g_hTarget

:ChangeTargetWaitDone

	Wait CHANGE_TARGET_WAIT, 1.5, ChangeTargetWait

	Exit

;------------------------------------------
:BaseRangeTargetHit
;
;	p0 = hTarget
;	p1 = damageAmt
;------------------------------------------

	GetParam 0, g_hObject
	if ( g_hObject!=g_hTarget )
		Exit
	endif

	GetTime lastTargetHit

	exit

;------------------------------------------
:BaseRangeInit
;
;	Be sure to call this in your Main!
;
;------------------------------------------

	gosub InitBase

	OnFoundPlayer BaseRangeFoundPlayer
	OnProjectile	BaseRangeOnProjectile, 200
	OnTargetHit		BaseRangeTargetHit

	Wait ATTACK_CHECK_WAIT,  1.5, BaseRangeAttackCheck

;
;	Note, we're replacing the base.inc chase target wait with 
;	our own...
;
	Wait CHANGE_TARGET_WAIT, 3.0, ChangeTargetWait

	
	Exit
