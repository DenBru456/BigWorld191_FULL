<?php
require_once( 'AuthenticatedPage.php' );
require_once( 'Session.php' );
require_once( 'BWAuthenticator.php' );
require_once( 'UserAgent.php' );

define ('FORCE_PASSWORD', 'pass' );

class LoginPage extends XHTMLMPPage
{
	var $returnUrl;

	function LoginPage()
	{
		XHTMLMPPage::XHTMLMPPage( "Login" );
	}

	function initialise()
	{
		$err = Array();

		if (isset( $_REQUEST['reset_nub'] ))
		{
			bw_set_nub_port( 0 );
			$matches = Array();
			ereg( "(.*)&?reset_nub=[^&]*(.*)",
				$_SERVER['PHP_SELF']."?".$_SERVER['QUERY_STRING'], $matches );
			header( 'Location: '. $matches[1].$matches[2] );
			exit;
		}

		$auth = new BWAuthenticator();

		// handle logout request to invalidate
		if (isset( $_REQUEST['logout'] ) && $_REQUEST['logout'])
		{
			$auth->invalidateToken();
			session_unset();
			header( 'Location: '. LOGIN_PAGE_URL );
			exit;
		}

		// check authentication token if it exists, or a username/password
		// if it exists
		if ($auth->doesAuthTokenExist())
		{
			$authErr =  $auth->authenticateSessionToken();
			if ($authErr)
			{
				$err = array_merge( $err, $authErr );
			}
		}
		else if (isset( $_REQUEST['username'] )
			&& isset( $_POST['password'] ))
		{
			// password must be in POST parameters for security
			$pass = $_POST['password'];
			if (FORCE_PASSWORD != '')
			{
				// we have forced password to be something - only use for
				// demos!
				$pass = FORCE_PASSWORD;
			}

			$authErr = $auth->authenticateUserPass(
				$_REQUEST['username'], $pass );
			if ($authErr)
			{
				$err = array_merge( $err, $authErr );
			}
		}
		else
		{
			// no auth token and no login attempt
			return;
		}

		// did we login successfully
		if (count( $err ) > 0)
		{
			# boot back to login if authentication failed
			$_SESSION['err_msgs'] = $err;
		}
		else
		{

			if ($this->returnUrl)
			{
				header( 'Location: '. $this->returnUrl );
				session_write_close();
				exit;
			}
			else
			{
				if ($auth->mailboxType() == "Avatar")
				{
					header( 'Location: '. CHARACTER_WELCOME_PAGE_URL );
				}
				else
				{
					header( 'Location: '. ACCOUNT_WELCOME_PAGE_URL );
				}
				session_write_close();
				exit;
			}
		}

	}


	function printFooter()
	{
		if (!isset( $_SESSION['display']['resolution_width'] ))
		{
			echo (
				xhtmlMpDiv(
					xhtmlMpImg( 'images/logo_bigworld.gif',
						'BigWorld Logo' ),
					'footer'
				)
			);

		}
		else
		{
			$imgMaxHeight = (int)
				(0.1 * (float)$_SESSION['display']['resolution_height']);
			$imgMaxWidth = (int)
				(0.75 * (float)$_SESSION['display']['resolution_width']);

			echo (
				xhtmlMpDiv(
					xhtmlMpImg( 'Image.php?'.
						'path=images/logo_bigworld.gif&'.
						'max_width='. $imgMaxWidth. '&'.
						'max_height='. $imgMaxHeight,
						'BigWorld Logo',
						'', ' height="10%"'),
					'footer'
				)
			);
		}
	}

	function printErrorMsgs()
	{
		if (array_key_exists( 'err_msgs', $_SESSION ))
		{
			echo( xhtmlMpList(
				$_SESSION['err_msgs'], FALSE, 'error' ) );

			session_unregister( 'err_msgs' );
		}
	}

	function printInstructions()
	{
	}

	function printLoginForm()
	{

		$username = '';
		if (isset( $_REQUEST['username'] ))
		{
			$username = $_REQUEST['username'];
		}
		$form = new XHTMLMPForm();

		$rows =
			xhtmlMpTableRow(
				xhtmlMpTableCell(
					xhtmlMpHeading( 'User name', 2 )
				).
				xhtmlMpTableCell(
					xhtmlMpFormInputText( 'username',
						$username,
						'',
						'textfield',
						' size="10"' )
			) ).
			xhtmlMpTableRow(
				xhtmlMpTableCell(
					xhtmlMpHeading( 'Password', 2 )
				).
				xhtmlMpTableCell(
					xhtmlMpFormInputPassword( 'password',
						'',
						'',
						'textfield',
						' size="10"'
					)
				)
			).
			xhtmlMpTableRow(
				xhtmlMpTableCell(
					'&nbsp;' ).
				xhtmlMpTableCell(
					xhtmlMpFormSubmit( '', 'Login', 'button' )
				)
			);

		$form->setContents( xhtmlMpTable( $rows, 0, '100%', '',
			' cellpadding="0"' ) );

		$form->setAction( "Login.php" );
		$form->setMethod( "post" );
		$form->setClassName( "loginbox" );

		echo( $form->output() );
	}

	function renderBody()
	{
		echo( xhtmlMpDiv(
			xhtmlMpHeading(
				'&middot;'.
					strtoupper( "BigWorld FantasyDemo" ).
					'&middot;',
				1, 'heading'
			) ,
			'', ' id="login"' )
		);

		$this->printErrorMsgs();
		$this->printLoginForm();


			if (isset( $_SESSION['display'] ))
			{
				$deviceInfo =& $_SESSION['useragent-info'];
				$dispInfo =& $_SESSION['display'];

				$contents = ( xhtmlMpDiv(
					$this->getDevice(). ' '.
					$dispInfo['resolution_width'].
					'x'.
					$dispInfo['resolution_height'],
					'user-agent-info'
					 )
				) ;

				echo( $contents );

			}
		$this->printInstructions();
		$this->printFooter();
	}
}

$page = new LoginPage();
$page->render();

?>
