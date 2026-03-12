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
#include "mmstrfile.h"
namespace angel{
	MMStrFile::MMStrFile(const std::string& mapname)
	{
		
		std::string::size_type pos1 = mapname.rfind('.');
		if(pos1 == std::string::npos)
			pos1 = mapname.size();
		std::string strname = mapname.substr(0,pos1)+".str";
		if( LoadFromFile(strname))
			return;

		std::string::size_type pos2 = mapname.rfind('/');
		if(pos2 == std::string::npos)
			pos2 = mapname.size();
		strname = std::string("icons") + mapname.substr(pos2,pos1-pos2)+".str";
		if( LoadFromFile(strname))
			return;
		strname = std::string("language") + mapname.substr(pos2,pos1-pos2)+".str";
		if( LoadFromFile(strname))
			return;
	}
	MMStrFile::~MMStrFile()
	{

	}
	bool MMStrFile::LoadFromFile(const std::string& filename)
	{
		pLodData ldata = LodManager.LoadFileData(filename);
		if(!ldata)
			return false;
		std::string val;
		for( LodData::const_iterator ii = ldata->begin(); ii != ldata->end(); ii++)
		//for( size_t i = 0; i < ldata->size(); i++)
		{
			char ch = (char)*ii;
			if(ch == 0 )
			{
				strs.push_back(val);
				val="";
				continue;
			}
			val += ch;
		}
		strs.push_back(val);
		return true;
	}

}