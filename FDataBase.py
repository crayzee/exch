import sqlite3
 
class FDataBase:
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()
 
    def getMenu(self):
        sql = '''SELECT * FROM mainmenu'''
        try:
            self.__cur.execute(sql)
            res = self.__cur.fetchall()
            if res: 
                return res
        except:
            print("Ошибка чтения из БД")
        return []
        
    def getCodes(self):
        sql = '''SELECT name, code FROM codes'''
        try:
            self.__cur.execute(sql)
            res = self.__cur.fetchall()
            if res: 
                return res
        except:
            print("Ошибка чтения из БД")
        return []   
        
    #https://stackoverflow.com/a/4429028
    def getRates(self, currency = '', date_start='', date_end='', sort='desc'):
        start_new = date_start[6:10] + date_start[3:5] + date_start[0:2]
        end_new = date_end[6:10] + date_end[3:5] + date_end[0:2]
        try:
            self.__cur.execute(
'''
SELECT r.currency_code, r.date_rate, r.exchange_rate, c.name, c.nominal 
FROM rates r LEFT JOIN codes c ON r.currency_code=c.code WHERE currency_code='{}' 
AND substr(date_rate,7)||substr(date_rate,4,2)||substr(date_rate,1,2) 
BETWEEN '{}' AND '{}' order by
substr(date_rate,7)||substr(date_rate,4,2)||substr(date_rate,1,2) {}'''.format(
                currency, start_new, end_new, sort))
                
            res = self.__cur.fetchall()
            if res: return res
        except sqlite3.Error as e:
            print("Ошибка получения статьи из БД " + str(e))
 
        return []
        
    def addCode(self, name, eng_name, nominal, code):
        try:
            self.__cur.execute(
                "INSERT INTO codes VALUES(NULL, ?, ?, ?, ?)", 
                    (name, eng_name, nominal, code))
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления статьи в БД "+str(e))
            return False
 
        return True
        
    def addData(self, currency, date_rate, rate):
        try:
            self.__cur.execute(
                "INSERT OR IGNORE INTO rates VALUES(NULL, ?, ?, ?)", 
                    (currency, date_rate, rate))
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления статьи в БД "+str(e))
            return False
 
        return True