#-*- coding: utf-8 -*-
import sys, pymysql, random, json, time, argparse, os
from slacker import Slacker
from websocket import create_connection
from konlpy.tag import Kkma
from konlpy.utils import pprint

reload(sys)
sys.setdefaultencoding('utf-8')

channels = {}

def init_data():
    parser = argparse.ArgumentParser(description='chicken master bot')

    parser.add_argument('-db', metavar='DB_INFO', type=str, required=True, help='mysql user info')
    parser.add_argument('-q', metavar='QUERY_INFO', type=str, required=True, help='mysql query list')
    parser.add_argument('-t', metavar='TOKEN_INFO', type=str, required=True, help='slack bot token info')

    args = vars(parser.parse_args())

    if not os.path.exists(args['db']):
        print(args['db'] + ' does not exist')
        sys.exit(-1)
    if not os.path.exists(args['q']):
        print(args['q'] + ' does not exist')
        sys.exit(-1)
    if not os.path.exists(args['t']):
        print(args['t'] + ' does not exist')
        sys.exit(-1)
    f = open(args['db'], 'r')
    info = json.loads(f.read())
    f.close()
    qf = open(args['q'], 'r')
    global query
    query=json.loads(qf.read())
    qf.close()
    global channels
    channels['dev'] = '#jstdio_dev'
    channels['gen'] = '#general'
    channels['job'] = '#job'

    sql_conn = pymysql.connect(host=info['host'], user=info['user'], password=info['password'], db=info['db'], charset=info['charset'], use_unicode=True)
    global curs
    curs = sql_conn.cursor(pymysql.cursors.DictCursor)
    
    global token
    tf = open(args['t'], 'r')
    token_info = json.loads(tf.read())
    tf.close()
    token = token_info['value']
    
    init_bot_chat()
    global shop_data
    shop_data = init_shop_data()
    sql_conn.close()

def init_bot_chat():
    sql = query['get_bot_chat']
    curs.execute(sql)
    rows = curs.fetchall()
    global reply_msg
    reply_msg=[]
    global chat_msg
    chat_msg=[]
    global recom_msg
    recom_msg=[]
    global greet_msg
    greet_msg=[]
    #print(rows)   
    for row in rows:
        if row['type']=='chat':
            chat_msg.append(row['text'])
        elif row['type']=='reply':
            reply_msg.append(row['text'])
        elif row['type']=='recommend':
            recom_msg.append(row['text'])
        elif row['type']=='greeting':
            greet_msg.append(row['text'])

def init_shop_data():
    sql = query['get_shop_data']
    curs.execute(sql)
    rows = curs.fetchall()
    return rows

def init_bot_token():
    sql = query['get_bot_token']
    curs.execute(sql)
    rows = curs.fetchall()
    return rows

def get_bot_chat():
    return chat_msg[random.randrange(len(chat_msg))]

def get_bot_reply():
    return reply_msg[random.randrange(len(reply_msg))]

def get_bot_greet():
    return greet_msg[random.randrange(len(greet_msg))]

def send_msg_to_channel(channel, msg):
    print("send msg to channel ["+channel+"] >> "+msg)
    slack.chat.post_message(channel, msg)

def get_shop_by_name(name):
    for shop in shop_data:
        if shop['name'] == name:
            return shop

def get_random_shop():
    idx = random.randrange(0, len(shop_data))
    shop = shop_data[idx]
    msg = recom_msg[random.randrange(len(recom_msg))] % (shop['name'], shop['best_menu'], shop['phone'])
    send_msg_to_channel(get_channel(), msg)
     
def show_all_shop_data():
    for shop in shop_data:
        msg = shop['name']+" "+shop['phone']+" "+shop['best_menu']
        send_msg_to_channel(get_channel(), msg)

def parse_message(txt):
    #print("received txt: "+txt)
    if txt.find('치킨')!=-1 or txt.find('닭') != -1:
        if txt.find('닥쳐') != -1 or txt.find('꺼져') != -1:
            send_msg_to_channel(get_channel(), 'ok...bye...')
            return -1
        elif txt.find('안뇽') != -1 or txt.find('안녕') != -1 or txt.find('하이') != -1 or txt.find('ㅎㅇ') != -1:
            send_msg_to_channel(get_channel(), get_bot_greet())
        elif txt.find('뭐먹') != -1 or txt.find('머먹') != -1 or txt.find('추천') != -1 or txt.find('어느') != -1 or txt.find('어떤') != -1:
            get_random_shop()
        elif txt.find('전부') != -1 or txt.find('리스트') != -1:
            show_all_shop_data()           
        else:
            send_msg_to_channel(get_channel(), get_bot_reply())
    elif txt.find('ㅋㅋㅋㅋ')!= -1 or txt.find('zzzz')!=-1:
        send_msg_to_channel(get_channel(), '병신같이 처웃지마ㅋㅋㅋㅋㅋㅋㅋㅋ웃으니까 치킨땡기잖앜ㅋㅋㅋㅋㅋㅋㅋㅋ')
    return 1;

def get_channel():
    #print('get_channel::', cur_channel)
    if cur_channel == u'G63C0CD4H':
        return dev_channel
    elif cur_channel == u'C62DMN4S3':
        return gen_channel
    elif cur_channel == u'G653BKS1Z':
        return job_channel
    else:
        return dev_channel

def set_cur_channel(cn):
    #print('set_cur_channel::',cn)
    global cur_channel
    cur_channel = cn

def Main():
#    init_data()
    
    print '====<System>: bot initiated===='
    send_msg_to_channel(get_channel(), get_bot_chat())
    response = slack.rtm.connect()
    endpoint = response.body['url']
    slack_socket = create_connection(endpoint)

    while True:
        recv = slack_socket.recv()
        if recv:    
#            print(recv)
            data = json.loads(recv)
            if data['type']=='message':
                set_cur_channel(unicode(data['channel']))
                if 'bot_id' in data:
                    continue
                else:
                    txt = str(unicode(data['text']))
                    if parse_message(txt) == -1:
                        break
    print '====<System>: bot is down===='

init_data()
slack = Slacker(token)
Main()
