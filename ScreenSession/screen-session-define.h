/*    
 *    Copyright (C) 2010-2011 Artur Skonecki
 *
 *    Authors: Artur Skonecki <admin [>at<] adb.cba.pl>
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU General Public License as published by
 *    the Free Software Foundation, version 3 of the License.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 * =====================================================================================
 *
 *       Filename:  screen-session-define.h
 *
 *    Description:  header file for screen-session-primer.c and screen-session-helper.c
 *
 *        Version:  1.0
 *        Created:  02.08.2010 18:21:25
 *       Revision:  none
 *       Compiler:  gcc
 *
 * =====================================================================================
 */
#include <assert.h>

#ifdef COLOR			/* if you dont want color remove '-DCOLOR' from config.mk */
#define cyan_b  "\033[1;36m"	/* 1 -> bold ;  36 -> cyan */
#define green_u "\033[4;32m"	/* 4 -> underline ;  32 -> green */
#define blue_s  "\033[9;34m"	/* 9 -> strike ;  34 -> blue */
#define blue_b  "\033[1;34m"
#define blue_r  "\033[7;34m"
#define green_b "\033[1;32m"
#define green_r "\033[7;32m"
#define red_b   "\033[1;31m"
#define red_r   "\033[7;31m"
#define red_s   "\033[9;31m"
#define brown_r  "\033[7;33m"

#define red   "\033[0;31m"	/* 0 -> normal ;  31 -> red */
#define green "\033[0;32m"
#define blue  "\033[0;34m"	/* 9 -> strike ;  34 -> blue */
#define black  "\033[0;30m"
#define brown  "\033[0;33m"
#define magenta  "\033[0;35m"
#define gray  "\033[0;37m"

#define none   "\033[0m"	/* to flush the previous property */
#else
#define cyan_b     ""
#define green_u    ""
#define blue_s     ""
#define blue_b     ""
#define blue_r     ""
#define green_b    ""
#define green_r    ""
#define red_b      ""
#define red_r      ""
#define red_s      ""

#define red        ""
#define green      ""
#define blue       ""
#define black      ""
#define brown      ""
#define magenta    ""
#define gray       ""

#define none       ""
#endif

#define VIM_SESSION "_session"
#define VIM_INFO "_info"

#define SEP green_r"|"none

#define PRIMER green"PRIMER: "none
#define USERINPUTMAXBUFFERSIZE   80
#define CMDLINE_BEGIN 20
#define BLACKLISTMAX 100
#define BASEDATA_LINES 8
#define PROCLINES 7

#define SAFE_FREE(pt)\
    assert(pt!=NULL);\
    free(pt);\
    pt = NULL;
#define SAFE_PTR(pt) assert(pt!=NULL); pt
