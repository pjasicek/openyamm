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
/*!
	@file
	@author		Albert Semenov
	@date		08/2008
	@module
*/
#ifndef __MAPINFO_H__
#define __MAPINFO_H__

#include <MyGUI.h>
#include "BaseLayout/BaseLayout.h"

namespace angel
{

	class Mapinfo: public wraps::BaseLayout
	{
	public:
		static Mapinfo * getInstancePtr();
		static Mapinfo & getInstance();

		Mapinfo();
		virtual ~Mapinfo( );

		void SetText(const std::string & str);
	private:
		static Mapinfo * m_instance;
		MyGUI::StaticTextPtr mText;
	};

} // namespace angel

#endif // __MAPINFO_H__
