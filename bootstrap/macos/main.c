#include "native.h"
#include <stdio.h>
#include <stdlib.h>
#include <sys/resource.h>
#include <mach-o/dyld.h>
#include <limits.h>
extern void zephyr_entry(void);
int main(int argc, char **argv) {
    // Zephyr's compiler has deeply recursive parser/codegen paths. Request up
    // to 64 MiB within the caller's hard limit, rather than relying on 8 MiB.
    struct rlimit limit;
    if (!getrlimit(RLIMIT_STACK,&limit)) {
        rlim_t wanted=64*1024*1024;
        if(limit.rlim_max!=RLIM_INFINITY && wanted>limit.rlim_max)wanted=limit.rlim_max;
        if(limit.rlim_cur<wanted) { limit.rlim_cur=wanted; setrlimit(RLIMIT_STACK,&limit); }
    }
    char module[PATH_MAX]; uint32_t size=sizeof(module);
    if(_NSGetExecutablePath(module,&size)) { fputs("executable path too long\n",stderr); return 1; }
    zephyr_macos_init(argc,argv,module);
    zephyr_entry();
    return 0;
}
