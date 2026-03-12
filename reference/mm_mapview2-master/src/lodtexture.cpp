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
#include "zlib.h"
namespace angel{
/*	static MaterialPtr MakeDefaultMaterial()
	{
		const int def_width=256;
		const int def_height=256;
		const char*defTexName="DefaultTexture";
		const char*defMatName="DefaultMaterial";
		if( MaterialManager::getSingleton().resourceExists(defMatName))
			return (MaterialPtr)MaterialManager::getSingleton().getByName(defMatName);

		TexturePtr texture = TextureManager::getSingleton().createManual(
			defTexName, // name
			ResourceGroupManager::DEFAULT_RESOURCE_GROUP_NAME,
			TEX_TYPE_2D,      // type
			def_width, def_height,         // width & height
			0,                // number of mipmaps
			PF_BYTE_RGBA,     // pixel format
			TU_DEFAULT);      // usage; should be TU_DYNAMIC_WRITE_ONLY_DISCARDABLE for
		// textures updated very often (e.g. each frame)
		// Get the pixel buffer
		HardwarePixelBufferSharedPtr pixelBuffer = texture->getBuffer();
		// Lock the pixel buffer and get a pixel box
		pixelBuffer->lock(HardwareBuffer::HBL_NORMAL); // for best performance use HBL_DISCARD!
		const PixelBox& pixelBox = pixelBuffer->getCurrentLock();

		uint8* pDest = static_cast<uint8*>(pixelBox.data);

		// Fill in some pixel data. This will give a semi-transparent blue,
		// but this is of course dependent on the chosen pixel format.
		for (size_t j = 0; j < def_height; j++)
			for(size_t i = 0; i < def_width; i++)
			{
				*pDest++ = 255; // R
				*pDest++ =   0; // G
				*pDest++ = 255; // B
				*pDest++ = 255; // A
			}

			// Unlock the pixel buffer
			pixelBuffer->unlock();

			// Create a material using the texture
			MaterialPtr material = MaterialManager::getSingleton().create(
				defMatName, // name
				ResourceGroupManager::DEFAULT_RESOURCE_GROUP_NAME);

			material->getTechnique(0)->getPass(0)->createTextureUnitState(defTexName);
			//material->getTechnique(0)->getPass(0)->setSceneBlending(SBT_TRANSPARENT_ALPHA);
			return material;
	}
	MaterialPtr GetLodMaterial(const std::string& name)
	{
		std::string matname(name + ".Material");
		std::string texname(name + ".Texture");


		if( MaterialManager::getSingleton().resourceExists(matname))
			return (MaterialPtr)MaterialManager::getSingleton().getByName(matname);

		TexturePtr texture;
		int alpha = 0;
		if(TextureManager::getSingleton().resourceExists(texname))
		{
			texture=TextureManager::getSingleton().getByName(texname);
		}else
		{
			angel::pLodData ldata=angel::LodManager.LoadFile( name );
			BYTE*data= &((*ldata)[0]);
			if(!data)
				return MakeDefaultMaterial();
			int size = (int)ldata->size();
			int psize = *(int*)(data+0x14);
			unsigned int unpsize1 = *(int*)(data+0x10);
			unsigned long unpsize2 = *(int*)(data+0x28);

			if( psize+0x30+0x300 != size )
				return MakeDefaultMaterial();
			if( unpsize2 && unpsize2 < unpsize1)
				return MakeDefaultMaterial();
			BYTE* pal = data + 0x30 + psize;
			BYTE*unpdata = new BYTE[unpsize2 ];
			boost::scoped_array<BYTE> sunpdata(unpdata);
			if ( uncompress( unpdata, &unpsize2 , data + 0x30, psize ) != Z_OK )
				return MakeDefaultMaterial();
			int width  = *(WORD*)(data+0x18);
			int height = *(WORD*)(data+0x1a);
			int imgsize = width*height;
			BYTE *pSrc=unpdata;


			// Create the texture
			texture = TextureManager::getSingleton().createManual(
				name + ".Texture", // name
				ResourceGroupManager::DEFAULT_RESOURCE_GROUP_NAME,
				TEX_TYPE_2D,      // type
				width, height,         // width & height
				0,                // number of mipmaps
				PF_BYTE_BGRA,     // pixel format
				TU_DEFAULT);      // usage; should be TU_DYNAMIC_WRITE_ONLY_DISCARDABLE for


			// Get the pixel buffer
			HardwarePixelBufferSharedPtr pixelBuffer = texture->getBuffer();

			// Lock the pixel buffer and get a pixel box
			pixelBuffer->lock(HardwareBuffer::HBL_NORMAL); // for best performance use HBL_DISCARD!
			const PixelBox& pixelBox = pixelBuffer->getCurrentLock();

			uint8* pDest = static_cast<uint8*>(pixelBox.data);

			// Fill in some pixel data. This will give a semi-transparent blue,
			// but this is of course dependent on the chosen pixel format.
			for (int j = 0; j < width; j++)
				for(int i = 0; i < height; i++)
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
					*pDest++ =   r; // G
					*pDest++ =   g; // R
					*pDest++ =   b;
					*pDest++ = a; // A
				}
				// Unlock the pixel buffer
				pixelBuffer->unlock();
		}
		// Create a material using the texture
		MaterialPtr material = MaterialManager::getSingleton().create(
			matname, // name
			ResourceGroupManager::DEFAULT_RESOURCE_GROUP_NAME);

		material->getTechnique(0)->getPass(0)->createTextureUnitState(texname);
		if(alpha)
			material->getTechnique(0)->getPass(0)->setSceneBlending(SBT_TRANSPARENT_ALPHA);
	}*/
	static TexturePtr GetDefaultTexture()
	{
		const int def_width=256;
		const int def_height=256;
		const char*defTexName="DefaultTexture";
		

		if( TextureManager::getSingleton().resourceExists(defTexName))
			return (TexturePtr )TextureManager::getSingleton().getByName(defTexName);
		angel::Log << "loading default texture" << angel::aeLog::endl;

		TexturePtr texture = TextureManager::getSingleton().createManual(
			defTexName, // name
			ResourceGroupManager::DEFAULT_RESOURCE_GROUP_NAME,
			TEX_TYPE_2D,      // type
			def_width, def_height,         // width & height
			0,                // number of mipmaps
			PF_BYTE_RGBA,     // pixel format
			TU_DEFAULT);//|TU_AUTOMIPMAP);      // usage; should be TU_DYNAMIC_WRITE_ONLY_DISCARDABLE for
		// textures updated very often (e.g. each frame)
		// Get the pixel buffer
		HardwarePixelBufferSharedPtr pixelBuffer = texture->getBuffer();
		// Lock the pixel buffer and get a pixel box
		pixelBuffer->lock(HardwareBuffer::HBL_NORMAL); // for best performance use HBL_DISCARD!
		const PixelBox& pixelBox = pixelBuffer->getCurrentLock();

		uint8* pDest = static_cast<uint8*>(pixelBox.data);

		// Fill in some pixel data. This will give a semi-transparent blue,
		// but this is of course dependent on the chosen pixel format.
		for (size_t j = 0; j < def_height; j++)
			for(size_t i = 0; i < def_width; i++)
			{
				*pDest++ = 255; // R
				*pDest++ =   0; // G
				*pDest++ = 255; // B
				*pDest++ = 255; // A
			}

			// Unlock the pixel buffer
			pixelBuffer->unlock();
			return texture;
	}
	TexturePtr GetLodTexture(const std::string& name)
	{

		std::string texname(name + ".Texture");
		

		if(TextureManager::getSingleton().resourceExists(texname))
			return TextureManager::getSingleton().getByName(texname);
		angel::Log << "loading texture " << name << angel::aeLog::endl;

		int alpha = 0;

		angel::pLodData ldata=angel::LodManager.LoadFile( name );

		if(!ldata)
			return GetDefaultTexture();
		BYTE*data= &((*ldata)[0]);
		int size = (int)ldata->size();
		int psize = *(int*)(data+0x14);
		unsigned int unpsize1 = *(int*)(data+0x10);
		unsigned long unpsize2 = *(int*)(data+0x28);

		if( psize+0x30+0x300 != size )
			return GetDefaultTexture();
		if( unpsize2 && unpsize2 < unpsize1)
			return GetDefaultTexture();
		BYTE* pal = data + 0x30 + psize;
		BYTE*unpdata = new BYTE[unpsize2 ];
		boost::scoped_array<BYTE> sunpdata(unpdata);
		if ( uncompress( unpdata, &unpsize2 , data + 0x30, psize ) != Z_OK )
			return GetDefaultTexture();
		int width  = *(WORD*)(data+0x18);
		int height = *(WORD*)(data+0x1a);
		int imgsize = width*height;
		BYTE *pSrc=unpdata;

        int nummipmaps = 3;
		// Create the texture
		TexturePtr texture = TextureManager::getSingleton().createManual(
			name + ".Texture", // name
			ResourceGroupManager::DEFAULT_RESOURCE_GROUP_NAME,
			TEX_TYPE_2D,      // type
			width, height,         // width & height
			nummipmaps,                // number of mipmaps
			PF_BYTE_BGRA,     // pixel format
			TU_DEFAULT);      // usage; should be TU_DYNAMIC_WRITE_ONLY_DISCARDABLE for



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
		
		return texture;
	}
}
