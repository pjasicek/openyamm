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
	class EventFile;
	class EvtCommand
	{
	public:
		EvtCommand(BYTE*data, int len, EventFile*_parent);
		~EvtCommand();
		const std::string& decompiled_str(){return _decompiled_str;}
		const std::string& codes(){return _codes_str;}
		const std::string& codes_txt(){return _codes_txt_str;}
		int seq_num(){return _seq_num;}
		int evt_num(){return _evt_num;}
	private:
		std::string _decompiled_str;
		std::string _codes_str;
		std::string _codes_txt_str;
		int _evt_num;
		int _seq_num;
		EventFile*evtfile;
	};
	class EventFile
	{
	     friend class EvtCommand;
	public:
		EventFile(const std::string& _mapname, int _version = 6);
		~EventFile();
		std::vector<const EvtCommand*> GetEvent(size_t evtn);
	protected:
	private:
		std::vector<EvtCommand*> cmds;
		std::string filename;
		std::string mapname;
		bool isGlobal;
		int version;
		const std::string& GetLocalString(size_t n);
	};
}