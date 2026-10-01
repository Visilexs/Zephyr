// Native Darwin services for the Zephyr runtime. Uses the Apple ARM64 ABI.
#include "native.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>
#include <pthread.h>
#include <dirent.h>
#include <limits.h>
#include <spawn.h>
#include <sys/wait.h>
#include <mach-o/dyld.h>

typedef uint64_t U;
static char *command_line;
static void (*exit_handler)(int);
static char module_path[PATH_MAX];
static _Thread_local U last_error;
static pthread_key_t tls_keys[512];
static unsigned tls_count;
static size_t page_round(size_t n) { size_t p = (size_t)getpagesize(); return (n+p-1)&~(p-1); }
static int protection(U p) { return p == 1 ? PROT_NONE : p == 2 ? PROT_READ : p == 4 ? PROT_READ|PROT_WRITE : p == 16 ? PROT_EXEC : p == 32 ? PROT_READ|PROT_EXEC : PROT_READ|PROT_WRITE|PROT_EXEC; }
static void unsupported(const char *name) { fprintf(stderr, "Zephyr macOS: %s is not supported\n", name); exit(1); }
void zephyr_macos_init(int argc, char **argv, const char *module) {
    if (!realpath(module, module_path)) { fprintf(stderr, "cannot resolve compiler/program path: %s\n", module); exit(1); }
    size_t size = 1;
    for (int i=0;i<argc;i++) {
        // The current Zephyr runtime's argument parser cannot encode literal quotes.
        if (strchr(argv[i], '"')) unsupported("literal double quotes in arguments (runtime parser limitation)");
        size += strlen(argv[i])+3;
    }
    command_line = calloc(1,size);
    if (!command_line) { perror("calloc"); exit(1); }
    char *at = command_line;
    for (int i=0;i<argc;i++) {
        if (i) *at++=' ';
        *at++='"'; size_t n=strlen(argv[i]); memcpy(at,argv[i],n); at+=n; *at++='"';
    }
}
U darwin_VirtualAlloc(U address,U size,U kind,U protect) {
    if (!size) return 0;
    if (address && kind == 4096) {
        size_t page = (size_t)getpagesize();
        uintptr_t base = address & ~(page-1);
        size_t span = page_round(size + address-base);
        return mprotect((void*)base,span,protection(protect)) == 0 ? address : 0;
    }
    void *p=mmap((void*)address,page_round(size),kind == 8192 ? PROT_NONE : protection(protect),MAP_PRIVATE|MAP_ANON,-1,0);
    return p == MAP_FAILED ? 0 : (U)p;
}
U darwin_VirtualProtect(U address,U size,U protect,U previous) {
    if (previous) *(uint32_t*)previous=4;
    size_t page=(size_t)getpagesize(); uintptr_t base=address&~(page-1);
    return mprotect((void*)base,page_round(size+address-base),protection(protect))==0;
}
U darwin_GetStdHandle(U number) { return (int32_t)number == -10 ? 0 : (int32_t)number == -11 ? 1 : 2; }
U darwin_WriteFile(U fd,U buffer,U size,U count,U overlapped) {
    (void)overlapped; ssize_t n;
    do { n=write((int)fd,(void*)buffer,size); } while(n<0 && errno==EINTR);
    if(count) *(uint32_t*)count=n<0?0:(uint32_t)n;
    if(n<0)last_error=errno==EPIPE?109:5;
    return n>=0;
}
U darwin_ReadFile(U fd,U buffer,U size,U count,U overlapped) {
    (void)overlapped; ssize_t n;
    do { n=read((int)fd,(void*)buffer,size); } while(n<0 && errno==EINTR);
    if(count) *(uint32_t*)count=n<0?0:(uint32_t)n;
    if(n<0)last_error=errno==EPIPE?109:5;
    return n>=0;
}
U darwin_CreateFileA(U path,U access,U share,U security,U disposition,U flags,U template) {
    (void)share;(void)security;(void)flags;(void)template;
    int mode = access&0x40000000 ? O_WRONLY : access&4 ? O_WRONLY|O_APPEND : O_RDONLY;
    if(disposition==2) mode|=O_CREAT|O_TRUNC;
    else if(disposition==4) mode|=O_CREAT;
    int fd=open((char*)path,mode,0666); if(fd<0)last_error=errno==ENOENT?2:5;
    return (U)(int64_t)fd;
}
U darwin_GetFileSize(U fd,U high) { struct stat s; if(fstat((int)fd,&s))return UINT32_MAX; if(high)*(uint32_t*)high=(U)s.st_size>>32; return (uint32_t)s.st_size; }
U darwin_CloseHandle(U fd) {
    if (fd == (U)-2) return 1; // std/io has no native child-thread resource to close
    if (fd > INT_MAX && fd != (U)-1) { free((void*)fd); return 1; }
    return close((int)fd)==0;
}
void zephyr_macos_set_exit_handler(void (*handler)(int)) { exit_handler=handler; }
U darwin_ExitProcess(U code) {
    if (exit_handler) exit_handler((int)code);
    exit((int)code);
}
U darwin_GetCommandLineA(void) { return (U)command_line; }
U darwin_GetModuleFileNameA(U module,U buffer,U capacity) {
    (void)module; size_t n=strlen(module_path); if(!capacity)return 0;
    size_t amount=n<capacity-1?n:capacity-1; memcpy((void*)buffer,module_path,amount); ((char*)buffer)[amount]=0;
    return n<capacity?n:capacity;
}
U darwin_GetFileAttributesA(U path) { struct stat s; if(stat((char*)path,&s))return UINT32_MAX; return S_ISDIR(s.st_mode)?16:128; }
U darwin_GetFullPathNameA(U path,U capacity,U buffer,U filepart) {
    char full[PATH_MAX]; if(!realpath((char*)path,full))return 0;
    size_t n=strlen(full); if(n>=capacity)return n+1;
    memcpy((void*)buffer,full,n+1);
    if(filepart)*(char**)filepart=(char*)buffer+(strrchr(full,'/')-full)+1;
    return n;
}
U darwin_InitializeCriticalSection(U address) {
    pthread_mutexattr_t attr; pthread_mutexattr_init(&attr); pthread_mutexattr_settype(&attr,PTHREAD_MUTEX_RECURSIVE);
    int r=pthread_mutex_init((pthread_mutex_t*)address,&attr); pthread_mutexattr_destroy(&attr); return r==0;
}
U darwin_EnterCriticalSection(U address) { return pthread_mutex_lock((pthread_mutex_t*)address)==0; }
U darwin_LeaveCriticalSection(U address) { return pthread_mutex_unlock((pthread_mutex_t*)address)==0; }
U darwin_TryEnterCriticalSection(U address) { return pthread_mutex_trylock((pthread_mutex_t*)address)==0; }
U darwin_GetCurrentThreadId(void) { uint64_t id; pthread_threadid_np(NULL,&id); return id; }
U darwin_GetCurrentThreadStackLimits(U low,U high) {
    void *top=pthread_get_stackaddr_np(pthread_self()); size_t size=pthread_get_stacksize_np(pthread_self());
    *(U*)low=(U)top-size; *(U*)high=(U)top; return 0;
}
U darwin_TlsAlloc(void) { if(tls_count>=512)return UINT32_MAX; unsigned i=tls_count++; return pthread_key_create(&tls_keys[i],NULL)==0?i:UINT32_MAX; }
U darwin_TlsSetValue(U slot,U value) { return slot<tls_count && pthread_setspecific(tls_keys[slot],(void*)value)==0; }
U darwin_TlsGetValue(U slot) { return slot<tls_count?(U)pthread_getspecific(tls_keys[slot]):0; }
U darwin_GetCurrentProcess(void) { return (U)-1; }
U darwin_FlushInstructionCache(U process,U address,U size) { (void)process;(void)address;(void)size; return 1; }
// Dynamic Windows libraries and Windows thread suspension cannot be emulated by
// returning plausible success values: stop with an explicit diagnostic instead.
U darwin_LoadLibraryA(U name) { (void)name; unsupported("Windows DLL loading"); return 0; }
U darwin_GetProcAddress(U module,U name) { (void)module;(void)name; unsupported("Windows DLL symbols"); return 0; }
U darwin_SuspendThread(U thread) { (void)thread; unsupported("thread suspension"); return 0; }
U darwin_ResumeThread(U thread) { (void)thread; unsupported("threads"); return 0; }
U darwin_GetThreadContext(U thread,U context) { (void)thread;(void)context; unsupported("thread contexts"); return 0; }
U darwin_CreateThread(U security,U size,U entry,U argument,U flags,U id) { (void)security;(void)size;(void)entry;(void)argument;(void)flags;(void)id; unsupported("threads"); return 0; }
U darwin_GetSystemInfo(U buffer) { memset((void*)buffer,0,48); *(uint32_t*)(buffer+32)=(uint32_t)sysconf(_SC_NPROCESSORS_ONLN); return 0; }
U darwin_VirtualFree(U address,U size,U kind) { (void)address;(void)size;(void)kind; unsupported("VirtualFree"); return 0; }
U darwin_SetLastError(U code) { last_error=code; return 0; }
U darwin_GetLastError(void) { return last_error; }
U darwin_DeleteFileA(U path) { return unlink((char*)path)==0; }
U darwin_GetEnvironmentVariableA(U name,U buffer,U capacity) {
    const char *v=getenv((char*)name); if(!v) { last_error=203; return 0; }
    size_t n=strlen(v); if(n>=capacity)return n+1; memcpy((void*)buffer,v,n+1); return n;
}
static U nanos(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t); return (U)t.tv_sec*1000000000+t.tv_nsec; }
U darwin_GetTickCount64(void) { return nanos()/1000000; }
U darwin_QueryPerformanceCounter(U buffer) { *(U*)buffer=nanos(); return 1; }
U darwin_QueryPerformanceFrequency(U buffer) { *(U*)buffer=1000000000; return 1; }
U darwin_Sleep(U milliseconds) { struct timespec t={milliseconds/1000,(milliseconds%1000)*1000000}; while(nanosleep(&t,&t) && errno==EINTR) {} return 0; }
U darwin_FindNextFileA(U handle,U buffer) {
    struct dirent *entry; errno=0;
    while((entry=readdir((DIR*)handle))) {
        if(strlen(entry->d_name)>=260) { last_error=206; return 0; }
        memset((void*)buffer,0,320); strcpy((char*)buffer+44,entry->d_name); return 1;
    }
    last_error=errno?5:18; return 0;
}
U darwin_FindFirstFileA(U pattern,U buffer) {
    char *path=strdup((char*)pattern); size_t n=strlen(path);
    if(n>=2 && !strcmp(path+n-2,"/*"))path[n-2]=0;
    DIR *d=opendir(path); free(path); if(!d) { last_error=errno==ENOENT?2:5; return (U)-1; }
    if(!darwin_FindNextFileA((U)d,buffer)) { closedir(d); return (U)-1; } return (U)d;
}
U darwin_FindClose(U handle) { return closedir((DIR*)handle)==0; }

// Native subprocesses: tokenize the command without invoking a shell. A shell
// is used only when the Zephyr program explicitly requests one (e.g. sh -c).
typedef struct { pid_t pid; int status; int waited; } Child;
extern char **environ;
U darwin_CreateProcessA(U application,U command,U process_security,U thread_security,
                       U inherit,U flags,U environment,U directory,U startup,U result) {
    (void)process_security;(void)thread_security;(void)inherit;(void)startup;
    if(application || flags || environment || directory) { last_error=87; return 0; }
    char *storage=strdup((char*)command); if(!storage)return 0;
    char **arguments=calloc(strlen(storage)/2+2,sizeof(char*)); if(!arguments) { free(storage); return 0; }
    char *read_at=storage,*write_at=storage;size_t argc=0;
    while(*read_at) {
        while(*read_at==' ' || *read_at=='\t')read_at++;
        if(!*read_at)break;
        arguments[argc++]=write_at;int quoted=0;
        while(*read_at && (quoted || (*read_at!=' ' && *read_at!='\t'))) {
            if(*read_at=='"') { quoted=!quoted;read_at++; }
            else *write_at++=*read_at++;
        }
        if(quoted) { free(arguments);free(storage);last_error=87;return 0; }
        // Advance over a delimiter before writing a NUL over it in-place.
        if(*read_at)read_at++;
        *write_at++=0;
    }
    if(!argc) { free(arguments);free(storage);last_error=87;return 0; }
    Child *child=calloc(1,sizeof(*child)); if(!child) { free(arguments);free(storage);return 0; }
    int error=posix_spawnp(&child->pid,arguments[0],NULL,NULL,arguments,environ);
    free(arguments);free(storage);
    if(error) { free(child);last_error=error==ENOENT?2:5;return 0; }
    *(U*)result=(U)child;*(U*)(result+8)=(U)-2;*(uint32_t*)(result+16)=child->pid;return 1;
}
U darwin_WaitForSingleObject(U handle,U milliseconds) {
    Child *child=(Child*)handle;if(child->waited)return 0;
    U start=nanos();int options=milliseconds==UINT32_MAX?0:WNOHANG;
    for(;;) {
        pid_t result=waitpid(child->pid,&child->status,options);
        if(result==child->pid) { child->waited=1;return 0; }
        if(result<0 && errno!=EINTR) { last_error=5;return UINT32_MAX; }
        if(options && nanos()-start>=milliseconds*1000000)return 258;
        if(options)darwin_Sleep(1);
    }
}
U darwin_GetExitCodeProcess(U handle,U result) {
    Child *child=(Child*)handle;uint32_t code=259;
    if(child->waited)code=WIFEXITED(child->status)?WEXITSTATUS(child->status):128+WTERMSIG(child->status);
    *(uint32_t*)result=code;return 1;
}

U darwin_UnsupportedNativeInterop(void) { unsupported("raw machine-code / Win64 callPointer interop on ARM64"); return 0; }
