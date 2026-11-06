import unittest
from convert import convert_rule


class ConversionTests(unittest.TestCase):
    def test_domain_semantics_unchanged(self):
        self.assertEqual(convert_rule('DOMAIN,example.com')[1], 'DOMAIN,example.com')
        self.assertEqual(convert_rule('DOMAIN-SUFFIX,example.com')[1], 'DOMAIN-SUFFIX,example.com')

    def test_no_resolve_is_not_duplicated(self):
        self.assertEqual(convert_rule('IP-CIDR,1.2.3.4/32,no-resolve')[1], 'IP-CIDR,1.2.3.4/32,no-resolve')

    def test_regex_preserved(self):
        pattern = r'^server-\d{1,3}\.example\.com$'
        self.assertEqual(convert_rule('DOMAIN-REGEX,' + pattern), ('DOMAIN-REGEX', pattern))

    def test_unknown_or_malformed_rules_fail(self):
        for rule in ('UNKNOWN,example.com', 'DOMAIN,example.com,DIRECT', 'IP-CIDR,bad', 'IP-ASN,no', 'DOMAIN,bad domain', 'DOMAIN,example.com\nDOMAIN,other'):
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                convert_rule(rule)


if __name__ == '__main__':
    unittest.main()
