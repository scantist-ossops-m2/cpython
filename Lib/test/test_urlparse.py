#! /usr/bin/env python

from test import test_support
import sys
import unicodedata
import unittest
import urlparse

RFC1808_BASE = "http://a/b/c/d;p?q#f"
RFC2396_BASE = "http://a/b/c/d;p?q"
RFC3986_BASE = 'http://a/b/c/d;p?q'
SIMPLE_BASE  = 'http://a/b/c/d'

# A list of test cases.  Each test case is a a two-tuple that contains
# a string with the query and a dictionary with the expected result.

parse_qsl_test_cases = [
    ("", []),
    ("&", []),
    ("&&", []),
    ("=", [('', '')]),
    ("=a", [('', 'a')]),
    ("a", [('a', '')]),
    ("a=", [('a', '')]),
    ("a=", [('a', '')]),
    ("&a=b", [('a', 'b')]),
    ("a=a+b&b=b+c", [('a', 'a b'), ('b', 'b c')]),
    ("a=1&a=2", [('a', '1'), ('a', '2')]),
]

class UrlParseTestCase(unittest.TestCase):

    def checkRoundtrips(self, url, parsed, split):
        result = urlparse.urlparse(url)
        self.assertEqual(result, parsed)
        t = (result.scheme, result.netloc, result.path,
             result.params, result.query, result.fragment)
        self.assertEqual(t, parsed)
        # put it back together and it should be the same
        result2 = urlparse.urlunparse(result)
        self.assertEqual(result2, url)
        self.assertEqual(result2, result.geturl())

        # the result of geturl() is a fixpoint; we can always parse it
        # again to get the same result:
        result3 = urlparse.urlparse(result.geturl())
        self.assertEqual(result3.geturl(), result.geturl())
        self.assertEqual(result3,          result)
        self.assertEqual(result3.scheme,   result.scheme)
        self.assertEqual(result3.netloc,   result.netloc)
        self.assertEqual(result3.path,     result.path)
        self.assertEqual(result3.params,   result.params)
        self.assertEqual(result3.query,    result.query)
        self.assertEqual(result3.fragment, result.fragment)
        self.assertEqual(result3.username, result.username)
        self.assertEqual(result3.password, result.password)
        self.assertEqual(result3.hostname, result.hostname)
        self.assertEqual(result3.port,     result.port)

        # check the roundtrip using urlsplit() as well
        result = urlparse.urlsplit(url)
        self.assertEqual(result, split)
        t = (result.scheme, result.netloc, result.path,
             result.query, result.fragment)
        self.assertEqual(t, split)
        result2 = urlparse.urlunsplit(result)
        self.assertEqual(result2, url)
        self.assertEqual(result2, result.geturl())

        # check the fixpoint property of re-parsing the result of geturl()
        result3 = urlparse.urlsplit(result.geturl())
        self.assertEqual(result3.geturl(), result.geturl())
        self.assertEqual(result3,          result)
        self.assertEqual(result3.scheme,   result.scheme)
        self.assertEqual(result3.netloc,   result.netloc)
        self.assertEqual(result3.path,     result.path)
        self.assertEqual(result3.query,    result.query)
        self.assertEqual(result3.fragment, result.fragment)
        self.assertEqual(result3.username, result.username)
        self.assertEqual(result3.password, result.password)
        self.assertEqual(result3.hostname, result.hostname)
        self.assertEqual(result3.port,     result.port)

    def test_qsl(self):
        for orig, expect in parse_qsl_test_cases:
            result = urlparse.parse_qsl(orig, keep_blank_values=True)
            self.assertEqual(result, expect, "Error parsing %s" % repr(orig))

    def test_roundtrips(self):
        testcases = [
            ('file:///tmp/junk.txt',
             ('file', '', '/tmp/junk.txt', '', '', ''),
             ('file', '', '/tmp/junk.txt', '', '')),
            ('imap://mail.python.org/mbox1',
             ('imap', 'mail.python.org', '/mbox1', '', '', ''),
             ('imap', 'mail.python.org', '/mbox1', '', '')),
            ('mms://wms.sys.hinet.net/cts/Drama/09006251100.asf',
             ('mms', 'wms.sys.hinet.net', '/cts/Drama/09006251100.asf',
              '', '', ''),
             ('mms', 'wms.sys.hinet.net', '/cts/Drama/09006251100.asf',
              '', '')),
            ('nfs://server/path/to/file.txt',
             ('nfs', 'server', '/path/to/file.txt',  '', '', ''),
             ('nfs', 'server', '/path/to/file.txt', '', '')),
            ('svn+ssh://svn.zope.org/repos/main/ZConfig/trunk/',
             ('svn+ssh', 'svn.zope.org', '/repos/main/ZConfig/trunk/',
              '', '', ''),
             ('svn+ssh', 'svn.zope.org', '/repos/main/ZConfig/trunk/',
              '', '')),
            ('git+ssh://git@github.com/user/project.git',
            ('git+ssh', 'git@github.com','/user/project.git',
             '','',''),
            ('git+ssh', 'git@github.com','/user/project.git',
             '', ''))
            ]
        for url, parsed, split in testcases:
            self.checkRoundtrips(url, parsed, split)

    def test_http_roundtrips(self):
        # urlparse.urlsplit treats 'http:' as an optimized special case,
        # so we test both 'http:' and 'https:' in all the following.
        # Three cheers for white box knowledge!
        testcases = [
            ('://www.python.org',
             ('www.python.org', '', '', '', ''),
             ('www.python.org', '', '', '')),
            ('://www.python.org#abc',
             ('www.python.org', '', '', '', 'abc'),
             ('www.python.org', '', '', 'abc')),
            ('://www.python.org?q=abc',
             ('www.python.org', '', '', 'q=abc', ''),
             ('www.python.org', '', 'q=abc', '')),
            ('://www.python.org/#abc',
             ('www.python.org', '/', '', '', 'abc'),
             ('www.python.org', '/', '', 'abc')),
            ('://a/b/c/d;p?q#f',
             ('a', '/b/c/d', 'p', 'q', 'f'),
             ('a', '/b/c/d;p', 'q', 'f')),
            ]
        for scheme in ('http', 'https'):
            for url, parsed, split in testcases:
                url = scheme + url
                parsed = (scheme,) + parsed
                split = (scheme,) + split
                self.checkRoundtrips(url, parsed, split)

    def checkJoin(self, base, relurl, expected):
        self.assertEqual(urlparse.urljoin(base, relurl), expected,
                         (base, relurl, expected))

    def test_unparse_parse(self):
        for u in ['Python', './Python','x-newscheme://foo.com/stuff','x://y','x:/y','x:/','/',]:
            self.assertEqual(urlparse.urlunsplit(urlparse.urlsplit(u)), u)
            self.assertEqual(urlparse.urlunparse(urlparse.urlparse(u)), u)

    def test_RFC1808(self):
        # "normal" cases from RFC 1808:
        self.checkJoin(RFC1808_BASE, 'g:h', 'g:h')
        self.checkJoin(RFC1808_BASE, 'g', 'http://a/b/c/g')
        self.checkJoin(RFC1808_BASE, './g', 'http://a/b/c/g')
        self.checkJoin(RFC1808_BASE, 'g/', 'http://a/b/c/g/')
        self.checkJoin(RFC1808_BASE, '/g', 'http://a/g')
        self.checkJoin(RFC1808_BASE, '//g', 'http://g')
        self.checkJoin(RFC1808_BASE, 'g?y', 'http://a/b/c/g?y')
        self.checkJoin(RFC1808_BASE, 'g?y/./x', 'http://a/b/c/g?y/./x')
        self.checkJoin(RFC1808_BASE, '#s', 'http://a/b/c/d;p?q#s')
        self.checkJoin(RFC1808_BASE, 'g#s', 'http://a/b/c/g#s')
        self.checkJoin(RFC1808_BASE, 'g#s/./x', 'http://a/b/c/g#s/./x')
        self.checkJoin(RFC1808_BASE, 'g?y#s', 'http://a/b/c/g?y#s')
        self.checkJoin(RFC1808_BASE, 'g;x', 'http://a/b/c/g;x')
        self.checkJoin(RFC1808_BASE, 'g;x?y#s', 'http://a/b/c/g;x?y#s')
        self.checkJoin(RFC1808_BASE, '.', 'http://a/b/c/')
        self.checkJoin(RFC1808_BASE, './', 'http://a/b/c/')
        self.checkJoin(RFC1808_BASE, '..', 'http://a/b/')
        self.checkJoin(RFC1808_BASE, '../', 'http://a/b/')
        self.checkJoin(RFC1808_BASE, '../g', 'http://a/b/g')
        self.checkJoin(RFC1808_BASE, '../..', 'http://a/')
        self.checkJoin(RFC1808_BASE, '../../', 'http://a/')
        self.checkJoin(RFC1808_BASE, '../../g', 'http://a/g')

        # "abnormal" cases from RFC 1808:
        self.checkJoin(RFC1808_BASE, '', 'http://a/b/c/d;p?q#f')
        self.checkJoin(RFC1808_BASE, '../../../g', 'http://a/../g')
        self.checkJoin(RFC1808_BASE, '../../../../g', 'http://a/../../g')
        self.checkJoin(RFC1808_BASE, '/./g', 'http://a/./g')
        self.checkJoin(RFC1808_BASE, '/../g', 'http://a/../g')
        self.checkJoin(RFC1808_BASE, 'g.', 'http://a/b/c/g.')
        self.checkJoin(RFC1808_BASE, '.g', 'http://a/b/c/.g')
        self.checkJoin(RFC1808_BASE, 'g..', 'http://a/b/c/g..')
        self.checkJoin(RFC1808_BASE, '..g', 'http://a/b/c/..g')
        self.checkJoin(RFC1808_BASE, './../g', 'http://a/b/g')
        self.checkJoin(RFC1808_BASE, './g/.', 'http://a/b/c/g/')
        self.checkJoin(RFC1808_BASE, 'g/./h', 'http://a/b/c/g/h')
        self.checkJoin(RFC1808_BASE, 'g/../h', 'http://a/b/c/h')

        # RFC 1808 and RFC 1630 disagree on these (according to RFC 1808),
        # so we'll not actually run these tests (which expect 1808 behavior).
        #self.checkJoin(RFC1808_BASE, 'http:g', 'http:g')
        #self.checkJoin(RFC1808_BASE, 'http:', 'http:')

    def test_RFC2368(self):
        # Issue 11467: path that starts with a number is not parsed correctly
        self.assertEqual(urlparse.urlparse('mailto:1337@example.org'),
                ('mailto', '', '1337@example.org', '', '', ''))

    def test_RFC2396(self):
        # cases from RFC 2396
        self.checkJoin(RFC2396_BASE, 'g:h', 'g:h')
        self.checkJoin(RFC2396_BASE, 'g', 'http://a/b/c/g')
        self.checkJoin(RFC2396_BASE, './g', 'http://a/b/c/g')
        self.checkJoin(RFC2396_BASE, 'g/', 'http://a/b/c/g/')
        self.checkJoin(RFC2396_BASE, '/g', 'http://a/g')
        self.checkJoin(RFC2396_BASE, '//g', 'http://g')
        self.checkJoin(RFC2396_BASE, 'g?y', 'http://a/b/c/g?y')
        self.checkJoin(RFC2396_BASE, '#s', 'http://a/b/c/d;p?q#s')
        self.checkJoin(RFC2396_BASE, 'g#s', 'http://a/b/c/g#s')
        self.checkJoin(RFC2396_BASE, 'g?y#s', 'http://a/b/c/g?y#s')
        self.checkJoin(RFC2396_BASE, 'g;x', 'http://a/b/c/g;x')
        self.checkJoin(RFC2396_BASE, 'g;x?y#s', 'http://a/b/c/g;x?y#s')
        self.checkJoin(RFC2396_BASE, '.', 'http://a/b/c/')
        self.checkJoin(RFC2396_BASE, './', 'http://a/b/c/')
        self.checkJoin(RFC2396_BASE, '..', 'http://a/b/')
        self.checkJoin(RFC2396_BASE, '../', 'http://a/b/')
        self.checkJoin(RFC2396_BASE, '../g', 'http://a/b/g')
        self.checkJoin(RFC2396_BASE, '../..', 'http://a/')
        self.checkJoin(RFC2396_BASE, '../../', 'http://a/')
        self.checkJoin(RFC2396_BASE, '../../g', 'http://a/g')
        self.checkJoin(RFC2396_BASE, '', RFC2396_BASE)
        self.checkJoin(RFC2396_BASE, '../../../g', 'http://a/../g')
        self.checkJoin(RFC2396_BASE, '../../../../g', 'http://a/../../g')
        self.checkJoin(RFC2396_BASE, '/./g', 'http://a/./g')
        self.checkJoin(RFC2396_BASE, '/../g', 'http://a/../g')
        self.checkJoin(RFC2396_BASE, 'g.', 'http://a/b/c/g.')
        self.checkJoin(RFC2396_BASE, '.g', 'http://a/b/c/.g')
        self.checkJoin(RFC2396_BASE, 'g..', 'http://a/b/c/g..')
        self.checkJoin(RFC2396_BASE, '..g', 'http://a/b/c/..g')
        self.checkJoin(RFC2396_BASE, './../g', 'http://a/b/g')
        self.checkJoin(RFC2396_BASE, './g/.', 'http://a/b/c/g/')
        self.checkJoin(RFC2396_BASE, 'g/./h', 'http://a/b/c/g/h')
        self.checkJoin(RFC2396_BASE, 'g/../h', 'http://a/b/c/h')
        self.checkJoin(RFC2396_BASE, 'g;x=1/./y', 'http://a/b/c/g;x=1/y')
        self.checkJoin(RFC2396_BASE, 'g;x=1/../y', 'http://a/b/c/y')
        self.checkJoin(RFC2396_BASE, 'g?y/./x', 'http://a/b/c/g?y/./x')
        self.checkJoin(RFC2396_BASE, 'g?y/../x', 'http://a/b/c/g?y/../x')
        self.checkJoin(RFC2396_BASE, 'g#s/./x', 'http://a/b/c/g#s/./x')
        self.checkJoin(RFC2396_BASE, 'g#s/../x', 'http://a/b/c/g#s/../x')

    def test_RFC3986(self):
        # Test cases from RFC3986
        self.checkJoin(RFC3986_BASE, '?y','http://a/b/c/d;p?y')
        self.checkJoin(RFC2396_BASE, ';x', 'http://a/b/c/;x')
        self.checkJoin(RFC3986_BASE, 'g:h','g:h')
        self.checkJoin(RFC3986_BASE, 'g','http://a/b/c/g')
        self.checkJoin(RFC3986_BASE, './g','http://a/b/c/g')
        self.checkJoin(RFC3986_BASE, 'g/','http://a/b/c/g/')
        self.checkJoin(RFC3986_BASE, '/g','http://a/g')
        self.checkJoin(RFC3986_BASE, '//g','http://g')
        self.checkJoin(RFC3986_BASE, '?y','http://a/b/c/d;p?y')
        self.checkJoin(RFC3986_BASE, 'g?y','http://a/b/c/g?y')
        self.checkJoin(RFC3986_BASE, '#s','http://a/b/c/d;p?q#s')
        self.checkJoin(RFC3986_BASE, 'g#s','http://a/b/c/g#s')
        self.checkJoin(RFC3986_BASE, 'g?y#s','http://a/b/c/g?y#s')
        self.checkJoin(RFC3986_BASE, ';x','http://a/b/c/;x')
        self.checkJoin(RFC3986_BASE, 'g;x','http://a/b/c/g;x')
        self.checkJoin(RFC3986_BASE, 'g;x?y#s','http://a/b/c/g;x?y#s')
        self.checkJoin(RFC3986_BASE, '','http://a/b/c/d;p?q')
        self.checkJoin(RFC3986_BASE, '.','http://a/b/c/')
        self.checkJoin(RFC3986_BASE, './','http://a/b/c/')
        self.checkJoin(RFC3986_BASE, '..','http://a/b/')
        self.checkJoin(RFC3986_BASE, '../','http://a/b/')
        self.checkJoin(RFC3986_BASE, '../g','http://a/b/g')
        self.checkJoin(RFC3986_BASE, '../..','http://a/')
        self.checkJoin(RFC3986_BASE, '../../','http://a/')
        self.checkJoin(RFC3986_BASE, '../../g','http://a/g')

        #Abnormal Examples

        # The 'abnormal scenarios' are incompatible with RFC2986 parsing
        # Tests are here for reference.

        #self.checkJoin(RFC3986_BASE, '../../../g','http://a/g')
        #self.checkJoin(RFC3986_BASE, '../../../../g','http://a/g')
        #self.checkJoin(RFC3986_BASE, '/./g','http://a/g')
        #self.checkJoin(RFC3986_BASE, '/../g','http://a/g')

        self.checkJoin(RFC3986_BASE, 'g.','http://a/b/c/g.')
        self.checkJoin(RFC3986_BASE, '.g','http://a/b/c/.g')
        self.checkJoin(RFC3986_BASE, 'g..','http://a/b/c/g..')
        self.checkJoin(RFC3986_BASE, '..g','http://a/b/c/..g')
        self.checkJoin(RFC3986_BASE, './../g','http://a/b/g')
        self.checkJoin(RFC3986_BASE, './g/.','http://a/b/c/g/')
        self.checkJoin(RFC3986_BASE, 'g/./h','http://a/b/c/g/h')
        self.checkJoin(RFC3986_BASE, 'g/../h','http://a/b/c/h')
        self.checkJoin(RFC3986_BASE, 'g;x=1/./y','http://a/b/c/g;x=1/y')
        self.checkJoin(RFC3986_BASE, 'g;x=1/../y','http://a/b/c/y')
        self.checkJoin(RFC3986_BASE, 'g?y/./x','http://a/b/c/g?y/./x')
        self.checkJoin(RFC3986_BASE, 'g?y/../x','http://a/b/c/g?y/../x')
        self.checkJoin(RFC3986_BASE, 'g#s/./x','http://a/b/c/g#s/./x')
        self.checkJoin(RFC3986_BASE, 'g#s/../x','http://a/b/c/g#s/../x')
        #self.checkJoin(RFC3986_BASE, 'http:g','http:g') # strict parser
        self.checkJoin(RFC3986_BASE, 'http:g','http://a/b/c/g') # relaxed parser

        # Test for issue9721
        self.checkJoin('http://a/b/c/de', ';x','http://a/b/c/;x')

    def test_urljoins(self):
        self.checkJoin(SIMPLE_BASE, 'g:h','g:h')
        self.checkJoin(SIMPLE_BASE, 'http:g','http://a/b/c/g')
        self.checkJoin(SIMPLE_BASE, 'http:','http://a/b/c/d')
        self.checkJoin(SIMPLE_BASE, 'g','http://a/b/c/g')
        self.checkJoin(SIMPLE_BASE, './g','http://a/b/c/g')
        self.checkJoin(SIMPLE_BASE, 'g/','http://a/b/c/g/')
        self.checkJoin(SIMPLE_BASE, '/g','http://a/g')
        self.checkJoin(SIMPLE_BASE, '//g','http://g')
        self.checkJoin(SIMPLE_BASE, '?y','http://a/b/c/d?y')
        self.checkJoin(SIMPLE_BASE, 'g?y','http://a/b/c/g?y')
        self.checkJoin(SIMPLE_BASE, 'g?y/./x','http://a/b/c/g?y/./x')
        self.checkJoin(SIMPLE_BASE, '.','http://a/b/c/')
        self.checkJoin(SIMPLE_BASE, './','http://a/b/c/')
        self.checkJoin(SIMPLE_BASE, '..','http://a/b/')
        self.checkJoin(SIMPLE_BASE, '../','http://a/b/')
        self.checkJoin(SIMPLE_BASE, '../g','http://a/b/g')
        self.checkJoin(SIMPLE_BASE, '../..','http://a/')
        self.checkJoin(SIMPLE_BASE, '../../g','http://a/g')
        self.checkJoin(SIMPLE_BASE, '../../../g','http://a/../g')
        self.checkJoin(SIMPLE_BASE, './../g','http://a/b/g')
        self.checkJoin(SIMPLE_BASE, './g/.','http://a/b/c/g/')
        self.checkJoin(SIMPLE_BASE, '/./g','http://a/./g')
        self.checkJoin(SIMPLE_BASE, 'g/./h','http://a/b/c/g/h')
        self.checkJoin(SIMPLE_BASE, 'g/../h','http://a/b/c/h')
        self.checkJoin(SIMPLE_BASE, 'http:g','http://a/b/c/g')
        self.checkJoin(SIMPLE_BASE, 'http:','http://a/b/c/d')
        self.checkJoin(SIMPLE_BASE, 'http:?y','http://a/b/c/d?y')
        self.checkJoin(SIMPLE_BASE, 'http:g?y','http://a/b/c/g?y')
        self.checkJoin(SIMPLE_BASE, 'http:g?y/./x','http://a/b/c/g?y/./x')

    def test_RFC2732(self):
        for url, hostname, port in [
            ('http://Test.python.org:5432/foo/', 'test.python.org', 5432),
            ('http://12.34.56.78:5432/foo/', '12.34.56.78', 5432),
            ('http://[::1]:5432/foo/', '::1', 5432),
            ('http://[dead:beef::1]:5432/foo/', 'dead:beef::1', 5432),
            ('http://[dead:beef::]:5432/foo/', 'dead:beef::', 5432),
            ('http://[dead:beef:cafe:5417:affe:8FA3:deaf:feed]:5432/foo/',
             'dead:beef:cafe:5417:affe:8fa3:deaf:feed', 5432),
            ('http://[::12.34.56.78]:5432/foo/', '::12.34.56.78', 5432),
            ('http://[::ffff:12.34.56.78]:5432/foo/',
             '::ffff:12.34.56.78', 5432),
            ('http://Test.python.org/foo/', 'test.python.org', None),
            ('http://12.34.56.78/foo/', '12.34.56.78', None),
            ('http://[::1]/foo/', '::1', None),
            ('http://[dead:beef::1]/foo/', 'dead:beef::1', None),
            ('http://[dead:beef::]/foo/', 'dead:beef::', None),
            ('http://[dead:beef:cafe:5417:affe:8FA3:deaf:feed]/foo/',
             'dead:beef:cafe:5417:affe:8fa3:deaf:feed', None),
            ('http://[::12.34.56.78]/foo/', '::12.34.56.78', None),
            ('http://[::ffff:12.34.56.78]/foo/',
             '::ffff:12.34.56.78', None),
            ]:
            urlparsed = urlparse.urlparse(url)
            self.assertEqual((urlparsed.hostname, urlparsed.port) , (hostname, port))

        for invalid_url in [
                'http://::12.34.56.78]/',
                'http://[::1/foo/',
                'ftp://[::1/foo/bad]/bad',
                'http://[::1/foo/bad]/bad',
                'http://[::ffff:12.34.56.78']:
            self.assertRaises(ValueError, urlparse.urlparse, invalid_url)

    def test_urldefrag(self):
        for url, defrag, frag in [
            ('http://python.org#frag', 'http://python.org', 'frag'),
            ('http://python.org', 'http://python.org', ''),
            ('http://python.org/#frag', 'http://python.org/', 'frag'),
            ('http://python.org/', 'http://python.org/', ''),
            ('http://python.org/?q#frag', 'http://python.org/?q', 'frag'),
            ('http://python.org/?q', 'http://python.org/?q', ''),
            ('http://python.org/p#frag', 'http://python.org/p', 'frag'),
            ('http://python.org/p?q', 'http://python.org/p?q', ''),
            (RFC1808_BASE, 'http://a/b/c/d;p?q', 'f'),
            (RFC2396_BASE, 'http://a/b/c/d;p?q', ''),
            ]:
            self.assertEqual(urlparse.urldefrag(url), (defrag, frag))

    def test_urlsplit_attributes(self):
        url = "HTTP://WWW.PYTHON.ORG/doc/#frag"
        p = urlparse.urlsplit(url)
        self.assertEqual(p.scheme, "http")
        self.assertEqual(p.netloc, "WWW.PYTHON.ORG")
        self.assertEqual(p.path, "/doc/")
        self.assertEqual(p.query, "")
        self.assertEqual(p.fragment, "frag")
        self.assertEqual(p.username, None)
        self.assertEqual(p.password, None)
        self.assertEqual(p.hostname, "www.python.org")
        self.assertEqual(p.port, None)
        # geturl() won't return exactly the original URL in this case
        # since the scheme is always case-normalized
        #self.assertEqual(p.geturl(), url)

        url = "http://User:Pass@www.python.org:080/doc/?query=yes#frag"
        p = urlparse.urlsplit(url)
        self.assertEqual(p.scheme, "http")
        self.assertEqual(p.netloc, "User:Pass@www.python.org:080")
        self.assertEqual(p.path, "/doc/")
        self.assertEqual(p.query, "query=yes")
        self.assertEqual(p.fragment, "frag")
        self.assertEqual(p.username, "User")
        self.assertEqual(p.password, "Pass")
        self.assertEqual(p.hostname, "www.python.org")
        self.assertEqual(p.port, 80)
        self.assertEqual(p.geturl(), url)

        # Addressing issue1698, which suggests Username can contain
        # "@" characters.  Though not RFC compliant, many ftp sites allow
        # and request email addresses as usernames.

        url = "http://User@example.com:Pass@www.python.org:080/doc/?query=yes#frag"
        p = urlparse.urlsplit(url)
        self.assertEqual(p.scheme, "http")
        self.assertEqual(p.netloc, "User@example.com:Pass@www.python.org:080")
        self.assertEqual(p.path, "/doc/")
        self.assertEqual(p.query, "query=yes")
        self.assertEqual(p.fragment, "frag")
        self.assertEqual(p.username, "User@example.com")
        self.assertEqual(p.password, "Pass")
        self.assertEqual(p.hostname, "www.python.org")
        self.assertEqual(p.port, 80)
        self.assertEqual(p.geturl(), url)


    def test_attributes_bad_port(self):
        """Check handling of non-integer ports."""
        p = urlparse.urlsplit("http://www.example.net:foo")
        self.assertEqual(p.netloc, "www.example.net:foo")
        self.assertRaises(ValueError, lambda: p.port)

        p = urlparse.urlparse("http://www.example.net:foo")
        self.assertEqual(p.netloc, "www.example.net:foo")
        self.assertRaises(ValueError, lambda: p.port)

    def test_attributes_without_netloc(self):
        # This example is straight from RFC 3261.  It looks like it
        # should allow the username, hostname, and port to be filled
        # in, but doesn't.  Since it's a URI and doesn't use the
        # scheme://netloc syntax, the netloc and related attributes
        # should be left empty.
        uri = "sip:alice@atlanta.com;maddr=239.255.255.1;ttl=15"
        p = urlparse.urlsplit(uri)
        self.assertEqual(p.netloc, "")
        self.assertEqual(p.username, None)
        self.assertEqual(p.password, None)
        self.assertEqual(p.hostname, None)
        self.assertEqual(p.port, None)
        self.assertEqual(p.geturl(), uri)

        p = urlparse.urlparse(uri)
        self.assertEqual(p.netloc, "")
        self.assertEqual(p.username, None)
        self.assertEqual(p.password, None)
        self.assertEqual(p.hostname, None)
        self.assertEqual(p.port, None)
        self.assertEqual(p.geturl(), uri)

    def test_caching(self):
        # Test case for bug #1313119
        uri = "http://example.com/doc/"
        unicode_uri = unicode(uri)

        urlparse.urlparse(unicode_uri)
        p = urlparse.urlparse(uri)
        self.assertEqual(type(p.scheme), type(uri))
        self.assertEqual(type(p.hostname), type(uri))
        self.assertEqual(type(p.path), type(uri))

    def test_noslash(self):
        # Issue 1637: http://foo.com?query is legal
        self.assertEqual(urlparse.urlparse("http://example.com?blahblah=/foo"),
                         ('http', 'example.com', '', '', 'blahblah=/foo', ''))

    def test_anyscheme(self):
        # Issue 7904: s3://foo.com/stuff has netloc "foo.com".
        self.assertEqual(urlparse.urlparse("s3://foo.com/stuff"),
                         ('s3','foo.com','/stuff','','',''))
        self.assertEqual(urlparse.urlparse("x-newscheme://foo.com/stuff"),
                         ('x-newscheme','foo.com','/stuff','','',''))

    def test_withoutscheme(self):
        # Test urlparse without scheme
        # Issue 754016: urlparse goes wrong with IP:port without scheme
        # RFC 1808 specifies that netloc should start with //, urlparse expects
        # the same, otherwise it classifies the portion of url as path.
        self.assertEqual(urlparse.urlparse("path"),
                ('','','path','','',''))
        self.assertEqual(urlparse.urlparse("//www.python.org:80"),
                ('','www.python.org:80','','','',''))
        self.assertEqual(urlparse.urlparse("http://www.python.org:80"),
                ('http','www.python.org:80','','','',''))

    def test_portseparator(self):
        # Issue 754016 makes changes for port separator ':' from scheme separator
        self.assertEqual(urlparse.urlparse("path:80"),
                ('','','path:80','','',''))
        self.assertEqual(urlparse.urlparse("http:"),('http','','','','',''))
        self.assertEqual(urlparse.urlparse("https:"),('https','','','','',''))
        self.assertEqual(urlparse.urlparse("http://www.python.org:80"),
                ('http','www.python.org:80','','','',''))


    def test_urlsplit_normalization(self):
        # Certain characters should never occur in the netloc,
        # including under normalization.
        # Ensure that ALL of them are detected and cause an error
        illegal_chars = u'/:#?@'
        hex_chars = {'{:04X}'.format(ord(c)) for c in illegal_chars}
        denorm_chars = [
            c for c in map(unichr, range(128, sys.maxunicode))
            if (hex_chars & set(unicodedata.decomposition(c).split()))
            and c not in illegal_chars
        ]
        # Sanity check that we found at least one such character
        self.assertIn(u'\u2100', denorm_chars)
        self.assertIn(u'\uFF03', denorm_chars)

        for scheme in [u"http", u"https", u"ftp"]:
            for c in denorm_chars:
                url = u"{}://netloc{}false.netloc/path".format(scheme, c)
                print "Checking %r" % url
                with self.assertRaises(ValueError):
                    urlparse.urlsplit(url)

def test_main():
    test_support.run_unittest(UrlParseTestCase)

if __name__ == "__main__":
    test_main()
