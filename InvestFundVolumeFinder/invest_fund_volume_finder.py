import queue
import time
import threading
import multiprocessing

from StockApis.kiwoom import KiwoomAPIModule
from PyQt5.QAxContainer import *
from PyQt5 import QtCore, QtWidgets

from InvestFundVolumeFinder.invest_fund_volume_db import InvestFundVolumeDB
from InvestFundVolumeFinder.xlsx_data_input_agent import XlsxDataInputAgent

from Util.debugger import *


MAX_COUNT = 650
MAX_ITERATION_COUNT = 3
WAIT_TIME_PER_REQUEST = 0.7
MAX_LOGIN_WAIT_TIME = 300
MAX_REQUEST_WAIT_TIME = 20


path = 'highest_invest_fund_volume_of_today'
os.makedirs(path, exist_ok=True)


class KiwoomInvestFundVolumeFinder(QtWidgets.QMainWindow):
    def __init__(self, collected, stock_codes_q, crawl_complete_q):

        super(KiwoomInvestFundVolumeFinder, self).__init__()
        self.stock_codes_q = stock_codes_q
        self.crawl_complete_q = crawl_complete_q
        self.stock_codes_collected = collected

        self.kiwoom_volume_finder_thread = KiwoomVolumeFinderThread(self.stock_codes_collected, self.stock_codes_q, self.crawl_complete_q)
        self.kiwoom_volume_finder_thread.finished.connect(self.close_main_window)

        debugger.debug('{}, Starts'.format(self.kiwoom_volume_finder_thread.__str__()))
        self.kiwoom_volume_finder_thread.start()

    def close_main_window(self):
        self.close()


class KiwoomVolumeFinderThread(QtCore.QThread):
    finished = QtCore.pyqtSignal()

    def __init__(self, collected, stock_codes_q, crawl_complete_q):
        super(KiwoomVolumeFinderThread, self).__init__()
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.kiwoom.dynamicCall("CommConnect()")
        self.kiwoom_api = KiwoomAPIModule(self.kiwoom)

        self.stock_codes_q = stock_codes_q
        self.crawl_complete_q = crawl_complete_q
        self.stock_codes_collected = collected

        self.stop_flag = False
        self.req_count = 0
        self.db = InvestFundVolumeDB()
        self.today_date = datetime.datetime.today().date()
        req_date = self.today_date.strftime('%Y%m%d')
        debugger.debug('req_date - {}'.format(req_date))

        self.connections()

    def __str__(self):
        return 'KiwoomVolumeFinderThread'

    def connections(self):
        self.kiwoom.OnReceiveTrData.connect(self.kiwoom_api.receive_tx_data)
        self.kiwoom.OnEventConnect.connect(self.kiwoom_api.connect_status_receiver)

    def filter_outdated_history(self, stock_code):
        db_date_list = list()
        for date_, _ in self.db.get_volume_history(stock_code):
            date_ = datetime.datetime.strptime(date_, '%Y%m%d').date()
            db_date_list.append(date_)

        if db_date_list:
            for _ in db_date_list[:]:
                oldest_date = min(db_date_list)
                if oldest_date < self.today_date - datetime.timedelta(days=365):
                    oldest_date_to_remove = oldest_date.strftime('%Y%m%d')
                    self.db.remove_volume_history_by_date(oldest_date_to_remove)
                else:
                    break
                db_date_list.remove(oldest_date)
        return db_date_list

    def request_invest_fund_volume(self, stock_code):
        db_date_list = self.filter_outdated_history(stock_code)

        if db_date_list:
            latest_date = max(db_date_list)
        else:
            latest_date = None

        req_date = self.today_date.strftime('%Y%m%d')

        stop_iter = False
        volume_history_list = list()

        for i in range(MAX_ITERATION_COUNT):
            try:
                res = self.kiwoom_api.get_invest_fund_volume(req_date, stock_code)
            except queue.Empty:
                self.stock_codes_q.put(stock_code)
                return False

            # if there is no data on first request it is due to TR restriction
            if not res and i == 0:
                self.stock_codes_q.put(stock_code)
                return False

            self.req_count += 1

            datetime_list = sorted(list(res.keys()), reverse=True)
            if not datetime_list:
                break

            latest_res_date = datetime_list[0]
            debugger.debug('{}, latest response date from kiwoom api : {}'.format(stock_code, latest_res_date))

            # save {<date>: value} pair to the db
            for date in datetime_list:
                if self.today_date - datetime.timedelta(days=365) > date:
                    stop_iter = True
                    break
                elif latest_date:
                    if latest_date > date:
                        stop_iter = True
                        break

                quantity = res[date]
                date_string = date.strftime('%Y%m%d')

                history_set = (stock_code, date_string, quantity)
                volume_history_list.append(history_set)

            # request date update for next iteration
            req_date = (min(datetime_list) - datetime.timedelta(days=1)).strftime('%Y%m%d')
            time.sleep(WAIT_TIME_PER_REQUEST)

            if stop_iter:
                break

        if volume_history_list:
            # save chunk data set in db
            self.db.add_volume_history(volume_history_list)

        self.crawl_complete_q.put(stock_code)
        return True

    def run(self):
        for _ in range(MAX_LOGIN_WAIT_TIME):
            if not self.kiwoom_api.is_connected:
                time.sleep(1)
                continue
            break

        # to put stock codes only one time
        # the value is None at the first time
        if not self.stock_codes_collected:
            all_stock_codes = self.get_all_stock_codes()
            for stock_code in sorted(all_stock_codes):
                self.stock_codes_q.put(stock_code)

        result_q = queue.Queue()
        get_all_volume_data_thread = threading.Thread(target=self.get_all_invest_fund_volume_thread,
                                                      args=(result_q,),
                                                      daemon=True)
        get_all_volume_data_thread.start()

        while not self.stop_flag:
            try:
                success_flag = result_q.get(timeout=MAX_REQUEST_WAIT_TIME)
            except queue.Empty:
                debugger.debug('Request has been rejected, too many requests')
                success_flag = False

            if not success_flag:
                break

        debugger.debug('{}, Closed.'.format(self.__str__()))
        self.finished.emit()

    def get_all_invest_fund_volume_thread(self, result_q):
        while True:
            try:
                stock_code = self.stock_codes_q.get(timeout=10)
            except queue.Empty:
                debugger.debug('No more stock codes left')
                success_flag = False
                result_q.put(success_flag)
                break

            if stock_code:
                res = self.request_invest_fund_volume(stock_code)
                if not res:
                    success_flag = False
                    result_q.put(success_flag)
                    break
                success_flag = True
                result_q.put(success_flag)
                debugger.info('{}, 투신정보를 성공적으로 가져왔습니다.'.format(stock_code))

            debugger.debug('req_count : {}'.format(self.req_count))
            if self.req_count > MAX_COUNT:
                debugger.debug('req_count - {}, Exceeded max request count'.format(self.req_count))
                success_flag = False
                result_q.put(success_flag)
                break

    def get_all_stock_codes(self):
        debugger.info("전체 종목 수집합니다.")
        self.all_stock_codes = set(self.kiwoom_api.get_kospi_stock_codes() + self.kiwoom_api.get_kosdaq_stock_codes())
        debugger.debug(len(self.all_stock_codes))
        debugger.info("전체 종목 수집완료.")

        return list(self.all_stock_codes)

    def stop(self):
        self.stop_flag = True


def run_in_process(collected, stock_q, crawl_complete_q):
    try:
        app = QtWidgets.QApplication([])
        kiwoom_invest_fund_volume_finder = KiwoomInvestFundVolumeFinder(collected, stock_q, crawl_complete_q)
        app.exec_()
    except:
        debugger.exception("FATAL")
        debugger.info('개발자에게 모든 로그를 보내주세요!')


if __name__ == '__main__':
    multiprocessing.freeze_support()

    try:
        current_time = datetime.datetime.now()

        continue_flag = True
        if current_time.hour + current_time.minute / 60 < 15.5:
            continue_msg = input('아직 장 마감이 안되어 과거 데이터가 출력 될 수 있습니다. 계속 하시겠습니까? (Y/N)')
            continue_flag = continue_msg.upper() == 'Y'

        if continue_flag:
            stock_codes_collected = False
            shared_manager = multiprocessing.Manager()

            stock_codes_queue = shared_manager.Queue()
            crawl_complete_queue = shared_manager.Queue()

            xlsx_data_input_agent = XlsxDataInputAgent(crawl_complete_queue, debugger)
            xlsx_data_input_agent.start()
            # pydevd.settrace(suspend=False, trace_only_current_thread=True)

            while True:
                p = multiprocessing.Process(target=run_in_process, args=(stock_codes_collected, stock_codes_queue, crawl_complete_queue), daemon=True)
                p.start()
                p.join()

                stock_codes_collected = True
                if stock_codes_queue.empty():
                    debugger.info('작업을 완료하여 프로그램이 종료됩니다')
                    xlsx_data_input_agent.stop()
                    break
    except Exception:
        debugger.exception("FATAL")
        debugger.info("개발자에게 logs 폴더를 압축하여 보내주세요!")
    finally:
        os.system("PAUSE")
        debugger.debug("DONE")
