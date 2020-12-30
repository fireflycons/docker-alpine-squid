#!/usr/bin/env python3
import argparse
import sys
import os

default_krb5_conf = '/etc/krb5.conf'
default_ntp_conf = '/etc/ntp.conf'
default_squid_conf = '/etc/squid/squid.conf'


def write_krb5_dict(f, d: dict, indent: int):
    for k, v in d.items():
        if isinstance(v, str):
            f.write(f'{" " * indent}{k} = {v}\n')
        elif isinstance(v, list):
            for v1 in v:
                f.write(f'{" " * indent}{k} = {v1}\n')
        elif isinstance(v, dict):
            f.write(f'{" " * indent}{k} = {{\n')
            write_krb5_dict(f, v, indent + 2)
            f.write(f'{" " * indent}}}\n')


def write_krb5_conf(conf: dict):
    indent = 2
    with open(default_krb5_conf, 'w') as f:
        for k,v in conf.items():
            f.write(f'[{k}]\n')
            write_krb5_dict(f, v, 2)

class SplitArgs(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, [v for v in values.split(',') if v])


parser = argparse.ArgumentParser()
#parser.add_argument('--lists', nargs='+', required=True)
parser.add_argument('--krb5-keytab', help='Path to kerberos keytab file', metavar='path', dest='keytab')
parser.add_argument('--krb5-realm', help='Kerberos realm', metavar='realm', dest='realm')
parser.add_argument('--krb5-kdc', help='FQDN of kerberos KDC server', metavar='kdc', dest='kdc', action=SplitArgs)
parser.add_argument('--krb5-adminserver', help='FQDN of kerberos admin server. If omitted, KDC is assumed', metavar='admin', dest='admin')
parser.add_argument('--ntp-servers', help='fqdn of NTP servers. KDCs assumed if omitted', dest='ntp', action=SplitArgs)
args = parser.parse_args()

# krb5.conf
if args.realm:
    # Check for keytab - must exist if we're doing kerberos
    if not args.keytab:
        sys.stderr.write('KRB_KEYTAB build argument must be specified if Kerberos support required\n')
        sys.exit(1)
    # Move keytab
    kt = os.path.join('/tmp/keytab', os.path.basename(args.keytab))
    os.rename(kt, '/etc/HTTP.keytab')
    os.chmod('/etc/HTTP.keytab', 0o0644)

    print('Writing krb5.conf')
    realm = args.realm.upper()
    domain = args.realm.lower()
    admin_server = args.admin if args.admin else args.kdc[0]
    krb5_conf = {
        'libdefaults': {
            'default_realm': realm,
            'dns_lookup_kdc': 'yes',
            'dns_lookup_realm': 'yes',
            'ticket_lifetime': '24h',
            'default_keytab_name': '/etc/krb5.keytab'
        },
        'realms': {
            realm: {
                'kdc': args.kdc,
                'admin_server': admin_server,
                'default_domain': domain
            }
        },
        'domain_realm': {
            f'.{domain}': realm,
            domain: realm
        }
    }

    write_krb5_conf(krb5_conf)
    os.chmod(default_krb5_conf, 0o0644)

else:
    # Modify squid.conf to comment out kerberos
    print('Disabling Kerberos support')
    in_krb_section = False
    with open(default_squid_conf, 'r') as infile:
        with open('/tmp/squid.conf', 'w') as outfile:
            line = infile.readline()
            while line:
                if line.startswith('#---BEGIN KERBEROS'):
                    in_krb_section = True
                elif line.startswith('#---END KERBEROS'):
                    in_krb_section = False
                elif in_krb_section:
                    line = f'# {line}'
                outfile.write(line)
                line = infile.readline()
    os.replace('/tmp/squid.conf', default_squid_conf)

# ntp.conf
if not args.ntp:
    if not args.kdc:
        sys.stderr.write('Cannot determine ntp time source\n')
        sys.exit(1)
    ntp_servers = args.kdc
else:
    ntp_servers = args.ntp

print('Writing ntp.conf')
with open(default_ntp_conf, 'w') as f:
    for s in ntp_servers:
        f.write(f'server {s}\n')

