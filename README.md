## Kiwoom Invest Fund Volume Finder

**2020.12 ~ 2021.1**

**프로젝트 설명**

*키움 API 를 사용하여 주식종목별 해당일자 기준 52 주 간 가장 높은 금액의*

*기관투자를 받은 주식 종목들을 찾아 엑셀파일로 저장하는 로직을 구현한 프로젝트입니다.*

*Python 으로 구현했습니다.*

**기술스택**

- Python 3,  SQLite

**세부내용**

- Python multiprocessing 의 process 메소드를 통해 일정 API call 횟수를 넘으면 프로그램 process 를 자동으로 재시작 하여 키움 API block 을 우회하는 로직 구현
- 키움 API call block 으로 인한 Deadlock 발생 문제를 막기 위해, 해당 로직을 관리하는 함수를 Thread 생성한 뒤, 해당 Thread 로 부터 일정시간동안 응답이 없으면 프로그램 process 를 자동으로 재시작하는 로직 구현 (Thread 에 대한 응답은 queue 객체로 관리)
- 52주간 데이터를 Bulk Insert 하여 DB 데이터 입력시간 대폭 단축
- 엑셀파일에 write 하는 Thread 를 분리
