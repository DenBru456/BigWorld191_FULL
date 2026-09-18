#!/usr/bin/env php

Web Integration Gateway PHP Test script
=======================================

<?php // functions

function doInventoryTest( $accountEntity = "Account",
		$accountName = "dominicw",
		$password = "aa",
		$avatarName = "Dom0" )
{
	bw_set_default_keep_alive_seconds( 300 );

	$res = bw_logon( $accountName, $password );

	$playerAccount = bw_look_up_entity_by_name( $accountEntity, $accountName );
	if (!$playerAccount)
	{
		die( "couldn't get $entity $accountName\n" );
	}
	bw_set_keep_alive_seconds( $playerAccount, 300 );

	$res = bw_exec( $playerAccount, "webGetCharacterList" );
	if (!$res)
	{
		die( "couldn't get character list for $entity $accountName\n" );
	}
	print_r( $res );

	$res = bw_exec( $playerAccount, "webChooseCharacter", $avatarName, "Avatar" );

	if (!$res['character'])
	{
		die( $res['errMsg']. "\n" );
	}

	$avatar = $res['character'];

	print_r( bw_exec( $avatar, "webGetGoldAndInventory" ) );

}

?>
<?php

$numIterations = 1;
if ($_SERVER['argc'] >= 2)
{
	$numIterations = (int)$_SERVER['argv'][1];
}
printf( "numIterations = %d\n", $numIterations );

$character = "Dom0";
if ($_SERVER['argc'] >= 3)
{
	$character = $_SERVER['argv'][2];
}

$username = "dominicw";
if ($_SERVER['argc'] >= 4)
{
	$username = $_SERVER['argv'][3];
}

$password = "aa";
if ($_SERVER['argc'] >= 5)
{
	$password = $_SERVER['argv'][4];
}

printf( "account/character/password = %s/%s/%s\n", 
	$username, $character, $password );

for ($i = 0; $i < $numIterations; ++$i)
{
	doInventoryTest( "Account", 
		$username, 
		$password,
		$character );
}
printf( "Finished $numIterations iterations.\n" );
?>
