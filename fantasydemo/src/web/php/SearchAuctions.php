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

class SearchAuctionsPage extends AuthenticatedXHTMLMPPage
{
	var $searchResults;
	var $playerBids;
	var $officialTime;
	var $player;
	var $auctionHouse;
	var $playerDBID;
	var $availableGold;

	/**
	 * Create a search auctions page.
	 */
	function SearchAuctionsPage()
	{
		AuthenticatedXHTMLMpPage::AuthenticatedXHTMLMPPage( 'Search Auctions' );
	}

	/**
	 * Perform a bid from a HTTP form post.
	 */
	function doBidAction( $auctionId )
	{
		$bidAmount = (int)($_REQUEST['bid_amount']);
		if ($bidAmount <= 0)
		{
			$this->addErrorMsg( "Bid amount is invalid." );
			return;
		}

		$res = bw_exec( $this->player, "webBidOnAuction", $auctionId,
			FALSE /*->buyoutOut*/, $bidAmount );
		
		if (is_string( $res ))
		{
			// error - should log out
			$this->addErrorMsg( $res );
			$this->setRedirect( "Login.php?logout=1" );
			return;
		}

		if (!$res['success'])
		{
			$this->addErrorMsg( $res['errMsg'] );
		}
		else
		{
			$this->addStatusMsg( $res['errMsg'] );
		}

	} // function doBidAction()


	/**
	 * Perform a buyout from a HTTP form post.
	 */
	function doBuyoutAction( $auctionId )
	{
		$res = bw_exec( $this->player, "webBidOnAuction", $auctionId,
			TRUE /* -> buyingOut*/, 0/* bid amount */ );
		if (is_string( $res ))
		{
			// error - should log out
			$this->addErrorMsg( $res );
			$this->setRedirect( "Login.php?logout=1" );
			return;
		}
		if ($res['success'])
		{
			$this->addStatusMsg( $res['errMsg'] );
		}
		else
		{
			$this->addErrorMsg( $res['errMsg'] );
		}
	} // function doBuyoutAuction()


	/**
	 * Perform the search requested from the HTTP form post.
	 */
	function doSearchAction()
	{
		// retrieve the search results by building a search criteria
		$itemMgr =& ItemTypeManager::instance();

		//	build criteria to describe
		//	(
		//		SellerDBID == playerID OR
		//		(
		//			ItemType == search_type_name AND
		//			BidRange( search_min_bid, search_max_bid )
		//		)
		//	)

		// do inner AND grouped criteria first

		$searchCriteria = '';
		// search item type name
		if (isset( $_REQUEST['search_type_name'] ) and
				( $searchTypeName = $_REQUEST['search_type_name'] ) )
		{
			$itemTypesList = Array();
			foreach( $itemMgr->itemTypes as $itemType => $itemTypeInfo )
			{

				if (eregi( $searchTypeName, $itemTypeInfo->name ))
				{
					$itemTypesList[] = $itemType;
				}
			}
			$res = bw_exec( $this->auctionHouse,
				"webCreateItemTypeCriteria", $itemTypesList );
			if (is_string( $res ))
			{
				// error - should log out
				$this->addErrorMsg( $res );
				$this->setRedirect( "Login.php?logout=1" );
				return;
			}
			$itemTypeCriteria = $res['criteria'];

			if ($searchCriteria == FALSE)
			{
				$searchCriteria = $itemTypeCriteria;
			}
			else
			{
				$res = bw_exec( $this->auctionHouse,
					"webCombineAnd",
					$searchCriteria,
					$itemTypeCriteria
				);
				$searchCriteria = $res['criteria'];
			}
		}
		// search min - max bid
		$searchMinBid = -1;
		$searchMaxBid = -1;
		if (isset( $_REQUEST['search_min_bid'] ))
		{
			if ($_REQUEST['search_min_bid'] == '')
			{
				$searchMinBid = -1;
			}
			else
			{
				$searchMinBid = (int)$_REQUEST['search_min_bid'];
			}
		}
		if (isset( $_REQUEST['search_max_bid'] ))
		{
			if ($_REQUEST['search_max_bid'] == '')
			{
				$searchMaxBid = -1;
			}
			else
			{
				$searchMaxBid = (int)$_REQUEST['search_max_bid'];
			}
		}
		if ($searchMinBid != -1 or $searchMaxBid != -1)
		{
			$res = bw_exec( $this->auctionHouse,
				"webCreateBidRangeCriteria",
				$searchMinBid,
				$searchMaxBid
			);
			$bidRangeCriteria = $res['criteria'];
			if ($searchCriteria == FALSE)
			{
				$searchCriteria = $bidRangeCriteria;
			}
			else
			{
				$res = bw_exec( $this->auctionHouse,
					"webCombineAnd",
					$searchCriteria,
					$bidRangeCriteria
				);
				$searchCriteria = $res['criteria'];
			}
		}

		$res = bw_exec( $this->auctionHouse,
			"webCreateBidderCriteria",
			(int)$this->playerDBID
		);

		$bidderCriteria = $res['criteria'];

		if (!$searchCriteria)
		{
			if (isset( $_REQUEST['search_submit'] ))
			{
				// retrieve all
				// leave search criteria empty
			}
			else
			{
				// only retrieve auctions player has bid on
				$searchCriteria = $bidderCriteria;
			}
		}
		else // if ($searchCriteria)
		{
			// encapsulate with seller criteria if the result of the
			// above is not empty,otherwise we want ALL auctions (ie
			// the player hit search without specifying criteria)
			$res = bw_exec( $this->auctionHouse,
				"webCombineOr",
				$bidderCriteria,
				$searchCriteria
			);
			$searchCriteria = $res['criteria'];
		}

		// perform the search
		$res = bw_exec( $this->auctionHouse,
			'webSearchAuctions',
			$searchCriteria
		);
		if (is_string( $res ))
		{
			// error - should log out
			$this->addErrorMsg( $res );
			$this->setRedirect( "Login.php?logout=1" );
			return;
		}
		if (!$res['success'])
		{
			$this->addErrorMsg( $res['errMsg'] );
			return;
		}

		debug( "searchCriteria: $searchCriteria" );
		debugObj( $res );

		// retrieve the info for each returned auction ID
		$res = bw_exec( $this->auctionHouse, 'webGetAuctionInfo',
			$res['searchedAuctions'] );
		foreach ($res['auctionInfo'] as $auctionInfo)
		{
			$auctionInfo['item'] = Array(
				$auctionInfo['itemLock'],
				$auctionInfo['itemType'],
				$auctionInfo['itemSerial']
			);
			$this->searchResults[$auctionInfo['auctionID']] = $auctionInfo;

		}

		debug( "search results: \n". debugStringObj( $this->searchResults ) );

		// retrieve the seller names as we go
		$sellerNames = Array();

		// move all the player's bids to $this->playerBids
		$this->playerBids = Array();
		foreach (array_keys( $this->searchResults ) as $auctionId)
		{
			$auctionInfo =& $this->searchResults[$auctionId];
			$sellerDBID = $auctionInfo['sellerDBID'];

			if (!isset( $sellerNames[$sellerDBID] ))
			{
				$sellerEntity = bw_look_up_entity_by_dbid(
					'Avatar', $auctionInfo['sellerDBID'] );
				$res = bw_exec( $sellerEntity, 'webGetPlayerInfo' );
				$sellerNames[$sellerDBID] = $res['playerName'];
			}
			$sellerName = $sellerNames[$sellerDBID];

			$auctionInfo['playerName'] = $sellerName;
			if (in_array( $this->playerDBID, $auctionInfo['bidders'] ))
			{
				$this->playerBids[ $auctionId ] = $auctionInfo;
				unset( $this->searchResults[$auctionId] );
			}
			else if ($this->playerDBID == $auctionInfo['sellerDBID'] )
			{
				unset( $this->searchResults[$auctionId] );
			}
		}
	} //  function doSearchAction()


	function renderHead()
	{
		AuthenticatedXHTMLMpPage::renderHead();

		// JavaScript for setting default bid amounts and enabling/disabling
		// buyout and bid submit buttons
		?>
<script language="JavaScript">

var selectedAuctionItemName = '';
var selectedAuctionBuyoutAmount = -1;

function updateBid( recommendedBid, buyoutAmount, itemName )
{
	bidAmountTextInput = document.getElementById( 'bid_amount' );
	if (bidAmountTextInput.value == '' )
	{
		// disable for now
		// bidAmountTextInput.value = recommendedBid;
	}

	document.getElementById( 'bid_submit' ).disabled = false;
	document.getElementById( 'buyout_submit' ).disabled = (buyoutAmount == null);

	selectedAuctionItemName = itemName;
	selectedAuctionBuyoutAmount = buyoutAmount;

}
</script>
<?
	}


	function initialise()
	{
		// set up class variables accessed later on
		$this->player = $this->auth->getMailbox();
		$this->auctionHouse = bw_look_up_entity_by_name(
			'AuctionHouse', 'AuctionHouse' );
		if (!$this->auctionHouse)
		{
			$this->addErrorMsg( "Could not contact auction house." );
		}

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

		$action = FALSE;

		// handle form action based on submit button name
		// of the form action:(.+)
		foreach( array_keys( $_REQUEST ) as $key)
		{
			$matches = Array();
			if (ereg( 'action:(.+)', $key, $matches ))
			{
				$action = $matches[1];
			}
		}

		if ($action)
		{
			$redirect = 'SearchAuctions.php?';

			// add search parameters that resulted in this action
			$firstSearchParam = TRUE;
			foreach(
				Array(
					"search_type_name",
					"search_min_bid",
					"search_max_bid",
					"search_submit"
				) as $searchParam
			)
			{
				if (!$firstSearchParam)
				{
					$redirect .= "&";
				}
				$redirect .= urlencode( $searchParam ). '='.
					urlencode( $_REQUEST[$searchParam] );
				$firstSearchParam = FALSE;
			}


			switch($action)
			{
				case "bid":
				case "buyout":
				{
					$auctionId = $_REQUEST['auction_select'];
					if (!$auctionId)
					{
						$this->addErrorMsg( "Selected auction is invalid." );
					}
					if ($action == "bid")
					{
						$this->doBidAction( $auctionId );
					}
					else // if ($action == "buyout")
					{
						$this->doBuyoutAction( $auctionId );
					}
				} break;

				default: 		break;
			}

			if ($redirect)
			{
				$this->setRedirect( $redirect );
				return;
			}
		}

		$this->doSearchAction();


		$res = bw_exec( $this->auctionHouse, 'webGetTime' );
		$this->officialTime = $res['time'];
	}

	function renderBody()
	{
		$this->renderErrorMsgs();
		$this->renderStatusMsgs();

		$this->printSearchForm();

		//echo xhtmlMpHeading( 'Official time ', 2 ). xhtmlMpPara(
		//	sprintf( "%.01f", $this->officialTime ) );

		$form = new XHTMLMpForm();
		$formContents = '';

		$searchResultsRows = $this->getSearchResultsRows();
		$playerBidRows = $this->getPlayerBidsRows();
		if ($searchResultsRows)
		{
			$formContents =
				xhtmlMpHeading( 'Search Results', 2 ).
				xhtmlMpTable( $searchResultsRows,
					'0', '', 'bidTable'
				);
		}
		else if (isset( $_REQUEST['search_submit'] ))
		{
			$formContents =
				xhtmlMpHeading( 'Search Results', 2 ).
				xhtmlMpPara( "No auctions found to match your criteria." );
		}


		$formContents .=
			xhtmlMpHeading( 'My Bids', 2 );
		if (!count( $this->playerBids ))
		{
			$formContents .= xhtmlMpPara(
				"You have made no bids. Search for items ".
				"you wish to bid for, and either enter a maximum bid or, for ".
				"nominated auctions, you may buy them out completely for the ".
				"buyout price."
			);

		}
		else
		{
			$formContents .= xhtmlMpTable(
				$playerBidRows,
				'0', '', 'tradeTable' );
		}

		$formContents .=
			xhtmlMpHeading( "Make Bid", 2 ).
			xhtmlMpTable(
				xhtmlMpTableRow(
					xhtmlMpTableCell(
						"Maximum bid: ".
						xhtmlMpFormInputText(
							'bid_amount', '', '3', '', ' id="bid_amount"'
						).
						' / '.
						xhtmlMpTag( 'b', $this->availableGold. " gold available" )
					).
					xhtmlMpTableCell(
						xhtmlMpFormSubmit(
							'action:bid', 'Bid', '',
							' disabled="true" id="bid_submit"'
						)
					)
				).
				xhtmlMpTableRow(
					xhtmlMpTableCell( '&nbsp;' ).
					xhtmlMpTableCell(
						xhtmlMpFormSubmit( 'action:buyout', 'Buyout', '',
							' disabled="true" id="buyout_submit" '.
							' onClick="return confirm( '.
								'\'Are you sure you wish to buyout this '.
								'auction of \' + '.
								'selectedAuctionItemName + '.
								'\' for \' + '.
								'selectedAuctionBuyoutAmount + '.
								'\' gold?\');" '
						)
					)
				),
				'0', '50%',
				'auctionActions'
			);

		$form->setContents( $formContents );
		// add the search criteria so that the redirection goes back to the set of
		// searched auctions
		$form->addHidden( 'search_type_name', $_REQUEST['search_type_name'] );
		$form->addHidden( 'search_min_bid', $_REQUEST['search_min_bid'] );
		$form->addHidden( 'search_max_bid', $_REQUEST['search_max_bid'] );

		echo( $form->output() );

	}

	function printSearchForm()
	{
		echo xhtmlMpHeading( 'Search Criteria', 2 );
		$form = new XHTMLMPForm();
		$form->setContents(
			xhtmlMpPara(
				'Item Type:&nbsp;'.
					xhtmlMpFormInputText( 'search_type_name',
						isset( $_REQUEST['search_type_name'] ) ?
							$_REQUEST['search_type_name'] : '',
						8 ).
				' Bid Range:&nbsp;'.
					xhtmlMpFormInputText( 'search_min_bid',
						isset( $_REQUEST['search_min_bid'] ) ?
							$_REQUEST['search_min_bid'] : '',
						3 ).
					'&nbsp;-&nbsp;'.
					xhtmlMpFormInputText( 'search_max_bid',
						isset( $_REQUEST['search_max_bid'] ) ?
							$_REQUEST['search_max_bid'] : '',
						3 ).
				' '.
				xhtmlMpFormSubmit( 'search_submit', 'Search' )
			)
		);

		$form->setClassName( 'auctionSearchForm' );
		$form->setMethod( 'get' );
		echo $form->output();


	}

	function getSearchResultsRows()
	{
		if (!$this->searchResults)
		{
			return;
		}

		$itemMgr =& ItemTypeManager::instance();


		$searchResultRows = xhtmlMpTableRow(
			xhtmlMpTableHeader( 'Item', '', ' colspan="2"').
			xhtmlMpTableHeader( 'Seller' ).
			xhtmlMpTableHeader( 'Expiry' ).
			xhtmlMpTableHeader( 'Current bid' ).
			xhtmlMpTableHeader( 'Buyout price' )
		);

		$sellerNames = Array();

		$first = '-first';
		$count = 0;
		foreach ($this->searchResults as $auctionId => $auctionInfo)
		{
			list( $itemLock, $itemType, $itemSerial ) = $auctionInfo['item'];
			$itemTypeName = $itemMgr->itemTypes[$itemType]->name;
			$itemTypeImgUrl = $itemMgr->itemTypes[$itemType]->iconImgUrl;
			$currentBid = $auctionInfo['currentBid'];
			$recommendedBid = (int) min( $currentBid + 1, 1.05 * $currentBid );

			$onClickJS = 'onClick="updateBid( '.
				$recommendedBid. ", ".
				(is_null($auctionInfo['buyoutPrice']) ?
						'null' : $auctionInfo['buyoutPrice']).
					", ".
				"'". $itemTypeName. "' );".
				'return true;"'
				;

			$cells =
				xhtmlMpTableCell(
					xhtmlMpFormInput( 'radio', 'auction_select', $auctionId,
						'', ' '.
						(($currentBid > $this->availableGold) ? 'disabled="true" ':'' ).
						$onClickJS ),
					'0'
				).
				xhtmlMpTableCell(
					xhtmlMpImg( $itemTypeImgUrl, '' ).
					$itemTypeName
				).
				xhtmlMpTableCell( $auctionInfo['playerName'] ).
				xhtmlMpTableCell(
//					sprintf( "%.01f",
//						$auctionInfo['expiry'] - $this->officialTime
//					).
//					" [".
					timeFloatToString(
						$auctionInfo['expiry'] - $this->officialTime )
//					."]"

				).
				xhtmlMpTableCell(
					xhtmlMpSpan( $auctionInfo['currentBid'],
					(($currentBid > $this->availableGold) ?
						"auctionBad" : "auctionGood" )
					)
				);

			if (is_null( $auctionInfo['buyoutPrice'] ))
			{
				$cells .= xhtmlMpTableCell( '-' );
			}
			else
			{
				$cells .= xhtmlMpTableCell( $auctionInfo['buyoutPrice'] );
			}


			$searchResultRows .= xhtmlMpTableRow(
				$cells,
				"alt". (($count++ % 2) + 1). $first
			);

			$first = FALSE;
		}

		if (!$count)
		{
			$searchResultRows .= xhtmlMpTableRow(
				xhtmlMpTableCell( "No auctions found.", FALSE, '', ' colspan="7"' ),
				'alt1-first'
			);
		}

		return $searchResultRows;

	}


	function getPlayerBidsRows()
	{
		$rows = xhtmlMpTableRow(
			xhtmlMpTableHeader( "Item", '', ' colspan="2"' ).
			xhtmlMpTableHeader( "Seller" ).
			xhtmlMpTableHeader( "Expiry" ).
			xhtmlMpTableHeader( "Current bid" ).
			xhtmlMpTableHeader( "Buyout price" ).
			xhtmlMpTableHeader( "Status" )
		);

		$itemMgr =& ItemTypeManager::instance();

		$first = "-first";
		$count = 0;
		foreach ($this->playerBids as $auctionId => $auctionInfo )
		{
			list( $itemLock, $itemType, $itemSerial ) = $auctionInfo['item'];
			$itemTypeName = $itemMgr->itemTypes[$itemType]->name;
			$itemTypeImgUrl = $itemMgr->itemTypes[$itemType]->iconImgUrl;

			$currentBid = $auctionInfo['currentBid'];
			$recommendedBid = (int) min( $currentBid + 1, 1.05 * $currentBid );

			$onClickJS = 'onClick="updateBid( '.
				$recommendedBid. ', '.
				(is_null($auctionInfo['buyoutPrice']) ?
						'null' : $auctionInfo['buyoutPrice']).
					', '.
				"'". $itemTypeName. "' ); return true;\" ";
				;

			$cells =
				xhtmlMpTableCell(
					xhtmlMpFormInput( 'radio', 'auction_select', $auctionId,
						'', " $onClickJS" ),
					'0'
				).
				xhtmlMpTableCell(
					xhtmlMpImg( $itemTypeImgUrl, $itemTypeName ).
					$itemTypeName
				).
				xhtmlMpTableCell(
					$auctionInfo['playerName']
				).
				xhtmlMpTableCell(
					timeFloatToString( $auctionInfo['expiry'] -
						$this->officialTime )
				).
				xhtmlMpTableCell( $auctionInfo['currentBid']  );
			if (!is_null( $auctionInfo['buyoutPrice'] ))
			{
				$cells .= xhtmlMpTableCell( $auctionInfo['buyoutPrice'] );
			}
			else
			{
				$cells .= xhtmlMpTableCell( '&nbsp;' );
			}
			if ($auctionInfo['highestBidder'] == $this->playerDBID)
			{
				$cells .= xhtmlMpTableCell(
					xhtmlMpSpan( "You are the highest bidder", "auctionGood" ).
					xhtmlMpSingleTag( 'br' ).
					"Max bid: ". $auctionInfo['currentMaxBid']
				);
			}
			else if (in_array( $this->playerDBID, $auctionInfo['bidders'] ))
			{
				$cells .= xhtmlMpTableCell(
					xhtmlMpSpan( "You have been outbid", 'auctionBad' )
				);
			}
			else
			{
				$cells .= xhtmlMpTableCell( "&nbsp;" );
			}

			$rows .= xhtmlMpTableRow(
				$cells,
				"alt". (($count++ % 2) + 1). $first
			);
			$first = "";
		}

		return $rows;
	}

}
// ----------------------------------------------------------------------------
// Section: Main body
// ----------------------------------------------------------------------------

$page = new SearchAuctionsPage();
$page->render();
?>
