// Minimal ptrace sampling profiler for static Zephyr ELF binaries (no perf or
// valgrind needed). Every interval it stops the child, records RIP and an RBP
// frame-chain walk (return addresses), then resumes it.
// Build: gcc -O2 -o sampler research/sampler.c
// Usage: sampler OUT.txt INTERVAL_US program args...
// Each output line: rip ret1 ret2 ... (hex), one line per sample.
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/ptrace.h>
#include <sys/types.h>
#include <sys/user.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static long peek(pid_t pid, unsigned long addr, int *ok) {
    errno = 0;
    long v = ptrace(PTRACE_PEEKDATA, pid, (void *)addr, 0);
    *ok = errno == 0;
    return v;
}

int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "usage: sampler OUT INTERVAL_US prog args...\n"); return 2; }
    FILE *out = fopen(argv[1], "w");
    long interval = atol(argv[2]);
    pid_t pid = fork();
    if (pid == 0) {
        ptrace(PTRACE_TRACEME, 0, 0, 0);
        execv(argv[3], argv + 3);
        perror("execv"); _exit(127);
    }
    int status;
    waitpid(pid, &status, 0);                     // stopped at exec
    ptrace(PTRACE_SETOPTIONS, pid, 0, PTRACE_O_EXITKILL);
    ptrace(PTRACE_CONT, pid, 0, 0);
    long samples = 0;
    for (;;) {
        struct timespec ts = { 0, interval * 1000 };
        nanosleep(&ts, 0);
        if (kill(pid, SIGSTOP) != 0) break;
        if (waitpid(pid, &status, 0) < 0) break;
        if (WIFEXITED(status) || WIFSIGNALED(status)) break;
        int sig = WSTOPSIG(status);
        if (sig != SIGSTOP) { ptrace(PTRACE_CONT, pid, 0, sig); continue; }
        struct user_regs_struct r;
        if (ptrace(PTRACE_GETREGS, pid, 0, &r) == 0) {
            fprintf(out, "%llx", r.rip);
            unsigned long fp = r.rbp;
            for (int depth = 0; depth < 64 && fp; depth++) {
                int ok1, ok2;
                long next = peek(pid, fp, &ok1);
                long ret = peek(pid, fp + 8, &ok2);
                if (!ok1 || !ok2 || (unsigned long)next <= fp) break;
                fprintf(out, " %lx", ret);
                fp = next;
            }
            fputc('\n', out);
            samples++;
        }
        ptrace(PTRACE_CONT, pid, 0, 0);
    }
    while (waitpid(pid, &status, 0) > 0 && !(WIFEXITED(status) || WIFSIGNALED(status))) ptrace(PTRACE_CONT, pid, 0, WSTOPSIG(status));
    fclose(out);
    fprintf(stderr, "%ld samples, child exit %d\n", samples, WIFEXITED(status) ? WEXITSTATUS(status) : -1);
    return 0;
}
