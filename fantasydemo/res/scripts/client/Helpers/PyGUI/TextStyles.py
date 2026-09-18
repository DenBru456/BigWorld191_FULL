import BigWorld, GUI, Math, ResMgr
from bwdebug import ERROR_MSG



styles = {
	'Heading': ('Heading.font', (255,255,255,255)),
	'Label': ('Label.font', (255,255,255,255)),

	'ButtonNormal': ('Label.font', (255,255,255,255)),
	'ButtonHover': ('Label.font', (255,128,64,255)),
	'ButtonPressed': ('Label.font', (255,0,0,255)),
	'ButtonActive': ('Label.font', (0,0,0,255)),
	'ButtonDisabled': ('Label.font', (125,125,125,255)),
}

fontAliases = {}

def setStyle( component, styleName ):
	if styles.has_key( styleName ):
		style = styles[ styleName ]
		component.font = fontAliases.get( style[0], style[0] )
		component.colour = style[1]
	else:
		ERROR_MSG( "No style named '%s'." % (styleName,) )

