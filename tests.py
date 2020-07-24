import unittest
import doctest

from collections import namedtuple

import ifAliasPersist as main


DB = namedtuple('DB', ['interfaces'])


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(main))
    return tests


class TestSNMPCommandHandler(unittest.TestCase):
    ifaliases = {1: 'Loopback', 3: 'Production', 4: 'Internal'}

    def assertEmpty(self, it):
        with self.assertRaises(StopIteration):
            next(it)

    def setUp(self):
        self.db = DB({
            i: {'index': i, 'ifalias': v}
            for i, v in self.ifaliases.items()
        })
        self.handler = main.SNMPCommandHandler(self.db)

    @staticmethod
    def ifidx_to_oid(ifidx):
        return f'{main.BASE_OID}.{ifidx}'

    def ifidx_to_output(self, idx):
        return '\n'.join((self.ifidx_to_oid(idx), 'string', self.ifaliases[idx]))

    def common_handler_test(self, cmd, args, response):
        args = iter(args)
        self.assertEqual(self.handler.handle(cmd, args), response)
        self.assertEmpty(args)

    def test_ping(self):
        self.common_handler_test('PING', [], 'PONG')

    def test_set(self):
        self.common_handler_test(
            'set',
            [self.ifidx_to_oid(1), 'Test'],
            'not-writable'
        )

    def test_get(self):
        oid = self.ifidx_to_oid(1)
        self.common_handler_test(
            'get',
            [oid],
            self.ifidx_to_output(1)
        )

    def test_getnext(self):
        self.common_handler_test(
            'getnext',
            [self.ifidx_to_oid(3)],
            self.ifidx_to_output(4)
        )

    def test_getnext_first(self):
        self.common_handler_test(
            'getnext',
            [main.BASE_OID],
            self.ifidx_to_output(1)
        )

    def test_getnext_last(self):
        self.common_handler_test(
            'getnext',
            [self.ifidx_to_oid(max(self.ifaliases.keys()))],
            'NONE'
        )

    def test_rstrip(self):
        self.common_handler_test(
            'get',
            [self.ifidx_to_oid(1) + '\n'],
            self.ifidx_to_output(1)
        )

    def test_unknown_command(self):
        with self.assertRaises(RuntimeError):
            self.handler.handle('invalid', [])


if __name__ == '__main__':
    unittest.main()
