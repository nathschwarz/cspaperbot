#!/usr/bin/env python3

import praw
import yaml
import logging
import sql
import re
import datetime
import argparse

conf_file = 'cspaperbot.conf'

user_agent = 'CS paper bot v1.0 by /u/nath_schwarz'
postfix = ("  \n*[Contact my creator](https://www.reddit.com/message/compose?to=%2Fr%2Fcspaperbot) | "
    "Post suggestions on /r/cspaperbot or open an issue on github | "
    "[source code](https://github.com/nathschwarz/cspaperbot)"
    "[wiki](/r/cspaperbot/wiki)"
    "*")

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
discussion_body = ("The paper this time was nominated by /u/{0}\n\n"
        "The table of submissions and votes for this voting can be viewed [here](/r/cspaperbot/wiki/voting/{1})  \n"
        "Links for all tables can be found [here](/r/cspaperbot/wiki/index#wiki_votings)\n\n"
        "{2}")

regex_middle = '[\*: \n]+'
regex_title = 'Title' + regex_middle + '(.+)\n'
regex_authors = 'Authors' + regex_middle + '(.+)'
regex_author_list = '(\w[\w \.]+)'
regex_link = 'Link' + regex_middle + '(https?://.+) *\n'
regex_abstract = 'Abstract' + regex_middle + '(.+)\n'

#dates
today = str(datetime.date.today())
today_plus_two_weeks = str(datetime.date.today() + datetime.timedelta(weeks = 2))

#globals
r = None
conf = None
db = sql.Database()
logger = None

def load_config():
    """Loads configuration from 'cspaperbot.conf' and returns it."""
    global conf
    try:
        with open(conf_file, 'r') as f:
            conf = yaml.load(f)
    except Exception as e:
        logger.error(e)

def write_config():
    """Writes configuration to 'cspaperbot.conf'."""
    try:
        with open(conf_file, 'w') as f:
            yaml.dump(conf, f, default_flow_style=False)
    except Exception as e:
        logger.error(e)

def login():
    """Logs in to reddit with given username and password, returns reddit-instance."""
    global r
    try:
        r = praw.Reddit(user_agent = user_agent)
        r.login(conf['username'], conf['password'])
        logger.info('Login successful')
    except Exception as e:
        logger.error(e)

def reply_to(comment, body):
    """Reply to given comment with given text. Appends postfix automatically."""
    logger.info('Commented on ' + comment.id + ":\n" + body)
    comment.reply(body + '  \n' + postfix)

def create_thread(title, body):
    return r.submit(conf['subreddit'], title + str(conf['paper_round']), body + ' \n' + postfix)

def create_voting_thread():
    logger.info('Created voting thread')
    voting_thread = create_thread(voting_title, voting_body)
    if conf['moderator'] == True:
        voting_thread.sticky()
        voting_thread.set_contest_mode()
    return voting_thread

def create_discussion_thread():
    logger.info('Created discussion thread')
    list_submissions, top_paper = parse_voting_thread()
    if list_submissions:
        discussion_thread = create_thread(discussion_title, discussion_body.format(top_paper.author.name, today, top_paper.body))
        add_wiki_page(submissiontable(list_submissions), discussion_thread.permalink)
        if conf['moderator'] == True:
            discussion_thread.sticky()
        top_paper = db.find_paper(parse_comment_to_paper(top_paper.body)['Title'])
        top_paper['Discussion'] = discussion_thread.permalink
        db.upsert_paper(top_paper)
        return discussion_thread
    else:
        logger.error('Empty response from parsed voting thread - no participation or error in parsing.')

def add_wiki_page(table, link):
    subreddit = 'cspaperbot'
    r.edit_wiki_page(subreddit, 'voting/'+today, '#Voting result of {0}\n\n[Discussion]({1})\n\n{2}'.format(today, link, table))
    r.edit_wiki_page(subreddit, 'index', '{0}  \n[Voting of {1}](/r/{2}/wiki/voting/{1}/)'.
                format(r.get_wiki_page(subreddit, 'index').content_md, today, subreddit))
    logger.info('Uploaded wiki-pages for new voting')

def submissiontable(list_submissions):
    table = 'Karma count | Submitter | Paper title | Link to paper  \n ---|---|---|---  \n'
    for submission in list_submissions:
        table += '{0} | /u/{1} | [{2}]({3}) | [Link]({4})\n'.format(
                str(submission['Karma']),
                submission['Last_submitter'],
                submission['Title'], submission['Last_submission_link'],
                submission['Link'])
    table += '\n\n'
    return table

def parse_comment_to_paper(comment):
    """Parses given comment body into a dictionary."""
    if 'WITHDRAWN' in comment:
        logger.info('Withdrawn submission:' + comment)
        return None
    try:
        paper = {}
        paper['Title'] = re.search(regex_title, comment).group(1)
        paper['Authors'] = re.findall(regex_author_list, re.search(regex_authors, comment).group(1).replace('and', ','))
        paper['Link'] = re.search(regex_link, comment).group(1)
        paper['Abstract'] = re.search(regex_abstract, comment).group(1)
        logger.info('Paper submission: ' + str(paper))
        return paper
    except Exception as e:
        logger.error('Parse error: ' + comment, e)

def process_comment(comment):
    logger.info('Processing comment')
    paper = parse_comment_to_paper(comment.body)
    if paper:
        query_paper = db.find_paper(paper['Title'])
        if query_paper:
            logger.info('Paper already submitted:' + str(query_paper))
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
            logger.info('New paper')
            paper['Count_proposed'] = 1
            paper['Discussion'] = ''
            paper['Submitters'] = [comment.author.name]
            paper['Karma'] = comment.ups
            paper['Last_submitter'] = comment.author.name
            paper['Last_submission_link'] = comment.permalink
            db.upsert_paper(paper)
            return paper

def parse_voting_thread():
    logger.info('Parsing voting thread')
    voting_thread = r.get_submission(submission_id = conf['current_voting_thread'])
    if conf['moderator']:
        voting_thread.unsticky()
        voting_thread.unset_contest_mode()
    comments = sorted([ comment for comment in voting_thread.comments if comment.author ],
            key = lambda x: x.ups, reverse = True)
    list_submissions = [ process_comment(comment) for comment in comments ]
    return list_submissions, comments[0]

def parse_pms():
    logger.info('Parsing PMs')
    pms = r.get_unread()
    for pm in pms:
        author = pm.author.name
        if 'reply' in pm.subject:
            logger.info('Reply to comment or post logged')
        if 'subscribe' in pm.body:
            reply = "Thanks, you're now "
            if 'unsubscribe' in pm.body:
                reply += "unsubscribed from "
                if 'discussion' in pm.body:
                    conf['discussion_subscribers'].discard(author)
                    reply += "discussion "
                if 'voting' in pm.body:
                    conf['voting_subscribers'].discard(author)
                    reply += "voting"
            else:
                reply += "subscribed to "
                if 'discussion' in pm.body:
                    conf['discussion_subscribers'].add(author)
                    reply += "discussion "
                if 'voting' in pm.body:
                    conf['voting_subscribers'].add(author)
                    reply += "voting"
            logger.info('Subscriptions: ' + author + ' - '+reply)
            r.send_message(pm.author.name, 'Submission settings', reply)
        else:
            logger.info('Unparseable message from ' + author + ', forwarding')
            r.send_message('nath_schwarz', 'Unparseable message from ' + author, pm.subject + '  \n' + pm.body)
        pm.mark_as_read()

def send_notifications(link, title, recipients):
    logger.info('Sending notification to subscribers')
    for recipient in recipients:
        r.send_message(recipient, title, link)

def execute_actions():
    logger.info('Checking for actions')
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
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("--stdout", action="store_true", help="print log output to stdout")
    args = parser.parse_args()

    global logger
    if args.verbose:
        logging.basicConfig(level = logging.INFO)
    else:
        logging.basicConfig(level = logging.ERROR)
    logging.basicConfig(filename = 'cspaperbot.log')
    logger = logging.getLogger('cspaperbot')

    logger.info('Initialization')
    global conf, r
    load_config()
    login()
    db.open(conf['db_file'])
    execute_actions()
    logger.info('Actions done, close db, save and logout')
    db.close()
    write_config()
    r.clear_authentication()

if __name__ == "__main__":
    main()
