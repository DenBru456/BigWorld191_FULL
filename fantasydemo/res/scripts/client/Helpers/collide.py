# -----------------------------------------------------------------------------
# file: collide
# Description:
#	- ???
# -----------------------------------------------------------------------------

import BigWorld
import Math
import math


[ COLLIDE_ENTITY,
	COLLIDE_TERRAIN,
	COLLIDE_NONE,
	COLLIDE_OTHER ] = range(4)

def collide( x, y ):
	player = BigWorld.player()
	if player is None:
		return COLLIDE_OTHER, None
		
	inv = Math.Matrix( BigWorld.camera().invViewMatrix )
	src = inv.applyToOrigin()
	far = BigWorld.projection().farPlane
	dst = src + _getWorldRay( x, y ).scale( far )

	entity = _pickEntity( src, dst )
	if entity and entity != player:
		return COLLIDE_ENTITY, entity

	spaceID = player.spaceID
	terrain = BigWorld.collide( spaceID, src, dst )
	if terrain:
		return COLLIDE_TERRAIN, terrain[0]
	else:
		return COLLIDE_NONE, dst


def _getWorldRay( x, y ):
	inv = Math.Matrix( BigWorld.camera().invViewMatrix )
	ray = inv.applyVector( _nearPlanePoint( x, y ) )
	ray.normalise()
	return ray


def _nearPlanePoint( x, y ):
	fov     = BigWorld.projection().fov
	near    = BigWorld.projection().nearPlane
	aspect  = BigWorld.screenWidth() / BigWorld.screenHeight()
	yLength = near * math.tan( fov * 0.5 )
	xLength = yLength * aspect
	return (xLength * x, yLength * y, near)


def _pickEntity( src, dst ):
	cur_ent   = None
	cur_cosin = 0
	maxDistSq = BigWorld.target.maxDistance * BigWorld.target.maxDistance
	for entity in BigWorld.entities.values():
		if src.distSqrTo( entity.position ) < maxDistSq:
			intersects, cosin = _entityIntersect(src, dst, entity)
			if intersects and cosin > cur_cosin:
				cur_cosin = cosin
				cur_ent   = entity
	return cur_ent


def _entityIntersect( src, dst, entity ):
	if not entity.model:
		return False, 0
	
	bbmatrit = Math.Matrix( entity.model.bounds )
	minpoint = bbmatrit.applyToOrigin()
	maxpoint = bbmatrit.applyPoint( ( 1, 1, 1 ) )
	centerpt = (maxpoint + minpoint).scale( 0.5 )

	centerray = centerpt - src
	centerray.normalise()
	mouseray = dst - src
	mouseray.normalise()
	boundray = maxpoint - src
	boundray.normalise()
	
	mousecos = mouseray.dot( centerray )
	boundcos = boundray.dot( centerray )
	
	return mousecos > boundcos, mousecos
