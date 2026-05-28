;-----------------------------------
;	CheckStat.inc
;	by SJR
;	Purpose:basic stat comparisons
;
;	Must init 'stat_hPlayer' yourself
;	Must init STATINDEX, STATCOMPARE
;-----------------------------------

#number		STATINDEX = 0

#number		STATCOMPARE = 0
#number		STATRESULT = 0

#number		stat_nValue = 0

;-------------------
:CheckStat
;-------------------
	GetAttribute STATINDEX, stat_nValue

	if( stat_nValue > STATCOMPARE )
		STATRESULT = 1
		Exit
	endif
	if( stat_nValue == STATCOMPARE )
		STATRESULT = 0
		Exit
	endif
	if( stat_nValue < STATCOMPARE )
		STATRESULT = -1
		Exit
	endif

	Exit 1