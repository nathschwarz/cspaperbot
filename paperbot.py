#!/usr/bin/env python3

import praw
import yaml
import logging
import sql
import re

#logging defaults
logging.basicConfig(filename = 'paperbot.log', level = logging.ERROR)

user_agent = 'CS paper bot v0.01 by /u/nath_schwarz'
postfix = ("  \n*[Contact my creator](https://www.reddit.com/message/compose?to=%2Fr%2Fcspaperbot) | "
    "Post suggestions on /r/cspaperbot or open an issue on github | "
    "[source code](https://github.com/nathschwarz/cspaperbot)*")

voting_title = "[Paper] Nominations and voting thread | Round "
voting_body = ("Please submit the papers you want discussed and vote for those you'd like to see.  \n"
    "Please use this as a template for nominations:  \n"
    "\*\*Title\*\*:  \n"
    "\*\*Authors\*\*:  \n"
    "\*\*Link\*\*:  \n"
    "\*\*Abstract\*\*:  \n"
    "\*\*Comments\*\*:  \n\n"
    "Keep in mind to separate authors with commata and not to use line breaks in the abstract.")

regex_title = 'Title.*? ([\w :]+)\n'
regex_authors = 'Authors.*? ([\w ,\.]+)'
regex_author_list = '(\w[\w ]+)'
regex_link = 'Link.*? (https?://[\w\-\.\/\~]+)\n'
regex_abstract = 'Abstract.*? ([\w \.\?\,\-\'\(\)\[\]]+)\n'

def load_config(conf_file = 'cspaperbot.conf'):
    """Loads configuration from 'cspaperbot.conf' and returns it."""
    try:
        with open(conf_file, 'r') as f:
            return yaml.load(f)
    except Exception as e:
        logging.error(e)

def write_config(conf, conf_file = 'cspaperbot.conf'):
    """Writes configuration to 'cspaperbot.conf'."""
    try:
        with open(conf_file, 'w') as f:
            yaml.dump(conf, f, default_flow_style=False)
    except Exception as e:
        logging.error(e)

def login(username, password):
    """Logs in to reddit with given username and password, returns reddit-instance."""
    try:
        r = praw.Reddit(user_agent = user_agent)
        r.login(username, password)
        logging.info('Login successful')
        return r
    except Exception as e:
        logging.error(e)

def reply_to(comment, body):
    """Reply to given comment with given text. Appends postfix automatically."""
    logging.info('Commented on ' + comment.id + ":\n" + body)
    comment.reply(body + '  \n' + postfix)

def create_voting_thread(r, subreddit, paper_round):
    """Create a voting thread in given subreddit with given round-number. Appends postfix automatically."""
    logging.info('Created voting thread')
    return r.submit(subreddit, voting_title + str(paper_round), text=voting_body+postfix)

def parse_comment_to_paper(comment):
    """Parses given comment body into a dictionary."""
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
                reply_to(comment, 'This paper was already discussed [here]('+query_paper['Discussion']+').\nThanks for your suggestion.')
            db.upsert_paper(query_paper)
        else:
            paper['Count_proposed'] = 1
            paper['Proposed_current_vote'] = 1
            paper['Discussion'] = ''
            paper['Submitters'] = [comment.author.name]
            db.upsert_paper(paper)

def main():
    conf = load_config()
    r = login(conf['username'], conf['password'])
    db = sql.Database()
    db.open(conf['db_file'])

    voting = r.get_submission(submission_id = conf['current_voting_thread'])
    comments = voting.comments
    for comment in comments:
        process_comment(comment)

    db.close()

if __name__ == "__main__":
    main()
