/******************************************************************************
BigWorld Technology
Copyright BigWorld Pty, Ltd.
All Rights Reserved. Commercial in confidence.

WARNING: This computer program is protected by copyright law and international
treaties. Unauthorized use, reproduction or distribution of this program, or
any portion of this program, may result in the imposition of civil and
criminal penalties as provided by law.
******************************************************************************/

/*
 * The start-up code that interfaces to the Win32 API.
 *
 * Two functions defined in this file: WinMain and WndProc.
 * WinMain is the entry point in Windows. WndProc is the callback function to
 * handle window messages..
 *
 */


#include "pch.hpp"

#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include "client/bw_winmain.hpp"
#include "pyscript/script.hpp"
#include "resource.h"


DECLARE_DEBUG_COMPONENT2( "App", 0 )


//
//	Application Specific Definitions:
//	Some pre-processing and debug defines for the application.
//
static const LPCTSTR APP_NAME = "App";

#if defined( _DEBUG )
const char * APP_TITLE = "BigWorld Client Debug Version";
#elif defined( _HYBRID )
  #if defined( _EVALUATION )
    const char * APP_TITLE = "BigWorld Client Evaluation Version";
  #else
    const char * APP_TITLE = "BigWorld Client Hybrid Version";
  #endif
#else
const char * APP_TITLE = "BigWorld Client Release Version";
#endif



LRESULT CALLBACK WndProc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam);

// Defined in compile_time.cpp
extern const char * compileTimeString;



#if BWCLIENT_AS_PYTHON_MODULE

HINSTANCE g_hinstance;

BOOL WINAPI DllMain( HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpReserved )
{
	g_hinstance = hinstDLL;
	
	// Perform actions based 
	// on the reason for calling.
	switch( fdwReason ) 
	{ 
	case DLL_PROCESS_ATTACH:
		break;

	case DLL_THREAD_ATTACH:
		break;

	case DLL_THREAD_DETACH:
		break;

	case DLL_PROCESS_DETACH:
		break;
	}
	return TRUE;  // Successful DLL_PROCESS_ATTACH.
}


static PyObject * py_bwclient_run( PyObject * self, PyObject * args )
{
	BW_GUARD;
	char * commandline = NULL;
	int ok = PyArg_ParseTuple(args, "s", &commandline);

	// Set up the window class
	HCURSOR cursor = LoadCursor( g_hinstance, MAKEINTRESOURCE(IDC_NULL) );
	WNDCLASS wc = { CS_HREDRAW | CS_VREDRAW, WndProc, 0, 0, g_hinstance, NULL,
					// LoadIcon( hInst, MAKEINTRESOURCE(IDI_BIGWORLD_ICON)),
					cursor, NULL, NULL, APP_NAME };
	if( !RegisterClass( &wc ) )
		return FALSE;

	BWWinMain( g_hinstance, commandline, SW_SHOWNORMAL, APP_NAME, APP_TITLE );


	Py_RETURN_NONE;
};


static PyMethodDef bwclient_methods[] = {
	{"run", py_bwclient_run, METH_VARARGS, "run( commandline )"},
	{NULL, NULL}
};


#define PY_MODULE_INIT_IMP(MODULE_NAME)                \
	PyMODINIT_FUNC init##MODULE_NAME()                 \
	{                                                  \
		Py_InitModule(#MODULE_NAME, bwclient_methods); \
	}
	
#define PY_MODULE_INIT(MODULE_NAME)                    \
	PY_MODULE_INIT_IMP(MODULE_NAME)

// BWCLIENT_NAME can be defined in the project 
// settings (C++/Preprocessor) using the $(TargetName) 
// macro: /D "BWCLIENT_NAME=$(TargetName).
PY_MODULE_INIT( BWCLIENT_NAME )


#else // BWCLIENT_AS_PYTHON_MODULE

//-----------------------------------------------------------------------------
// WinMain()
// Desc: Application entry point.
//-----------------------------------------------------------------------------
int PASCAL WinMain(	HINSTANCE hInstance,
					HINSTANCE hPrevInstance,
					LPSTR lpCmdLine,
					int nCmdShow )
{
	BW_GUARD_BEGIN;


    // Set up the window class
	HCURSOR cursor = LoadCursor( hInstance, MAKEINTRESOURCE(IDC_NULL) );
    WNDCLASS wc = { CS_HREDRAW | CS_VREDRAW, WndProc, 0, 0, hInstance, NULL,
                    // LoadIcon( hInst, MAKEINTRESOURCE(IDI_BIGWORLD_ICON)),
					cursor, NULL, NULL, APP_NAME };

    if( !RegisterClass( &wc ) )
        return FALSE;

#if ENABLE_STACK_TRACKER
	__try
#endif
	{
		return BWWinMain(	hInstance,
							lpCmdLine,
							nCmdShow,
							APP_NAME,
							APP_TITLE );
	}

#if ENABLE_STACK_TRACKER 
	__except( ExceptionFilter(GetExceptionCode()) )
	{
	}

	BW_GUARD_END;
	return -1;
#endif
}

#endif // BWCLIENT_AS_PYTHON_MODULE


//-----------------------------------------------------------------------------
// Name: WndProc()
// Desc: Window procedure for the game window
//-----------------------------------------------------------------------------
LRESULT CALLBACK WndProc( HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam )
{
	return BWWndProc( hWnd, msg, wParam, lParam );
}




// winmain.cpp
