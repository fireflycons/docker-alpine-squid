FROM alpine:latest as build

RUN set -ex \
    && apk add --update --no-cache \
        heimdal \
        alpine-sdk \
        heimdal-dev \
        git

# Build kerberos helpers
COPY negotiate-kerberos-auth /usr/local/src/negotiate-kerberos-auth
WORKDIR /usr/local/src/negotiate-kerberos-auth
RUN make

# Get latest stable pysguard
WORKDIR /usr/local/src
RUN git clone --depth 1 --branch latest https://github.com/fireflycons/pysguard.git

FROM alpine:latest

ARG CA_CERT
ARG BLACKLIST_URL
ARG KRB5_KEYTAB
ARG KRB5_REALM
ARG KRB5_KDC
ARG KRB5_ADMINSERVER
ARG NTP_SERVERS

RUN set -ex \
    && apk add --update --no-cache \
        curl \
        heimdal \
        nano \
        ntpsec \
        python3 \
        py3-pip \
        squid \
        tini \
    &&  pip install \
        pyyaml \
        ipcalc \
        indexedproperty \
        dnspython

WORKDIR /
COPY root /
COPY $CA_CERT /etc/squid/cert/ca.pem
COPY Dockerfile ${KRB5_KEYTAB}* /tmp/keytab/

COPY --from=build /usr/local/src/negotiate-kerberos-auth/negotiate_kerberos_auth \
                  /usr/local/src/negotiate-kerberos-auth/negotiate_kerberos_auth_test \
                  /usr/lib/squid/

COPY --from=build /usr/local/src/pysguard/src/pysguard.py /usr/lib/squid/

ENV KRB5_KTNAME=/etc/HTTP.keytab KRB5_CONFIG=/etc/krb5.conf

RUN chown squid:squid /etc/squid/cert/* \
    && chmod 644 /etc/squid/cert/*

WORKDIR /tmp

RUN chmod +x setup.py \
    && ./setup.py --krb5-realm "${KRB5_REALM}" \
                  --krb5-kdc "${KRB5_KDC}" \
                  --krb5-adminserver "${KRB5_ADMINSERVER}" \
                  --krb5-keytab "${KRB5_KEYTAB}" \
                  --ntp-servers "${NTP_SERVERS}"

WORKDIR /usr/bin
RUN ln -s python3.8 python

RUN squid -z -N \
    && /usr/lib/squid/security_file_certgen -c -s /var/cache/squid/ssl_db -M 4MB \
    && chown -R squid:squid /var/cache/squid/ssl_db

WORKDIR /var/lib/pysguard/db

RUN curl ${BLACKLIST_URL} --output blacklists.tar.gz \
    && tar -zxf blacklists.tar.gz \
    && rm -f blacklists.tar.gz \
    && mv blacklists/* . \
    && rmdir blacklists/ \
    && /usr/lib/squid/pysguard.py -C -c /etc/pysguard/pysguard.conf.yaml

#VOLUME /var/log/squid
EXPOSE 3128/tcp

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/docker-run.sh"]
