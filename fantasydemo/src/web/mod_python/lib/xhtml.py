'''
This is a helper module for printing XHTML.
'''

def comment( contents ):
	'''Returns a commented section of XML.'''
	return '<!--' + contents + '-->'

def link( href, label, className=None, attributes=None ):
	'''Returns an external link element.'''
	if attributes is None:
		attributes = {}
	attributes['href'] = href

	return tag( 'a', label, className, attributes )

def list( items, ordered=False, className=None, attributes=None ):
	'''Returns a list element.'''
	contents = ''
	for item in items:
		contents += tag( 'li', item )
	if ordered:
		listtag = 'ol'
	else:
		listtag = 'ul'
	return tag( listtag, contents, className, attributes )

def img( src, alt, className=None, attributes=None ):
	'''Returns am image element.'''
	if attributes is None:
		attributes = {}
	attributes['src'] = src
	attributes['alt'] = alt

	return singleTag( 'img', className, attributes )

def heading( contents, number=1, className=None ):
	'''Returns a heading element. '''
	return tag( 'h%d' % (number), contents, className )

def para( contents, className=None, attributes=None ):
	'''Returns a paragraph element.'''
	return tag( 'p', contents, className, attributes )

def pre( contents, className=None, attributes=None ):
	'''Returns a pre-formatted element.'''
	return tag( 'pre', contents, className, attributes )

def formInputCheckbox( name, className=None, attributes=None ):
	if attributes == None:
		attributes = {}

	attributes['type'] = 'checkbox'
	attributes['name'] = name

	return singleTag( 'input', className, attributes )

def formInputSelect( name, options, defaultItem=None,
		className=None, attributes=None ):
	"""
	Returns a combo-box select form input element.

	@param options 	list of tuples (value, label) or
					(option-group-list, option-group-label)
					where option-group-list is another list of such tuples.
	"""
	if attributes == None:
		attributes = {}
	contents = ''
	for (option, optionLabel) in options:
		contents += formInputSelectOption(option, optionLabel, defaultItem)
	attributes["name"] = name
	return tag('select', contents, className, attributes)

def formInputSelectOptionGroup( optionGroupList, label, defaultItem ):
	''' Returns an option group for a combo-box select form input element. '''
	out = '<optgroup label="%s">' % label
	for option, label in optionGroupList:
		out += formInputSelectOption( option, label, defaultItem )
	out += '</optgroup>'
	return out

def formInputSelectOption( option, label, defaultItem ):
	''' Returns an option for a combo-box select form input element. '''
	if type( option ) == list:
		return formInputSelectOptionGroup( option, label, defaultItem )
	else:
		attributes = {}
		if str( option ) == str( defaultItem ):
			attributes["selected"] = "selected"
		attributes["value"] = option
		return tag( 'option', label, None, attributes )


def formInputSubmit( value='submit', name=None, className=None,
		attributes=None ):
	''' Returns a submit form input element. '''
	if attributes is None:
		attributes = {}
	attributes['type'] = 'submit'
	if not name is None:
		attributes['name'] = name
	attributes['value'] = value
	return singleTag( 'input', className, attributes )

def formInputText( name, value=None, width=None, className=None,
		attributes=None ):
	''' Returns a text form input element. '''
	if attributes is None:
		attributes = {}
	attributes['type'] = 'text'
	attributes['name'] = name
	if not value is None:
		attributes['value'] = value
	if not width is None:
		attributes['size'] = width

	return singleTag( 'input', className, attributes )

def formInputPassword( name, value=None, width=None, className=None,
		attributes=None ):
	''' Returns a password form input element. '''
	if attributes is None:
		attributes = {}
	attributes['type'] = 'password'
	attributes['name'] = name
	if not value is None:
		attributes['value'] = value
	if not width is None:
		attributes['width'] = width

	return singleTag( 'input', className, attributes )

def formInputHidden( name, value, attributes=None ):
	''' Returns an hidden form input element. '''
	if attributes is None:
		attributes = {}
	attributes['type'] = 'hidden'
	attributes['name'] = name
	attributes['value'] = value
	return singleTag( 'input', None, attributes )

def form( contents, method="post", action=None, className=None,
		attributes=None ):
	''' Returns a form element.'''
	if attributes is None:
		attributes = {}
	if not method is None:
		attributes['method'] = method
	if not action is None:
		attributes['action'] = action

	return tag( 'form', contents, className, attributes )


def singleTag( tagName, className=None, attributes=None ):
	'''Returns a tag element.'''
	if attributes is None:
		attributes = {}
	if className != None:
		if type(attributes) != dict:
			attributes = {}
		attributes['class'] = className
	return "<%s%s/>" % (tagName, attrString( attributes ))

def tag( tagName, contents, className=None, attributes=None ):
	"""
	Tag-izes the contents with the given tag name and XHTML class and any
	attributes.
	"""
	if attributes is None:
		attributes = {}
	if className != None:
		if type( attributes ) != dict:
			attributes = {}
		attributes['class'] = className
	return "<%s%s>%s</%s>" % \
		(tagName, attrString( attributes ), contents, tagName)

def attrString( attributes ):
	'''Creates an attribute string from the given attributes dictionary.'''
	if attributes is None:
		return ''

	return " " + " ".join( "%s=\"%s\"" % (key, value)
		for key, value in attributes.items() )

# common constant strings
BR = singleTag( 'br' )

# xhtml.py
