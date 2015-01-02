#!/usr/bin/env python3

import praw
import yaml
import logging
import sql
import re
import datetime

#logging defaults
logging.basicConfig(filename = 'paperbot.log', level = logging.ERROR)
conf_file = 'cspaperbot.conf'

user_agent = 'CS paper bot v1.0 by /u/nath_schwarz'
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

regex_title = 'Title[\*: ]+(.+)\n'
regex_authors = 'Authors.*? ?(.+)'
regex_author_list = '(\w[\w ]+)'
regex_link = 'Link.*? ?(https?://[\w\-\.\/\~]+)\n'
regex_abstract = 'Abstract[\*: ]+(.+)\n'

#dates
today = str(datetime.date.today())
today_plus_two_weeks = str(datetime.date.today() + datetime.timedelta(weeks = 2))

#globals
r = None
conf = None
db = sql.Database()

def load_config():
    """Loads configuration from 'cspaperbot.conf' and returns it."""
    global conf
    try:
        with open(conf_file, 'r') as f:
            conf = yaml.load(f)
    except Exception as e:
        logging.error(e)

def write_config():
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
    list_submissions, top_paper = parse_voting_thread()
    if list_submissions:
        discussion_thread = create_thread(discussion_title,
            discussion_body  + top_paper.author.name +
            submissiontable(list_submissions) + top_paper.body)
        if conf['moderator'] == True:
            discussion_thread.sticky()
        top_paper = db.find_paper(parse_comment_to_paper(top_paper.body)['Title'])
        top_paper['Discussion'] = discussion_thread.permalink
        db.upsert_paper(top_paper)
        return discussion_thread
    else:
        logging.error('Empty response from parsed voting thread - no participation or error in parsing.')

def submissiontable(list_submissions):
    table = "  \n\nKarma count | Submitter | Paper title | Link to paper  \n ---|---|---|---  \n"
    for submission in list_submissions:
        table += str(submission['Karma'])
        table += '|/u/' + submission['Last_submitter']
        table += '|[' + submission['Title'] + '](' + submission['Last_submission_link'] + ')'
        table += '|' + '[Link](' + submission['Link'] + ')\n'
    table += '  \n\n'
    return table

def parse_comment_to_paper(comment):
    """Parses given comment body into a dictionary."""
    if 'WITHDRAWN' in comment:
        logging.info('Withdrawn submission:' + comment)
        return None
    if '[deleted]' in comment:
        logging.info('Deleted submission' + comment)
        return None
    try:
        paper = {}
        paper['Title'] = re.search(regex_title, comment).group(1)
        paper['Authors'] = re.findall(regex_author_list, re.search(regex_authors, comment).group(1))
        paper['Link'] = re.search(regex_link, comment).group(1)
        paper['Abstract'] = re.search(regex_abstract, comment).group(1)
        logging.info('Paper submission: ' + str(paper))
        return paper
    except Exception as e:
        logging.error('Parse error: ' + comment, e)

def process_comment(comment):
    logging.info('Processing comment')
    paper = parse_comment_to_paper(comment.body)
    if paper:
        query_paper = db.find_paper(paper['Title'])
        if query_paper:
            logging.info('Paper already submitted:' + str(query_paper))
            query_paper['Count_proposed'] += 1
            #This line is awful. Sadly nosqlite doesn't support sets
            if comment.author.name not in paper['Submitters']:
                query_paper['Submitters'] += [comment.author.name]
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
            paper['Karma'] = comment.ups
            paper['Last_submitter'] = comment.author.name
            paper['Last_submission_link'] = comment.permalink
            db.upsert_paper(paper)
            return paper

def parse_voting_thread():
    logging.info('Parsing voting thread')
    voting_thread = r.get_submission(submission_id = conf['current_voting_thread'], comment_sort = 'Best')
    if conf['moderator']:
        voting_thread.unsticky()
        voting_thread.unset_contest_mode()
    comments = voting_thread.comments
    top_comment = comments[0]
    list_submissions = [ process_comment(comment) for comment in comments]
    list_submissions = filter(None, list_submissions)
    return list_submissions, top_comment

def parse_pms():
    pms = r.get_unread()
    for pm in pms:
        author = pm.author.name
        if 'subscribe' in pm.body:
            if 'discussion' in pm.body:
                logging.info('Discussion subscriber' + author)
                conf['discussion_subscribers'].add(author)
            if 'voting' in pm.body:
                logging.info('Voting subscriber' + author)
                conf['voting_subscribers'].add(author)
        if 'unsubscribe' in pm.body:
            if 'discussion' in pm.body:
                logging.info('Discussion unsubscriber' + author)
                conf['discussion_subscribers'].remove(author)
            if 'voting' in pm.body:
                logging.info('Voting unsubscriber' + author)
                conf['voting_subscribers'].remove(author)
        pm.mark_as_read()

def send_notifications(link, title, recipients):
    for recipient in recipients:
        r.send_message(recipient, title, link)

def execute_actions():
    logging.info('Checking for actions')
    parse_pms()
    if today == conf['next_voting_date']:
        thread = create_voting_thread()
        send_notifications(thread.permalink, thread.title, conf['voting_subscribers'])
        conf['next_voting_date'] = today_plus_two_weeks
        conf['current_voting_thread'] = thread.id
    elif today == conf['next_discussion_date']:
        thread = create_discussion_thread()
        send_notifications(thread.permalink, thread.title, conf['discussion_subscribers'])
        conf['next_discussion_date'] = today_plus_two_weeks
        conf['paper_round'] += 1

def main():
    global conf, r
    load_config()
    login()
    db.open(conf['db_file'])
    execute_actions()
    db.close()
    write_config()
    r.clear_authentication()

if __name__ == "__main__":
    main()
