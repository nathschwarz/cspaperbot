#!/usr/bin/env python3
import unittest
import sql
import sqlite3

class TestSQL(unittest.TestCase):
    def test_open_fail(self):
        self.db.open('nonexistent/file.db')
        self.assertTrue(self.db.db == None)

    def test_open(self):
        self.db.open(self.db_file)
        self.assertTrue(self.db.db != None)

    def test_get_paper(self):
        to_check = 'Dummy paper 01'
        self.db.open()
        from_db = self.db.get_paper(to_check)

        self.test_cursor.execute("SELECT * FROM papers WHERE Title LIKE '{}'".format(to_check))
        dummy = self.test_cursor.fetchone()

        self.assertTrue(dummy == from_db)

    def test_get_user(self):
        to_check = 'cspaperbot'
        self.db.open()
        from_db = self.db.get_user(to_check)

        self.test_cursor.execute("SELECT * FROM users WHERE Name LIKE '{}'".format(to_check))
        dummy = self.test_cursor.fetchone()

        self.assertTrue(dummy == from_db)

    def test_get_author(self):
        to_check = 'Paul Paper-Leecher'
        self.db.open()
        from_db = self.db.get_author(to_check)

        self.test_cursor.execute("SELECT * FROM authors WHERE Name LIKE '{}'".format(to_check))
        dummy = self.test_cursor.fetchone()

        self.assertTrue(dummy == from_db)

    def setUp(self):
        self.db = sql.Database()
        self.db_file = 'db/papers.db'
        self.test_db = sqlite3.connect(self.db_file)
        self.test_db.row_factory = sqlite3.Row
        self.test_cursor = self.test_db.cursor()
        pass

    def tearDown(self):
        pass

if __name__ == "__main__":
    unittest.main()
