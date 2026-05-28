;-------------------------------------------------------------
;	Range.inc
;	Jeff Leggett
;	10/17/2001
;
;	Type1: (Legends-like)
;		- Prefers MELEE combat. 
;		- Runs after target
;		- Shoots in periodic intervals
;		- Shoots when target out of range
;		- Shoots when cannot reach the target..
;		
;	Type2:
;		- For AI that does not chase after the target
;		- Stays at it's spot and simply shoots at the
;		  target when it has a shot.
;		- After each shot, dodges to hiding place (if there)
;		- When ready to fire again, it peaks back out and
;		  looks for target...
;		- If the target gets within Melee range, it turns into
;		  Type1
;
;
;-------------------------------------------------------------

;;; Note: .SCR file needs to include either basecrawl.inc or
;;;		  basemelee.inc depending on the type of melee system
;;;		  you want to use...
;;; #include basecrawl.inc

#include AIGLOBALS.INC
#include BaseTimers.inc

#number				MAX_RANGE_ATTACK_INTERVAL = 5


#number				RANGE_ATTACK_CHECK_MIN = 1.0
#number				RANGE_ATTACK_CHECK_MAX = 2.5

#number				RANGE_ATTACK1_CHECK_MIN = 0.2
#number				RANGE_ATTACK1_CHECK_MAX = 0.4

#number				MIN_HIDE_TIME = 1

#number				RANGE_TYPE1 = 1
#number				RANGE_TYPE2 = 2
#number				g_rangeAttackType = 1

#number				g_attackChance = 100

#number				g_bMeleeAttack = 0

#number				g_hideDirX
#number				g_hideDirY
#number				g_hideDirZ

#number				g_hideTime

#number				g_startPosX
#number				g_startPosY
#number				g_startPosZ

#number				g_rangeAttackRange = 1000
#number				g_lastRangeAttack = 0

#number				g_nLastHideTime = 0



;-------------------------------------------------------------
:PreRangeAttack
;-------------------------------------------------------------
	GetTime g_nLastAttackTime

	if ( g_rangeAttackType==RANGE_TYPE2 )
		Stop
	else
		gosub GetTimeToTarget
		if ( g_nTimeToTarget < 1 )
			Stop
		endif
	endif

	; Make sure we face our target during the attack anim...
	Target g_hTarget, TRUE

	FaceObject g_hTarget, 360

	Exit

;-------------------------------------------------------------
:DoRangeAttack
;-------------------------------------------------------------

 	GetTime g_nLastAttackTime
	GetTime g_lastRangeAttack

	RangeAttack RangeAttackDone

	exit

;-------------------------------------------------------------
:PostRangeAttack
;	
;	virtual function only..
;
;-------------------------------------------------------------

	exit


;-------------------------------------------------------------
:StartRangeAttack
;-------------------------------------------------------------

	gosub PreRangeAttack
	gosub DoRangeAttack
	gosub PostRangeAttack

	exit


;-------------------------------------------------------------
:CanRangeAttack
;
;	Set's g_bCanAttack to TRUE or FALSE
;
;-------------------------------------------------------------

	if ( g_bResurrecting==TRUE )
		g_bCanAttack = FALSE
		Exit
	Endif

	CanRangeAttack g_bCanAttack

	Exit

;-------------------------------------------------------------
:EstimateRangeAttackHit
;
;	Put value in g_hObject
;
;-------------------------------------------------------------

	EstimateRangeAttackHit g_hObject

	exit

;-------------------------------------------------------------
:CheckRangeTick
;
;	See if we can range attack the target....
;
;-------------------------------------------------------------

	GetRandomFloat RANGE_ATTACK_CHECK_MIN, RANGE_ATTACK_CHECK_MAX, g_nRandom

	Wait ATTACK_CHECK_WAIT, g_nRandom, CheckRangeTick

	if ( g_hTarget==NULL )
		exit
	endif

	gosub CanRangeAttack

	if ( g_bCanAttack==FALSE )
		Exit
	Endif

;
;	Don't range attack if they're within melee attack range...
;
	AIGetDistance g_hTarget, g_nDist1

	if ( g_nDist1 < g_attackRange )
		Exit
	Endif

	if ( g_nDist1 > g_rangeAttackRange )
		Exit
	Endif

	gosub EstimateRangeAttackHit


	g_attackChance	= 0

	if ( g_hObject==NULL )
		g_attackChance = 20
	else
		if ( g_hObject==g_hTarget )
			g_attackChance = 100
		else
			IsClass g_hObject,AIBase,g_bTemp

			if ( g_bTemp==TRUE )
				g_attackChance = 0
			else
				IsWorldObject g_hObject, g_bTemp
				if ( g_bTemp==TRUE )
					g_attackChance = 0
				else
					g_attackChance = 15
				endif
			endif
		endif
	endif

	if ( g_attackChance==0 )
		Exit
	endif

	GetRandomInt 0, 100, g_nRandom

	if ( g_nRandom > g_attackChance )
		; See if we should run away
		gosub CheckForHidingPlace
		exit
	endif

	gosub StartRangeAttack

	Exit

;-------------------------------------------------------------
:CheckRangeAttackStart
;-------------------------------------------------------------

	GetRandomFloat RANGE_ATTACK_CHECK_MIN, RANGE_ATTACK_CHECK_MAX, g_nRandom
	Wait ATTACK_CHECK_WAIT, g_nRandom, CheckRangeTick

	Exit

;-------------------------------------------------------------
:CheckRangeAttackStop
;-------------------------------------------------------------

	Wait ATTACK_CHECK_WAIT, 0, DoNothing

	Exit

;-------------------------------------------------------------
:SetupTarget
;-------------------------------------------------------------

	gosub SetupTarget,1
	gosub CheckRangeAttackStart

	Exit

;-------------------------------------------------------------
:ClearTarget
;-------------------------------------------------------------

	gosub ClearTarget,2
	gosub CheckRangeAttackStop
	
	Exit

;-------------------------------------------------------------
:MeleeAttack
;
;	if we're doing a melee attack, postpone our range attack
;	check...
;
;-------------------------------------------------------------
	gosub CheckRangeAttackStart
	gosub MeleeAttack,1

	g_bMeleeAttack = TRUE

	exit

;--------------------------------------------------------
:BaseRunAway
;--------------------------------------------------------
	
	gosub CheckRangeAttackStop
	gosub BaseRunAway,2

	exit	

;-------------------------------------------------------------
;
;	Type 2-specific code goes here...
;
;-------------------------------------------------------------


;-------------------------------------------------------------
:AggressiveOutOfRange
;
;	in TYPE2 mode, we don't want to run after them....
;
;-------------------------------------------------------------

	if ( g_rangeAttackType!=RANGE_TYPE2 )
		gosub AggressiveOutOfRange,1
		Exit
	endif

	if ( g_bMeleeAttack==TRUE )
		AIGetDistance g_hTarget, g_nDist1

		g_nDist2 = g_attackRange * 3

		if ( g_nDist1 > g_nDist2 )
			g_bMeleeAttack = FALSE
		endif
		if ( g_bMeleeAttack==TRUE )
			gosub AggressiveOutOfRange,1
		endif
	endif

	exit


;-------------------------------------------------------------
:HideDone
;-------------------------------------------------------------

	Stop
;;	SetPos g_hMyObject, g_startPosX, g_startPosY, g_startPosZ

	gosub AggressiveStart
	gosub CheckRangeAttackStart
	gosub CheckRangeTick

	GetTime g_nLastHideTime

	SetStat g_hMyObject,WalkRunMode,WALKRUNMODE_FORWARD


	Exit

;-------------------------------------------------------------
:EndHide
;-------------------------------------------------------------

	GetPos g_hMyObject, g_posX, g_posY, g_posZ
;	g_targetDirX = g_startPosX
;	g_targetDirY = g_posY
;	g_targetDirZ = g_startPosZ
;	VecDist g_posX, g_posY, g_posZ, g_startPosX,g_posY,g_startPosZ, g_nDist1
;	VecSub g_targetDirX,g_targetDirY,g_targetDirZ,g_posX,g_posY,g_posZ
;	VecNorm g_targetDirX,g_targetDirY,g_targetDirZ
;	Strafe g_targetDirX,0,g_targetDirZ, TRUE
;	g_hideTime = g_nDist1 / g_runVel
;	Wait HIDE_WAIT, g_hideTime, HideDone

	SetStat g_hMyObject,WalkRunMode,WALKRUNMODE_TARGET
	WalkToPos g_startPosX, g_posY, g_startPosZ,5,HideDone


	exit

;-------------------------------------------------------------
:AtHidingPlace
;-------------------------------------------------------------
	Stop

	GetStat g_hMyObject,RecoveryTimeLeft,g_nTemp
	
	g_nTemp	= g_nTemp - g_hideTime

	if ( g_nTemp <= 0 )
		g_nTemp = 0.2
	endif	

	GetRandomFloat 0.4, 2.0, g_nRandom

	g_nTemp = g_nTemp + g_nRandom

	Wait HIDE_WAIT, g_nTemp, EndHide

	SetStat g_hMyObject,WalkRunMode,WALKRUNMODE_FORWARD

	exit


;-------------------------------------------------------------
:DoHidingPlace
;-------------------------------------------------------------
	gosub CheckRangeAttackStop
	gosub AggressiveStop

	SetStat g_hMyObject,WalkRunMode,WALKRUNMODE_TARGET
	RunTo g_hHidingPlace,0,AtHidingPlace
  	Exit


;	g_hObject = g_hTarget
;	g_hTarget = g_hHidingPlace
;	gosub BE_GetTargetDir
;	g_hTarget = g_hObject
;
;	g_hideDirX = g_targetDirX
;	g_hideDirY = g_targetDirY
;	g_hideDirZ = g_targetDirZ
;
;	GetPos g_hHidingPlace, g_velX, g_velY, g_velZ
;	GetPos g_hMyObject, g_posX, g_posY, g_posZ
;
;	VecDist g_posX, g_posY, g_posZ, g_velX, g_posY, g_velZ, g_nDist1
;
;	g_hideTime = g_nDist1 / g_runVel
;
;	Strafe g_hideDirX, 0, g_hideDirZ, TRUE
;
;	Wait HIDE_WAIT, g_hideTime, AtHidingPlace
;
	exit

;-------------------------------------------------------------
:CheckForHidingPlace
;
;	JSL--> Unused/Untested feature causing problems...
;		Killed it on 2/18/2002
;
;-------------------------------------------------------------

	g_hHidingPlace	= NULL

; jsl-->2/18/2002
	Exit

	if ( g_rangeAttackType != RANGE_TYPE2 )
		Exit
	Endif

	gosub EstimateRangeAttackHit

	if ( g_hObject==g_hTarget )
		g_nTemp	= 85
	else
		g_nTemp	= 20
	endif

	GetRandomInt 0,100,g_nRandom

	if ( g_nRandom < g_nTemp )
		exit
	Endif

	GetTime g_nTemp
	
	Sub g_nTemp,g_nLastHideTime

	if ( g_nTemp < MIN_HIDE_TIME )
		Exit
	Endif

	FindHidingPlace g_hHidingPlace

	if ( g_hHidingPlace==NULL )
		exit
	endif

	gosub DoHidingPlace

	exit

;-------------------------------------------------------------
:RangeAttackDone
;
;	if Type2, see if we've got a hiding place to go to..
;-------------------------------------------------------------

	gosub AttackTickCancel

	OnTargetBeyondDist 0

	SetStat g_hMyObject,RunVel,g_runVel

	gosub AggressiveStart

	if ( g_rangeAttackType == RANGE_TYPE2 )
		gosub CheckForHidingPlace
	endif

	exit TRUE

;-------------------------------------------------------------
:SetupRangeAttackType
;-------------------------------------------------------------
	if ( g_rangeAttackType==RANGE_TYPE2 )
		RANGE_ATTACK_CHECK_MIN = RANGE_ATTACK1_CHECK_MIN
		RANGE_ATTACK_CHECK_MAX = RANGE_ATTACK1_CHECK_MAX
	endif

	Exit


;--------------------------------------------------------
:ShouldRunAfter
;
;	If it's time to do a range attack, let's not run
;   after them...
;
;--------------------------------------------------------

	AIGetDistance g_hTarget, g_nTargetDist

	if ( g_nTargetDist >= g_rangeAttackRange )
		gosub ShouldRunAfter,1
		Exit
	Endif

	if ( g_lastRangeAttack==0 )
		GetTime g_lastRangeAttack
	endif

	GetTime g_nTemp
	Sub g_nTemp,g_lastRangeAttack

	if ( g_nTemp > MAX_RANGE_ATTACK_INTERVAL )
		CanRangeAttack g_bTemp
		if ( g_bTemp==TRUE )
			gosub EstimateRangeAttackHit
			if ( g_hObject==g_hTarget )
				g_bTemp = FALSE
				;cprint Not Running after target, it's time to range attack!!
				Exit
			endif
		Endif
	Endif

	gosub ShouldRunAfter,1

	Exit

;-------------------------------------------------------------
:RangeInit
;-------------------------------------------------------------

	GetMyHandle g_hMyObject

	GetStat g_hMyObject,RangeAttackType,g_rangeAttackType
	GetStat g_hMyObject,RangeAttackRange,g_rangeAttackRange

	gosub SetupRangeAttackType

	GetPos g_hMyObject,g_startPosX,g_startPosY,g_startPosZ

	Exit

