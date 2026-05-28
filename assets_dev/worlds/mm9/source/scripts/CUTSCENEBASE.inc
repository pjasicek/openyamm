;--------------------------------------------
;	BaseCutScene.inc
;	by SJR
;	10-16-01
;	Purpose:base include for cut scenes
;
;	Parent must set up:
;		sNotifyName, sLocationName, sTargetName, LISTFIRST, LISTLAST
;--------------------------------------------
#include	BaseGlobals.inc
#include	ListMaker.inc

#string		sLocationName = ""
#string		sTargetName = ""
#string		sNotifyName = ""

#string		cutscene_sMyName = ""

#hobject	cutscene_hLocation = 0
#hobject	cutscene_hTarget = 0
#hobject	cutscene_hNotify = 0
#hobject	cutscene_hMe = 0

#number		cutscene_x = 0
#number		cutscene_y = 0
#number		cutscene_z = 0

;--------------------------------------------
:InitCutSceneBase
;	must set up your vars
;	before calling this
;--------------------------------------------
	;;get last one, then wrap to first
	LISTINDEX = LISTLAST

	GetMyHandle cutscene_hMe
	GetObjectName cutscene_hMe, cutscene_sMyName
	SetConsoleStrVar CUTSCENE_NAME, cutscene_sMyName

	AddTrigger Next, StartNextScene

	Exit TRUE

;--------------------------------------------
:SceneInterrupt
;	look at something not on the list
;--------------------------------------------
	GetParam 0, cutscene_hTarget
	gosub AlignCamera

	if( LISTINDEX==LISTFIRST )
		gosub CameraOn
	endif

	;;put it into "last scene mode"
	if( LISTINDEX==LISTLAST )
		RemoveTrigger Next
		AddTrigger Next, CameraOff
	endif

	Exit TRUE

;--------------------------------------------
:StartNextScene
;	next set of locations+targets
;--------------------------------------------
	gosub GetNextLocation
	;;quit if either object is bad
	if( cutscene_hLocation==0 )
		gosub CameraOff
		Exit TRUE
	endif
	if( cutscene_hTarget==0 )
		gosub CameraOff
		Exit TRUE
	endif

	gosub AlignCamera
	Trigger cutscene_hNotify, trigger

	;;only turn cam on once, otherwise blinking occurs
	if( LISTINDEX==LISTFIRST )
		gosub CameraOn
	endif

	;;put it into "last scene mode"
	if( LISTINDEX==LISTLAST )
		RemoveTrigger Next
		AddTrigger Next, CameraOff
	endif

	Exit TRUE

;--------------------------------------------
:GetNextLocation
;	advance all scene objects by 1
;--------------------------------------------
	LISTNAME = sLocationName
	gosub GetNextObject
	cutscene_hLocation = LISTOBJECT

	LISTNAME = sTargetName
	gosub GetCurrentObject
	cutscene_hTarget = LISTOBJECT

	LISTNAME = sNotifyName
	gosub GetCurrentObject
	cutscene_hNotify = LISTOBJECT

	Exit TRUE

;--------------------------------------------
:AlignCamera
;	sets pos to cutscene_hLocation
;	sets dir to cutscene_hTarget
;--------------------------------------------
	GetPOS cutscene_hLocation, cutscene_x,cutscene_y,cutscene_z
	SetPOS cutscene_hMe, cutscene_x,cutscene_y,cutscene_z
	FaceObject cutscene_hTarget, 0, DoNothing

	Exit TRUE

;--------------------------------------------
:CameraOn
;	camera and letterbox on
;--------------------------------------------
	gosub OnSceneStart
	Trigger cutscene_hMe, on

	LetterBox TRUE

	Exit TRUE

;--------------------------------------------
:CameraOff
;	camera, letterbox, fade off
;--------------------------------------------
	Trigger cutscene_hMe, off
	gosub OnSceneDone

	LetterBox FALSE

	Exit TRUE

;--------------------------------------------
:OnSceneDone
;	called when the entire sequence
;	is done. override this routine
;--------------------------------------------
	Exit 1

;--------------------------------------------
:OnSceneStart
;	called when the entire sequence
;	has started. override this routine
;--------------------------------------------
	Exit 1