;-----------------------------------
;	Circle.inc
;	by SJR
;	12-11-01
;	Purpose:generate circle coordinates
;-----------------------------------

#number		PI = 3.141592653589793238462643383279

;;outputs: (u,v) = circle(x,y)
#number		circle_u = 0
#number		circle_v = 0

;;inputs
#number		circle_nRadius = 1
#number		circle_SumdA = 0
#number		circle_dA = 0
#number		circle_nDir = 1

;-----------------------------------
:InitCircle
;	radianize angles, cap direction
;-----------------------------------
	circle_SumdA = 0
	;;radianize it
	circle_dA = circle_dA / 180 * PI

	if( circle_nDir>=0 )
		circle_nDir = 1
	else
		circle_nDir = -1
	endif

	Exit 1

;-----------------------------------
:CircleIncrement
;	rotates (u,v) by (+\-)circle_dA
;-----------------------------------
	circle_SumdA = circle_dA * circle_nDir + circle_SumdA

	Cos circle_SumdA, circle_u
	Sin circle_SumdA, circle_v

	circle_u = circle_nRadius * circle_u
	circle_v = circle_nRadius * circle_v

	Exit 1