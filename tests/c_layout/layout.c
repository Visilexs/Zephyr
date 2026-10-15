/* The C side of tests/c_layout/layout.zeph: the same structs, the same output. */
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
struct Header { uint32_t magic; uint16_t version; uint16_t flags; uint64_t size; };
struct Mixed { uint8_t tag; double value; int16_t small; bool ok; float ratio; struct Header inner; uint8_t name[5]; int32_t count; };
struct __attribute__((packed)) Packed { uint8_t tag; uint32_t value; uint16_t more; };
struct Arrays { int16_t xs[3]; float fs[2]; struct Header hs[2]; uint8_t tail; };
struct Tiny { uint8_t a; };
struct Pair { uint8_t a; uint16_t b; };
struct Trail { uint64_t big; uint8_t small; };
struct __attribute__((packed)) PackedInner { uint8_t a; struct Header h; uint8_t b; };
struct Wrap { uint8_t a; struct Packed p; int8_t b; };
struct Floats { float a; double b; float c; };
struct Ints { int8_t a; int64_t b; int32_t c; int64_t d; uint16_t e; };
#define O(T, f) (int)offsetof(struct T, f)
int main(void) {
    printf("Header %d %d %d %d %d\n", (int)sizeof(struct Header), O(Header, magic), O(Header, version), O(Header, flags), O(Header, size));
    printf("Mixed %d %d %d %d %d %d %d %d %d\n", (int)sizeof(struct Mixed), O(Mixed, tag), O(Mixed, value), O(Mixed, small), O(Mixed, ok), O(Mixed, ratio), O(Mixed, inner), O(Mixed, name), O(Mixed, count));
    printf("Packed %d %d %d %d\n", (int)sizeof(struct Packed), O(Packed, tag), O(Packed, value), O(Packed, more));
    printf("Arrays %d %d %d %d %d\n", (int)sizeof(struct Arrays), O(Arrays, xs), O(Arrays, fs), O(Arrays, hs), O(Arrays, tail));
    printf("Tiny %d %d\n", (int)sizeof(struct Tiny), O(Tiny, a));
    printf("Pair %d %d %d\n", (int)sizeof(struct Pair), O(Pair, a), O(Pair, b));
    printf("Trail %d %d %d\n", (int)sizeof(struct Trail), O(Trail, big), O(Trail, small));
    printf("PackedInner %d %d %d %d\n", (int)sizeof(struct PackedInner), O(PackedInner, a), O(PackedInner, h), O(PackedInner, b));
    printf("Wrap %d %d %d %d\n", (int)sizeof(struct Wrap), O(Wrap, a), O(Wrap, p), O(Wrap, b));
    printf("Floats %d %d %d %d\n", (int)sizeof(struct Floats), O(Floats, a), O(Floats, b), O(Floats, c));
    printf("Ints %d %d %d %d %d %d\n", (int)sizeof(struct Ints), O(Ints, a), O(Ints, b), O(Ints, c), O(Ints, d), O(Ints, e));
    printf("scalars %d %d %d %d %d %d %d %d\n", (int)sizeof(int8_t), (int)sizeof(uint16_t), (int)sizeof(int32_t), (int)sizeof(uint64_t), (int)sizeof(float), (int)sizeof(double), (int)sizeof(bool), (int)sizeof(int64_t));
    return 0;
}
