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
from flask import Flask, request, render_template
from flask_mwoauth import MWOAuth

import config

app = Flask(__name__)
app.secret_key = config.secret_key

mwoauth = MWOAuth(consumer_key=config.oauth_key, consumer_secret=config.oauth_secret)
app.register_blueprint(mwoauth.bp)


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
    username = mwoauth.get_current_user(False)
    if not username:
        return render_template('login.html')
    languages = get_languages()
    codes = sorted(list(languages))
    wikis = {'wikis': list(get_attached_wikis(username))}

    return render_template(
        'main.html', username=username, codes=codes,
        languages=languages, wikis=wikis
    )

if __name__ == '__main__':
    app.run(debug=True)
