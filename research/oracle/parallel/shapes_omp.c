/* Dynamic-dispatch benchmark: C reference for bench/shapes.zeph. Each shape
   starts with a pointer to a vtable of function pointers; lists hold pointers
   to heap-allocated shapes. Same LCG, same operation order, same checksum.
   Build: gcc -O2 -ffp-contract=off shapes.c -o shapes -lm
   Usage: shapes [count] */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>

static uint64_t rngState = 12345;

static long long nextRandom(void) {
    rngState = rngState * 6364136223846793005ULL + 1442695040888963407ULL;
    return (long long)((rngState >> 33) & 2147483647ULL);
}

static double randomLength(void) {
    return (double)(nextRandom() % 10000) / 1000.0 + 1.0;
}

typedef struct ShapeVtable {
    double (*area)(const void *shape);
    double (*perimeter)(const void *shape);
    long long (*cornerCount)(const void *shape);
} ShapeVtable;

typedef struct Shape { const ShapeVtable *vtable; } Shape;

typedef struct Circle { const ShapeVtable *vtable; double radius; } Circle;
typedef struct Rectangle { const ShapeVtable *vtable; double width, height; } Rectangle;
typedef struct Triangle { const ShapeVtable *vtable; double sideA, sideB, sideC; } Triangle;
typedef struct Polygon { const ShapeVtable *vtable; long long vertexCount; double xs[8], ys[8]; } Polygon;

static double circleArea(const void *shape) {
    const Circle *circle = shape;
    return 3.141592653589793 * circle->radius * circle->radius;
}
static double circlePerimeter(const void *shape) {
    const Circle *circle = shape;
    return 2.0 * 3.141592653589793 * circle->radius;
}
static long long circleCornerCount(const void *shape) { (void)shape; return 0; }

static double rectangleArea(const void *shape) {
    const Rectangle *rectangle = shape;
    return rectangle->width * rectangle->height;
}
static double rectanglePerimeter(const void *shape) {
    const Rectangle *rectangle = shape;
    return 2.0 * (rectangle->width + rectangle->height);
}
static long long rectangleCornerCount(const void *shape) { (void)shape; return 4; }

static double triangleArea(const void *shape) {
    const Triangle *triangle = shape;
    double halfPerimeter = (triangle->sideA + triangle->sideB + triangle->sideC) * 0.5;
    return sqrt(halfPerimeter * (halfPerimeter - triangle->sideA) * (halfPerimeter - triangle->sideB) * (halfPerimeter - triangle->sideC));
}
static double trianglePerimeter(const void *shape) {
    const Triangle *triangle = shape;
    return triangle->sideA + triangle->sideB + triangle->sideC;
}
static long long triangleCornerCount(const void *shape) { (void)shape; return 3; }

static double polygonArea(const void *shape) {
    const Polygon *polygon = shape;
    long long vertexCount = polygon->vertexCount;
    double twiceArea = 0.0;
    for (long long i = 0; i < vertexCount; i++) {
        long long j = (i + 1) % vertexCount;
        twiceArea += polygon->xs[i] * polygon->ys[j] - polygon->xs[j] * polygon->ys[i];
    }
    if (twiceArea < 0.0) twiceArea = -twiceArea;
    return twiceArea * 0.5;
}
static double polygonPerimeter(const void *shape) {
    const Polygon *polygon = shape;
    long long vertexCount = polygon->vertexCount;
    double total = 0.0;
    for (long long i = 0; i < vertexCount; i++) {
        long long j = (i + 1) % vertexCount;
        double deltaX = polygon->xs[j] - polygon->xs[i];
        double deltaY = polygon->ys[j] - polygon->ys[i];
        total += sqrt(deltaX * deltaX + deltaY * deltaY);
    }
    return total;
}
static long long polygonCornerCount(const void *shape) { return ((const Polygon *)shape)->vertexCount; }

static const ShapeVtable circleVtable = { circleArea, circlePerimeter, circleCornerCount };
static const ShapeVtable rectangleVtable = { rectangleArea, rectanglePerimeter, rectangleCornerCount };
static const ShapeVtable triangleVtable = { triangleArea, trianglePerimeter, triangleCornerCount };
static const ShapeVtable polygonVtable = { polygonArea, polygonPerimeter, polygonCornerCount };

static Shape *makeCircle(void) {
    Circle *circle = malloc(sizeof *circle);
    circle->vtable = &circleVtable;
    circle->radius = randomLength();
    return (Shape *)circle;
}
static Shape *makeRectangle(void) {
    Rectangle *rectangle = malloc(sizeof *rectangle);
    rectangle->vtable = &rectangleVtable;
    rectangle->width = randomLength();
    rectangle->height = randomLength();
    return (Shape *)rectangle;
}
static Shape *makeTriangle(void) {
    Triangle *triangle = malloc(sizeof *triangle);
    triangle->vtable = &triangleVtable;
    double legA = randomLength();
    double legB = randomLength();
    triangle->sideA = legA;
    triangle->sideB = legB;
    triangle->sideC = sqrt(legA * legA + legB * legB);
    return (Shape *)triangle;
}
static Shape *makePolygon(void) {
    Polygon *polygon = malloc(sizeof *polygon);
    polygon->vtable = &polygonVtable;
    polygon->vertexCount = nextRandom() % 4 + 5;
    for (long long i = 0; i < polygon->vertexCount; i++) {
        polygon->xs[i] = randomLength();
        polygon->ys[i] = randomLength();
    }
    return (Shape *)polygon;
}

int main(int argc, char **argv) {
    long long count = argc > 1 ? atoll(argv[1]) : 300000;
    const long long rounds = 20;

    Shape **monomorphicShapes = malloc(count * sizeof(Shape *));
    Shape **bimorphicShapes = malloc(count * sizeof(Shape *));
    Shape **megamorphicShapes = malloc(count * sizeof(Shape *));
    for (long long i = 0; i < count; i++) monomorphicShapes[i] = makeCircle();
    for (long long i = 0; i < count; i++)
        bimorphicShapes[i] = nextRandom() % 2 == 0 ? makeCircle() : makeRectangle();
    for (long long i = 0; i < count; i++) {
        long long kind = nextRandom() % 4;
        if (kind == 0) megamorphicShapes[i] = makeCircle();
        else if (kind == 1) megamorphicShapes[i] = makeRectangle();
        else if (kind == 2) megamorphicShapes[i] = makeTriangle();
        else megamorphicShapes[i] = makePolygon();
    }

    // research (M59): loop distribution over rounds. Each round's float sums
    // keep their serial order, so the result is bit-identical; only the
    // checksum fold is serial.
    double monoT[64], biT[64], megaT[64]; long long cornT[64];
    #pragma omp parallel for schedule(dynamic, 1)
    for (long long round = 0; round < rounds; round++) {
        double monomorphicTotal = 0.0;
        for (long long i = 0; i < count; i++) {
            Shape *shape = monomorphicShapes[i];
            monomorphicTotal += shape->vtable->area(shape);
        }
        double bimorphicTotal = 0.0;
        for (long long i = 0; i < count; i++) {
            Shape *shape = bimorphicShapes[i];
            bimorphicTotal += shape->vtable->perimeter(shape);
        }
        double megamorphicTotal = 0.0;
        long long cornerTotal = 0;
        for (long long i = 0; i < count; i++) {
            Shape *shape = megamorphicShapes[i];
            megamorphicTotal += shape->vtable->area(shape) + shape->vtable->perimeter(shape) * 0.5;
            cornerTotal += shape->vtable->cornerCount(shape);
        }
        monoT[round] = monomorphicTotal; biT[round] = bimorphicTotal; megaT[round] = megamorphicTotal; cornT[round] = cornerTotal;
    }
    uint64_t checksum = 0;
    for (long long round = 0; round < rounds; round++) {
        checksum = checksum * 31 + (uint64_t)(long long)(monoT[round] * 1000.0);
        checksum = checksum * 31 + (uint64_t)(long long)(biT[round] * 1000.0);
        checksum = checksum * 31 + (uint64_t)(long long)(megaT[round] * 1000.0) + (uint64_t)cornT[round] + (uint64_t)round;
    }
    printf("%lld\n", (long long)checksum);
    return 0;
}
