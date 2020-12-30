#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "xalloc.h"

void *
xmalloc(size_t sz)
{
    if (sz < 1)
        sz = 1;

    void *p = malloc(sz);

    if (p == NULL) {
        static char msg[128];
        snprintf(msg, 128, "xmalloc: Unable to allocate %lu bytes!\n", (unsigned long)sz);
        perror(msg);
        exit(1);
    }
    return (p);
}

void
xfree(void *s)
{
    if (s == NULL)
        return;

    free(s);
}

char *
xstrdup(const char *s)
{
    size_t sz;
    char *p;

    if (s == NULL) {
        perror("xstrdup: tried to dup a NULL pointer!");
        exit(1);
    }

    /* copy string, including terminating character */
    sz = strlen(s) + 1;
    p = (char *)xmalloc(sz);
    memcpy(p, s, sz);

    return p;
}

