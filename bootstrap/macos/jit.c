// Native executable memory services. The Python driver links ARM64 objects in
// memory; this boundary is the only place that makes their code writable.
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <pthread.h>
#include <libkern/OSCacheControl.h>
#include <setjmp.h>
#include "native.h"

static unsigned char *code, *data;
static size_t capacity;
static jmp_buf guest_exit;
static int exit_code;
extern void zephyr_jit_enter(void *entry);

static void leave_guest(int status) {
    exit_code = status;
    longjmp(guest_exit,1);
}

int zephyr_jit_execute(void *entry) {
    exit_code = 0;
    zephyr_macos_set_exit_handler(leave_guest);
    if (!setjmp(guest_exit)) zephyr_jit_enter(entry);
    zephyr_macos_set_exit_handler(NULL);
    return exit_code;
}

void *zephyr_jit_open(size_t size) {
    if (code) return NULL;
    code = mmap(NULL, size, PROT_READ|PROT_WRITE|PROT_EXEC,
                MAP_PRIVATE|MAP_ANON|MAP_JIT, -1, 0);
    if (code == MAP_FAILED) { code = NULL; return NULL; }
    data = mmap(code + size, size, PROT_READ|PROT_WRITE,
                MAP_PRIVATE|MAP_ANON, -1, 0);
    if (data == MAP_FAILED) { munmap(code,size); code = NULL; data = NULL; return NULL; }
    capacity = size;
    pthread_jit_write_protect_np(1);
    return code;
}

void *zephyr_jit_data(void) { return data; }

int zephyr_jit_publish(size_t offset, const void *bytes, size_t size) {
    if (!code || offset > capacity || size > capacity-offset) return 0;
    pthread_jit_write_protect_np(0);
    memcpy(code+offset, bytes, size);
    pthread_jit_write_protect_np(1);
    sys_icache_invalidate(code+offset, size);
    return 1;
}

void zephyr_jit_close(void) {
    if (code) munmap(code,capacity);
    if (data) munmap(data,capacity);
    code = data = NULL;
    capacity = 0;
}
