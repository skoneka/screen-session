/*
 * =====================================================================================
 *
 *       Filename:  screen-session-primer.c
 *
 *    Description:  primes windows during screen session loading
 *
 *        Version:  1.0
 *        Created:  02.08.2010 18:21:25
 *       Revision:  none
 *       Compiler:  gcc
 *
 *         Author:  Artur Skonecki (), 
 *        Company:  adb.cba.pl
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

#define USERINPUTMAXBUFFERSIZE   80
#define CMDLINE_BEGIN 20
#define BLACKLISTMAX 100
#define BASEDATA_LINES 7
#define PROCLINES 7
#define QUOTEME(x) #x
#define Q(x) QUOTEME(x)
#define X $
#define O \20

/* defining _POSIX_SOURCE causes compilation errors on solaris  */
int kill (int pid, int sig);

int blacklist[BLACKLISTMAX];
int blacklist_c = 0;

#define FONTHEIGHT 9
#define FONTWIDTH 6
char *fonts[] = {
  /*  */
  " $$$$ ",
  "$$  $$",
  "$$  $$",
  "$$  $$",
  "$$  $$",
  "$$  $$",
  "$$  $$",
  "$$  $$",
  " $$$$ ",
  /*  */
  "  $$$$",
  " $$$$$",
  "$$$$$$",
  "   $$$",
  "   $$$",
  "   $$$",
  "   $$$",
  "   $$$",
  "   $$$",
  /*  */
  " $$$$ ",
  "$$  $$",
  "    $$",
  "   $$ ",
  "  $$  ",
  " $$   ",
  "$$    ",
  "$$    ",
  "$$$$$$",
  /*  */
  "$$$$$ ",
  "    $$",
  "   $$ ",
  "  $$  ",
  "   $$ ",
  "    $$",
  "    $$",
  "$$ $$ ",
  " $$$  ",
  /*  */
  "$$  $$",
  "$$  $$",
  "$$  $$",
  "$$  $$",
  "$$$$$$",
  "    $$",
  "    $$",
  "    $$",
  "    $$",
  /*  */
  "$$$$$$",
  "$$    ",
  "$$    ",
  "$$    ",
  "$$$$$$",
  "    $$",
  "    $$",
  "    $$",
  "$$$$$$",
  /*  */
  "$$$$$$",
  "$$    ",
  "$$    ",
  "$$    ",
  "$$$$$$",
  "$$  $$",
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
  "    $$",
  "    $$",
  /*  */
  "$$$$$$",
  "$$  $$",
  "$$  $$",
  "$$  $$",
  "$$$$$$",
  "$$  $$",
  "$$  $$",
  "$$  $$",
  "$$$$$$",
  /*  */
  "$$$$$$",
  "$$  $$",
  "$$  $$",
  "$$  $$",
  "$$$$$$",
  "    $$",
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
  "      ",
  "      ",
  /*  */
  "      ",
  "$    $",
  "$$  $$",
  " $$$$ ",
  "  $$  ",
  "  $$  ",
  " $$$$ ",
  "$$  $$",
  "$    $",
};

enum menu
{
  NONE = 0,
  RESET,
  EXIT,
  ALL,
  ONLY,
  NUMBER,
  DEFAULT
};

void print_ints(int *numbers,int n) 
{
  int i;
  for(i=0;i<n;i++)
    {
      printf("%d ",numbers[i]);
    }
}
int
line_to_string (FILE * fp, char **line, size_t * size)
{
  int rc;
  void *p;
  size_t count;

  count = 0;
  while ((rc = getc (fp)) != EOF)
    {
      ++count;
      if (count + 2 > *size)
	{
	  p = realloc (*line, count + 2);
	  if (p == NULL)
	    {
	      if (*size > count)
		{
		  (*line)[count] = '\0';
		  (*line)[count - 1] = (char) rc;
		}
	      else
		{
		  ungetc (rc, fp);
		}
	      count = 0;
	      break;
	    }
	  *line = p;
	  *size = count + 2;
	}
      if (rc == '\n')
	{
	  (*line)[count - 1] = '\0';
	  break;
	}
      (*line)[count - 1] = (char) rc;
    }
  if (rc != EOF)
    {
      rc = count > INT_MAX ? INT_MAX : count;
    }
  else
    {
      if (*size > count)
	{
	  (*line)[count] = '\0';
	}
    }
  return rc;

}

int
getline (char **lineptr, size_t * n, FILE * stream)
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
  while (*p && len)
    {
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

  if (pDir != NULL)
    {
      bExists = 1;
      (void) closedir (pDir);
    }

  return bExists;
}

int
file_exists (const char *filename)
{
  FILE *file = NULL;
  if ((file = fopen (filename, "r")))
    {
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
  free (file);
  return session;
}

int
requireSession (const char *basepath, const char *file_in_session, int full)
{
  char *file = malloc ((strlen (file_in_session) + 1) * sizeof (char));
  char *session = malloc ((strlen (file_in_session) + 1) * sizeof (char));
  char *basedir = malloc ((strlen (basepath) + 1) * sizeof (char));

  strcpy (basedir, basepath);
  strcpy (file, file_in_session);


  char *pch = NULL;
  pch = strtok (file, "/");
  if (pch)
    strcpy (session, pch);
  else
    {
      free (file);
      free (session);
      free (basedir);
      return 1;
    }

  char *filepath =
    malloc ((strlen (basedir) + strlen (session) + 2) * sizeof (char));
  char *testfilepath =
    malloc ((strlen (basedir) + strlen (session) + strlen (file_in_session) +
	     2) * sizeof (char));
  strcpy (filepath, basedir);
  strcat (filepath, "/");
  strcat (filepath, session);

  strcpy (testfilepath, basedir);
  strcat (testfilepath, "/");
  strcat (testfilepath, file_in_session);
  if (file_exists (testfilepath))
    {
      free (file);
      free (filepath);
      free (testfilepath);
      free (session);
      free (basedir);
      return 0;
    }
  else
    {
      free (filepath);
      char *fullstr = "--full";
      char *buf =
	malloc ((strlen (basedir) + strlen (session) + strlen (fullstr) + 1 +
		 55) * sizeof (char));
      if (full)
	sprintf (buf, "screen-session other -n --dir %s --unpack %s %s",
		 basedir, session, fullstr);
      else
	sprintf (buf, "screen-session other -n --dir %s --unpack %s", basedir,
		 session);
      system (buf);
      free (file);
      free (buf);
      free (session);
      free (basedir);
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
  char *p;
  number = strtol (buffer, &p, 0);
  if (strcmp ("", p) != 0)
    {
      return -1;
    }
  else if (errno == ERANGE)
    {
      return -1;
    }
  else if (errno == EINVAL)
    {
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

int
userInput (int *menu_num, int **num, int max)
{
  char ch;			/* handles user input */
  char buffer[USERINPUTMAXBUFFERSIZE];	/* sufficient to handle one line */
  int char_count;		/* number of characters read for this line */
  int exit_flag = 0, valid_choice, number = 0;
  enum menu menu_choice = NONE;
  int *args=malloc(USERINPUTMAXBUFFERSIZE*sizeof(int));
  int args_index=0;
  
  while (exit_flag == 0 && menu_choice == NONE)
    {
      valid_choice = 0;
      while (valid_choice == 0)
	{
	  printf
	    ("%sRESTORE:%s [%sA%s]ll / [%sE%s]xit / [%sD%s]efault / [%sR%s]eset / [%snumber%s] / [%sO%s]nly [%snumber%s] ?\n",
	     green, none, red_b, none, red_b, none,red_b, none, red_b, none, blue, none,red_b, none, blue, none);
	  printf ("> ");
	  ch = getchar ();
	  char_count = 0;
          char menu=ch;
          if(menu >= '0' && menu <= '9')
            {
              ungetc(menu,stdin);
              menu='N';
            }
          args_index=0;
          args[args_index]=-1;
          int got_number=0;
	  while ((char_count < USERINPUTMAXBUFFERSIZE))
	    {
	      ch = getchar ();
              //printf("menu='%c' index='%d'  ch='%c'\n",menu, args_index,ch);
	      if (ch != ' ' && ch !='\n' ) {
		buffer[char_count++] = ch;
		buffer[char_count] = '\0';
                got_number=1;
              }
              else if (got_number){
                  args[args_index]=parseNumber(buffer);
                  args_index = (args[args_index]>(-1))?(args_index+1):(args_index);
                  char_count=0;
                  got_number=0;
              }
              if (ch == '\n')
                break;
	    }
          args_index--;
	  buffer[char_count] = 0x00;	/* null terminate buffer */
	  switch (menu)
	    {
	    case 'r':
	    case 'R':
	      number = -1;
	      valid_choice = 1;
	      menu_choice = RESET;
	      break;
	    case 'd':
	    case 'D':
	      number = -1;
	      valid_choice = 1;
	      menu_choice = DEFAULT;
	      break;
	    case 'a':
	    case 'A':
	      number = -1;
	      menu_choice = ALL;
	      valid_choice = 1;
	      break;
	    case 'o':
	    case 'O':
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
            case 'q':
            case 'Q':
	      menu_choice = EXIT;
	      valid_choice = 1;
	      break;
	    case 'n':
	    case 'N':
	      menu_choice = NUMBER;
	      number = args[0];
	      if (number == -1)
		valid_choice = 0;
	      else if (number > max)
		valid_choice = 0;
	      else
		valid_choice = 1;
	      break;
	    default:
	      menu_choice = NONE;
	      valid_choice = 0;
	    }


	}
    }
  *num = args;
  *menu_num = menu_choice;
   return args_index+1;
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
  //has to pass program name because nested programs do not get name in argv[0]
  args[3] = malloc ((strlen (program) + 1) * sizeof (char));
  args[4] = malloc ((strlen (arg3) + 1) * sizeof (char));
  for (i = 5; i < procs_n + 5; i++)
    {
      int i_procs = i - 5;
      int blacklisted = 0;
      int j;
      for (j = 0; j < blacklist_c; j++)
	{
	  if (blacklist[j] == procs[i_procs])
	    {
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

  while ((c = fgetc (fp)) != EOF)
    {
      if (c == '\n')
	{
	  if (strncmp (s, line, line_c) == 0)
	    return 1;
	  nl_c++;
	  line_c = 0;
	}
      else
	{
	  line[line_c] = c;
	  line_c++;
	  line[line_c] = 0;

	}
    }
  if (line_c != 0)
    {
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

  if (!fp)
    {
      fprintf (stderr,"%s:%d Cannot open blacklist '%s'.\n",__FILE__,__LINE__, filepath);
      perror("Error :");
      free (filepath);
      return 0;
    }
  else
    free (filepath);
  //int ret=FileSearch(fp,program);
  //return (ret==-1)? 0 : 1;
  int ret = filesearch_line (fp, program);
  if (ret)
    {
      blacklist[blacklist_c] = programid;
      blacklist_c++;
    }
  fclose (fp);
  return ret;

}

int
start (char *basedir, char *thisprogram, char *config, int procs_n,
       int *procs)
{
  if (procs_n == 0)
    return 0;
  size_t proc_cwd_s = 0;
  size_t proc_exe_s = 0;
  size_t proc_vim_s = 0;
  char *proc_cwd = NULL;
  char *proc_exe = NULL;
  char *proc_vim = NULL;
  int proc_args_n;
  char proc_blacklisted[7];
  char **proc_args;
  int i, nl_c = 0;
  char c;
  FILE *fp = NULL;
  chdir (basedir);
  requireSession (basedir, config, 0);

  fp = fopen (config, "r");

  if (!fp)
    {

      fprintf (stderr,"%s:%d Cannot open data file. Aborting.\n",__FILE__,__LINE__);
      perror("Error :");
      printf ("Press any key to continue...\n");
      mygetch ();
      return 1;
    }

  // skip not important lines
  while ((c = fgetc (fp)) != EOF)
    {
      if (c == '\n')
	{
	  nl_c++;
	}
      else if (nl_c > (BASEDATA_LINES + (procs[0] * PROCLINES)))
	break;
    }
  c = fgetc (fp);
  getline (&proc_cwd, &proc_cwd_s, fp);
  proc_cwd = strtrim_right (proc_cwd, '\n');
  printf ("PRIMER: CWD(%s) starting: ",proc_cwd);
  //fscanf(fp,"%s\n",proc_cwd); //cwd exe args
  getline (&proc_exe, &proc_exe_s, fp);
  proc_exe = strtrim_right (proc_exe, '\n');
  fscanf (fp, "%d\n", &proc_args_n);
  if (procs_n > 1)
    {
      proc_args_n += 2;
    }
  proc_args = malloc ((proc_args_n + 5) * sizeof (char *));

  long file_pos = ftell (fp);
  char *buf = NULL;
  size_t buf_size = 0;
  getline (&buf, &buf_size, fp);
  fseek (fp, file_pos, SEEK_SET);
  int l = 0, prev_l = 0;

  /* get length of program arguments */
  for (i = 0; i < proc_args_n; i++)
    {
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
  while ((c = fgetc (fp)) != EOF)
    {
      if (c == '\0')
	{
	  null_c++;
	  word_c = 0;
	  if (null_c % 2)
	    fputs (" \"", stdout);
	  else
	    fputs ("\" ", stdout);
	}
      else if (c == '\n')
	{
	  if (null_c % 2)
	    fputs ("\" ", stdout);
	  break;
	}
      else
	{
	  fputc (c, stdout);
	  proc_args[null_c][word_c] = c;
	  proc_args[null_c][word_c + 1] = 0;
	  word_c++;

	}
      if (null_c > proc_args_n)
	break;
    }
  fscanf (fp, "%s\n", proc_blacklisted);
  getline (&proc_vim, &proc_vim_s, fp);
  proc_vim = strtrim_right (proc_vim, '\n');
  fclose (fp);
  if (strcmp (proc_vim, "None") != 0)
    {
      proc_args[proc_args_n] = malloc ((strlen ("-S") + 1) * sizeof (char));
      proc_args[proc_args_n+2] = malloc ((strlen ("-i") + 1) * sizeof (char));
      char *session = get_session (config);
      proc_args[proc_args_n + 1] =
	malloc ((strlen (basedir) + strlen (session) + strlen (proc_vim) +
		 strlen (VIM_SESSION)+5) * sizeof (char));
      proc_args[proc_args_n + 3] =
	malloc ((strlen (basedir) + strlen (session) + strlen (proc_vim) +
		 strlen (VIM_INFO)+5) * sizeof (char));
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
	malloc ((strlen (session) + strlen (proc_vim) + strlen (VIM_SESSION) + 5) * sizeof (char));
      strcpy (buf, session);
      strcat (buf, "/");
      strcat (buf, proc_vim);
      strcat (buf, VIM_SESSION);
      requireSession (basedir, buf, 1);
      free (buf);
    }

  if (strcmp (proc_blacklisted, "True") == 0)
    return 0;
  //else if ( is_blacklisted(basedir,thisprogram) )
  //    return 0;

  if (procs_n > 1)
    {
      for (i = proc_args_n - 1; i > 3; i--)
	{
	  strcpy (proc_args[i], proc_args[i - 3]);
	}
      strcpy (proc_args[1], "-c");

      char *command =
	malloc (((procs_n - 1) * 4 + (2 * strlen (thisprogram)) +
		 strlen (basedir) + strlen (config) + strlen (proc_exe) +
		 10) * sizeof (char));
      strcpy (command, thisprogram);
      strcat (command, " -s");
      strcat (command, " ");
      strcat (command, basedir);
      strcat (command, " ");
      strcat (command, thisprogram);
      strcat (command, " ");
      strcat (command, config);
      for (i = 1; i < procs_n; i++)
	{
	  char buf[4];
	  sprintf (buf, " %d", procs[i]);
	  strcat (command, buf);
	}
      strcat (command, "; ");
      strcat (command, proc_exe);
      proc_args[2] = command;
      //strcpy(proc_args[2],command);
    }
  printf ("\n");
  chdir (proc_cwd);
  //printf("exe:%s\n",proc_exe);
  //for(i=0;i<proc_arg_n;
  execvp (proc_exe, proc_args);
  return 1;

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
      print_number ("x 0 x", red);
      printf ("timeout: 10 sec ; number = 1\n\
\n\
goto:\t [number]'\n\
goto:\t [number]g\n\
swap:\t [number]s \n\
rotate left:\t [number]l\n\
rotate right:\t [number]r\n\
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
  printf ("prefix: %d ; ", prefix);
  printf ("mode: %c\n", mode);
  FILE *f = fopen (fname, "w");
  fprintf (f, "%c%d", mode, prefix);
  fclose (f);
  kill (pid, SIGUSR1);

}
FILE *
read_scrollback(char *fullpath, char *scrollbackfile)
{
  FILE *fp=NULL;
  char c;
  requireSession (fullpath, scrollbackfile, 1);
  fp = fopen (scrollbackfile, "r");
  if (fp)
    {
      while ((c = fgetc (fp)) != EOF)
        {
          fputc (c, stdout);
        }
      fclose (fp);
    }
  else
    {
      fprintf (stderr,"%s:%d Cannot open scrollback file.\n",__FILE__,__LINE__);
      perror("Error :");
    }
  fp = NULL;
  return fp;

}
#ifndef TEST
int
main (int argc, char **argv)
{
// /full/path/to/program workingdir scrollbackfile datafile
//./program -s basedir thisprogramname datafile [processes..]
  int i;
  FILE *fp = NULL;
  int c;
  if (argc == 1)
    {
      printf ("screen-session %s helper program\n",VERSION);
      return 0;
    }
  if (strcmp (argv[1], "-s") == 0)
    {
      int *procs;
      procs = malloc ((argc - 5) * sizeof (int));
      for (i = 5; i < argc; i++)
	procs[i - 5] = atoi (argv[i]);
      start (argv[2], argv[3], argv[4], i - 5, procs);
      return 0;
    }
  else if (strcmp (argv[1], "-D") == 0)
    {
      //start a program in a directory
      //primer -D directory program args
      chdir(argv[2]);
      execvp(argv[3],&argv[3]);
      return 0;
    }
  else if (strcmp (argv[1], "-m") == 0)
    {
      //marker mode for ScreenSession.__get_focus_offset()
      //sleep(4);
      mygetch ();
      return 0;
    }
  else if (strcmp (argv[1], "-r") == 0)
    {
      //requireSession
      requireSession (argv[2], argv[3], 0);
      return 0;
    }
  else if (strcmp (argv[1], "-rf") == 0)
    {
      //requireSession
      requireSession (argv[2], argv[3], 1);
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
  else if (strcmp (argv[1], "-p") == 0) {
    //session saver primer
    char *homedir = getenv ("HOME");
    char *workingdir = argv[2];
    char *scrollbackfile = argv[3];
    char *datafile = argv[4];

    char *fullpath =
      malloc ((strlen (homedir) + strlen (workingdir) + 2) * sizeof (char));
    strcpy (fullpath, homedir);
    strcat (fullpath, "/");
    strcat (fullpath, workingdir);
    chdir (fullpath);
    fp=read_scrollback(fullpath,scrollbackfile);

    //printf("%sOpen: '%s' in: '$HOME/%s'%s\n",green_r,datafile,workingdir,none);
    printf ("%s%s'%s'%s ", none, green_r, datafile, none);
    requireSession (fullpath, datafile, 0);
    fp = fopen (datafile, "r");
    if (!fp)
      {
        fprintf (stderr,"%s:%d Cannot open data file. Aborting.\n",__FILE__,__LINE__);
        perror("Error :");
        printf ("Press any key to continue...\n");
        mygetch ();
        return 1;
      }

    int procs_c = 0;
    size_t filter_s = 20;
    char *filter = malloc (filter_s * sizeof (char));
    printf ("%sSAVED: ", none);
    size_t buftext_s;
    char *buftext = NULL;
    size_t title_s;
    char *title = NULL;
    getline (&buftext, &buftext_s, fp);	//win number
    getline (&buftext, &buftext_s, fp);	//save time
    printf ("%s%s\n", green_r, buftext);
    getline (&buftext, &buftext_s, fp);	//group
    getline (&buftext, &buftext_s, fp);	//win type
    getline (&title, &title_s, fp);	    //title

    getline (&filter, &filter_s, fp);	    //filter
    getline (&buftext, &buftext_s, fp);	//scrollback len

    filter = strtrim_right (filter, '\n');
    if (strcmp (filter, "-1") != 0)
      printf ("\nFilter: %s\n", filter);
    printf ("%s", none);

    fscanf (fp, "%d\n", &procs_c);
    printf ("%s%d%s in %s%s%s\n", red_r, procs_c, blue_r, red_r, title, none);

    size_t proc_cwd_s = 0;
    size_t proc_exe_s = 0;
    size_t proc_vim_s = 0;
    char *proc_cwd = NULL;
    char *proc_exe = NULL;
    char *proc_vim = NULL;
    int proc_args_n;
    char cmdline_begin[CMDLINE_BEGIN + 1];
    int cmdline_begin_c = 0;
    char proc_blacklisted[7];
    char buf[5];
    for (i = 0; i < procs_c; i++)
      {
        fscanf (fp, "%s\n", buf);	//read --
        printf ("%s%s %d%s: ", blue_b, buf, i, none);
        //cwd exe args
        getline (&proc_cwd, &proc_cwd_s, fp);
        proc_cwd = strtrim_right (proc_cwd, '\n');
        getline (&proc_exe, &proc_exe_s, fp);
        proc_exe = strtrim_right (proc_exe, '\n');
        fscanf (fp, "%d\n", &proc_args_n);
        int null_c = 0;
        cmdline_begin_c = 0;
        while ((c = fgetc (fp)) != EOF)
          {
            if (cmdline_begin_c < CMDLINE_BEGIN)
              {
                cmdline_begin[cmdline_begin_c] = c;
                cmdline_begin[cmdline_begin_c + 1] = '\0';
                cmdline_begin_c++;
              }
            if (c == '\0')
              {
                null_c++;
                if (null_c == 1)
                  fputs (" \"", stdout);
                else
                  fputs ("\" \"", stdout);
              }
            else if (c == '\n')
              {
                fputs ("\" ", stdout);
                break;
              }
            else
              fputc (c, stdout);
            if (null_c > proc_args_n)
              break;
          }

        fscanf (fp, "%s\n", proc_blacklisted);
        getline (&proc_vim, &proc_vim_s, fp);
        proc_vim = strtrim_right (proc_vim, '\n');
        printf ("\n");
        printf ("\tCWD: %s\n", proc_cwd);
        printf ("\tEXE: %s\n", proc_exe);
        if (strcmp ("None", proc_vim) != 0)
          printf ("\tVIMSESSION: %s\n", proc_vim);
        if (strncmp (proc_blacklisted, "True", 4) == 0
            || is_blacklisted (fullpath, cmdline_begin, i))
          printf ("\t%sBLACKLISTED - program and child processes\n\
                      \tcannot be started (use [O]nly)%s\n", magenta, none);
      }
    fclose (fp);
    free(proc_vim);
    free(proc_cwd);
    free(proc_exe);
    free(title);
    free(buftext);
    int menu;
    int number;
    int *numbers;
    int numbers_c=userInput (&menu, &numbers, procs_c);
    char *shell = NULL;
    char **arglist = NULL;
    int *args;

    // execute filter
    if (strncmp (filter, "-1", 2) != 0)
      {
        printf ("Setting up filter...\n");
        char command0[] = "screen -X stuff \"exec ";
        char command1[] = "\"^M";
        char *command =
          malloc ((strlen (command0) + strlen (filter) + strlen (command1) +
                   1) * sizeof (char));
        strcpy (command, command0);
        strcat (command, filter);
        strcat (command, command1);
        system ("screen -X colon");
        system (command);
        free(command);
      }
    free(filter);

    args = malloc (procs_c * sizeof (int));
    switch (menu)
      {

      case EXIT:
        printf ("PRIMER: Exiting...\n");
        return 0;
        break;
      case RESET:
        printf("PRIMER: Reseting...\n");
        requireSession (fullpath, scrollbackfile, 1);
        execv (argv[0],argv);
        break;
      case DEFAULT:
        read_scrollback(fullpath,scrollbackfile);
        shell = getenv ("SHELL");
        arglist = malloc (2 * sizeof (char *));
        arglist[0] = malloc ((strlen (shell) + 1) * sizeof (char));
        arglist[1] = NULL;
        strcpy (arglist[0], shell);
        printf ("PRIMER: Starting default shell(%s) in last cwd(%s)...\n", shell,
                proc_cwd);
        chdir (proc_cwd);
        execvp (shell, arglist);
        break;

      case ONLY:
        read_scrollback(fullpath,scrollbackfile);
        printf ("PRIMER: Starting processes ");
        print_ints(numbers,numbers_c);
        printf("...\n");
        args[0] = numbers[0];
        //sort ints?
        arglist = make_arglist (argv[0], "-s", fullpath, datafile,numbers_c, numbers);
        //arglist = make_arglist (argv[0], "-s", fullpath, datafile,1, args);

        /* i=0;
        while(arglist[i]!=NULL)
          printf("%s\n",arglist[i++]); */
        execv (argv[0], arglist);
        break;

      case ALL:
        read_scrollback(fullpath,scrollbackfile);
        printf ("PRIMER: Starting all programs...\n");
        for (i = 0; i < procs_c; i++)
          {
            args[i] = i;
          }
        arglist =
          make_arglist (argv[0], "-s", fullpath, datafile, procs_c, args);
        execv (argv[0], arglist);

        break;

      case NUMBER:
        read_scrollback(fullpath,scrollbackfile);
        number=numbers[0];
        printf ("PRIMER: Starting programs up to %d...\n", number);
        if (number > procs_c)
          {
            number = procs_c;
            printf ("PRIMER: No such window. Starting programs up to %d...\n",
                    number - 1);
          }
        else
          number++;
        for (i = 0; i < number; i++)
          {
            args[i] = i;
          }
        arglist =
          make_arglist (argv[0], "-s", fullpath, datafile, number, args);
        execv (argv[0], arglist);
        break;

      }
    fprintf (stderr,"%s:%d fatal error - unsupported action\n",__FILE__,__LINE__);
    mygetch ();
    return 44;
  }
  else {
      printf ("screen-session %s helper program\n",VERSION);
  }
}

#endif
