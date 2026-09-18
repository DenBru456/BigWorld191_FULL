<?php

/**
 *	bigworld_php
 *
 *	This extension provides a mechanism with which you can call remote methods
 *	defined on base entities. It also provides a mechanism for logging players
 *	on.
 *
 *
 *	The BigWorld external extension defines the following functions.
 *
 *
 *	function bw_logon($username, $password)
 *
 *		Attempt to logon the given username and password combination. Returns
 *		TRUE on success, or an error message.
 *
 *		@param username the username
 *		@param password the password
 *		@return TRUE on success, or a string error message if it failed.
 *
 *
 *	function bw_test(...)
 *
 *		Extension module test method.
 *
 *
 *	function bw_look_up_entity_by_name($entityType, $entityName)
 *
 *		Performs a look-up on the entity with the given name.
 *
 *		@param entityType the entity type name, e.g. 'Avatar'
 *		@param entityName the entity name
 *		@return mailbox resource entity, or TRUE if entity exists but is not
 *		checked out, or FALSE if the entity does not exist
 *
 *
 *	function bw_look_up_entity_by_dbid ($entityType, $dbid)
 *
 *		Performs a look-up on the entity with the given database ID.
 *
 *		@param entityType the entity type name, e.g. 'Avatar'
 *		@param dbid the database ID of the entity
 *		@return mailbox resource entity, or TRUE if entity exists but is not
 *		checked out, or FALSE if the entity does not exist
 *
 *
 *	function bw_exec($mailbox, $methodname, ...)
 *
 *		Calls the specified method on the mailbox. Must be a Base method.
 *
 *		@param mailbox the mailbox resource for the entity
 *		@param methodname the name of the method
 *		@return array of return values, a string describing an error, or NULL
 *		if there are no return values
 *
 *
 *	function bw_set_nub_port($port)
 *
 *		Recreates the nub, using the given port.
 *
 *		@param port the port number, or 0 for a random port.
 *
 *
 *	function bw_serialise( $mailbox )
 *
 *		Serialises the given mailbox resource. You can use this to store
 *		mailboxes in the persistent session between requests, and then use
 *		bw_deserialise() to reload them as a mailbox resource.
 *
 *		@param mailbox the resource of the mailbox
 *		@return string the serialised mailbox string
 *
 *
 *	function bw_deserialise($string)
 *
 *		Deserialises the given mailbox serialised string. Use this function to
 *		retrieve mailboxes that have been serialised to the session by
 *		bw_serialise().
 *
 *		@param string the serialised mailbox string
 *		@return resource the deserialised mailbox
 *
 *
 *	function bw_pyprint ($pyResource)
 *
 *		Returns a string of the PyResource's string representation,
 *		equivalent to 'str(obj)'
 *
 *		@param pyResource	a PyObject resource
 *		@return string
 *
 *	function set_default_keep_alive_seconds( $seconds )
 *
 *		Sets the default keep-alive interval, in seconds, on new mailboxes, as
 *		returned by bw_look_up_*() class of functions.
 *
 *		@param seconds	the new default keep-alive interval, in seconds 
 *
 *	function set_keep_alive_seconds( $mailbox, $seconds )
 *
 *		Sets the keep-alive interval, in seconds, on this mailbox. If $seconds
 *		is 0, then no keep-alive interval is set. A keep-alive message is
 *		immediately sent if $seconds is not 0.
 *
 *	function get_keep_alive_seconds( $mailbox )
 *
 *		Gets the keep-alive interval, in seconds, on this mailbox. 
 */
if (!extension_loaded( 'bigworld_php' ))
{
	dl( 'bigworld_php.' . PHP_SHLIB_SUFFIX );
}

?>
