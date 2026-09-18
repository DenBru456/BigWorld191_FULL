<?php
/**
 *	Defines the authenticator interface.
 */

require_once( 'Debug.php' );
require_once( 'Session.php' );

/**
 *	Session variable array keys.
 */
define( 'AUTHENTICATOR_SESSION_KEY_TOKEN', 			'token' );
define( 'AUTHENTICATOR_TOKEN_KEY_IP_ADDRESS', 		'ip_address' );
define( 'AUTHENTICATOR_TOKEN_KEY_LAST_ACTIVITY', 	'last_activity' );
define( 'AUTHENTICATOR_TOKEN_KEY_USERNAME', 		'username' );


/**
 *	The Authenticator class.
 */
class Authenticator
{
	function Authenticator()
	{
	}

	function authenticateSessionToken()
	{
		$out = array();
		if (isset( $_SESSION[AUTHENTICATOR_SESSION_KEY_TOKEN] ))
		{
			$token =& $_SESSION[AUTHENTICATOR_SESSION_KEY_TOKEN];
			// check that they haven't been inactive too long
			if (isset( $token[AUTHENTICATOR_TOKEN_KEY_LAST_ACTIVITY] ))
			{
				$lastActivity =& $token[AUTHENTICATOR_TOKEN_KEY_LAST_ACTIVITY];
				$timeNow = time();

				if ($timeNow >=
					$lastActivity + AUTHENTICATOR_INACTIVITY_PERIOD)
				{
					$out[] = 'Session inactive for more than '.
						AUTHENTICATOR_INACTIVITY_PERIOD. ' seconds';
				}
			}
			else
			{
				$out[] = 'Invalid authentication token';
			}

			// check that the cookie isn't spoofed by checking against IP
			// address
			if (isset( $token[AUTHENTICATOR_TOKEN_KEY_IP_ADDRESS] ))
			{
				$address =& $token[AUTHENTICATOR_TOKEN_KEY_IP_ADDRESS];
				if ($address != $_SERVER['REMOTE_ADDR'])
				{
					$out[] = 'IP address changed';
				}
			}
			else
			{
				$out[] = 'Invalid authentication token';
			}
		}
		else
		{
			$out[] = 'No authentication token exists';
		}

		if (count( $out ) == 0)
		{
			return FALSE;
		}
		else
		{
			// destroy the session
			session_unregister( AUTHENTICATOR_SESSION_KEY_TOKEN );
			return $out;
		}
	}

	function doesAuthTokenExist()
	{
		return isset( $_SESSION[AUTHENTICATOR_SESSION_KEY_TOKEN] );
	}

	function setSessionToken( $token )
	{
		$_SESSION[AUTHENTICATOR_SESSION_KEY_TOKEN] = $token;
	}

	function authenticateUserPass( $username, $pass )
	{
		$out = Array();
		// debug('username='. debugStringObj($username). ',
		// pass = '. debugStringObj($pass));
		if ($username == '')
		{
			$out[] = "Username is empty";
		}
		if ($pass == '')
		{
			$out[] = "Password is empty";
		}

		if (count( $out ) == 0)
		{
			// debug('null authenticator - returning false - no errs');
			$this->setSessionToken( Array(
				AUTHENTICATOR_TOKEN_KEY_IP_ADDRESS => $_SERVER['REMOTE_ADDR'],
				AUTHENTICATOR_TOKEN_KEY_LAST_ACTIVITY => time(),
				AUTHENTICATOR_TOKEN_KEY_USERNAME => $username,
			) );
			return false;
		}
		else
		{
			return $out;
		}
	}


	function updateLastActivity()
	{
		$_SESSION[AUTHENTICATOR_SESSION_KEY_TOKEN]
			[AUTHENTICATOR_TOKEN_KEY_LAST_ACTIVITY] = time();
	}

	function setVariable( $key, $value )
	{
		$_SESSION[AUTHENTICATOR_SESSION_KEY_TOKEN][$key] = $value;
	}

	function &getVariable( $key )
	{
		return $_SESSION[AUTHENTICATOR_SESSION_KEY_TOKEN][$key];
	}


	function invalidateToken()
	{
		session_unregister( AUTHENTICATOR_SESSION_KEY_TOKEN );
	}
}
?>
