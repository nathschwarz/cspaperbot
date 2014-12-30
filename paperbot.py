#!/usr/bin/env python3

import praw
import yaml
import logging
import re

#logging defaults
logging.basicConfig(filename = 'paperbot.log', level = logging.ERROR)

user_agent = 'CS paper bot v0.01 by /u/nath_schwarz'

regex_title = 'Title.*? ([\w :]+)\n'
regex_authors = 'Authors.*? ([\w ,\.]+)'
regex_author_list = '(\w[\w ]+)'
regex_link = 'Link.*? (https?://[\w\-\.\/\~]+)\n'
regex_abstract = 'Abstract.*? ([\w \.\?\,\-\'\(\)\[\]]+)\n'
def write_config(conf, conf_file = 'cspaperbot.conf'):
    try:
        with open(conf_file, 'w') as f:
            yaml.dump(conf, f)
    except Exception as e:
        logging.error(e)

def login(user_agent, username, password):
    try:
        r = praw.Reddit(user_agent = user_agent)
        r.login(username, password)
        logging.info('Login successful')
        return r
    except Exception as e:
        logging.error(e)

def get_comments_on_voting(r, thread_id):
    return r.get_submission(submission_id = thread_id).comments

def parse_comment_to_paper(comment):
    title = re.search(regex_title, comment)
    if title is None:
        logging.info('Empty comment submission:\n' + comment)
        return None
    paper = {}
    paper['Title'] = title.group(1)
    paper['Authors'] = re.findall(regex_author_list, re.search(regex_authors, comment).group(1))
    paper['Link'] = re.search(regex_link, comment).group(1)
    paper['Abstract'] = re.search(regex_abstract, comment).group(1)
    logging.info("Paper submission:\n" + paper)
    return paper

def process_comment(comment):
    paper = parse_comment_to_paper(comment.body)
    if paper:
        query_paper = db.find_paper(paper['Title'])
        if query_paper:
            logging.info('Paper already submitted:' + query_paper)
            query_paper['Count_proposed'] += 1
            query_paper['Proposed_current_vote'] = 1
            if comment.author not in query_paper['Submitters']:
                query_paper['Submitters'] += comment.author.name
            if query_paper['Discussion'] is not '':
                comment.reply('This paper was already discussed [here]('+query_paper['Discussion']+').\nThanks for your suggestion.')
            db.upsert_paper(query_paper)
        else:
            paper['Count_proposed'] = 1
            paper['Proposed_current_vote'] = 1
            paper['Discussion'] = ''
            paper['Submitters'] = [comment.author.name]
            db.upsert_paper(paper)

def main():
    conf = load_config()
    r = login(user_agent, conf['username'], conf['password'])
    voting = r.get_submission(submission_id = conf['current_voting_thread'])
    comments = voting.comments
    for comment in comments:
        process_comment(comment)

if __name__ == "__main__":
    main()
