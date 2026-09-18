<?php
require_once( 'Debug.php' );
require_once( WURFL_DIR. '/wurfl_config.php' );
require_once( WURFL_DIR. '/'. WURFL_CLASS_FILE );

if (!isset( $_SESSION['display'] ))
{
	// query WURFL for user agent device capabilities
	$wurflObj = new wurfl_class( $wurfl, $wurfl_agents );
	$headers = apache_request_headers();
	foreach ($headers as $key => $value)
	{
		// add lowercase ones too (e.g. as the blackberry sends them)
		$headers[strtolower($key)] = $value;
	}
	if (isset( $headers['user-agent'] ) && $headers['user-agent'] != '')
	{
		$_SESSION['user_agent'] = $headers['user-agent'];

		$wurflObj->GetDeviceCapabilitiesFromAgent( $headers['user-agent'] );
		
		if (isset( $wurflObj->capabilities['product_info'] ))
		{
			$_SESSION['useragent-info'] = 
				$wurflObj->capabilities['product_info'];

			if ($wurflObj->capabilities['product_info']['is_wireless_device'])
			{
				if (isset( $wurflObj->capabilities['display'] ))
				{
					$_SESSION['display'] = $wurflObj->capabilities['display'];
				}
			}
		}
	}
}
?>
