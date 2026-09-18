'''This module provides a number of utilities to simplify the writing of code
that needs to execute in order over a number of  frames using python generators
and BigWorld.callback().

To use this module, implement the required code as a generator by using the
'yield' keyword to specify points where the execution of the code needs to wait.
The generator function should be decorated with BWCoroutine or BWMemberCoroutine
to denote it as a coroutine. They yield should be used with one of the
BWWaitFor* classes defined in this module.
For example:

@BWCoroutine
def myFunction()
	print "Start of function"
	yeild BWWaitForPeriod( 10.0 )
	print "Ten seconds later"
'''

import BigWorld
from functools import partial



def BWCoroutine( coroutineFunction ):
	'''The function doctorates the given function as a BWCoroutine. The
	decorated function will have an additional callback parameter as its first
	argument. This will be called when the coroutine exits.
	Note: For member functions of classes use @BWMemberCoroutine

	Example:

		@BWCoroutine
		def myCoroutine( waitTime ):
			print "Start of myCoroutine. Waiting for %fseconds" % waitTime
			yield BWWaitForPeriod( waitTime )
			print "End of myCoroutine"

		def afterCoroutineFunction():
			print "After coroutine"

		myCoroutine(afterCoroutineFunction )

	Result:
		Start of myCoroutine. Waiting for 8.65sec
		End of myCoroutine
		After coroutine

	'''
	return _BWCoroutineInstance( coroutineFunction )


def BWMemberCoroutine( coroutineFunction ):
	'''This decorator function is similar to BWCoroutine but is designed for
	member functions of classes.
	'''
	return _BWCoroutineMemberDescriptor( coroutineFunction )


def coroutineTick(  coroutineObject ):
	try:
		waitObject = coroutineObject.generator.next()
	except StopIteration:
		coroutineObject.completionCallback()
		return

	assert isinstance( waitObject, _BWWait )
	waitObject( coroutineObject )


class _BWCoroutineInstance( object ):
	def __init__( self, coroutineFunction ):
		self.coroutineFunction = coroutineFunction

	def __call__( self, completionCallback, *args ):
		self.completionCallback = completionCallback
		self.generator = self.coroutineFunction( *args )
		coroutineTick( self )


class _BWCoroutineMemberInstance( object ):
	def __init__( self, coroutineFunction, instance ):
		self.coroutineFunction = coroutineFunction
		self.instance = instance

	def __call__( self, completionCallback, *args ):
		self.completionCallback = completionCallback
		self.generator = self.coroutineFunction( self.instance, *args )
		del self.instance
		BigWorld.callback( 0.0, partial( coroutineTick, self ) )


class _BWCoroutineMemberDescriptor( object ):
	def __init__( self, coroutineFunction ):
		self.coroutineFunction = coroutineFunction

	def __get__( self, instance, type ):
		return _BWCoroutineMemberInstance( self.coroutineFunction, instance )


class _BWWait:
	def __init__( self ):
		pass


class BWWaitForPeriod( _BWWait ):
	'''This class implements a wait object that when yielded, from a suspends
	the coroutine for the given number of seconds using BigWorld.callback().
	'''

	def __init__( self, waitTime ):
		_BWWait.__init__( self )
		self.waitTime = waitTime

	def __call__( self, coroutineObject ):
		BigWorld.callback( self.waitTime, partial( coroutineTick, coroutineObject ) )


class BWWaitForCondition( _BWWait ):
	'''This class implements a wait object that when yielded, poles it's
	provided condition at the specified frequency until true or the timeout
	period expires.
	'''

	def __init__( self, checkFrequency, timeout, onTimeout, condition ):
		_BWWait.__init__( self )
		self.condition = condition
		self.checkFrequency = checkFrequency
		self.timeoutTime = timeout + BigWorld.time()
		self.onTimeout = onTimeout

	def __call__( self, coroutineObject ):
		if self.condition():
			BigWorld.callback( 0.0, partial( coroutineTick, coroutineObject ) )
		elif BigWorld.time() > self.timeoutTime:
			self.onTimeout()
			del self.condition
			del self.onTimeout
		else:
			BigWorld.callback( self.checkFrequency, partial( self, coroutineObject ) )


class BWWaitForCoroutine( _BWWait ):
	'''This class implements a wait object that when yielded, waits for the
	given coroutine to complete.
	Note: This class provides its own callback for the given coroutine so that
	argument should not be included in the parameter list.

	@BWCoroutine
	def functionA( someString)
		print "Start of functionA", someString
		yeild BWWaitForPeriod( 10.0 )
		print "Ten seconds later: functionA", someString

	@BWCoroutine
	def functionB()
		print "Start of functionB"
		yeild BWWaitForCoroutine( 10.0, lambda: None, functionA, "called from functionB" )
		print "functionB after function A"

	functionB( lambda: None )

	Result:
	Start of functionB
	Start of functionA called from functionB
	Ten seconds later: functionA called from functionB
	functionB after function A
	'''

	def __init__( self, timeout, onTimeout, coroutineFunction, *args ):
		_BWWait.__init__( self )
		self.onTimeout = onTimeout
		self.coroutineFunction = coroutineFunction
		self.coroutineFunctionArgs = args
		BigWorld.callback( timeout, self.handleTimeout )

	def __call__( self, coroutineObject ):
		self.coroutineObject = coroutineObject
		self.coroutineFunction( self.handleCompletionCallback, *self.coroutineFunctionArgs )
		del self.coroutineFunctionArgs
		del self.coroutineFunction

	def handleCompletionCallback( self ):
		self.onTimeout = lambda: None
		BigWorld.callback( 0.0, partial( coroutineTick, self.coroutineObject ) )

	def handleTimeout( self ):
		self.onTimeout()





