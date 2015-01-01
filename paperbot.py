#!/usr/bin/env python3

import praw
import yaml
import logging
import sql
import re
import datetime

#logging defaults
logging.basicConfig(filename = 'paperbot.log', level = logging.ERROR)

user_agent = 'CS paper bot v0.01 by /u/nath_schwarz'
postfix = ("  \n*[Contact my creator](https://www.reddit.com/message/compose?to=%2Fr%2Fcspaperbot) | "
    "Post suggestions on /r/cspaperbot or open an issue on github | "
    "[source code](https://github.com/nathschwarz/cspaperbot)*")

voting_title = "[Paper] Nominations and voting thread Round "
voting_body = ("Please submit the papers you want discussed and vote for those you'd like to see.  \n"
    "Please use this as a template for nominations:  \n"
    "\*\*Title\*\*:  \n"
    "\*\*Authors\*\*:  \n"
    "\*\*Link\*\*:  \n"
    "\*\*Abstract\*\*:  \n"
    "\*\*Comments\*\*:  \n\n"
    "Keep in mind to separate authors with commata and not to use line breaks in the abstract.")

discussion_title = "[Paper] Discussion Round "
discussion_body = ("The paper this time was nominated by /u/")

regex_title = 'Title.*? ([\w :]+)\n'
regex_authors = 'Authors.*? ([\w ,\.]+)'
regex_author_list = '(\w[\w ]+)'
regex_link = 'Link.*? (https?://[\w\-\.\/\~]+)\n'
regex_abstract = 'Abstract.*? (.+)\n'

#dates
today = str(datetime.date.today())
today_plus_two_weeks = str(datetime.date.today() + datetime.timedelta(weeks = 2))

#globals
r = None
conf = None
db = sql.Database()

def load_config(conf_file = 'cspaperbot.conf'):
    """Loads configuration from 'cspaperbot.conf' and returns it."""
    global conf
    try:
        with open(conf_file, 'r') as f:
            conf = yaml.load(f)
    except Exception as e:
        logging.error(e)

def write_config(conf_file = 'cspaperbot.conf'):
    """Writes configuration to 'cspaperbot.conf'."""
    try:
        with open(conf_file, 'w') as f:
            yaml.dump(conf, f, default_flow_style=False)
    except Exception as e:
        logging.error(e)

def login():
    """Logs in to reddit with given username and password, returns reddit-instance."""
    global r
    try:
        r = praw.Reddit(user_agent = user_agent)
        r.login(conf['username'], conf['password'])
        logging.info('Login successful')
    except Exception as e:
        logging.error(e)

def reply_to(comment, body):
    """Reply to given comment with given text. Appends postfix automatically."""
    logging.info('Commented on ' + comment.id + ":\n" + body)
    comment.reply(body + '  \n' + postfix)

def create_thread(title, body):
    return r.submit(conf['subreddit'], title + str(conf['paper_round']), body + ' \n' + postfix)

def create_voting_thread():
    logging.info('Created voting thread')
    voting_thread = create_thread(voting_title, voting_body)
    if conf['moderator'] == True:
        voting_thread.sticky()
        voting_thread.set_contest_mode()
    return voting_thread

def create_discussion_thread():
    logging.info('Created discussion thread')
    chosen_paper = parse_voting_thread()
    if chosen_paper:
        discussion_thread = create_thread(discussion_title, discussion_body + chosen_paper.author.name + '  \n' + chosen_paper.body)
        if conf['moderator'] == True:
            discussion_thread.sticky()
        chosen_paper = db.find_paper(parse_comment_to_paper(chosen_paper.body)['Title'])
        chosen_paper['Discussion'] = discussion_thread.id
        db.upsert_paper(chosen_paper)
        return discussion_thread
    else:
        logging.error('Empty response from parsed voting thread - no participation or error in parsing.')

def parse_comment_to_paper(comment):
    """Parses given comment body into a dictionary."""
    if 'WITHDRAWN' in comment:
        logging.info('Withdrawn submission:\n' + comment)
        return None
    try:
        paper = {}
        paper['Title'] = re.search(regex_title, comment).group(1)
        paper['Authors'] = re.findall(regex_author_list, re.search(regex_authors, comment).group(1))
        paper['Link'] = re.search(regex_link, comment).group(1)
        paper['Abstract'] = re.search(regex_abstract, comment).group(1)
        logging.info("Paper submission:\n" + str(paper))
        return paper
    except Exception as e:
        logging.error('Parse error:\n' + comment, e)

def process_comment(comment):
    logging.info('Processing comment')
    paper = parse_comment_to_paper(comment.body)
    if paper:
        query_paper = db.find_paper(paper['Title'])
        if query_paper:
            logging.info('Paper already submitted:' + str(query_paper))
            query_paper['Count_proposed'] += 1
            if comment.author not in query_paper['Submitters']:
                query_paper['Submitters'] += comment.author.name
            db.upsert_paper(query_paper)
            #if the paper wasn't discussed it is added to the list of choices
            if query_paper['Discussion'] is '':
                return query_paper
            else:
                reply_to(comment, 'This paper was already discussed [here]('+query_paper['Discussion']+').\nThanks for your suggestion.')
        else:
            paper['Count_proposed'] = 1
            paper['Discussion'] = ''
            paper['Submitters'] = [comment.author.name]
            db.upsert_paper(paper)
            return paper
    return None

def parse_voting_thread():
    logging.info('Parsing voting thread')
    if conf['moderator'] == True:
        voting_thread.unsticky()
        voting_thread.unset_contest_mode()

    voting_thread = r.get_submission(submission_id = conf['current_voting_thread'], comment_sort = 'Best')
    comments = voting_thread.comments
    best_comment = None
    for comment in comments:
        process_comment(comment)
        if not best_comment:
            best_comment = comment
    return best_comment

def execute_actions():
    logging.info('Checking for actions')
    if today == conf['next_voting_date']:
        conf['next_voting_date'] = today_plus_two_weeks
        conf['current_voting_thread'] = create_voting_thread().id
    elif today == conf['next_discussion_date']:
def main():
    logging.info('This should log.')
    global conf, r
    load_config()
    login()
    db.open(conf['db_file'])
    execute_actions()
    db.close()
    write_config()

if __name__ == "__main__":
    main()
