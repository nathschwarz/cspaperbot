#!/usr/bin/env python3

import praw
import yaml
import logging

#logging defaults
logging.basicConfig(filename = 'paperbot.log', level = logging.ERROR)

def load_config(conf_file = 'cspaperbot.conf'):
    try:
        with open(conf_file, 'r') as f:
            return yaml.load(f)
    except Exception as e:
        logging.error(e)

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

def main():
    conf = load_config()
    r = login(conf['user_agent'], conf['username'], conf['password'])

if __name__ == "__main__":
    main()
