import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from streamlit_option_menu import option_menu
import mysql.connector
from PIL import Image
import base64
import folium
import geopandas as gpd
import warnings
import json
warnings.filterwarnings('ignore')

# -------------------- MYSQL 연동 -------------------- #
# DB 연동
def connect_db():

  # DB 정보 불러오기
    with open("db_info.json", "r") as file:
        data = json.load(file)
    
  # DB 연결하기
    db = mysql.connector.connect(
        **st.secrets["mysql"]
    )

    db2 = mysql.connector.connect(
        **st.secrets["mysql"]
    )
    
    return db, db2

# 활동자료 DB 연결
def get_db1(num, filter=False):

    cat_lst = ["전체", "에너지", "산업공정", "농업", "LULUCF", "폐기물", "간접배출"]
    query_s = 'select cast(c.연도 as char) as 연도, c.시도, c.시군구, a.구분1, a.구분2, a.구분3, a.구분4, a.구분5, b.활동자료1, b.활동자료2, b.활동자료3, b.단위, c.값, c.최신업데이트일, c.업데이트가능여부 '
    query_f = 'from TB_CATEGORY a, TB_ACT_INFO b, TB_ACT_VALUE c '
    query_w = f'where a.id = b.category_id and b.id = c.activity_id and c.연도 >= {st.session_state.input_list[2]} and c.연도 <= {st.session_state.input_list[3]} and c.시도 = "{st.session_state.input_list[0]}" '
    if num != 0:
        query_w = query_w + f' and a.`구분1` = "{cat_lst[num]}"'
    if filter and st.session_state.input_list[1] != "전체":
        query_w = query_w + f' and c.시군구 = "{st.session_state.input_list[1]}"'

    query = query_s + query_f + query_w
    df = pd.read_sql(query, db)
    return df

# 배출량 DB 연결
def get_db2(num, filter=False):

    cat_lst = ["전체", "에너지", "산업공정", "농업", "LULUCF", "폐기물", "간접배출"]
    query_s = 'select cast(b.연도 as char) as 연도, b.시도, b.시군구, a.구분1, a.구분2, a.구분3, a.구분4, a.구분5, b.단위, ROUND(b.배출량, 0) as 배출량, b.최신업데이트일, b.업데이트가능여부 '
    query_f = 'from TB_CATEGORY a, TB_EMIT_VALUE b '
    query_w = f'where a.id = b.category_id and b.연도 >= {st.session_state.input_list[2]} and b.연도 <= {st.session_state.input_list[3]} and b.시도 = "{st.session_state.input_list[0]}"'
    if num != 0:
        query_w = query_w + f' and a.`구분1` = "{cat_lst[num]}"'
    if filter and st.session_state.input_list[1] != "전체":
        query_w = query_w + f' and b.시군구 = "{st.session_state.input_list[1]}"'

    query = query_s + query_f + query_w
    df = pd.read_sql(query, db)
    return df

# 활동자료/배출량 DB 업데이트
def update_db(num):

    cur = db.cursor()
    tb_lst = ['TB_ACT_VALUE', 'TB_EMIT_VALUE']
    cur.execute(f'UPDATE {tb_lst[num]} SET 최신업데이트일 = CURDATE() WHERE 업데이트가능여부 = "가능";')
    cur.execute(f'UPDATE {tb_lst[num]} SET 업데이트가능여부 = "완료" WHERE 최신업데이트일 = curdate();')
    db.commit()

    return 0

# -------------------- 지자체 설정 -------------------- #
# 광역지자체
def get_region_list():
    
  # 지역 데이터 생성
    df = pd.DataFrame({
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

    return df

# 기초지자체
def get_subregion_list(region):
    df_region = get_region_list()
    df_subregion = df_region.loc[df_region['광역지자체']==region, '기초지자체']
    return df_subregion.tolist()

# 지도 이동
def move_map():
    df_region = get_region_list()
    idx1 = df_region.loc[df_region['광역지자체'] == st.session_state.input_list[0],:].index[0]
    idx2 = df_region.loc[idx1, '기초지자체'].index(st.session_state.input_list[1])

    gdf = gpd.read_file(f'./행정구역시군구_경계/LARD_ADM_SECT_SGG_{idx1+1}_{st.session_state.input_list[0]}/LARD_ADM_SECT_SGG.shp', encoding='euc-kr')
    gdf2 = gdf.to_crs(epsg=4326)
    gdf2['center'] = gdf2.representative_point()
    # boundary = [[gdf2.bounds.iloc[0,1],gdf2.bounds.iloc[0,0]],[gdf2.bounds.iloc[0,3],gdf2.bounds.iloc[0,2]]]
    center = (np.median(gdf2['center'].y), np.median(gdf2['center'].x))

    sgg_gdf = gdf.loc[gdf['SGG_NM'].notnull(),:]
    sgg_gdf2 = sgg_gdf.to_crs(epsg=4326)
    target_name = ""

    if idx2 != 0:
        for idx, row in sgg_gdf2.iterrows():
            if st.session_state.input_list[1] == row['SGG_NM']:
                target_name = row['SGG_NM']
                break
        target_gdf = sgg_gdf2.loc[sgg_gdf2['SGG_NM'] == target_name,:]
        target_gdf['center'] = target_gdf.representative_point()
        center = (np.median(target_gdf['center'].y), np.median(target_gdf['center'].x))
        boundary = [[target_gdf.bounds.iloc[0,1],target_gdf.bounds.iloc[0,0]],[target_gdf.bounds.iloc[0,3],target_gdf.bounds.iloc[0,2]]]

    m = folium.Map(location=center, tiles = "CartoDB positron")
    marker = folium.Marker(location=center)
    marker.add_to(m)
    
    # 행정경계 레이어 스타일 설정
    folium.GeoJson(
        sgg_gdf2,
        name='geoJson',
        tooltip=folium.features.GeoJsonTooltip(fields=['SGG_NM'], labels=False, style='font-weight:bold; font-size:15px;'),
        style_function=lambda feature: {
            'color': 'gray', 'weight': 4, 'fillOpacity': 0.1, 'fillColor': 'white',
        }
    ).add_to(m)

    if idx2 !=0:
        m.fit_bounds(boundary)
    else:
        m.fit_bounds(m.get_bounds())

    return m

# -------------------- 페이지 구성 -------------------- #
# 사이드바 설정
def set_sidebar():

    st.sidebar.image(Image.open('./logo.png'), use_column_width = True)
    st.sidebar.title(":green[에코아이] / 환경정보사업팀")
    st.sidebar.write("---")
    
    # 광역지자체 선택
    df_region = get_region_list()
    idx_region = int(df_region[df_region['광역지자체'] == st.session_state.input_list[0]].index[0] if 'input_list' in st.session_state else 0)
    selected_region = st.sidebar.selectbox("광역지자체", df_region['광역지자체'], key='region_select', index=idx_region, label_visibility="collapsed")
    if selected_region != st.session_state.input_list[0]:
        st.session_state.input_list[1] = "전체"
    subregion_list = get_subregion_list(selected_region)

    # 기초지자체 선택
    if selected_region:
        idx_subregion = int(subregion_list[0].index(st.session_state.input_list[1]) if 'input_list' in st.session_state else 0)
        selected_subregion = st.sidebar.selectbox('기초지자체', subregion_list[0], key='subregion_select', index=idx_subregion, label_visibility="collapsed")
    else:
        selected_subregion = None

    # 연도 선택
    year = st.sidebar.slider('연도', min_value=2015, max_value=2022, value=(st.session_state.input_list[2],st.session_state.input_list[3]), label_visibility="collapsed")

    if st.sidebar.button("적용", key="submit_button", use_container_width=True):
        st.session_state.input_list = [selected_region, selected_subregion, year[0], year[1]]
        m = move_map()
#        m.save("map.html")
        st.rerun()

    st.sidebar.write("---")
    st.sidebar.write(f'➡️ **{st.session_state.input_list[0]} {st.session_state.input_list[1]} ({st.session_state.input_list[2]}년 ~ {st.session_state.input_list[3]}년)**', unsafe_allow_html=True)
    if st.sidebar.button("초기화", key="refresh_button", use_container_width=True):
        st.session_state.input_list = ['서울특별시', '전체', 2015, 2022]
        m = move_map()
#        m.save("map.html")
        st.rerun()

# 홈페이지
def get_home():

    st.write(f'<div style="font-size: 120px; font-weight: bold; text-align: center; height:150px;"> ECOEYE DATA PLATFORM </div>', unsafe_allow_html=True)
    st.write("---")
    selected = option_menu(
        menu_title = None,
        options = ["온실가스 배출량 데이터 시스템", "산업 데이터 시스템", "ESG 데이터 시스템"],
        icons = ['bar-chart', 'wrench', 'building'],
        orientation = 'horizontal',
        styles={
            "container": {"padding":"0!important", "background-color": "#fafafa"},
            "icon": {"color": "red", "font-size": "22px"}, 
            "nav-link": {"font-size": "22px", "text-align": "center", "margin":"0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "green"},
            }
    )
    if selected == "온실가스 배출량 데이터 시스템":
        description = "에코아이에서 자체 산정한 지역별 온실가스 배출량 데이터와<br>주요 통계지표를 결합한 데이터 분석 및 시각화 서비스를 제공합니다."
        img = './eco.jpg'
    elif selected == "산업 데이터 시스템":
        description = ""
        img = './ind.jpg'
    elif selected == "ESG 데이터 시스템":
        description = ""
        img = './esg.jpg'

    with open(img, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    st.markdown(
        f"""
        <div style="color: #404040; font-size: 20px; font-weight: bold; text-align: center; height:350px; margin: 10px 0px 30px 0px;
                    background-image: url(data:image/{"png"};base64,{encoded_string.decode()}); background-position: center;
                    background-size: 100% auto; background-repeat: no-repeat;">
            <br><br>
            <p style="font-size: 50px; font-weight: bold;">{selected}</p>
            ㅡ<br>
            <p style="font-size: 30px;">{description}</p>
        </div>
        """, unsafe_allow_html=True
    )
    col1, col2, col3 = st.columns([2,1,2])
    with col2:
        if selected == "온실가스 배출량 데이터 시스템" and st.button("**Start!**", use_container_width=True):
            if st.session_state.member == None:
                st.error('로그인 후 사용 가능합니다.', icon="⚠️")
            else:
                st.session_state.page = 0
                st.rerun()

# 회원가입 페이지
def get_join_page():
    st.write(f'<div style="font-size: 70px; font-weight: bold; height:90px;"> 회원가입 </div>', unsafe_allow_html=True)
    st.write("---")
    with st.form(key='join_form'):
        id = st.text_input(label='***아이디**')
        pw = st.text_input(label='***비밀번호**')
        name = st.text_input(label='***이름**')
        gender = st.selectbox('**성별**', ['남', '여'])
        age = st.text_input(label='**나이**')
        email = st.text_input(label='**이메일**')
        st.write(f'<div style="font-size: 15px; text-align: right;"> * 필수 항목 </div>', unsafe_allow_html=True)
        st.write("---")
        join_button = st.form_submit_button(label='회원가입')
    if join_button:
        if pd.read_sql(f"select count(*) from `member` where id = '{id}';", db2).iloc[0,0] == 0:
            cur = db2.cursor()
            cur.execute(f"INSERT INTO `MEMBER` VALUES ('{id}', '{pw}', '{name}', '{gender}', {age}, '{email}', 0, 0, now(), null);")
            db2.commit()
            temp = pd.read_sql(f"select * from `member` where id = '{id}' and pw = '{pw}' and deleteYn = 0;", db2)
            st.session_state.member = temp.iloc[0,:].tolist()
            st.success('회원가입이 완료되었습니다.', icon="✅")
            time.sleep(2)
            st.session_state.page = 10
            st.rerun()
        else:
            st.error('이미 존재하는 아이디입니다.', icon="⛔")

# 로그인 페이지
def get_login_page():
    st.write(f'<div style="font-size: 70px; font-weight: bold; height:90px;"> LOGIN </div>', unsafe_allow_html=True)
    st.write("---")
    with st.form(key='login_form'):
        id_input = st.text_input(label='**아이디를 입력하세요.**')
        pw_input = st.text_input(label='**비밀번호를 입력하세요.**')
        st.write("---")
        login_button = st.form_submit_button(label='로그인')
    if login_button:
            temp = pd.read_sql(f"select * from `member` where id = '{id_input}' and pw = '{pw_input}' and deleteYn = 0;", db2)
            if len(temp) != 0:
                st.session_state.member = temp.iloc[0,:].tolist()
                st.success('로그인 되었습니다.', icon="✅")
                time.sleep(2)
                st.session_state.page = 10
                st.rerun()
            else:
                st.error('아이디 또는 비밀번호를 잘못 입력하였습니다.', icon="⛔")

# 마이페이지
def get_mypage():
    st.write(f'<div style="font-size: 70px; font-weight: bold; height:90px;"> 마이페이지 </div>', unsafe_allow_html=True)
    st.write("---")
    st.header("나의 회원정보")
    col1, col2, col3, col4, col5, col6 = st.columns([1.5,1.5,1,1,3.5,2])
    col1.metric("아이디", st.session_state.member[0])
    col2.metric("이름", st.session_state.member[2])
    col3.metric("성별", st.session_state.member[3])
    col4.metric("나이", st.session_state.member[4])
    col5.metric("이메일", st.session_state.member[5])
    col6.metric("가입일자", f'{st.session_state.member[8]}'[:10])
    if st.session_state.member[6]:
        st.write("---")
        df = pd.read_sql(f"select * from `member` where deleteYn = 0;", db2)
        df = df[['id', 'name', 'gender', 'age', 'email', 'managerYn', 'regDate']]
        df.columns = ['아이디', '이름', '성별', '나이', '이메일', '관리자여부', '가입일자']
        st.header("회원목록")
        st.dataframe(df, use_container_width=True)

# 메인 페이지
def get_page_0():
    st.title("온실가스 배출량 데이터 시스템")
    st.write("---")

    col1, col2, col3 = st.columns([1,0.01,1])
    with col1:
        m = move_map()
        m.save("map.html")
        st.components.v1.html(open("map.html", "r", encoding="utf-8").read(), height=550)
    with col3:
        st.write('<div style="font-size: 30px; font-weight: bold; margin: 20px 0px 50px 0px; text-align: center;"> " 지역 기반 온실가스 배출량 데이터 시스템 " </div>', unsafe_allow_html=True)
        st.image(Image.open('./main_info.png'), use_column_width=True)
        st.write('<div style="font-size: 20px; margin: 30px 0px 50px 0px; text-align: center;"> 에코아이에서 자체 산정한 지역별 <b>온실가스 배출량 데이터</b>와 <br> 주요 통계지표를 결합한 <b>데이터 분석 및 시각화 서비스</b>를 제공합니다. </div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            go_1 = st.button("활동자료 DB >", key="go_1_button", use_container_width=True)
            if go_1:
                st.session_state.page = 1
                st.rerun()
        with c2:
            go_2 = st.button("배출량 DB >", key="go_2_button", use_container_width=True)
            if go_2:
                st.session_state.page = 2
                st.rerun()
        with c3:
            go_3 = st.button("분석 시각화 >", key="go_3_button", use_container_width=True)
            if go_3:
                st.session_state.page = 3
                st.rerun()
    st.write("---")

# 활동자료 페이지
def get_page1():
    st.title("활동자료 DB :orange[(Sample)]")
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["에너지", "산업공정", "농업", "LULUCF", "폐기물", "간접배출"])
    with tab1:
        col1, col2 = st.columns([1,10])
        with col1:
            filter = ['시도', '시군구']
            if st.checkbox('구분1', value=True, key='에11'):
                filter.append('구분1')
            if st.checkbox('구분2', value=True, key='에12'):
                filter.append('구분2')
            if st.checkbox('구분3', value=True, key='에13'):
                filter.append('구분3')
            if st.checkbox('구분4', value=True, key='에14'):
                filter.append('구분4')
            if st.checkbox('구분5', value=True, key='에15'):
                filter.append('구분5')
            if st.checkbox('활동자료1', value=True, key='에16'):
                filter.append('활동자료1')
            if st.checkbox('활동자료2', value=True, key='에17'):
                filter.append('활동자료2')
            if st.checkbox('활동자료3', value=True, key='에18'):
                filter.append('활동자료3')
            filter.append('단위')
        with col2:
            st.dataframe(pd.pivot_table(get_db1(1, True),values='값',index=filter, columns='연도', aggfunc=np.sum), use_container_width=True)
    with tab2:
        col1, col2 = st.columns([1,10])
        with col1:
            filter = ['시도', '시군구']
            if st.checkbox('구분1', value=True, key='산11'):
                filter.append('구분1')
            if st.checkbox('구분2', value=True, key='산12'):
                filter.append('구분2')
            if st.checkbox('구분3', value=True, key='산13'):
                filter.append('구분3')
            if st.checkbox('구분4', value=True, key='산14'):
                filter.append('구분4')
            if st.checkbox('활동자료1', value=True, key='산15'):
                filter.append('활동자료1')
            if st.checkbox('활동자료2', value=True, key='산16'):
                filter.append('활동자료2')
            if st.checkbox('활동자료3', value=True, key='산17'):
                filter.append('활동자료3')
            filter.append('단위')
        with col2:
            st.dataframe(pd.pivot_table(get_db1(2, True),values='값',index=filter, columns='연도', aggfunc=np.sum), use_container_width=True)
    with tab3:
        col1, col2 = st.columns([1,10])
        with col1:
            filter = ['시도', '시군구']
            if st.checkbox('구분1', value=True, key='농11'):
                filter.append('구분1')
            if st.checkbox('구분2', value=True, key='농12'):
                filter.append('구분2')
            if st.checkbox('구분3', value=True, key='농13'):
                filter.append('구분3')
            if st.checkbox('구분4', value=True, key='농14'):
                filter.append('구분4')
            if st.checkbox('구분5', value=True, key='농15'):
                filter.append('구분5')
            if st.checkbox('활동자료1', value=True, key='농16'):
                filter.append('활동자료1')
            if st.checkbox('활동자료2', value=True, key='농17'):
                filter.append('활동자료2')
            if st.checkbox('활동자료3', value=True, key='농18'):
                filter.append('활동자료3')
            filter.append('단위')
        with col2:
            st.dataframe(pd.pivot_table(get_db1(3, True),values='값',index=filter, columns='연도', aggfunc=np.sum), use_container_width=True)
    with tab4:
        col1, col2 = st.columns([1,10])
        with col1:
            filter = ['시도', '시군구']
            if st.checkbox('구분1', value=True, key='L11'):
                filter.append('구분1')
            if st.checkbox('구분2', value=True, key='L12'):
                filter.append('구분2')
            if st.checkbox('구분3', value=True, key='L13'):
                filter.append('구분3')
            if st.checkbox('활동자료1', value=True, key='L14'):
                filter.append('활동자료1')
            if st.checkbox('활동자료2', value=True, key='L15'):
                filter.append('활동자료2')
            if st.checkbox('활동자료3', value=True, key='L16'):
                filter.append('활동자료3')
            filter.append('단위')
        with col2:
            st.dataframe(pd.pivot_table(get_db1(4, True),values='값',index=filter, columns='연도', aggfunc=np.sum), use_container_width=True)
    with tab5:
        col1, col2 = st.columns([1,10])
        with col1:
            filter = ['시도', '시군구']
            if st.checkbox('구분1', value=True, key='폐11'):
                filter.append('구분1')
            if st.checkbox('구분2', value=True, key='폐12'):
                filter.append('구분2')
            if st.checkbox('구분3', value=True, key='폐13'):
                filter.append('구분3')
            if st.checkbox('활동자료1', value=True, key='폐14'):
                filter.append('활동자료1')
            if st.checkbox('활동자료2', value=True, key='폐15'):
                filter.append('활동자료2')
            if st.checkbox('활동자료3', value=True, key='폐16'):
                filter.append('활동자료3')
            filter.append('단위')
        with col2:
            st.dataframe(pd.pivot_table(get_db1(5, True),values='값',index=filter, columns='연도', aggfunc=np.sum), use_container_width=True)
    with tab6:
        col1, col2 = st.columns([1,10])
        with col1:
            filter = ['시도', '시군구']
            if st.checkbox('구분1', value=True, key='간11'):
                filter.append('구분1')
            if st.checkbox('구분2', value=True, key='간12'):
                filter.append('구분2')
            if st.checkbox('구분3', value=True, key='간13'):
                filter.append('구분3')
            if st.checkbox('구분4', value=True, key='간14'):
                filter.append('구분4')
            if st.checkbox('구분5', value=True, key='간15'):
                filter.append('구분5')
            if st.checkbox('활동자료1', value=True, key='간16'):
                filter.append('활동자료1')
            if st.checkbox('활동자료2', value=True, key='간17'):
                filter.append('활동자료2')
            if st.checkbox('활동자료3', value=True, key='간18'):
                filter.append('활동자료3')
            filter.append('단위')
        with col2:
            st.dataframe(pd.pivot_table(get_db1(6, True),values='값',index=filter, columns='연도', aggfunc=np.sum), use_container_width=True)
    
    col1, col2 = st.columns([7,1])
    with col2:
        if st.session_state.input_list[1] == "전체":
            cnt = pd.read_sql('select count(*) from TB_ACT_VALUE '
                    + f'where 연도 >= {st.session_state.input_list[2]} and 연도 <= {st.session_state.input_list[3]} '
                    + f'and 시도 = "{st.session_state.input_list[0]}" '
                    + f'and 업데이트가능여부 = "가능"', db).iloc[0,0]
        else:
            cnt = pd.read_sql('select count(*) from TB_ACT_VALUE '
                    + f'where 연도 >= {st.session_state.input_list[2]} and 연도 <= {st.session_state.input_list[3]} '
                    + f'and 시도 = "{st.session_state.input_list[0]}" and 시군구 = "{st.session_state.input_list[1]}" '
                    + f'and 업데이트가능여부 = "가능"', db).iloc[0,0]
        if cnt == 0:
            button_clicked = st.button(f'업데이트 완료', type="primary", use_container_width=True, disabled=True)
        else:
            button_clicked = st.button(f'{cnt}개 업데이트', type="primary", use_container_width=True, disabled=False)
        
        if button_clicked:
            st.session_state.page = 991
            st.rerun()

    st.write("---")
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        go_0 = st.button("메인 페이지", key="go_0_button", use_container_width=True)
        if go_0:
            st.session_state.page = 0
            st.rerun()
    with c2:
        go_2 = st.button("배출량 DB", key="go_2_button", use_container_width=True)
        if go_2:
            st.session_state.page = 2
            st.rerun()
    with c3:
        go_3 = st.button("분석 시각화", key="go_3_button", use_container_width=True)
        if go_3:
            st.session_state.page = 3
            st.rerun()

# 활동자료 업데이트 페이지
def get_update_page1():
    st.title("활동자료 DB … :green[업데이트 중]")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["에너지", "산업공정", "AFOLU", "폐기물", "간접배출"])
    with tab1:
        st.dataframe(pd.pivot_table(get_db1(1, True),values='값',index=['시도', '시군구', '구분1', '구분2', '구분3', '구분4', '구분5', '활동자료1', '단위'], columns='연도', aggfunc=np.sum), use_container_width=True)
    with tab2:
        st.dataframe(pd.pivot_table(get_db1(2, True),values='값',index=['시도', '시군구', '구분1', '구분2', '구분3', '구분4', '구분5', '활동자료1', '단위'], columns='연도', aggfunc=np.sum), use_container_width=True)
    with tab3:
        st.dataframe(pd.pivot_table(get_db1(3, True),values='값',index=['시도', '시군구', '구분1', '구분2', '구분3', '구분4', '구분5', '활동자료1', '단위'], columns='연도', aggfunc=np.sum), use_container_width=True)
    with tab4:
        st.dataframe(pd.pivot_table(get_db1(4, True),values='값',index=['시도', '시군구', '구분1', '구분2', '구분3', '구분4', '구분5', '활동자료1', '단위'], columns='연도', aggfunc=np.sum), use_container_width=True)
    with tab5:
        st.dataframe(pd.pivot_table(get_db1(5, True),values='값',index=['시도', '시군구', '구분1', '구분2', '구분3', '구분4', '구분5', '활동자료1', '단위'], columns='연도', aggfunc=np.sum), use_container_width=True)
    
    update_db(0)

    pg_bar = st.progress(0, text="⏩Progress")
    for percent_complete in range(100):
        time.sleep(0.1)
        pg_bar.progress(percent_complete + 1, text="Progress")

    time.sleep(0.1)
    st.success("업데이트가 완료되었습니다.")
    time.sleep(1)
    st.session_state.page = 1
    st.rerun()

# 배출량 페이지
def get_page2():
    st.title("온실가스 배출량 DB")
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["에너지", "산업공정", "농업", "LULUCF", "폐기물", "간접배출"])
    with tab1:
        col1, col2 = st.columns([1,12])
        with col1:
            filter = ['시도', '시군구']
            if st.checkbox('구분1', value=True, key='에21'):
                filter.append('구분1')
            if st.checkbox('구분2', value=True, key='에22'):
                filter.append('구분2')
            if st.checkbox('구분3', value=True, key='에23'):
                filter.append('구분3')
            if st.checkbox('구분4', value=True, key='에24'):
                filter.append('구분4')
            if st.checkbox('구분5', value=True, key='에25'):
                filter.append('구분5')
            filter.append('단위')
        with col2:
            st.dataframe(pd.pivot_table(get_db2(1, True),values='배출량',index=filter, columns='연도', aggfunc=np.sum), use_container_width=True)
    with tab2:
        col1, col2 = st.columns([1,12])
        with col1:
            filter = ['시도', '시군구']
            if st.checkbox('구분1', value=True, key='산21'):
                filter.append('구분1')
            if st.checkbox('구분2', value=True, key='산22'):
                filter.append('구분2')
            if st.checkbox('구분3', value=True, key='산23'):
                filter.append('구분3')
            if st.checkbox('구분4', value=True, key='산24'):
                filter.append('구분4')
            filter.append('단위')
        with col2:
            st.dataframe(pd.pivot_table(get_db2(2, True),values='배출량',index=filter, columns='연도', aggfunc=np.sum), use_container_width=True)
    with tab3:
        col1, col2 = st.columns([1,12])
        with col1:
            filter = ['시도', '시군구']
            if st.checkbox('구분1', value=True, key='농21'):
                filter.append('구분1')
            if st.checkbox('구분2', value=True, key='농22'):
                filter.append('구분2')
            if st.checkbox('구분3', value=True, key='농23'):
                filter.append('구분3')
            if st.checkbox('구분4', value=True, key='농24'):
                filter.append('구분4')
            if st.checkbox('구분5', value=True, key='농25'):
                filter.append('구분5')
            filter.append('단위')
        with col2:
            st.dataframe(pd.pivot_table(get_db2(3, True),values='배출량',index=filter, columns='연도', aggfunc=np.sum), use_container_width=True)
    with tab4:
        col1, col2 = st.columns([1,12])
        with col1:
            filter = ['시도', '시군구']
            if st.checkbox('구분1', value=True, key='L21'):
                filter.append('구분1')
            if st.checkbox('구분2', value=True, key='L22'):
                filter.append('구분2')
            if st.checkbox('구분3', value=True, key='L23'):
                filter.append('구분3')
            filter.append('단위')
        with col2:
            st.dataframe(pd.pivot_table(get_db2(4, True),values='배출량',index=filter, columns='연도', aggfunc=np.sum), use_container_width=True)
    with tab5:
        col1, col2 = st.columns([1,12])
        with col1:
            filter = ['시도', '시군구']
            if st.checkbox('구분1', value=True, key='폐21'):
                filter.append('구분1')
            if st.checkbox('구분2', value=True, key='폐22'):
                filter.append('구분2')
            if st.checkbox('구분3', value=True, key='폐23'):
                filter.append('구분3')
            filter.append('단위')
        with col2:
            st.dataframe(pd.pivot_table(get_db2(5, True),values='배출량',index=filter, columns='연도', aggfunc=np.sum), use_container_width=True)
    with tab6:
        col1, col2 = st.columns([1,12])
        with col1:
            filter = ['시도', '시군구']
            if st.checkbox('구분1', value=True, key='간21'):
                filter.append('구분1')
            if st.checkbox('구분2', value=True, key='간22'):
                filter.append('구분2')
            if st.checkbox('구분3', value=True, key='간23'):
                filter.append('구분3')
            if st.checkbox('구분4', value=True, key='간24'):
                filter.append('구분4')
            if st.checkbox('구분5', value=True, key='간25'):
                filter.append('구분5')
            filter.append('단위')
        with col2:
            st.dataframe(pd.pivot_table(get_db2(6, True),values='배출량',index=filter, columns='연도', aggfunc=np.sum), use_container_width=True)

    col1, col2 = st.columns([7,1])
    with col2:
        if st.session_state.input_list[1] == "전체":
            cnt = pd.read_sql('select count(*) from TB_EMIT_VALUE '
                    + f'where 연도 >= {st.session_state.input_list[2]} and 연도 <= {st.session_state.input_list[3]} '
                    + f'and 시도 = "{st.session_state.input_list[0]}" '
                    + f'and 업데이트가능여부 = "가능"', db).iloc[0,0]
        else:
            cnt = pd.read_sql('select count(*) from TB_EMIT_VALUE '
                    + f'where 연도 >= {st.session_state.input_list[2]} and 연도 <= {st.session_state.input_list[3]} '
                    + f'and 시도 = "{st.session_state.input_list[0]}" and 시군구 = "{st.session_state.input_list[1]}" '
                    + f'and 업데이트가능여부 = "가능"', db).iloc[0,0]
        if cnt == 0:
            button_clicked = st.button(f'업데이트 완료', type="primary", use_container_width=True, disabled=True)
        else:
            button_clicked = st.button(f'{cnt}개 업데이트', type="primary", use_container_width=True, disabled=False)
        
        if button_clicked:
            st.session_state.page = 992
            st.rerun()
    
    st.write("---")
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        go_0 = st.button("메인 페이지", key="go_0_button", use_container_width=True)
        if go_0:
            st.session_state.page = 0
            st.rerun()
    with c2:
        go_1 = st.button("활동자료 DB", key="go_1_button", use_container_width=True)
        if go_1:
            st.session_state.page = 1
            st.rerun()
    with c3:
        go_3 = st.button("분석 시각화", key="go_3_button", use_container_width=True)
        if go_3:
            st.session_state.page = 3
            st.rerun()

# 배출량 업데이트 페이지
def get_update_page2():
    st.title("온실가스 배출량 DB … :green[업데이트 중]")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["에너지", "산업공정", "AFOLU", "폐기물", "간접배출"])
    with tab1:
        st.dataframe(pd.pivot_table(get_db2(1, True),values='배출량',index=['시도', '시군구', '구분1', '구분2', '구분3', '구분4', '구분5', '단위'], columns='연도', aggfunc=np.sum), use_container_width=True)
    with tab2:
        st.dataframe(pd.pivot_table(get_db2(2, True),values='배출량',index=['시도', '시군구', '구분1', '구분2', '구분3', '구분4', '구분5', '단위'], columns='연도', aggfunc=np.sum), use_container_width=True)
    with tab3:
        st.dataframe(pd.pivot_table(get_db2(3, True),values='배출량',index=['시도', '시군구', '구분1', '구분2', '구분3', '구분4', '구분5', '단위'], columns='연도', aggfunc=np.sum), use_container_width=True)
    with tab4:
        st.dataframe(pd.pivot_table(get_db2(4, True),values='배출량',index=['시도', '시군구', '구분1', '구분2', '구분3', '구분4', '구분5', '단위'], columns='연도', aggfunc=np.sum), use_container_width=True)
    with tab5:
        st.dataframe(pd.pivot_table(get_db2(5, True),values='배출량',index=['시도', '시군구', '구분1', '구분2', '구분3', '구분4', '구분5', '단위'], columns='연도', aggfunc=np.sum), use_container_width=True)
    
    update_db(1)

    pg_bar = st.progress(0, text="⏩Progress")
    for percent_complete in range(100):
        time.sleep(0.1)
        pg_bar.progress(percent_complete + 1, text="Progress")

    time.sleep(0.1)
    st.success("업데이트가 완료되었습니다.")
    time.sleep(1)
    st.session_state.page = 2
    st.rerun()

# 분석결과 페이지
def get_page3():
    st.title("분석 시각화")
    st.write("---")
    col1, col2, col3 = st.columns([1, 0.1, 6])
    with col1:
        selected = option_menu(
            menu_title = None,
            options = ["배출통계", "지표분석"],
            icons = ['bar-chart', 'people'],
            # orientation = 'horizontal',
       )
        
    with col3:
      ### 배출통계
        if selected == "배출통계":
            with st.container():
                st.write("### :black[1. 연도별 온실가스 배출량 추이]", unsafe_allow_html=True)
                col1, col2 = st.columns([2,1])
                with col2:
                    p = st.multiselect("항목 선택", options=['총배출량', '순배출량'], default=['총배출량', '순배출량'], key="p")
                with col1:
                    df = get_db2(0, True)
                    table = pd.pivot_table(df.loc[df['구분1']!="LULUCF"], index=['연도'], values=['배출량'], aggfunc='sum')
                    table2 = pd.pivot_table(df, index=['연도'], values=['배출량'], aggfunc='sum')
                    table.style.format({'배출량': '{:,.0f}'}).set_properties(**{'text-align': 'right'})
                    fig = make_subplots(rows=1, cols=1)
                    text = ['{:,.0f}'.format(value) for value in table['배출량']]
                    text2 = ['{:,.0f}'.format(value) for value in table2['배출량']]
                    if '총배출량' in p:
                        fig.add_trace(go.Scatter(x=table.index, y=table['배출량'], name = "총배출량", mode="lines+markers+text", marker=dict(color="#F87474"), text=text, textposition="top center"), row=1, col=1)
                    if '순배출량' in p:
                        fig.add_trace(go.Scatter(x=table2.index, y=table2['배출량'], name = "순배출량", mode="lines+markers+text", marker=dict(color="#3AB0FF"), text=text2, textposition="bottom center"), row=1, col=1)
                    fig.update_layout(title=f"ㅡ {st.session_state.input_list[0]} {st.session_state.input_list[1]}",
                                        title_font=dict(size=20), font=dict(size=15), xaxis_title='연도', yaxis_title='배출량(tCO2e)', height=500,
                                        legend=dict(x=0.35, y=1.1, orientation="h"))
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    st.dataframe(pd.merge(table, table2, on='연도').rename(columns={'배출량_x':'총배출량', '배출량_y':'순배출량'}), use_container_width=True)
                st.write("---")

            with st.container():
                st.write("### :black[2. 시도별 온실가스 배출량 비교]", unsafe_allow_html=True)
                col1, col2 = st.columns([2,1])
                with col2:
                    y1 = st.selectbox("연도 선택", options=range(st.session_state.input_list[2],st.session_state.input_list[3]+1), key="year1")
                with col1:
                    df = pd.read_sql('select cast(b.연도 as char) as 연도, b.시도, round(sum(b.배출량),0) as 배출량 from TB_CATEGORY a, TB_EMIT_VALUE b where a.id = b.category_id group by b.연도, b.시도;', db)
                    table = pd.pivot_table(df[df['연도']==str(y1)], index=['시도'], values='배출량', aggfunc='sum').sort_values(by='배출량', ascending=False)
                    table['** 비율'] = table['배출량'] / sum(table['배출량'])
                    table.style.format({'배출량': '{:,.0f}'}).set_properties(**{'text-align': 'right'})
                    colors = ['#F87474' if i == st.session_state.input_list[0] else '#C7C7C7' for i in table.index]
                    fig = go.Figure(go.Bar(x=table.index, y=table['배출량'], marker=dict(color=colors)))
                    fig.add_annotation(x=st.session_state.input_list[0],
                                        y=table.loc[st.session_state.input_list[0],'배출량'],
                                        text='{:,.0f}'.format(table.loc[st.session_state.input_list[0],'배출량']),
                                        font=dict(size=15), showarrow=True, ax=15, ay=-30, arrowhead=2)
                    fig.update_layout(title=f"ㅡ {st.session_state.input_list[0]}", height=500,
                                    title_font=dict(size=20), xaxis_title='시도', yaxis_title='배출량(tCO2e)')
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    st.dataframe(table, use_container_width=True)
                    st.write("<div style='text-align: right;'>** 각 시도가 차지하는 비율</div>", unsafe_allow_html=True)
                st.write("---")

            with st.container():
                st.write("### :black[3. 시군구별 온실가스 배출량 비교]", unsafe_allow_html=True)
                col1, col2 = st.columns([2,1])
                with col2:
                    y2 = st.selectbox("연도 선택", options=range(st.session_state.input_list[2],st.session_state.input_list[3]+1), key="year2")
                with col1:
                    df = get_db2(0, False)
                    table = pd.pivot_table(df[df['연도']==str(y2)], index=['시군구'], values='배출량', aggfunc='sum').sort_values(by='배출량', ascending=False)
                    table['** 비율'] = table['배출량'] / sum(table['배출량'])
                    table.style.format({'배출량': '{:,.0f}'}).set_properties(**{'text-align': 'right'})
                    colors = ['#F87474' if st.session_state.input_list[1] != "전체" and i == st.session_state.input_list[1] else '#C7C7C7' for i in table.index]
                    fig = go.Figure(go.Bar(x=table.index, y=table['배출량'], marker=dict(color=colors)))
                    if st.session_state.input_list[1] != "전체":
                        fig.add_annotation(x=st.session_state.input_list[1],
                                           y=table.loc[st.session_state.input_list[1],'배출량'],
                                           text='{:,.0f}'.format(table.loc[st.session_state.input_list[1],'배출량']),
                                           font=dict(size=15), showarrow=True, ax=15, ay=-30, arrowhead=2)
                    fig.update_layout(title=f"ㅡ {st.session_state.input_list[0]} {st.session_state.input_list[1]}", height=500,
                                    title_font=dict(size=20), xaxis_title='시군구', yaxis_title='배출량(tCO2e)')
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    st.dataframe(table, use_container_width=True)
                    st.write("<div style='text-align: right;'>** 시도 내 각 시군구가 차지하는 비율</div>", unsafe_allow_html=True)
                st.write("---")

            with st.container():
                st.write("### :black[4. 부문별 온실가스 배출량 비교]", unsafe_allow_html=True)
                col1, col2 = st.columns([2,1])
                with col2:
                    y3 = st.selectbox("연도 선택", options=range(st.session_state.input_list[2],st.session_state.input_list[3]+1), key="year3")
                with col1:
                    df = get_db2(0, False)
                    table = pd.pivot_table(df[df['연도']==str(y3)], index=['시군구', '구분1'], values='배출량', aggfunc='sum').reset_index()
                    table.style.format({'배출량': '{:,.0f}'}).set_properties(**{'text-align': 'right'})

                    categories = ['에너지', '산업공정', '농업', 'LULUCF', '폐기물', '간접배출']
                    colors = ['#F87474', '#3AB0FF', '#FFB562', '#8BDB81', '#B799FF', '#C7C7C7']
                    cat_sum = table.groupby(['시군구', '구분1'])['배출량'].sum()
                    tot_sum = table.groupby('시군구')['배출량'].sum()
                    relative_values = cat_sum / tot_sum
                    table['** 비율'] = relative_values.reset_index()['배출량']

                    fig = make_subplots(rows=1, cols=1)
                    for category, color in zip(categories, colors):
                        subset = table[table['구분1'] == category]
                        fig.add_trace(go.Bar(x=subset['시군구'], y=relative_values[subset.index], name=category, marker_color=color), row=1, col=1)
                    fig.update_layout(title=f"ㅡ {st.session_state.input_list[0]} 전체", title_font=dict(size=20), height=500,
                                      xaxis_title='시군구', yaxis_title='누적 백분율(%)', barmode='relative', legend=dict(x=0.15, y=1.1, orientation="h"))
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    st.dataframe(table.set_index('시군구'), use_container_width=True)
                    st.write("<div style='text-align: right;'>** 시군구 내 각 부문이 차지하는 비율</div>", unsafe_allow_html=True)
                
                s = st.selectbox("비교군 선택", options=table['시군구'].unique())
                fig = make_subplots(rows=1, cols=2, specs=[[{"type": "pie"}, {"type": "pie"}]])
                if st.session_state.input_list[1] != "전체":
                    fig.add_trace(go.Pie(labels=table[table['시군구']==st.session_state.input_list[1]]['구분1'], values=table[table['시군구']==st.session_state.input_list[1]]['배출량'],
                                         hole=0.5, textposition='inside', marker=dict(colors=colors)), row=1, col=1)
                    fig.add_annotation(x=0.225, y=0.5, xanchor='center', yanchor='middle', text=st.session_state.input_list[1], font=dict(size=30), showarrow=False)
                    fig.add_trace(go.Pie(labels=table[table['시군구']==s]['구분1'], values=table[table['시군구']==s]['배출량'],
                                         hole=0.5, textposition='inside', marker=dict(colors=colors)), row=1, col=2)
                    fig.add_annotation(x=0.775, y=0.5, xanchor='center', yanchor='middle', text=s, font=dict(size=30), showarrow=False)
                else:
                    fig.add_trace(go.Pie(labels=table['구분1'], values=table['배출량'],
                                         hole=0.5, textposition='inside', marker=dict(colors=colors)), row=1, col=1)
                    fig.add_annotation(x=0.225, y=0.5, xanchor='center', yanchor='middle', text=st.session_state.input_list[1], font=dict(size=30), showarrow=False)
                    fig.add_trace(go.Pie(labels=table[table['시군구']==s]['구분1'], values=table[table['시군구']==s]['배출량'],
                                         hole=0.5, textposition='inside', marker=dict(colors=colors)), row=1, col=2)
                    fig.add_annotation(x=0.775, y=0.5, xanchor='center', yanchor='middle', text=s, font=dict(size=30), showarrow=False)
                fig.update_layout(title=f"ㅡ {st.session_state.input_list[0]} {st.session_state.input_list[1]} vs {s}", title_font=dict(size=20), font=dict(size=15), height=500,
                                  margin=dict(l=10, r=10, t=100, b=30), legend=dict(x=0.45, y=0.5, orientation="v", traceorder='normal'))
                st.plotly_chart(fig, use_container_width=True)

      ### 지표분석
        if selected == "지표분석":
            with st.container():
                st.write("### :black[1. 연도별 탄소집약도 추이]", unsafe_allow_html=True)
                col1, col2 = st.columns([2,1])
                with col1:
                    df = pd.read_sql(f'select a.시도, a.시군구, cast(b.연도 as char) as 연도, sum(b.소비량) as "에너지소비량", sum(b.소비량)/sum(d.배출량) as "탄소집약도" from tb_region a, tb_energy b, tb_category c, tb_emit_value d where a.코드 = b.코드 and a.시도 = d.시도 and a.시군구 = d.시군구 and b.연도 = d.연도 and c.ID = d.Category_ID and a.시도 = "{st.session_state.input_list[0]}" group by a.시도, a.시군구, b.연도;', db)
                    
                    fig = make_subplots(rows=1, cols=1)
                    table = pd.pivot_table(df, index=['연도'], values=['탄소집약도'], aggfunc='mean')
                    table.style.format({'총배출량': '{:,.0f}','에너지소비량': '{:,.0f}','탄소집약도': '{:,.2f}'}).set_properties(**{'text-align': 'right'})
                    text = ['{:,.2f}'.format(value) for value in table['탄소집약도']]
                    fig.add_trace(go.Scatter(x=list(range(len(table.index))), y=table['탄소집약도'], name = "전체", mode="lines+markers+text", marker=dict(color="#3AB0FF"), text=text, textposition="top center"))
                    if st.session_state.input_list[1] != "전체":
                        table2 = pd.pivot_table(df[df['시군구']==st.session_state.input_list[1]], index=['연도'], values=['탄소집약도'], aggfunc='mean')
                        table2.style.format({'총배출량': '{:,.0f}','에너지소비량': '{:,.0f}','탄소집약도': '{:,.2f}'}).set_properties(**{'text-align': 'right'})
                        text2 = ['{:,.2f}'.format(value) for value in table2['탄소집약도']]
                        fig.add_trace(go.Scatter(x=list(range(len(table2.index))), y=table2['탄소집약도'], name = st.session_state.input_list[1], mode="lines+markers+text", marker=dict(color="#F87474"), text=text2, textposition="top center"))
                    fig.update_layout(title=f"ㅡ {st.session_state.input_list[0]} {st.session_state.input_list[1]}",
                                    title_font=dict(size=20), font=dict(size=15), height=500,
                                    xaxis=dict(title='연도', tickmode='array', tickvals=list(range(len(table.index))), ticktext=table.index), yaxis_title='탄소집약도',
                                    legend=dict(x=0.35, y=1.1, orientation="h"))
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    table['시도'] = st.session_state.input_list[0]
                    table = table[['시도', '탄소집약도']]
                    st.dataframe(table, use_container_width=True)
                    if st.session_state.input_list[1] != "전체":
                        table2['시군구'] = st.session_state.input_list[1]
                        table2 = table2[['시군구', '탄소집약도']]
                        st.dataframe(table2, use_container_width=True)
                st.write("---")

            with st.container():
                st.write("### :black[2. 시군구 총배출량 vs 1인당 배출량]", unsafe_allow_html=True)
                col1, col2 = st.columns([2,1])
                with col2:
                    y4 = st.selectbox("연도 선택", options=range(st.session_state.input_list[2],st.session_state.input_list[3]+1), key="year4")
                with col1:
                    df = pd.read_sql(f'select a.시도, a.시군구, b.연도, sum(d.배출량) as 총배출량, sum(d.배출량) / b.인구수 as `1인당 배출량` from tb_region a, tb_population b, tb_category c, tb_emit_value d where a.코드 = b.코드 and a.시도 = d.시도 and a.시군구 = d.시군구 and b.연도 = d.연도 and b.연도 = {y4} and c.id = d.category_id and a.시도 = "{st.session_state.input_list[0]}" and c.구분1 <> "LULUCF" group by a.시도, a.시군구, b.연도, b.인구수;', db)
                    table = pd.pivot_table(df, index=['시군구'], values=['연도', '총배출량', '1인당 배출량'], aggfunc='sum').sort_values(by='총배출량', ascending=False)

                    x_mid = (table['1인당 배출량'].min() + table['1인당 배출량'].max()) / 2
                    y_mid = (table['총배출량'].min() + table['총배출량'].max()) / 2
                    size = [15 if i == st.session_state.input_list[1] else 10 for i in table.index]
                    symbol = ['star' if i == st.session_state.input_list[1] else 'circle' for i in table.index]
                    colors = ['#fc4c4c' if i == st.session_state.input_list[1] else '#C7C7C7' for i in table.index]
                    fig = go.Figure(data=go.Scatter(x=table['1인당 배출량'], y=table['총배출량'], mode = "markers+text", marker=dict(size=size, symbol=symbol, color=colors), text=table.index, textposition="top center"))
                    fig.add_vline(x=x_mid, line_width=2, line_dash="dot", line_color="gray")
                    fig.add_hline(y=y_mid, line_width=2, line_dash="dot", line_color="gray")
                    fig.add_shape(type="rect", x0=x_mid, y0=y_mid, x1=(6*table['1인당 배출량'].max()-x_mid)*0.2, y1=(6*table['총배출량'].max()-y_mid)*0.2, line_width=2, fillcolor='rgba(255,0,0,0.05)', line_color='rgba(255,0,0,0)')
                    fig.add_shape(type="rect", x0=(6*table['1인당 배출량'].min()-x_mid)*0.2, y0=(6*table['총배출량'].min()-y_mid)*0.2, x1=x_mid, y1=y_mid, line_width=2, fillcolor='rgba(0,255,0,0.05)', line_color='rgba(0,255,0,0)')
                    fig.update_layout(title=f"ㅡ {st.session_state.input_list[0]} 전체",
                                    title_font=dict(size=20), font=dict(size=15), xaxis_title='1인당 배출량', yaxis_title='총배출량', height=700)
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    table['총배출량'] = table['총배출량'].round(0)
                    st.dataframe(table[['총배출량','1인당 배출량']], use_container_width=True)
                st.write("---")

            with st.container():
                st.write("### :black[3. 시군구 총배출량 vs GRDP당 배출량]", unsafe_allow_html=True)
                col1, col2 = st.columns([2,1])
                with col2:
                    y5 = st.selectbox("연도 선택", options=range(st.session_state.input_list[2],st.session_state.input_list[3]+1), key="year5")
                with col1:
                    df = pd.read_sql(f'select a.시도, a.시군구, b.연도, sum(d.배출량) as 총배출량, sum(d.배출량) / b.grdp as `GRDP당 배출량` from tb_region a, tb_grdp b, tb_category c, tb_emit_value d where a.코드 = b.코드 and a.시도 = d.시도 and a.시군구 = d.시군구 and b.연도 = d.연도 and b.연도 = {y5} and c.id = d.category_id and a.시도 = "{st.session_state.input_list[0]}" and c.구분1 <> "LULUCF" group by a.시도, a.시군구, b.연도, b.grdp;', db)
                    table = pd.pivot_table(df, index=['시군구'], values=['연도', '총배출량', 'GRDP당 배출량'], aggfunc='sum').sort_values(by='총배출량', ascending=False)
                    table.style.format({'총배출량': '{:,.0f}','GRDP당 배출량': '{:,.0f}'}).set_properties(**{'text-align': 'right'})
                    x_mid = (table['GRDP당 배출량'].min() + table['GRDP당 배출량'].max()) / 2
                    y_mid = (table['총배출량'].min() + table['총배출량'].max()) / 2
                    size = [15 if i == st.session_state.input_list[1] else 10 for i in table.index]
                    symbol = ['star' if i == st.session_state.input_list[1] else 'circle' for i in table.index]
                    colors = ['#fc4c4c' if i == st.session_state.input_list[1] else '#C7C7C7' for i in table.index]
                    fig = go.Figure(data=go.Scatter(x=table['GRDP당 배출량'], y=table['총배출량'], mode = "markers+text", marker=dict(size=size, symbol=symbol, color=colors), text=table.index, textposition="top center"))
                    fig.add_vline(x=x_mid, line_width=2, line_dash="dot", line_color="gray")
                    fig.add_hline(y=y_mid, line_width=2, line_dash="dot", line_color="gray")
                    fig.add_shape(type="rect", x0=x_mid, y0=y_mid, x1=(6*table['GRDP당 배출량'].max()-x_mid)*0.2, y1=(6*table['총배출량'].max()-y_mid)*0.2, line_width=2, fillcolor='rgba(255,0,0,0.05)', line_color='rgba(255,0,0,0)')
                    fig.add_shape(type="rect", x0=(6*table['GRDP당 배출량'].min()-x_mid)*0.2, y0=(6*table['총배출량'].min()-y_mid)*0.2, x1=x_mid, y1=y_mid, line_width=2, fillcolor='rgba(0,255,0,0.05)', line_color='rgba(255,0,0,0)')
                    fig.update_layout(title=f"ㅡ {st.session_state.input_list[0]} 전체",
                                    title_font=dict(size=20), font=dict(size=15), xaxis_title='GRDP당 배출량', yaxis_title='총배출량', height=700)
                    # fig.update_xaxes(range=[table['GRDP당 배출량'].min()*0.5,table['GRDP당 배출량'].max()*1.5])
                    # fig.update_yaxes(range=[table['총배출량'].min()*0.5,table['총배출량'].max()*1.5])
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    table['총배출량'] = table['총배출량'].round(0)
                    st.dataframe(table[['총배출량','GRDP당 배출량']], use_container_width=True)
    
    st.write("---")
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        go_0 = st.button("메인 페이지", key="go_0_button", use_container_width=True)
        if go_0:
            st.session_state.page = 0
            st.rerun()
    with c2:
        go_1 = st.button("활동자료 DB", key="go_1_button", use_container_width=True)
        if go_1:
            st.session_state.page = 1
            st.rerun()
    with c3:
        go_2 = st.button("배출량 DB", key="go_2_button", use_container_width=True)
        if go_2:
            st.session_state.page = 2
            st.rerun()

# --------------------- 메인 함수 --------------------- #
def main():

  # 페이지 설정
    st.set_page_config(
        page_title="에코아이 | 지역 기반 온실가스 데이터 시스템",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="auto",
        menu_items={
            'Get Help': 'mailto:donumm64@ecoeye.com',
            'About': "### 에코아이 환경정보사업팀 \n ##### 지역 기반 온실가스 데이터 플랫폼 \n 인턴연구원 강지원"
        }
    )

  # 세션 정보
    st.session_state = st.session_state
    if 'member' not in st.session_state:
        st.session_state.member = None
    if 'input_list' not in st.session_state:
        st.session_state.input_list = ['서울특별시', '전체', 2015, 2022]
    if 'page' not in st.session_state:
        st.session_state.page = 10

  # 사이드바 설정
    set_sidebar()
    
  # DB 연결
    global db, db2
    db, db2 = connect_db()

  # 고정 영역
    col0, col1, col2, col3 = st.columns([1,7,1,1])
    with col0:
        if st.button('**Home**'):
            st.session_state.page = 10
            st.rerun()
    with col1:
        if st.session_state.member != None:
            if st.session_state.member[6]:
                usertype = "관리자"
            else:
                usertype = "일반회원"
            st.write(f'<div style="font-size: 22px; font-weight: bold; text-align: right;"> {st.session_state.member[2]}님({usertype}) </div>', unsafe_allow_html=True)
    with col2:
        if st.session_state.member == None:
            if st.button('**회원가입**', use_container_width=True):
                st.session_state.page = 11
                st.rerun()
        else:
            if st.button("**마이페이지**", use_container_width=True):
                st.session_state.page = 13
                st.rerun()
    with col3:
        if st.session_state.member == None:
            if st.button('**로그인**', use_container_width=True):
                st.session_state.page = 12
                st.rerun()
        else:
            if st.button("**로그아웃**", use_container_width=True):
                st.success('로그아웃 완료', icon="✅")
                st.session_state.member = None
                time.sleep(2)
                st.session_state.page = 10
                st.rerun()

  # 페이지 이동
    if st.session_state.page == 0:
        get_page_0()
    elif st.session_state.page == 1:
        get_page1()
    elif st.session_state.page == 2:
        get_page2()
    elif st.session_state.page == 3:
        get_page3()
    elif st.session_state.page == 991:
        get_update_page1()
    elif st.session_state.page == 992:
        get_update_page2()
    elif st.session_state.page == 10:
        get_home()
    elif st.session_state.page == 11:
        get_join_page()
    elif st.session_state.page == 12:
        get_login_page()
    elif st.session_state.page == 13:
        get_mypage()

if __name__ == "__main__":

    main()