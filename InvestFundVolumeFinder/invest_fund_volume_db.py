import sqlite3
from Util.debugger import debugger


class InvestFundVolumeDB(object):
    def __init__(self):
        self.conn = sqlite3.connect("invest_fund_volume.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS invest_fund_volume(
        stock_code VARCHAR,
        date VARCHAR,
        quantity INT,
        PRIMARY KEY (stock_code, date))
        """)

    def execute_with_conn_check(self, query, val, is_bulk=False, is_commit=True):
        for _ in range(3):
            try:
                if is_bulk:
                    self.cursor.executemany(query, val)
                else:
                    self.cursor.execute(query, val)
                if is_commit:
                    self.conn.commit()
                return
            except:
                self.conn.close()
                self.conn = sqlite3.connect("invest_fund_volume.db", check_same_thread=False)
                self.cursor = self.conn.cursor()

        debugger.debug("Failed to interact with db")

    def add_volume_history(self, volume_history_list):
        query = """
            INSERT OR REPLACE INTO invest_fund_volume(stock_code, date, quantity)
            VALUES (?,?,?)
        """

        val = volume_history_list
        self.execute_with_conn_check(query, val, is_bulk=True)

    def remove_volume_history_by_date(self, date):
        query = "DELETE FROM invest_fund_volume WHERE date=?"
        val = (date,)

        self.execute_with_conn_check(query, val)

    def get_volume_history(self, stock_code):
        query = """
                SELECT
                date, 
                quantity
                FROM invest_fund_volume WHERE stock_code=? ORDER BY date DESC"""
        val = (stock_code,)

        self.execute_with_conn_check(query, val, is_commit=False)
        return self.cursor.fetchall()


if __name__ == '__main__':
    db = InvestFundVolumeDB()
