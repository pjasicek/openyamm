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
        
aeLog::aeLog( msglevel_t msglev ):msglev(msglev),currentlev( LOG_NORMAL )
{

}

aeLog::~aeLog( )
{
	Shutdown();
}

void aeLog::Init( const char* fname)
{
	logfile.open(fname);
	if( !logfile )
		throw error( (boost::format("aeLog:cannot open %s") % fname).str() );
	logfile << "Log started\n";
}

void aeLog::Shutdown()
{
	if( sstr.str().size() )
	{
		operator<<(endl);
	}
	logfile << "Log shutdown\n";
	logfile.close();
}
void aeLog::Print( msglevel_t level, const char* text )
{
	if( level < msglev )
		return;

	logfile << text << std::endl;
}

void aeLog::Print( msglevel_t level, const std::string& text )
{
	if( level < msglev )
		return;
	logfile << text << std::endl;
}

aeLog& aeLog::operator<< ( const logcontrol_t val )
{
	switch( val ) 
	{
	case endl:
		Print( currentlev, sstr.str() );
		currentlev = LOG_NORMAL;
		sstr.str("");
		break;
	case normal:
		currentlev = LOG_NORMAL;
		break;
	case debug:
		currentlev = LOG_DEBUG;
		break;
	default:
		break;
	}
	return *this;
}

aeLog Log;
}
