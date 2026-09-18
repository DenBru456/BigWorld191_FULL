<?php
require_once ( 'Debug.php' );
require_once ( 'Constants.php' );
require_once ( 'XHTML-MP-functions.php' );
require_once( 'Util.php');
error_reporting( E_ALL );


class XHTMLMPPage
{
    var $contentType;
    var $docType;
    var $title;
    var $styleHref;

    var $redirect;

    var $initTime;
    var $renderBodyTime;

    function XHTMLMPPage( $title )
	{
        $this->title = $title;
        $this->docType = DOCTYPE_HTML;
        $this->contentType = CONTENTTYPE_HTML;

        $this->styleHrefs = Array( DEFAULT_STYLE );
		if ($this->getDevice() == "Sony PlayStation Portable")
		{
			$this->styleHrefs = Array( 'styles/psp/fantasydemo.css' );
		}
		else if ($this->getDevice() == "Research In Motion Ltd. BlackBerry 7100")
		{
			$this->styleHrefs = Array( 'styles/blackberry/fantasydemo.css' );
		}

        $this->redirect = false;

        $this->initTime = 0;
        $this->renderBodyTime = 0;
    }

	function getDevice()
	{
		if (isset( $_SESSION['useragent-info'] ))
		{
			return $_SESSION['useragent-info']['brand_name'].
				' '.
				$_SESSION['useragent-info']['model_name'];
		}

		return FALSE;
	}

    function initialise()
	{
        // do nothing - override in subclasses to process
        // request variables
    }

    function setRedirect($url)
	{
        $this->redirect = $url;
    }

    function renderHead()
	{
        echo( xhtmlMpTag( 'title', $this->title ) );

        foreach ($this->styleHrefs as $styleHref)
		{
        	$attrString = '';
	        $attrString = xhtmlMpAddAttribute( $attrString, 'rel',
    	        'stylesheet' );
			$attrString = xhtmlMpAddAttribute( $attrString, 'href',
            	$styleHref );
        	echo( xhtmlMpSingleTag( 'link', '', $attrString ). "\n" );
		}

    }

    function renderBody()
	{
    }

    function doInitialise()
	{
        $initStart = gettimeofday();
        $this->initialise();
        $initFinish = gettimeofday();
        $this->initTime = timeofdayDiffMs( $initStart, $initFinish );
    }

    function doRenderBody()
	{
        $renderBodyStart = gettimeofday();
        $this->renderBody();
        $renderBodyFinish = gettimeofday();

        $this->renderBodyTime = timeofdayDiffMs(
			$renderBodyStart, $renderBodyFinish );
    }

    function doRenderHead()
	{
        $this->renderHead();
    }

    function render()
	{
		deferErrorPrinting( TRUE );

		$this->doInitialise();
        if ($this->redirect)
		{
            header( 'Location: '. $this->redirect );
            exit;
        }
    //    header( 'Content-Type: '. $this->contentType );

		echo( "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n" );
        echo( $this->docType."\n" );

		echo( "<html>\n" );

		deferErrorPrinting( FALSE );

		debug( "PHP_SELF: ". $_SERVER['PHP_SELF'] );

        echo( "<head>\n" );

        $this->renderHead();
        echo( "</head>\n" );

        echo( "<body>\n" );

        $this->doRenderBody();

        echo( "</body>\n" );

        debug( 'Init time: ' . $this->initTime. 'ms'.
            "\nRenderBody time: ". $this->renderBodyTime. 'ms' );
        echo( "</html>\n" );
    }
}
?>
