#include "hw2.h"

int main(int argc, char **argv) {
    printf("\n---Starting Custom Shell---\n ---------------\n");

    int childPid;
    char *cmdLine;
    parseInfo *info;

    while(1) {
        pwd();
        cmdLine = readline(">");
        info = parse(cmdLine);
        childPid = fork();
        if (!isPipe(info) && cd(info)) continue;
        if (childPid == 0) {
            executeCommand(info);
        } else {
            waitpid(childPid, NULL, 0);
        }
    }
}


