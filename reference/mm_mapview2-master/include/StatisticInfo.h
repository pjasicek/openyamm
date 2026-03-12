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
/*!
	@file
	@author		Albert Semenov
	@date		08/2008
	@module
*/
#ifndef __STATISTIC_INFO_H__
#define __STATISTIC_INFO_H__

#include <MyGUI.h>
#include "version.h"

namespace statistic
{

	class StatisticInfo
	{

	public:
		typedef std::pair<std::string, std::string> PairString;
		typedef std::vector<PairString> VectorPairString;

		StatisticInfo() :
			mInfo(nullptr)
		{
			//MyGUI::Gui::getInstance().load("core_skin_debug.xml");

			const std::string layer = "Statistic";
			if ( ! MyGUI::LayerManager::getInstance().isExist(layer)) return;

			const std::string skin = "StatisticRect";
			if ( ! MyGUI::SkinManager::getInstance().isExist(skin)) return;

			mInfo = MyGUI::Gui::getInstance().createWidget<MyGUI::Widget>(skin, MyGUI::IntCoord(), MyGUI::Align::Default, layer);

			// если не найдется то поставится Default
			const std::string font = "DejaVuSans.14";
			mInfo->setFontName(font);
		}


		~StatisticInfo()
		{
			if (mInfo) {
				MyGUI::Gui::getInstance().destroyChildWidget(mInfo);
				mInfo = nullptr;
			}
		}

		template <typename T>
		void change(const std::string & _key, const T & _value)
		{
			for (VectorPairString::iterator iter=mParams.begin(); iter!=mParams.end(); ++iter) {
				if (iter->first == _key) {
					iter->second = MyGUI::utility::toString<T>(_value);
					return;
				}
			}
			mParams.push_back(std::make_pair(_key, MyGUI::utility::toString<T>(_value)));
		}

		void remove(const std::string & _key)
		{
			for (VectorPairString::iterator iter=mParams.begin(); iter!=mParams.end(); ++iter) {
				if (iter->first == _key) {
					mParams.erase(iter);
					return;
				}
			}
		}

		void update()
		{
			if (mInfo) {
				std::ostringstream stream;
				for (VectorPairString::iterator iter=mParams.begin(); iter!=mParams.end(); ++iter) {
					if (iter != mParams.begin()) stream << "\n";
					stream << iter->first << "  :  " << iter->second;
				}

				mInfo->setCaption(stream.str());
				

				MyGUI::ISubWidgetText * text = mInfo->getSubWidgetText();
				if (text) {
					const MyGUI::IntSize& size = text->getTextSize() + mInfo->getSize() - text->getSize();
					static int maxwidth=0;
					if(size.width > maxwidth)
						maxwidth=size.width;
					//mInfo->setCoord(MyGUI::Gui::getInstance().getViewWidth() - size.width - 20, MyGUI::Gui::getInstance().getViewHeight() - size.height - 20, size.width, size.height);
					mInfo->setCoord(MyGUI::Gui::getInstance().getViewWidth() - maxwidth - 20, MyGUI::Gui::getInstance().getViewHeight() - size.height - 20, maxwidth, size.height);
				}
			}
		}

		void clear()
		{
			mParams.clear();
		}

		void clear(const std::string & _key)
		{
			for (VectorPairString::iterator iter=mParams.begin(); iter!=mParams.end(); ++iter) {
				if (iter->first == _key) {
					mParams.erase(iter);
					return;
				}
			}
		}

	private:
		MyGUI::WidgetPtr mInfo;
		VectorPairString mParams;

	};

} // namespace staticstic
namespace angel
{
	class CopyrightInfo
	{
	public:
		CopyrightInfo():
		  mInfo(nullptr)
		  {
			  const std::string layer = "Info";
			  if ( ! MyGUI::LayerManager::getInstance().isExist(layer)) return;

			  const std::string skin = "StaticText";
			  //const std::string skin = "WindowCaptionSmall";//"WindowCaption";
			  
			  if ( ! MyGUI::SkinManager::getInstance().isExist(skin)) return;

			  mInfo = MyGUI::Gui::getInstance().createWidget<MyGUI::Widget>(skin, MyGUI::IntCoord(), MyGUI::Align::Default, layer);

			  // если не найдется то поставится Default
			  const std::string font = "DejaVuSans.14";
			  mInfo->setFontName(font);
			  
			  std::stringstream s;
			  s<< "Might&Magic Mapviewer by Angel\n" << VERSION <<"\nhttp://sites.google.com/site/angelddeath/";
			  mInfo->setCaption(s.str());
			  mInfo->setTextColour(MyGUI::Colour(1,1,1));
			  MyGUI::ISubWidgetText * text = mInfo->getSubWidgetText();
			  if (text) 
			  {
				  const MyGUI::IntSize& size = text->getTextSize() + mInfo->getSize() - text->getSize();

				  mInfo->setCoord(0/*MyGUI::Gui::getInstance().getViewWidth() - size.width - 1*/, MyGUI::Gui::getInstance().getViewHeight() - size.height-1, size.width, size.height);
			  }
			  mInfo->eventMouseButtonPressed= newDelegate(this, &CopyrightInfo::mouseButtonPressed);
			  
		  }
		  void mouseButtonPressed(MyGUI::WidgetPtr _sender, int _left, int _top, MyGUI::MouseButton _id)
		  {
#pragma warning( push )
#pragma warning( disable : 4309 )
  				char url[]={
				  0x87, 0x84, 0x91, 0x9f, 0xca, 0xca, 0xc0, 0x83, 0x8c, 0x9b, 0x95, 0x96, 0xc1, 0x97, 0x8a, 0x80, 
				  0x97, 0x89, 0x8a, 0xde, 0x86, 0x80, 0x9d, 0xca, 0x9c, 0x99, 0x91, 0x8a, 0xdf, 0x84, 0x81, 0x97, 
				  0x80, 0x83, 0x94, 0x81, 0x8a, 0x91, 0x91, 0x87, 0xdf, 0xe5};
				  char key[]={0xef,0xf0,0xe5};
#pragma warning(pop)


				if( _id == MyGUI::MouseButton::Left)
				{
					for (int i =0,j=0; i< sizeof(url);i++,j++)
					{
						url[i]^=key[j%sizeof(key)];
					}

					ShellExecute(NULL, "open", url, NULL, NULL, SW_SHOWNORMAL);
					for (int i =0,j=0; i< sizeof(url);i++,j++)
					{
						url[i]^=key[j%sizeof(key)];
					}
				}

		  }
		  ~CopyrightInfo()
		  {
			  if (mInfo) {
				  MyGUI::Gui::getInstance().destroyChildWidget(mInfo);
				  mInfo = nullptr;
			  };
		  }
		  private:
			  MyGUI::WidgetPtr mInfo;
	};
}//namespace angel
#endif // __STATISTIC_INFO_H__
