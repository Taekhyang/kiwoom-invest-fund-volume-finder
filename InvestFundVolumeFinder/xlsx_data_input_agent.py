import threading
import os

import datetime
from InvestFundVolumeFinder.xlsx_module import XlsxModule
from InvestFundVolumeFinder.invest_fund_volume_db import InvestFundVolumeDB


class XlsxDataInputAgent(threading.Thread):
    def __init__(self, crawl_complete_q, logger):
        super().__init__()
        self.logger = logger
        self.stopped = threading.Event()
        self.db = InvestFundVolumeDB()

        self.crawl_complete_q = crawl_complete_q

        self._path = os.path.join(os.getcwd(), "highest_invest_fund_volume_of_today" + os.sep)
        self.today_date = datetime.datetime.today().strftime('%Y%m%d%H%M')

    def stop(self):
        self.stopped.set()

    def is_today_highest(self, stock_code):
        all_volume_history = self.db.get_volume_history(stock_code)
        if not all_volume_history:
            return False

        latest_data = all_volume_history.pop(0)
        latest_volume = latest_data[1]
        latest_date = latest_data[0]

        date_volume_dict = dict()
        for date, volume in all_volume_history:
            date_volume_dict.setdefault(date, volume)

        date_volume_dict = dict(map(reversed, date_volume_dict.items()))
        volume_list = list(date_volume_dict.keys())

        if volume_list:
            max_volume = max(volume_list)
            if latest_volume > max_volume:
                if max_volume == 0:
                    volume_power = 1
                    self.logger.info('{} - 최고투신수량을 기록했습니다, 이전 매수 기록 없음, 최신 : {} - {}'.format(stock_code, latest_date, latest_volume))
                elif max_volume > 0:
                    volume_power = latest_volume / max_volume
                    last_max_volume_date = date_volume_dict[max_volume]
                    self.logger.info('{} - 최고투신수량을 기록했습니다, 최신 : {} - {}, 이전 : {} - {}'.format(stock_code, latest_date, latest_volume, last_max_volume_date, max_volume))
                else:
                    return False
                return volume_power
        else:
            if not latest_volume == 0:
                volume_power = 1
                self.logger.info('{} - 최고투신수량을 기록했습니다, 이전 매수 기록 없음, 최신 : {} - {}'.format(stock_code, latest_date, latest_volume))
                return volume_power
        return False

    def run(self):
        file_name = self.today_date + '.xlsx'

        xlsx_module = XlsxModule(self._path + file_name, new=True)
        xlsx_module.export_xlsx_to_row(('종목코드', '매수강도'))

        while True:
            try:
                stock_code = self.crawl_complete_q.get(timeout=1)
            except Exception:
                if self.stopped.is_set():
                    return
                continue

            is_today_highest = self.is_today_highest(stock_code)
            if is_today_highest:
                volume_power = is_today_highest
                data_to_export = (stock_code, volume_power)
                try:
                    xlsx_module.export_xlsx_to_row(data_to_export)
                except Exception as e:
                    self.logger.debug('xlsx_module export error: {}'.format(str(e)))
                    self.crawl_complete_q.put(stock_code)
