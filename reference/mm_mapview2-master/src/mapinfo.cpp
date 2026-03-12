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
#include "stdafx.h"


namespace angel{

	Mapinfo* Mapinfo::m_instance = 0;

	Mapinfo* Mapinfo::getInstancePtr() { return m_instance; }
	Mapinfo& Mapinfo::getInstance() { assert(m_instance); return *m_instance; }


	Mapinfo::Mapinfo() : BaseLayout("mapinfo.layout")
	{
		assert(!m_instance);
		m_instance = this;
		            
		assignWidget(mText, "Mapinfotext");
		mMainWidget->setVisible(true);
	}

	Mapinfo::~Mapinfo()
	{
		mMainWidget->setVisible(false);
		m_instance = 0;
	}
	wchar_t mb2wc(char ch)
	{
		wchar_t wch;
		MultiByteToWideChar(CP_ACP,0,&ch,1,&wch,sizeof(wch));
		//mbstowcs(&wch,&ch,1);
		return wch;
	}

	void Mapinfo::SetText(const std::string & str)
	{
		std::wstring wstr;
		std::transform(str.begin(),str.end(), std::back_insert_iterator<std::wstring>(wstr), mb2wc);
		mText->setCaption(Ogre::UTFString(wstr));
		const MyGUI::IntSize& size  = mText->getTextSize();
		mMainWidget->setSize(size+MyGUI::IntSize(10,4));
		mText->setSize(size);
	}

}
