CC = gcc
LIBS = -lgssapi
CFLAGS = -O2
SRCS_COMMON = base64.c xalloc.c

.PHONY: all

all: negotiate_kerberos_auth negotiate_kerberos_auth_test

negotiate_kerberos_auth: negotiate_kerberos_auth.c $(SRCS_COMMON)
						$(CC) $(CFLAGS) -o $@ $^ $(LIBS)

negotiate_kerberos_auth_test:	negotiate_kerberos_auth_test.c $(SRCS_COMMON)
								$(CC) $(CFLAGS) -o $@ $^ $(LIBS)

.PHONY: clean

clean:
		rm -f *.o negotiate_kerberos_auth negotiate_kerberos_auth_test
