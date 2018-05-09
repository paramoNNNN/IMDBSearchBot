#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import time
import sqlite3 as lite
import telepot
from datetime import datetime
from bs4 import BeautifulSoup
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

con = lite.connect('users.db', check_same_thread=False)
cur = con.cursor()

debug = False
state = 0
inlinepm = "blabblab"
keyboard0 = {'keyboard': ['Contact Creator']}
def on_chat_message(msg):
    global state
    print(msg)
    # if 'from' in msg
    user_id = msg['from']['id']
    if 'forward_from_message_id' in msg:
        message_id = msg['forward_from_message_id']
    elif 'message_id' in msg:
        message_id = msg['message_id']
    content_type, chat_type, chat_id = telepot.glance(msg)
    if 'text' in msg:
        msg_text = msg['text']
    elif 'caption' in msg:
        msg_text = "Photo" + "  " + unicode(msg['caption'])
    else:
        msg_text = "N/A"
    # set username
    if 'from' in msg:
        if 'username' in msg['from']:
            username = msg['from']['username']
        else:
            username = msg['from']['first_name']
    elif msg['chat']['type'] == "channel":
        username = msg['chat']['username']
    else:
        username = msg['from']['first_name']

    # Check user in db
    cur.execute("SELECT * FROM members WHERE Id = ?", (user_id,))
    row = cur.fetchall()
    if len(row) == 0 and chat_type == 'private':
        cur.execute("INSERT INTO members VALUES(?, ?, ?, ?)", (user_id, username, 0, str(datetime.now()),))
        con.commit()

    # Get user state from db
    if chat_type == 'private':
        cur.execute("SELECT state FROM members WHERE Id = ?", (user_id,))
        row = cur.fetchall()
        state = row[0][0]

    # MODS
    if chat_type == 'private':
        # Set last_seen in db
        cur.execute("UPDATE members set last_seen = ? WHERE Id = ?", (str(datetime.now()), user_id,))
        con.commit()

        if str(state).startswith('u'):
            set_state(0, user_id)
            imdb_id = state[1:]

            session = requests.session()
            response = session.get('http://imdb.com/title/' + str(imdb_id))
            soup = BeautifulSoup(response.text, 'html.parser')

            title = soup.find('h1', {'itemprop': 'name'}).text

            cur.execute("INSERT INTO movies(imdb_id, movie_name, url, is_correct, submitted_by) VALUES(?, ?, ?, ?, ?)", (imdb_id, title, msg_text, 'false', user_id))
            con.commit()
            bot.sendMessage(chat_id, "your link will be accessible after confirmation")
            return

        if '/start' == msg_text:
            bot.sendMessage(chat_id, 'Just give me a name' + "\n" + '/last_links - Get last download links added' + "\n" + '/watchlist - Show your Watchlist')

        elif msg_text.startswith('/r'):
            url_id = msg_text[2:]
            cur.execute("SELECT * FROM reports WHERE url_id = ? and reported_by = ? and status = ?", (url_id, user_id, 'false'))
            result = cur.fetchall()
            if len(result) > 0:
                bot.sendMessage(chat_id, "Your report has already submitted")
                return
            else:
                cur.execute("INSERT INTO reports(url_id, reported_by, status, message_id) VALUES(?, ?, ?, ?)", (url_id, user_id, 'false', msg['message_id']))
                con.commit()
                bot.sendMessage(chat_id, "Thanks, We'll check that as soon as possible")

        elif '/watchlist' == msg_text:
            cur.execute("SELECT * FROM watchlist WHERE user_id = ?", (user_id,))
            result = cur.fetchall()

            result_to_send = "Your Watchlist: " + "\n"
            for idx, item in enumerate(result):
                result_to_send += \
                    "*" + str(idx + 1) + ".*" + "\n" + \
                    '📄*Title:* ' + str(item[3]) + "\n"+ "\n" +\
                    '🔗*IMDb Link:* ' + '[IMDb](http://imdb.com/title/' + str(item[2]) + ")"+ "\n" + "\n" +\
                    '➕*MoreInfo:* /m' + str(item[2]) + "\n" + "\n" +\
                    "\n" + "\n"

            bot.sendMessage(chat_id, result_to_send, parse_mode="Markdown", disable_web_page_preview=True)

        elif '/last_links' == msg_text:
            cur.execute("SELECT imdb_id, movie_name, url FROM movies WHERE is_correct = ? ORDER BY Id DESC limit 8", ('true',))
            result = cur.fetchall()
            result_to_send = ""
            button_links = []

            for idx, val in enumerate(result):
                result_to_send += \
                    "*" + str(idx + 1) + ".*" + "\n" + \
                    '📄*Title:* ' + str(val[1]) + "\n"+ "\n" +\
                    '🔗*IMDb Link:* ' + '[IMDb](http://imdb.com/title/' + str(val[0]) + ")"+ "\n" + "\n" +\
                    '🔗*Download Link:* ' + '[Download](' + str(val[2]) + ')' + "\n" + "\n" + \
                    '➕*MoreInfo:* /m' + str(val[0]) + "\n" + "\n" +\
                    "\n" + "\n"

            for idx, val in enumerate(result):
                button_links.append(
                    InlineKeyboardButton(text=str(idx + 1), callback_data="m" + val[0])
                )

            keyboardi = InlineKeyboardMarkup(inline_keyboard=[
                button_links,
            ])

            bot.sendMessage(chat_id, result_to_send, parse_mode="Markdown", reply_markup=keyboardi, disable_web_page_preview=True)

        elif 'send_to_all=' in msg_text and (username == "paramoNNN"):
            txt = msg_text.split('=')[1]

            cur.execute("SELECT * FROM members")
            result = cur.fetchall()
            for item in result:
                try:
                    bot.sendMessage(item[0], txt)
                except:
                    bot.sendMessage(chat_id, "This user blocked bot: " + str(item[0]) + ", " + item[1])
                time.sleep(0.2)

        elif '/check_reports' == msg_text and (user_id == 516036245):
            cur.execute("SELECT * FROM reports WHERE status = ?", ('false',))
            result = cur.fetchall()
            
            if len(result) == 0:
                bot.sendMessage(chat_id, "Nothing Found! 😞")

            for idx, report in enumerate(result):
                cur.execute("SELECT url FROM movies WHERE Id = ?", (report[1],))
                url = cur.fetchone()

                cur.execute("SELECT Username FROM members WHERE Id = ?", (user_id,))
                username = cur.fetchone();

                result_to_send = '*' + str(idx + 1) + '.*' + '\n' + \
                                  '🔗*Download Link:* ' + '[Download](' + url[0] + ')' + '\n' + \
                                  '✅*Submitted By:* @' + username[0] + '\n'

                keyboardi = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="It's Broken",
                     callback_data="ra" + str(report[0]) + ":" + str(report[1]) + ":" + str(report[2]))
                     ],
                    [InlineKeyboardButton(text="It's not Broken",
                     callback_data="rd" + str(report[0]) + ":" + str(report[1]) + ":" + str(report[2]))
                    ]
                ])

                bot.sendMessage(chat_id, result_to_send, parse_mode="Markdown", reply_markup=keyboardi)

        elif '/check_links' == msg_text and (user_id == "516036245"):
            cur.execute("SELECT * FROM movies WHERE is_correct = ?", ('false',))
            result = cur.fetchall()

            if len(result) < 1:
                bot.sendMessage(chat_id, "Nothing Found! 😞")

            for val in result:
                cur.execute("SELECT Username FROM members WHERE Id = ?", (user_id,))
                username = cur.fetchone()

                result_to_send = "🔗IMDb Link: http://imdb.com/title/" + str(val[1]) + "\n" +\
                                 "📄Title: " + val[2] + "\n" +\
                                 "⬇️Download Link: " + val[3] + "\n" +\
                                 "✅Submitted By: " + "@" + username[0]

                keyboardi = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Accept",
                     callback_data="a" + str(val[1]) + ":" + str(val[0]))
                     ],
                    [InlineKeyboardButton(text="Decline",
                     callback_data="d" + str(val[1]) + ":" + str(val[0]))
                    ]
                ])
                bot.sendMessage(chat_id, result_to_send, reply_markup=keyboardi)

        elif msg_text.startswith('/m'):
            result_to_send = get_movie_info(msg_text[2:])

            cur.execute("SELECT * FROM watchlist WHERE user_id = ? and movie_id = ?", (user_id, msg_text[2:],))
            result = cur.fetchall()
            if len(result) == 0:
                watchlist_keyboard = [InlineKeyboardButton(text="Add to Watchlist",
                                callback_data="wa" + msg_text[2:] + ":" + result_to_send['title'])
                             ]
            elif len(result) != 0:
                watchlist_keyboard = [InlineKeyboardButton(text="Remove from Watchlist",
                                callback_data="wr" + msg_text[2:] + ":" + result_to_send['title'])
                             ]

            bot.sendChatAction(chat_id, 'upload_photo')
            time.sleep(0.3)
            keyboardi = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Set Download Link",
                 callback_data="u" + msg_text[2:])
                ],
                [InlineKeyboardButton(text="Get Download Links",
                 callback_data="g" + msg_text[2:])
                ],
                watchlist_keyboard
            ])
            bot.sendPhoto(chat_id, result_to_send['image'], result_to_send['result_to_send'], reply_markup=keyboardi)
        else:
            bot.sendMessage(chat_id, "Searching...")
            result = search(name=msg_text, page=1)
            button_links = []


            for idx, link in enumerate(result['button_links']):
                button_links.append(
                    [InlineKeyboardButton(text=result['titles'][idx], callback_data="m" + link)]
                )

            button_links.append([InlineKeyboardButton(text="⬅️", callback_data="text:" + msg_text + ":page:1:action:prev"),
                                InlineKeyboardButton(text="➡️", callback_data="text:" + msg_text + ":page:1:action:next")])

            keyboardi = InlineKeyboardMarkup(inline_keyboard=button_links)

            if result['result'] == "":
                result['result'] = "Nothing Found! 😞"
                keyboardi = None

            bot.sendMessage(chat_id, result['result'], reply_markup=keyboardi, parse_mode="Markdown", disable_web_page_preview=True)

def on_callback_query(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    print('Callback Query:', query_id, from_id, query_data)

    if msg['data'].startswith('wa'):
        data = msg['data'][2:].split(':')
        movie_id = data[0]
        movie_name = data[1]

        cur.execute("SELECT * FROM watchlist WHERE user_id = ? and movie_id = ?", (from_id, movie_id,))
        result = cur.fetchall()
        if len(result) != 0:
            bot.answerCallbackQuery(query_id, text="This Movie is already in your Watchlist")
            bot.sendMessage(from_id, "This Movie is already in your Watchlist", reply_to_message_id=msg['message']['message_id'])
            return

        cur.execute("INSERT INTO watchlist(user_id, movie_id, movie_name) VALUES(?, ?, ?)", (from_id, movie_id, movie_name,))
        con.commit()

        result_to_send = get_movie_info(movie_id)

        keyboardi = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Set Download Link",
                callback_data="u" + movie_id)
            ],
            [InlineKeyboardButton(text="Get Download Links",
                callback_data="g" + movie_id)
            ],
            [InlineKeyboardButton(text="Remove from Watchlist",
                callback_data="wr" + movie_id + ":" + result_to_send['title'])
            ]
        ])
        bot.editMessageReplyMarkup((msg['message']['chat']['id'], msg['message']['message_id']), reply_markup=keyboardi)

        bot.answerCallbackQuery(query_id, text="Successfully added to your Watchlist")
        bot.sendMessage(from_id, "Successfully added to your Watchlist", reply_to_message_id=msg['message']['message_id'])

    elif msg['data'].startswith('wr'):
        data = msg['data'][2:].split(':')
        movie_id = data[0]
        movie_name = data[1]

        cur.execute("SELECT * FROM watchlist WHERE user_id = ? and movie_id = ?", (from_id, movie_id,))
        result = cur.fetchall()
        if len(result) == 0:
            bot.answerCallbackQuery(query_id, text="This Movie is already removed from your Watchlist")
            bot.sendMessage(from_id, "This Movie is already removed from your Watchlist", reply_to_message_id=msg['message']['message_id'])
            return

        cur.execute("DELETE FROM watchlist WHERE user_id = ? and movie_id = ?", (from_id, movie_id,))
        con.commit()

        result_to_send = get_movie_info(movie_id)

        keyboardi = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Set Download Link",
                callback_data="u" + movie_id)
            ],
            [InlineKeyboardButton(text="Get Download Links",
                callback_data="g" + movie_id)
            ],
            [InlineKeyboardButton(text="Add to Watchlist",
                callback_data="wa" + movie_id + ":" + result_to_send['title'])
            ]
        ])
        bot.editMessageReplyMarkup((msg['message']['chat']['id'], msg['message']['message_id']), reply_markup=keyboardi)

        bot.answerCallbackQuery(query_id, text="Successfully removed from your Watchlist")
        bot.sendMessage(from_id, "Successfully removed from your Watchlist", reply_to_message_id=msg['message']['message_id'])

    elif msg['data'].startswith('ra'):
        data = msg['data'][2:].split(':')
        report_id = data[0]
        movie_id = data[1]
        user_id = data[2]

        cur.execute("UPDATE reports set status = ? WHERE Id = ?", ('broken', report_id,))
        cur.execute("UPDATE movies set is_correct = ? WHERE Id = ?", ('broken', movie_id,))
        con.commit()

        cur.execute("SELECT Id FROM members WHERE Id = ?", (user_id,))
        result = cur.fetchone()

        cur.execute("SELECT message_id FROM reports WHERE Id = ?", (report_id,))
        message_id = cur.fetchone()
        if message_id is not None:
            message_id = message_id[0]
        else:
            message_id = 0

        bot.answerCallbackQuery(query_id, text="Successfully accepted")

        if result is not None:
            # bot.sendMessage(result[0], "🚫This link you reported its broken and we deleted it. thanks for your report", reply_to_message_id=message_id)
            cur.execute("SELECT imdb_id FROM movies WHERE Id = ?", (movie_id,))
            imdb_id = cur.fetchone()[0]
            bot.sendMessage(result[0], "🚫This link you reported its broken and we deleted it. thanks for your report \n ➕MoreInfo: /m" + imdb_id)

    elif msg['data'].startswith('rd'):
        data = msg['data'][2:].split(':')
        report_id = data[0]
        movie_id = data[1]
        user_id = data[2]

        cur.execute("UPDATE reports set status = ? WHERE Id = ?", ('n', report_id,))
        cur.execute("UPDATE movies set is_correct = ? WHERE Id = ?", ('true', movie_id,))
        con.commit()

        cur.execute("SELECT Id FROM members WHERE Id = ?", (user_id,))
        result = cur.fetchone()

        cur.execute("SELECT message_id FROM reports WHERE Id = ?", (report_id,))
        message_id = cur.fetchone()
        if message_id is not None:
            message_id = message_id[0]
        else:
            message_id = 0

        bot.answerCallbackQuery(query_id, text="Successfully declined")

        if result is not None:
            # bot.sendMessage(result[0], "✅This link you reported is ok and nothing to do. thanks for your report", reply_to_message_id=message_id)
            cur.execute("SELECT imdb_id FROM movies WHERE Id = ?", (movie_id,))
            imdb_id = cur.fetchone()[0]
            bot.sendMessage(result[0], "✅This link you reported is ok and nothing to do. thanks for your report \n ➕MoreInfo: /m" + imdb_id)

    elif msg['data'].startswith('m'):
        result_to_send = get_movie_info(msg['data'][1:])

        cur.execute("SELECT * FROM watchlist WHERE user_id = ? and movie_id = ?", (from_id, msg['data'][1:],))
        result = cur.fetchall()
        if len(result) == 0:
            watchlist_keyboard =  [InlineKeyboardButton(text="Add to Watchlist",
                            callback_data="wa" + msg['data'][1:] + ":" + result_to_send['title'])
                         ]
        elif len(result) != 0:
            watchlist_keyboard =  [InlineKeyboardButton(text="Remove from Watchlist",
                            callback_data="wr" + msg['data'][1:] + ":" + result_to_send['title'])
                         ]

        keyboardi = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Set Download Link",
             callback_data="u" + msg['data'][1:])
            ],
            [InlineKeyboardButton(text="Get Download Links",
             callback_data="g" + msg['data'][1:])
            ],
            watchlist_keyboard
        ])

        bot.sendChatAction(msg['message']['chat']['id'], 'upload_photo')
        time.sleep(0.3)
        bot.answerCallbackQuery(query_id, text="Movie Info")
        bot.sendPhoto(msg['message']['chat']['id'], result_to_send['image'], result_to_send['result_to_send'], reply_markup=keyboardi)

    elif msg['data'].startswith('a'):
        data = msg['data'].split(':', 1)
        imdb_id = data[0][1:]
        Id = data[1]
        cur.execute("UPDATE movies set is_correct = ? WHERE imdb_id = ? and Id = ?", ('true', imdb_id, Id))
        con.commit()
        bot.answerCallbackQuery(query_id, text="Successfully accepted")

    elif msg['data'].startswith('d'):
        data = msg['data'].split(':', 1)
        imdb_id = data[0][1:]
        Id = data[1]
        cur.execute("UPDATE movies set is_correct = ? WHERE imdb_id = ? and Id = ?", ('declined', imdb_id, Id))
        con.commit()
        bot.answerCallbackQuery(query_id, text="Successfully declined")

    elif msg['data'].startswith('u'):
        set_state(msg['data'], from_id)
        bot.sendMessage(msg['message']['chat']['id'], "Send me a Correct link")
        bot.answerCallbackQuery(query_id, text="Send me a Correct link")

    elif msg['data'].startswith('g'):
        print(msg)
        set_state(0, from_id)
        links = get_links(msg['data'][1:])
        result_to_send = ""
        for idx, val in enumerate(links):
            result_to_send += "*" + str(idx + 1) + ". *" + "\n" +\
                              "🔗*Download Link:* " + "[Download]" + "(" + str(val[1]) + ")" + "\n" +\
                              "🚫*Report:* " + "/r" + str(val[0]) + "\n" + "\n"

        if result_to_send == "":
            result_to_send = "Nothing Found! 😞"

        bot.answerCallbackQuery(query_id, str("Links"))
        bot.sendMessage(msg['message']['chat']['id'], result_to_send, parse_mode="Markdown",
                        reply_to_message_id=msg['message']['message_id'], disable_web_page_preview=True)

    elif msg['data'].startswith('text'):
        data = msg['data'].split(':')
        name = data[1]
        page = int(data[3])
        action = data[5]
        result = ""
        button_links = []

        if action == "next":
            page = page + 1
            result = search(name=name, page=page)

        elif action == "prev":
            page = page - 1
            if page < 1:
                page = 1
            result = search(name=name, page=page)

        for idx, link in enumerate(result['button_links']):
            button_links.append(
                [InlineKeyboardButton(text=result['titles'][idx], callback_data="m" + link)]
            )

        button_links.append([InlineKeyboardButton(text="⬅️", callback_data="text:" + name + ":page:" + str(page) + ":action:prev"),
                          InlineKeyboardButton(text="➡️", callback_data="text:" + name + ":page:" + str(page) + ":action:next")])

        keyboardi = InlineKeyboardMarkup(inline_keyboard=button_links)


        if result['result'] == "":
            result['result'] = "Nothing Found! 😞"
            keyboardi = None

        if result['count'] == 0:
            bot.answerCallbackQuery(query_id, text="Nothing Found! 😞")
            return
        try:
            bot.editMessageText((msg['message']['chat']['id'], msg['message']['message_id']),
                                 text=result['result'], reply_markup=keyboardi, parse_mode="Markdown", disable_web_page_preview=True)
        except:
            bot.answerCallbackQuery(query_id, text="Nothing Found! 😞")


def set_state(_state, user_id):
    cur.execute("UPDATE members SET state = ? WHERE Id = ?", (_state, user_id,))
    con.commit()

def get_links(imdb_id):
    cur.execute("SELECT Id, url FROM movies WHERE imdb_id = ? and is_correct = ?", (imdb_id, 'true'))
    links = cur.fetchall()
    return links

def get_movie_info(imdb_id):
    session = requests.session()
    response = session.get('http://imdb.com/title/' + imdb_id)
    soup = BeautifulSoup(response.text, 'html.parser')

    if soup.find('title').text == "404 Error - IMDb":
        # bot.sendMessage(chat_id, "Nothing Found! 😞")
        return

    title = soup.find('h1', {'itemprop': 'name'}).text

    image = soup.find('img', {'itemprop': 'image'}).attrs['src']

    ratingValue = soup.find('span', {'itemprop': 'ratingValue'})
    if ratingValue is not None:
        ratingValue = ratingValue.text
    else:
        ratingValue = "N/A"

    ratingCount = soup.find('span', {'itemprop': 'ratingCount'})
    if ratingCount is not None:
        ratingCount = ratingCount.text
    else:
        ratingCount = "N/A"

    duration = soup.find('time', {'itemprop': 'duration'})
    if duration is not None:
        duration = duration.text
        duration = duration.replace(" ", "")
        duration = duration.replace("\n", "")
    else:
        duration = "N/A"

    contentRating = soup.find('span', {'itemprop': 'contentRating'})
    if contentRating is not None:
        contentRating = contentRating.text
    else:
        contentRating = "N/A"

    result_to_send = \
    '📄Title: ' + title + "\n" + "\n" +\
    '📈Rating Value: ' + ratingValue + "\n" + "\n" +\
    '📊Rating Count: ' + ratingCount + "\n" + "\n" +\
    '🕐Duration: ' + duration + "\n" + "\n" +\
    '✅Content Rating: ' + contentRating + "\n" + "\n"

    return {'result_to_send': result_to_send, 'image': image, 'title': title}

def search(name, page):
    url = "http://www.imdb.com/find?q=" + str(name) + "&s=tt&ref_=fn_tt_ex"

    session = requests.session()
    response = session.get(url)

    soup = BeautifulSoup(response.text, 'html.parser')
    result = soup.findAll('tr', {'class': 'findResult'})
    result_to_send = ""
    count = 0
    button_links = []
    titles = []

    next_page = page * 5
    if len(result) > 0:
        if next_page > len(result):
            _next = len(result)
        else:
            _next = next_page

        result_to_send = "Page: " + str(page) + " - " + str((next_page - 5) + 1) + "/" + str(_next) + "\n" + "Total: " +\
        str(len(result)) + "\n"

    for idx, item in enumerate(result[next_page - 5:next_page]):
        _result = item.find('td', {'class': 'result_text'})
        count += 1
        if _result is not None:
            title = _result.text
            titles.append(title)

            if title[0] == " ":
                title = title[1:]
                print(title)

            result_to_send += "*" + str(idx + 1) + ".*" + "\n"+\
            '🔗*Link:* ' + '[IMDb](http://imdb.com' + _result.find('a').attrs['href'] + ")"+ "\n" + "\n" +\
            '📄*Title:* ' + title + "\n"+ "\n" +\
            '➕*MoreInfo:* /m' + _result.find('a').attrs['href'].split('/')[2] + "\n" + "\n" +\
            "\n"

            button_links.append(_result.find('a').attrs['href'].split('/')[2])
            # print("****************")
            # print('url: ' + 'http://imdb.com' + _result.find('a').attrs['href'])
            # print('title: ' + title)
            # print('Rating Value: ' + ratingValue)
            # print('Rating Count: ' + ratingCount)
            # print('Duration: ' + duration)
            # print('Content Rating: ' + contentRating)
            # print("****************" + "\n")

    return {'result': result_to_send, 'count': count, 'button_links': button_links, 'titles': titles}

bot = telepot.Bot("495745045:AAHBjyNiVRB5wGj0LiK5mRQEwewt3zYNVIY")
MessageLoop(bot, {'chat': on_chat_message,
                  'callback_query': on_callback_query}).run_as_thread()
print('IMDb Searcher BOT Starting ...')

while 1:
    time.sleep(1)

# -----taha----- #
