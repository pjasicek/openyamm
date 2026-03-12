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

namespace angel
{
	MMTabTxt::MMTabTxt(const std::string& fname)
	{
		pLodData ldata = LodManager.LoadFileData(fname);
		if(!ldata)
			throw error("MMTabTxt cannot load file");
		int lastpos = 0;
		std::string val;
		TabTxtLine* linep=new TabTxtLine;
		for( size_t i = 0; i < ldata->size(); i++)
		{
			char ch = (char)ldata->at(i);
			if( ch == '\t')
			{
				linep->push_back(val);
				val="";
				continue;
			}
			if( ch == 0x0d)
			{
				if( (i+1) == ldata->size() || ldata->at(i+1) != 0x0a)
				{
					angel::Log << "MMTabTxt: 0x0d without 0x0a line:" << lines.size() << " blk:" << linep->size() << " file: "<< fname << angel::aeLog::endl;
				}else
				{
					i++;
				}
				linep->push_back(val);
				val="";
				lines.push_back(linep);
				linep=new TabTxtLine;
				continue;
			}
			val += ch;
		}
		linep->push_back(val);
		lines.push_back(linep);
	}
	MMTabTxt::~MMTabTxt()
	{
		for (size_t i=0; i< lines.size();i++)
		{
			delete lines[i];
			lines[i]=NULL;
		}
	}
	const MMTabTxt::TabTxtLine* MMTabTxt::FindLine(int val, unsigned int col)
	{
		class find_dword_by_col: public std::unary_function<TabTxtLine*,bool>
		{
			unsigned int col;
			 int val;
		public:
			explicit find_dword_by_col(int _val, int _col):val(_val),col(_col){}
			bool operator()(const TabTxtLine* l) const
			{
				if(l->size()<= col)
					return false;
				std::stringstream ss(l->at(col));
				int check_val;
				ss >> check_val;
				if(ss.fail())
					return false;
				return check_val == val;
			}
		};
		std::vector<TabTxtLine*>::iterator cur = std::find_if(lines.begin(),lines.end(),find_dword_by_col(val,col));
		if(cur != lines.end())
			return *cur;
		return NULL;
	}
	const MMTabTxt::TabTxtLine* MMTabTxt::FindLineI(const std::string& val, unsigned int col)
	{
		class find_stri_by_col: public std::unary_function<TabTxtLine*,bool>
		{
			unsigned int col;
			std::string val;
		public:
			explicit find_stri_by_col(const std::string& _val, unsigned int _col):val(_val),col(_col)
			{
				std::transform( val.begin(), val.end(), val.begin(), tolower);
			}
			bool operator()(const TabTxtLine* l) const
			{
				if(l->size()<= col)
					return false;
				std::string s=l->at(col);
				std::transform( s.begin(), s.end(), s.begin(), tolower);
				
				return s==val;
			}
		};
		std::vector<TabTxtLine*>::iterator cur = std::find_if(lines.begin(),lines.end(),find_stri_by_col(val,col));
		if(cur != lines.end())
			return *cur;
		return NULL;
	}
	const MMTabTxt::TabTxtLine* MMTabTxt::FindLine(const std::string& data, unsigned int col)
	{
		class find_str_by_col: public std::unary_function<TabTxtLine*,bool>
		{
			unsigned int col;
			std::string data;
		public:
			explicit find_str_by_col(const std::string& _data, unsigned int _col):data(_data),col(_col){}
			bool operator()(const TabTxtLine* l) const
			{
				if(l->size()<= col)
					return false;
				return l->at(col)==data;
			}
		};
		std::vector<TabTxtLine*>::iterator cur = std::find_if(lines.begin(),lines.end(),find_str_by_col(data,col));
		if(cur != lines.end())
			return *cur;
		return NULL;
	}
	const MMTabTxt::TabTxtLine* MMTabTxt::LineByIndex(unsigned int index)
	{
		if(index >=lines.size())
			return NULL;
		return lines[index];
	}
}
