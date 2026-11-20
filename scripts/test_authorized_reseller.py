#!/usr/bin/env python3
"""Offline importer regression tests (no network access needed)."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).parent))
import import_authorized_reseller as mod


def write_png(path):
    # Minimal PNG magic to exercise media checks, not a renderable storefront photo.
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + b'x' * 1200)


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.photos = self.root / 'photos'
        self.photos.mkdir()
        write_png(self.photos / 'account.png')
        self.inventory = self.root / 'inventory.json'
        self.inventory.write_text(json.dumps({'items': [{'title': 'Existing', 'price': '100'}]}))
        self.feed = self.root / 'feed.json'
        self.source = {
            'id': 'abc_123', 'title': '🔥 M416 Glacier Lv.7 | 4 X-Suits',
            'description': 'M416 Glacier level 7\n4 X-Suits\nWhatsApp seller +123456789012\nTransfer via linked email',
            'price_usd': '189.00', 'currency': 'USD', 'category': 'Account',
            'photos': ['account.png'], 'account_level': 75,
        }

    def test_full_import_preserves_titles_and_product_details(self):
        self.feed.write_text(json.dumps({'items': [self.source]}))
        r = mod.import_feed(self.feed, self.photos, self.inventory)
        self.assertEqual(r['new_products'], 1)
        self.assertEqual(json.loads(self.inventory.read_text())['items'][0]['title'], 'Existing')
        # Mock ROOT to direct applied media into the test directory.
        with patch.object(mod, 'ROOT', self.root):
            r = mod.import_feed(self.feed, self.photos, self.inventory, apply=True)
        self.assertTrue(r['applied'])
        data = json.loads(self.inventory.read_text())['items']
        self.assertEqual(len(data), 2)
        self.assertEqual(data[1]['title'], self.source['title'])
        self.assertEqual(data[1]['source_title'], self.source['title'])
        self.assertEqual(data[1]['price'], '189.00')
        self.assertNotIn('seller', data[1]['description'].lower())
        self.assertIn('Transfer via linked email', data[1]['description'])
        self.assertIn('+923454342911', data[1]['description'])
        self.assertTrue((self.root / data[1]['thumbnail'].lstrip('/')).exists())

    def test_rejects_unconfirmed_currency(self):
        with self.assertRaisesRegex(ValueError, 'USD'):
            mod.price_usd({'price': '159', 'currency': 'EUR'})

    def test_rejects_mixed_contact_with_factual_details(self):
        with self.assertRaisesRegex(ValueError, 'mixed'):
            mod.cleaned_description('M416 Glacier level 7 - Contact me on Telegram @supplier\nFull account')

    def test_rejects_fake_source_photo(self):
        with self.assertRaisesRegex(ValueError, 'locally downloaded'):
            mod.safe_photo('https://gameboost.com/a.png', self.photos)

    def test_rejects_pc_accounts(self):
        with self.assertRaisesRegex(ValueError, 'Steam'):
            mod.prepare_row({**self.source, 'title': 'PUBG Steam Account'}, self.photos)

    def test_avoids_duplicate_and_overwrite(self):
        self.feed.write_text(json.dumps({'items': [self.source, self.source]}))
        with self.assertRaisesRegex(ValueError, 'Repeated supplier listing'):
            mod.import_feed(self.feed, self.photos, self.inventory)
        self.feed.write_text(json.dumps({'items': [self.source]}))
        with patch.object(mod, 'ROOT', self.root):
            mod.import_feed(self.feed, self.photos, self.inventory, apply=True)
            r = mod.import_feed(self.feed, self.photos, self.inventory, apply=True)
        self.assertEqual(r['new_products'], 0)
        self.assertEqual(len(r['duplicates_skipped']), 1)


if __name__ == '__main__':
    unittest.main()