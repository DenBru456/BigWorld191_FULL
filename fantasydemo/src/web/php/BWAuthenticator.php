<?php
require_once( 'Authenticator.php' );
require_once( 'BigWorld.php' );

define( 'BW_AUTHENTICATOR_TOKEN_KEY_MAILBOX', 'mailbox' );
define( 'BW_AUTHENTICATOR_TOKEN_KEY_MAILBOX_TYPE', 'mailbox_type' );

class BWAuthenticator extends Authenticator
{
	function BWAuthenticator()
	{
		Authenticator::Authenticator();
	}

	function getMailbox()
	{
		$mailboxPickle =& $this->getVariable(
			BW_AUTHENTICATOR_TOKEN_KEY_MAILBOX );
		if (isset( $mailboxPickle )
				&& is_string( $mailboxPickle )
				&& strlen( $mailboxPickle ))
		{
			return bw_deserialise( $mailboxPickle );
		}
		else
		{
			return FALSE;
		}
	}

	function setMailboxType( $type )
	{
		$this->setVariable( BW_AUTHENTICATOR_TOKEN_KEY_MAILBOX_TYPE, $type );
	}

	function mailboxType()
	{
		return $this->getVariable( BW_AUTHENTICATOR_TOKEN_KEY_MAILBOX_TYPE );
	}

	function setMailbox( $newMailbox, $type )
	{
		$pickle = bw_serialise( $newMailbox );
		$this->setVariable( BW_AUTHENTICATOR_TOKEN_KEY_MAILBOX,  $pickle );
		$this->setMailboxType( $type );
	}

	function authenticateUserPass( $username, $pass )
	{
		// This is used to return error messages back to the user
		$res = Array();

		// 	debug('username='. debugStringObj($username). ',
		// 		pass = '. debugStringObj($pass));
		if ($username == '')
		{
			$res[] = "Username is empty";

		}
		if ($pass == '')
		{
			$res[] = "Password is empty";
		}
		if (count( $res ))
		{
			return $res;
		}

		// authenticate account - allow for the fact that player may already
		// be logged on
		$logonResult = bw_logon( $username, $pass,
			/* allow_already_logged_on */TRUE );
		if ($logonResult !== TRUE)
		{
			if (is_string( $logonResult ))
			{
				$res[] = $logonResult;
			}
			else
			{
				$res[] = debugStringObj( $logonResult );
			}
			return $res;
		}
	

		// for new accounts, it may not necessarily be checked out as soon as
		// we log on.
		$retries = 5;
		$sleepTime = 1.0;
		$mailbox = false;
		while (!is_resource( $mailbox ) && $retries)
		{
			$mailbox = bw_look_up_entity_by_name( "Account", $username );
			--$retries;
			sleep( $sleepTime );
		}

		if (is_bool( $mailbox ))
		{
			if ($mailbox)
			{
				$res[] = "Entity is not checked out";
				return $res;
			}
			else
			{
				$res[] = "Entity does not exist";
				return $res;
			}
		}
		else if (is_resource( $mailbox ))
		{
			$this->setMailboxType( "Account" );
			bw_set_keep_alive_seconds( $mailbox,
				AUTHENTICATOR_INACTIVITY_PERIOD );
			$pickle = bw_serialise( $mailbox );
			$this->setSessionToken( Array(
				AUTHENTICATOR_TOKEN_KEY_IP_ADDRESS 		=>
					$_SERVER['REMOTE_ADDR'],
				AUTHENTICATOR_TOKEN_KEY_LAST_ACTIVITY 	=> time(),
				AUTHENTICATOR_TOKEN_KEY_USERNAME 		=> $username,
				BW_AUTHENTICATOR_TOKEN_KEY_MAILBOX 		=> $pickle
			) );
		}
		else if (is_string( $mailbox ))
		{
			$res[] = sprintf( "Login failed: %s", $mailbox );
		}

		if (count( $res ) == 0)
		{
			return FALSE;
		}

		return $res;

	}
}
?>
