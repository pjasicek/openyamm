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
#include "eventfile.h"

namespace angel{
	EvtCommand::EvtCommand(BYTE*data, int len, EventFile*_parent):
		evtfile(_parent),_codes_str((char*)data,len)
	{

	}
	EvtCommand::~EvtCommand()
	{

	}
	
	EventFile::EventFile(const std::string& _mapname, int _version): version(_version),mapname(_mapname)

	{

	}
	EventFile::~EventFile()	
	{

	}
	std::vector<const EvtCommand*> EventFile::GetEvent(size_t evtn)
	{

	}
	const std::string& EventFile::GetLocalString(size_t n)
	{

	}
}