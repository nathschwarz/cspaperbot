#!/usr/bin/env python3

import logging
import nosqlite

class Database:
    db = None
    papers = None
    authors = None
    users = None
    logger = logging.getLogger('sql')

    def open(self, db_file):
        self.logger.info('Opening database')
        try:
            self.db = nosqlite.Connection(db_file)
            self.papers = self.db['papers']
            self.authors = self.db['authors']
            self.users = self.db['users']
        except Exception as e:
            self.logger.error('Failed to open database: ', e)

    def close(self):
        self.logger.info('Closing database')
        self.db.close()

    def upsert(self, table, entry):
        self.logger.info('Upserting entry')
        table.insert(entry)

    def upsert_paper(self, paper):
        self.upsert(self.papers, paper)

    def upsert_author(self, author):
        self.upsert(self.authors, author)

    def upsert_user(self, user):
        self.upsert(self.users, user)

    def find_entry(self, table, spec):
        self.logger.info('Searching for entry')
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
