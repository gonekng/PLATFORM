import time, sys, os
import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains

# 접속 및 크롤링
def crawl(driver):

    # ------------------------------------------ 1. 크롤링 시작 ------------------------------------------
    print("\n크롤링 시작")
    try:
        # PEDSIS 접속
        driver.get("https://www.pedsis.co.kr//htmlPage.do?p_html_page=cmmn/login")

        # 로그인
        input_id = driver.find_element(By.CSS_SELECTOR, "input.mgt2.login_id")
        input_pw = driver.find_element(By.CSS_SELECTOR, "input.mgt3.login_passw")
        input_id.send_keys('BIGBANG')
        input_pw.send_keys('big0076')
        login_box = driver.find_element(By.XPATH, "//a[@class='intro_btn_login fr']")
        login_box.click()
        time.sleep(1)

        # 경고창
        driver.get("https://www.pedsis.co.kr/htmlPage.do?p_html_page=cmmn/mainFrame")
        alert = driver.switch_to.alert
        alert.accept()

        # 팝업창 닫기
        popups = driver.window_handles
        for i in popups:
            if i != popups[0]:
                driver.switch_to.window(i)
                driver.close()
        driver.switch_to.window(popups[0])

        # 비밀번호 다음에 변경
        time.sleep(1)
        driver.switch_to.frame('mainFrame')
        driver.execute_script("fn_passwordSession('N')")

        # 조회 화면 접근
        time.sleep(1)
        driver.switch_to.default_content()
        driver.switch_to.frame('topFrame')
        driver.execute_script("doLeftMain('10004')")

        driver.switch_to.default_content()
        driver.switch_to.frame('leftFrame')
        driver.execute_script("goMenu('https://biweb.pedsis.co.kr/analytics/saw.dll?Dashboard&PortalPath=%2Fshared%2F%EA%B5%AD%EB%82%B4%EC%86%8C%EB%B9%84%2F_portal%2F%EA%B5%AD%EB%82%B4%EC%86%8C%EB%B9%84%ED%98%84%ED%99%A9_10227&page=%EA%B5%AD%EB%82%B4%EC%86%8C%EB%B9%84%ED%98%84%ED%99%A9', 'D', '1', '10227')")

        time.sleep(1)
        driver.switch_to.default_content()
        driver.switch_to.frame('mainFrame')
    except Exception as e:
        exc_type, exe_obj, exc_tb = sys.exc_info()
        error_lst.append([exc_type, exc_tb.tb_lineno])
        print("----------ERROR OCCURED----------")
        print(exc_type, exc_tb.tb_lineno)
        print("---------------------------------")
    
    # print_list1(driver)
    # print_list2(driver)
    # print_list3(driver)

    # ------------------------------------------ 2. 데이터 조회 ------------------------------------------
    global input_df, input_lst, label_lst, data_lst, value_lst

    input_df = pd.read_csv("pedsis_input.csv", encoding='euc-kr')
    label_lst = ["시작년도", "시작월", "종료년도", "종료월", "단위", "시도", "시군구", "수요처", "제품(중)", "제품(소)", "산업(대)", "산업(중)", "산업(소)"]

    for idx in range(len(input_df)):
        print("\n========================================================\n", idx+1, ":")

        # 활동자료 종류 : [대분류, 중분류, 소분류, 활동자료]
        data_lst = input_df.iloc[idx, 0].split("_")
        range_lst = set_range()
        
        # 조회할 조건
        input_lst = [
                        # 기간(시작년도,시작월,종료년도,종료월)
                        (range_lst[0] - 2024) * (-1), 0, (range_lst[1] - 2024) * (-1), 11,
                        # 단위
                        int(input_df.iloc[idx,1]), 
                        # 지역(시도, 시군구)
                        range_lst[2], range_lst[3], 0, 
                        # 제품(중분류, 소분류)
                        int(input_df.iloc[idx,2]), int(input_df.iloc[idx,3]),
                        # 산업(대분류, 중분류, 소분류)
                        int(input_df.iloc[idx,4]), int(input_df.iloc[idx,5]), [int(input_df.iloc[idx,6]), int(input_df.iloc[idx,7]), int(input_df.iloc[idx,8]), int(input_df.iloc[idx,9])]
                    ]
        value_lst = ["" for _ in range(13)]

        try:
            # 조회
            search(driver)
            
            # 조회 결과 출력
            errorinfo = driver.find_elements(By.XPATH, "//td[@class='ErrorInfo']")
            is_result = len(errorinfo) == 0
            if is_result:
                print("\n결과 조회 중...")
            else:
                print("\n", errorinfo[0].text)
            if idx == 0:
                df_result = convert_df(driver, is_result, idx)
            else:
                df_result = pd.concat(df_result, convert_df(driver, is_result, idx))
        except Exception as e:
            exc_type, exe_obj, exc_tb = sys.exc_info()
            error_lst.append([exc_type, exc_tb.tb_lineno])
            print("----------ERROR OCCURED----------")
            print(exc_type, exc_tb.tb_lineno)
            print("---------------------------------")

    # ------------------------------------------ 3. 데이터 저장 ------------------------------------------
    try:
        if not os.path.exists('PEDSIS_DATA/'):
            os.makedirs('PEDSIS_DATA/')
        else:
            if not os.path.exists(f"PEDSIS_DATA/{value_lst[5]}_{value_lst[6]}_({value_lst[0]}-{value_lst[2]}).csv".replace(" ", "")):
                df_result.to_csv(f"PEDSIS_DATA/{value_lst[5]}_{value_lst[6]}_({value_lst[0]}-{value_lst[2]}).csv".replace(" ", ""), mode='w', encoding='euc-kr')
            else:
                df_result.to_csv(f"PEDSIS_DATA/{value_lst[5]}_{value_lst[6]}_({value_lst[0]}-{value_lst[2]}).csv".replace(" ", ""), mode='a', encoding='euc-kr', header=False)
    except Exception as e:
        exc_type, exe_obj, exc_tb = sys.exc_info()
        error_lst.append([exc_type, exc_tb.tb_lineno])
        print("----------ERROR OCCURED----------")
        print(exc_type, exc_tb.tb_lineno)
        print("---------------------------------")

    print("크롤링 종료\n")
    return 0

def print_list1(driver):
    
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.XPATH, f"//img[@class='{'promptComboBoxButtonMoz'}' or @class='{'promptDropDownButton'}']"))
    )[5].click()
    time.sleep(1)
    lst = WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']/div"))
    )
    time.sleep(1)
    for i in range(1, len(lst)-1):
        print(lst[i].get_attribute('title'))
        lst[i].click()
        time.sleep(1)
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, f"//img[@class='{'promptComboBoxButtonMoz'}' or @class='{'promptDropDownButton'}']"))
        )[6].click()
        time.sleep(1)
        lst2 = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']/div"))
        )

        for j in range(len(lst2)):
            if j==1:
                continue
            print("\t", lst2[j].get_attribute('title'))
            lst2 = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']/div"))
            )
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, f"//img[@class='{'promptComboBoxButtonMoz'}' or @class='{'promptDropDownButton'}']"))
        )[5].click()
        time.sleep(1)
        lst = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']/div"))
        )

def print_list2(driver):
    
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.XPATH, f"//img[@class='{'promptComboBoxButtonMoz'}' or @class='{'promptDropDownButton'}']"))
    )[8].click()
    time.sleep(1)
    lst = WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']/div"))
    )
    time.sleep(1)
    for i in range(len(lst)):
        print(lst[i].get_attribute('title'))
        lst[i].click()
        time.sleep(1)
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, f"//img[@class='{'promptComboBoxButtonMoz'}' or @class='{'promptDropDownButton'}']"))
        )[9].click()
        time.sleep(1)
        lst2 = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']/div"))
        )

        for j in range(len(lst2)):
            print("\t", lst2[j].get_attribute('title'))
            lst2 = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']/div"))
            )
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, f"//img[@class='{'promptComboBoxButtonMoz'}' or @class='{'promptDropDownButton'}']"))
        )[8].click()
        time.sleep(1)
        lst = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']/div"))
        )

def print_list3(driver):
    
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.XPATH, f"//img[@class='{'promptComboBoxButtonMoz'}' or @class='{'promptDropDownButton'}']"))
    )[10].click()
    time.sleep(1)
    lst = WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']/div"))
    )
    time.sleep(1)
    for i in range(len(lst)):
        print(lst[i].get_attribute('title'))
        if i==0:
            continue
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']/div"))
        )[i].click()
        time.sleep(1)
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, f"//img[@class='{'promptComboBoxButtonMoz'}' or @class='{'promptDropDownButton'}']"))
        )[11].click()
        time.sleep(1)
        lst2 = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']/div"))
        )

        for j in range(len(lst2)):
            print("\t", lst2[j].get_attribute('title'))
            if j==0:
                continue
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']//input[@class='checkboxRadioButton']"))
            )[j-1].click()
            time.sleep(1)
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']//input[@class='checkboxRadioButton']"))
            )[j].click()
            time.sleep(2)
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, f"//img[@class='{'promptComboBoxButtonMoz'}' or @class='{'promptDropDownButton'}']"))
            )[12].click()
            time.sleep(1)
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, f"//img[@class='{'promptComboBoxButtonMoz'}' or @class='{'promptDropDownButton'}']"))
            )[12].click()
            time.sleep(1)
            lst3 = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']/div"))
            )
            for k in range(len(lst3)):
                print("\t\t", lst3[k].get_attribute('title'))
                lst3 = WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']/div"))
                )
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, f"//img[@class='{'promptComboBoxButtonMoz'}' or @class='{'promptDropDownButton'}']"))
            )[11].click()
            time.sleep(1)
            lst2 = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']/div"))
            )
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, f"//img[@class='{'promptComboBoxButtonMoz'}' or @class='{'promptDropDownButton'}']"))
        )[10].click()
        time.sleep(1)
        lst = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']/div"))
        )

# 분석범위 설정
def set_range():
    s_year = int(input('# 시작년도 : '))
    e_year = int(input('# 종료년도 : '))

    df_region = pd.DataFrame({
        '광역지자체' : ['서울특별시','부산광역시','대구광역시','인천광역시','광주광역시','대전광역시','울산광역시','경기도','강원도','충청북도','충청남도','전라북도','전라남도','경상북도','경상남도','제주특별자치도','세종특별자치시'],
        '기초지자체' : [
                        ['전체', '종로구', '중구', '동대문구', '성동구', '성북구', '도봉구', '서대문구', '은평구', '마포구', '용산구', '영등포구', '동작구', '강남구', '강동구', '강서구', '구로구', '관악구', '노원구', '양천구', '중랑구', '서초구', '송파구', '광진구', '강북구', '금천구'],
                        ['전체', '중구', '서구', '동구', '영도구', '부산진구', '동래구', '남구', '북구', '해운대구', '사하구', '강서구', '금정구', '연제구', '수영구', '사상구', '기장군'],
                        ['전체', '중구', '동구', '서구', '남구', '북구', '수성구', '달서구', '달성군'],
                        ['전체', '중구', '동구', '미추홀구', '부평구', '서구', '남동구', '연수구', '계양구', '강화군', '옹진군'],
                        ['전체', '동구', '서구', '북구', '광산구', '남구'],
                        ['전체', '동구', '중구', '서구', '유성구', '대덕구'],
                        ['전체', '중구', '남구', '동구', '북구', '울주군'],
                        ['전체', '수원시', '성남시', '의정부시', '안양시', '부천시', '동두천시', '광명시', '이천시', '평택시', '구리시', '과천시', '안산시', '오산시', '의왕시', '군포시', '시흥시', '남양주시', '하남시', '고양시', '용인시', '양주시', '여주시', '화성시', '파주시', '광주시', '연천군', '포천시', '가평군', '양평군', '안성시', '김포시'],
                        ['전체', '춘천시', '원주시', '강릉시', '속초시', '동해시', '태백시', '삼척시', '홍천군', '횡성군', '영월군', '평창군', '정선군', '철원군', '화천군', '양구군', '인제군', '고성군', '양양군'],
                        ['전체', '청주시', '충주시', '제천시', '보은군', '옥천군', '영동군', '진천군', '괴산군', '음성군', '단양군', '증평군'],
                        ['전체', '천안시', '공주시', '아산시', '보령시', '서산시', '논산시', '계룡시', '금산군', '부여군', '서천군', '청양군', '홍성군', '예산군', '당진시', '태안군'],
                        ['전체', '전주시', '군산시', '익산시', '남원시', '정읍시', '김제시', '완주군', '진안군', '무주군', '장수군', '임실군', '순창군', '고창군', '부안군'],
                        ['전체', '목포시', '여수시', '순천시', '나주시', '광양시', '담양군', '곡성군', '구례군', '고흥군', '보성군', '화순군', '장흥군', '강진군', '해남군', '영암군', '무안군', '함평군', '영광군', '장성군', '완도군', '진도군', '신안군'],
                        ['전체', '포항시', '경주시', '김천시', '영주시', '영천시', '안동시', '구미시', '문경시', '상주시', '경산시', '군위군', '의성군', '청송군', '영양군', '영덕군', '청도군', '고령군', '성주군', '칠곡군', '예천군', '봉화군', '울진군', '울릉군'],
                        ['전체', '창원시', '진주시', '통영시', '사천시', '김해시', '밀양시', '거제시', '양산시', '의령군', '함안군', '창녕군', '고성군', '남해군', '하동군', '산청군', '함양군', '거창군', '합천군'],
                        ['전체', '제주시', '서귀포시'],
                        ['전체']
                    ]
    })
    while True:
        try:
            sido = df_region.loc[df_region['광역지자체'] == input('# 광역지자체 : ')].index[0]
            sigungu = df_region.loc[sido, '기초지자체'].index(input('# 기초지자체 : '))
            break
        except Exception as e:
            exc_type, exe_obj, exc_tb = sys.exc_info()
            print("----------ERROR OCCURED----------")
            print(exc_type, exc_tb.tb_lineno)
            print("---------------------------------")
            print("잘못된 입력입니다. 다시 입력해주세요.")

    return [s_year, e_year, sido, sigungu]

# 데이터 조회
def search(driver):

    print("\n### 조회 조건")
    for i in range(len(label_lst)):
        try:
            if(i == 7):
                value_lst[7] = "전체"
                continue
            else:
                time.sleep(1)

                # 드롭다운 버튼 클릭
                elements = WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.XPATH, f"//img[@class='{'promptComboBoxButtonMoz'}' or @class='{'promptDropDownButton'}']"))
                )
                elements[i].click()

                if(i == 12):
                    time.sleep(2)
                    elements = WebDriverWait(driver, 20).until(
                        EC.presence_of_all_elements_located((By.XPATH, f"//img[@class='{'promptComboBoxButtonMoz'}' or @class='{'promptDropDownButton'}']"))
                    )
                    elements[i].click()
                
                # 조건에 해당하는 항목 찾기
                time.sleep(3)
                dd_lst = WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']/div"))
                )
                if(i==12):
                    num_lst = []
                    for num in input_lst[12]:
                        if num != 0:
                            if num < len(dd_lst):
                                num_lst.append(dd_lst[num].get_attribute('title'))
                        else:
                            num_lst.append("전체")
                            break
                    value_lst[12] = num_lst
                else:
                    if input_lst[i] < len(dd_lst):
                        num = input_lst[i]
                    else:
                        print("해당하는 인덱스가 없습니다.")
                        num = 0
                    value_lst[i] = (dd_lst[num].get_attribute('title'))
                
                # 드롭다운 리스트 선택
                if(i in [6,9,11,12]):
                    if(num != 0):
                        WebDriverWait(driver, 20).until(
                            EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']//input[@class='checkboxRadioButton']"))
                        )[0].click()
                        time.sleep(2)
                        
                        if(i==12):
                            for num in input_lst[12]:
                                if num < len(dd_lst):
                                    WebDriverWait(driver, 20).until(
                                            EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']//input[@class='checkboxRadioButton']"))
                                    )[num].click()
                        else:
                            WebDriverWait(driver, 20).until(
                                    EC.presence_of_all_elements_located((By.XPATH, "//*[@class='floatingWindowDiv']/div/div[@class='DropDownValueList']//input[@class='checkboxRadioButton']"))
                            )[num].click()
                else:
                    dd_lst[num].click()
                
                print(label_lst[i], " : ", value_lst[i])
        except Exception as e:
            exc_type, exe_obj, exc_tb = sys.exc_info()
            error_lst.append([exc_type, exc_tb.tb_lineno])
            print("----------ERROR OCCURED----------")
            print(exc_type, exc_tb.tb_lineno)
            print("---------------------------------")

    # 조회 버튼 클릭
    time.sleep(2)
    search_button = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//*[@id='gobtn']"))
    )
    search_button.click()

# 조회 결과 저장
def convert_df(driver, is_result, idx):

    years = []
    months = []
    values = []

    action = ActionChains(driver)
    if is_result:
        # 결과 테이블 접근
        time.sleep(2)
        row_header = WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='PTRowHdr']//td[@class='PTRHC0 OOCT']/table/tbody/tr/td")))
        for i in range(len(row_header)):
            try:
                # 소비년월 데이터 가져오기
                row_header = WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='PTRowHdr']//td[@class='PTRHC0 OOCT']/table/tbody/tr/td")))
                action.move_to_element(row_header[i]).perform() # 스크롤
                time.sleep(0.1)

                year = row_header[i].text[:4]
                month = row_header[i].text[-2:]
                years.append(int(year)) if year != "" else years.append(year)
                months.append(int(month)) if month != "" else months.append(month)

                # 소비량 데이터 가져오기
                data_body = WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//td[@class='PTDT OORT']"))
                )
                action.move_to_element(data_body[i]).perform()
                time.sleep(0.1)

                value = data_body[i].text.replace(",","")
                values.append(int(value)) if value != "" else values.append(value)

                print(f'\r {i+1}행 가져옴', end='')
            except Exception as e:
                exc_type, exe_obj, exc_tb = sys.exc_info()
                error_lst.append([exc_type, exc_tb.tb_lineno])
                print("----------ERROR OCCURED----------")
                print(exc_type, exc_tb.tb_lineno)
                print("---------------------------------")
    else:
        years = [_ for _ in range(int(value_lst[0]), int(value_lst[2])+1)]
        months = [1 for _ in range(int(value_lst[0]), int(value_lst[2])+1)]
        values = [0 for _ in range(int(value_lst[0]), int(value_lst[2])+1)]

    # 데이터 가공 및 출력
    print("\n\n### 조회 결과")
    df = pd.DataFrame(zip(years, months, values), columns=['연도', '월', '소비량'])
    df_sum = df.groupby('연도')['소비량'].sum().reset_index()
    for y in range(int(value_lst[0]), int(value_lst[2])+1):
        if y not in years:
            df_sum.loc[len(df_sum)] = {'연도':y, '소비량':0}
    df_sum.sort_values('연도', inplace=True, ignore_index=True)

    df_sum = df_sum.transpose()
    df_sum.rename(columns=df_sum.iloc[0], inplace=True)
    df_sum.drop(df_sum.index[0], inplace=True)

    df_sum['대분류'] = data_lst[0]
    df_sum['중분류'] = data_lst[1]
    df_sum['소분류'] = data_lst[2]
    df_sum['활동자료'] = data_lst[3]
    df_sum['제품(중)'] = value_lst[8]
    df_sum['제품(소)'] = value_lst[9]
    df_sum['단위'] = value_lst[4]
    
    col1 = df_sum.columns[-7:].to_list()
    col2 = df_sum.columns[:-7].to_list()
    df_sum = df_sum[col1+col2].reset_index(drop=True)
    df_sum = df_sum.rename(index={0:idx})
    print(df_sum)

    return df_sum

def main():
    
    global error_lst
    error_lst = []

    # 브라우저 옵션 설정
    options = Options()
    # options.add_argument('--headless')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    # 브라우저 열기
    browser = webdriver.Chrome("C:/Users/ecoeye/Documents/chromedriver-win64/chromedriver.exe", options=options)
    browser.maximize_window()
    browser.implicitly_wait(10)

    # 크롤링 수행
    crawl(browser)
    browser.close()

    for _ in range(len(error_lst)):
        print(_, ":", error_lst[_])

if __name__ == "__main__":
    main()