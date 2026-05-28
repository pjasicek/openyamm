;-------------------------------
;	HonkFirstCeremony.inc
;	by SJR
;	01-10-02
;	Purpose:
;-------------------------------
#include HonkHostility.inc

#hobject	first_hHONK_CEREMONY = 0

;-------------------------------
:InitHonkFirstCeremony
;-------------------------------
	if( first_hHONK_CEREMONY==0 )
		GetObjectHandle HONK_CEREMONY, first_hHONK_CEREMONY
		if( first_hHONK_CEREMONY==0 )
			Wait 0, 1, InitHonkFirstCeremony
		endif
	endif

	CreateObjectLink first_hHONK_CEREMONY
	OnObjectLinkBroken first_CheckObject

	Exit 1

;-------------------------------
:first_CheckObject
;-------------------------------
	GetParam 0, g_hObject
	if( g_hObject==first_hHONK_CEREMONY )
		gosub OnFirstCeremony
	else
		gosub BecomeHostile
	endif

	Exit 1

;-------------------------------
:OnFirstCeremony
;-------------------------------
	Exit 1