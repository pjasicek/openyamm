/*

Copyright (C) 2010 Angel (angel.d.death@gmail.com)

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  

See the included (GNU.txt) GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
*/
#include "selectmapdialog.h"
#include <windows.h>
#include <ogre.h>
#include <string>
#include <vector>
#include "lodfile.h"
#include "tabtxt.h"
#include "resource.h"
#include "mapstats.h"

namespace angel{
namespace
{
    SelectMapDlg* dlg=NULL;  // This is a pointer to instance, since this is a static member
}


SelectMapDlg::SelectMapDlg(Ogre::RenderWindow* _mWindow,std::string _oldname):mWindow(_mWindow),oldname(_oldname)
{
                static const boost::regex re("maps/.+\\.(blv|odm)");
                mHInstance = GetModuleHandle( NULL );
                angel::LodManager.GetFileList( re, &maplist);
}
SelectMapDlg::~SelectMapDlg(){}
void SelectMapDlg::SetWindow(Ogre::RenderWindow* _mWindow){mWindow=_mWindow;}

std::string SelectMapDlg::GetMapname()
{
        if( dlg )
			throw Ogre::Exception(0,"dublicate dialog", "SelectMapDlg::GetMapname");
                
        dlg=this;
      	HWND hWnd=NULL;
      	if(mWindow)
      		mWindow->getCustomAttribute("WINDOW", &hWnd); 
      	if(hWnd && mWindow->isFullScreen())
      		ShowWindow(hWnd,SW_HIDE);
        int i = DialogBox(mHInstance, MAKEINTRESOURCE( IDD_SELECTMAP ), NULL, SelectMapDlgProc);
        if (i == -1)
        {
            int winError = GetLastError();
            char* errDesc;
            int i;

            errDesc = new char[255];
            // Try windows errors first
            i = FormatMessage(
                FORMAT_MESSAGE_FROM_SYSTEM |
                FORMAT_MESSAGE_IGNORE_INSERTS,
                NULL,
                winError,
                MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), // Default language
                (LPTSTR) errDesc,
                255,
                NULL
            );

            throw Ogre::Exception(winError,errDesc, "SelectMapDlg::GetMapname");
        }
      	if(hWnd && mWindow->isFullScreen())
      		ShowWindow(hWnd,SW_SHOW);
      	dlg=NULL;
        if (i != -2)
            return maplist.at(i);
        else
            return oldname;


}
BOOL SelectMapDlg::SelectMapDlgProc( HWND hwndDlg, UINT message, WPARAM wParam, LPARAM lParam )
{
	switch ( message )
	{
	case WM_INITDIALOG:
		{
			char str[0x100];

			SendDlgItemMessage( hwndDlg, IDC_MAPLIST, LB_RESETCONTENT, 0, 0 );
			size_t selected = 0;
			

			for ( size_t i = 0; i< dlg->maplist.size(); ++i)
			{
				const std::string& mapfilename=dlg->maplist[i];
				std::string clname,txtname;
				txtname=mapfilename;
				while(txtname.size()<20)
					txtname+=' ';

				angel::MapStats mapstats(mapfilename);
				txtname += mapstats.GetString(1);
				
				strncpy(str,txtname.c_str(),sizeof(str));
				if( mapfilename == dlg->oldname )
					selected = i;
				SendDlgItemMessage( hwndDlg, IDC_MAPLIST, LB_ADDSTRING, 0,( LPARAM ) &str );
				
			}
			SendDlgItemMessage( hwndDlg, IDC_MAPLIST, LB_SETCURSEL, selected, 0 );

			int 	CenterX, CenterY;
			WINDOWINFO wi;
			GetWindowInfo(hwndDlg, &wi);
			CenterX = (GetSystemMetrics(SM_CXSCREEN) - (wi.rcWindow.left - wi.rcWindow.right )) / 2;
			CenterY = (GetSystemMetrics(SM_CYSCREEN) - (wi.rcWindow.bottom - wi.rcWindow.top)) / 2;
			
			if (CenterX > CenterY*2)
				CenterX >>= 1;	// dual screens
			CenterX = (CenterX < 0) ? 0: CenterX;
			CenterY = (CenterY < 0) ? 0: CenterY;
			SetWindowPos (hwndDlg, NULL, CenterX, CenterY, 0, 0,
				SWP_NOSIZE | SWP_NOZORDER | SWP_SHOWWINDOW | SWP_DRAWFRAME);
		}
		break;
	case WM_COMMAND:
		switch ( LOWORD( wParam ) )
		{
		case IDOK:
			EndDialog( hwndDlg, SendDlgItemMessage( hwndDlg, IDC_MAPLIST, LB_GETCURSEL, 0, 0 ) );
			// Fall through. 
			break;
		case IDCANCEL:
			EndDialog( hwndDlg, -2 );
			break;
		case IDC_MAPLIST:
			switch(HIWORD(wParam)) 
			{
			case LBN_DBLCLK:
				EndDialog( hwndDlg, SendDlgItemMessage( hwndDlg, IDC_MAPLIST, LB_GETCURSEL, 0, 0 ) );
				break;
			default:
				break;
			}
			break;
		}
		break;
	default:
		return FALSE;
	}
	return TRUE;
}
}
