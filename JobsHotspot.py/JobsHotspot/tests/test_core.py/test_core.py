"""Credential boundaries and actual counter behaviour. Created by Jobs."""
import unittest
from jobs_hotspot.core import RateTracker, format_bytes, valid_credentials
from jobs_hotspot.models import Interface, Snapshot
from jobs_hotspot.i18n import CATALOG, LANGUAGES, ROWS


class CoreTests(unittest.TestCase):
    def test_utf8_ssid_and_ascii_password_boundaries(self):
        self.assertTrue(valid_credentials('热点', '12345678'))
        self.assertTrue(valid_credentials('a'*32, 'p'*63))
        for ssid,password in [('a'*33,'12345678'),('界'*11,'12345678'),('  ','12345678'),
                ('x\n','12345678'),('x','short'),('x','p'*64),('x','密码12345678')]:
            self.assertFalse(valid_credentials(ssid,password))

    def test_rate_priming_unknown_reset_and_replacement(self):
        tracker = RateTracker()
        def sample(identifier,received,sent):
            return Snapshot('MacOS',[Interface(identifier,'Ethernet','ethernet',True,'',received,sent)])
        self.assertEqual(tracker.update(sample('en1',100,200),now=10)['en1'],(None,None))
        self.assertEqual(tracker.update(sample('en1',300,600),now=12)['en1'],(100,200))
        self.assertEqual(tracker.update(sample('en1',10,-1),now=14)['en1'],(None,None))
        self.assertEqual(tracker.update(sample('en2',800,1200),now=16)['en2'],(None,None))
        self.assertEqual(format_bytes(-1),'—')
        self.assertEqual(format_bytes(1024,rate=True),'1.0 KiB/s')

    def test_all_languages_have_complete_translations(self):
        self.assertEqual(len(LANGUAGES),10)
        for locale,_ in LANGUAGES:
            self.assertEqual(set(CATALOG[locale]),set(ROWS))
            self.assertTrue(all(CATALOG[locale].values()))
