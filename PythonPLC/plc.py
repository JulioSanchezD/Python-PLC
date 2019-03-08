import sqlite3
import time

class PLC:

    def __init__(self, name):
        self.name = name
        self.conn = sqlite3.connect('{}.db'.format(name))
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS memory
             (name TEXT PRIMARY KEY, value)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS counters
             (name TEXT PRIMARY KEY, preset_value INTEGER, current_value INTEGER)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS timers
             (name TEXT PRIMARY KEY, preset_time INTEGER)''')
        self.conn.commit()

    def createRetentiveTag(self, name, value):
        """Retentive Tags doesn't accept booleans, instead use binary integers"""
        data = dict(self.cursor.execute("SELECT * FROM memory").fetchall())
        if not name in data:
            self.cursor.execute('INSERT INTO memory VALUES (?, ?)', (name, value))
            self.conn.commit() 
        else:
            print("Tag {} already created".format(name))       
    
    def getValue(self, name):
        value = self.cursor.execute('SELECT value FROM memory WHERE name = ?', (name,)).fetchone()
        return value[0]
            
    def latch(self, name):
        self.cursor.execute('UPDATE memory SET value = 1 where name = ?', (name,))
        self.conn.commit()
            
    def unlatch(self, name):
        self.cursor.execute('UPDATE memory SET value = 0 where name = ?', (name,))
        self.conn.commit()
    
    def createCounter(self, name, preset_value):
        return self.Counter(name, self.conn, self.cursor, preset_value)

    def createTimer(self, name, preset_time):
        return self.Timer(name, self.conn, self.cursor, preset_time)
    
    class Pulse():

        def __init__(self):
            self.state = False

        def positiveTrigger(self, target):
            if target and not self.state:
                self.state = True
                return True
            elif not target and self.state:
                self.state = False
            return False
    
    class Counter():

        def __init__(self, name, conn, cursor, preset_value):
            self.counter_name = name
            self.conn = conn
            self.cursor = cursor
            data = dict(self.cursor.execute("select name, preset_value from counters").fetchall())
            if not name in data:
                self.cursor.execute('INSERT INTO counters VALUES (?, ?, 0)', (name, preset_value))
                self.conn.commit()
        
        @property
        def current_value(self):
            return self.cursor.execute('SELECT current_value FROM counters WHERE name = (?)', (self.counter_name,)).fetchone()[0]

        @property
        def preset_value(self):
            return self.cursor.execute('SELECT preset_value FROM counters WHERE name = (?)', (self.counter_name,)).fetchone()[0]
        
        @property
        def done(self):
            cv = self.current_value
            pv = self.preset_value
            if cv >= pv:
                return True
            return False
        
        @current_value.setter
        def current_value(self, cv):
            self.cursor.execute('UPDATE counters SET current_value = ? where name = ?', (cv, self.counter_name))
            self.conn.commit()

        @preset_value.setter
        def preset_value(self, pv):
            self.cursor.execute('UPDATE counters SET preset_value = ? where name = ?', (pv, self.counter_name))
            self.conn.commit()

        def countUp(self):
            cv = self.current_value
            cv += 1
            self.current_value = cv 
            self.conn.commit()
            return self.done

        def countDown(self):
            cv = self.current_value
            cv -= 1
            self.current_value = cv 
            return self.done

        def reset(self):
            self.current_value = 0
            self.conn.commit()
    
    class Timer():
        """Time expressed in mili seconds"""

        def __init__(self, name, conn, cursor, preset_time):
            self.timer_name = name
            self.conn = conn
            self.cursor = cursor
            data = dict(self.cursor.execute("select * from timers").fetchall())
            if not name in data:
                self.cursor.execute('INSERT INTO timers VALUES (?, ?)', (name, preset_time*1000))
                self.conn.commit()
            self.start_time = None
            self.active = False

        @property
        def preset_time(self):
            return self.cursor.execute('SELECT preset_time FROM timers WHERE name = (?)', (self.timer_name,)).fetchone()[0]
        
        @property
        def elapsed_time(self):
            if self.active:
                return (time.perf_counter() - self.start_time) * 2000 # It should be 1000, IDK with 2000 is accurate
            return None

        @property
        def done(self):
            if self.elapsed_time >= self.preset_time:
                return True
            return False

        def energize(self):
            if not self.active:
                self.start_time = time.perf_counter()
                self.active = True

        def reset(self):
            self.active = False
            self.start_time = None

        



        