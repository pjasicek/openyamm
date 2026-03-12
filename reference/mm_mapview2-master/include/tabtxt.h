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
	
	class MMTabTxt
	{
	public:
		class TabTxtLine: public std::vector<std::string> 
		{
		public:
			TabTxtLine():blankstr(){}
			~TabTxtLine(){}
			const std::string& GetString(size_t i)
			{
				if( size() <=i)return blankstr;
				return operator[](i);
			}

			int GetInt(size_t i)
			{
				if(size() <=i)return 0;
				return atoi(at(i).c_str());
			}
		protected:
			std::string blankstr;
		};
		MMTabTxt(const std::string& fname);
		~MMTabTxt();
		const TabTxtLine* FindLine(int val, unsigned int col = 0);
		const TabTxtLine* FindLine(const std::string& data, unsigned int col = 0);
		const TabTxtLine* FindLineI(const std::string& val, unsigned int col = 0);//no case
		const TabTxtLine* LineByIndex(unsigned int index);
		size_t GetNumLines()
		{
			return lines.size();
		}
	private:
		std::vector<TabTxtLine*> lines;
	};
}