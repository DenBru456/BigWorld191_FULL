import BigWorld
import ResMgr
import Math
import math

import CameraNode
import MenuScreenAvatar

MENU_SPACE_RESPATH = "spaces/menu_space"
MENU_CAMERA_NAME = "MenuCamera"

g_menuSpaceID = None
g_menuCamera = None

g_loaded = False
g_finishLoadCallback = None


def init():
	assert not g_loaded

	global g_menuSpaceID
	g_menuSpaceID = BigWorld.createSpace()
	BigWorld.addSpaceGeometryMapping( g_menuSpaceID, None, MENU_SPACE_RESPATH )

	global g_menuCamera
	g_menuCamera = BigWorld.FreeCamera()
	g_menuCamera.fixed = True
	m = Math.Matrix()
	m.setRotateYPR( (0,0,0) )
	m.translation = (50, 2, 50)
	m.invert()
	g_menuCamera.set( m )
	g_menuCamera.spaceID = g_menuSpaceID

	BigWorld.camera( g_menuCamera )

	global g_finishLoadCallback
	g_finishLoadCallback = BigWorld.callback( 0.01, finishLoad )


def fini():
	global g_menuSpaceID
	global g_menuCamera
	global g_finishLoadCallback
	global g_loaded

	g_loaded = False

	if g_finishLoadCallback:
		BigWorld.cancelCallback( g_finishLoadCallback )

	if g_menuCamera == BigWorld.camera():
		BigWorld.camera( None )
	g_menuCamera = None

	if g_menuSpaceID != None:
		BigWorld.clearSpace( g_menuSpaceID )
		BigWorld.releaseSpace( g_menuSpaceID )
		g_menuSpaceID = None


def finishLoad():
	assert g_menuCamera.spaceID == g_menuSpaceID
	assert g_menuSpaceID != None
	assert g_menuCamera != None

	status = BigWorld.spaceLoadStatus( 200 )

	cameraNodes = [i for i in BigWorld.userDataObjects.values() if isinstance( i, CameraNode.CameraNode )]
	menuCameraList = [i for i in cameraNodes if i.name == MENU_CAMERA_NAME]
	menuScreenAvatars = [i for i in BigWorld.entities.values() if isinstance( i, MenuScreenAvatar.MenuScreenAvatar )]

	if status < 1.0 or len( menuCameraList ) != 1 \
					or len( menuScreenAvatars ) != 1:
		g_finishLoadCallback = BigWorld.callback( 0.01, finishLoad )
		return

	#print "finish load"

	menuCamera = menuCameraList[0]
	m = Math.Matrix()
	m.setRotateYPR( (menuCamera.yaw, menuCamera.pitch, menuCamera.roll) )
	m.translation = menuCamera.position
	m.invert()
	g_menuCamera.set( m )
	BigWorld.projection().fov = math.radians( menuCamera.fov )

	assert BigWorld.camera() is g_menuCamera

	global g_loaded
	g_loaded = True

	#print "finish load end"





