;-------------------------------------------------------------
;	FollowPath.inc
;	Jeff Leggett
;	11/09/1999
;
;		This include file can be used to have your object
;	(typically a camera) follow a path.  Your object will
;	use both the positional information and rotation information
;	stored in the path you pass to it.  
;
;	Usage:
;		gosub FollowPathInit
;		Set g_sFollowPathName, <Your Path Name Here>
;		Set g_nFollowPathSpeed, < Your speed here>
;		Set g_nFollowPathCallback, < Callback # to use when we reach a marker>
;		Set g_nFollowPathDoneCallback, <callback# to use when path is done>
;		Set g_nFollowPathLoops, 1
;		SetCallback g_nFollowPath
;		gosub FollowPath
;
;
;-------------------------------------------------------------


#include globals.inc

; globals that other scripts can/should use
#string				g_sFollowPathName
#number				g_nFollowPathSpeed
#number				g_nFollowPathLoops
#number				g_nFollowPathCallback
#number				g_nFollowPathDoneCallback
;
; You may check what path # we are currently
; heading for with this variable
;
#number				g_nFollowPathNbr


; local variables that only this script should use

#hobject			hFollowPathObject
#number				nFollowPathRate
#number				nFollowPathCount
#number				nFollowPathLoopCount

#string				sFollowPathTemp

;---------------------------------------------------------------------
:FollowPathInit
;---------------------------------------------------------------------

	; Default to NOT doing any callbacks
	Set g_nFollowPathCallback, -1
	Set g_nFollowPathDoneCallback, -1

	; 
	Set g_nFollowPathLoops, 1

	OnPlayerInterrupt FollowPathPlayerInterrupt

	Exit

;---------------------------------------------------------------------
:FollowPath
;
;	Prior to calling this routine, you need to setup the following
;	global variables:
;
;		g_sFollowPathName		-> name of path to follow
;		g_nFollowPathSpeed		-> Speed object should follow path
;
;---------------------------------------------------------------------

	Set g_nFollowPathNbr, 0
	Set	nFollowPathCount, 0

	gosub FollowPathGetPathCount

	if ( nFollowPathCount==0 )
		Exit 0
	endif

	gosub FollowPathFirst

	Exit 1

;---------------------------------------------------------------------
:FollowPathGetCurrHandle
;	Gets handle to current path marker...
;---------------------------------------------------------------------

	Set sFollowPathTemp, g_sFollowPathName
	Add sFollowPathTemp, g_nFollowPathNbr

	GetObjectHandle sFollowPathTemp, hFollowPathObject

	Exit

;---------------------------------------------------------------------
:FollowPathFirst
;---------------------------------------------------------------------

	Set g_nFollowPathNbr, 0
	Set nFollowPathLoopCount, 0
	gosub FollowPathGetCurrHandle
	gosub FollowPathMove

	Exit

;---------------------------------------------------------------------
:FollowPathNext
;
;	Finds next path name and follows it
;---------------------------------------------------------------------		
	;Let the path object know were here
	Trigger hFollowPathObject,Trigger	

	Add g_nFollowPathNbr, 1
	
;	DebugOut ---Follow Path Number----	
;	DebugOut g_nFollowPathNbr

;	DebugOut ---Follow Path Count---
;	DebugOut nFollowPathCount

	if ( g_nFollowPathNbr >= nFollowPathCount )		
		Add nFollowPathLoopCount, 1
			
		if ( nFollowPathLoopCount >= g_nFollowPathLoops )
			; we're done!

;			DebugOut ---Follow Path Number----
;			DebugOut g_nFollowPathNbr

;			DebugOut ---Follow Path Count---
;			DebugOut nFollowPathCount
						
;			DebugOut calling done callback...
			DoCallback g_nFollowPathDoneCallback			
			Exit
		endif

		; Loop back to First one...
		Set g_nFollowPathNbr, 0
	else
		; Call our callback (with g_nFollowPathNbr set to the marker we're currently at!)		
		Sub g_nFollowPathNbr, 1
		DoCallback g_nFollowPathCallback		
		Add g_nFollowPathNbr, 1
	endif


	; Go to next marker...
	gosub FollowPathGetCurrHandle

;	DebugOut calling followPath Move
	gosub FollowPathMove

	Exit

;---------------------------------------------------------------------
:FollowPathMove
;	
;	Do the calculations and get us moving...
;---------------------------------------------------------------------

	GetPos hFollowPathObject, g_posX, g_posY, g_posZ
	GetRotation hFollowPathObject, g_rotX, g_rotY, g_rotZ, g_rotSpin

	CalcRotationRate hFollowPathObject,g_nFollowPathSpeed, nFollowPathRate

	SetRotation g_rotX,g_rotY,g_rotZ,g_rotSpin,nFollowPathRate
	MoveToPos g_posX,g_posY,g_posZ,g_nFollowPathSpeed, FollowPathNext

	Exit

;---------------------------------------------------------------------
:FollowPathGetPathCount
;---------------------------------------------------------------------

	Set nFollowPathCount,0
	Set g_bTemp, TRUE

	while ( g_bTemp==TRUE )
		Set sFollowPathTemp,g_sFollowPathName
		Add sFollowPathTemp,nFollowPathCount

		GetObjectHandle sFollowPathTemp, hFollowPathObject

		if ( hFollowPathObject==0 )
			; we've counted them all!
			Set g_bTemp, FALSE
		else
			Add nFollowPathCount, 1
		endif
	endwhile

	Exit


;---------------------------------------------------------------------
:FollowPathStop
;---------------------------------------------------------------------
	Stop

	Exit

;---------------------------------------------------------------------
:FollowPathPlayerInterrupt
;
;	Player pressed the USE key during camera playback.
;
;	By default, we'll abort the script and turn off the camera...
;
;---------------------------------------------------------------------

	GetMyHandle g_hMyObject
	gosub FollowPathStop
	Trigger g_hMyObject,OFF

	exit TRUE
