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
#include "odmmap.h"
#include "zlib.h"

namespace angel{
	bool    ODMmap::PrepareODM()
	{
		version = 0;
		if(!strcmp((char*)data+0x40, "MM6 Outdoor v1.11"))
		{
			version = 6;
			entsize = 0x1c;  
			spawnsize = 0x14;
			return true;
		}

		if(!strcmp((char*)data+0x40, "MM6 Outdoor v7.00"))
		{
			version = 7;
			entsize = 0x20;  
			spawnsize = 0x18;
			return true;
		}
		for ( int i = 0x40 ; i < 0x50 ; i++ )
		{
			if(data[i])
				return false;
		}

		version = 8;
		entsize = 0x20;  
		spawnsize = 0x18;
		return true;
	}
	bool    ODMmap::LoadODM()
	{
		if(!version)
			return false;
		int off = 0xb0;
		if( version == 8 )
			off += 4;
//#define CHECK_OFF( xxx ) { off += (xxx);if( off > (int)datasize || off < 0 ) return false;}	
#define CHECK_OFF( xxx ) { angel::Log << angel::aeLog::debug <<boost::format( " off = %8x size = %8x")% off % (xxx) <<angel::aeLog::endl;\
	off += (xxx);if( off > (int)datasize || off < 0 ) return false;}	
		
		{//terrain maps
			angel::Log.Print(angel::aeLog::LOG_DEBUG,"Terrains Maps");
			mastertile = data[0x5f];
			tile_idx_tbl = (tile_idx_s*)(data+0xA0);
			heightmap = data + off ; CHECK_OFF(0x4000);
			tilemap = data + off ; CHECK_OFF(0x4000);
			zeroedmap = data + off ; CHECK_OFF(0x4000);	
			//InitTerrain();
			if( version >6 )
			{
				num_TerNorm = *(int*)(data+off); off+=4;
				CMAP1 = data + off ; CHECK_OFF(0x20000);
				CMAP2 = data + off ; CHECK_OFF(0x10000);
				TerNorm = (short*) (data + off) ; CHECK_OFF( num_TerNorm * 12 );
			}else
			{
				num_TerNorm = 0;
				CMAP1 = CMAP2 = NULL;
				TerNorm = NULL;
			}
		}
		{//BModels
			angel::Log.Print(angel::aeLog::LOG_DEBUG,"BModels");
			int num_bddata = *(int*)(data+off); off+=4;
			BYTE*BDData  = data + off ; CHECK_OFF( num_bddata * 0xbc );
			BYTE*BDData_facesdata = data + off ;
			bmodels.reserve( num_bddata );
			for ( int i = 0 ; i < num_bddata ; i++ )
			{
				bmodel_t bm;// = bmodels[i];

				//bm.bindata = BDData + i * 0xbc;
				bm.bmodel_hdr = *(bmodel_odm_t*)(BDData + i * 0xbc);
				/*bm.numvertex = *(int*)(bm.bindata + 0x44);
				bm.numfaces  = *(int*)(bm.bindata + 0x4c);
				bm.num3      = *(int*)(bm.bindata + 0x5c);*/
				bm.vertexes.resize(bm.bmodel_hdr.num_vertex);
				std::copy((mm_int_vec3_s*)(data+off), (mm_int_vec3_s*)(data+off)+bm.bmodel_hdr.num_vertex, bm.vertexes.begin());
				//bm.vertex_array = (int*)(data+off); 
				CHECK_OFF( bm.bmodel_hdr.num_vertex  * 12 );

				bm.faces.resize(bm.bmodel_hdr.num_faces);
				std::copy((bmodel_face_odm_t*)(data+off), (bmodel_face_odm_t*)(data+off)+bm.bmodel_hdr.num_faces, bm.faces.begin());
				//bm.face_array     = data + off; 
				CHECK_OFF( bm.bmodel_hdr.num_faces * (0x134) );
				bm.unk_array.resize(bm.bmodel_hdr.num_faces);
				std::copy((short*)(data+off),(short*)(data+off)+bm.bmodel_hdr.num_faces,bm.unk_array.begin());
				//bm.face_unk_array = (short*)( data + off ); 
				CHECK_OFF( bm.bmodel_hdr.num_faces * 2 );
				char* face_texnames_array = (char*)data +off; 
				CHECK_OFF( bm.bmodel_hdr.num_faces * 10 ;)
				bm.bspnodes.resize(bm.bmodel_hdr.num3);
				std::copy((bm_bspnode_t*)(data+off),(bm_bspnode_t*)(data+off)+bm.bmodel_hdr.num3,bm.bspnodes.begin());
				//bm.hz_array     = data + off; 
				CHECK_OFF( bm.bmodel_hdr.num3 * 8 );
				bm.faces_tex_names.resize(bm.bmodel_hdr.num_faces);
				bm.ogre_faces.resize(bm.bmodel_hdr.num_faces);
				
				bm.origin.x = (bm.bmodel_hdr.bbox.max.x+bm.bmodel_hdr.bbox.min.x)/2;
				bm.origin.y = (bm.bmodel_hdr.bbox.max.y+bm.bmodel_hdr.bbox.min.y)/2;
				bm.origin.z = (bm.bmodel_hdr.bbox.max.z+bm.bmodel_hdr.bbox.min.z)/2;

				for( int k = 0; k < bm.bmodel_hdr.num_faces; k++)
				{
					bm.faces_tex_names[k]=face_texnames_array+k*10;
					bmodel_face_odm_t&face = bm.faces[k];
					bm.ogre_faces[k].bbox=face.bbox;//AxisAlignedBox(face.bbox.minx,face.bbox.miny,face.bbox.minz,face.bbox.maxx,face.bbox.maxy,face.bbox.maxz);
					bm.ogre_faces[k].plane=face.plane;//Plane(face.plane.normal.x/65536.0,face.plane.normal.y/65536.0,face.plane.normal.z/65536.0,face.plane.dist/65536.0);
				}
			    /*bm.bbox=AxisAlignedBox(bm.bmodel_hdr.bbox.min.x-center.x,bm.bmodel_hdr.bbox.min.y-center.y,bm.bmodel_hdr.bbox.min.z-center.z,
												 bm.bmodel_hdr.bbox.max.x-center.x,bm.bmodel_hdr.bbox.max.y-center.y,bm.bmodel_hdr.bbox.max.z-center.z);*/
			    /*bm.bbox=AxisAlignedBox(bm.bmodel_hdr.bbox.min.x,bm.bmodel_hdr.bbox.min.y,bm.bmodel_hdr.bbox.min.z,
												 bm.bmodel_hdr.bbox.max.x,bm.bmodel_hdr.bbox.max.y,bm.bmodel_hdr.bbox.max.z);*/
				bm.bbox=bm.bmodel_hdr.bbox;

				bm.hide=false;
				bmodels.push_back(bm);
			}
		}
		{
			angel::Log.Print(angel::aeLog::LOG_DEBUG,"Entites");
			int num_entites = *(int*)(data+off); off+=4;
			if( num_entites > 0xbb8)
				return false;
			BYTE*entdata  = data + off ; CHECK_OFF( num_entites*entsize );
			char*entnames = (char*)data + off ; CHECK_OFF( num_entites*0x20 );
			LoadEnts(num_entites,entdata,entnames);
			//LoadSprites();
		}
		{
			angel::Log.Print(angel::aeLog::LOG_DEBUG,"IDList");
			int num_idlist = *(int*)(data+off); off+=4;
			WORD*idlistdata  = (WORD*)(data + off) ; CHECK_OFF( num_idlist*2 );
			idlist.resize(num_idlist);
			std::copy(idlistdata,idlistdata+num_idlist,idlist.begin());
		}
		{
			angel::Log.Print(angel::aeLog::LOG_DEBUG,"OMAP");
			DWORD*OMAPdata  = (DWORD*)(data + off) ; CHECK_OFF( 0x10000 );
			OMAP.resize(ntilex*ntiley);
			std::copy(OMAPdata,OMAPdata+ntilex*ntiley,OMAP.begin());
		}
		{
			angel::Log.Print(angel::aeLog::LOG_DEBUG,"SPAWN");
			int num_spawn = *(int*)(data+off); off+=4;
			
			BYTE*spawndata  = data + off ; 
			CHECK_OFF( num_spawn*spawnsize );
			LoadSpawn(num_spawn, spawndata);
		}
		if( off != datasize)
		{
			return false;
		}
		return true;


	}
	void ODMmap::LoadSpawn(int num_spawn, BYTE* spawndata)
	{
		spawns.resize(num_spawn);
		for (int i = 0; i< num_spawn; i++)
		{
			spawns[i].mm6spawn = *(odm_spawn_t*)(spawndata+i*spawnsize);
			if( version > 6 )
				spawns[i].group = *(DWORD*)(spawndata+i*spawnsize + 0x14);
			else
				spawns[i].group = 0;
		}
	}
	void    ODMmap::LoadEnts(int num, BYTE* entdata,char*entnames)
	{
		entites.resize(num);
		for (int i = 0; i< num; i++)
		{
			entites[i].mm6ent= *(odm_ent_t*)(entdata+i*entsize);
			if( version > 6 )
			{
				entites[i].spec_trig= *(WORD*)(entdata+i*entsize + 0x1c);
				entites[i].padding= *(WORD*)(entdata+i*entsize + 0x1c+2);
			}
			else
			{
				entites[i].spec_trig= 0;
				entites[i].padding= 0;
			}
			memcpy(entites[i].name, entnames+i*entname_size,entname_size);
		}
	}


	ODMmap::ODMmap( pLodData loddata, const char *fname, SceneManager *_mSceneMgr )
		:ldata(loddata),data(&(*loddata)[0]),datasize(loddata->size()),version(0),selected_bmodel_idx(-1),selected_face_idx(-1),
		selected_bmodel(NULL),mSceneMgr(_mSceneMgr),showents(true),selected_ent_idx(-1),selected_spawn_idx(-1),
		mMapinfo(0),mapstats(fname)
	{
		angel::Log <<  "Load ODMmap " <<  fname << angel::aeLog::endl;
		if(!PrepareODM() )
		{
			//delete[] data;
			throw error ("Cannot detect ODM version with pak version 7\n");
		};
		/*

		BYTE*mdata=&((*loddata)[0]);

		if ( *( DWORD * ) ( mdata ) == 0x16741 && *( DWORD * ) ( mdata + 4 ) == 0x6969766d )
		{
			int psize = *( int * ) ( mdata + 8 );

			if ( psize + 0x10 != loddata->size() )
				throw error ("invalid ODM7 file\n");
			datasize = *( int * ) ( mdata + 12 );
			data = new BYTE[datasize];

			if ( uncompress( data, &datasize, mdata + 0x10, psize ) != Z_OK )
			{
				delete[]data;
				data = NULL;
				throw error ("Cannot uncompress ODM7\n");
			}

			if(!PrepareODM() )
			{
				delete[] data;
				throw error ("Cannot detect ODM version with pak version 7\n");
			};
			if( version < 7 )
				angel::Log << "Warning odm" << version <<"  map  in pak version 7+" <<angel::aeLog::endl;
		} else
		{
			int psize = *( int * ) ( mdata );

			if ( psize + 0x8 != loddata->size() )
				throw error ("invalid odm6 file\n");
			datasize  = *( int * ) ( mdata + 4 );
			data = new BYTE[datasize];

			if ( uncompress( data, &datasize, mdata + 0x8, psize ) != Z_OK )
			{
				delete[]data;
				data = NULL;
				throw error ("Cannot uncompress odm6\n");
			}
			if(!PrepareODM() )
			{
				delete[] data;
				throw error ("Cannot detect odm version with pak version 6\n");
			};
			if( version != 6 )
				angel::Log << "Warning odm" << version <<"  map  in pak version 6" <<angel::aeLog::endl;
		}*/
		LoadODM( );
		
		//mMapinfo->SetText(fname);

		mapname = fname;
		//		angel::Log <<  "Loaded faces: " << faces.size() << ", vertexs: " << vertexes.size() << angel::aeLog::endl;
	}

	ODMmap::~ODMmap()
	{
		DeselectAll();
		//OverlayManager::getSingleton().getByName("MMView/MapOverlay")->hide();
		//OverlayManager::getSingleton().getByName("MMView/ODMMapBModelInfoOverlay")->hide();

		//if( data )
		//	delete[]data;
	}
//render stuff
	void	ODMmap::AddTerrainToScene()
	{
#pragma pack(push,1)	
		typedef struct
		{
			char name[20];
			WORD hz[3];
		}dtile_t;
#pragma pack(pop)
		//loading tile data
		BYTE*   tiledata;
		if( version == 8 )
		{
			char *tilename;

			switch( mastertile )
			{
			case 0: tilename = "language/dtile.bin";break;
			case 1: tilename = "language/dtile2.bin";break;
			case 2: tilename = "language/dtile3.bin";break;
			default: tilename = "language/dtile.bin";
					 angel::Log << angel::aeLog::debug <<boost::format( "unknown mastertile %8x")% mastertile <<angel::aeLog::endl;
				     break;
			}
			pLodData ptiledata_l  = LodManager.LoadFile( tilename);
			if( !ptiledata_l  )
				throw error ("Cannot load dtile.bin\n");
			int size = (int)ptiledata_l->size();
			BYTE*ptiledata = &((*ptiledata_l)[0]);

			unsigned long unpsize = *( unsigned long * ) ( ptiledata + 0x58 );
			int psize = *( int * ) ( ptiledata + 0x44 );

			if ( psize + 0x60 != size )
				throw error ("invalid dtile.bin file\n");
			tiledata = new BYTE[unpsize];
			if ( uncompress( tiledata, &unpsize, ptiledata + 0x60, psize ) != Z_OK )
			{
				delete[]tiledata;
				throw error ("Cannot uncompress dtile.bin\n");
			}
		}else
		{
			pLodData ptiledata_l  = LodManager.LoadFile( "icons/dtile.bin");
			if( !ptiledata_l )
				throw error("cannot load dtile.bin");
			BYTE*ptiledata = &((*ptiledata_l)[0]);
			
			int size = (int)ptiledata_l->size();
			if( !ptiledata  )
				throw error ("Cannot load dtile.bin\n");

			unsigned long unpsize = *( unsigned long * ) ( ptiledata + 0x28 );
			int psize = *( int * ) ( ptiledata + 0x14 );

			if ( psize + 0x30 != size )
				throw error ("invalid dtile.bin file\n");
			tiledata =new BYTE[unpsize];
			if ( uncompress( tiledata, &unpsize, ptiledata + 0x30, psize ) != Z_OK )
			{
				delete[]tiledata;
				throw error ("Cannot uncompress dtile.bin\n");
			}
		}
		int num = *(int*)(tiledata);
		dtile_t* tbl = (dtile_t*)(tiledata+4);
		//get tile texture names
		struct tile_tex_names_s
		{
			std::string name1,name2;
		};
		std::vector<tile_tex_names_s> tex_names;
		tex_names.resize(256);
		
		for ( int i = 0; i< 256; i++ )
		{
			int index;
			if( i >= 0xc6 )
			{
			 index =  i - 0xc6 + tile_idx_tbl[3].idx;
			}else
			{
		 	 if( i < 0x5a )
			 {
				 index = i;
			 }else
			 {
				 int n = (i-0x5a)/0x24;
				 index = tile_idx_tbl[n].idx - n*0x24; //??? was [n*2] may be [n]
				 index += i-0x5a;
			 }
			}
			char*name=tbl[index].name;
			if(!name[0])
				 name = "pending";
			tex_names[i].name1=name;
			if( tbl[index].hz[2] == 0x300)
			{
			 int group = tbl[index].hz[0];
			 for (int j = 0 ;j<4;j++)
			 {
				 if(tile_idx_tbl[j].hz==group )
				 {
					 int idx2 = tile_idx_tbl[j].idx;
					 char *name2 = tbl[idx2].name;
					 if( name2 && name2[0])
					 {
						 tex_names[i].name2=name2;
					 }
					 break;
				 }
			 }
			}
		}

		//making geometry
#if 0 //make big tile
		{
			SceneNode *Node =  mSceneMgr->getRootSceneNode()->createChildSceneNode("ODMTerrainNode");
			const int num_sub_tile = 4;

			for ( int x1 = 0; x1 < ntilex-1 ; x1+=num_sub_tile)
				for ( int y1 = 0; y1 < ntiley-1; y1+=num_sub_tile)
				{
					char name[0x20];
					sprintf(name,"TerrTile%4dx%4d",x1,y1);
					ManualObject* manOb = mSceneMgr->createManualObject(name);
					manOb->setDynamic(false);
					for ( int x2 = 0; x2 < num_sub_tile ; x2++)
						for ( int y2 = 0; y2 < num_sub_tile; y2++)
						{
							int x =  x1 + x2;
							int y =  y1 + y2;
							if( x+1 >= ntilex || y+1 >= ntiley)
								continue;

							int tile_index = tilemap[y*0x80+x];
							//int tile_index=TerrMap[x][y].tile_index;
							std::string matname="TileMat"+StringConverter::toString( tile_index);

							{
								TexturePtr texture1 = angel::GetLodTexture(std::string("bitmaps/")+tex_names[tile_index].name1);
								TexturePtr texture2;
								bool isTex2 = (tex_names[tile_index].name2 != "");
								if( isTex2 )
									texture2 = angel::GetLodTexture(std::string("bitmaps/")+tex_names[tile_index].name2);

								//load texture
								MaterialPtr material;

								if(MaterialManager::getSingleton().resourceExists(matname) )
								{
									material=MaterialManager::getSingleton().getByName(matname);
								}else
								{
									material = MaterialManager::getSingleton().create(
										matname, // name
										ResourceGroupManager::DEFAULT_RESOURCE_GROUP_NAME);
									if( isTex2  )
									{
										TextureUnitState* texstate = material->getTechnique(0)->getPass(0)->createTextureUnitState(texture2->getName());
										texstate->setTextureAddressingMode(TextureUnitState::TAM_MIRROR);
										Pass* pass = material->getTechnique(0)->createPass();
										texstate = pass->createTextureUnitState(texture1->getName());
										texstate->setTextureAddressingMode(TextureUnitState::TAM_MIRROR);
										pass->setSceneBlending(SBT_TRANSPARENT_ALPHA);
										pass->setDepthBias(0,-1);
									}else
									{
										TextureUnitState* texstate = material->getTechnique(0)->getPass(0)->createTextureUnitState(texture1->getName());
										texstate->setTextureAddressingMode(TextureUnitState::TAM_MIRROR);
									}
									material->getTechnique(0)->getPass(0)->setDepthBias(0,-1);
									

									//material->setAmbient(0.5,0.5,0.5);
									//material->setTextureFiltering(TFO_ANISOTROPIC);
									//material->setTextureAnisotropy(8);
									//material->getTechnique(0)->getPass(0)->setSceneBlending(SBT_TRANSPARENT_ALPHA);
								}
							}
							
							manOb->begin(matname, RenderOperation::OT_TRIANGLE_FAN);
							//manOb->begin(matname, RenderOperation::OT_TRIANGLE_LIST);
							
							Vector3 v1,v2,v3,v4;
							v1.x = v2.x = (x-0x40)*tilesize;
							v3.x = v4.x = (x-0x40+1)*tilesize;
							v1.y = v4.y = -(y-0x40)*tilesize;
							v2.y = v3.y = -(y-0x40+1)*tilesize;

							v1.z = heightmap[y*0x80+x];
							v2.z = heightmap[(y+1)*0x80+x];
							v3.z = heightmap[(y+1)*0x80+x+1];
							v4.z = heightmap[y*0x80+x+1];
							v1.z *= heightsize;
							v2.z *= heightsize;
							v3.z *= heightsize;
							v4.z *= heightsize;

							manOb->position(v1);
							manOb->textureCoord(0.0,0.0);

							manOb->position(v2);
							manOb->textureCoord(0.0,1.0);

							manOb->position(v3);
							manOb->textureCoord(1.0,1.0);

							manOb->position(v4);
							manOb->textureCoord(1.0,0.0);

							//manOb->quad(0,1,2,3);
							manOb->end();
						}
						Node->createChildSceneNode()->attachObject(manOb);
				}
	}
#else //group by texture
		//making geometry
		{
			SceneNode *Node =  mSceneMgr->getRootSceneNode()->createChildSceneNode("ODMTerrainNode");
			
			for ( int tile_index = 0; tile_index <256 ; tile_index++)
				{
					char name[0x20];
					sprintf_s(name,sizeof(name),"TerrTile%3d",tile_index);
					std::string matname="TileMat"+std::string("bitmaps/")+tex_names[tile_index].name1;
					{
						//TexturePtr texture1 = angel::GetLodTexture(std::string("bitmaps/")+tex_names[tile_index].name1);
						TexturePtr texture1 = angel::LodTextureManager::getSingleton().load(std::string("bitmaps/")+tex_names[tile_index].name1);
						TexturePtr texture2;
						bool isTex2 = (tex_names[tile_index].name2 != "");
						if( isTex2 )
							//texture2 = angel::GetLodTexture(std::string("bitmaps/")+tex_names[tile_index].name2);
							texture2 = angel::LodTextureManager::getSingleton().load(std::string("bitmaps/")+tex_names[tile_index].name2);


						//load texture
						MaterialPtr material;

						if(MaterialManager::getSingleton().resourceExists(matname) )
						{
							material=MaterialManager::getSingleton().getByName(matname);
						}else
						{
							material = MaterialManager::getSingleton().create(
								matname, // name
								ResourceGroupManager::DEFAULT_RESOURCE_GROUP_NAME);
							if( isTex2  )
							{
								TextureUnitState* texstate = material->getTechnique(0)->getPass(0)->createTextureUnitState(texture2->getName());
								texstate->setTextureAddressingMode(TextureUnitState::TAM_MIRROR);
								//texstate->setTextureFiltering(FO_NONE,FO_NONE,FO_ANISOTROPIC);
								Pass* pass = material->getTechnique(0)->createPass();
								texstate = pass->createTextureUnitState(texture1->getName());
								texstate->setTextureAddressingMode(TextureUnitState::TAM_MIRROR);
								//texstate->setTextureFiltering(FO_NONE,FO_NONE,FO_ANISOTROPIC);
								pass->setSceneBlending(SBT_TRANSPARENT_ALPHA);
								pass->setDepthBias(0,-1);
							}else
							{
								TextureUnitState* texstate = material->getTechnique(0)->getPass(0)->createTextureUnitState(texture1->getName());
								texstate->setTextureAddressingMode(TextureUnitState::TAM_MIRROR);
								//texstate->setTextureFiltering(FO_NONE,FO_NONE,FO_ANISOTROPIC);
							}
							material->getTechnique(0)->getPass(0)->setDepthBias(0,-1);
							//material->setReceiveShadows(true);
							


							//material->setAmbient(0.5,0.5,0.5);
							//material->setTextureFiltering(TFO_ANISOTROPIC);
							//material->setTextureAnisotropy(8);
							//material->getTechnique(0)->getPass(0)->setSceneBlending(SBT_TRANSPARENT_ALPHA);
						}
					}

					ManualObject* manOb = mSceneMgr->createManualObject(name);
					manOb->setVisibilityFlags(TERRAIN_MASK);
					manOb->setDynamic(false);
					manOb->begin(matname, RenderOperation::OT_TRIANGLE_LIST);
					for ( int x = 0; x < ntilex-1; x++)
						for ( int y = 0; y < ntiley-1; y++)
						{

							if(  tile_index != tilemap[y*0x80+x])
								continue;
							
							Vector3 v1,v2,v3,v4;
							v1.x = v2.x = (x-0x40)*tilesize;
							v3.x = v4.x = (x-0x40+1)*tilesize;
							v1.y = v4.y = -(y-0x40)*tilesize;
							v2.y = v3.y = -(y-0x40+1)*tilesize;

							v1.z = heightmap[y*0x80+x];
							v2.z = heightmap[(y+1)*0x80+x];
							v3.z = heightmap[(y+1)*0x80+x+1];
							v4.z = heightmap[y*0x80+x+1];
							v1.z *= heightsize;
							v2.z *= heightsize;
							v3.z *= heightsize;
							v4.z *= heightsize;

							manOb->position(v1);
							manOb->textureCoord(0.0,0.0);

							manOb->position(v2);
							manOb->textureCoord(0.0,1.0);

							manOb->position(v3);
							manOb->textureCoord(1.0,1.0);

							manOb->position(v1);
							manOb->textureCoord(0.0,0.0);

							manOb->position(v3);
							manOb->textureCoord(1.0,1.0);

							manOb->position(v4);
							manOb->textureCoord(1.0,0.0);

							//manOb->quad(0,1,2,3);
							
						}
						manOb->end();
						Node->createChildSceneNode()->attachObject(manOb);
				}
	}

#endif
		delete[]tiledata;
	}
	void	ODMmap::AddBModelsToScene()
	{
		SceneNode *Node =  mSceneMgr->getRootSceneNode()->createChildSceneNode("ODMBModelsNode");
		for ( size_t j = 0; j < bmodels.size(); j++)
		{
			bmodel_t& bm = bmodels[j];
			ManualObject* manOb = mSceneMgr->createManualObject("ODMBModel" + StringConverter::toString( j));
			manOb->setVisibilityFlags(BMODEL_MASK);
			manOb->estimateVertexCount(bm.bmodel_hdr.num_vertex);
			manOb->setDynamic(false);
			//manOb->setCastShadows(true);
			//manOb->setBoundingBox(AxisAlignedBox(bm.bmodel_hdr.bbox.min.x,bm.bmodel_hdr.bbox.min.y,bm.bmodel_hdr.bbox.min.z,bm.bmodel_hdr.bbox.max.x,bm.bmodel_hdr.bbox.max.y,bm.bmodel_hdr.bbox.max.z));
			//manOb->setKeepDeclarationOrder(true);
			manOb->setRenderingDistance(2048*4*8);
			/*mm_int_vec3_s center;
			center.x = (bm.bmodel_hdr.bbox.max.x+bm.bmodel_hdr.bbox.min.x)/2;
			center.y = (bm.bmodel_hdr.bbox.max.y+bm.bmodel_hdr.bbox.min.y)/2;
			center.z = (bm.bmodel_hdr.bbox.max.z+bm.bmodel_hdr.bbox.min.z)/2;*/
			manOb->setBoundingBox(AxisAlignedBox(bm.bbox.getMinimum()-bm.origin,bm.bbox.getMaximum()-bm.origin));
			std::vector<std::string> tex_names;
			for( size_t i =0; i < bm.faces.size(); i++)
			{
				std::string texname=std::string("bitmaps/")+bm.faces_tex_names[i];
				if( std::find(tex_names.begin(),tex_names.end(),texname)==tex_names.end() )
					tex_names.push_back(texname);
			}
			for(size_t n =0; n<tex_names.size(); n++)
			{
				MaterialPtr material;
				std::string texname=tex_names[n];
				//TexturePtr texture = angel::GetLodTexture(texname);
				TexturePtr texture = angel::LodTextureManager::getSingleton().load(texname);
				std::string matname = texname+".Material";
				if(MaterialManager::getSingleton().resourceExists(matname) )
				{
					material=MaterialManager::getSingleton().getByName(matname);
				}else
				{
					material = MaterialManager::getSingleton().create(
						matname, // name
						ResourceGroupManager::DEFAULT_RESOURCE_GROUP_NAME);
					TextureUnitState* texstate = material->getTechnique(0)->getPass(0)->createTextureUnitState(texture->getName());
					//texstate->setTextureAddressingMode(TextureUnitState::TAM_MIRROR);
				}
				manOb->begin(matname, RenderOperation::OT_TRIANGLE_LIST);
				for( size_t i =0; i < bm.faces.size(); i++)
				{
					bmodel_face_odm_t face = bm.faces[i];
					std::string texname2=std::string("bitmaps/")+bm.faces_tex_names[i];
					if( texname != texname2 )
						continue;
					for( int k = 1; k < face.numv-1; k++)
					{
						for(int m = 0; m < 3;m++)
						{
							int index=(m)?k+m-1:0;
							mm_int_vec3_s& vec = bm.vertexes[face.v_idx[index]];
							Real u = Real(face.tex_dx + face.tex_x[index])/Real(texture->getWidth());
							Real v = Real(face.tex_dy + face.tex_y[index])/Real(texture->getHeight());
							//Real u = Real(face.tex_x[index])/Real(texture->getWidth());
							//Real v = Real(face.tex_y[index])/Real(texture->getHeight());
							manOb->position(vec.x-bm.origin.x,vec.y-bm.origin.y,vec.z-bm.origin.z);
							manOb->textureCoord(u,v);
						}
					}
				}
				manOb->end();
			}
			SceneNode * subnode = Node->createChildSceneNode();
			subnode->setPosition(bm.origin);
			subnode->attachObject(manOb);
			//Node->createChildSceneNode()->attachObject(manOb);
		}
	}
	void	ODMmap::AddSpawnToScene()
	{
		SceneNode *Node =  mSceneMgr->getRootSceneNode()->createChildSceneNode("Spawn");
		Entity *ent;
		
		for (size_t i =0 ; i< spawns.size(); i++)
		{
			SceneNode* headNode = Node->createChildSceneNode();
			ent = mSceneMgr->createEntity("Spawn" + StringConverter::toString(i),"cube.mesh");
			ent->setMaterialName("MmView/Spawn");
			ent->setVisibilityFlags(SPAWN_MASK);
			
			headNode->attachObject(ent);

			Real cubesize= ent->getBoundingBox().getMaximum().x - ent->getBoundingBox().getMinimum().x;
			Real radius = spawns[i].mm6spawn.radius;
			Vector3 vv=Vector3(spawns[i].mm6spawn.origin) + Vector3::UNIT_Z*cubesize/2;
			if(spawns[i].mm6spawn.origin.z == 0 )
			{
				int x = spawns[i].mm6spawn.origin.x/tilesize+0x40;
				int y = (-1*spawns[i].mm6spawn.origin.y/tilesize)+0x40;
				vv += Vector3::UNIT_Z* heightmap[y*0x80+x]*heightsize;
			}
			headNode->setPosition(vv);
			//headNode->scale(2,2,8);
//			spawns[i].bbox=AxisAlignedBox( vv+ Vector3(-cubesize,-cubesize,-cubesize*4),vv+ Vector3(+cubesize,+cubesize,+cubesize*4));
			spawns[i].bbox=AxisAlignedBox( vv+ Vector3(-cubesize/2,-cubesize/2,-cubesize/2),vv+ Vector3(+cubesize/2,+cubesize/2,+cubesize/2));
		}

	}
	void	ODMmap::AddEntsToScene()
	{
		SceneNode *Node =  mSceneMgr->getRootSceneNode()->createChildSceneNode("Entites");
		Entity *ent;
		

		for (size_t i =0 ; i< entites.size(); i++)
		{
			SceneNode* headNode = Node->createChildSceneNode();
			ent = mSceneMgr->createEntity("Entity" + StringConverter::toString(i),"cube.mesh");
			ent->setMaterialName("MmView/Entity");
			ent->setVisibilityFlags(ENTITY_MASK);
			

			headNode->attachObject(ent);
			Real cubesize= ent->getBoundingBox().getMaximum().x - ent->getBoundingBox().getMinimum().x;
			
			Vector3 vv=Vector3(entites[i].mm6ent.origin) + Vector3::UNIT_Z*cubesize/2;
			headNode->setPosition(vv);
			
			//headNode->scale(1,1,2);
			entites[i].bbox=AxisAlignedBox( vv+ent->getBoundingBox().getMinimum(),vv+ ent->getBoundingBox().getMaximum());
		}
	}
	void	ODMmap::AddToScene()
	{
		AddTerrainToScene();
		AddBModelsToScene();
		AddSpawnToScene();
		AddEntsToScene();
		SetMapInfoOverlay();

		//mSceneMgr->setAmbientLight(ColourValue(0.7, 0.7, 0.7));
		//устанавливаем камеру
		//mCamera->setPosition(60, 200, 70);
		//mCamera->lookAt(0,0,0);

		///$ProjectiveDecalApplication.createScene().setupHeads
		// создаём головы (названные head0, head1, etc.) по окружности
		/*Entity *ent;
		for (unsigned int i = 0; i < 6; i++)
		{
			SceneNode* headNode = mSceneMgr->getRootSceneNode()->createChildSceneNode();
			ent = mSceneMgr->createEntity("head" + StringConverter::toString(i),"ogrehead.mesh");
			headNode->attachObject(ent);
			Radian angle(i * Math::TWO_PI / 6);
			headNode->setPosition(75 * Math::Cos(angle), 0, 75 * Math::Sin(angle));
		}*/
	}
	void ODMmap::SetMapInfoOverlay()
	{
		/*Overlay*mMyOverlay = OverlayManager::getSingleton().getByName("MMView/MapOverlay");
		OverlayElement* guiDbg = OverlayManager::getSingleton().getOverlayElement("MMView/MMMap/Mapname");
		guiDbg->setCaption(String("Mapname:")+mapname);
		guiDbg = OverlayManager::getSingleton().getOverlayElement("MMView/MMMap/MapStats");
		guiDbg->setCaption(std::string("BModels:")+ StringConverter::toString(bmodels.size()));
		
		mMyOverlay->show();*/
		std::stringstream s;
		s << /*"Mapname: " <<*/ mapstats.GetString(1)<<"\n"/*"Mapfile:"*/ << mapname << "\nBModels: "<<bmodels.size();
		angel::Mapinfo::getInstance().SetText(s.str());
	}
	void    ODMmap::SelectBModel()
	{
		if( selected_bmodel_idx == -1  || selected_face_idx == -1)
		{
			DeselectBModel();
			return;
		}
		bmodel_t& bm= bmodels[selected_bmodel_idx];
		bmodel_face_odm_t& face=bm.faces[selected_face_idx];
		bm_face_t& ogre_face=bm.ogre_faces[selected_face_idx];
		bmodel_odm_t& bmhdr = bm.bmodel_hdr;

		selected_bmodel = mSceneMgr->getManualObject("ODMBModel" + StringConverter::toString( selected_bmodel_idx));
		SceneNode *Node=selected_bmodel->getParentSceneNode();
		Node->showBoundingBox(true);
		ManualObject* manOb = mSceneMgr->createManualObject("SelFace");
		manOb->setVisibilityFlags(BMODEL_MASK);
		manOb->setDynamic(true);
		manOb->begin("BLV/SelectedFace", RenderOperation::OT_TRIANGLE_LIST);

		for( int k = 1; k < face.numv-1; k++)
		{
			for(int m = 0; m < 3;m++)
			{
				int index=(m)?k+m-1:0;
				mm_int_vec3_s& vec = bm.vertexes[face.v_idx[index]];
				manOb->position(vec.x-bm.origin.x,vec.y-bm.origin.y,vec.z-bm.origin.z);
			}

		}
		manOb->end();
		Node->attachObject(manOb);

		Overlay*mMyOverlay = OverlayManager::getSingleton().getByName("MMView/ODMMapBModelInfoOverlay");
		mMyOverlay->show();

		std::stringstream s;
		s << "BModel#:\t"<< selected_bmodel_idx <<"\n";
		s << "BM Names:\t"<< bmhdr.name1 << "\t" << bmhdr.name2 <<"\n";
		s << "Attr:"<< std::hex << std::setw(8)<<std::setfill('0') << bmhdr.attrib <<"\t";
		s << std::dec;
		s << "Vertex: "<< bmhdr.num_vertex << "\tFaces: "<<bmhdr.num_faces <<"\n";
		s << "ConvexFacets: "<< bmhdr.unk02 <<"\tBSPNodes: "<<bmhdr.num3<<"\n";
		s << "BSPOffset: "<<bmhdr.unk03a<<"\tDecorNum:"<< bmhdr.unk03b <<"\n";
		s << "Center\tX: "<<bmhdr.unk03[0]<<"\tY: "<< bmhdr.unk03[1] <<"\n";
		s << "Origin1: "<<bmhdr.origin1.x<<"\t"<<bmhdr.origin1.y<<"\t"<<bmhdr.origin1.z<<"\n";
		s << "BBox1 min: "<<bmhdr.bbox.min.x<<"\t" <<bmhdr.bbox.min.y<<"\t"<<bmhdr.bbox.min.z<<"\n";
		s << "BBox1 max: "<<bmhdr.bbox.max.x<<"\t" <<bmhdr.bbox.max.y<<"\t"<<bmhdr.bbox.max.z<<"\n";
		s << "BBox2 min: "<<bmhdr.unk04[0]<<"\t"<<bmhdr.unk04[1]<<"\t"<<bmhdr.unk04[2]<<"\n";
		s << "BBox2 max: "<<bmhdr.unk04[3]<<"\t"<<bmhdr.unk04[4]<<"\t"<<bmhdr.unk04[5]<<"\n";
		s << "BoundCenter: "<<bmhdr.origin2.x<<"\t"<<bmhdr.origin2.y<<"\t"<<bmhdr.origin2.z<<"\n";
		s << "BoundRadius: "<< bmhdr.unk05 << "\n";
		OverlayManager::getSingleton().getOverlayElement("MMView/ODMMap/FBModelParams")->
			setCaption(s.str());


		s.str("");
		s << "Face#: "<<selected_face_idx <<"\t";

		s << "Texture: "<< bm.faces_tex_names[selected_face_idx];
		s << "\tAttr: " << std::hex << std::setw(8)<<std::setfill('0')  << (DWORD)face.attr << "\n";
		s << std::dec;
		s << "Numv: " <<(int)face.numv;
		s << "\tType: " << std::hex << std::setw(2)<<std::setfill('0')  <<(int)face.POLYGON_TYPE;
		s << "\tShade: " << std::hex << std::setw(2)<<std::setfill('0')  <<(int)face.SHADE;
		s << std::dec;
		s << "\nBmpIDx: " <<face.unk02;
		s << "\tUnkArr: " << std::hex << std::setw(4)<<std::setfill('0')  << (WORD)bm.unk_array[selected_face_idx]<<"\n";
		s << std::dec;
		/*s<< "Plane:\tv("<<face.plane.normal.x ;
		s << "\t"<<face.plane.normal.y;
		s << "\t"<<face.plane.normal.z;
		s << ")\tdist:"<<face.plane.dist << "\n";*/
		s<< "Plane: " << ogre_face.plane.normal;
		s<< "\nPlane dist: " << ogre_face.plane.d <<"\n";

		s << "BBox min: "<< ogre_face.bbox.getMinimum() << "\n";
		s << "BBox max: "<< ogre_face.bbox.getMaximum() << "\n";
		s << "Z_CALC: ";
		s << face.z_calc[0] <<"\t"<< face.z_calc[1] <<"\t"<< face.z_calc[2] <<"\t";
		s << face.z_calc[3] <<"\t"<< face.z_calc[4] <<"\t"<< face.z_calc[5] <<"\n";
		/*s <<std::hex << std::setw(8)<<std::setfill('0')<< face.Z_CALC1 <<" 2:";
		s <<std::hex << std::setw(8)<<std::setfill('0')<< face.Z_CALC2 <<" 3:";
		s <<std::hex << std::setw(8)<<std::setfill('0')<< face.Z_CALC3 <<"\n";*/
		/*s <<std::hex << face.Z_CALC1 /65536.0 <<" 2:";
		s <<std::hex << face.Z_CALC2 /65536.0 <<" 3:";
		s <<std::hex << face.Z_CALC3 /65536.0 <<"\n";*/

		s << std::dec;
		s <<"#COG: "<< face.COG_NUMBER;
		s <<"\t#EVT: "<< face.COG_TRIGGERED_NUMBER;
		s << "\tTRIGGER: "<< std::hex << std::setw(4)<<std::setfill('0')<< face.COG_TRIGGER<<"\t";
		s <<"\nReserved: "<< face.RESERVED;
		s << std::dec;

		s << "\nGradient: " <<(int)face.GRADIENT_VERTEXES[0]<<"\t";
		s << (int)face.GRADIENT_VERTEXES[1]<<"\t";
		s << (int)face.GRADIENT_VERTEXES[2]<<"\t";
		s << (int)face.GRADIENT_VERTEXES[3]<<"\n";
		s << std::hex << std::setw(2)<<std::setfill('0');
		s << "Visibility: " <<(int)face.VISIBILITY;
		s << "\tPADDING: " <<(int)face.PADDING[0]<< "\t"<<(int)face.PADDING[1]<<"\n";
		OverlayManager::getSingleton().getOverlayElement("MMView/ODMMap/BMFaceParams")->
			setCaption(s.str());
	}
	void    ODMmap::DeselectBModel()
	{

		if( selected_bmodel )
		{
			SceneNode *node=selected_bmodel->getParentSceneNode();
			if(node)
			   node->showBoundingBox(false);
		}
		selected_bmodel=NULL;
		mSceneMgr->destroyManualObject("SelFace");
		selected_bmodel_idx=selected_face_idx=-1;
		Overlay*mMyOverlay = OverlayManager::getSingleton().getByName("MMView/ODMMapBModelInfoOverlay");
		mMyOverlay->hide();
	}
	void    ODMmap::SelectEntity()
	{
		if( selected_ent_idx == -1 )
			return;
		Entity* ent_o = mSceneMgr->getEntity("Entity" + StringConverter::toString(selected_ent_idx));
		if( !ent_o )
		{
			angel::Log << "could not find entity " << selected_ent_idx <<angel::aeLog::endl;
		}else
		{
			ent_o->getParentSceneNode()->showBoundingBox(true);
		}
		Overlay*mMyOverlay = OverlayManager::getSingleton().getByName("MMView/ODMMapEntityInfoOverlay");
		mMyOverlay->show();
		std::stringstream s;
		ent_t& ent=entites[selected_ent_idx];
		s << "Entity#: "<< selected_ent_idx << "\t";
		s << "Name: "<< ent.name << "\n";
		s << "Origin: "<< ent.mm6ent.origin << "\n";

		s << "DecListId#: "<< ent.mm6ent.declist_id<< "\t";
		s << "AIattrMarkers: "<< ent.mm6ent.AIattrMarkers<< "\n";
		s << "Facing: "<< std::setw(4)<<std::setfill('0')  << ent.mm6ent.facing<< "\n";
		s << std::dec;

		s << "Evt1: "<< ent.mm6ent.evt1<< "\t";
		s << "Evt2: "<< ent.mm6ent.evt2<< "\n";
		s << "Var1: "<< ent.mm6ent.var1<< "\t";
		s << "Var2: "<< ent.mm6ent.var2<< "\n";
		if( version > 6)
		{
			s << "Spec Trig: "<< std::hex << std::setw(4)<<std::setfill('0')  << ent.spec_trig<< "\t";
			s << "padding: "<< std::hex << std::setw(4)<<std::setfill('0')  << ent.padding<< "\n";
		}

		OverlayManager::getSingleton().getOverlayElement("MMView/ODMMap/EntityParams")->
			setCaption(s.str());

	}
	void    ODMmap::DeselectEntity()
	{
		Overlay*mMyOverlay = OverlayManager::getSingleton().getByName("MMView/ODMMapEntityInfoOverlay");
		mMyOverlay->hide();
		if( selected_ent_idx == -1 )
			return;
		Entity* ent = mSceneMgr->getEntity("Entity" + StringConverter::toString(selected_ent_idx));
		if( !ent )
		{
			angel::Log << "could not find entity " << selected_ent_idx <<angel::aeLog::endl;
		}else
		{
			ent->getParentSceneNode()->showBoundingBox(false);
		}
		
		selected_ent_idx=-1;
	}
	void    ODMmap::SelectSpawn()
	{
		if( selected_spawn_idx == -1 )
			return;
		Entity* ent_o = mSceneMgr->getEntity("Spawn" + StringConverter::toString(selected_spawn_idx));
		if( !ent_o )
		{
			angel::Log << "could not find spawn " << selected_spawn_idx <<angel::aeLog::endl;
		}else
		{
			ent_o->getParentSceneNode()->showBoundingBox(true);
		}
		Overlay*mMyOverlay = OverlayManager::getSingleton().getByName("MMView/ODMMapSpawnInfoOverlay");
		mMyOverlay->show();
		std::stringstream s;
		spawn_t& swp=spawns[selected_spawn_idx];
		s << "Spawn#: "<< selected_spawn_idx << "\t";
		s << "index: "<< swp.mm6spawn.index << "\n";

		s << "Origin: "<< swp.mm6spawn.origin<< "\t";
		s << "Radius: "<< swp.mm6spawn.radius<< "\n";

		s << "Type_ID: "<< std::hex << std::setw(4)<<std::setfill('0')  << swp.mm6spawn.type_id<< "\t";
		s << "Attrib: "<< std::hex << std::setw(4)<<std::setfill('0')  << swp.mm6spawn.attrib<< "\n";
		if( version > 6)
		{
			s << "Group: "<< std::hex << std::setw(8)<<std::setfill('0')  << swp.group<< "\n";
			
		}
		OverlayManager::getSingleton().getOverlayElement("MMView/ODMMap/SpawnParams")->
			setCaption(s.str());
	}
	void    ODMmap::DeselectSpawn()
	{
		Overlay*mMyOverlay = OverlayManager::getSingleton().getByName("MMView/ODMMapSpawnInfoOverlay");
		mMyOverlay->hide();
		if( selected_spawn_idx == -1 )
			return;
		Entity* ent = mSceneMgr->getEntity("Spawn" + StringConverter::toString(selected_spawn_idx));
		if( !ent )
		{
			angel::Log << "could not find spawn " << selected_spawn_idx <<angel::aeLog::endl;
		}else
		{
			ent->getParentSceneNode()->showBoundingBox(false);
		}

		selected_spawn_idx=-1;

	}
	void ODMmap::Select( Ray ray)
	{
				Vector3 crosspoint;
				Real maxdist = 36000;
				DWORD vismask=mSceneMgr->getVisibilityMask();
				DeselectAll();

				for( size_t i =0; i < bmodels.size(); i++)
				{
					bmodel_t& bm= bmodels[i];
					if(bm.hide)
						continue;
					static std::pair<bool, Real> result;
					result = ray.intersects(bm.bbox);
					if(!result.first)
						continue;
					for(size_t j = 0; j< bm.faces.size();j++)
					{
						bmodel_face_odm_t& face=bm.faces[j];
						bm_face_t& ogre_face=bm.ogre_faces[j];
						result = ray.intersects(ogre_face.bbox);
						if(!result.first)
							continue;
						result = ray.intersects(ogre_face.plane);
						if(!result.first)
							continue;
						//Real dist=ogre_face.plane.getDistance(ray.getOrigin());
						Real dist=result.second;
						if( dist > maxdist)
							continue;
						if( ogre_face.plane.getDistance(ray.getOrigin()) < 0)
							continue;
						crosspoint= ray.getPoint(dist);
						mm_int_vec3_s v=bm.vertexes[face.v_idx[0]];
						Vector3 v1=Vector3(v.x,v.y,v.z)-crosspoint;
						v=bm.vertexes[face.v_idx[1]];
						Vector3 v2=Vector3(v.x,v.y,v.z)-crosspoint;

						Vector3 basenormal( v1.crossProduct(v2));
						bool q = true;
						for( int k = 1 ; k < face.numv; k++ )
						{
							v=bm.vertexes[face.v_idx[k]];
							Vector3 v3=Vector3(v.x,v.y,v.z)-crosspoint;
							v=bm.vertexes[face.v_idx[(k+1)%face.numv]];
							Vector3 v4=Vector3(v.x,v.y,v.z)-crosspoint;
							if( basenormal.dotProduct(v3.crossProduct(v4)) < 0 )
							{
								q=false;
								break;
							}
						}
						if(!q)
							continue;
						maxdist = dist;
						selected_bmodel_idx=(int)i;
						selected_face_idx=(int)j;
					}

				}
				if(vismask & ENTITY_MASK)
				for( size_t i =0; i < entites.size(); i++)
				{
					static std::pair<bool, Real> result;
					ent_t& ent=entites[i];
					//result = ray.intersects(Ogre::Sphere(Vector3(ent.mm6ent.origin),20));
					result = ray.intersects(ent.bbox);
					if(!result.first)
						continue;
					Real dist = (Ogre::Vector3(ent.mm6ent.origin)  - ray.getOrigin()).length();
					if( dist < maxdist )
					{
						DeselectAll();
						maxdist=dist;
						selected_ent_idx =(int) i;
					}
				}
				if(vismask & SPAWN_MASK)
				for( size_t i =0; i < spawns.size(); i++)
				{
					static std::pair<bool, Real> result;
					spawn_t& spw=spawns[i];
					//result = ray.intersects(Ogre::Sphere(Vector3(ent.mm6ent.origin),20));
					result = ray.intersects(spw.bbox);
					if(!result.first)
						continue;
					Real dist = result.second;
					if( dist < maxdist )
					{
						DeselectAll();
						maxdist=dist;
						selected_spawn_idx =(int) i;
					}
				}
				//SetODMMapFaceInfoOverlay();
				/*if(selected_face_idx == -1)
					return;*/
				SelectBModel();
				SelectEntity();
				SelectSpawn();
	}
	void ODMmap::DeselectAll()
	{
		DeselectBModel();
		DeselectEntity();
		DeselectSpawn();
	}
	void ODMmap::ToggleSelectedBModel()
	{
		if(selected_bmodel_idx  == -1 )
			return;
		bmodel_t& bm= bmodels[selected_bmodel_idx];
		if( bm.hide )
		{
			bm.hide=false;
			selected_bmodel->getParentSceneNode()->setVisible(true);
		}else
		{
			bm.hide=true;
			selected_bmodel->getParentSceneNode()->setVisible(false);
		}
	
	}
	void ODMmap::ToggleEnts()
	{
		DWORD vismask=mSceneMgr->getVisibilityMask();
		DeselectAll();

		if(!showents)
			mSceneMgr->setVisibilityMask(vismask|(SPAWN_MASK|ENTITY_MASK));
		else
			mSceneMgr->setVisibilityMask(vismask - (vismask&(SPAWN_MASK|ENTITY_MASK)));
		showents=!showents;
	}
	void ODMmap::ResetBmodels()
	{
		for( size_t i =0; i < bmodels.size(); i++)
		{
			bmodel_t& bm= bmodels[i];
			bm.hide=false;
			ManualObject*ob= mSceneMgr->getManualObject("ODMBModel" + StringConverter::toString( i));
			if(ob)
				ob->getParentSceneNode()->setVisible(true);

		}
	}
	void ODMmap::Save(std::string fname)
	{

	}


}