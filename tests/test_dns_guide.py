import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import dns_guide as dg  # noqa: E402

G = {"business": "Test Roofing Ltd (DEMO)", "domain": "testroofing-demo.co.uk", "registrar": "123-reg",
     "records": [{"type": "A", "host": "@", "value": "203.0.113.10"},
                 {"type": "CNAME", "host": "www", "value": "hosting-target.net"}]}


class DnsGuide(unittest.TestCase):
    def test_builds_guide_with_records_and_email_warning(self):
        md = dg.build(G)
        self.assertIn("203.0.113.10", md)
        self.assertIn("Don't change nameservers", md)
        self.assertIn("MX or TXT", md)
        self.assertIn("screenshot", md)

    def test_refuses_mx_txt_ns(self):
        for t in ("MX", "TXT", "NS"):
            g = dict(G, records=[{"type": t, "host": "@", "value": "x.net"}])
            with self.assertRaises(dg.GuideError):
                dg.build(g)

    def test_refuses_placeholder_values(self):
        g = dict(G, records=[{"type": "A", "host": "@", "value": "{host_ip}"}])
        with self.assertRaises(dg.GuideError):
            dg.build(g)

    def test_refuses_other_hosts(self):
        g = dict(G, records=[{"type": "A", "host": "mail", "value": "203.0.113.10"}])
        with self.assertRaises(dg.GuideError):
            dg.build(g)

    def test_wix_flag(self):
        self.assertIn("tested before launch", dg.build(dict(G, registrar="Wix")))

    def test_html_escapes(self):
        self.assertNotIn("<script>", dg.to_html(dg.build(dict(G, business="<script>x</script>"))))


if __name__ == "__main__":
    unittest.main()
