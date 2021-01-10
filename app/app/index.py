# -*- coding: utf-8 -*-
from flask import request
from flask import Flask, send_from_directory
from gensim.models import Word2Vec
import json
import pymysql

app = Flask(__name__)
sIP = "192.168.200.180"
sPort = 5000

# main
@app.route('/', methods=['POST'])
def hello_world():
    recommend_item = list()
    input_data = str(request.form)
    input_data = input_data[19:]
    input_data = input_data.strip('([()]\'')
    beaconInfo = input_data.split(",")
    uuid = beaconInfo[0]
    major = beaconInfo[2]
    userId = beaconInfo[6]
    # MySQL Connection 연결
    conn = pymysql.connect(host=sIP, user='root', port='3306',
                           passwd='1234', db='ProjectServer', charset='utf8', unix_socket="/tmp/mysql.sock")
    # Connection 으로부터 Cursor 생성
    curs = conn.cursor()

    # SQL문 실행
    # 비콘 uuid 와 매칭되는 상품 코드 조회
    sql = "SELECT * FROM beaconInfo WHERE uuid = %s AND major = %s"
    curs.execute(sql, (uuid, major))
    rows = curs.fetchall()
    bStockcode = rows[0][2]
    bItemName = rows[0][3]
    # top5 상품코드 조회
    sql2 = "SELECT p.item1, p.item2, p.item3, p.item4, p.item5 FROM purchase p INNER JOIN userinfo u" \
           " ON p.customerid = u.userID WHERE p.stockcode = %s AND u.userID = %s"
    curs.execute(sql2, (bStockcode, userId))
    recommend_stockcode = curs.fetchall()

    if len(recommend_stockcode) > 0:
        # top5 상품코드 -> 상품명 조회
        sql3 = "SELECT description FROM product WHERE stockcode = %s"
        for v in recommend_stockcode[0]:
            curs.execute(sql3, str(v))
            temp_itemName = str(curs.fetchone()).strip('([()]\',')
            recommend_item.append(temp_itemName)
    conn.close()

    # json
    itemData = {'ITEMS': []}
    itemData['ITEMS'].append({'itemName': bItemName}) # 비콘의 상품.

    # 인자값으로 들어간 상품명이랑 가장 유사한 상품을 출력.
    if len(recommend_stockcode) <= 0:  # user가 비콘의 상품과 연관성이 없을 때 Word2vec으로 대체함.
        model = Word2Vec.load('Online_Retail_Similarity_word2vec_model_training')
        d = model.most_similar(u'%s' % (bItemName), topn=5)
        for (x, y) in d:
            itemData['ITEMS'].append({'itemName': x})
    else:
        for x in recommend_item:
            print('recommenItem : {}'.format(x))
            itemData['ITEMS'].append({'itemName': x})
    jsonData = json.dumps(itemData)
    jsonData = bytes(jsonData, 'utf8')
    print(jsonData)
    return jsonData


# login
@app.route('/login', methods=['POST'])
def login():
    input_data = str(request.form)
    input_data = input_data[19:]
    input_data = input_data.strip('([()]\'')
    input_data = input_data.split(",")

    userId = input_data[0]
    userPw = input_data[1]
    print('[ userID : {} login ]'.format(userId))
    # MySQL Connection 연결
    conn = pymysql.connect(host=sIP, user='root', port='3306',
                           passwd='1234', db='ProjectServer', charset='utf8', unix_socket="/tmp/mysql.sock")
    # Connection 으로부터 Cursor 생성
    curs = conn.cursor()

    # SQL문 실행
    sql = "SELECT count(*) FROM userInfo WHERE userID = %s AND userPW = %s"
    curs.execute(sql, (userId, userPw))

    # 데이타 Fetch
    rows = curs.fetchall()
    conn.close()

    msg = "false"
    if rows[0][0] == 1:  # 로그인 성공
        msg = "true"
    print('[login : {}]'.format(msg))
    return msg


# register
@app.route('/register', methods=['POST'])
def register():
    input_data = str(request.form)
    input_data = input_data[19:]
    input_data = input_data.strip('([()]\'')
    input_data = input_data.split(",")

    userId = input_data[0]
    userPw = input_data[1]

    # MySQL Connection 연결
    conn = pymysql.connect(host=sIP, user='root', port='3306',
                           passwd='1234', db='ProjectServer', charset='utf8', unix_socket="/tmp/mysql.sock")
    # Connection 으로부터 Cursor 생성
    curs = conn.cursor()

    # SQL문 실행
    sql = "INSERT INTO userinfo(userID, userPW) VALUES (%s, %s)"
    check = curs.execute(sql, (userId, userPw))
    conn.commit()
    print('check : {}'.format(check))
    conn.close()
    msg = "false"
    if check == 1:
        msg = "true"
    print('[register : {}]'.format(msg))
    return msg


# img
@app.route('/<path:path>')
def test(path):
    return send_from_directory(app.static_folder, request.path[1:])


# setting
if __name__ == '__main__':
    app.run(
        host=sIP,
        port=sPort)
