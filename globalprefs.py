#!/usr/bin/python
from __future__ import unicode_literals
import json
from flask import Flask, request, url_for
from flask_mwoauth import MWOAuth
from werkzeug.contrib.cache import FileSystemCache

import config

app = Flask(__name__)
app.secret_key = config.secret_key

cache = FileSystemCache('cache')

mwoauth = MWOAuth(consumer_key=config.oauth_key, consumer_secret=config.oauth_secret)
app.register_blueprint(mwoauth.bp)


def embed_json(name, data):
    # https://stackoverflow.com/questions/9320427/best-practice-for-embedding-arbitrary-json-in-the-dom
    return '<script type="application/json" id="{0}">{1}</script>'.format(name, json.dumps(data))


def get_languages():
    languages = cache.get('languages')
    if languages is None:
        data = mwoauth.request({'action': 'query', 'meta': 'siteinfo', 'siprop': 'languages'})
        languages = {}
        for lang in data['query']['languages']:
            languages[lang['code']] = lang['*']
            cache.set('languages', languages)
    return languages


def get_attached_wikis(username):
    #meta=globaluserinfo&guiuser=Catrope&guiprop=merged&format=jsonfm
    wikis = mwoauth.request({
        'action': 'query',
        'meta': 'globaluserinfo',
        'guiuser': username,
        'guiprop': 'merged'
    })  # Shouldn't matter what wiki this request runs on
    for wiki in wikis['query']['globaluserinfo']['merged']:
        yield wiki['url']


@app.route('/api')
def api():
    wiki = request.args['wiki'].replace('http:', 'https://') + '/w'
    value = request.args['value']
    token = mwoauth.request({'action': 'tokens', 'type': 'options'}, wiki)['tokens']['optionstoken']
    d = mwoauth.request({'action': 'options', 'token': token, 'change': 'language={0}'.format(value)}, wiki)
    return json.dumps(d)


@app.route('/')
def index():
    t = '<html><head><title>Global preferences</title></head><body>'
    username = mwoauth.get_current_user(False)
    if username:
        t += 'You are currently logged in as {0}. <a href="logout">Logout</a>'.format(username)
    else:
        t += 'You are not logged in. <a href="login">Login</a>.'
        return t
    t += '\n<br />\n'
    t += 'Language: <select name="lang" id="lang-select">\n'
    languages = get_languages()
    for lang in languages:
        try:
            t += '<option value="{0}">{1}</option>\n'.format(lang.decode('utf-8','ignore'), languages[lang].decode('utf-8','ignore'))
        except UnicodeEncodeError:
            pass  # Ahhhhhhhhhhh
    t += '</select>\n'
    t += '<br />'
    t += '<button name="go" id="button-go">Go!</button>'
    t += '<div id="logging"></div>'
    # Embed some JSON...
    wikis = {'wikis': list(get_attached_wikis(username))}
    t += embed_json('attached-wikis', wikis)
    t += '<script type="text/javascript" src="//tools.wmflabs.org/static/js/jquery-2.0.3.min.js"></script>'
    link = url_for('static', filename='js.js')
    t += '<script type="text/javascript" src="{0}"></script>'.format(link)
    t += '</body></html>'

    return t

if __name__ == '__main__':
    app.run()
