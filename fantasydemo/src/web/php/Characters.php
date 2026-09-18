<?php
require_once( 'Authenticator.php' );
require_once( 'AuthenticatedPage.php' );

class CharactersPage extends AuthenticatedXHTMLMPPage
{
	var $characterList;

	function CharactersPage()
	{
		AuthenticatedXHTMLMPPage::AuthenticatedXHTMLMPPage( "Characters" );
		$this->menubar->removeItem( 'Home' );
		$this->menubar->removeItem( 'Character' );
		$this->menubar->removeItem( 'Inventory' );
		$this->menubar->removeItem( 'AuctionHouse' );
		$this->menubar->removeItem( 'MyAuctions' );
		$this->menubar->removeItem( 'Logout' );
		$this->menubar->addItem( 'Logout', '?logout=1' );
	}

	function initialise()
	{
		$account = $this->auth->getMailbox();

		if(isset( $_GET['logout'] ))
		{
				$this->setRedirect( 'Login.php?logout=1' );
				return;
		}
		
		if (!$account)
		{
			$this->setRedirect( 'Login.php?logout=1' );
			return;
		}
		if ($this->auth->mailboxType() == "Avatar")
		{
			$this->setRedirect( CHARACTER_WELCOME_PAGE_URL );
			return;
		}

		$res = bw_exec( $account, "webGetCharacterList" );
		if (is_string( $res ))
		{
			// check whether our mailbox is still valid
			$this->addErrorMsg( $res );
			$this->setRedirect( "Login.php?logout=1" );
			return;
		}

		$this->characterList = $res['characters'];

		if (isset( $_GET['new_character_name'] ))
		{
			$account =& $this->auth->getMailbox();
			$res = bw_exec( $account, "webCreateCharacter",
				$_GET['new_character_name'] );
			if (!$res['success'])
			{
				$this->addErrorMsg( "Could not create character: ". 
					$res['errMsg'] );
				return;
			}

			$this->addStatusMsg( "Character creation successful" );

			$res = bw_exec( $account, "webGetCharacterList" );
			$this->characterList = $res['characters'];
			return;
		}
		

		if (isset( $_GET['character'] ))
		{
			$res = bw_exec( $account, "webChooseCharacter",
				$_GET['character'], "Avatar" );
			if ($res['errMsg'])
			{
				$this->addErrorMsg( $res['errMsg'] );
				return;
			}
				
			$this->addStatusMsg( "Login successful" );
			debug( debugStringObj( $res ) );
			
			$mailbox = $res['character'];
			
			bw_set_keep_alive_seconds( $mailbox, 
				AUTHENTICATOR_INACTIVITY_PERIOD );
			$this->auth->setMailbox( $mailbox, "Avatar" );

			$this->setRedirect( 'News.php' );
			

		}
		

	}

	function renderBody()
	{
		$this->renderErrorMsgs();

		echo xhtmlMpHeading( "Character List", 2 );

		if (!count( $this->characterList ))
		{

		}
		$rows = '';
		$count = 0;

		$height = 100;
		if (isset( $_SESSION['display'] ))
		{
			$height = $_SESSION['display']['resolution_height'] / 3;
		}

		foreach ($this->characterList as $character)
		{
			$row = xhtmlMpTableRow(
				xhtmlMpTableCell(
					xhtmlMpLink( '?character='. $character['name'],
						xhtmlMpImg( 'Image.php?path=images/'. 
								$character['charClass']. 
								'_profile_front.png&max_height='.$height,
							$character['name']. "'s Portrait" )
					), FALSE, 'portrait'
				).
				xhtmlMpTableCell(
					xhtmlMpLink( '?character='. $character['name'],
						$character['name'] ).
						' ('. ucfirst( $character['charClass'] ). ')', 
					FALSE, 'name'
				),
				($count++ % 2) ? "alt1":"alt2"

			);
			$rows .= $row;
		}

		$newCharacterForm = new XHTMLMPForm();
		$newCharacterForm->setMethod( "get" );
		$newCharacterForm->setContents( 
			"Character Name: ".
			xhtmlMpFormInputText( "new_character_name" ).
			xhtmlMpFormSubmit( "", "Create" ) );
		$rows .= xhtmlMpTableRow( 
			xhtmlMpTableCell( 'Add new character' ).
			xhtmlMpTableCell(
				$newCharacterForm->output() ),

			($count++ % 2) ? "alt1":"alt2"
		);
					
			
		echo xhtmlMpTable( $rows, "0", '', "character_list",
			' cellspacing="0" cellpadding="0"' );
	}
}

$page = new CharactersPage();
$page->render();
?>
