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
#ifndef _ae_blvMap
#define _ae_blvMap
//#include "stdafx.h"
#include <windows.h>
#include <vector>
#include <string>
#include "lodfile.h"
#include "mapstats.h"
#include "aeGeometry.h"

namespace angel{

	class BLVmap
	{
	private:
		enum VisMask
		{
			WALLS_MASK = 1<<0,
			PORTALS_MASK = 1<<1,
			SPAWN_MASK = 1<<2,
			ENTITY_MASK = 1<<3
		};
#pragma pack(push,1)
		struct face_blv_t
		{//starts at 0x10 in mm7,mm8
			mm_int_plane_s plane;					//0x00
			short z_calc[6];						//0x10 Z_CALC1,Z_CALC2,Z_CALC3,
			int attrib;								//0x1c
			int VERTEX_INDEX_OFFSET,				//0x20 //not used(fills on load)
				X_DISPLACEMENT_OFFSET,
				Y_DISPLACEMENT_OFFSET,
				Z_DISPLACEMENT_OFFSET,
				U_TEXTURE_OFFSET,					//0x30
				V_TEXTURE_OFFSET;
			WORD fparm_index;				//0x38
			short			   bitmap_index;			//0x3a
			WORD			   room_number,				//0x3c
						   room_behind_number;		//0x3e
			mm_short_bbox_s bbox;					//0x40
			BYTE facet_type,numvertex;				//0x4c
			BYTE padding[2];						//0x4e (unused?)
		};
		struct faceparams_blv_t
		{
			mm_int_vec3_s	fade;					//0x00
			WORD	facet_index;					//0x0c
			short	bitmap_index;					//0x0e
			WORD	texture_frame_table_index;		//0x10
			WORD	texture_frame_table_COG;		//0x12
			short tex_u;							//0x14 tex_u
			short tex_v;							//0x16 tex_u
			WORD  cog_number;						//0x18 
			WORD  cog_triggered;					//0x1A event index
			WORD  cog_trigger_type;					//0x1c
			short	fade_base_x;					//0x1e
			short	fade_base_y;					//0x20
			WORD	light_level;					//0x22
		};
		struct blv_spawn_t
		{
			mm_int_vec3_s origin;			//0x00
			WORD radius;					//0x0c
			WORD type_id;					//0x0e
			WORD index;						//0x10
			WORD attrib;					//0x12
		};
		struct blv_ent_t
		{
			WORD declist_id;				//0x00
			WORD AIattrMarkers;				//0x02
			mm_int_vec3_s origin;			//0x04
			int facing;						//0x10
			WORD evt1,evt2;					//0x14
			WORD var1,var2;					//0x18
		};

#pragma pack(pop)
		static const int entname_size = 0x20;
		struct ent_t
		{
			blv_ent_t mm6ent;
			WORD spec_trig,padding;
			char name[entname_size];
			Ogre::AxisAlignedBox bbox;
		};
		struct spawn_t
		{
			blv_spawn_t mm6spawn;
			DWORD group;						//0x14
			Ogre::AxisAlignedBox bbox;
			//    1 - bunch of goblins
			//    2 - bunch of mages
			//    3 - bunch of archers
			//    4 - one goblin
			//    5 - one apprentice mage
			//    6 - one archer
			//    7 - one goblin shaman
			//    8 - one journeyman mage
			//    9 - one archer
			//    10 - one goblin king
			//    11 - one mage
		};
		struct face_t
		{
			std::string texname;
			std::string matname;
			int texw,texh;
			//p_aeTexture tex;

			//plane_t plane,plane7;
			Ogre::Plane plane;
			Ogre::AxisAlignedBox bbox;
			mm_float_plane_s plane7;
			//bbox_t	bbox;
			//int		areas[2];
			int		fparm_index;
			//int tex_x,tex_y; //textureoffs;
			//unknown data
			//BYTE	data0x10[0x10],b0x4c;
			//WORD	b0x4e;

			//int numvertexs;
			face_blv_t blvhdr;
			faceparams_blv_t blvfaceparam;
			char texture_name[11];
			BYTE faceparams2[10];
			std::vector<WORD> vertex_idxs;
			std::vector<short> vertex_normal_x;
			std::vector<short> vertex_normal_y;
			std::vector<short> vertex_normal_z;

			std::vector<short> vertex_tex_x;
			std::vector<short> vertex_tex_y;
			//BYTE    *bindata;
			//int		offv;
		};
		char* BLVNodeName;

		BYTE    *data;
		pLodData ldata;
		size_t     datasize;

		short   *vertex_data;
		int		num_vertex;
		BYTE    *faces_array;
		int		num_faces;
		short   *facedata;
		int     facedatasize;
		BYTE    *facetextures;

		int		numfaceparms;
		faceparams_blv_t   *faceparams1;
		BYTE    *faceparams2;

		int		num_sectors;
		BYTE	*sectorsdata;
		int		Rdatasize;
		BYTE	*sectorsRdata;
		int		RLdatasize;
		BYTE	*sectorsRLdata;
		int		num_sprites_hz;
		int		num_sprites;
		BYTE	*spritesdata;
		char	*spritesnamesdata;
		int		num_lights;
		BYTE	*lightsdata;
		int		num_unk9;
		BYTE	*Unknown9data;
		int		num_spawn;
		BYTE	*spawndata;
		int		num_outline;
		BYTE	*mapoutlinedata;

		int		version;
		int		facesize;
		int		spritesize;
		int		lightsize;
		int		spawnsize;
		int		sectorsize;
		
		std::vector<ent_t> entites;
		std::vector<spawn_t> spawns;

		std::vector<mm_short_vec3_s> mm_vertexes;
		std::vector<Vector3> vertexes;
		
		std::vector<face_t> faces;
		int selected_face_index,selected_ent_idx,selected_spawn_idx;
		std::string mapname;
		angel::MapStats mapstats;

		SceneManager *mSceneMgr;

		void    LoadSpawn(int num_spawn, BYTE* spawndata);
		void    LoadEnts(int num, BYTE* entdata,char*entnames);
		bool    PrepareBLV();
		bool    DetectBLVVersion();
		void	LoadBLVMap();
		void	LoadTexture(face_t& face);
		void AddPortalsToScene();
		void	AddSpawnToScene();
		void	AddEntsToScene();
		void SetMapInfoOverlay();
		//void SetBLVMapFaceInfoOverlay();
		void DeselectAll();
		void DeselectFace();
		void SelectFace();
		void    SelectSpawn();
		void    DeselectSpawn();
		void    SelectEntity();
		void    DeselectEntity();
		bool isPortal( const face_t & face )
		{
			if ( face.texname.size(  ) < 1 )
				return true;
			if ( face.blvhdr.attrib & 1 )
				return true;
			return false;
		}
		bool showportals,showents;
	public:
		BLVmap(pLodData loddata,const char*fname,SceneManager *_mSceneMgr);
		~BLVmap();
		void AddToScene();
		int MapVersion() { return version;}  
		void TogglePortals();
		void ToggleEnts();
		const std::string& MapName(){ return mapname;}
		void Select(Ray ray);

	};
}
#endif //_ae_blvMap
