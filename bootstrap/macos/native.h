#ifndef ZEPHYR_DARWIN_H
#define ZEPHYR_DARWIN_H
void zephyr_macos_init(int argc, char **argv, const char *module);
void zephyr_macos_set_exit_handler(void (*handler)(int));
#endif
