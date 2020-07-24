#!/usr/bin/env python3

import sys

from bisect import bisect
from inspect import signature

try:
    from pyroute2 import NDB as DB
except ImportError:
    from pyroute2 import IPDB as DB

BASE_OID = '.1.3.6.1.2.1.31.1.1.1.18'


def oid_to_ifidx(oid):
    """
    Convert an OID string to an interface index

    The OID has to be rooted at the BASE_OID, otherwise a ValueError is thrown.
    A ValueError is also thrown when the last portion of the OID is not numeric
    (all other elements have to be numeric due to the check against BASE_OID)

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


def get_next_ifidx(ifidxs, ifidx):
    """
    Returns the next greater interface index

    The ifidx need not be an element of ifidxs, in which case the next bigger
    index is returned.

    If ifidx is the greates index, raises IndexError

    >>> get_next_ifidx([1, 1, 3], 1)
    3
    >>> get_next_ifidx([1, 3], 2)
    3
    >>> get_next_ifidx([1, 3], 3)
    Traceback (most recent call last):
        ...
    IndexError: list index out of range
    """
    sorted_ifidxs = sorted(ifidxs)
    return sorted_ifidxs[bisect(sorted_ifidxs, ifidx)]


class SNMPCommandHandler:
    def __init__(self, db):
        self.db = db

    def get_ifalias(self, ifidx):
        try:
            iface = self.db.interfaces[{'index': ifidx}]
        except TypeError:
            iface = self.db.interfaces[ifidx]
        ifalias = iface['ifalias'] or ''
        return f'{BASE_OID}.{ifidx}\nstring\n{ifalias}'

    def handle(self, cmd, args):
        """
        Call handle_{cmd} with the next elements from args as arguments

        For example if cmd is PING then handle_PING needs 0 arguments, hence
        args is not used at all and self.handle_PING() is called.

        If cmd is set then the next two elements from args (with .rstrip()
        called on them) are used as the two arguments to self.handle_set(...)
        """
        try:
            handler = getattr(self, f'handle_{cmd}')
        except AttributeError:
            raise RuntimeError("Unknown command: %s" % (cmd,))
        sig = signature(handler)
        args = iter(args)
        try:
            return handler(*(
                next(args).rstrip() for parameter in sig.parameters
            ))
        except (ValueError, IndexError, KeyError):
            return 'NONE'

    @staticmethod
    def handle_PING():
        return 'PONG'

    def handle_set(self, oid, value):
        return 'not-writable'

    def handle_get(self, oid):
        return self.get_ifalias(oid_to_ifidx(oid))

    def handle_getnext(self, oid):
        ifidx = get_next_ifidx(
            (iface['index'] for iface in self.db.interfaces.values()),
            oid_to_ifidx(oid),
        )
        return self.get_ifalias(ifidx)


def main():
    with DB() as db:
        handler = SNMPCommandHandler(db)
        for cmd in sys.stdin:
            print(handler.handle(cmd.rstrip(), sys.stdin), flush=True)


if __name__ == '__main__':
    main()
