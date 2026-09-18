# This module contains constant data associated with the Guard entity type. 
# The data is loaded from the xml file scripts/data/guard.xml for use 
# by the client and server.
# Note: For the moment all data loaded by this module should be client safe.

import ResMgr
import AvatarModel


AVATAR_MODEL_DATA = AvatarModel.pack( {'models':['characters/npc/fd_orc_guard/orc.model'], 'dyes':[], 'sfx':[] } )


SOURCE_ARMOUR_COLOURS = (	ResMgr.openSection('scripts/data/guard.xml/armourColours/clothesColour1').readVector4s( 'colour' ),
							ResMgr.openSection('scripts/data/guard.xml/armourColours/clothesColour2').readVector4s( 'colour' ),
							ResMgr.openSection('scripts/data/guard.xml/armourColours/clothesColour3').readVector4s( 'colour' ),
							ResMgr.openSection('scripts/data/guard.xml/armourColours/clothesColour4').readVector4s( 'colour' ), )


SOURCE_SKIN_COLOURS	= (		ResMgr.openSection('scripts/data/guard.xml/skinColours/clothesColour1').readVector4s( 'colour' ),
							ResMgr.openSection('scripts/data/guard.xml/skinColours/clothesColour2').readVector4s( 'colour' ),
							ResMgr.openSection('scripts/data/guard.xml/skinColours/clothesColour3').readVector4s( 'colour' ),
							ResMgr.openSection('scripts/data/guard.xml/skinColours/clothesColour4').readVector4s( 'colour' ), )

