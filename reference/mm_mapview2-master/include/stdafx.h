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

#include <windows.h>
// C RunTime Header Files
#include <stdlib.h>
#include <malloc.h>
#include <memory.h>
#include <tchar.h>

#include <string>
#include <vector>
#include <map>
#include <string>
#include <locale>
#include <iostream>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <exception>
#include <functional>

#include <boost/shared_ptr.hpp>
#include <boost/scoped_ptr.hpp>
#include <boost/weak_ptr.hpp>
#include <boost/scoped_array.hpp>
#include <boost/format.hpp>

#include <Ogre.h>
#include <OgreConfigFile.h>
#include <OgreStringConverter.h>
#include <OgreException.h>
#include <MyGUI.h>
#include "Console.h"
#include <OgreTextAreaOverlayElement.h>
#include "mapinfo.h"



//Use this define to signify OIS will be used as a DLL
//(so that dll import/export macros are in effect)
#define OIS_DYNAMIC_LIB
#include <OIS/OIS.h>

using namespace Ogre;
#include "LodTextureManager.h"

#include "resource.h"
#include "aeError.h"
#include "log.h"
#include "lodfile.h"
#include "tabtxt.h"
#include "mapstats.h"
//#include "lodtexture.h"
#include "BLVmap.h"
#include "ODMmap.h"

