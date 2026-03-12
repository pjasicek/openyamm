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
#ifndef _ae_mmLod_FILE
#define _ae_mmLod_FILE
#include <string>
#include <map>
#include <vector>
#include <fstream>
#include <cstdio>
#include <boost/regex.hpp>
#include <boost/shared_ptr.hpp>
#include <Windows.h>

namespace angel{
typedef std::vector<BYTE> LodData;
typedef boost::shared_ptr<LodData> pLodData;


class LodFile
{
private:
	typedef struct 
	{
		FILE*		  f;
		std::string   name;
		std::string   dirname;
	}lod_file_t;
	typedef struct 
	{
		int lodindex,off,size,version;
	}pak_item_t;
	std::vector<lod_file_t> paks;
	std::map<std::string, pak_item_t> files;
	pak_item_t FindFile(const std::string& fname);
	pLodData LoadMapFileData(const pak_item_t&);
	pLodData LoadSpritesFileData(const pak_item_t&);
	pLodData LoadSpritesFileHdr(const pak_item_t&);
public:
	LodFile(){}
	~LodFile();
	bool  AddLod( const std::string& fname );
	bool  FileExist(const std::string& fname)
	{
		pak_item_t pitm = FindFile(fname);
		return pitm.size >=0;
	}
	pLodData LoadFile( const std::string& fname); //данные как они есть в lod файле
	pLodData LoadFileData( const std::string& fname);//для картинок в конец дописывается незапакованная палитра
	pLodData LoadFileHdr( const std::string& fname);//только данные 0x20 без имени (в mm8 language имя размером 0x40, в остальных 0x10)
	pLodData LoadFileHdrName( const std::string& fname);//только блок заголовка с именем 0x40 в mm8 lang, 0x10 в остальных
	int	  GetFileList( const boost::regex& re, std::vector <std::string>* filelist);	
	size_t GetNumPaks(){return paks.size();};
	size_t GetNumFiles(){return files.size();};
protected:
	

};
extern LodFile LodManager;
};
#endif //_ae_mmLod_FILE