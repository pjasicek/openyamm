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
//#include "LodTextureManager.h"
#include "zlib.h"
//#include <lodfile.h>
//using namespace Ogre;
template<> angel::LodTextureManager *Ogre::Singleton<angel::LodTextureManager>::ms_Singleton = 0;	
namespace angel{
    

	LodTextureManager *LodTextureManager::getSingletonPtr()
	{
		return ms_Singleton;
	}

	LodTextureManager &LodTextureManager::getSingleton()
	{  
		assert(ms_Singleton);  
		return(*ms_Singleton);
	}

	LodTextureManager::LodTextureManager()
	{
	}

	LodTextureManager::~LodTextureManager()
	{
	}

	Ogre::TexturePtr LodTextureManager::load(const Ogre::String &name, const Ogre::String &group)
	{
		Ogre::ResourceManager::ResourceCreateOrRetrieveResult res = Ogre::TextureManager::getSingleton().createOrRetrieve(name, group, true, this);
		Ogre::TexturePtr tex = res.first;
		tex->load();
		return tex;
	}
	void LodTextureManager::loadSprite(Ogre::Resource* res, pLodData hdr, pLodData ldata)
	{
		Texture* texture = static_cast<Texture*>(res);
		angel::Log <<"texture " << res->getName() << " error datasize "  << angel::aeLog::endl;
		return GetDefaultTexture(res);
	}

	void LodTextureManager::loadResource(Ogre::Resource* res)
	{
		int alpha = 0;
		angel::Log << angel::aeLog::debug <<"loading texture " << res->getName() << angel::aeLog::endl;
		
		angel::pLodData ldata = angel::LodManager.LoadFileData( res->getName() );

//		angel::pLodData ldata=angel::LodManager.LoadFile( res->getName() );
		
		if(!ldata)
			return GetDefaultTexture(res);
		angel::pLodData hdr = angel::LodManager.LoadFileHdr( res->getName() );

		BYTE*data= &((*ldata)[0]);
		BYTE*hdrdata= &((*hdr)[0]);
		int size = (int)ldata->size();
		int psize = *(int*)(hdrdata+0x4);
		unsigned int unpsize1 = *(int*)(hdrdata+0x0);
		unsigned long unpsize2 = *(int*)(hdrdata+0x18);

		if( unpsize2+0x300 != size )
		{
			//angel::Log <<"texture " << res->getName() << " error datasize "  << unpsize2 << "/" << size<< angel::aeLog::endl;
			//return GetDefaultTexture(res);
			return loadSprite(res,hdr,ldata);
		}
//		if( unpsize2 && unpsize2 < unpsize1)
//			return GetDefaultTexture(res);
		BYTE* pal = data + unpsize2;
		int width  = *(WORD*)(hdrdata+0x8);
		int height = *(WORD*)(hdrdata+0xa);
		int imgsize = width*height;
		BYTE *pSrc=data;


/*		BYTE*data= &((*ldata)[0]);
		int size = (int)ldata->size();
		int psize = *(int*)(data+0x14);
		unsigned int unpsize1 = *(int*)(data+0x10);
		unsigned long unpsize2 = *(int*)(data+0x28);

		if( psize+0x30+0x300 != size )
			return GetDefaultTexture(res);
		if( unpsize2 && unpsize2 < unpsize1)
			return GetDefaultTexture(res);
		BYTE* pal = data + 0x30 + psize;
		BYTE*unpdata = new BYTE[unpsize2 ];
		boost::scoped_array<BYTE> sunpdata(unpdata);
		if ( uncompress( unpdata, &unpsize2 , data + 0x30, psize ) != Z_OK )
			return;
		int width  = *(WORD*)(data+0x18);
		int height = *(WORD*)(data+0x1a);
		int imgsize = width*height;
		BYTE *pSrc=unpdata;*/

		
		int nummipmaps = 3;
		// Create the texture
		Texture* texture = static_cast<Texture*>(res);
		texture->setTextureType(TEX_TYPE_2D);
		texture->setWidth(width);
		texture->setHeight(height);
		texture->setNumMipmaps(nummipmaps);
		texture->setFormat(PF_BYTE_BGRA);
		texture->setUsage(TU_DEFAULT);
		texture->setDepth(1);
		texture->setHardwareGammaEnabled(false);
		texture->setFSAA(0);
		texture->createInternalResources();

		/*TextureManager::getSingleton().createManual(
		name + ".Texture", // name
		ResourceGroupManager::DEFAULT_RESOURCE_GROUP_NAME,
		TEX_TYPE_2D,      // type
		width, height,         // width & height
		nummipmaps,                // number of mipmaps
		PF_BYTE_BGRA,     // pixel format
		TU_DEFAULT);      // usage; should be TU_DYNAMIC_WRITE_ONLY_DISCARDABLE for
		*/


		// Fill in some pixel data. This will give a semi-transparent blue,
		// but this is of course dependent on the chosen pixel format.
		int w=width;
		int h=height;

		int n=0,off=0; 
		nummipmaps = (int)texture->getNumMipmaps();
		for ( n = 0,off= 0; off < (int)unpsize2 && n <nummipmaps + 1 ;  n++)
		{
			if( w < 1 || h <1 )
				break;
			// Get the pixel buffer
			HardwarePixelBufferSharedPtr pixelBuffer = texture->getBuffer(0,n);

			// Lock the pixel buffer and get a pixel box
			pixelBuffer->lock(HardwareBuffer::HBL_NORMAL); // for best performance use HBL_DISCARD!
			const PixelBox& pixelBox = pixelBuffer->getCurrentLock();

			uint8* pDest = static_cast<uint8*>(pixelBox.data);

			for (int j = 0; j < w; j++)
				for(int i = 0; i < h; i++)
				{
					int index=*pSrc++;
					int r = pal[index*3+0]; 
					int g = pal[index*3+1]; 
					int b = pal[index*3+2]; 
					int a = 0xff;
					if( index == 0 && ((r == 0 && g >250 && b > 250) || (r > 250 && g ==0 && b > 250)))
					{
						alpha=1;
						a= 0;
						r=g=b=0;
					}
					*pDest++ =   b; // G
					*pDest++ =   g; // R
					*pDest++ =   r;
					*pDest++ = a; // A
				}
				pixelBuffer->unlock();


				//off += w*h;
				w/=2;
				h/=2;
		}
		// Unlock the pixel buffer

	}
	void LodTextureManager::GetDefaultTexture(Ogre::Resource* res)
	{
		// Create the texture
		Texture* texture = static_cast<Texture*>(res);
		Ogre::Image img;
		img.load("pending.png",Ogre::ResourceGroupManager::DEFAULT_RESOURCE_GROUP_NAME);
		texture->loadImage(img);
	}
}
