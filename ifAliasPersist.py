import sys

from bisect import bisect

from pyroute2 import NDB

BASE_OID = '.1.3.6.1.2.1.31.1.1.1.18'


def oid_to_ifidx(oid):
    """
    Convert an OID string to an interface index while checking it for conformity

    The OID has to be rooted at the BASE_OID, otherwise a ValueError is thrown.
    A ValueError is also thrown when the last portion of the OID is not numeric.

    If only the BASE_OID is passed, 0 is returned.

    >>> oid_to_ifidx('.1.3.6.1.2.1.31.1.1.1.18')
    0
    >>> oid_to_ifidx('.1.3.6.1.2.1.31.1.1.1.18.123')
    123
    >>> oid_to_ifidx('.1.3.6.1.2.1.31.1.1.1.18.a')
    Traceback (most recent call last):
        ...
    ValueError: invalid literal for int() with base 10: 'a'
    >>> oid_to_ifidx('.1.3.6.1.2.1')
    Traceback (most recent call last):
        ...
    ValueError: OID does not start with .1.3.6.1.2.1.31.1.1.1.18.: '.1.3.6.1.2.1'
    """
    if oid == BASE_OID:
        return 0

    if not oid.startswith(BASE_OID + '.'):
        raise ValueError(
            "OID does not start with %s: %r" % (BASE_OID + '.', oid)
        )

    # raises ValueError if not a number
    return int(oid[len(BASE_OID) + 1:])


def get_next_ifidx(ndb, ifidx):
    sorted_ifidxs = sorted(iface['index'] for iface in ndb.interfaces)
    return sorted_ifidxs[bisect(sorted_ifidxs, ifidx)]


def main():
    with NDB() as ndb:
        for cmd in sys.stdin:
            cmd = cmd.rstrip()
            if cmd == 'PING':
                print('PONG')
                continue

            oid = sys.stdin.readline().rstrip()
            if cmd == 'set':
                # The next line contains the value that we would be supposed to
                # set - if we supported writes
                sys.stdin.readline()
                print('not-writable')
                continue

            try:
                ifidx = oid_to_ifidx(oid)
                if cmd == 'getnext':
                    ifidx = get_next_ifidx(ndb, ifidx)
                ifalias = ndb.interfaces[{'index': ifidx}]['ifalias'] or ''
                print(f'{BASE_OID}.{ifidx}\nstring\n{ifalias}')
            except (ValueError, IndexError, KeyError):
                print('NONE')


if __name__ == '__main__':
    main()
