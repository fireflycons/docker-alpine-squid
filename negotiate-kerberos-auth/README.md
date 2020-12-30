# negotiate_kerberos_auth

These sources, originally created by Markus Moeller, were extracted from the full Squid source [here](https://github.com/dkurochkin/squid) and adapted by me to compile directly on Alpine against Heimdal Kerberos.

The binary versions of this helper are null implementations in the Squid APK on the Alpine packages site. If you look at the original source it appears that `negotiate_kerberos_auth` was compiled with `HAVE_GSSAPI` undefined, resulting in Squid receiving the following error:

```
BH Kerberos authentication not supported
```

Original license included - see [COPYING](./COPYING)


