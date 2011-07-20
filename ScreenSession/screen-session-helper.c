/*    
 *    Copyright (C) 2010-2011 Artur Skonecki
 *
 *    Authors: Artur Skonecki http://github.com/skoneka
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
 *       Filename:  screen-session-helper.c
 *
 *    Description:  regions tool helper application
 *
 *        Version:  1.0
 *        Created:  02.08.2010 18:21:25
 *       Revision:  none
 *       Compiler:  gcc
 *
 * =====================================================================================
 */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <termios.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>
#include <dirent.h>
#include <limits.h>
#include <signal.h>

#include "screen-session-define.h"

/* defining _POSIX_SOURCE causes compilation errors on solaris  */
int kill (int pid, int sig);

#define FONTHEIGHT 7
#define FONTWIDTH 6
char *fonts[] = {
  /*  */
  " $$$$ ",
  "$$  $$",
  "$$  $$",
  "$$  $$",
  "$$  $$",
  "$$  $$",
  " $$$$ ",
  /*  */
  "   $$$",
  "  $$$$",
  " $$$$$",
  "    $$",
  "    $$",
  "    $$",
  "    $$",
  /*  */
  " $$$$ ",
  "$$  $$",
  "    $$",
  "   $$ ",
  "  $$  ",
  " $$   ",
  "$$$$$$",
  /*  */
  "$$$$$ ",
  "    $$",
  "   $$ ",
  " $$$  ",
  "   $$ ",
  "    $$",
  "$$$$$ ",
  /*  */
  "$$  $$",
  "$$  $$",
  "$$  $$",
  "$$$$$$",
  "    $$",
  "    $$",
  "    $$",
  /*  */
  "$$$$$$",
  "$$    ",
  "$$    ",
  "$$$$$$",
  "    $$",
  "    $$",
  "$$$$$$",
  /*  */
  "$$$$$$",
  "$$    ",
  "$$    ",
  "$$$$$$",
  "$$  $$",
  "$$  $$",
  "$$$$$$",
  /*  */
  "$$$$$$",
  "    $$",
  "    $$",
  "    $$",
  "    $$",
  "    $$",
  "    $$",
  /*  */
  "$$$$$$",
  "$$  $$",
  "$$  $$",
  "$$$$$$",
  "$$  $$",
  "$$  $$",
  "$$$$$$",
  /*  */
  "$$$$$$",
  "$$  $$",
  "$$  $$",
  "$$$$$$",
  "    $$",
  "    $$",
  "$$$$$$",
  /*  */
  "      ",
  "      ",
  "      ",
  "      ",
  "      ",
  "      ",
  "      ",
  /*  */
  "      ",
  "$    $",
  " $  $ ",
  "  $$  ",
  "  $$  ",
  " $  $ ",
  "$    $",
};

int
mygetch (void)
{
  int ch;
  struct termios oldt, newt;

  tcgetattr (STDIN_FILENO, &oldt);
  newt = oldt;
  newt.c_cc[VMIN] = 1;
  newt.c_cc[VTIME] = 0;
  newt.c_lflag &= ~(ICANON | ECHO);
  tcsetattr (STDIN_FILENO, TCSANOW, &newt);
  ch = getchar ();
  tcsetattr (STDIN_FILENO, TCSANOW, &oldt);

  return ch;
}

int
getinput (int *prefix, char *mode)
{
  char prefix_str[10];
  int prefix_str_c = 0;
  char ch;
  prefix_str[0] = '\0';
  while (1)
    {
      ch = mygetch ();
      if (ch >= '0' && ch <= '9' && prefix_str_c < 10)
	{
	  prefix_str[prefix_str_c] = ch;
	  prefix_str_c++;
	  prefix_str[prefix_str_c] = '\0';
	}
      else
	{
	  *mode = ch;
	  break;
	}

    }
  if (prefix_str_c > 0)
    *prefix = atoi (prefix_str);
  else
    *prefix = 1;
  return 0;
}

char **
get_font (char c)
{
  char **font = NULL;
  switch (c)
    {
    case '0':
      font = &fonts[0 * FONTHEIGHT];
      break;
    case '1':
      font = &fonts[1 * FONTHEIGHT];
      break;
    case '2':
      font = &fonts[2 * FONTHEIGHT];
      break;
    case '3':
      font = &fonts[3 * FONTHEIGHT];
      break;
    case '4':
      font = &fonts[4 * FONTHEIGHT];
      break;
    case '5':
      font = &fonts[5 * FONTHEIGHT];
      break;
    case '6':
      font = &fonts[6 * FONTHEIGHT];
      break;
    case '7':
      font = &fonts[7 * FONTHEIGHT];
      break;
    case '8':
      font = &fonts[8 * FONTHEIGHT];
      break;
    case '9':
      font = &fonts[9 * FONTHEIGHT];
      break;
    case ' ':
      font = &fonts[10 * FONTHEIGHT];
      break;
    default:
      font = &fonts[11 * FONTHEIGHT];
      break;
    }
  return font;
}
void
print_number (char *n, char *color)
{
  char ***font = malloc ((strlen (n) + 1) * sizeof (char ***));
  int letter_c = 0;
  while (n[letter_c] != '\0')
    {
      font[letter_c] = get_font (n[letter_c]);
      letter_c++;
    }
  int k;
  int j;
  printf ("%s", color);
  for (k = 0; k < FONTHEIGHT; k++)
    {
      for (j = 0; j < letter_c; j++)
	{
	  printf ("%s ", font[j][k]);
	}
      printf ("\n");
    }
  printf ("%s", none);
}

void
regions_helper (char *fname, char *n)
{
  int pid = -1;
  char *pch = NULL;
  pch = strrchr (fname, '-');
  if (pch)
    {
      pid = atoi (pch + 1);
//        printf("signal %d",pid);
//        kill(pid,SIGUSR2);
    }
  else
    {
      printf ("BAD ARGUMENTS");
      return;
    }
  if (n[0] == '0')
    {
      print_number ("0", red);
printf ("\
goto:\t [number]<space><g><'>\n\
swap:\t [number]<s> \n\
rotate left:\t [number]<l>\n\
rotate right:\t [number]<r>\n\
");
    }
  else
    {
      print_number (n, green);
    }
  int prefix;
  char mode;
  getinput (&prefix, &mode);
  if (mode == '\n')
    mode = 'e';
  /*
  printf ("prefix: %d ; ", prefix);
  printf ("mode: %c\n", mode);
  */
  FILE *f = fopen (fname, "w");
  fprintf (f, "%c%d", mode, prefix);
  fclose (f);
  kill (pid, SIGUSR1);
  mygetch();

}
#ifndef TEST
int
main (int argc, char **argv)
{
  if (argc == 1)
    {
      printf ("screen-session %s helper program\n",VERSION);
      return 0;
    }
  else if (strcmp (argv[1], "-n") == 0)
    {
      //print number
      print_number (argv[2], none);
      return 0;
    }
  else if (strcmp (argv[1], "-nh") == 0)
    {
      //regions helper
      regions_helper (argv[2], argv[3]);
      return 0;
    }
  else {
      printf ("screen-session %s helper program\n",VERSION);
  }
}

#endif
