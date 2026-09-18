<?php

/*
 * SearchAuctions.php
 * Allows player to search through auctions.
 */

// ----------------------------------------------------------------------------
// Section: Includes/Requires
// ----------------------------------------------------------------------------
require_once( 'XHTML-MP-functions.php' );
require_once( 'AuthenticatedPage.php' );
require_once( 'Items.php' );
require_once( 'Util.php' );


// ----------------------------------------------------------------------------
// Section: SearchAuctionsPage
// ----------------------------------------------------------------------------

class PlayerAuctionsPage extends AuthenticatedXHTMLMPPage
{
	var $playerAuctions;
	var $officialTime;
	var $player;
	var $auctionHouse;
	var $playerDBID;

	function PlayerAuctionsPage()
	{
		AuthenticatedXHTMLMpPage::AuthenticatedXHTMLMPPage( 'My Auctions' );
	}

	function initialise()
	{
		// set up class variables accessed later on
		$this->player = $this->auth->getMailbox();
		$this->auctionHouse = bw_look_up_entity_by_name(
			'AuctionHouse', 'AuctionHouse' );

		$res = bw_exec( $this->player, "webGetPlayerInfo" );
		if (is_string( $res ))
		{
			// error - should log out
			$this->addErrorMsg( $res );
			$this->setRedirect( "Login.php?logout=1" );
			return;
		}
		$this->playerDBID = $res['databaseID'];

		$res = bw_exec( $this->player, "webGetGoldAndInventory" );
		$this->availableGold = $res['goldPieces'];

		$res = bw_exec( $this->auctionHouse, 'webGetTime' );
		$this->officialTime = $res['time'];

		$this->doGetPlayerAuctions();


	}


	function doGetPlayerAuctions()
	{
		$itemMgr =& ItemTypeManager::instance();

		$res = bw_exec( $this->auctionHouse,
			"webCreateSellerCriteria",
			(int)$this->playerDBID
		);
		if (is_string( $res ))
		{
			$this->addErrorMsg( $res );
			$this->setRedirect( "Login.php?logout=1" );
			return;
		}

		$sellerCriteria = $res['criteria'];

		$res = bw_exec( $this->auctionHouse,
			'webSearchAuctions',
			$sellerCriteria
		);
		if (!$res['success'])
		{
			$this->addErrorMsg( $res['errMsg'] );
			return;
		}

		$res = bw_exec( $this->auctionHouse, 'webGetAuctionInfo',
			$res['searchedAuctions'] );
		$this->playerAuctions = $res['auctionInfo'];
	} //  function doSearchAction()



	function renderBody()
	{
		$this->renderErrorMsgs();
		$this->renderStatusMsgs();

		$this->printPlayerAuctions();

	}

	function printPlayerAuctions()
	{
		echo xhtmlMpHeading( 'My Auctions', 2 );
		if (!count( $this->playerAuctions ))
		{
			echo xhtmlMpPara(
				"You have created no auctions that are currently pending. ".
				"Go to ". xhtmlMpLink( "Inventory.php", "Inventory" ).
				" to create an auction from one of your inventory items." );
			return;
		}

		$rows = xhtmlMpTableRow(
			xhtmlMpTableHeader( "Item" ).
			xhtmlMpTableHeader( "Expiry" ).
			xhtmlMpTableHeader( "Current bid" ).
			xhtmlMpTableHeader( "Buyout price" )
		);

		$itemMgr =& ItemTypeManager::instance();

		$first = "-first";
		$count = 0;
		foreach ($this->playerAuctions as $auctionInfo )
		{
			$auctionId = $auctionInfo['auctionID'];
			$itemType = $auctionInfo['itemType'];
			$itemTypeName = $itemMgr->itemTypes[$itemType]->name;
			$itemTypeImgUrl = $itemMgr->itemTypes[$itemType]->iconImgUrl;


			$cells =
				xhtmlMpTableCell(
					xhtmlMpImg( $itemTypeImgUrl, $itemTypeName ).
					$itemTypeName
				).
				xhtmlMpTableCell(
					timeFloatToString( $auctionInfo['expiry'] -
						$this->officialTime )
				).
				xhtmlMpTableCell( $auctionInfo['currentBid']  ).
				xhtmlMpTableCell( $auctionInfo['buyoutPrice'] == FALSE ?
					"-": $auctionInfo['buyoutPrice'])
			;


			$rows .= xhtmlMpTableRow(
				$cells,
				"alt". (($count++ % 2) + 1). $first
			);
			$first = "";
		}

		echo xhtmlMpTable(
			$rows,
			'0', '', 'tradeTable'
		);

	}

}

// ----------------------------------------------------------------------------
// Section: Main body
// ----------------------------------------------------------------------------

$page = new PlayerAuctionsPage();
$page->render();
?>
