from urllib.request import urlopen
import xml.etree.ElementTree as ET
import sqlite3
import os
from flask import Flask, render_template, url_for, request, g, flash, abort
from FDataBase import FDataBase
import json
from datetime import datetime
from io import StringIO

class CodeGetter():
    ''' Сохранить в БД данные по валютам:
        - название
        - название (англ)
        - номинал
        - внутренний код
    '''
    def __init__(self):
        pass
        
    def run(self):
        url_template = (
'http://www.cbr.ru/scripts/XML_val.asp?d=0')
        response = urlopen( url_template)
        root = ET.fromstring( response.read())
        codes = {}
        codes['items'] = []
        for item in root.findall('Item'):
            # По кодам этих валют данных нет на сайте ЦБ
            if item.attrib['ID'] not in ["R01015", "R01040F", 
            "R01095", "R01205","R01305","R01310","R01315","R01325", 
            "R01390","R01405","R01420","R01435","R01436", "R01510",
            "R01510A","R01523","R01570","R01665A","R01670B","R01720A",
            "R01740","R01750","R01790","R01795","R0","R01805"]:
                codes['items'].append( {
                    'name': item.find('Name').text, 
                    'eng_name': item.find('EngName').text, 
                    'nominal': item.find('Nominal').text, 
                    'code': item.attrib['ID']
                })
        return codes

class ExchGetter():
    '''Скачать данные за интересующий период в xml формате:
            - start_date: начало периода
            - end_date: окончание периода
            - curr_code: внутренний код валюты
        Отдаем словарь jsons для дальнейшей записи в БД
    '''
    def __init__(self, start_date, end_date, curr_code):
        self.start_date = start_date
        self.end_date = end_date
        self.curr_code = curr_code
        
    def run(self):
        url_template = (
'http://www.cbr.ru/scripts/XML_dynamic.asp?date_req1={}&date_req2={}&VAL_NM_RQ={}')
        
        response = urlopen( 
            url_template.format(self.start_date, self.end_date, self.curr_code))
        
        try:
            root = ET.fromstring( response.read())
        except ET.ParseError as err:
            with open( 'error_syntax.log', 'w') as error_log_file:
                error_log_file.write( str( err))
            return {'error': True}
        
        jsons = {}
        jsons['items'] = []
        for record in root.findall('Record'):
            jsons['items'].append( { 'currency': record.attrib['Id'],
                'date_rate': record.attrib['Date'],
                'exchange_rate': record.find('Value').text} )
        return jsons
        
        
        
# конфигурация приложения Flask
DATABASE = '/tmp/flsite.db'
DEBUG = True
SECRET_KEY = 'fdgfh78@#5?>gfhf89dx,v06k'
#USERNAME = 'admin'
#PASSWORD = 'SecretFish85'
        
app = Flask(__name__)
app.config.from_object(__name__)
app.config.update( dict(DATABASE=os.path.join(app.root_path,'flsite.db')))
        
def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn
    
def create_db():
    '''Вспомогательная функция для создания таблиц БД'''
    db = connect_db()
    with app.open_resource('tmp/sq_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()

def get_db():
    '''Соединение с БД, если оно еще не установлено'''
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db
    
@app.route("/", methods=["POST", "GET"])
def index():
    db = get_db()
    dbase = FDataBase(db)
    # codes - это чтобы построить выпадающий список с валютами
    codes = dbase.getCodes()    
    
    if request.method == "POST":
    
        ds = request.form['date_start']
        de = request.form['date_end']
        
        date_start = datetime.strptime( ds, "%Y-%m-%d").strftime("%d.%m.%Y")
        date_end = datetime.strptime( de, "%Y-%m-%d").strftime("%d.%m.%Y")
        
        if de < ds:
            flash('Ошибка: дата начала позднее даты окончания', category='error')
            return render_template('index.html', menu = dbase.getMenu(), codes = codes,
                currency = request.form['currency'])
        
        rates = dbase.getRates( currency=request.form['currency'], 
                date_start=date_start, date_end=date_end, 
                sort=request.form['sort'] )
        if not rates:
            flash('Данные еще не добавлены', category='error')
        
        return render_template('index.html', menu = dbase.getMenu(), 
            codes = dbase.getCodes(), date_start=date_start, date_end=date_end, 
            sort=request.form['sort'], rates=rates, 
            currency = request.form['currency'] )    
            
    return render_template('index.html', menu = dbase.getMenu(), codes = codes )
    
@app.teardown_appcontext
def close_db(error):
    '''Закрываем соединение с БД, если оно было установлено'''
    if hasattr(g, 'link_db'):
        g.link_db.close()

@app.route("/add_data", methods=["POST", "GET"])
def addData():
    db = get_db()
    dbase = FDataBase(db)
    codes = dbase.getCodes()    
 
    if request.method == "POST":
    
        ds = request.form['date_start']
        de = request.form['date_end']
        
        date_start = datetime.strptime( ds, "%Y-%m-%d").strftime("%d.%m.%Y")
        date_end = datetime.strptime( de, "%Y-%m-%d").strftime("%d.%m.%Y")
        
        if de < ds:
            flash('Ошибка: дата начала позднее даты окончания', category='error')
            return render_template('add_data.html', menu = dbase.getMenu(), 
                title="Добавление данных", codes = codes,
                currency = request.form['currency'] )        
      
        c = ExchGetter( start_date=date_start, end_date=date_end, 
            curr_code=request.form['currency'])
        jsons = c.run()
        if jsons.get('error'):
            flash('Произошла ошибка: проверьте, пожалуйста логи',
                category='error')
        elif jsons['items']:
            for j in jsons['items']:
                res = dbase.addData( j['currency'], j['date_rate'], 
                    j['exchange_rate'])
            flash('Данные добавлены успешно', category='success')
        else:
            flash('Данных по такой валюте нет, либо вы указали даты,'\
                ' которые еще не наступили', category='error')
        
 
        return render_template('add_data.html', menu = dbase.getMenu(), 
            title="Добавление данных", codes = codes, jsons=jsons,
            currency = request.form['currency'])
    return render_template('add_data.html', menu = dbase.getMenu(), 
        title="Добавление данных",codes=codes )

@app.route("/add_codes")
def addCodes():
    db = get_db()
    dbase = FDataBase(db)
    
    c = CodeGetter()
    codes = c.run()
    
    for c in codes['items']:    
        res = dbase.addCode( c['name'], c['eng_name'], c['nominal'], c['code'])
        
    return "done!"    
    
with app.test_request_context():
    print(url_for('index'))

if __name__ == "__main__":    
    app.run(host='127.0.0.1', port=5000)