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

#define MAXBUFFERSIZE   80

char buf[256];

enum menu
{
    NONE=0,
    RESET,
    EXIT,
    ALL,
    ONLY,
    NUMBER
};

void cleartoendofline( void );          /* ANSI function prototype */



void cleartoendofline( void )
{
    char ch;
    ch = getchar();
    while( ch != '\n' )
        ch = getchar();
}
int parseNumber(char *buffer) {
        int number;
        number = atoi( buffer );
        if( (number < 0) )
            number = 0;
        return number;
}

int mygetch ( void ) 
{
  int ch;
  struct termios oldt, newt;
  
  tcgetattr ( STDIN_FILENO, &oldt );
  newt = oldt;
  newt.c_lflag &= ~( ICANON | ECHO );
  tcsetattr ( STDIN_FILENO, TCSANOW, &newt );
  ch = getchar();
  tcsetattr ( STDIN_FILENO, TCSANOW, &oldt );
  
  return ch;
}


void userInput(int *menu_num, int *num) {
    char    ch;                     /* handles user input */
    char    buffer[MAXBUFFERSIZE];  /* sufficient to handle one line */
    int     char_count;             /* number of characters read for this line */
    int     exit_flag = 0, valid_choice,number=0 ;
    enum menu menu_choice=NONE;

    while( exit_flag  == 0 && menu_choice==NONE) {
        valid_choice = 0;
        while( valid_choice == 0 ) {
            printf("[number] / [O]nly [number] / [A]ll / [E]xit / [R]eset?\n");
            ch = getchar();
            char_count = 0;
            while( (ch != '\n')  &&  (char_count < MAXBUFFERSIZE)) {
                if(ch!=' ')
                    buffer[char_count++] = ch;
                ch = getchar();
            }
            buffer[char_count] = 0x00;      /* null terminate buffer */
            switch( buffer[0] ) {
                case 'r':
                case 'R':
                    number =-1;
                    valid_choice=1;
                    menu_choice=RESET;
                    break;
                case 'a':
                case 'A':
                    number =-1;
                    menu_choice=ALL;
                    valid_choice=1;
                    break;
                case 'o':
                case 'O':
                    menu_choice=ONLY;
                    number = parseNumber(buffer+1);
                    valid_choice=1;
                    break;
                case 'e':
                case 'E':
                    menu_choice=EXIT;
                    valid_choice=1;
                    break;
                case '1':
                case '2':
                case '3':
                case '4':
                case '5':
                case '6':
                case '7':
                case '8':
                case '9':
                case '0':
                    menu_choice=NUMBER;
                    number = parseNumber(buffer);
                    valid_choice=1;
                    break;
                default:
                    menu_choice=NONE;
                    valid_choice=0;
            }

                
        }

/*         valid_choice = 0;
        while( valid_choice == 0 ) {
            printf("Continue (Y/N)?\n");
            scanf(" %c", &ch );
            ch = toupper( ch );
            if((ch == 'Y') || (ch == 'N') )
                valid_choice = 1;
            else
                printf("\007Error: Invalid choice\n");
            cleartoendofline();
        }
        if( ch == 'N' ) exit_flag = 1;
 */    }
    *num=number;
    *menu_num=menu_choice;
}

char **make_arglist_simple(char *program) {
    char **args=NULL;
    args=malloc(2*sizeof(char*));
    args[0]=malloc((strlen(program)+1)*sizeof(char));
    args[1]=NULL;    
    strcpy(args[0],program);
    return args;
}
char **make_arglist(char *program,char *arg1, char *arg2, int procs_n,int *procs) {
    int i;
    char **args=NULL;
    char buf[10];
    args=malloc((2+procs_n)*sizeof(char*));
    args[0]=malloc((strlen(program)+1)*sizeof(char));
    args[1]=malloc((strlen(arg1)+1)*sizeof(char));
    args[2]=malloc((strlen(arg2)+1)*sizeof(char));
    for(i=3;i<procs_n+3;i++) {
        int i_procs=i-3;
        sprintf(buf,"%d",procs[i_procs]);
        args[i]=malloc((strlen(buf)+1)*sizeof(char));
        strcpy(args[i],buf);
    }
    strcpy(args[0],program);
    strcpy(args[1],arg1);
    strcpy(args[2],arg2);
    args[procs_n+3]=NULL;
    return args;
}
int start(char *thisprogram,char *config,int procs_n,int *procs) {
    if(procs_n==0)
        return 0;
    char proc_cwd[256];
    char proc_exe[256];
    int proc_args_n;
    char proc_blacklisted[10];
    char **proc_args;
    int i,nl_c=0;
    char c;
    FILE *fp=NULL;
    fp=fopen(config,"r");
    if(!fp) {
        printf("Cannot open data file. Aborting.\n");
        printf("Press any key to continue...\n");
        mygetch();
        return 1;
    }
    while((c=fgetc(fp))!=EOF) {
        if(c=='\n') {
            nl_c++;
        }
        else if (nl_c > (5+(procs[0]*6)))
            break;
    }
    printf("starting: ");
    fscanf(fp,"%s\n",proc_cwd); //cwd exe args
    fscanf(fp,"%s\n",proc_exe);
    fscanf(fp,"%d\n",&proc_args_n);
    if(procs_n>1) {
        proc_args_n+=2;
    }
    proc_args = malloc((proc_args_n+1)*sizeof(char*));
    for(i=0;i<proc_args_n;i++) {
        proc_args[i]=malloc(100*sizeof(char));
    }
    proc_args[proc_args_n]=NULL;
    int null_c=0;
    int word_c=0;
    while((c=fgetc(fp))!=EOF) {
        if(c=='\0') {
            null_c++;
            word_c=0;
            if(null_c%2)
                fputs(" \"",stdout);
            else 
                fputs("\" ",stdout);
        }
        else if(c=='\n') {
            if(null_c%2)
                fputs("\" ",stdout);
            break;
        }
        else {
            fputc(c,stdout);
            proc_args[null_c][word_c]=c;
            word_c++;
            
        }
        if (null_c > proc_args_n)
            break;
    }
    fscanf(fp,"%s\n",proc_blacklisted);
    if(strcmp(proc_blacklisted,"True")==0)
        return 0;
    if(procs_n>1) {
        for(i=proc_args_n-1;i>2;i--) {
            strcpy(proc_args[i],proc_args[i-2]);
        }
        strcpy(proc_args[1],"-c");

        char command[1000];
        strcpy(command,thisprogram);
        strcat(command," -s ");
        strcat(command,config);
        for(i=1;i<procs_n;i++) {
            char buf[10];
            sprintf(buf," %d",procs[i]);
            strcat(command,buf);
        }
        strcat(command,"; ");
        strcat(command,proc_exe);

        strcpy(proc_args[2],command);
        
    }
    printf("\n");
    chdir(proc_cwd);
    execvp(proc_exe,proc_args);
    return 1;

}

int main(int argc, char **argv) {
//./program scrollbackfile datafile
//./program -s datafile [processes..]
    int i;
    FILE *fp=NULL;
    int c;
    if(argc==1) {
        printf("screen-session helper program\n");
        return 0;
    }
    if (strcmp(argv[1],"-s")==0) {
        int *procs;
        procs=malloc((argc-3)*sizeof(int));
        for (i=3;i<argc;i++)
            procs[i-3]=atoi(argv[i]);
        start(argv[0],argv[2],i-3,procs);
        return 0;
    }
    else if (strcmp(argv[1],"-m")==0) {
        //marker mode for ScreenSession.__get_focus_offset()
        sleep(10);
        return 0;
    }
     
    fp=fopen(argv[1],"r");
    if(fp) {
        printf("BEGIN SCROLLBACK\n");
        while((c=fgetc(fp))!=EOF) {
            fputc(c,stdout);
        }
        fclose(fp);
        printf("\nEND SCROLLBACK\n");
    }
    else {
        printf("Cannot open scrollback file.\n");
    }
    fp=NULL;



    fp=fopen(argv[2],"r");
    if(!fp) {
        printf("Cannot open data file. Aborting.\n");
        printf("Press any key to continue...\n");
        mygetch();
        return 1;
    }

    int nl_c=0;
    int procs_c=0;
    while((c=fgetc(fp))!=EOF) {
        if(c=='\n') {
            nl_c++;
        }
        if (nl_c==1)
           fputc(c,stdout);
        else if (nl_c > 4)
            break;
     //   fputc(c,stdout);
    }
    
    fscanf(fp,"%d\n",&procs_c);
    printf("\nThis window had %d programs running:\n",procs_c);

    char proc_cwd[256];
    char proc_exe[256];
    int proc_args_n;
    char proc_blacklisted[10];


    for(i=0;i<procs_c;i++) {
        fscanf(fp,"%s\n",buf); //read --
        printf("%s %d: ",buf,i);

        fscanf(fp,"%s\n",proc_cwd); //cwd exe args
        fscanf(fp,"%s\n",proc_exe);
        fscanf(fp,"%d\n",&proc_args_n);
        int null_c=0;
        while((c=fgetc(fp))!=EOF) {
            if(c=='\0') {
                null_c++;
                if(null_c%2)
                    fputs(" \"",stdout);
                else 
                    fputs("\" ",stdout);
            }
            else if(c=='\n') {
                if(null_c%2)
                    fputs("\" ",stdout);
                break;
            }
            else
                fputc(c,stdout);
            if (null_c > proc_args_n)
                break;
        }
        
        fscanf(fp,"%s\n",proc_blacklisted);
        printf("\n");
        printf("\tCWD: %s\n",proc_cwd);
        printf("\tEXE: %s\n",proc_exe);
        if (strcmp(proc_blacklisted,"True")==0)
            printf("\tBLACKLISTED\n");
    }
    printf("--Restore--\n");
    int menu;
    int number;
    userInput(&menu,&number);
    char *shell=NULL;
    char **arglist=NULL;
    int *args;
    args=malloc(procs_c*sizeof(int));
    switch(menu) {
        case EXIT:
            printf("Exiting...\n");
            return 0;
            break;
        case RESET:
            shell = getenv("SHELL");
            printf("Starting default shell(%s) in last cwd(%s)...\n",shell,proc_cwd);
            //printf("Starting default shell in last working directory...\n");
            chdir(proc_cwd);
            execl(shell,shell,NULL);
            
            break;
        case ONLY:
            printf("Starting program %d...\n",number);
            args[0]=number;
            arglist=make_arglist(argv[0],"-s",argv[2],1,args);
            execvp(argv[0],arglist);
            break;
        case ALL:
            printf("Starting all programs...\n");
            for(i=0;i<procs_c;i++) {
                args[i]=i;
            }
            arglist=make_arglist(argv[0],"-s",argv[2],procs_c,args);
            execvp(argv[0],arglist);

            break;
        case NUMBER:
            printf("Starting programs up to %d...\n",number);
            if(number>procs_c) {
                number=procs_c;
                printf("No such window. Starting programs up to %d...\n",number-1);
            }
            else
                number++;
            for(i=0;i<number;i++) {
                args[i]=i;
            }
            arglist=make_arglist(argv[0],"-s",argv[2],number,args);
            execvp(argv[0],arglist);
            break;

    }

    return 0;
}


