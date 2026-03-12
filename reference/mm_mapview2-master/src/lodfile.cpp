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
#include <lodfile.h>
#include <zlib.h>
#include <log.h>

namespace angel{

LodFile LodManager;
typedef struct
{
	char fname[0x10];
	int off,size,hz,num;
}lod_head_typ;

typedef struct
{
	char fname[0x10];
	int  off,size,hz,num;
}lod6_item_typ;

/*typedef struct
{
	char fname[0x10];
	int off,size,hz,num;
}lod7_item_typ;*/


typedef struct
{
	char fname[0x40];
	int  off,size,hz;
}lod8_item_typ;


LodFile::~LodFile()
{
	for ( unsigned int i = 0; i< paks.size() ; ++i)
	{
		if( paks[i].f )
			fclose(paks[i].f);
	}
}

bool  LodFile::AddLod( const std::string& fname )
{
	lod_file_t lfile;
	FILE*f;
	f = fopen( fname.c_str(), "rb" );
	
	angel::Log << angel::aeLog::debug << "AddLod: "<< fname << angel::aeLog::endl;
	if(!f)
	{
		
		return false;
	}
	lfile.f = f;
	lfile.name = fname;
	char tmp[0x10];	
	fread(tmp,sizeof(tmp),1,f);
	int version = 6;
	if( strcmp(tmp,"LOD"))
	{
		fclose(f);
		return false;
	}
	if( !strcmp(tmp+4,"MMVIII"))
	{
		version = 8;
		fseek(f,0x100,0);
		lod_head_typ header;
		fread(&header,sizeof(header),1,f);
		std::string dirname = header.fname;
		std::transform( dirname .begin(), dirname .end(), dirname.begin(), tolower);
		lfile.dirname = dirname;
		lod8_item_typ *tbl = new lod8_item_typ[header.num];
		fread(tbl,header.num*sizeof(lod8_item_typ),1,f);
		int baseoff = header.off;
		for (int i =0; i < header.num;++i)
		{
			std::string tname = dirname+"/"+tbl[i].fname;
			std::transform( tname.begin(), tname.end(), tname.begin(), tolower);
			files[tname].off = baseoff+tbl[i].off;
			files[tname].size = tbl[i].size;
			files[tname].lodindex = (int)paks.size();
			files[tname].version = 8;
		}
		delete[]tbl;
		paks.push_back(lfile);
		angel::Log << "Added "<< header.num << " files from " << fname << angel::aeLog::endl;
/*		fclose(f);
		return false;*/
	}else
	{
		fseek(f,0x100,0);
		lod_head_typ header;
		fread(&header,sizeof(header),1,f);
		std::string dirname = header.fname;
		std::transform( dirname .begin(), dirname .end(), dirname.begin(), tolower);
		lfile.dirname = dirname;
		lod6_item_typ *tbl = new lod6_item_typ[header.num];
		fread(tbl,header.num*sizeof(lod6_item_typ),1,f);
		int baseoff = header.off;

		for (int i =0; i < header.num;++i)
		{
			std::string tname = dirname+"/"+tbl[i].fname;
			std::transform( tname.begin(), tname.end(), tname.begin(), tolower);
			files[tname].off = baseoff+tbl[i].off;
			files[tname].size = tbl[i].size;
			files[tname].lodindex = (int)paks.size();
			files[tname].version = 6;
		}
		delete[]tbl;
		paks.push_back(lfile);
		angel::Log << "Added "<< header.num << " files from " << fname << angel::aeLog::endl;
	}
	return true;
}

pLodData LodFile::LoadFile( const std::string& fname)
{
	pak_item_t pakitm = FindFile(fname);
	if(pakitm.size < 0 )
		return pLodData();

	int fsize = pakitm.size;
	FILE*f = paks[pakitm.lodindex].f;
	fseek(f,pakitm.off,0);
	pLodData data(new LodData(fsize));
	
	//BYTE *data = new BYTE[*fsize];
	fread(&(*data)[0],fsize,1,f);
	return data;
}
LodFile::pak_item_t LodFile::FindFile(const std::string& fname)
{
	std::string tname(fname);
	std::transform( tname.begin(), tname.end(), tname.begin(), tolower);
	std::map<std::string, pak_item_t>::const_iterator ii = files.find( tname );
	
	if( ii == files.end() )
	{
		angel::Log << "LodFile::LoadFile: file "<< tname << " not found" << angel::aeLog::endl;
		pak_item_t pakitm;
		pakitm.size=-1;
		return pakitm;
	}
	return (*ii).second;
}
pLodData LodFile::LoadFileData( const std::string& fname)//для картинок в конец дописывается незапакованная палитра
{
	pak_item_t pakitm = FindFile(fname);
	if(pakitm.size < 0 )
		return pLodData();
	if(paks[pakitm.lodindex].dirname == "maps")
		return LoadMapFileData(pakitm);
	if(paks[pakitm.lodindex].dirname == "sprites08")
		return LoadSpritesFileData(pakitm);
	int fsize = pakitm.size;
	FILE*f = paks[pakitm.lodindex].f;
	int off = pakitm.off;
	fseek(f,off,0);
	BYTE*tmp=new BYTE[fsize];
	if(!tmp)
	{
		angel::Log << "LodFile::LoadFileData: file "<< fname << " error alloc mem" <<angel::aeLog::endl;
		return pLodData();
	}
	fread(tmp,fsize,1,f);
    BYTE*hdrdata=tmp+((pakitm.version == 8)?0x40:0x10);
	int psize = *(int*)(hdrdata+0x4);
	unsigned int unpsize1 = *(int*)(hdrdata+0);
	unsigned long unpsize2 = *(int*)(hdrdata+0x18);
	if( unpsize2 && unpsize2 < unpsize1)
	{
		angel::Log << "LodFile::LoadFileData: file "<< fname << " unpsize1 < unpsize2" << angel::aeLog::endl;
	}
	unsigned long unpsize = unpsize2;

	if(!unpsize)
		unpsize=psize;
	BYTE* adddata = hdrdata+ 0x20 + psize;
	int addsize = fsize - (adddata-tmp);
	//angel::Log << "LodFile::LoadFileData: file "<< fname << " addsize = "  << addsize << angel::aeLog::endl;
	pLodData data(new LodData(unpsize+addsize));
	BYTE*unpdata = &(*data)[0];
	if(unpsize2)
	{
		int z_res = uncompress( unpdata, &unpsize , hdrdata+0x20, psize );

		if ( z_res != Z_OK )
		{
			angel::Log << "LodFile::LoadFileData: file "<< fname << " error unpaking " <<  z_res <<angel::aeLog::endl;
			delete[]tmp;
			return pLodData();
		}

	}else
	{
		memcpy(unpdata, hdrdata+0x20, psize);
	}
	if( addsize > 0  )
		memcpy(unpdata + unpsize2, adddata,addsize );
	delete[]tmp;
	return data;
}
pLodData LodFile::LoadFileHdr( const std::string& fname)//только данные 0x20 без имени (в mm8 language имя размером 0x40, в остальных 0x10)
{
	pak_item_t pakitm = FindFile(fname);
	if(pakitm.size < 0  )
		return pLodData();
	if(paks[pakitm.lodindex].dirname == "maps")
		return pLodData();
	if(paks[pakitm.lodindex].dirname == "sprites08")
		return LoadSpritesFileHdr(pakitm);

	int fsize = pakitm.size;
	FILE*f = paks[pakitm.lodindex].f;
	int off = pakitm.off+((pakitm.version == 8)?0x40:0x10);
	fseek(f,off,0);
	pLodData data(new LodData(0x20));

	fread(&(*data)[0],0x20,1,f);
	return data;

}
pLodData LodFile::LoadFileHdrName( const std::string& fname)//только блок заголовка с именем 0x40 в mm8 lang, 0x10 в остальных
{
	pak_item_t pakitm = FindFile(fname);
	if(pakitm.size < 0 )
		return pLodData();
	if(paks[pakitm.lodindex].dirname == "maps")
		return pLodData();

	int fsize = pakitm.size;
	FILE*f = paks[pakitm.lodindex].f;
	int off = pakitm.off;
	fseek(f,off,0);
	int namesize=((pakitm.version == 8)?0x40:0x10);
	pLodData data(new LodData(namesize));

	fread(&(*data)[0],namesize,1,f);
	return data;
}
pLodData LodFile::LoadSpritesFileData(const pak_item_t& pakitm)
{
	int fsize = pakitm.size;
	FILE*f = paks[pakitm.lodindex].f;
	int off = pakitm.off;
	fseek(f,pakitm.off,0);
	BYTE*tmp=new BYTE[fsize];
	fread(tmp,fsize,1,f);
	
	WORD height = *(WORD*)(tmp+0x12);
	int hdrsize=0x20+height*8;

	int psize = *(int*)(tmp+0xc);
	unsigned long unpsize = *(int*)(tmp+0x1c);
	if( psize+0x20+height*8 != fsize )
	{
		angel::Log << "LodFile::LoadSpritesFileData: incorrect sprite data size"  << angel::aeLog::endl;
		delete[]tmp;
		return pLodData ();
	}
	
	pLodData data(new LodData(unpsize));
	BYTE*unpdata = &(*data)[0];
	int z_res = uncompress( unpdata, &unpsize , tmp+hdrsize, psize );

	if ( z_res != Z_OK )
	{
		angel::Log << "LodFile::LoadFileData: sprite error unpaking " <<  z_res <<angel::aeLog::endl;
		delete[]tmp;
		return pLodData();
	}
	delete[]tmp;
	return data;
}
pLodData LodFile::LoadSpritesFileHdr(const pak_item_t& pakitm)
{
	int fsize = pakitm.size;
	FILE*f = paks[pakitm.lodindex].f;
	int off = pakitm.off;
	fseek(f,pakitm.off,0);
	BYTE*tmp=new BYTE[fsize];
	fread(tmp,fsize,1,f);

	WORD height = *(WORD*)(tmp+0x12);
	int hdrsize=0x20+height*8;
	pLodData data(new LodData(hdrsize));

	memcpy(&(*data)[0],tmp,hdrsize);
	delete[]tmp;
	return data;
}
pLodData LodFile::LoadMapFileData(const pak_item_t& pakitm)
{
	int fsize = pakitm.size;
	FILE*f = paks[pakitm.lodindex].f;
	int off = pakitm.off;
	fseek(f,pakitm.off,0);
	BYTE*tmp=new BYTE[fsize];
	fread(tmp,fsize,1,f);
	BYTE*mdata=tmp;
	if ( *( DWORD * ) ( mdata ) == 0x16741 && *( DWORD * ) ( mdata + 4 ) == 0x6969766d )
	{
		int psize = *( int * ) ( mdata + 8 );

		if ( psize + 0x10 != fsize )
		{
			angel::Log << "LodFile::LoadMapFileData: invalid map7 size" << angel::aeLog::endl;
		}
		unsigned long  datasize = *( int * ) ( mdata + 12 );
		pLodData data(new LodData(datasize));
		BYTE*unpdata = &(*data)[0];
		int z_res = uncompress( unpdata, &datasize, mdata+0x10 , psize );
		delete[]tmp;
		if ( z_res != Z_OK )
		{
			angel::Log << "LodFile::LoadMapFileData: error unpaking " <<  z_res <<angel::aeLog::endl;
			return pLodData();
		}
		return data;
	}else
	{
		int psize = *( int * ) ( mdata);

		if ( psize + 0x8 != fsize )
		{
			angel::Log << "LodFile::LoadMapFileData: file invalid map6 size" << angel::aeLog::endl;
		}
		unsigned long  datasize = *( int * ) ( mdata + 4 );
		pLodData data(new LodData(datasize));
		BYTE*unpdata = &(*data)[0];
		int z_res = uncompress( unpdata, &datasize, mdata+0x8 , psize );
		delete[]tmp;
		if ( z_res != Z_OK )
		{
			angel::Log << "LodFile::LoadMapFileData:  error unpaking " <<  z_res <<angel::aeLog::endl;
			return pLodData();
		}
		return data;
	}
}
int	  LodFile::GetFileList( const boost::regex& re, std::vector <std::string>* filelist)
{
	std::map<std::string, pak_item_t>::const_iterator ii = files.begin();
	int num = 0;
	for ( ; ii != files.end(); ++ii )
	{
		if( boost::regex_match( (*ii).first, re))
		{
			filelist->push_back( (*ii).first );
			num++;
		}
	}
	return num;
}
}
