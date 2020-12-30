# Alpine Container Squid Proxy

I cobbled this together for two reasons

1. Primarily to create a safe browsing environment for my kids.
1. To mess about with and better understand proxies, MITM (Man-in-the-middle SSL decryption) and Kerberos authentication. Intercepting https traffic at a proxy is not uncommon within organisations, under the pretense that they are scanning for malicious payloads in the pages that their employees access.

THIS IS TARGETED AT PRIVATE USE. USE IN ANY OTHER ENVIRONMENT INCLUDING LEGALITY THEREOF IS ENTIRELY AT YOUR OWN RISK.

## General Configuration

For any of this to work correctly, you'll need full network authentication across your LAN, i.e. Windows or Samba Active Directory with Kerberos enabled, and a certificate authority therein to produce a trusted root CA certificate.

The Squid proxy is built as a container which will be served by a Linux host - any of the popular distros should do providing you can join it to your Active Directory domain.

* A certificate authority is required to make browsers on the network trust https connections after they have been peeked by Squid.
* Kerberos is required if you want to capture user information at the proxy.


## SSL Bumping setup

Given that nearly everything on the web now is HTTPS, it is necessary to effectively perform a man-in-the-middle on all requests passing though the proxy. In simplistic terms, The SSL negotiation goes like this

1. Client issues CONNECT request, giving only the target host name.
1. SSL negotiation is completed, securing the connection.
1. Browser now requests the full path to the target object.

In order to get the URL at step 3 above, we need to intercept the encrypted traffic using an additional certificate. Whilst we can use a self-signed certificate for this purpose, browsers will detect this has happened and present a warning to the user, and in most cases will block access to the target site. Using a self-signed cert would require you to install this individually on every browser on the LAN to make it be trusted.

The way we manage this transparently in Squid is to recreate the cerficate chain to the target site to make it once again appear to have come from a trusted CA. Therefore, you need a Certificate Authority on your network that applications will trust. If running Windows Active Directory domain, then you have one - refer to Microsoft documentation to create a CA.

In order to get Squid to rebuild the certificate chain, we need to export the root certificate for your CA along with its private key into a PEM format file to give to Squid which will look something like this

```
-----BEGIN PRIVATE KEY-----
MIIEvgIBADAEXAMPLE
-----END PRIVATE KEY-----
-----BEGIN CERTIFICATE-----
MIIDezCCAmOEXAMPLE
-----END CERTIFICATE-----
```

To export the CA cert and key in Windows, run the Certification Authority MMC snap-in and select backup. In the backup wizard select Private Key and Certificate. A PKCS#12 file will be created in the backup directory. Use `openssl` at the command line to convert this to PEM.

To enable the feature in Squid, the following is required in `squid.conf`. We adorn the `http_port` directive that sets up squid's listener with `ssl-bump` modifier and the cert details and enable bumping with the directives that follow. Adjust paths and file names appropriately for your system ([reference](https://wiki.squid-cache.org/ConfigExamples/Intercept/SslBumpExplicit)). This is all done for you in the `squid.conf` provided in this repo

```
sslcrtd_program /usr/lib/squid/security_file_certgen -s /var/cache/squid/ssl_db -M 4MB
http_port 3128 ssl-bump cert=/etc/squid/cert/ca.pem generate-host-certificates=on dynamic_cert_mem_cache_size=4MB
acl step1 at_step SslBump1
ssl_bump peek step1
ssl_bump bump all
```

## Authentication

If you wish the proxy to track users/have rules based on users, then it is necessary to enable Kerberos support. For this, you'll need Active Directory authentication (or Samba AD on Linux) across your network.

On host machine

* Join the host machine to the domain (I used cockpit from a CentOS host)
* Create a keytab for Squid to use. If using Windows Active Directory, install `msktutil` from EPEL (RedHat family) and run `msktutil -u -s $(hostname) -s HTTP -k HTTP.keytab`. Note that if you generate the keytab using Windows utilities, there is a disagreement between Windows and Linux as to the encryption algorithm. Otherwise use Samba's keytab utility.
* Ensure port 3128 ingress is permitted by the host's firewall
* Run the container using `--network=host`, so that the container identifies as the host machine.

## Building the Container

Firstly, choose the blacklist you want to use (see Blacklists below). You'll need to inspect the contents of the tarball noting specific directories against which you will create rules. Set up your `pysguard` configuration. Copy the example to `pysguard.conf.yaml` in the same directory and adjust the rules accordingly. See also the [pysguard site](https://github.com/fireflycons/pysguard)

The Dockerfile has several arguments that are used to configure the runtime envionment.

Where paths are required, these are relative to the location of `Dockerfile` and must be within the build context (i.e. at the same level or below `Dockerfile`)

| Argument         | Required    | Value|
|------------------|-------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| CA_CERT          | Yes         | Path to CA root certificate PEM file. SSL bumping (see below) is required for this setup to be of any practical use.|
| BLACKLIST_URL    | Yes         | URL of SQuidGuard format blacklist to initialise `pysguard`. See Blacklists below.
| KRB5_REALM       | No          | Kerberos realm for user lookups. If not present, then Squid will not perform user lookups (all requests will be anonymous).|
| KRB5_KEYTAB      | Conditional | Path to keytab file for Squid to use. Required if KRB5_REALM is present (see Authentication below).|
| KRB5_KDC         | Conditional | Comma separated list of KDC servers (FQDN). Required if KRB5_REALM is present.|
| KRB5_ADMINSERVER | No          | If not present, first KDC server is assumed.|
| NTP_SERVERS      | Conditional | Comma separated list of NTP servers. If this is absent and KRB5_KDC is set, then the KDCs are assumed to be NTP servers, else this must have a value. |

Now create a directory `private-assets` in the root of where you cloned this repo. In here place the CA certificate PEM file and if using Kerberos, the keytab file you have generated.

Now use a script similar to this to build and run the container

```bash
#!/bin/sh
docker build --build-arg CA_CERT=./private-assets/my-ca-cert.pem \
             --build-arg KRB5_KEYTAB=./private-assets/my.keytab \
             --build-arg KRB5_REALM=MYREALM.COM \
             --build-arg KRB5_KDC=dc1.myrealm.coom,dc2.myrealm.com \
             --build-arg BLACKLIST_URL=ftp://ftp.ut-capitole.fr/pub/reseau/cache/squidguard_contrib/blacklists.tar.gz \
             -t dockeralpinesquid .

if [ $? -eq 0 ]
then
    echo "Launching container..."
    docker run -d --network=host -v /var/log/squid:/var/log/squid dockeralpinesquid
fi
```

## Client Configuration

On a Windows network with Active Directory, place the users you wish to go though the proxy in their own OU. Now configure a GPO on this OU to force browsers to use the proxy.

An example GPO configuation can be found [here](https://theitbros.com/config-internet-explorer-11-proxy-settings-gpo/).

## Blacklists

Links to compatible blacklists can be found [here](http://www.squidguard.org/blacklists.html). Locate the `.tar.gz` or `.tgz` file that contains the blacklist and pass the full URL of this to the `BLACKLIST_URL` docker build argument

## Acknowledgements

This repo contains a slightly modified version of negotiate_kerberos_auth by Markus Moeller. See [here](./negotiate-kerberos-auth/README.md) for details.
