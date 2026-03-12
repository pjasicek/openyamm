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
#ifndef __LODTEXTUREMANAGER_H__
#define __LODTEXTUREMANAGER_H__

#include <Ogre.h>
#include <lodfile.h>

namespace angel{
	class LodTextureManager : public Ogre::Singleton<LodTextureManager>, public Ogre::ManualResourceLoader
	{
	public:

		LodTextureManager();
		virtual ~LodTextureManager();

		virtual Ogre::TexturePtr load(const Ogre::String &name, const Ogre::String &group = "LodTextures");

		static LodTextureManager &getSingleton();
		static LodTextureManager *getSingletonPtr();
		/** @see ManualResourceLoader::loadResource */
		void loadResource(Ogre::Resource* res);
	private:
		void GetDefaultTexture(Ogre::Resource* res);
		void loadSprite(Ogre::Resource* res, pLodData hdr, pLodData ldata);
	};
}
#endif
