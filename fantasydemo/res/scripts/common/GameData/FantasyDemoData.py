# This module contains constant data used by the FantasyDemo module that is 
# loaded from xml. The data is loaded from entities/data/fantasy_demo.xml 
# and the space.settings of the default space.
# Note: For the moment all data loaded by this module should be client safe.

import ResMgr

SPACES = ResMgr.openSection( "scripts/data/fantasy_demo.xml/spaces" ).readStrings( "space" )

DEFAULT_SPACE_START_POS = ResMgr.openSection( SPACES[0] ).readVector3( "space.settings/startPosition" )
