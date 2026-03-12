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
#pragma once
#include "tabtxt.h"
#include "lodfile.h"
namespace angel{
	class MapStats: public MMTabTxt::TabTxtLine
	{
	public:
		MapStats(const std::string& _mapname ):fullmapname(_mapname),mapstats(NULL),blankstr()
		{
			if(angel::LodManager.FileExist("language/mapstats.txt"))
				mapstats = new angel::MMTabTxt("language/mapstats.txt");
			else
				if(angel::LodManager.FileExist("icons/mapstats.txt"))
					mapstats = new angel::MMTabTxt("icons/mapstats.txt");

			std::string::size_type pos = fullmapname.rfind('/');
			if( pos == std::string::npos)
				mapname = fullmapname;
			else
				mapname = fullmapname.substr(pos+1);
			const angel::MMTabTxt::TabTxtLine* line=NULL;
			if(mapstats)
				line=mapstats->FindLineI(mapname,2);
			if(line )
				MMTabTxt::TabTxtLine::operator=(*line);
		}
		~MapStats()
		{
			delete mapstats;
		}
/*		const std::string& GetString(size_t i)
		{
			if( size() <=i)return blankstr;
			return at(i);
		}

		int GetInt(size_t i)
		{
			if(size() <=i)return 0;
			return atoi(at(i).c_str());
		}*/
	protected:
		std::string fullmapname;
		std::string mapname;
		angel::MMTabTxt* mapstats;
		std::string blankstr;
	private:
	};
}