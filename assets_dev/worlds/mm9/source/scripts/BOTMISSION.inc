;--------------------------------------------------------------
;	BotMission.Scr
;
;		Bot mission thinking....  Bot AI concerning fullfilling
;	mission objectives goes here...
;
;	
;--------------------------------------------------------------


#include botGlobals.inc

#number	GT_RESCUE_PRINCESS		= 1

; What is the mission of this Map?
#number	g_mission				= 1

#number	MS_NONE					= 0
#number MS_FINDING_PRINCESS		= 1
#number MS_HAVE_PRINCESS		= 2
#number MS_FOLLOWING_FRIEND		= 3

; What are we currently doing?
#number g_missionStatus			= 0


; Do we have the princess?
#number	g_bHavePrincess			= 0

#hobject g_hPrincess			= 0

#hobject g_hRescueZone			= 0

;--------------------------------------------------------------
:BotMissPause
;
;	Pause our mission thinking (we're probably dealing with 
;	an enemy...)
;
;--------------------------------------------------------------

	WAIT MISSION_WAIT, 0, DoNothing

	Exit

;--------------------------------------------------------------
:BotMissResume
;
;	Continue on with our mission objectives...
;
;--------------------------------------------------------------

	Wait MISSION_WAIT, 0.5, BotMissTick

	Exit

;--------------------------------------------------------------
:RescuePrincess
;
;	See if we currently have the princess.
;	if not, go to the hostage site...
;--------------------------------------------------------------

	GetObjectHandle Princess0, g_hPrincess
	GetObjectHandle RescueZone0, g_hRescueZone

	if ( g_hPrincess==NULL )
		DebugOut No princess to rescue!!
		Exit
	endif

	if ( g_hRescueZone==NULL )
		DebugOut No rescue zone for princess!!
		Exit
	endif

	Set g_mission, GT_RESCUE_PRINCESS

	gosub BotMissTick

	Exit

;--------------------------------------------------------------
:CancelTick
;--------------------------------------------------------------

	Wait MISSION_WAIT, 0, DoNothing

	Exit

;--------------------------------------------------------------
:ReallyAtRescueZone2
;--------------------------------------------------------------
	Stop
	Exit

;--------------------------------------------------------------
:ReallyAtRescueZone
;
;	We're really there, so time to stop...
;
;--------------------------------------------------------------

	gosub CancelTick
	Stop
	Walk
	Wait MISSION_WAIT, 0.5, ReallyAtRescueZone2

	Exit

;--------------------------------------------------------------
:AtRescueZone
;
;	We are at the bounding box of the rescue zone...
;	Now go in...
;
;--------------------------------------------------------------

	GetPos g_hMyObject, g_posX, g_posY, g_posZ
	GetPos g_hRescueZone, g_posX, g_nTemp, g_posZ

	RunToPos g_posX, g_posY, g_posZ, 12, ReallyAtRescueZone


	Exit

;--------------------------------------------------------------
:HavePrincessTick
;
;
;	Keep heading towards the Princess Rescue Zone
;--------------------------------------------------------------

	RunTo g_hRescueZone, 0, AtRescueZone

	Exit

;--------------------------------------------------------------
:FoundPrincess
;
;	We've found her, now "use" her...
;--------------------------------------------------------------

	Set g_bHavePrincess, TRUE
	Trigger g_hPrincess,Use

	Exit

;--------------------------------------------------------------
:FindPrincessTick
;
;	Keep searching for princess.....
;
;--------------------------------------------------------------

	RunTo g_hPrincess, 36, FoundPrincess

	Exit

;--------------------------------------------------------------
:BotMissTick
;
;	Do our thinking....
;
;--------------------------------------------------------------

	if ( g_bHavePrincess==TRUE )
		gosub HavePrincessTick
	else
		gosub FindPrincessTick
	endif

	Wait MISSION_WAIT, 0.5, BotMissTick

	Exit

;--------------------------------------------------------------
:PrincessLost
;
;	The princess will trigger us if somebody else
;--------------------------------------------------------------

	Set g_bHavePrincess, FALSE

	Exit

;--------------------------------------------------------------
:Celebrate
;
;	We won!!
;--------------------------------------------------------------

	if ( g_nTemp==0 )
		Set g_nTemp, 1
	else
		Set g_nTemp, 0
	endif

	SetCrouch g_nTemp

	Wait 8, 0.5, Celebrate

	Exit

;--------------------------------------------------------------
:PrincessRescued
;
;
;	We rescued the princess!!!  Yahoo!
;
;--------------------------------------------------------------

	Stop
	Wait MISSION_WAIT, 0, DoNothing

	gosub Celebrate

	Exit

;--------------------------------------------------------------
:BotMissInit
;
;	Initialization stuff...
;
;--------------------------------------------------------------

	AddTrigger RescuePrincess, RescuePrincess
	AddTrigger RP, RescuePrincess
	AddTrigger PrincessLost, PrincessLost
	AddTrigger PrincessRescued, PrincessRescued

	Exit

