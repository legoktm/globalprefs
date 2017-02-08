#!/usr/bin/python
"""
Allows a user to set language preferences across Wikimedia wikis
Copyright (C) 2014, 2017 Kunal Mehta <legoktm@member.fsf.org>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import json
from flask import Flask, request, url_for
from flask_mwoauth import MWOAuth

import config

app = Flask(__name__)
app.secret_key = config.secret_key

mwoauth = MWOAuth(consumer_key=config.oauth_key, consumer_secret=config.oauth_secret)
app.register_blueprint(mwoauth.bp)


def embed_json(name, data):
    # https://stackoverflow.com/questions/9320427/best-practice-for-embedding-arbitrary-json-in-the-dom
    return '<script type="application/json" id="{0}">{1}</script>'.format(name, json.dumps(data))


def get_languages():
    data = mwoauth.request({'action': 'query', 'meta': 'siteinfo', 'siprop': 'languages'})
    languages = {}
    for lang in data['query']['languages']:
        languages[lang['code']] = lang['*']
    return languages


def get_attached_wikis(username):
    if 'debug' in request.args:
        return ['http://www.mediawiki.org']
    #meta=globaluserinfo&guiuser=Catrope&guiprop=merged&format=jsonfm
    wikis = mwoauth.request({
        'action': 'query',
        'meta': 'globaluserinfo',
        'guiuser': username,
        'guiprop': 'merged'
    })  # Shouldn't matter what wiki this request runs on
    return [wiki['url'] for wiki in wikis['query']['globaluserinfo']['merged']]


@app.route('/api/')
def api():
    wiki = request.args['wiki'].replace('http:', 'https:') + '/w'
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
    codes = sorted(list(languages))
    for lang in codes:
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
    t += '<script type="text/javascript" src="//tools-static.wmflabs.org/cdnjs/ajax/libs/jquery/2.0.3/jquery.min.js"></script>'
    link = url_for('static', filename='js.js')
    t += '<script type="text/javascript" src="{0}"></script>'.format(link)
    t += '</body></html>'

    return t

if __name__ == '__main__':
    app.run()
