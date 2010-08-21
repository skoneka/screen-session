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
#include <string.h>

int main(int argc, char **argv) {
///./program scrollbackfile datafile
    int i;
    char buf[256];
    FILE *fp=NULL;
    char ch;
    int c;
     
    fp=fopen(argv[1],"r");
    if(fp) {
        while((c=fgetc(fp))!=EOF) {
            fputc(c,stdout);
        }
        fclose(fp);
    }
    else {
        printf("Cannot open scrollback file.\n");
    }
    fp=NULL;
    printf("\nEND OF SCROLLBACK\n");



    fp=fopen(argv[2],"r");
    if(fp) {

        int nl_c=0;
        int procs_c=0;
        while((c=fgetc(fp))!=EOF) {
            if(c=='\n') {
                nl_c++;
            }
            if (nl_c > 4)
                break;
         //   fputc(c,stdout);
        }
        
        fscanf(fp,"%s\n",buf);
        printf("%s\n",buf);
        procs_c=atoi(buf);
        printf("This window had %d processes:\n",procs_c);
        char procs[10][100];
        for(i=0;i<procs_c;i++) {
            fscanf(fp,"%s\n",buf); //read --
            printf("%s %d: ",buf,i);
            int j;
            for(j=0;j<3;j++) {
                fscanf(fp,"%s\n",buf); //cwd exe args
                strcpy(procs[i*3+j],buf);
            }
            for(j=2;j>=0;j--) {
                printf("%s\n",procs[i*3+j]);
            }
        }

        int arg_list_len=3;
        char *arg_list[] = {
            "sh",
            "/",
            NULL
        };
        printf("CWD to %s\n",procs[0]);
        //chdir(procs[0]);

printf("arg_list:");
for(i=0;i<arg_list_len;i++)
    printf("%s ",arg_list[i]);
printf("\n");

        //  printf("starting..\n");
        execvp("sh",arg_list);
        printf("after\n");
    }
    else {
        printf("Cannot open data file.\n");
    }
    


    return 0;
}
