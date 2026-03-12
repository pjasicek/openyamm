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
#ifndef _ae_LOG_FILE
#define _ae_LOG_FILE

#include <string>
#include <vector>
#include <iostream>
#include <fstream>
#include <sstream>
#include <boost/format.hpp>

namespace angel{

class aeLog
{
public:
	typedef enum {LOG_DEBUG, LOG_NORMAL, LOG_NONE} msglevel_t;
	typedef enum {endl, normal, debug} logcontrol_t;
	aeLog( msglevel_t msglev = LOG_NORMAL );
	~aeLog();
	void SetMsgLevel( msglevel_t mlev )
	{
		msglev = mlev;
	}
	void Init( const char* fname);
	void Print( msglevel_t level, const char* text);
	void Print( msglevel_t level, const std::string& text );
	void Print( const char* text)
	{
		Print( LOG_NORMAL, text );
	}
	void Print( const std::string& text )
	{
		Print( LOG_NORMAL, text );
	}
	void Shutdown();
	template<class T>
	aeLog& operator<< ( const T& val )
	{
		sstr << val;
		return *this;
	}

	aeLog& operator<< ( int val )
	{
		sstr << val;
		return *this;
	}

	aeLog& operator<< ( float val )
	{
		sstr << val;
		return *this;
	}

	aeLog& operator<< ( const char* val )
	{
		sstr << val;
		return *this;
	}

	aeLog& operator<< ( const logcontrol_t val );
	
	private:
        std::ofstream	logfile;
		std::ostringstream sstr;
		msglevel_t		msglev;
		msglevel_t		currentlev;
};

extern aeLog Log;
}
#endif //_ae_LOG_FILE