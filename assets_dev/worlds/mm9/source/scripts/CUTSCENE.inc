;--------------------------------------------
;	CutScene.inc
;	by SJR
;	10-16-01
;	Purpose:Must be run by a camera
;			object. Handles cut scenes
;
;	Triggers:
;		"Next" = snap to next scene
;		"Move" = move to next scene
;
;	Parent must set up:
;		sNotifyName, sLocationName, sTargetName
;		LISTFIRST, LISTLAST
;--------------------------------------------
#include CutSceneBase.inc

#number		cutscene_nDist = 0
#number		cutscene_nRate = 0
#number		cutscene_nGap = 0

#number		cutscene_xDir = 0
#number		cutscene_yDir = 0
#number		cutscene_zDir = 0

#number		cutscene_nTemp = 0

;--------------------
:InitCutScene
;--------------------
	gosub InitCutSceneBase

	Exit TRUE

;--------------------
:StartNextScene
;--------------------
	gosub StartNextScene, 1

	Exit TRUE

;--------------------
:OnZoomToTarget
;--------------------
	Exit TRUE

;--------------------
:OnZoomFromTarget
;--------------------
	Exit TRUE

;--------------------
:FollowTarget
;	view follows the target
;--------------------
	Target cutscene_hTarget, TRUE

	Exit TRUE

;--------------------
:RevolveAroundTarget
;--------------------
	Exit TRUE

;--------------------
:ZoomToTarget
;	closes in on the target
;--------------------
	GetDistance cutscene_hMe, cutscene_hTarget, cutscene_nDist
	cutscene_nDist = cutscene_nDist - cutscene_nGap
	GetForwardDir cutscene_xDir,cutscene_yDir,cutscene_zDir
	MoveDir cutscene_xDir,cutscene_yDir,cutscene_zDir, cutscene_nDist, cutscene_nRate, OnZoomToTarget

	Exit TRUE

;--------------------
:ZoomFromTarget
;	pulls back from target
;--------------------
	GetDistance cutscene_hMe, cutscene_hTarget, cutscene_nDist
	cutscene_nDist = cutscene_nDist - cutscene_nGap
	GetFaceDir cutscene_hMe,cutscene_xDir,cutscene_yDir,cutscene_zDir
	cutscene_xDir = cutscene_xDir * -1
	cutscene_yDir = cutscene_yDir * -1
	cutscene_zDir = cutscene_zDir * -1
	MoveDir cutscene_xDir,cutscene_yDir,cutscene_zDir, cutscene_nDist, cutscene_nRate, OnZoomFromTarget

	Exit TRUE
