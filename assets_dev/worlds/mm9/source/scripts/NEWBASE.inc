;--------------------------------------------------------
;	NewBase.inc
;	Jeff Leggett
;	10/03/2001
;
;	New and improved base script.  
;
;	Cleaner
;	More modular
;	Makes more use of function overloading...
;
;	Additions to basecrawl.inc:
;		strafe attacks
;		evasive maneuvers
;	
;
;--------------------------------------------------------

#include basecrawl.inc
#include baseevade.inc

#number				g_nStrafeAttackPct = 80

#number				g_bCanBlendAnim = 1
#number				g_bCanHeadTurn = 1
#number				g_nEvadeChance = 100
#number				g_nMaxEvadeDist = 500


;--------------------------------------------------------
:TargetMoving
;--------------------------------------------------------

	gosub TargetMoving,1

	Exit

;--------------------------------------------------------
:TargetStill
;
;	if we're not strafing, just call parent which will
;	stop us.
;
;	If we are strafing, don't call parent so that we
;	will continue to strafe...
;
;--------------------------------------------------------

	if ( g_bStrafeAttack==FALSE )
		gosub TargetStill,1
	endif

	Exit

;--------------------------------------------------------
:AttackObstacle
;
;	p0 - hObstacle
;
;
;	if the obstacle is our target, then if they're not
;	moving we'll want to stop...  If not, then just
;	ignore the obstacle and our speed throttling will 
;	take over for us... (ie: exit TRUE)
;
;--------------------------------------------------------

	GetParam 0, g_hObject

	if ( g_hObject==g_hTarget )
		gosub IsTargetMoving

		if ( g_bTemp==FALSE )
			Stop
			exit TRUE
		endif

		exit TRUE

	endif
	
	exit FALSE


;--------------------------------------------------------
:PostAttack
;
;	overloaded to potentially do a strafe attack...
;
;--------------------------------------------------------

	g_bStrafeAttack = FALSE

	gosub PostAttack, 1
	gosub IsTargetMoving

	if ( g_bTemp==FALSE )

		GetRandomInt 0, 100, g_nRandom

		if ( g_nRandom < g_nStrafeAttackPct )
			g_bPickDir = TRUE
			gosub BE_AttackStrafe
			g_bPickDir = TRUE
			g_bStrafeAttack = TRUE
		Endif
	endif

	exit

;------------------------------------------
:ShouldEvade
;
;	Returns TRUE or FALSE in g_bTemp
;------------------------------------------

	GetRandomInt 0,100,g_nRandom

	GetStat g_hMyObject, EvadeChance, g_nEvadeChance

	if ( g_nRandom < g_nEvadeChance )
		g_bTemp = TRUE
	else
		g_bTemp = FALSE
	Endif

	Exit

;--------------------------------------------------------
:CancelEvade
;--------------------------------------------------------

	gosub BaseEvadeStop
	gosub AggressiveStart

	Exit

;--------------------------------------------------------
:DoEvade
;
;	Backup and/or strafe a little...
;
;--------------------------------------------------------

	GetStat g_hMyObject,RecoveryTime,g_nEvadeTime
	gosub SpeedThrottleStop
	gosub AggressiveStop
	OnTargetBeyondDist g_nMaxEvadeDist, CancelEvade

	gosub BaseEvadeStart

;;;;		Mul g_nTemp, 0.8

	g_nTemp = g_nEvadeTime
	g_nTemp	= 2
	if ( g_nTemp < 1 )
		g_nTemp = 1
	Endif


	Wait AGGRESSIVE_WAIT, g_nTemp, CancelEvade

	Exit

;--------------------------------------------------------
:BackpedalTauntDone
;--------------------------------------------------------

	gosub AttackDone,1
	Exit

;--------------------------------------------------------
:AttackBackpedalDone
;--------------------------------------------------------
	gosub BaseEvadeStop
	Taunt BackpedalTauntDone

	Exit

;--------------------------------------------------------
:AttackDone
;
;	overloaded to potentially back/strafe away from target
;
;--------------------------------------------------------
	
	gosub ShouldEvade

	if ( g_bTemp==FALSE	)
		g_bEvading	= FALSE
;
;		if we did a strafe attack, but we don't want to
;		evade, then, just backoff...
;
		if ( g_bStrafeAttack==TRUE )
			gosub BE_BackPedal
			Wait AGGRESSIVE_WAIT, 0.3, AttackBackpedalDone
			Exit
		endif

		gosub AttackDone,1
	else
		gosub AttackTickCancel
		gosub DoEvade
	endif

	exit

;--------------------------------------------------------
:BE_AttackStrafeObstacle
;
;	if we have an obstacle and decide to backup,
;	go ahead and cancel speed throttle...
;
;--------------------------------------------------------

	gosub BE_AttackStrafeObstacle, 1

	if ( g_bTemp==TRUE )
		gosub SpeedThrottleStop
	endif

	Exit


;--------------------------------------------------------
:BaseInit
;--------------------------------------------------------

	gosub BaseCrawlInit

	GetStat g_hMyObject, StrafeAttackPct, g_nStrafeAttackPct
	GetStat g_hMyObject, CanBlendAnim, g_bCanBlendAnim
	GetStat g_hMyObject, CanHeadTurn, g_bCanHeadTurn
	
	Exit

