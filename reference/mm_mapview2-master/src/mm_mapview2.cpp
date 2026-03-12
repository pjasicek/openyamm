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
#include "selectmapdialog.h"
#include <Shlobj.h>
#include "StatisticInfo.h"


#if OGRE_PLATFORM == OGRE_PLATFORM_APPLE
#include <CoreFoundation/CoreFoundation.h>

// This function will locate the path to our application on OS X,
// unlike windows you can not rely on the curent working directory
// for locating your configuration files and resources.
std::string macBundlePath(  )
{
	char    path[1024];
	CFBundleRef mainBundle = CFBundleGetMainBundle(  );

	assert( mainBundle );

	CFURLRef mainBundleURL = CFBundleCopyBundleURL( mainBundle );

	assert( mainBundleURL );

	CFStringRef cfStringRef =
	    CFURLCopyFileSystemPath( mainBundleURL, kCFURLPOSIXPathStyle );
	assert( cfStringRef );

	CFStringGetCString( cfStringRef, path, 1024, kCFStringEncodingASCII );

	CFRelease( mainBundleURL );
	CFRelease( cfStringRef );

	return std::string( path );
}
#endif

class   MMMapviewApp:public FrameListener, public WindowEventListener,
    public OIS::KeyListener, public OIS::MouseListener {
      public:
	MMMapviewApp(  );
	virtual ~ MMMapviewApp(  );
	virtual void go( void );
	virtual void windowResized( RenderWindow * rw );
	virtual void windowClosed( RenderWindow * rw );
	virtual bool windowClosing( RenderWindow * rw );
	virtual void moveCamera(  );
	virtual void showDebugOverlay( bool show );
	bool frameRenderingQueued( const FrameEvent & evt );
	bool frameStarted( const FrameEvent & evt );
	bool frameEnded( const FrameEvent & evt );
	virtual bool mouseMoved( const OIS::MouseEvent & arg );
	virtual bool mousePressed( const OIS::MouseEvent & arg, OIS::MouseButtonID id );
	virtual bool mouseReleased( const OIS::MouseEvent & arg, OIS::MouseButtonID id );
	bool keyPressed( const OIS::KeyEvent & e );
	bool keyReleased( const OIS::KeyEvent & e );
	void ToggleHelpOverlay(  );

      protected:
    MyGUI::Gui * mGUI;
	Root * mRoot;
	Camera *mCamera;
	SceneManager *mSceneMgr;
	RenderWindow *mWindow;
	angel::LodTextureManager* mLTM;

	Ogre::String mResourcePath;

	Vector3 mTranslateVector;
	Real mCurrentSpeed;
	bool mStatsOn;

	std::string mDebugText;

	unsigned int mNumScreenShots;
	float mMoveScale;
	float mSpeedLimit;
	Degree mRotScale;

	// just to stop toggles flipping too fast
	Real mTimeUntilNextToggle;
	Radian mRotX, mRotY;
	TextureFilterOptions mFiltering;
	int mAniso;

	int mSceneDetailIndex;
	Real mMoveSpeed;
	Degree mRotateSpeed;
	Overlay *mDebugOverlay;
	Overlay *mMyOverlay;
	demo::Console * mConsole;
	bool mlook;
	statistic::StatisticInfo * mInfo;
	angel::CopyrightInfo*mCInfo;
	angel::Mapinfo* mMapinfo;

	//OIS Input devices
	OIS::InputManager * mInputManager;
	OIS::Mouse * mMouse;
	OIS::Keyboard * mKeyboard;
	OIS::JoyStick * mJoy;
	Real mRotate;		// Константа вращения
	Real mMove;		// Константа движения

	boost::scoped_ptr < angel::BLVmap > pBLVMap;
	boost::scoped_ptr < angel::ODMmap > pODMMap;
	std::string mapname, gamedir;
	std::string newmapname;
	bool isForward, isBack, isLeft, isRight, isSpeed;
	Real m_pitch,m_yaw;
	bool mContinue;
	bool displayCameraDetails;

	virtual bool setup( void );
	virtual bool configure( void );
	virtual void chooseSceneManager( void );
	virtual void createCamera( void );
	virtual void createFrameListener( void );
	virtual void createScene( void );	
	virtual void destroyScene( void );	
	virtual void createViewports( void );
	virtual void setupResources( void );
	virtual void createResourceListener( void );
	virtual void loadResources( void );
	virtual void updateStats( void );
	void createGui();
	void destroyGui();

      private:
	void InitListeners();
	//void CreateCopyrightOverlay(  );
	void MakeScreenshot(  );
	bool CheckGameDir(  );
	bool GetGameDir(  );
	bool LoadMap();
};

MMMapviewApp::MMMapviewApp(  ):
mGUI(0),mCamera(0), mTranslateVector(Vector3::ZERO), mCurrentSpeed(0), mWindow(0), mStatsOn(true), mNumScreenShots(0),
mMoveScale(0.0f), mRotScale(0.0f), mTimeUntilNextToggle(0), mFiltering(TFO_BILINEAR),
mAniso(1), mSceneDetailIndex(0), mMoveSpeed(500), mRotateSpeed(36), mDebugOverlay(0),
mInputManager(0), mMouse(0), mKeyboard(0), mJoy(0),pBLVMap(0),pODMMap(0),
m_pitch(0.13),m_yaw(0.13),mlook(true),mInfo(0),mCInfo(0)
{
        mRoot = 0;
        mWindow = 0;
		mInputManager =0;
		mCamera =0;
		mSceneMgr=0;
		mDebugOverlay=0;
		mMyOverlay=0;
		mMouse=0;
		mKeyboard=0;
		mJoy=0;
		mLTM=0;
		displayCameraDetails=false;


		// Provide a nice cross platform solution for locating the configuration files
		// On windows files are searched for in the current working directory, on OS X however
		// you must provide the full path, the helper function macBundlePath does this for us.
#if OGRE_PLATFORM == OGRE_PLATFORM_APPLE
	mResourcePath = macBundlePath() + "/Contents/Resources/";
#else
	mResourcePath = "";
#endif

}
void MMMapviewApp::InitListeners()
{
       	//mDebugOverlay = OverlayManager::getSingleton().getByName("Core/DebugOverlay");

       	LogManager::getSingletonPtr()->logMessage("*** Initializing OIS ***");
       	OIS::ParamList pl;
       	size_t windowHnd = 0;
       	std::ostringstream windowHndStr;

       	mWindow->getCustomAttribute("WINDOW", &windowHnd);
       	windowHndStr << windowHnd;
       	pl.insert(std::make_pair(std::string("WINDOW"), windowHndStr.str()));

       	mInputManager = OIS::InputManager::createInputSystem( pl );
		bool bufferedKeys = true;
		bool bufferedMouse = true;
		bool bufferedJoy = false;

       	//Create all devices (We only catch joystick exceptions here, as, most people have Key/Mouse)
       	mKeyboard = static_cast<OIS::Keyboard*>(mInputManager->createInputObject( OIS::OISKeyboard, bufferedKeys ));
       	mMouse = static_cast<OIS::Mouse*>(mInputManager->createInputObject( OIS::OISMouse, bufferedMouse ));
       	try {
       		mJoy = static_cast<OIS::JoyStick*>(mInputManager->createInputObject( OIS::OISJoyStick, bufferedJoy ));
       	}
       	catch(...) {
       		mJoy = 0;
       	}

       	//Set initial mouse clipping size
       	windowResized(mWindow);

       	showDebugOverlay(true);

       	//Register as a Window listener
       	WindowEventUtilities::addWindowEventListener(mWindow, this);
       	//gamedir=_gamedir;
       	// состояние клавиатуры и мыши
       	mContinue=true;
//       	mMouseDown = false;
//       	mToggle = 0.0;x
       	//mSceneMgr = sceneMgr;
       	// установим скорость вращения и движения
       	mRotate = 0.13;
       	mMove = 250;
       	mMoveSpeed=2000;
       	mCamera->setFixedYawAxis(true, Vector3::UNIT_Z);
       	mCamera->pitch( Degree(90) );
       	mKeyboard->setEventCallback(this);
       	mMouse->setEventCallback(this);
       	isSpeed=isForward=isBack=isLeft=isRight=false;
       	//CreateCopyrightOverlay();
}
MMMapviewApp::~MMMapviewApp(  )
{
      	std::ofstream of("mmview.cfg");
        if (of)
      	{
      		of << "[General]" << std::endl;
      		of << "gamedir=" << gamedir <<std::endl;
      		of << "mapname=" << mapname<<std::endl;
			of << "m_pitch=" << Ogre::StringConverter::toString(m_pitch)<<std::endl;
			of << "m_yaw=" << Ogre::StringConverter::toString(m_yaw)<<std::endl;
      	}
      	
	//Remove ourself as a Window listener
       	destroyGui();
       	windowClosed(mWindow);
		if( mLTM )
			delete mLTM;

		if (mRoot)
            delete mRoot;
		
}

void MMMapviewApp::go( void )
{
		angel::Log.Init("console.log");
       	ConfigFile cfg;
		mapname="";
		
       	try
       	{
       		cfg.load("mmview.cfg");
       		gamedir = cfg.getSetting("gamedir","General");
       		newmapname = cfg.getSetting("mapname","General");
			String t = cfg.getSetting("m_pitch","General","0.13");
			if( t == "") t = "0.13";
			m_pitch = Ogre::StringConverter::parseReal(t);
			t = cfg.getSetting("m_yaw","General","0.13");
			if( t == "") t = "0.13";
			m_yaw = Ogre::StringConverter::parseReal(t);
			
       	}catch(Exception&)
       	{
       		gamedir = "";
       		newmapname = "";
       	}

       	while(!CheckGameDir())
       	{
       		if(!GetGameDir())
       		{
       			return;
       		}
       	}
       	
       	
       	//angel::Log << "setup()" << angel::aeLog::endl;
       	angel::LodManager.AddLod(gamedir+"/data/bitmaps.lod");
       	angel::LodManager.AddLod(gamedir+"/data/games.lod");
       	angel::LodManager.AddLod(gamedir+"/data/icons.lod");
       	angel::LodManager.AddLod(gamedir+"/data/events.lod");
       	angel::LodManager.AddLod(gamedir+"/data/sprites.lod");
       	angel::LodManager.AddLod(gamedir+"/data/EnglishD.lod");
       	angel::LodManager.AddLod(gamedir+"/data/EnglishT.lod");
       	if(angel::LodManager.GetNumPaks() < 3 )
       		gamedir="";
		mLTM = new angel::LodTextureManager();
       	//angel::pLodData data  = angel::LodManager.LoadFile( newmapname);
       	angel::SelectMapDlg smdlg(mWindow,"");
		
       	if(!angel::LodManager.FileExist( newmapname))
       		newmapname = smdlg.GetMapname();
       	if(newmapname == "")
       	{
       		return;
       	}
//		          throw error("cannot load map");
       	if (!setup())
       		return;
       	
       	mRoot->startRendering();

       	// clean up
		pODMMap.reset();
		pBLVMap.reset();
       	destroyScene();
       	angel::Log << "end app" << angel::aeLog::endl;
}

void MMMapviewApp::windowResized( RenderWindow * rw )
{
       	unsigned int width, height, depth;
       	int left, top;
       	rw->getMetrics(width, height, depth, left, top);

       	const OIS::MouseState &ms = mMouse->getMouseState();
       	ms.width = width;
       	ms.height = height;
}

bool MMMapviewApp::windowClosing( RenderWindow * rw )
{
	mContinue=false;
	return false;
}
void MMMapviewApp::windowClosed( RenderWindow * rw )
{
	//Only close for window that created OIS (the main window in these demos)
	if( rw == mWindow )
	{
		WindowEventUtilities::removeWindowEventListener(mWindow, this);
		if( mMouse )
			mMouse->setEventCallback(0);
		if( mKeyboard )
			mKeyboard->setEventCallback(0);

		if( mInputManager )
		{
			mInputManager->destroyInputObject( mMouse );
			mInputManager->destroyInputObject( mKeyboard );
			mInputManager->destroyInputObject( mJoy );

			OIS::InputManager::destroyInputSystem(mInputManager);
			mInputManager = 0;
			mMouse=0;
			mKeyboard=0;
			mJoy=0;

		}
		mRoot->removeFrameListener(this);
	}
}

void MMMapviewApp::moveCamera(  )
{
       	// Make all the changes to the camera
       	// Note that YAW direction is around a fixed axis (freelook style) rather than a natural YAW
       	//(e.g. airplane)
       	mCamera->yaw(mRotX);
       	mCamera->pitch(mRotY);
       	mCamera->moveRelative(mTranslateVector);
       	//moveCamera();
       	mRotX=0;mRotY=0;
}

void MMMapviewApp::showDebugOverlay( bool show )
{
       	/*if (mDebugOverlay)
       	{
       		if (show)
       			mDebugOverlay->show();
       		else
       			mDebugOverlay->hide();
       	}*/
}

bool MMMapviewApp::frameRenderingQueued( const FrameEvent & evt )
{
	return true;

}

bool MMMapviewApp::frameStarted( const FrameEvent & evt )
{
       	mMouse->capture();
       	mKeyboard->capture();

       	mTranslateVector=Vector3::ZERO;
       	mMoveScale = mMoveSpeed * evt.timeSinceLastFrame;
       	if(isSpeed)mMoveScale*=3;
       	if(isBack)mTranslateVector.z += mMoveScale;
       	if(isForward)mTranslateVector.z -= mMoveScale;
       	if(isLeft)mTranslateVector.x -= mMoveScale;
       	if(isRight)mTranslateVector.x += mMoveScale;

       	moveCamera();
		if(displayCameraDetails)
			mDebugText = "P: " + StringConverter::toString(mCamera->getDerivedPosition()) +
			" " + "O: " + StringConverter::toString(mCamera->getDerivedOrientation());

		// добавляем время
		if (mGUI) mGUI->injectFrameEntered(evt.timeSinceLastFrame);

//		if(mContinue)return ExampleFrameListener::frameStarted( evt );
       	return mContinue;

}

bool MMMapviewApp::frameEnded( const FrameEvent & evt )
{
       	updateStats();
       	return true;
}

bool MMMapviewApp::mouseMoved( const OIS::MouseEvent & arg )
{
	    if(!mlook)
		{
			if (mGUI) 
				if(mGUI->injectMouseMove(arg))return true;
		}else
		{
			mRotX = Degree(-arg.state.X.rel * m_yaw );
			mRotY = Degree(-arg.state.Y.rel * m_pitch );
		}
       	return true;
}

bool MMMapviewApp::mousePressed( const OIS::MouseEvent & arg, OIS::MouseButtonID id )
{
	    if(!mlook)
		{
			if (mGUI) 
				if(mGUI->injectMousePress(arg, id))
					return true;
		}else
       	if(id == OIS::MB_Right)
       	{
       	   if(pBLVMap)
       		   pBLVMap->Select(Ray(mCamera->getPosition(),mCamera->getDirection()));
       	   if(pODMMap)
       		   pODMMap->Select(Ray(mCamera->getPosition(),mCamera->getDirection()));
       	}
		if(id == OIS::MB_Left)
		{
			mlook=!mlook;
			if(mlook)
			{
				mGUI->hidePointer();
			}else
			{
				mGUI->showPointer();
			}
		}
       	return true;
}

bool MMMapviewApp::mouseReleased( const OIS::MouseEvent & arg, OIS::MouseButtonID id )
{
	if(!mlook)
	{
		if (mGUI) mGUI->injectMouseRelease(arg, id);
		return true;
	}
	
	return true;
}
bool MMMapviewApp::keyPressed( const OIS::KeyEvent & e )
{
	   if(!mlook)
		   if (mGUI) if(mGUI->injectKeyPress(e))return true;
	   
       switch (e.key)
       {
		   case OIS::KC_ESCAPE: 
			   if(mlook)
					mContinue=false;
			   else
			   {

			   }
			break;
		   case OIS::KC_GRAVE:
/*			   mlook=!mlook;
			   if(mlook)
			   {
				   mGUI->hidePointer();
			   }else
			   {
				   mGUI->showPointer();
			   }*/
			   //if(!mlook)
				//mConsole->setVisible( !mlook );
			   break;
		   case OIS::KC_F1:
			   ToggleHelpOverlay();

			   break;
		   case OIS::KC_W: 
		   case OIS::KC_UP: 
			   isForward=true;
			   break;
		   case OIS::KC_S: 
		   case OIS::KC_DOWN: 
			   isBack=true;
			   break;
		   case OIS::KC_A: 
		   case OIS::KC_LEFT: 
			   isLeft=true;
			   break;
		   case OIS::KC_D: 
		   case OIS::KC_RIGHT: 
			   isRight=true;
			   break;
		   case OIS::KC_LSHIFT: 
		   case OIS::KC_RSHIFT: 
		   case OIS::KC_CAPITAL: 
			   isSpeed=!isSpeed;
			   break;
		   case OIS::KC_Y:
			   if(pODMMap)
				   pODMMap->ToggleEnts();
			   if(pBLVMap)
				   pBLVMap->ToggleEnts();
				   break;
		   case OIS::KC_H:
			   if(pODMMap)
			   if(mKeyboard->isModifierDown(OIS::Keyboard::Alt))
			   {
				   pODMMap->ResetBmodels();
			   }
			   else
			   {
				   pODMMap->ToggleSelectedBModel();
			   }
				   break;
		   case OIS::KC_P:
			   if(pBLVMap)
				   pBLVMap->TogglePortals();
			   break;
		   case OIS::KC_F:
			   {
				   mStatsOn = !mStatsOn;
				   showDebugOverlay(mStatsOn);
				   mTimeUntilNextToggle = 1;
			   }
			   break;
		   case OIS::KC_T:
			   {
				   switch(mFiltering)
				   {
				   case TFO_BILINEAR:
					   mFiltering = TFO_TRILINEAR;
					   mAniso = 1;
					   break;
				   case TFO_TRILINEAR:
					   mFiltering = TFO_ANISOTROPIC;
					   mAniso = 8;
					   break;
				   case TFO_ANISOTROPIC:
					   mFiltering = TFO_BILINEAR;
					   mAniso = 1;
					   break;
				   default: break;
				   }
				   MaterialManager::getSingleton().setDefaultTextureFiltering(mFiltering);
				   MaterialManager::getSingleton().setDefaultAnisotropy(mAniso);
				   showDebugOverlay(mStatsOn);
			   }
			   break;
		   case OIS::KC_SYSRQ:
			   {
			           MakeScreenshot();
			   }
			   break;
		   case OIS::KC_R:
			   {
				   mSceneDetailIndex = (mSceneDetailIndex+1)%3 ;
				   switch(mSceneDetailIndex) {
					case 0 : mCamera->setPolygonMode(PM_SOLID); break;
					case 1 : mCamera->setPolygonMode(PM_WIREFRAME); break;
					case 2 : mCamera->setPolygonMode(PM_POINTS); break;
				   }

			   }
			   break;

           case OIS::KC_L: 
			   {
					angel::SelectMapDlg smdlg(mWindow,mapname);
					newmapname = smdlg.GetMapname();
					createScene();
			   }
               //mContinue = false;
               break;
           default:
               break;
       }
   
   return mContinue; 
}

bool MMMapviewApp::keyReleased( const OIS::KeyEvent & e )
{
	   if(!mlook)
		   if (mGUI) if(mGUI->injectKeyRelease(e))
		return true; 
       switch (e.key)
       {
		   case OIS::KC_W: 
		   case OIS::KC_UP: 
			   isForward=false;
			   break;
		   case OIS::KC_S: 
		   case OIS::KC_DOWN: 
			   isBack=false;
			   break;
		   case OIS::KC_A: 
		   case OIS::KC_LEFT: 
			   isLeft=false;
			   break;
		   case OIS::KC_D: 
		   case OIS::KC_RIGHT: 
			   isRight=false;
			   break;
		   case OIS::KC_LSHIFT: 
		   case OIS::KC_RSHIFT: 
			   isSpeed=!isSpeed;
			   break;
			default:
				break;
	   }
	   return true; 
}

void MMMapviewApp::ToggleHelpOverlay(  )
{
       		Overlay*mMyOverlay = OverlayManager::getSingleton().getByName("MMView/HelpOverlay");
       		if(mMyOverlay->isVisible())
       			mMyOverlay->hide();
       		else
       			mMyOverlay->show();

       		std::string s=
       			"F1: show help\n"
       			"ESC: quit\n"
       			"WSAD: Move\n"
       			"SHIFT: +speed\n"
       			"L: Load Map\n"
       			"PrtSc: Screenshot\n"
       			"R: Render mode\n"
       			"F: Toggle frame rate stats on/off\n"
       			"T: Cycle texture filtering(Bilinear, Trilinear, Anisotropic(8))\n"
       			"P: Toggle portals(BLV map only)\n"
       			"MOUSE2: select face/bmodel\n"
       			"H: show/hide selected BModel(odm map only)\n"
       			"Alt-H: show all hided BModels(odm map only)\n";
				"Y: show/hide ents and spawns\n";
       		OverlayManager::getSingleton().getOverlayElement("MMView/HelpText")->setCaption(s);
}

bool MMMapviewApp::setup( void )
{
       	String pluginsPath;
       	// only use plugins.cfg if not static
#ifndef OGRE_STATIC_LIB
       	pluginsPath = mResourcePath + "plugins.cfg";
#endif
       	
       mRoot = new Root(pluginsPath, 
           mResourcePath + "ogre.cfg", mResourcePath + "Ogre.log");

       setupResources();

       bool carryOn = configure();
       if (!carryOn) return false;

       chooseSceneManager();
       createCamera();
       createViewports();

       // Set default mipmap level (NB some APIs ignore this)
       TextureManager::getSingleton().setDefaultNumMipmaps(5);

       	// Create any resource listeners (for loading screens)
       	createResourceListener();
		// Load resources
		loadResources();

	   // Create the scene
	   createGui();
	   createScene();
	   
	   createFrameListener();
       return true;

}

bool MMMapviewApp::configure( void )
{
// Show the configuration dialog and initialise the system
// You can skip this and use root.restoreConfig() to load configuration
// settings if you were sure there are valid ones saved in ogre.cfg
	if(!mRoot->restoreConfig())
	{
		if(mRoot->showConfigDialog())
		{
			// If returned true, user clicked OK so initialise
			// Here we choose to let the system create a default rendering window by passing 'true'
			mWindow = mRoot->initialise(true,"Might&Magic Mapviewer by Angel");
			return true;
		}
		else
		{
			return false;
		}
	}
	else
	{
		mWindow = mRoot->initialise(true,"Might&Magic Mapviewer by Angel");
		return true;
	}
}

void MMMapviewApp::chooseSceneManager( void )
{
       // Create the SceneManager, in this case a generic one
       mSceneMgr = mRoot->createSceneManager(ST_GENERIC, "ExampleSMInstance");
}

void MMMapviewApp::createCamera( void )
{
        // Create the camera
        mCamera = mSceneMgr->createCamera("PlayerCam");

        // Position it at 500 in Z direction
        mCamera->setPosition(Vector3(0,0,500));
        // Look back along -Z
        mCamera->lookAt(Vector3(0,0,-300));
        mCamera->setNearClipDistance(5);
}

void MMMapviewApp::createFrameListener( void )
{
        InitListeners();
        mRoot->addFrameListener(this);
}
void MMMapviewApp::createGui()
{
	mGUI = new MyGUI::Gui();
	mGUI->initialise(mWindow);
	/*MyGUI::ButtonPtr button = mGUI->createWidget<MyGUI::Button>(
		"Button", 10, 10, 300, 26, MyGUI::Align::Default, "Main");
	button->setCaption("exit");*/


	mConsole = new demo::Console();

	/*mConsole->registerConsoleDelegate("colour", MyGUI::newDelegate(this, &DemoKeeper::command));
	mConsole->registerConsoleDelegate("show", MyGUI::newDelegate(this, &DemoKeeper::command));
	mConsole->registerConsoleDelegate("alpha", MyGUI::newDelegate(this, &DemoKeeper::command));
	mConsole->registerConsoleDelegate("coord", MyGUI::newDelegate(this, &DemoKeeper::command));
*/
	mConsole->setVisible(false);
	if(mlook)
		mGUI->hidePointer();
	

	mInfo = new statistic::StatisticInfo();
	mCInfo = new angel::CopyrightInfo();
	mMapinfo = new angel::Mapinfo();
	Overlay*mMyOverlay = OverlayManager::getSingleton().getByName("MMView/MapOverlay");
	mMyOverlay ->show();
	
}
void MMMapviewApp::destroyGui()
{
	delete mConsole;
	if (mGUI) {

		if (mInfo) {
			delete mInfo;
			mInfo = 0;
		}
		if( mCInfo )
		{
			delete mCInfo;
			mCInfo = 0;
		}
		if(mMapinfo)
		{
			delete mMapinfo;
			mMapinfo = 0;
		}

		mGUI->shutdown();
		delete mGUI;
		mGUI = 0;
	}
}

void MMMapviewApp::createScene( void )
{
       	if(!LoadMap())return;
       	destroyScene();
       	
       	if(pODMMap)pODMMap->AddToScene();
       	if(pBLVMap)pBLVMap->AddToScene();
       	mSceneMgr->setAmbientLight(ColourValue(0.9, 0.9, 0.9));
       	//mCamera->setFixedYawAxis(false);
       	
       	//mCamera->setOrientation( Quaternion (Vector3::UNIT_X, Vector3::ZERO , Vector3::ZERO) );
       	//mCamera->setOrientation( Quaternion (Degree(0), Vector3::UNIT_Y) );
       	mCamera->setPosition(0, 0, 500);
       	//mCamera->setFarClipDistance(2048 * 8*2);
       	MaterialManager::getSingleton().setDefaultTextureFiltering(TFO_ANISOTROPIC);
       	MaterialManager::getSingleton().setDefaultAnisotropy(8);
       	
       	//mSceneMgr->setAmbientLight(ColourValue(0.4, 0.4, 0.4));
       	/*mSceneMgr->setAmbientLight(ColourValue(0, 0, 0));
       	mSceneMgr->setShadowTechnique( SHADOWTYPE_STENCIL_ADDITIVE );
       	Light *light = mSceneMgr->createLight( "Sun" );
       	light->setType( Light::LT_POINT);
       	//light->setDiffuseColour( ColourValue( .95, .93, 0.95 ) );
       	//light->setSpecularColour( ColourValue( .95, .93, 0.95 ) );
       	Vector3 lightpos(0, 0, 500);
       	light->setPosition( lightpos );
       	//light->setDirection( -lightpos );*/

       	//mSceneMgr->showBoundingBoxes(true);
        
}
void MMMapviewApp::destroyScene( void )
{
       	mSceneMgr->clearScene();
       	mSceneMgr->destroyAllManualObjects();
       	mSceneMgr->setVisibilityMask(-1);
       	MaterialManager::getSingleton().unloadUnreferencedResources(false);
       	TextureManager::getSingleton().unloadUnreferencedResources(false);
		MaterialManager::getSingleton().unloadAll();
		TextureManager::getSingleton().unloadAll();
       	
       	//MeshManager::getSingleton().unloadAll();
       	//MaterialManager::getSingleton().unloadAll();
}
void MMMapviewApp::createViewports( void )
{
        // Create one viewport, entire window
        Viewport* vp = mWindow->addViewport(mCamera);
        vp->setBackgroundColour(ColourValue(0,0,0));

        // Alter the camera aspect ratio to match the viewport
        mCamera->setAspectRatio(
            Real(vp->getActualWidth()) / Real(vp->getActualHeight()));
}

void MMMapviewApp::setupResources( void )
{
       // Load resource paths from config file
       ConfigFile cf;
       cf.load(mResourcePath + "resources.cfg");

       // Go through all sections & settings in the file
       ConfigFile::SectionIterator seci = cf.getSectionIterator();

       String secName, typeName, archName;
       while (seci.hasMoreElements())
       {
           secName = seci.peekNextKey();
           ConfigFile::SettingsMultiMap *settings = seci.getNext();
           ConfigFile::SettingsMultiMap::iterator i;
           for (i = settings->begin(); i != settings->end(); ++i)
           {
               typeName = i->first;
               archName = i->second;
  #if OGRE_PLATFORM == OGRE_PLATFORM_APPLE
               // OS X does not set the working directory relative to the app,
               // In order to make things portable on OS X we need to provide
               // the loading with it's own bundle path location
               ResourceGroupManager::getSingleton().addResourceLocation(
                   String(macBundlePath() + "/" + archName), typeName, secName);
  #else
               ResourceGroupManager::getSingleton().addResourceLocation(
                   archName, typeName, secName);
  #endif
           }
       }
}

void MMMapviewApp::createResourceListener( void )
{

}

void MMMapviewApp::loadResources( void )
{
       	// Initialise, parse scripts etc
       	ResourceGroupManager::getSingleton().initialiseAllResourceGroups();
}

void MMMapviewApp::updateStats( void )
{
	if (mInfo) {
		/*static float time = 0;
		time += evt.timeSinceLastFrame;
		if (time > 1) {
			time -= 1;*/
			try {
				const Ogre::RenderTarget::FrameStats& stats = mWindow->getStatistics();
				mInfo->change("FPS", (int)stats.lastFPS);
				mInfo->change("triangle", stats.triangleCount);
				mInfo->change("batch", stats.batchCount);
				mInfo->change("batch gui", MyGUI::LayerManager::getInstance().getBatch());
				mInfo->update();
			} catch (...) { }
//		}
	}

#if 0
		static String currFps = "Current FPS: ";
      	static String avgFps = "Average FPS: ";
      	static String bestFps = "Best FPS: ";
      	static String worstFps = "Worst FPS: ";
      	static String tris = "Triangle Count: ";
      	static String batches = "Batch Count: ";

      	// update stats when necessary
      	try {
      		OverlayElement* guiAvg = OverlayManager::getSingleton().getOverlayElement("Core/AverageFps");
      		OverlayElement* guiCurr = OverlayManager::getSingleton().getOverlayElement("Core/CurrFps");
      		OverlayElement* guiBest = OverlayManager::getSingleton().getOverlayElement("Core/BestFps");
      		OverlayElement* guiWorst = OverlayManager::getSingleton().getOverlayElement("Core/WorstFps");

      		const RenderTarget::FrameStats& stats = mWindow->getStatistics();
      		guiAvg->setCaption(avgFps + StringConverter::toString(stats.avgFPS));
      		guiCurr->setCaption(currFps + StringConverter::toString(stats.lastFPS));
      		guiBest->setCaption(bestFps + StringConverter::toString(stats.bestFPS)
      			+" "+StringConverter::toString(stats.bestFrameTime)+" ms");
      		guiWorst->setCaption(worstFps + StringConverter::toString(stats.worstFPS)
      			+" "+StringConverter::toString(stats.worstFrameTime)+" ms");

      		OverlayElement* guiTris = OverlayManager::getSingleton().getOverlayElement("Core/NumTris");
      		guiTris->setCaption(tris + StringConverter::toString(stats.triangleCount));

      		OverlayElement* guiBatches = OverlayManager::getSingleton().getOverlayElement("Core/NumBatches");
      		guiBatches->setCaption(batches + StringConverter::toString(stats.batchCount));

      		OverlayElement* guiDbg = OverlayManager::getSingleton().getOverlayElement("Core/DebugText");
      		guiDbg->setCaption(mDebugText);
      	}
      	catch(...) { /* ignore */ }
#endif

}

#if 0
void MMMapviewApp::CreateCopyrightOverlay(  )
{
       	//mMyOverlay = OverlayManager::getSingleton().getByName("MMView/MMOverlay");
       	//mMyOverlay->show();
       	//OverlayElement* guiDbg = OverlayManager::getSingleton().getOverlayElement("MMView/DebugText");
       	/*OverlayElement* guiDbg = OverlayManager::getSingleton().createOverlayElement("TextArea","CopyrightText");
       	guiDbg->setDimensions(50,30);
       	guiDbg->setPosition(0,0);
       	guiDbg->setParameter("font_name","BlueHighway");
       	guiDbg->setParameter("char_height","16");
       	guiDbg->setCaption("Might&Magic Mapviewer 2.1 by Angel\nhttp://angel-death.newmail.ru/");
       	guiDbg->setEnabled(true);*/
       	OverlayManager& overlayManager = OverlayManager::getSingleton();
       	TextAreaOverlayElement* textArea = static_cast<TextAreaOverlayElement*>(
       		overlayManager.createOverlayElement("TextArea", "MMView/Copyright"));
       	textArea->setMetricsMode(Ogre::GMM_PIXELS);
       	textArea->setPosition(0, 0);
       	textArea->setDimensions(200, 20);
       	textArea->setCaption("Might&Magic Mapviewer 2.1a by Angel\nhttp://angel-death.newmail.ru/");
       	textArea->setCharHeight(20);
       	textArea->setFontName("BlueHighway");
       	textArea->setColourBottom(ColourValue(1, 1, 1));
       	textArea->setColourTop(ColourValue(1, 1, 1));
       	OverlayContainer* panel = static_cast<OverlayContainer*>(
       						overlayManager.createOverlayElement("Panel", "MMView/CopyrightPanel"));
       	panel->setMetricsMode(Ogre::GMM_PIXELS);
       	panel->setPosition(0, 0);
       	panel->setDimensions(200, 40);
		//panel->setHorizontalAlignment(GHA_RIGHT);


       	Overlay* overlay = overlayManager.create("MMView/CopyrightOverlay");
       	overlay->add2D(panel);
       	// Add the text area to the panel
       	panel->addChild(textArea);
       	// Show the overlay
       	overlay->show();
       	//guiDbg->setCaption("Might&Magic");
}
#endif

void MMMapviewApp::MakeScreenshot(  )
{
 	   std::ostringstream ss;
 	   ss << "screenshot_" << ++mNumScreenShots << ".png";
 	   mWindow->writeContentsToFile(ss.str());
 	   mDebugText = "Saved: " + ss.str();
}

bool MMMapviewApp::CheckGameDir(  )
{
	if ( -1 != GetFileAttributes( ( gamedir + "//mm6.exe" ).c_str(  ) ) )
		return true;
	if ( -1 != GetFileAttributes( ( gamedir + "//mm7.exe" ).c_str(  ) ) )
		return true;
	if ( -1 != GetFileAttributes( ( gamedir + "//mm8.exe" ).c_str(  ) ) )
		return true;
	return false;
}

bool MMMapviewApp::GetGameDir(  )
{
	BROWSEINFO info;
	char szDir[MAX_PATH];
	char szDisplayName[MAX_PATH];
	LPITEMIDLIST pidl;
	LPMALLOC pShellMalloc;

	if ( SHGetMalloc( &pShellMalloc ) == NO_ERROR )
	{
		memset( &info, 0x00, sizeof( info ) );
		info.hwndOwner = 0;
		info.pidlRoot = NULL;
		info.pszDisplayName = szDisplayName;
		info.lpszTitle = "Select Might&Magic game folder";
		info.ulFlags = BIF_RETURNONLYFSDIRS | BIF_STATUSTEXT;
		info.lpfn = NULL;	// callback function

		pidl = SHBrowseForFolder( &info );

		if ( pidl )
		{
			if ( SHGetPathFromIDList( pidl, szDir ) )
			{
				gamedir = szDir;
			}
			pShellMalloc->Free( pidl );
			pShellMalloc->Release(  );
			return true;
		} else
		{
			gamedir = "";
			return false;
		}
	}
	gamedir = "";
	return false;
}
bool MMMapviewApp::LoadMap()
{
	if( mapname == newmapname)
		return false;
	angel::pLodData data  = angel::LodManager.LoadFileData( newmapname);
	if ( !data )
	{
		throw error("cannot load map");
	}
	
	std::string ext = newmapname.substr(newmapname.size()-4,4);
	std::transform( ext.begin(), ext.end(), ext.begin(), std::tolower);
	

	
	
	if( ext == ".odm" )
	{
		pODMMap.reset( new angel::ODMmap( data,  newmapname.c_str(),mSceneMgr ));
		pBLVMap.reset();
		
	}
	if( ext == ".blv" )
	{
		pBLVMap.reset( new angel::BLVmap( data,  newmapname.c_str(),mSceneMgr ));
		pODMMap.reset();
		
	}
	mapname=newmapname;
	return true;
}

#if OGRE_PLATFORM == OGRE_PLATFORM_WIN32
#define WIN32_LEAN_AND_MEAN
#include "windows.h"

INT WINAPI WinMain( HINSTANCE hInst, HINSTANCE, LPSTR strCmdLine, INT )
#else
int main( int argc, char **argv )
#endif
{
	// Create application object
	MMMapviewApp app;

	try
	{
		app.go(  );
	} catch( Exception & e )
	{
#if OGRE_PLATFORM == OGRE_PLATFORM_WIN32
		MessageBox( NULL, e.getFullDescription(  ).c_str(  ),
			    "An exception has occured!",
			    MB_OK | MB_ICONERROR | MB_TASKMODAL );
#else
		fprintf( stderr, "An exception has occured: %s\n",
			 e.getFullDescription(  ).c_str(  ) );
#endif
	}
	catch( std::exception & e )
	{
		MessageBox( NULL, e.what(  ), "Game Error", MB_OK );
		angel::Log << "Error: " << e.what(  ) << angel::aeLog::endl;
	}

	return 0;
}
