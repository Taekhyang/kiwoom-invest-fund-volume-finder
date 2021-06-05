## Kiwoom Invest Fund Volume Finder

**2020.12 ~ 2021.1**

**프로젝트 설명**

*키움 API 를 사용하여 모든 코스피 종목의 데이터를 검색하면서*

*오늘 자 기준 52 주 간 가장 높은 금액의 기관투자를 받은 주식 종목들을 찾아서 해당 종목들을 엑셀파일로 저장하는 로직을 구현한 프로젝트입니다.*

*Python 3 로 구현했습니다.*

**기술스택**

- Python 3,  SQLite

**세부내용**

- Python multiprocessing 의 process 메소드를 통해 일정 API call 횟수를 넘으면 프로그램 process 를 자동으로 재시작 하여 키움 API block 을 우회하는 로직 구현
- 키움 API call block 으로 인한 deadlock 발생 문제를 막기 위해, 해당 문제가 발생할 수 있는 함수가 실행되는 Thread 를 생성한 뒤, 해당 Thread 로 부터 일정시간동안 응답이 없으면 프로그램 process 를 자동으로 재시작하는 로직 구현 (Thread 에 대한 응답은 queue 객체로 관리)
- 52주간 데이터를 Bulk Insert 하여 DB 데이터 입력시간 대폭 단축
- 엑셀파일에 write 하는 Thread 를 분리


**Project Description**

*It is a project that uses the Kiwoom API to search for data on all KOSPI stocks and finds the stocks*

*that received the highest amount of institutional investment for 52 weeks as of today and saves them as Excel files.*

*used Python 3*

**Tech Stack**

- Python 3,  SQLite

**Details**

- Implemented logic that automatically restarts the program process and bypasses the Kiwoom API block when it exceeds a certain number of API calls through the process method of Python multiprocessing.

 - To prevent deadlock issues caused by Kiwoom API call blocks, create a Thread on which the function that could cause the problem runs, and then automatically restart the program process if there is no response from that Thread for a period of time (the response from Thread is managed through a queue object).

- Used Bulk insert data for 52 weeks, dramatically reducing DB data entry time

- added a extra thread for just writing matched tickers in the excel file
