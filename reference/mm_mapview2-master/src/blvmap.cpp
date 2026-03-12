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
#include "blvmap.h"
#include "zlib.h"
#include <sstream>

namespace angel{

	bool    BLVmap::DetectBLVVersion()
	{
		DWORD		off = 0x88;
#define CHECK_OFF( xxx ) { angel::Log << angel::aeLog::debug <<boost::format( " off = %8x size = %8x")% off % (xxx) <<angel::aeLog::endl;\
	off += (xxx);if( off > datasize || off < 0 ) return false;}	

		{//Vertexs
			angel::Log.Print(angel::aeLog::LOG_DEBUG,"Vertex");
			num_vertex = *(int*)(data+off); off+=4;
			vertex_data = (short*)(data+off);
			CHECK_OFF( num_vertex*6 );
		}
		{//Faces
			angel::Log.Print(angel::aeLog::LOG_DEBUG,"Faces");
			num_faces = *(int*)(data+off);  off+=4;
			faces_array = data+off;
			CHECK_OFF( num_faces * facesize );
			facedatasize = *(int*)(data+0x68);
			facedata = (short*)( data+off );
			CHECK_OFF( facedatasize );

			facetextures = data + off;
			CHECK_OFF( num_faces *0x0a );

			numfaceparms = *(int*)(data+off);  off+=4;
			//faceparams1 = data +off;
			faceparams1  = (faceparams_blv_t*)(data+off);
			CHECK_OFF(numfaceparms *0x24);
			faceparams2 = data +off;
			CHECK_OFF(numfaceparms *0x0a);
		}
		{
			angel::Log.Print(angel::aeLog::LOG_DEBUG,"Sectors");
			num_sectors = *(int*)(data+off);off+=4;
			sectorsdata = data +off;
			CHECK_OFF(num_sectors*sectorsize);

			Rdatasize = *(int*)(data+0x6c);
			sectorsRdata = data + off;
			CHECK_OFF(Rdatasize);
			RLdatasize = *(int*)(data+0x70);
			sectorsRLdata = data + off;
			CHECK_OFF(RLdatasize);
		}
		{
			angel::Log.Print(angel::aeLog::LOG_DEBUG,"Sprites");
			num_sprites_hz = *(int*)(data+off); off+=4;
			num_sprites = *(int*)(data+off);off+=4;
			spritesdata = data + off;
			CHECK_OFF(num_sprites*spritesize);
			spritesnamesdata = (char*)(data + off);
			CHECK_OFF(0x20 * num_sprites);
		}
		{
			angel::Log.Print(angel::aeLog::LOG_DEBUG,"Lights");
			num_lights = *(int*)(data+off); off+=4;
			lightsdata = data + off;
			CHECK_OFF(num_lights*lightsize);
		}
		{
			angel::Log.Print(angel::aeLog::LOG_DEBUG,"Unk9");
			num_unk9 = *(int*)(data+off); off+=4;
			Unknown9data = data + off;
			CHECK_OFF(num_unk9*8);
		}
		{
			angel::Log.Print(angel::aeLog::LOG_DEBUG,"Spawn");
			num_spawn = *(int*)(data+off); off+=4;
			spawndata = data + off;
			CHECK_OFF(num_spawn*spawnsize);
		}
		{
			angel::Log.Print(angel::aeLog::LOG_DEBUG,"Outline");
			num_outline = *(int*)(data+off); off+=4;
			mapoutlinedata= data + off;
			CHECK_OFF(num_outline*0xc);
		}
		if( off != datasize )return false;
		return true;
	}
	bool    BLVmap::PrepareBLV()
	{
		angel::Log.Print(angel::aeLog::LOG_DEBUG,"Try BLV6");
		version		= 	 6;
		facesize	= 0x50;  
		sectorsize	= 0x74;
		spritesize	= 0x1c;
		lightsize	= 0x0C; 
		spawnsize	= 0x14;
		if( DetectBLVVersion() ) return true;

		angel::Log.Print(angel::aeLog::LOG_DEBUG,"Try BLV7");
		version		= 	 7;
		facesize	= 0x60;  
		sectorsize	= 0x74;
		spritesize	= 0x20;
		lightsize	= 0x10; 
		spawnsize	= 0x18;
		if( DetectBLVVersion() ) return true;

		angel::Log.Print(angel::aeLog::LOG_DEBUG,"Try BLV8");
		version		= 	 8;
		facesize	= 0x60;  
		sectorsize	= 0x78;
		spritesize	= 0x20;
		lightsize	= 0x14; 
		spawnsize	= 0x18;
		if( DetectBLVVersion() ) return true;
		return false;
	}
	void BLVmap::LoadSpawn(int num_spawn, BYTE* spawndata)
	{
		spawns.resize(num_spawn);
		for (int i = 0; i< num_spawn; i++)
		{
			spawns[i].mm6spawn = *(blv_spawn_t*)(spawndata+i*spawnsize);
			if( version > 6 )
				spawns[i].group = *(DWORD*)(spawndata+i*spawnsize + 0x14);
			else
				spawns[i].group = 0;
		}
	}
	void    BLVmap::LoadEnts(int num, BYTE* entdata,char*entnames)
	{
		entites.resize(num);
		for (int i = 0; i< num; i++)
		{
			entites[i].mm6ent= *(blv_ent_t*)(entdata+i*spritesize);
			if( version > 6 )
			{
				entites[i].spec_trig= *(WORD*)(entdata+i*spritesize + 0x1c);
				entites[i].padding= *(WORD*)(entdata+i*spritesize + 0x1c+2);
			}
			else
			{
				entites[i].spec_trig= 0;
				entites[i].padding= 0;
			}
			memcpy(entites[i].name, entnames+i*entname_size,entname_size);
		}
	}

	void BLVmap::LoadBLVMap( )
	{
		{// get vertexs
			vertexes.resize(num_vertex);
			mm_vertexes.resize(num_vertex);
			
			std::copy((mm_short_vec3_s*)vertex_data,(mm_short_vec3_s*)vertex_data+num_vertex,mm_vertexes.begin());

			for ( size_t i = 0; i < vertexes.size(); i++ )
			{
				vertexes[i].x = vertex_data[i*3+0];
				vertexes[i].y = vertex_data[i*3+1];
				vertexes[i].z = vertex_data[i*3+2];
			}
		}
		{//faces
			//faces.resize( num_faces );
			faces.reserve( num_faces );

			short  *v = ( short * ) facedata;

			for ( int i = 0; i < num_faces; i++ )
			{

//				face_t& face = faces[i];
				face_t  face;// = faces[i];
				std::copy((char*)facetextures + i * 0xa,(char*)facetextures + i * 0xa+0x0a,face.texture_name);
				face.texture_name[10]=0;

				face.texname = face.texture_name;
				BYTE* bindata = faces_array + i * facesize;
				if( version > 6) 
				{
					face.plane7 = *(mm_float_plane_s*)(bindata);
					face.blvhdr = *(face_blv_t*)(bindata +0x10);
					//face.plane = Ogre::Plane(face.plane7.normal.x,face.plane7.normal.y,face.plane7.normal.z,face.plane7.dist);
					//face.plane = face.plane7;
					face.plane = face.blvhdr.plane;
				}else
				{
					face.blvhdr = *(face_blv_t*)(bindata);
					face.plane7.normal.x = face.blvhdr.plane.normal.x/65536.0;
					face.plane7.normal.y = face.blvhdr.plane.normal.y/65536.0;
					face.plane7.normal.z = face.blvhdr.plane.normal.z/65536.0;
					face.plane7.dist	 = face.blvhdr.plane.dist/65536.0;
					//face.plane = Ogre::Plane(face.blvhdr.plane.normal.x/65536.0,face.blvhdr.plane.normal.y/65536.0,face.blvhdr.plane.normal.z/65536.0,face.blvhdr.plane.dist/65536.0);
					face.plane = face.blvhdr.plane;
				}
				face.bbox = face.blvhdr.bbox;//Ogre::AxisAlignedBox(face.blvhdr.bbox.minx,face.blvhdr.bbox.miny,face.blvhdr.bbox.minz,
												//face.blvhdr.bbox.maxx,face.blvhdr.bbox.maxy,face.blvhdr.bbox.maxz);

//				face.index = (int)i;

				int numv = face.blvhdr.numvertex;

				if( numv < 3 )
				{
					angel::Log << angel::aeLog::debug <<"Face " << i << " has  < 3 nodes off:"<< bindata - data << angel::aeLog::endl;
				}
				//face.numvertexs = numv;
				

				face.vertex_idxs.resize( numv +1);
				face.vertex_normal_x.resize( numv +1);
				face.vertex_normal_y.resize( numv +1);
				face.vertex_normal_z.resize( numv +1);
				face.vertex_tex_x.resize( numv + 1 );
				face.vertex_tex_y.resize( numv + 1 );

				memcpy(&face.vertex_idxs[0], v + (numv+1)* 0, numv*2 +2 );
				memcpy(&face.vertex_normal_x[0], v + (numv+1)* 1, numv*2 +2 );
				memcpy(&face.vertex_normal_y[0], v + (numv+1)* 2, numv*2 +2);
				memcpy(&face.vertex_normal_z[0], v + (numv+1)* 3, numv*2+2);
				memcpy(&face.vertex_tex_x[0], v + (numv+1)* 4, numv*2+2);
				memcpy(&face.vertex_tex_y[0], v + (numv+1)* 5, numv*2+2);

				face.fparm_index = face.blvhdr.fparm_index;//data_index;// *(WORD*)(face.bindata + 0x38);

				if( face.fparm_index  > numfaceparms )
					angel::Log << angel::aeLog::debug <<"Face " << i << " has invalid fparm_index = "<< face.fparm_index << angel::aeLog::endl;
//				face.blvfaceparam = *(faceparams_blv_t*)(faceparams1+face.fparm_index*0x24)
				face.blvfaceparam = faceparams1[face.fparm_index];
				std::copy(faceparams2+face.fparm_index*0xa,faceparams2+face.fparm_index*0xa+0xa,face.faceparams2);
				//face.tex_x = *(short*)(faceparams1+face.fparm_index*0x24+0x14);
				//face.tex_y = *(short*)(faceparams1+face.fparm_index*0x24+0x14 + 2);
//				face.offv = ((BYTE*)v) - data;
				v += ( numv + 1 ) * 6;
				faces.push_back(face);
			}

		}
		{
			LoadEnts(num_sprites,spritesdata,spritesnamesdata);
			LoadSpawn(num_spawn,spawndata);
		}

	}
	BLVmap::BLVmap( pLodData loddata, const char *fname, SceneManager *_mSceneMgr ):
	    ldata(loddata),data(&(*loddata)[0]),datasize(loddata->size()),selected_face_index(-1),showportals(false),mSceneMgr(_mSceneMgr),
		showents(true),selected_ent_idx(-1),selected_spawn_idx(-1),mapstats(fname)
	{
		BLVNodeName="BLVNode";
		angel::Log <<  "Load BLVmap " <<  fname << angel::aeLog::endl;
		if(!PrepareBLV() )
		{
			throw error ("Cannot detect blv version with pak version 7\n");
		};

/*		BYTE*mdata=&((*loddata)[0]);


		if ( *( DWORD * ) ( mdata ) == 0x16741 && *( DWORD * ) ( mdata + 4 ) == 0x6969766d )
		{
			int psize = *( int * ) ( mdata + 8 );

			if ( psize + 0x10 != loddata->size() )
				throw error ("invalid blv7 file\n");
			datasize = *( int * ) ( mdata + 12 );
			data = new BYTE[datasize];

			if ( uncompress( data, &datasize, mdata + 0x10, psize ) != Z_OK )
			{
				delete[]data;
				data = NULL;
				throw error ("Cannot uncompress blv7\n");
			}

			if(!PrepareBLV() )
			{
				delete[] data;
				throw error ("Cannot detect blv version with pak version 7\n");
			};
			if( version < 7 )
				angel::Log << "Warning blv" << version <<"  map  in pak version 7+" <<angel::aeLog::endl;
		} else
		{
			int psize = *( int * ) ( mdata );

			if ( psize + 0x8 != loddata->size() )
				throw error ("invalid blv6 file\n");
			datasize  = *( int * ) ( mdata + 4 );
			data = new BYTE[datasize];

			if ( uncompress( data, &datasize, mdata + 0x8, psize ) != Z_OK )
			{
				delete[]data;
				data = NULL;
				throw error ("Cannot uncompress blv6\n");
			}
			if(!PrepareBLV() )
			{
				delete[] data;
				throw error ("Cannot detect blv version with pak version 6\n");
			};
			if( version != 6 )
				angel::Log << "Warning blv" << version <<"  map  in pak version 6" <<angel::aeLog::endl;
		}*/
		LoadBLVMap( );
		mapname = fname;
		
		angel::Log <<  "Loaded faces: " << faces.size() << ", vertexs: " << vertexes.size() << angel::aeLog::endl;
	}
	void BLVmap::SetMapInfoOverlay()
	{
/*		Overlay*mMyOverlay = OverlayManager::getSingleton().getByName("MMView/MapOverlay");
		OverlayElement* guiDbg = OverlayManager::getSingleton().getOverlayElement("MMView/MMMap/Mapname");
		guiDbg->setCaption(String("Mapname:")+mapname);
		guiDbg = OverlayManager::getSingleton().getOverlayElement("MMView/MMMap/MapStats");
		guiDbg->setCaption(std::string("Faces:")+ StringConverter::toString(faces.size()) + ", vertexs: "  +StringConverter::toString(vertexes.size()));
		
		mMyOverlay->show();*/
		std::stringstream s;
		s << /*"Mapname: " <<*/ mapstats.GetString(1)<<"\n"/*"Mapfile:"*/ << mapname << "\nFaces: "<<faces.size() << ", vertexs: " <<vertexes.size();
		angel::Mapinfo::getInstance().SetText(s.str());

	}
	void	BLVmap::AddSpawnToScene()
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
			headNode->setPosition(vv);
			//headNode->scale(2*radius/cubesize,2*radius/cubesize,2*radius/cubesize);
			spawns[i].bbox=AxisAlignedBox( vv+ Vector3(-cubesize/2,-cubesize/2,-cubesize/2),vv+ Vector3(+cubesize/2,+cubesize/2,+cubesize/2));
		}

	}
	void	BLVmap::AddEntsToScene()
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
			Vector3 vv=Vector3(entites[i].mm6ent.origin) + Vector3::UNIT_Z*ent->getBoundingRadius();
			headNode->setPosition(vv);

			//entites[i].bbox=AxisAlignedBox( vv+ent->getBoundingBox().getMinimum(),vv+ ent->getBoundingBox().getMaximum());

			//headNode->scale(1,1,2);
			entites[i].bbox=AxisAlignedBox( vv+ent->getBoundingBox().getMinimum(),vv+ ent->getBoundingBox().getMaximum());
		}
	}

	void BLVmap::AddPortalsToScene()
	{
		//MaterialPtr material=MaterialManager::getSingleton().getByName("BLV/Portal");
		SceneNode *Node =  mSceneMgr->getRootSceneNode()->createChildSceneNode("BLVPortalNode");
		ManualObject* manOb = mSceneMgr->createManualObject("BLVPortals");
		manOb->setVisibilityFlags(PORTALS_MASK);
		manOb->setDynamic(true);
		manOb->begin("BLV/Portal", RenderOperation::OT_TRIANGLE_LIST);
		for( std::vector<face_t>::iterator i = faces.begin(); i != faces.end(); ++i)
		{
			face_t &face = *i;
			if( !isPortal(face) )
				continue;
			if(face.blvhdr.numvertex <3 )
				continue;
			for( int j = 1 ; j < face.blvhdr.numvertex -1; j++ )
			{
				/*mm_short_vec3_s v0 = vertexes[face.vertex_idxs[0]];
				mm_short_vec3_s v1 = vertexes[face.vertex_idxs[j]];
				mm_short_vec3_s v2 = vertexes[face.vertex_idxs[j+1]];*/
				/*float tu0 = Real(face.tex_x + face.vertex_tex_x[0]) / texw;
				float tv0 = Real(face.tex_y + face.vertex_tex_y[0]) / texh;
				float tu1 = Real(face.tex_x + face.vertex_tex_x[j]) / texw;
				float tv1 = Real(face.tex_y + face.vertex_tex_y[j]) / texh;
				float tu2 = Real(face.tex_x + face.vertex_tex_x[j+1]) / texw;
				float tv2 = Real(face.tex_y + face.vertex_tex_y[j+1]) / texh;*/
				//manOb->position(v0.x,v0.y,v0.z);
				manOb->position(vertexes[face.vertex_idxs[0]]);
				//manOb->textureCoord(tu0,tv0);
				//manOb->position(v1.x,v1.y,v1.z);
				manOb->position(vertexes[face.vertex_idxs[j]]);
				//manOb->textureCoord(tu1,tv1);
				//manOb->position(v2.x,v2.y,v2.z);
				manOb->position(vertexes[face.vertex_idxs[j+1]]);
				//manOb->textureCoord(tu2,tv2);
				//manOb->normal(face.vertex_normal_x[j],face.vertex_normal_y[j],face.vertex_normal_z[j]);
			}
		}
		manOb->end();
		Node->attachObject(manOb);
	}
	void BLVmap::AddToScene()
	{
		//String materialName="";
		AddSpawnToScene();
		AddEntsToScene();
		SetMapInfoOverlay();
		AddPortalsToScene();
		mSceneMgr->setVisibilityMask(DWORD(-1) - (DWORD(-1)&PORTALS_MASK));
		SceneNode *blvNode =  mSceneMgr->getRootSceneNode()->createChildSceneNode(BLVNodeName);
#if 1
        int faceidx=0;
		std::vector<std::string> tex_names;
		for( size_t i =0; i < faces.size(); i++)
		{
			face_t &face = faces[i];
			if( isPortal(face) )
				continue;
			if(face.blvhdr.numvertex<3 )
				continue;

			std::string texname=std::string("bitmaps/")+face.texname;
			if( std::find(tex_names.begin(),tex_names.end(),texname)==tex_names.end() )
				tex_names.push_back(texname);
		}
		for(size_t tn =0;tn<tex_names.size();tn++)
		{
			std::string texname=tex_names[tn];

			//TexturePtr texture = angel::GetLodTexture(texname);
			TexturePtr texture = LodTextureManager::getSingleton().load(texname);
			int texw = (int)texture->getWidth();
			int texh = (int)texture->getHeight();

			//load texture
			MaterialPtr material;
			std::string matname=texname+".Material";
			if(MaterialManager::getSingleton().resourceExists(matname) )
			{
				material=MaterialManager::getSingleton().getByName(matname);
			}else
			{
				material = MaterialManager::getSingleton().create(
				matname, // name
				ResourceGroupManager::DEFAULT_RESOURCE_GROUP_NAME);
				material->getTechnique(0)->getPass(0)->createTextureUnitState(texture->getName());
				//material->setAmbient(0.5,0.5,0.5);
				//material->getTechnique(0)->getPass(0)->setSceneBlending(SBT_TRANSPARENT_ALPHA);
			}
			

			char name[0x20];
			sprintf_s(name,sizeof(name),"FaceOb%6d",tn);
			ManualObject* manOb = mSceneMgr->createManualObject(name);
			manOb->setVisibilityFlags(WALLS_MASK);
			manOb->setDynamic(false);
			manOb->begin(matname, RenderOperation::OT_TRIANGLE_LIST);
			for( std::vector<face_t>::iterator i = faces.begin(); i != faces.end(); ++i)
			{
				face_t &face = *i;
				if( isPortal(face) )
					continue;
				if(face.blvhdr.numvertex <3 )
					continue;
				std::string texname2=std::string("bitmaps/")+face.texname;
				if( texname2 != texname )
					continue;
				//LoadTexture(face);
				
				for( int j = 1 ; j < face.blvhdr.numvertex -1; j++ )
				{
/*					mm_short_vec3_s v0 = vertexes[face.vertex_idxs[0]];
					mm_short_vec3_s v1 = vertexes[face.vertex_idxs[j]];
					mm_short_vec3_s v2 = vertexes[face.vertex_idxs[j+1]];*/
					float tu0 = Real(face.blvfaceparam.tex_u + face.vertex_tex_x[0]) / texw;
					float tv0 = Real(face.blvfaceparam.tex_v + face.vertex_tex_y[0]) / texh;
					float tu1 = Real(face.blvfaceparam.tex_u + face.vertex_tex_x[j]) / texw;
					float tv1 = Real(face.blvfaceparam.tex_v + face.vertex_tex_y[j]) / texh;
					float tu2 = Real(face.blvfaceparam.tex_u + face.vertex_tex_x[j+1]) / texw;
					float tv2 = Real(face.blvfaceparam.tex_v + face.vertex_tex_y[j+1]) / texh;
					//manOb->position(v0.x,v0.y,v0.z);
					manOb->position(vertexes[face.vertex_idxs[0]]);
					manOb->textureCoord(tu0,tv0);
					//manOb->position(v1.x,v1.y,v1.z);
					manOb->position(vertexes[face.vertex_idxs[j]]);
					manOb->textureCoord(tu1,tv1);
					//manOb->position(v2.x,v2.y,v2.z);
					manOb->position(vertexes[face.vertex_idxs[j+1]]);
					manOb->textureCoord(tu2,tv2);

/*					//manOb->position(v0.x,v0.y,v0.z);
					manOb->position(face.vertex_idxs[0]);
					manOb->textureCoord(tu0,tv0);
					//manOb->position(v1.x,v1.y,v1.z);
					manOb->position(face.vertex_idxs[j]);
					manOb->textureCoord(tu1,tv1);
					//manOb->position(v2.x,v2.y,v2.z);
					manOb->position(face.vertex_idxs[j+1]);
					manOb->textureCoord(tu2,tv2);*/
					//manOb->normal(face.vertex_normal_x[j],face.vertex_normal_y[j],face.vertex_normal_z[j]);
				}
			}
			manOb->end();
			SceneNode* subnode = blvNode->createChildSceneNode();
			subnode->attachObject(manOb);
		}
#else
        int faceidx=0;
		for( std::vector<face_t>::iterator i = faces.begin(); i != faces.end(); ++i,++faceidx)
		{
			face_t &face = *i;
			if( isPortal(face) )
				continue;
			if(face.numvertexs <3 )
				continue;
            char name[0x20];
			sprintf(name,"FaceOb%6d",faceidx);
			ManualObject* manOb = mSceneMgr->createManualObject(name);
			manOb->setDynamic(false);
			//manOb->setDynamic(true);
			
			LoadTexture(face);
//#define blvUSE_VBO
#ifdef blvUSE_VBO
			manOb->begin(face.matname, RenderOperation::OT_TRIANGLE_LIST);
#else
			manOb->begin(face.matname, RenderOperation::OT_TRIANGLE_FAN);
#endif
			/*Vector3 center((face.bbox.maxs.x+face.bbox.mins.x)/2,
						   (face.bbox.maxs.y+face.bbox.mins.y)/2,
						   (face.bbox.maxs.z+face.bbox.mins.z)/2);*/
			for( int j =0 ; j < face.numvertexs; j++ )
			{
				vec3_t v = vertexes[face.vertex_idxs[j]];
				
				float tu = Real(face.tex_x + face.vertex_tex_x[j]) / face.texw;
				float tv = Real(face.tex_y + face.vertex_tex_y[j]) / face.texh;
				//manOb->position(v.x-center.x,v.y-center.y,v.z-center.z);
				manOb->position(v.x,v.y,v.z);
				manOb->textureCoord(tu,tv);
//				manOb->index(j);
				//manOb->normal(face.vertex_normal_x[j],face.vertex_normal_y[j],face.vertex_normal_z[j]);

			}
#ifdef blvUSE_VBO
			for( int j =1 ; j < face.numvertexs -1 ; j++ )
			{
				manOb->index(0);
				manOb->index(j);
				manOb->index(j+1);
			}
#endif
			manOb->end();
#if 0
			sprintf(name,"FaceMesh%6d",faceidx);
			
			MeshPtr mPtr= manOb->convertToMesh(name);
			//mPtr->_setBounds(AxisAlignedBox(face.bbox.mins[0],face.bbox.mins[1],face.bbox.mins[2],face.bbox.maxs[0],face.bbox.maxs[1],face.bbox.maxs[2]));
			char entname[0x20];
			sprintf(entname,"FaceEnt%6d",faceidx);
			Entity* ent = mSceneMgr->createEntity( entname, name );
			blvNode->createChildSceneNode()->attachObject(ent);
#else
			SceneNode* subnode = blvNode->createChildSceneNode();
			//subnode->setPosition(center);
			subnode->attachObject(manOb);
#endif
		}
#endif
		
	}
	void	BLVmap::LoadTexture(face_t& face)
	{
			//TexturePtr texture = angel::GetLodTexture(std::string("bitmaps/")+face.texname);
		    TexturePtr texture = angel::LodTextureManager::getSingleton().load(std::string("bitmaps/")+face.texname);

			face.texw = (int)texture->getWidth();
			face.texh = (int)texture->getHeight();

			//load texture
			MaterialPtr material;
			face.matname=face.texname+".Material";
			if(MaterialManager::getSingleton().resourceExists(face.matname) )
			{
				material=MaterialManager::getSingleton().getByName(face.matname);
			}else
			{
				material = MaterialManager::getSingleton().create(
				face.matname, // name
				ResourceGroupManager::DEFAULT_RESOURCE_GROUP_NAME);
				material->getTechnique(0)->getPass(0)->createTextureUnitState(texture->getName());
				//material->setAmbient(0.5,0.5,0.5);
				//material->getTechnique(0)->getPass(0)->setSceneBlending(SBT_TRANSPARENT_ALPHA);
			}
	}
	void BLVmap::TogglePortals()
	{
		DWORD vismask=mSceneMgr->getVisibilityMask();

		if(!showportals)
			mSceneMgr->setVisibilityMask(vismask|PORTALS_MASK);
		else
			mSceneMgr->setVisibilityMask(vismask - (vismask&PORTALS_MASK));
		showportals=!showportals;
	}
	void BLVmap::ToggleEnts()
	{
		DWORD vismask=mSceneMgr->getVisibilityMask();
		DeselectAll();

		if(!showents)
			mSceneMgr->setVisibilityMask(vismask|(SPAWN_MASK|ENTITY_MASK));
		else
			mSceneMgr->setVisibilityMask(vismask - (vismask&(SPAWN_MASK|ENTITY_MASK)));
		showents=!showents;
	}

	BLVmap::~BLVmap()
	{
		DeselectAll();
		if( data )
			delete[]data;

		vertexes.clear();
		faces.clear();
		//OverlayManager::getSingleton().getByName("MMView/MapOverlay")->hide();
		OverlayManager::getSingleton().getByName("MMView/BLVMapFaceInfoOverlay")->hide();
	}
#if 0
	void BLVmap::SetBLVMapFaceInfoOverlay()
	{
		Overlay*mMyOverlay = OverlayManager::getSingleton().getByName("MMView/BLVMapFaceInfoOverlay");
		if( selected_face_index == -1 )
		{
			mMyOverlay->hide();
			return;
		}
		face_t& face=faces[selected_face_index];
		face_blv_t			facehdr = face.blvhdr;
		faceparams_blv_t faceparams = face.blvfaceparam;

		mMyOverlay->show();
/*		OverlayManager::getSingleton().getOverlayElement("MMView/MMBLVMap/FaceParamHeaders")->
			setCaption("Texture\nBBox\n\nPlane\n\nAttributes\nZ_CALC 1,2,3\nFacet type\nBitmapIndex\nRooms\nPadding\n"
			"FParamIdx\nFade\nFadebase: x y\nFPIdx:Facet,Bitmap\nTexFrmTbl:Idx,COG\n"
			"COG: idx,evt,type\nLightLevel:"
			);*/
		std::stringstream s;
		s << "Face#: "<<selected_face_index <<"\t";
		s<< "Texture: " <<face.texture_name;
		s << "\tAttr:"<<std::hex << std::setw(8)<<std::setfill('0')<< facehdr.attrib <<"\n";
		s << std::dec ;
		s<< "BBox max:\t" <<face.bbox.getMinimum() << "\nBBox min:\t" << face.bbox.getMaximum() <<"\n";
		s<< "Plane:\t"<<face.plane.normal << "\nPlane dist:\t"<< face.plane.d <<"\n";
		s<< "PlaneI:\t"<<facehdr.plane<<"\n";
/*		s << "Z_CALC 1:";
		s <<std::hex << std::setw(8)<<std::setfill('0')<< facehdr.Z_CALC1 <<"\t2:";
		s <<std::hex << std::setw(8)<<std::setfill('0')<< facehdr.Z_CALC2 <<"\t3:";
		s <<std::hex << std::setw(8)<<std::setfill('0')<< facehdr.Z_CALC3 <<"\n";*/
		s << "Z_CALC: ";
		s << facehdr.z_calc[0] <<"\t"<< facehdr.z_calc[1] <<"\t"<< facehdr.z_calc[2] <<"\t";
		s << facehdr.z_calc[3] <<"\t"<< facehdr.z_calc[4] <<"\t"<< facehdr.z_calc[5] <<"\n";


		s <<"FacetType: " <<std::hex << std::setw(2)<<std::setfill('0')<< (DWORD)facehdr.facet_type<<"\t";
		s << std::dec ;
		s << "BitmapIdx: "<<facehdr.bitmap_index <<"\n";

		s << "Room: "<<facehdr.room_number <<"\tRoom behind: " <<facehdr.room_behind_number;
		s <<"\tPadding: "<< (int)facehdr.padding[0] <<"\t" << (int)facehdr.padding[1] <<"\n";
		s << "Fparm idx: "<<facehdr.fparm_index;
		s << "\tFacetIdx: "<<faceparams.facet_index;
		s << "\tBitmapIdx: "<< faceparams.bitmap_index <<"\n";

		s << "Fade X: "<< faceparams.fade.x << "\tY: "<< faceparams.fade.y << "\tZ: "<< faceparams.fade.z <<"\n";
		s << "Fade base X: "<< faceparams.fade_base_x << "\tY: " << faceparams.fade_base_y << "\n";
		s << "TextureFrameTbl idx: "<< faceparams.texture_frame_table_index;
		s << "\tCOG: " <<faceparams.texture_frame_table_COG <<"\n";
		s <<"#COG: "<< faceparams.cog_number;
		s <<"\t#EVT: "<< faceparams.cog_triggered;
		s << "\tType: "<< std::hex << std::setw(4)<<std::setfill('0')<< faceparams.cog_trigger_type <<"\n";
		s << std::dec ;
		s << "Light level: "<< faceparams.light_level <<"\n";
		OverlayManager::getSingleton().getOverlayElement("MMView/MMBLVMap/FaceParamData")->setCaption(s.str());
			

	}
#endif
	void BLVmap::DeselectAll()
	{
		DeselectFace();
		DeselectSpawn();
		DeselectEntity();
	}
	void BLVmap::SelectFace()
	{
		//SetBLVMapFaceInfoOverlay();
		if( selected_face_index== -1)
		{
			DeselectFace();
			return;
		}
		face_t &face = faces[selected_face_index];

		//angel::Log << "select face " << selected_face_index << " "<< face.texture_name <<angel::aeLog::endl;

		SceneNode *Node;
		if( mSceneMgr->hasSceneNode("SelFaceNode"))
			Node = mSceneMgr->getSceneNode("SelFaceNode");
		else
			Node =  mSceneMgr->getRootSceneNode()->createChildSceneNode("SelFaceNode");


		ManualObject* manOb = mSceneMgr->createManualObject("SelFace");

		manOb->setDynamic(true);
		if(isPortal(face))
		{
			manOb->begin("BLV/SelectedPortal", RenderOperation::OT_TRIANGLE_LIST);
			manOb->setVisibilityFlags(PORTALS_MASK);
		}
		else
		{
			manOb->setVisibilityFlags(WALLS_MASK);
			manOb->begin("BLV/SelectedFace", RenderOperation::OT_TRIANGLE_LIST);
		}

		for( int j = 1 ; j < face.blvhdr.numvertex -1; j++ )
		{
			manOb->position(vertexes[face.vertex_idxs[0]]);
			manOb->position(vertexes[face.vertex_idxs[j]]);
			manOb->position(vertexes[face.vertex_idxs[j+1]]);
		}
		manOb->end();
		Node->attachObject(manOb);
		face_blv_t			facehdr = face.blvhdr;
		faceparams_blv_t faceparams = face.blvfaceparam;
		Overlay*mMyOverlay = OverlayManager::getSingleton().getByName("MMView/BLVMapFaceInfoOverlay");
		mMyOverlay->show();
		std::stringstream s;
		s << "Face#: "<<selected_face_index <<"\t";
		s<< "Texture: " <<face.texture_name;
		s << "\tAttr:"<<std::hex << std::setw(8)<<std::setfill('0')<< facehdr.attrib <<"\n";
		s << std::dec ;
		s<< "BBox max:\t" <<face.bbox.getMinimum() << "\nBBox min:\t" << face.bbox.getMaximum() <<"\n";
		s<< "Plane:\t"<<face.plane.normal << "\nPlane dist:\t"<< face.plane.d <<"\n";
		//s<< "PlaneI:\t"<<facehdr.plane<<"\n";
		s<< "Plane7:\t"<<face.plane7<<"\n";
		s << "Z_CALC: ";
		s << facehdr.z_calc[0] <<"\t"<< facehdr.z_calc[1] <<"\t"<< facehdr.z_calc[2] <<"\t";
		s << facehdr.z_calc[3] <<"\t"<< facehdr.z_calc[4] <<"\t"<< facehdr.z_calc[5] <<"\n";


		s <<"FacetType: " <<std::hex << std::setw(2)<<std::setfill('0')<< (DWORD)facehdr.facet_type<<"\t";
		s << std::dec ;
		s << "BitmapIdx: "<<facehdr.bitmap_index <<"\n";

		s << "Room: "<<facehdr.room_number <<"\tRoom behind: " <<facehdr.room_behind_number;
		s <<"\tPadding: "<< (int)facehdr.padding[0] <<"\t" << (int)facehdr.padding[1] <<"\n";
		s << "Fparm idx: "<<facehdr.fparm_index;
		s << "\tFacetIdx: "<<faceparams.facet_index;
		s << "\tBitmapIdx: "<< faceparams.bitmap_index <<"\n";

		s << "Fade X: "<< faceparams.fade.x << "\tY: "<< faceparams.fade.y << "\tZ: "<< faceparams.fade.z <<"\n";
		s << "Fade base X: "<< faceparams.fade_base_x << "\tY: " << faceparams.fade_base_y << "\n";
		s << "TextureFrameTbl idx: "<< faceparams.texture_frame_table_index;
		s << "\tCOG: " <<faceparams.texture_frame_table_COG <<"\n";
		s <<"#COG: "<< faceparams.cog_number;
		s <<"\t#EVT: "<< faceparams.cog_triggered;
		s << "\tType: "<< std::hex << std::setw(4)<<std::setfill('0')<< faceparams.cog_trigger_type <<"\n";
		s << std::dec ;
		s << "Light level: "<< faceparams.light_level <<"\n";
		OverlayManager::getSingleton().getOverlayElement("MMView/MMBLVMap/FaceParamData")->setCaption(s.str());

	}
	void BLVmap::DeselectFace()
	{
		Overlay*mMyOverlay = OverlayManager::getSingleton().getByName("MMView/BLVMapFaceInfoOverlay");
		mMyOverlay->hide();
		mSceneMgr->destroyManualObject("SelFace");
		selected_face_index=-1;
	}
	void    BLVmap::SelectEntity()
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
	void    BLVmap::DeselectEntity()
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
	void    BLVmap::SelectSpawn()
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
	void    BLVmap::DeselectSpawn()
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

	void BLVmap::Select( Ray ray)
	{
		Vector3 crosspoint;
		Real maxdist = 36000;
		DWORD vismask=mSceneMgr->getVisibilityMask();

		DeselectAll();

		for( size_t i =0; i < faces.size(); i++)
		{
			face_t &face = faces[i];
			if( !showportals && isPortal(face) )
				continue;
			if(face.blvhdr.numvertex <3 )
				continue;
			static std::pair<bool, Real> result;
			result = ray.intersects(face.bbox);
			if(!result.first)
				continue;
			result = ray.intersects(face.plane);
			if(!result.first)
				continue;
			Real dist=result.second;
			//Real dist=face.plane.getDistance(ray.getOrigin());
			if( !isPortal(face) &&  face.plane.getDistance(ray.getOrigin())< 0)
				continue;
			crosspoint= ray.getPoint(dist);

			Vector3 v1=vertexes[face.vertex_idxs[0]]-crosspoint;
			Vector3 v2=vertexes[face.vertex_idxs[1]]-crosspoint;

			Vector3 basenormal( v1.crossProduct(v2));
			bool q = true;
			for( int j = 1 ; j < face.blvhdr.numvertex; j++ )
			{
				Vector3 v3=vertexes[face.vertex_idxs[j]]-crosspoint;
				Vector3 v4=vertexes[face.vertex_idxs[(j+1)%face.blvhdr.numvertex]]-crosspoint;
				if( basenormal.dotProduct(v3.crossProduct(v4)) < 0 )
				{
					q=false;
					break;
				}
			}
			if(!q)
				continue;
			if( dist > maxdist)
				continue;
			maxdist = dist;
			selected_face_index = (int)i;
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

				SelectFace();
				SelectEntity();
				SelectSpawn();
	}
}