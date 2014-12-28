#!/usr/bin/env python3

import sqlite3
import logging

#logging defaults
logging.basicConfig(filename='database.log', level=logging.ERROR)

class Database:
    """Class to interact with the sqlite-database."""
    db = None
    cursor = None

    def open(self, db_file = 'db/papers.db'):
        """Opens the database and prepares the class."""
        try:
            self.db = sqlite3.connect(db_file)
            self.db.row_factory = sqlite3.Row
            self.cursor = self.db.cursor()
        except Exception as e:
            logging.error(e)

    def close(self):
        if self.db:
            self.db.commit()
            self.db.close()
        else:
            logging.info('db empty - close unsuccessful')

    def get_row(self, table, row, entry):
        self.cursor.execute("SELECT * FROM {0} WHERE {1} LIKE '%{2}%'".format(table, row, entry))
        return self.cursor.fetchone()

    def get_user(self, username):
        return self.get_row('users', 'Name', username)

    def get_author(self, name):
        return self.get_row('authors', 'Name', name)

    def get_paper(self, title):
        return self.get_row('papers', 'Title', title)
