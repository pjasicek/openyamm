Might&Magic 6-8 Mapviewver
======================================================
Written by Angel
Email: angel.d.death@gmail.com
WWW: http://sites.google.com/site/angelddeath/
     http://angel-death.newmail.ru/
Current version: 2.0
Date: 23.01.09
3D Engine: Ogre3D http://www.ogre3d.org/

Установка
============

Распакуйте Might&Magic Mapviewer и файлы Ogre3D(https://sites.google.com/site/angelddeath/Home/ogre3dfiles.rar?attredirects=0) в каую-нибудь папку, и запустите
при первом запуске укажите каталог игры (Might&Magic VI,Might&Magic VII or Might&Magic VIII)
и видео настроики
для смены каталога игры удалите mmview.cfg
для смены настроек графики удалите ogre.cfg

Использование
============
F1: показать справку
ESC: выход
WSAD: движение
SHIFT: ускорение
L: Загрузить карты
PrtSc: сделать скриншот
R: Пререключение режима отрисовки
F: Показать/прятать статистику FPS
T: Переключение фильтрации текстур(Bilinear, Trilinear, Anisotropic(8))
P: Вкл/выкл порталы (только на BLV картах)
MOUSE2: выбрать face/bmodel
H: показать/спрятать выбранную  BModel(только на ODM картах)
Alt-H: вернуть все спрятанные BModels(только на ODM картах)
Y: show/hide ents and spawns

Версии
=============
Версия 2.0 (23.01.09)
Переписан с использованим Ogre3D Engine

Версия 2.01 (24.01.09)
Мелкие изменения

Версия 2.1 (xx.01.09)
Исправлено текстурирование BModels
изменено отображение z_calc
fixed crash on alt-f4
Добавлены Entites & Spawn 

Версия 2.1a (27.01.09)
исправлена ODM Spawn Z-координата(у большинаства спавнов она равна 0, и поэтому он оказывался под поверхностью, поднял на поверхность)

Версия 2.2 (xx.01.09)
Чуствительность мыши (m_pitch,m_yaw) в mmview.cfg
Исправлен выбор face
Имя карты из mapstats.txt
