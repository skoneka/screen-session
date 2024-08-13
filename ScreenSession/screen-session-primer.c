#define _POSIX_C_SOURCE 200809L
/*
 *    Copyright (C) 2010-2011 Artur Skonecki http://github.com/skoneka
 *
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU General Public License as published by
 *    the Free Software Foundation, version 3 of the License.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY;
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 * =====================================================================================
 *
 *       Filename:  screen-session-primer.c
 *
 *    Description:  session saver helper application,
 *                  primes windows during Screen session loading
 *
 *        Version:  1.0
 *        Created:  02.08.2010 18:21:25
 *       Revision:  none
 *       Compiler:  gcc
 *
 * =====================================================================================
 */

char help_str[] = "\
This is a program which \"primes\" other processes saved by screen-session.\n\
Description of possible actions:\n\
Key      | Arguments | Description\n\
----------------------------------\n\
[A]ll    |           | try to restart all saved processes\n\
[Z]ombie |           | run the zombie command vector\n\
[Q]uit   |           | terminate primer\n\
[D]efault|           | start $SHELL in the last working directory\n\
[R]eset  |           | reload primer\n\
[E]dit   |           | edit primer's source file with $EDITOR\n\
         |[number]   | try to restart saved processes up to [number]\n\
[O]nly   |[numbers..]| select processes which will be restarted\n\
[F]ilter |           | toggle filter ( :exec ) restoring\n\
\n\
Scrollback will not be reread if the KEY letter is uppercase.\n\
";

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
#include <libgen.h>

#include "screen-session-define.h"

int blacklist[BLACKLISTMAX];
int blacklist_c = 0;
char *scs_exe = NULL;

enum menu
{
  NONE = 0,
  RESET,
  ZOMBIE,
  EXIT,
  ALL,
  ONLY,
  NUMBER,
  EDIT,
  DEFAULT
};

int
copy_file (char *inputfile, char *outputfile)
{
  FILE *filer = NULL, *filew = NULL;
  int numr, numw;
  char buffer[100];

  if ((filer = fopen (inputfile, "rb")) == NULL) {
    fprintf (stderr, "open read file error.\n");
    return 1;
  }

  if ((filew = fopen (outputfile, "wb")) == NULL) {
    fprintf (stderr, "open write file error.\n");
    return 1;
  }
  while (feof (filer) == 0) {
    if ((numr = fread (buffer, 1, 100, filer)) != 100) {
      if (ferror (filer) != 0) {
	fprintf (stderr, "read file error.\n");
	return 1;
      }
      else if (feof (filer) != 0);
    }
    if ((numw = fwrite (buffer, 1, numr, filew)) != numr) {
      fprintf (stderr, "write file error.\n");
      return 1;
    }
  }

  fclose (filer);
  fclose (filew);
  return 0;
}

void
print_cmd (int cmdargs_s, char *cmdargs)
{
  int i = 0;
  while (i < cmdargs_s) {
    if (cmdargs[i] == '\0') {
      if (cmdargs[i + 1] == '\0')
	break;
      else
	fputc (',', stdout);
    }
    else
      fputc (cmdargs[i], stdout);
    i++;
  }
  fputc ('\n', stdout);
}

void
print_ints (int *numbers, int n)
{
  int i;
  for (i = 0; i < n; i++) {
    printf ("%d ", numbers[i]);
  }
}
int
line_to_string (FILE * fp, char **line, size_t * size)
{
  int rc;
  void *p = NULL;
  size_t count;

  count = 0;
  while ((rc = getc (fp)) != EOF) {
    ++count;
    if (count + 2 > *size) {
      p = realloc (*line, count + 2);
      if (p == NULL) {
	if (*size > count) {
	  (*line)[count] = '\0';
	  (*line)[count - 1] = (char) rc;
	}
	else {
	  ungetc (rc, fp);
	}
	count = 0;
	break;
      }
      *line = p;
      *size = count + 2;
    }
    if (rc == '\n') {
      (*line)[count - 1] = '\0';
      break;
    }
    (*line)[count - 1] = (char) rc;
  }
  if (rc != EOF) {
    rc = count > INT_MAX ? INT_MAX : count;
  }
  else {
    if (*size > count) {
      (*line)[count] = '\0';
    }
  }
  return rc;

}

int
mygetline (char **lineptr, size_t * n, FILE * stream)
{
  return line_to_string (stream, lineptr, n);
}


/*----------trim (char) c from right-side of string *p------------------*/
char *
strtrim_right (register char *p, register char c)
{
  register char *end;
  register int len;

  len = strlen (p);
  while (*p && len) {
    end = p + len - 1;
    if (c == *end)
      *end = 0;
    else
      break;
    len = strlen (p);
  }
  return (p);
}

int
DirectoryExists (const char *pzPath)
{
  if (pzPath == NULL)
    return 0;

  DIR *pDir;
  int bExists = 0;

  pDir = opendir (pzPath);

  if (pDir != NULL) {
    bExists = 1;
    (void) closedir (pDir);
  }

  return bExists;
}

int
file_exists (const char *filename)
{
  FILE *file = NULL;
  if ((file = fopen (filename, "r"))) {
    fclose (file);
    return 1;
  }
  return 0;
}

char *
get_session (const char *file_in_session)
{
  char *file = malloc ((strlen (file_in_session) + 1) * sizeof (char));
  char *session = malloc ((strlen (file_in_session) + 1) * sizeof (char));

  strcpy (file, file_in_session);


  char *pch = NULL;
  pch = strtok (file, "/");
  if (pch)
    strcpy (session, pch);
  SAFE_FREE (file);
  return session;
}

int
requireSession (const char *basepath, const char *file_in_session, int force)
{
  char *file = malloc ((strlen (file_in_session) + 1) * sizeof (char));
  char *session = malloc ((strlen (file_in_session) + 5) * sizeof (char));
  char *basedir = malloc ((strlen (basepath) + 1) * sizeof (char));

  strcpy (basedir, basepath);
  strcpy (file, file_in_session);


  char *pch = NULL;
  pch = strtok (file, "/");
  if (pch)
    strcpy (session, pch);
  else {
    SAFE_FREE (file);
    SAFE_FREE (session);
    SAFE_FREE (basedir);
    return 1;
  }

  char *filepath =
    malloc ((strlen (basedir) + strlen (session) + 2) * sizeof (char));
  char *testfilepath =
    malloc ((strlen (basedir) + strlen (file_in_session) + 2) * sizeof (char));
  strcpy (filepath, basedir);
  strcat (filepath, "/");
  strcat (filepath, session);

  strcpy (testfilepath, basedir);
  strcat (testfilepath, "/");
  strcat (testfilepath, file_in_session);
  if (!force && file_exists (testfilepath)) {
    SAFE_FREE (file);
    SAFE_FREE (filepath);
    SAFE_FREE (testfilepath);
    SAFE_FREE (session);
    SAFE_FREE (basedir);
    return 0;
  }
  else {
    SAFE_FREE (filepath);
    char *buf =
      malloc ((strlen (scs_exe) + strlen (basedir) + strlen (session) + 1 +
	       30) * sizeof (char));
    printf (PRIMER "unpacking: %s\n", session);
    sprintf (buf, "%s other --dir \"%s\" --unpack \"%s\"", scs_exe, basedir,
	     session);
    system (buf);
    SAFE_FREE (file);
    SAFE_FREE (buf);
    SAFE_FREE (session);
    SAFE_FREE (basedir);
    return 0;
  }
}



void
cleartoendofline (void)
{
  char ch;
  ch = getchar ();
  while (ch != '\n')
    ch = getchar ();
}

int
parseNumber (char *buffer)
{
  int number;
  char *p = NULL;
  number = strtol (buffer, &p, 0);
  if (strcmp ("", p) != 0) {
    return -1;
  }
  else if (errno == ERANGE) {
    return -1;
  }
  else if (errno == EINVAL) {
    return -1;
  }
  number = atoi (buffer);
  if ((number < 0))
    number = 0;
  return number;
}



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

char * gen_fullpath(char *homedir, char *workingdir) {
      char *fullpath =
          malloc ((strlen (homedir) + strlen (workingdir) + 2) * sizeof (char));
      strcpy (fullpath, homedir);
      strcat (fullpath, "/");
      strcat (fullpath, workingdir);
      return fullpath;
}



int
userInput (int *menu_num, int **num, int max, int *bFilter, int *bScrollback)
{
  char ch;			/* handles user input */
  char buffer[USERINPUTMAXBUFFERSIZE];	/* sufficient to handle one line */
  int char_count;		/* number of characters read for this line */
  int exit_flag = 0, valid_choice, number = 0;
  enum menu menu_choice = NONE;
  int *args = malloc (USERINPUTMAXBUFFERSIZE * sizeof (int));
  int args_index = 0;
  int show_filter = *bFilter;

  while (exit_flag == 0 && menu_choice == NONE) {
    valid_choice = 0;
    while (valid_choice == 0) {
      printf
	("%sRESTORE:%s [%sA%s]ll " SEP " [%sZ%s]ombie " SEP " [%sQ%s]uit "
	 SEP " [%sD%s]efault " SEP " [%sR%s]eset " SEP " [%snumber%s] "
	 SEP " [%sO%s]nly [%snumbers%s] " SEP " [%sE%s]dit " SEP
	 " [%sH%s]elp ", green, none, red_b, none, red_b, none, red_b,
	 none, red_b, none, red_b, none, blue, none, red_b, none, blue,
	 none, red_b, none, red_b, none);
      if (show_filter)
	printf (SEP " [%sF%s]ilter %s", red_b, none,
		(*bFilter) ? "OFF" : "ON");

      printf ("%s?>%s ", green_r, none);
      ch = getchar ();
      char_count = 0;
      char menu = ch;
      if (menu >= '1' && menu <= '9') {
	ungetc (menu, stdin);
	menu = 'N';
      }
      args_index = 0;
      args[args_index] = -1;
      int got_number = 0;
      while ((char_count < USERINPUTMAXBUFFERSIZE)) {
	ch = getchar ();
	if (ch != ' ' && ch != '\n') {
	  buffer[char_count++] = ch;
	  buffer[char_count] = '\0';
	  got_number = 1;
	}
	else if (got_number) {
	  args[args_index] = parseNumber (buffer);
	  args_index =
	    (args[args_index] > (-1)) ? (args_index + 1) : (args_index);
	  char_count = 0;
	  got_number = 0;
	}
	if (ch == '\n')
	  break;
      }
      args_index--;
      buffer[char_count] = 0x00;	/* null terminate buffer */
      switch (menu) {
      case 'Z':
        *bScrollback = !bScrollback;
      case 'z':
      case '0':
	number = 0;
	valid_choice = 1;
	menu_choice = ZOMBIE;
	args[0] = 0;
	args_index = 0;
	break;
      case 'r':
      case 'R':
	number = -1;
	valid_choice = 1;
	menu_choice = RESET;
	break;
      case 'D':
        *bScrollback = !bScrollback;
      case 'd':
	number = -1;
	valid_choice = 1;
	menu_choice = DEFAULT;
	break;
      case 'A':
        *bScrollback = !bScrollback;
      case 'a':
	number = -1;
	menu_choice = ALL;
	valid_choice = 1;
	break;
      case 'O':
        *bScrollback = !bScrollback;
      case 'o':
      case '/':
	menu_choice = ONLY;
	number = args[0];
	if (number == -1)
	  valid_choice = 0;
	else if (number > max)
	  valid_choice = 0;
	else
	  valid_choice = 1;
	break;
      case 'e':
      case 'E':
	menu_choice = EDIT;
	valid_choice = 1;
	break;
      case 'q':
      case 'Q':
	menu_choice = EXIT;
	valid_choice = 1;
	break;
      case 'N':
        *bScrollback = !bScrollback;
      case 'n':
	menu_choice = NUMBER;
	number = args[0];
	if (number == -1)
	  valid_choice = 0;
	else if (number > max)
	  valid_choice = 0;
	else
	  valid_choice = 1;
	break;
      case 'f':
      case 'F':
	*bFilter = (*bFilter) ? 0 : 1;
	printf ("Filter turned %s\n", (*bFilter) ? "OFF" : "ON");
	menu_choice = NONE;
	valid_choice = 0;
	break;
      case '?':
      case 'h':
      case 'H':
	printf ("%s", help_str);
	valid_choice = 0;
	menu_choice = NONE;
      default:
	menu_choice = NONE;
	valid_choice = 0;
	break;
      }


    }
  }
  *num = args;
  *menu_num = menu_choice;
  return args_index + 1;
}

char **
make_arglist (char *program, char *arg1, char *arg2, char *arg3, int procs_n,
	      int *procs)
{
  int i;
  char **args = NULL;
  char buf[10];
  args = malloc ((5 + procs_n) * sizeof (char *));
  args[0] = malloc ((strlen (program) + 1) * sizeof (char));
  args[1] = malloc ((strlen (arg1) + 1) * sizeof (char));
  args[2] = malloc ((strlen (arg2) + 1) * sizeof (char));
  /* has to pass program name because nested programs do not get name in argv[0] */
  args[3] = malloc ((strlen (program) + 1) * sizeof (char));
  args[4] = malloc ((strlen (arg3) + 1) * sizeof (char));
  for (i = 5; i < procs_n + 5; i++) {
    int i_procs = i - 5;
    int blacklisted = 0;
    int j;
    for (j = 0; j < blacklist_c; j++) {
      if (blacklist[j] == procs[i_procs]) {
	blacklisted = 1;
	break;
      }
    }
    if (blacklisted)
      break;
    sprintf (buf, "%d", procs[i_procs]);
    args[i] = malloc ((strlen (buf) + 1) * sizeof (char));
    strcpy (args[i], buf);
  }
  strcpy (args[0], program);
  strcpy (args[1], arg1);
  strcpy (args[2], arg2);
  strcpy (args[3], program);
  strcpy (args[4], arg3);
  args[procs_n + 5] = NULL;
  return args;
}


int
filesearch_line (FILE * fp, char *s)
{
  fseek (fp, 0, SEEK_SET);
  char line[CMDLINE_BEGIN];
  int nl_c = 0;
  int line_c = 0;
  char c;

  while ((c = fgetc (fp)) != EOF) {
    if (c == '\n') {
      if (strncmp (s, line, line_c) == 0)
	return 1;
      nl_c++;
      line_c = 0;
    }
    else {
      line[line_c] = c;
      line_c++;
      line[line_c] = 0;

    }
  }
  if (line_c != 0) {
    if (strncmp (s, line, line_c))
      return 1;
  }

  return 0;
}

int
is_blacklisted (char *basedir, char *program, int programid)
{
  char *blackfile = "BLACKLIST";
  char *filepath =
    malloc ((strlen (basedir) + strlen (blackfile) + 2) * sizeof (char));
  strcpy (filepath, basedir);
  strcat (filepath, "/");
  strcat (filepath, blackfile);
  FILE *fp = NULL;
  fp = fopen (filepath, "r");

  if (!fp) {
    /*
       fprintf (stderr,PRIMER": %s:%d Cannot open blacklist '%s'.\n",__FILE__,__LINE__, filepath);
       perror("Error :");
     */
    SAFE_FREE (filepath);
    return 0;
  }
  else
    SAFE_FREE (filepath);
  int ret = filesearch_line (fp, program);
  if (ret) {
    blacklist[blacklist_c] = programid;
    blacklist_c++;
  }
  fclose (fp);
  return ret;
}

void
recurse_chdir (char *path)
{
  /*
     use if the chdir() directory might not exist anymore
   */
  int s;
  s = chdir (path);
  if (s == -1) {
    char *npath = dirname (path);
    if (strcmp (npath, ".") == 0)
      return;
    else
      recurse_chdir (npath);
  }
  return;
}

int
start (char *basedir, char *thisprogram, char *config, int procs_n,
       int *procs)
{
  if (procs_n == 0)
    return 0;
  size_t proc_cwd_s = 1;
  size_t proc_exe_s = 1;
  size_t proc_vim_s = 1;
  char *proc_cwd = malloc (proc_cwd_s * sizeof (char));
  char *proc_exe = malloc (proc_exe_s * sizeof (char));
  char *proc_vim = malloc (proc_vim_s * sizeof (char));
  int proc_args_n;
  char proc_blacklisted[7];
  char **proc_args = NULL;
  int i, nl_c = 0;
  char c;
  FILE *fp = NULL;
  chdir (basedir);
  requireSession (basedir, config, 0);

  fp = fopen (config, "r");

  if (!fp) {

    fprintf (stderr, PRIMER ": %s:%d Cannot open data file. Aborting.\n",
	     __FILE__, __LINE__);
    perror ("Error :");
    printf ("Press any key to continue...\n");
    mygetch ();
    return 1;
  }

  /* skip irrelevant lines */
  while ((c = fgetc (fp)) != EOF) {
    if (c == '\n') {
      nl_c++;
    }
    else if (nl_c > (BASEDATA_LINES + (procs[0] * PROCLINES)))
      break;
  }
  c = fgetc (fp);
  mygetline (&proc_cwd, &proc_cwd_s, fp);	/* CWD */
  proc_cwd = strtrim_right (proc_cwd, '\n');
  printf (PRIMER "CWD(%s) starting: ", proc_cwd);
  mygetline (&proc_exe, &proc_exe_s, fp);	/* EXE - executable path */
  proc_exe = strtrim_right (proc_exe, '\n');
  fscanf (fp, "%d\n", &proc_args_n);	/* The number of program arguments */
  if (procs_n > 1) {
    proc_args_n += 2;
  }
  proc_args = malloc ((proc_args_n + 5) * sizeof (char *));

  long file_pos = ftell (fp);
  size_t buf_size = 1;
  char *buf = malloc (buf_size * sizeof (char));
  mygetline (&buf, &buf_size, fp);
  fseek (fp, file_pos, SEEK_SET);
  int l = 0, prev_l = 0;

  /* allocate memory for program arguments */
  for (i = 0; i < proc_args_n; i++) {
    l = strlen (buf + prev_l);
    prev_l += l + 1;
    proc_args[i] = malloc ((l + 1) * sizeof (char));
  }

  proc_args[proc_args_n] = NULL;
  proc_args[proc_args_n + 1] = NULL;
  proc_args[proc_args_n + 2] = NULL;
  proc_args[proc_args_n + 3] = NULL;
  proc_args[proc_args_n + 4] = NULL;
  int null_c = 0;
  int word_c = 0;

  /* fill proc_args table with program arguments */
  while ((c = fgetc (fp)) != EOF) {
    if (c == '\0') {
      null_c++;
      word_c = 0;
      if (null_c % 2)
	fputs (" \"", stdout);
      else
	fputs ("\" ", stdout);
    }
    else if (c == '\n') {
      if (null_c % 2)
	fputs ("\" ", stdout);
      break;
    }
    else {
      fputc (c, stdout);
      proc_args[null_c][word_c] = c;
      proc_args[null_c][word_c + 1] = 0;
      word_c++;

    }
    if (null_c > proc_args_n)
      break;
  }
  fscanf (fp, "%s\n", proc_blacklisted);	/* whether the particular process was blacklisted, currently broken */
  mygetline (&proc_vim, &proc_vim_s, fp);	/* vim save file base name */
  proc_vim = strtrim_right (proc_vim, '\n');
  fclose (fp);
  printf("\n");

  /* if there is a vim save file base name append "-S vim_session -i vim_info" to
   * proc_args */

  char *needle_vim = "vim_";
  char *needle_shellvars = "shellvars_";

  if (strcmp (proc_vim, "-1") != 0 && strcmp (proc_vim, "None") != 0 ) {
	  char *session = get_session (config);
	  if (strncmp(proc_vim, needle_vim, strlen(needle_vim)) == 0 ) {
	    proc_args[proc_args_n] = malloc ((strlen ("-S") + 1) * sizeof (char));
	    proc_args[proc_args_n + 2] = malloc ((strlen ("-i") + 1) * sizeof (char));
	    proc_args[proc_args_n + 1] =
	      malloc ((strlen (basedir) + strlen (session) + strlen (proc_vim) +
		       strlen (VIM_SESSION) + 5) * sizeof (char));
	    proc_args[proc_args_n + 3] =
	      malloc ((strlen (basedir) + strlen (session) + strlen (proc_vim) +
		       strlen (VIM_INFO) + 5) * sizeof (char));

	    strcpy (proc_args[proc_args_n], "-S");

	    strcpy (proc_args[proc_args_n + 1], basedir);
	    strcat (proc_args[proc_args_n + 1], "/");
	    strcat (proc_args[proc_args_n + 1], session);
	    strcat (proc_args[proc_args_n + 1], "/");
	    strcat (proc_args[proc_args_n + 1], proc_vim);
	    strcat (proc_args[proc_args_n + 1], VIM_SESSION);

	    strcpy (proc_args[proc_args_n + 2], "-i");

	    strcpy (proc_args[proc_args_n + 3], basedir);
	    strcat (proc_args[proc_args_n + 3], "/");
	    strcat (proc_args[proc_args_n + 3], session);
	    strcat (proc_args[proc_args_n + 3], "/");
	    strcat (proc_args[proc_args_n + 3], proc_vim);
	    strcat (proc_args[proc_args_n + 3], VIM_INFO);

	    char *buf =
	      malloc ((strlen (session) + strlen (proc_vim) + strlen (VIM_SESSION) +
		       5) * sizeof (char));
	    strcpy (buf, session);
	    strcat (buf, "/");
	    strcat (buf, proc_vim);
	    strcat (buf, VIM_SESSION);
	    requireSession (basedir, buf, 0);
	    SAFE_FREE (buf);
	  } else if (strncmp(proc_vim, needle_shellvars, strlen(needle_shellvars)) == 0 ) {
      printf (PRIMER "Load shell envvars with: source $SCSENV\n");
	  }
	SAFE_FREE (session);
  }

  if (strcmp (proc_blacklisted, "True") == 0)
    return 0;
  /* else if ( is_blacklisted(basedir,thisprogram) )
     return 0; */
  /* procs_n > 1 means there is more than a one process left to restart
   * so we assume it is a shell */
  if (procs_n > 1) {
    /* move saved arguments of the current shell to make place for
     *   "-c command" */
    for (i = proc_args_n - 1; i > 3; i--) {
      strcpy (proc_args[i], proc_args[i - 3]);
    }

    strcpy (proc_args[1], "-c");

    char *command =
      malloc (((procs_n) * 4 + 2 * ((2 * strlen (thisprogram)) +
				    strlen (basedir) + strlen (config) +
				    strlen (proc_exe) + 20)) * sizeof (char));

    /* primer - continue unwinding queued processes IDs */
    strcpy (command, thisprogram);
    strcat (command, " -s");
    strcat (command, " ");
    strcat (command, basedir);
    strcat (command, " ");
    strcat (command, thisprogram);
    strcat (command, " ");
    strcat (command, config);

    /* append queued processes IDs but skip the current shell ID */
    for (i = 1; i < procs_n; i++) {
      char buf[4];
      sprintf (buf, " %d", procs[i]);
      strcat (command, buf);
    }

    /* command separator */
    strcat (command, "; ");

    /* primer - will start the current shell after the termination of queued processes */
    strcat (command, thisprogram);
    strcat (command, " -s");
    strcat (command, " ");
    strcat (command, basedir);
    strcat (command, " ");
    strcat (command, thisprogram);
    strcat (command, " ");
    strcat (command, config);

    /* append the currently started shell ID */
    char buf[4];
    sprintf (buf, " %d", procs[0]);
    strcat (command, buf);

    proc_args[2] = command;
  }
  printf ("\n");
  recurse_chdir (proc_cwd);
  execvp (proc_exe, proc_args);
  return 1;
}

int
read_scrollback (char *fullpath, char *scrollbackfile)
{
  if (strcmp (scrollbackfile, "0") == 0)
    return 0;
  FILE *fp = NULL;
  char c;
  chdir (fullpath);
  requireSession (fullpath, scrollbackfile, 0);
  fp = fopen (scrollbackfile, "r");
  if (fp) {
    while ((c = fgetc (fp)) != EOF) {
      fputc (c, stdout);
    }
    fclose (fp);
  }
  else {
    fprintf (stderr, PRIMER ": %s:%d Cannot open scrollback file.\n",
	     __FILE__, __LINE__);
    return 1;
  }
  fp = NULL;
  return 0;

}

void
execute_filter (int bFilter, char *scs_exe, char *filter)
{
  /* execute filter */
  if (bFilter && (strncmp (filter, "-1", 2) != 0)) {
    printf ("Setting up filter...\n");
    char *command0 = malloc ((51 + strlen (scs_exe)) * sizeof (char));
    sprintf (command0, "screen -S \"$(%s name)\" -X stuff \"exec ", scs_exe);
    char command1[] = "\"^M";
    char *command =
      malloc ((strlen (command0) + strlen (filter) + strlen (command1) +
	       1) * sizeof (char));
    strcpy (command, command0);
    strcat (command, filter);
    strcat (command, command1);
    system ("screen -X colon");
    system (command);
    SAFE_FREE (command);
    SAFE_FREE (command0);
  }
}

void
reset_primer (char **argv, char *fullpath, char *scrollbackfile,
	      char *datafile)
{
  printf (PRIMER "Reseting...\n");
  if (strcmp (scrollbackfile, "0") == 0)
    requireSession (fullpath, datafile, 0);
  else
    requireSession (fullpath, scrollbackfile, 0);
  execv (argv[0], argv);
}

#ifndef TEST
int
main (int argc, char **argv)
{

/*
/full/path/to/program -p workingdir scrollbackfile datafile
./program -s basedir thisprogramname datafile [processes_ids..]
*/
  int i;
  /*
  for (i=0; i<argc; i++)
      printf("%s\n", argv[i]);
  printf("End Of argv\n");
  */
  FILE *fp = NULL;
  int c;
  if (argc == 1) {
    printf ("screen-session %s priming program\n", VERSION);
    return 0;
  }
  char *scs_path = malloc ((strlen (argv[0]) + 1) * sizeof (char));
  char *pch = NULL;
  strcpy (scs_path, argv[0]);
  pch = strrchr (scs_path, '/');
  *pch = '\0';
  scs_exe =
    malloc ((strlen (scs_path) + strlen ("/screen-session") +
	     1) * sizeof (char));
  strcpy (scs_exe, scs_path);
  SAFE_FREE (scs_path);
  strcat (scs_exe, "/screen-session");
  if (strcmp (argv[1], "-s") == 0) {
    /* 
       programs starter
       Example invocation:
       INSTDIR/screen-session-primer -s HOME/.screen-sessions INSTDIR/screen-session-primer 13983.pts-218.cvops/win_2 1 2 3
     */
    int *procs = malloc ((argc - 5) * sizeof (int));
    for (i = 5; i < argc; i++)
      procs[i - 5] = atoi (argv[i]);
    start (argv[2], argv[3], argv[4], i - 5, procs);
    return 0;
  }
  else if (strcmp (argv[1], "-D") == 0) {
    /*
       start a program in a directory
       primer -D directory program args
     */
    recurse_chdir (argv[2]);
    execvp (argv[3], &argv[3]);
    return 0;
  }
  else if (strcmp (argv[1], "-r") == 0) {
    /* requireSession */
    requireSession (argv[2], argv[3], 0);
    return 0;
  }
  else if (strcmp (argv[1], "-rf") == 0) {
    /* requireSession ?force? */
    requireSession (argv[2], argv[3], 0);
    return 0;
  }
  else if (strncmp (argv[1], "-p", 2) == 0) {
    /* 
       priming procedure invoked by session saver
       Example invocation:
       INSTALLPATH/screen-session-primer "-p" ".screen-sessions" "13983.pts-218.cvops/hardcopy.2" "13983.pts-218.cvops/win_2"
     */
    int force_start = (argv[1][2] == 'S') ? 1 : 0;
    char *homedir = getenv ("HOME");
    char *workingdir = argv[2];
    char *scrollbackfile = argv[3];
    char *datafile = argv[4];


    char *fullpath = gen_fullpath(homedir, workingdir);

    chdir (fullpath);		/* some fopen's currently depend on this */
    read_scrollback (fullpath, scrollbackfile);

    requireSession (fullpath, datafile, 0);
    fp = fopen (datafile, "r");
    if (!fp) {
      fprintf (stderr,
	       PRIMER ": %s:%d Cannot open data file (%s). Aborting.\n",
	       __FILE__, __LINE__, datafile);
      perror ("Error :");
      printf ("Press any key to continue...\n");
      mygetch ();
      return 1;
    }

    int procs_c = 0;
    size_t filter_s = 1;
    char *filter = malloc (filter_s * sizeof (char));
    size_t cmdargs_s = 1;
    char *cmdargs = malloc (cmdargs_s * sizeof (char));
    size_t buftext_s = 1;
    char *buftext = malloc (buftext_s * sizeof (char));
    size_t type_s = 1;
    char *type = malloc (type_s * sizeof (char));
    size_t title_s = 1;
    char *title = malloc (title_s * sizeof (char));
    size_t timesaved_s = 1;
    char *timesaved = malloc (timesaved_s * sizeof (char));
    mygetline (&buftext, &buftext_s, fp);	/* win number */
    mygetline (&buftext, &buftext_s, fp);	/* CURRENTLY UNUSED (put window flags here) */
    mygetline (&buftext, &buftext_s, fp);	/* group */
    mygetline (&type, &type_s, fp);	/* win type */
    mygetline (&title, &title_s, fp);	/* title */
    mygetline (&filter, &filter_s, fp);	/* filter */
    mygetline (&buftext, &buftext_s, fp);	/* scrollback len */
    mygetline (&cmdargs, &cmdargs_s, fp);	/* This pool is not used by primer. Screen dumps on this position zombie command vector. session asver processes this vector and saves it as a first process (id=0) which is later used by [Z]ombie.
					 */
    fscanf (fp, "%d\n", &procs_c);
    int bFilter = 0;
    if (!force_start) {
      printf ("%sTITLE:%s %s\n", green_r, none, title);
      if (type[0] != 'z') {
	filter = strtrim_right (filter, '\n');
	if (strcmp (filter, "-1") != 0) {
	  bFilter = 1;
	  printf ("%sFILTER:%s %s\n", green_r, none, filter);
	}
	printf ("%s", none);

	printf ("%s %d %s in %s %s %s\n", red_r, procs_c - 1, blue_r,
		red_r, datafile, none);
      }
    }

    size_t proc_cwd_s = 1;
    size_t proc_exe_s = 1;
    size_t proc_vim_s = 1;
    char *proc_cwd = malloc (proc_cwd_s * sizeof (char));
    char *proc_exe = malloc (proc_exe_s * sizeof (char));
    char *proc_vim = malloc (proc_vim_s * sizeof (char));
    int proc_args_n;
    char cmdline_begin[CMDLINE_BEGIN + 1];
    int cmdline_begin_c = 0;
    char proc_blacklisted[7];
    char buf[5];
    int b_zombie = 1;
    /* 
    if (type[0] == 'z')
      b_zombie = 1;
    else
      b_zombie = 0;
    */  
    for (i = 0; i < procs_c; i++) {
      fscanf (fp, "%s\n", buf);	/* read -- separator */
      if (!force_start && i != 0)
	printf ("%s%s %d%s: ", blue_b, buf, i, none);
      /* cwd exe args */
      mygetline (&proc_cwd, &proc_cwd_s, fp);
      proc_cwd = strtrim_right (proc_cwd, '\n');
      mygetline (&proc_exe, &proc_exe_s, fp);
      proc_exe = strtrim_right (proc_exe, '\n');
      fscanf (fp, "%d\n", &proc_args_n);
      int null_c = 0;
      cmdline_begin_c = 0;
      if (!force_start && b_zombie)
	printf ("%sZOMBIE:%s ", red, none);
      while ((c = fgetc (fp)) != EOF) {
	if (cmdline_begin_c < CMDLINE_BEGIN) {
	  cmdline_begin[cmdline_begin_c] = c;
	  cmdline_begin[cmdline_begin_c + 1] = '\0';
	  cmdline_begin_c++;
	}
	if (i != 0 || b_zombie) {
	  if (!force_start) {
	    if (c == '\0') {
	      null_c++;
	      if (null_c == 1)
		fputs (" \"", stdout);
	      else
		fputs ("\" \"", stdout);
	    }
	    else if (c == '\n') {
	      fputs ("\" ", stdout);
	      break;
	    }
	    else
	      fputc (c, stdout);
	  }
	}
	else {
	  if (c == '\n') {
	    break;
	  }
	}
	if (null_c > proc_args_n)
	  break;
      }
      if (!force_start && b_zombie) {
	printf ("\n");
	b_zombie = 0;
      }
      fscanf (fp, "%s\n", proc_blacklisted);
      mygetline (&proc_vim, &proc_vim_s, fp);
      proc_vim = strtrim_right (proc_vim, '\n');
      if (!force_start && i != 0) {
	printf ("\n");
	printf ("\tCWD: %s\n", proc_cwd);
	printf ("\tEXE: %s\n", proc_exe);
	if (strcmp ("-1", proc_vim) != 0 && strcmp ("None", proc_vim) != 0) {
	  char *needle_vim = "vim_";
	  char *needle_shellvars = "shellvars_";
		if(strncmp(proc_vim, needle_vim, strlen(needle_vim)) == 0) {
		  printf ("\tVIMSESSION: %s\n", proc_vim);
		} else if (strncmp(proc_vim, needle_shellvars, strlen(needle_shellvars)) == 0) {
      char *session = get_session (datafile);
      char *shellvars_path =
      malloc ((strlen (fullpath) + strlen(session) + strlen (proc_vim) + 3) * sizeof (char));
      strcpy (shellvars_path, fullpath);
      strcat (shellvars_path, "/");
      strcat (shellvars_path, session);
      strcat (shellvars_path, "/");
      strcat (shellvars_path, proc_vim);
      setenv("SCSENV", shellvars_path, 1);

      printf ("\tLoad shell envvars with: $ source $SCSENV\n");
      SAFE_FREE (session);
      SAFE_FREE (shellvars_path);
		}
	}
	if (strncmp (proc_blacklisted, "True", 4) == 0
	    || is_blacklisted (fullpath, cmdline_begin, i))
	  printf
	    ("\t%sBLACKLISTED - program and child processes\n\tcannot be started (use [O]nly)%s\n",
	     magenta, none);
      }
    }
    mygetline (&buftext, &buftext_s, fp);	/*last line - output from :time */
    if (!force_start && type[0] != 'z')
      printf ("%sSAVED:%s %s\n", green_r, none, buftext);
    fclose (fp);
    SAFE_FREE (proc_vim);
    SAFE_FREE (title);
    SAFE_FREE (timesaved);
    SAFE_FREE (buftext);
    int menu;
    int number;
    int *numbers = NULL;
    int numbers_c;
    int bScrollback = 1;
    recurse_chdir (proc_cwd);
    if (force_start)
      menu = ALL;
    else
      numbers_c = userInput (&menu, &numbers, procs_c - 1, &bFilter, &bScrollback);
    char *shell = NULL;
    char **arglist = NULL;
    int *args = NULL;


    switch (menu) {

    case EXIT:
      printf (PRIMER "Exiting...\n");
      return 0;
      break;
    case RESET:
      reset_primer (argv, fullpath, scrollbackfile, datafile);
      break;
    case DEFAULT:
      if (bScrollback)
        read_scrollback (fullpath, scrollbackfile);
      shell = getenv ("SHELL");
      arglist = malloc (2 * sizeof (char *));
      arglist[0] = malloc ((strlen (shell) + 1) * sizeof (char));
      arglist[1] = NULL;
      strcpy (arglist[0], shell);
      printf (PRIMER "Starting $SHELL(%s) in last cwd(%s)...\n", shell,
	      proc_cwd);
      recurse_chdir (proc_cwd);
      execute_filter (bFilter, scs_exe, filter);
      execvp (shell, arglist);
      break;
    case ZOMBIE:
      printf (PRIMER "ZOMBIE\n");
      /* FALLTHROUGH */
    case ONLY:
      if (bScrollback)
        read_scrollback (fullpath, scrollbackfile);
      printf (PRIMER "Starting processes ");
      print_ints (numbers, numbers_c);
      printf ("...\n");
      arglist =
	make_arglist (argv[0], "-s", fullpath, datafile, numbers_c, numbers);
      execute_filter (bFilter, scs_exe, filter);
      execv (argv[0], arglist);
      break;

    case ALL:
      args = malloc (procs_c * sizeof (int));
      if (!force_start && bScrollback)
	read_scrollback (fullpath, scrollbackfile);
      printf (PRIMER "Starting all programs... ");
      for (i = 1; i <= procs_c - 1; i++) {
	args[i - 1] = i;
      }
      print_ints (args, procs_c - 1);
      printf ("\n");
      arglist =
	make_arglist (argv[0], "-s", fullpath, datafile, procs_c - 1, args);
      SAFE_FREE (args);
      execute_filter (bFilter, scs_exe, filter);
      execv (argv[0], arglist);

      break;

    case NUMBER:
      args = malloc (procs_c * sizeof (int));
      if (bScrollback)
        read_scrollback (fullpath, scrollbackfile);
      number = numbers[0];
      printf (PRIMER "Starting programs up to %d ( ", number);
      if (number > procs_c) {
	number = procs_c;
	printf (PRIMER "No such window. Starting programs up to %d ( ",
		number - 1);
      }
      for (i = 1; i <= number; i++) {
	args[i - 1] = i;
      }
      print_ints (args, number);
      printf (")\n");
      arglist =
	make_arglist (argv[0], "-s", fullpath, datafile, number, args);
      SAFE_FREE (args);
      execute_filter (bFilter, scs_exe, filter);
      execv (argv[0], arglist);
      break;
    case EDIT:
      requireSession (fullpath, datafile, 0);
      char *EDITOR = getenv ("EDITOR");
      char *session = get_session (datafile);
      char *buf1 =
	malloc ((strlen (fullpath) + strlen (datafile) + 2) * sizeof (char));
      sprintf (buf1, "%s/%s", fullpath, datafile);
      char *buf2 =
	malloc ((strlen (getenv("USER")) + strlen (session) + 40 + 6) 
                * sizeof (char));
      sprintf (buf2, "/tmp/screen-session-%s/primer_edit_%s_%d",
	       getenv ("USER"), session, getpid ());
      char *buf0 =
	malloc ((strlen (EDITOR) + strlen (buf2) + 8) * sizeof (char));
      sprintf (buf0, "%s \"%s\"", EDITOR, buf2);
      printf (PRIMER "Editing source: %s\n", buf1);
      copy_file (buf1, buf2);
      system (buf0);
      requireSession (fullpath, datafile, 1);
      copy_file (buf2, buf1);
      remove (buf2);
      SAFE_FREE (buf0);
      SAFE_FREE (buf1);
      SAFE_FREE (buf2);

      char *buf_pack =
        malloc ((1 + 31 + strlen (scs_exe) + strlen (workingdir) +
                 strlen (session)) * sizeof (char));
      sprintf (buf_pack, "%s other --dir \"%s\" --pack \"%s\"", scs_exe,
               workingdir, session);
      system (buf_pack);
      SAFE_FREE (buf_pack);
      reset_primer (argv, fullpath, scrollbackfile, datafile);

      /*
      int pid = fork ();
      if (pid == 0) {
	char *buf_pack =
	  malloc ((1 + 31 + strlen (scs_exe) + strlen (workingdir) +
		   strlen (session)) * sizeof (char));
        printf(buf_pack);
	sprintf (buf_pack, "%s other --dir \"%s\" --pack \"%s\"", scs_exe,
		 workingdir, session);
	system (buf_pack);
	SAFE_FREE (buf_pack);
	exit (0);
      }
      else if (pid < 0)
	fprintf (stderr, PRIMER ": %s:%d failed to fork a process\n",
		 __FILE__, __LINE__);
      else
	reset_primer (argv, fullpath, scrollbackfile, datafile);
      break;
      */

    }
    fprintf (stderr, PRIMER ": %s:%d fatal error - unsupported action %d\n",
	     __FILE__, __LINE__, menu);
    mygetch ();
    return 44;
  }
  else {
    printf ("screen-session %s priming program: No such mode \"%s\"\n",
	    VERSION, argv[1]);
  }
}

#endif
