;---------------------------------
;	TheThing.inc (john carpenter's)
;	by SJR
;	11-04-01
;	Purpose:turn into a weirdo lookin
;			rastafied evil terror eye
;			thing with big pointy teeth
;---------------------------------
#include BaseFile.inc

#hobject	hAttach = 0

#string		sHeadName = ""
#string		sHeadSkin = ""
#string		sLimbName = ""
#string		sLimbSkin = ""

#stringarray	spAnims[7]
#string			sAnim = ""
#string		ANIMCOMMAND = "LOOPANIM "

#number		nCounter = 6

;---------------------------------
:InitTheThing
;---------------------------------
	CacheSound sounds\animsounds\dragon\wince2.wav

	SetModelFilenames "models\evileyeterror.abc", "skins\evileyeterror.dtx"
	gosub InitStrings
	OnFoundTarget BeginBaseScript

	sHeadName = PARENT + lobberpod + ABC
	sHeadSkin = PARENT + lobberpod + DTX

	sLimbName = PARENT + lobberpod + ABC
	sLimbSkin = PARENT + lobberpod + DTX

	AttachProp sHeadName, sHeadSkin, rhand1, hAttach
	gosub SetAnim
	AttachProp sHeadName, sHeadSkin, lhand1, hAttach
	gosub SetAnim
	AttachProp sHeadName, sHeadSkin, rangeattack5, hAttach
	gosub SetAnim
	AttachProp sLimbName, sLimbSkin, rangeattack2, hAttach
	gosub SetAnim
	AttachProp sLimbName, sLimbSkin, rangeattack3, hAttach
	gosub SetAnim
	AttachProp sLimbName, sLimbSkin, rangeattack6, hAttach
	gosub SetAnim
	AttachProp sHeadName, sHeadSkin, rangeattack4, hAttach
	gosub SetAnim

	Exit

;------------------
:SetAnim
;	set the socket anims
;------------------
	ArrayGet spAnims, nCounter, sAnim
	Trigger hAttach, sAnim
	nCounter = nCounter + 1
	Mod nCounter, 7

	Exit

;------------------
:InitStrings
;	init the socket names
;------------------
	ArrayPut spAnims, 0, hattack1
	ArrayPut spAnims, 1, rattack1
	ArrayPut spAnims, 2, wince1
	ArrayPut spAnims, 3, wince2
	ArrayPut spAnims, 4, land
	ArrayPut spAnims, 5, hattack1
	ArrayPut spAnims, 6, walk

	nCounter = 6
	while( nCounter>=0 )
		ArrayGet spAnims, nCounter, sAnim
		sAnim = ANIMCOMMAND + sAnim
		ArrayPut spAnims, nCounter, sAnim
		nCounter = nCounter - 1
	endwhile
	nCounter = 0

	Exit

;---------------------------------
:BeginBaseScript
;	play a freaky sound, launch base.scr
;---------------------------------
	PlaySound sounds\animsounds\dragon\wince2.wav, DoNothing, 1, 500, 0, 100

	RunScript baseRange.scr

	Exit

;---------------------------------
:DoNothing
;---------------------------------
	Exit 1