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
#include <vector>
#include <string>

namespace angel{
	class MMStrFile
	{
	public:
		MMStrFile(const std::string& mapname);
		~MMStrFile();
		const std::string& operator[](size_t i)
		{
			if( (i) >= strs.size() )return blankstr;
			return strs[i];
		}
		size_t size(){return strs.size();}

	protected:
	private:
		bool LoadFromFile(const std::string& filename);
		std::vector<std::string> strs;
		std::string blankstr;
	};

}