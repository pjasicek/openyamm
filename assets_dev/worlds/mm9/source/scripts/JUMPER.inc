;----------------------------------------------------------
;	Jumper.Inc
;	Jeff Leggett
;	01/08/2002
;	
;	Base script used by AI that jump off cliffs at the 
;	player...	
;
;----------------------------------------------------------

#include AIGlobals.inc
#include Flags.inc

#number		minWait = 1
#number		maxWait = 2.5

#hobject	hPlayer

#number		startX
#number		startY
#number		startZ

#number		faceX
#number		faceY
#number		faceZ

#string		sRubbleSound=Sounds\Events\rubble.wav


;----------------------------------------------------------
:RunNormalScript
;----------------------------------------------------------
	GetStatStr g_hMyObject,ScriptName,g_sTemp
	SetStat g_hMyObject,GroundTouchNotify,FALSE
	RunScript g_sTemp
	Exit

;----------------------------------------------------------
:JumpLandHack
;	prevent the bounce?
;----------------------------------------------------------
	SetVelocity g_hMyObject,0,0,0

	gosub RunNormalScript	

	exit

;----------------------------------------------------------
:JumperHitGround
;----------------------------------------------------------
	OnTouchNotify
	Stop
	SetIdle
	SetPushBack g_dirX,0,g_dirZ,0
	SetVelocity g_hMyObject,0,0,0
	Wait 22,0.01,JumpLandHack

	Exit

;----------------------------------------------------------
:SetupTouchNotify
;----------------------------------------------------------
	
	SetFlag g_hMyObject,FLAG_SOLID
	ClearFlag g_hMyObject,FLAG_GOTHRUWORLD

	SetStat g_hMyObject,GroundTouchNotify,TRUE
	OnTouchNotify JumperHitGround

	Exit

;----------------------------------------------------------
:JumpAtTarget
;----------------------------------------------------------

	Target g_hTarget, TRUE

	SetStat g_hMyObject,Gravity,TRUE

	PlayAnimSound JumpingDown,0
	LoopAnim JumpingDown,0

	GetPos g_hTarget,g_dirX,g_dirY,g_dirZ
	GetPos g_hMyObject,g_posX,g_posY,g_posZ

	VecSub g_dirX,g_dirY,g_dirZ,g_posX,g_posY,g_posZ
	g_dirY = 0
	VecNorm g_dirX,g_dirY,g_dirZ

	GetFaceDir g_hMyObject,faceX,faceY,faceZ

	faceY = 0

	VecAngle g_dirX,g_dirY,g_dirZ,faceX,faceY,faceZ,g_nTemp

	if ( g_nTemp < 0 )
		g_nTemp = g_nTemp * -1
	endif

	; if angle is too far, just jump in forward direction...
	if ( g_nTemp > 45 )
		g_dirX		= faceX
		g_dirZ		= faceZ
	endif

	SetVelocity g_hMyObject,0,100,0

	VecScale g_dirX,g_dirY,g_dirZ,250

	SetPushBack g_dirX,g_dirY,g_dirZ,2

	Wait 28,0.2,SetupTouchNotify



	Exit


;----------------------------------------------------------
:ReadyToJump
;----------------------------------------------------------
	Wait 23, 1, JumpAtTarget
;;	gosub JumpAtTarget
	exit

;----------------------------------------------------------

;----------------------------------------------------------
:JumperGetPlayer
;	
;----------------------------------------------------------

; Cancel our wait... (just in case)
	Wait 9, 0, DoNothing

	GetPlayerHandle g_hTarget

	SetFlag g_hMyObject,FLAG_VISIBLE

	LoopAnim LyingDown,0

	GetFaceDir g_hMyObject,g_dirX,g_dirY,g_dirZ

	VecScale g_dirX,g_dirY,g_dirZ,60

	VecAdd g_dirX,g_dirY,g_dirZ,startX,startY,startZ
	MoveToPos g_dirX,g_dirY,g_dirZ,50,ReadyToJump

	PlaySound Sounds\Events\rubble.wav,DoNothing,1000,2000

	RemoveTrigger BuddyDead

	Exit


;----------------------------------------------------------
:ResetJumper
;----------------------------------------------------------
	SetStat g_hMyObject,Gravity,FALSE
	ClearFlag g_hMyObject,FLAG_SOLID
	ClearFlag g_hMyObject,FLAG_VISIBLE
	SetFlag g_hMyObject,FLAG_GOTHRUWORLD

;	if ( sMyName==Jumper0 )
;		startX		= -1700
;		startY		= 1646
;		startZ		= -151
;	endif

;	if ( sMyName==Jumper1 )
;		startX		= -583
;		startY		= 1760
;		startZ		= -29
;	endif

	SetPos g_hMyObject,startX,startY,startZ
	LoopAnim LyingDown,0

	exit


;----------------------------------------------------------
:JumperWaitGetPlayer
;----------------------------------------------------------

	GetRandomFloat minWait,maxWait,g_nRandom

	Wait 9, g_nRandom, JumperGetPlayer

	Exit

;----------------------------------------------------------
:JumperSetupPos
;----------------------------------------------------------

	GetPos g_hMyObject,startX,startY,startZ

	Exit

;----------------------------------------------------------
:SetupJumper
;----------------------------------------------------------
	GetMyHandle g_hMyObject


	SetStat g_hMyObject,Gravity,FALSE
	ClearFlag g_hMyObject,FLAG_SOLID
	ClearFlag g_hMyObject,FLAG_VISIBLE
	SetFlag g_hMyObject,FLAG_GOTHRUWORLD

	Wait 29,0.1,ResetJumper
	Wait 28,0.1,JumperSetupPos

	AddTrigger Reset,ResetJumper
	AddTrigger Jump,JumperGetPlayer
	AddTrigger GetPlayer,JumperGetPlayer
	AddTrigger BuddyDead,JumperGetPlayer
	AddTrigger WaitGetPlayer,JumperWaitGetPlayer

	CacheSound sRubbleSound

	Exit
