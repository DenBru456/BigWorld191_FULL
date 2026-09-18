# Name: Create storm
# Desc: Creates storm and rain entities
# Target: baseapps

# Storm

properties = dict( name="RAIN", propensity=4.0, arg0=1.0, arg1=1.0 )
BigWorld.createBaseAnywhere( "WeatherSystem", properties )

properties = dict( name="STORM", propensity=1.0, arg0=1.0, arg1=1.0 )
BigWorld.createBaseAnywhere( "WeatherSystem", properties )

print "Created storm"
