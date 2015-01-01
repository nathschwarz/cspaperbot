#!/usr/bin/env python3

import logging
import nosqlite

#logging defaults
logging.basicConfig(filename='database.log', level=logging.ERROR)

class Database:
    db = None
    papers = None
    authors = None
    users = None

    def open(self, db_file):
        self.db = nosqlite.Connection(db_file)
        self.papers = self.db['papers']
        self.authors = self.db['authors']
        self.users = self.db['users']

    def close(self):
        self.db.close()

    def upsert(self, table, entry):
        table.insert(entry)

    def upsert_paper(self, paper):
        self.upsert(self.papers, paper)

    def upsert_author(self, author):
        self.upsert(self.authors, author)

    def upsert_user(self, user):
        self.upsert(self.users, user)

    def find_entry(self, table, spec):
        result = table.find(spec)
        if result == []:
            return None
        else:
            return result[0]

    def find_paper(self, title):
        return self.find_entry(self.papers, {'Title':title})

    def find_author(self, name):
        return self.find_entry(self.authors, {'Name':name})

    def find_user(self, name):
        return self.find_entry(self.users, {'Name':name})
