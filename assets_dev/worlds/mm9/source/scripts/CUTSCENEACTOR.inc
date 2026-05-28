;-------------------------------
;	CutSceneActor.inc
;	by SJR
;	11-07-01
;	Purpose:single routine for
;			messaging CutScene.inc
;			when scene done
;-------------------------------

#string		sceneactor_sCameraName = ""
#hobject	sceneactor_hCamera = 0

;-------------------------------
:EndScene
;	call this once at the end of each scene
;-------------------------------
	;;get the registered name of the camera
	if( sceneactor_hCamera==0 )
		GetConsoleStrVar CUTSCENE_NAME, sceneactor_sCameraName
		GetObjectHandle sceneactor_sCameraName, sceneactor_hCamera
		if( sceneactor_hCamera==0 )
			Exit 1
		endif
	endif

	;;signal it to advance to the next scene
	Trigger sceneactor_hCamera, Next

Exit 1
;-------------------------------