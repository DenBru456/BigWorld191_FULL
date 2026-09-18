import struct


# This class is a UserDataType for our trade log entries in the database
class TradeLog:
	def __init__( self, 
			dbIDA, tradeIDA, itemAIndex, itemAType,
			dbIDB, tradeIDB, itemBIndex, itemBType ):
		self.dbIDA = dbIDA
		self.tradeIDA = tradeIDA
		self.itemAIndex = itemAIndex
		self.itemAType  = itemAType
		self.dbIDB = dbIDB
		self.tradeIDB = tradeIDB
		self.itemBIndex = itemBIndex
		self.itemBType  = itemBType

# This class handles all the manipulations of our UserDataType
class TypeHandler:
	def addToStream( self, t ):
		if not t:
			t = self.defaultValue()
		stream = struct.pack( "QiiiQiii",
			t.dbIDA, t.tradeIDA, t.itemAType, t.itemAIndex, 
			t.dbIDB, t.tradeIDB, t.itemBIndex, t.itemBType )
		return stream

	def createFromStream( self, stream ):
		return TradeLog(*struct.unpack( "QiiiQiii", stream ))

	def addToSection( self, t, section ):
		if not t: t = self.defaultValue()
		section.write( "dbIDA",			t.dbIDA )
		section.write( "tradeIDA",		t.tradeIDA )
		section.write( "itemAType",	t.itemAType )
		section.write( "itemAIndex",	t.itemAIndex )
		section.write( "dbIDB",			t.dbIDB )
		section.write( "tradeIDB",		t.tradeIDB )
		section.write( "itemBIndex",	t.itemBIndex )
		section.write( "itemBType",	t.itemBType )

	def createFromSection( self, section ):
		return TradeLog(
			section.readInt64( "dbIDA" ), section.readInt( "tradeIDA" ), section.readInt( "itemAIndex" ), section.readInt( "itemAType" ),
			section.readInt64( "dbIDB" ), section.readInt( "tradeIDB" ), section.readInt( "itemBIndex" ), section.readInt( "itemBType" ) )

	def fromStreamToSection( self, stream, section ):
		o = self.createFromStream( stream )
		self.addToSection( o, section )

	def fromSectionToStream( self, section ):
		o = self.createFromSection( section )
		return self.addToStream( o )

	def bindSectionToDB( self, binder ):
		binder.bind( "dbIDA",		"INT64" )
		binder.bind( "tradeIDA",	"UINT32" )
		binder.bind( "itemAIndex",	"INT32" )
		binder.bind( "itemAType",	"INT32" )
		binder.bind( "dbIDB",		"INT64" )
		binder.bind( "tradeIDB",	"UINT32" )
		binder.bind( "itemBIndex",	"INT32" )
		binder.bind( "itemBType",	"INT32" )

	def defaultValue( self ):
		return TradeLog( 0, 0, -1, 0, 0, -1)

typeHandler = TypeHandler()

