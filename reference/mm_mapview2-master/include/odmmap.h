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
#ifndef _ae_ODMMap
#define _ae_ODMMap
//#include "stdafx.h"
#include <windows.h>
#include <vector>
#include <string>
#include "aeGeometry.h"
#include "lodfile.h"
#include "mapstats.h"


namespace angel{
	class ODMmap
	{
	private:
		enum VisMask
		{
			TERRAIN_MASK = 1<<0,
			BMODEL_MASK = 1<<1,
			SPAWN_MASK = 1<<2,
			ENTITY_MASK = 1<<3
		};

#pragma pack(push,1)
		static const int maxnumv_bmface = 0x14;
		struct bmodel_face_odm_t
		{
			mm_int_plane_s plane;					//0x00 real_coord = coord/65536.0
			short z_calc[6];			//0x10 z_calc FACET_Z_CALC1 FACET_Z_CALC2 FACET_Z_CALC3 
			DWORD	attr;							//0x1c FACET_ATTRIBUTES
			unsigned short v_idx[maxnumv_bmface];	//0x20
			short	tex_x[maxnumv_bmface];			//0x48
			short	tex_y[maxnumv_bmface];			//0x70
			short	normal_x[maxnumv_bmface];		//0x98 X_INTERCEPT_DISPLACEMENTS
			short	normal_y[maxnumv_bmface];		//0xc0 Y_INTERCEPT_DISPLACEMENTS
			short	normal_z[maxnumv_bmface];		//0xe8 Z_INTERCEPT_DISPLACEMENTS
			short   unk02;							//0x110 FACET_BITMAP_INDEX
			short	tex_dx,tex_dy;					//0x112
			mm_short_bbox_s  bbox;					//0x116
			unsigned short COG_NUMBER,              //0x122 faceid for using in events (change texture..)
						   COG_TRIGGERED_NUMBER,	//0x124 event# on use
						   COG_TRIGGER,				//0x126 //event on touch?
						   RESERVED;				//0x128
			BYTE	GRADIENT_VERTEXES[4];			//0x12A 
			BYTE	numv;							//0x12e
			BYTE	POLYGON_TYPE;					//0x12f
			BYTE	SHADE;							//0x130
			BYTE	VISIBILITY;						//0x131
			BYTE	PADDING[2];						//0x132 (unused?)
		};
		struct bmodel_odm_t
		{
			char name1[0x20],name2[0x20];
			int attrib;						//0x40 attibutes
			int num_vertex;					//0x44
			int *pVertexes;					//0x48 fills on load (unused(fill on load))
			int num_faces;					//0x4c
			int unk02;						//0x50 // CONVEX_FACETS_COUNT WORD, 2 bytes padding (suspect unused)
			int *pFaces,*pUnkArray;			//0x54 0x58 - ORDERING_OFFSET (unused(fill on load))
											//ordering offset
			int num3;						//0x5c //BSPNODE_COUNT (suspect unused)
			int unk03a;						//0x60 BSPNODE_OFFSET
			int unk03b;						//0x64 DECORATIONS_COUNT (suspect unused)
			int unk03[2];					//0x68 CENTER_X CENTER_Y
			mm_int_vec3_s origin1;				//0x70
			mm_int_bbox_s bbox;					//0x7c
			int unk04[6];					//0x94 BF BBOX
			mm_int_vec3_s origin2;				//0xac Bounding center
			int unk05;						//0xb8 Bounding radius
		};
		struct odm_spawn_t
		{
			mm_int_vec3_s origin;			//0x00
			WORD radius;					//0x0c
			WORD type_id;					//0x0e
			WORD index;						//0x10
			WORD attrib;					//0x12
		};
		struct odm_ent_t
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
			odm_ent_t mm6ent;
			WORD spec_trig,padding;
			char name[entname_size];
			Ogre::AxisAlignedBox bbox;
		};
		struct spawn_t
		{
			odm_spawn_t mm6spawn;
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

		struct bm_face_t
		{
			Ogre::AxisAlignedBox bbox;
			Ogre::Plane plane;
		};
		struct bm_bspnode_t
		{
			DWORD hz[2];
		};

		struct bmodel_t
		{
			//BYTE	*bindata;
			bmodel_odm_t bmodel_hdr;
			//int		*vertex_array;
			//BYTE	*face_array;
			//short*	face_unk_array;
			//char*	face_texnames_array;
			//BYTE	*hz_array;
//			int		numvertex,numfaces,num3;
//			bbox_t	bbox;
//			vec3_t	origin1,origin2;
//			int		unk0x94[6],unk0xb8;
//			std::string						name1,name2;
			//std::vector<odm_bmodel_face_t>  faces;
			std::vector<mm_int_vec3_s> vertexes;
			std::vector<bmodel_face_odm_t> faces;
			std::vector<bm_face_t> ogre_faces;
			std::vector<std::string> faces_tex_names;
			std::vector<short> unk_array; //num_faces*2
			std::vector<bm_bspnode_t> bspnodes;//bspnode array 8*num3;
			Ogre::Vector3 origin;
			Ogre::AxisAlignedBox bbox;
			bool hide;
		};
#pragma pack(push,1)	
		struct tile_idx_s
		{
			WORD hz,idx;
		};
#pragma pack(pop)

		BYTE	mastertile;
		static const int tilesize = 512;
		static const int heightsize = 32;
		static const int ntilex = 0x80;
		static const int ntiley = 0x80;

		std::string mapname;
		angel::MapStats mapstats;
		int version;
		int entsize;
		int spawnsize;

		//pointers to binary data
		BYTE    *data;
		pLodData ldata;
		tile_idx_s* tile_idx_tbl;
		size_t     datasize;
		BYTE*   heightmap;
		BYTE*   tilemap;
		BYTE*   zeroedmap;
		int     num_TerNorm;
		BYTE*   CMAP1;
		BYTE*   CMAP2;
		short*   TerNorm;

		//int     num_bddata;
		//BYTE*   BDData;
		//BYTE*   BDData_facesdata;

		//int     num_entites;
		//BYTE*   entites;
		//char*   entnames;
		std::vector<ent_t> entites;


		//int     num_idlist;
		//BYTE*   idlist;
		std::vector<WORD> idlist;

		//BYTE*   OMAP; // size = 0x10000  
		std::vector<DWORD> OMAP;

		std::vector<spawn_t> spawns;
		//int     num_spawn;
		//BYTE*   spawn;



		std::vector<bmodel_t> bmodels;
		
		
		int selected_bmodel_idx,selected_face_idx,selected_ent_idx,selected_spawn_idx;
		ManualObject* selected_bmodel;
		bool showents;
		
	private:
		SceneManager *mSceneMgr;
		angel::Mapinfo* mMapinfo;
		//bool    SelectVersion();
		bool    PrepareODM();
		bool	LoadODM();
		void    LoadSpawn(int num_spawn, BYTE* spawndata);
		void    LoadEnts(int num, BYTE* entdata,char*entnames);
		void	AddTerrainToScene();
		void	AddBModelsToScene();
		void	AddSpawnToScene();
		void	AddEntsToScene();
		void	SetMapInfoOverlay();
		//void	SetODMMapFaceInfoOverlay();
		void    SelectBModel();
		void    DeselectBModel();
		void    SelectSpawn();
		void    DeselectSpawn();
		void    SelectEntity();
		void    DeselectEntity();
		void    DeselectAll();
	public:
		ODMmap(pLodData loddata,const char*fname,SceneManager *_mSceneMgr);
		~ODMmap();
		int MapVersion() { return version;}  
		const std::string& MapName(){ return mapname;}
		void AddToScene();
		void Select( Ray ray);
		void ToggleSelectedBModel();
		void ToggleEnts();
		void ResetBmodels();
		void Save(std::string fname);
	};
}
#endif //_ae_ODMMap
