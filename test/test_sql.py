#!/usr/bin/env python3
import unittest
import sql

class TestSQL(unittest.TestCase):
    def test_open_fail(self):
        self.db.open('nonexistent/file.db')
        self.assertTrue(self.db.db == None)

    def test_open(self):
        self.db.open()
        self.assertTrue(self.db.db != None)

    def test_get_paper(self):
        self.db.open()
        dummy = {
                'Authors': 'Dummy Author Sr., Dummy Author Jr.',
                'Count_proposed': 4,
                'Discussion': '',
                'Submitters': 'cspaperbot, dummyuser',
                'Title': 'Dummy paper 01',
                'Link': 'https://link.to/a/dummy/paper.pdf',
                'Abstract': 'Very short and undescriptive abstract of dummy paper 01',
                'Proposed_current_vote': 1
                }
        from_db = self.db.get_paper('Dummy paper 01')
        self.assertTrue(dummy == dict(from_db))

    def test_get_user(self):
        self.db.open()
        dummy = {
                'Name': 'cspaperbot',
                'Discussed_submissions': 'Dummy paper 01',
                'Discussion_comments': 0,
                'Submissions': 1
                }
        from_db = self.db.get_user('cspaperbot')
        self.assertTrue(dummy == dict(from_db))

    def test_get_author(self):
        self.db.open()
        dummy = {
                'Name': 'Paul Paper-Leecher',
                'Homepage': 'https://paper-leecher.com/',
                'CV': 'https://paper-leecher.com/cv.pdf'
                }
        from_db = self.db.get_author('Paul Paper-Leecher')
        self.assertTrue(dummy == dict(from_db))

    def setUp(self):
        self.db = sql.Database()

    def tearDown(self):
        pass

if __name__ == "__main__":
    unittest.main()
