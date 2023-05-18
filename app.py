import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import streamlit as st
import mysql.connector
from PIL import Image
import folium
import geopandas as gpd
import warnings
warnings.filterwarnings('ignore')

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
    gdf2['center'] = gdf2.centroid
    center1 = (np.median(gdf2['center'].y), np.median(gdf2['center'].x))

    sgg_gdf = gdf.loc[gdf['SGG_NM'].notnull(),:]
    sgg_gdf2 = sgg_gdf.to_crs(epsg=4326)
    target_name = ""

    if idx2 != 0:
        for idx, row in sgg_gdf2.iterrows():
            if st.session_state.input_list[1] in row['SGG_NM']:
                target_name = row['SGG_NM']
                break
        target_gdf = sgg_gdf2.loc[sgg_gdf2['SGG_NM'] == target_name,:]
        target_gdf['center'] = target_gdf.centroid
        center2 = (np.median(target_gdf['center'].y), np.median(target_gdf['center'].x))

    if idx2 == 0:
        m = folium.Map(location=center1, zoom_start=10, min_zoom=9, max_zoom=12, )
        marker = folium.Marker(location=center1)
    else:
        m = folium.Map(location=center2, zoom_start=12, min_zoom=10, max_zoom=14)
        marker = folium.Marker(location=center2)
    popup = folium.Popup(st.session_state.input_list[1])
    marker.add_child(popup)
    marker.add_to(m)
    
    vworld_key="E00B11DC-0EA7-30F4-B7F6-0D5B4A4CDFA3"
    tiles = f"http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/Base/{{z}}/{{y}}/{{x}}.png"

    folium.TileLayer(
        tiles=tiles,
        attr="Vworld",
        overlay=True,
        control=True
    ).add_to(m)

    # # 배경지도 타일 설정하기
    # tiles = "CartoDB positron"
    # # 배경지도 타일 레이어를 지도에 추가하기
    # folium.TileLayer(tiles=tiles).add_to(m)

    folium.GeoJson(
        sgg_gdf,
        name='geoJson',
        tooltip=folium.features.GeoJsonTooltip(fields=['SGG_NM']),
        style_function=lambda feature: {
            'color': 'gray', 'weight': 2, 'fillOpacity': 0.1,
        }
    ).add_to(m)

    m.save('map.html')
    st.components.v1.html(open("map.html", "r", encoding="utf-8").read(), height=500)

# -------------------- MYSQL 연동 -------------------- #
# DB 연동
def connect_db():

  # DB 연결하기
    # mydb = mysql.connector.connect(**st.secrets["mysql"])
    mydb = mysql.connector.connect(
        host = "localhost",
        port = "3306",
        user = "root",
        database = "emissionsdb",
        password = "0000"
    )

    return mydb

# 활동자료 DB 연결
def get_db1(num):

    db = connect_db()
    cat_lst = ["전체", "에너지", "산업공정", "AFOLU", "폐기물", "간접배출"]
    if st.session_state.input_list[1] == "전체":
        if num == 0:
            df = pd.read_sql('select cast(c.연도 as char) as 연도, c.시도, c.시군구, a.대분류, a.중분류, a.소분류, b.활동자료1, b.활동자료2, b.활동자료3, c.단위, c.값, c.최신업데이트일, b.업데이트가능여부 '
                            + 'from category a, activity_info b, activity_value c '
                            + 'where a.id = b.category_id and b.id = c.activity_id '
                            + f'and c.연도 >= {st.session_state.input_list[2]} and c.연도 <= {st.session_state.input_list[3]} '
                            + f'and c.시도 = "{st.session_state.input_list[0]}"', db)
        else:
            df = pd.read_sql('select cast(c.연도 as char) as 연도, c.시도, c.시군구, a.대분류, a.중분류, a.소분류, b.활동자료1, b.활동자료2, b.활동자료3, c.단위, c.값, c.최신업데이트일, b.업데이트가능여부 '
                            + 'from category a, activity_info b, activity_value c '
                            + 'where a.id = b.category_id and b.id = c.activity_id '
                            + f'and c.연도 >= {st.session_state.input_list[2]} and c.연도 <= {st.session_state.input_list[3]} '
                            + f'and c.시도 = "{st.session_state.input_list[0]}" '
                            + f'and a.대분류 = "{cat_lst[num]}"', db)
    else:
        if num == 0:
            df = pd.read_sql('select cast(c.연도 as char) as 연도, c.시도, c.시군구, a.대분류, a.중분류, a.소분류, b.활동자료1, b.활동자료2, b.활동자료3, c.단위, c.값, c.최신업데이트일, b.업데이트가능여부 '
                            + 'from category a, activity_info b, activity_value c '
                            + 'where a.id = b.category_id and b.id = c.activity_id '
                            + f'and c.연도 >= {st.session_state.input_list[2]} and c.연도 <= {st.session_state.input_list[3]} '
                            + f'and c.시도 = "{st.session_state.input_list[0]}" and c.시군구 = "{st.session_state.input_list[1]}"', db)
        else:
            df = pd.read_sql('select cast(c.연도 as char) as 연도, c.시도, c.시군구, a.대분류, a.중분류, a.소분류, b.활동자료1, b.활동자료2, b.활동자료3, c.단위, c.값, c.최신업데이트일, b.업데이트가능여부 '
                            + 'from category a, activity_info b, activity_value c '
                            + 'where a.id = b.category_id and b.id = c.activity_id '
                            + f'and c.연도 >= {st.session_state.input_list[2]} and c.연도 <= {st.session_state.input_list[3]} '
                            + f'and c.시도 = "{st.session_state.input_list[0]}" and c.시군구 = "{st.session_state.input_list[1]}" '
                            + f'and a.대분류 = "{cat_lst[num]}"', db)

    return df

# 배출량 DB 연결
def get_db2(num):

    db = connect_db()
    cat_lst = ["전체", "에너지", "산업공정", "AFOLU", "폐기물", "간접배출"]
    if st.session_state.input_list[1] == "전체":
        if num == 0:
            df = pd.read_sql('select cast(b.연도 as char) as 연도, b.시도, b.시군구, a.대분류, a.중분류, a.소분류, b.단위, b.배출량, b.최신업데이트일 '
                            + 'from category a, emission_value b '
                            + 'where a.id = b.category_id '
                            + f'and b.연도 >= {st.session_state.input_list[2]} and b.연도 <= {st.session_state.input_list[3]} '
                            + f'and b.시도 = "{st.session_state.input_list[0]}"', db)
        else:
            df = pd.read_sql('select cast(b.연도 as char) as 연도, b.시도, b.시군구, a.대분류, a.중분류, a.소분류, b.단위, b.배출량, b.최신업데이트일 '
                            + 'from category a, emission_value b '
                            + 'where a.id = b.category_id '
                            + f'and b.연도 >= {st.session_state.input_list[2]} and b.연도 <= {st.session_state.input_list[3]} '
                            + f'and b.시도 = "{st.session_state.input_list[0]}" '
                            + f'and a.대분류 = "{cat_lst[num]}"', db)
    else:
        if num == 0:
            df = pd.read_sql('select cast(b.연도 as char) as 연도, b.시도, b.시군구, a.대분류, a.중분류, a.소분류, b.단위, b.배출량, b.최신업데이트일 '
                            + 'from category a, emission_value b '
                            + 'where a.id = b.category_id '
                            + f'and b.연도 >= {st.session_state.input_list[2]} and b.연도 <= {st.session_state.input_list[3]} '
                            + f'and b.시도 = "{st.session_state.input_list[0]}" and b.시군구 = "{st.session_state.input_list[1]}"', db)
        else:
            df = pd.read_sql('select cast(b.연도 as char) as 연도, b.시도, b.시군구, a.대분류, a.중분류, a.소분류, b.단위, b.배출량, b.최신업데이트일 '
                            + 'from category a, emission_value b '
                            + 'where a.id = b.category_id '
                            + f'and b.연도 >= {st.session_state.input_list[2]} and b.연도 <= {st.session_state.input_list[3]} '
                            + f'and b.시도 = "{st.session_state.input_list[0]}" and b.시군구 = "{st.session_state.input_list[1]}" '
                            + f'and a.대분류 = "{cat_lst[num]}"', db)

    return df

# 활동자료 DB 업데이트
def update_db():

    db = connect_db()
    cur = db.cursor()
    cur.execute('UPDATE activity_value A JOIN activity_info B ON A.activity_id = B.id SET A.최신업데이트일 = now() WHERE B.업데이트가능여부 = "가능";')
    cur.execute('UPDATE activity_info A JOIN activity_value B ON A.id = B.activity_id SET A.업데이트가능여부 = "완료" WHERE B.최신업데이트일 = curdate();')
    db.commit()

    return 0

# -------------------- 페이지 구성 -------------------- #
# 메인 페이지
def get_main_page():
    st.header("지자체 온실가스 배출량 정보 시스템")
    st.write("---")

    col1, col2, col3 = st.columns([2,0.1,2])
    df_region = get_region_list()

    with col3:
        # 광역지자체 선택
        idx_region = int(df_region[df_region['광역지자체'] == st.session_state.input_list[0]].index[0] if 'input_list' in st.session_state else 0)
        selected_region = st.selectbox("**광역지자체를 선택하세요.**", df_region['광역지자체'], key='region_select', index=idx_region)
        if selected_region != st.session_state.input_list[0]:
            st.session_state.input_list[1] = "전체"
        subregion_list = get_subregion_list(selected_region)
        st.session_state.input_list[0] = selected_region
        st.write("---")

        # 기초지자체 선택
        if selected_region:
            idx_subregion = int(subregion_list[0].index(st.session_state.input_list[1]) if 'input_list' in st.session_state else 0)
            selected_subregion = st.selectbox('**기초지자체를 선택하세요**', subregion_list[0], key='subregion_select', index=idx_subregion)
            st.session_state.input_list[1] = selected_subregion
        else:
            selected_subregion = None
        st.write("---")

        # 연도 선택
        year = st.slider('**연도 범위를 선택하세요.**', min_value=2015, max_value=2023, value=(st.session_state.input_list[2],st.session_state.input_list[3]))
        st.session_state.input_list[2] = year[0]
        st.session_state.input_list[3] = year[1]
        st.write("---")

        # 버튼 추가
        c1, c2, c3 = st.columns([3,1,1])
        with c1:
            st.write(f'🔍 **{selected_region} {selected_subregion}, {year[0]}년 ~ {year[1]}년**', unsafe_allow_html=True)
        with c2:
            refresh = st.button("초기화", key="refresh_button", use_container_width=True)
            if refresh:
                st.session_state.input_list = ['서울특별시', '전체', 2015, 2023]
                st.experimental_rerun()
        with c3:
            go_next = st.button("다음  >", key="next_button", use_container_width=True)
            if go_next:
                st.session_state.page = 1
                st.experimental_rerun()
    with col1:
        move_map()

    st.write("---")

# 활동자료 페이지
def get_page1():
    st.header("활동자료 DB")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["에너지", "산업공정", "AFOLU", "폐기물", "간접배출"])
    with tab1:
        st.dataframe(get_db1(1), use_container_width=True)
    with tab2:
        st.dataframe(get_db1(2), use_container_width=True)
    with tab3:
        st.dataframe(get_db1(3), use_container_width=True)
    with tab4:
        st.dataframe(get_db1(4), use_container_width=True)
    with tab5:
        st.dataframe(get_db1(5), use_container_width=True)
    
    col1, col2 = st.columns([7,1])
    with col2:
        db = connect_db()
        if st.session_state.input_list[1] == "전체":
            cnt = pd.read_sql('select count(*) from activity_info a, activity_value b where a.id = b.activity_id '
                    + f'and b.연도 >= {st.session_state.input_list[2]} and b.연도 <= {st.session_state.input_list[3]} '
                    + f'and b.시도 = "{st.session_state.input_list[0]}" '
                    + f'and a.업데이트가능여부 = "가능"', db).iloc[0,0]
        else:
            cnt = pd.read_sql('select count(*) from activity_info a, activity_value b where a.id = b.activity_id '
                    + f'and b.연도 >= {st.session_state.input_list[2]} and b.연도 <= {st.session_state.input_list[3]} '
                    + f'and b.시도 = "{st.session_state.input_list[0]}" and b.시군구 = "{st.session_state.input_list[1]}" '
                    + f'and a.업데이트가능여부 = "가능"', db).iloc[0,0]
        if cnt == 0:
            button_disabled = True
        else:
            button_disabled = False
        
        button_clicked = st.button('업데이트', type="primary", use_container_width=True, disabled=button_disabled)
        if button_clicked:
            st.session_state.page = 999
            st.experimental_rerun()

    col1, col2, col3 = st.columns([1,6,1])
    with col1:
        go_next = st.button("< Previous", key="previous_button", use_container_width=True)
        if go_next:
            st.session_state.page = 0
            st.experimental_rerun()
    with col3:
        go_next = st.button("Next >", key="next_button", use_container_width=True)
        if go_next:
            st.session_state.page = 2
            st.experimental_rerun()

# 업데이트 페이지
def get_update_page():
    st.header("활동자료 DB … :green[DATA UPDATE]")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["에너지", "산업공정", "AFOLU", "폐기물", "간접배출"])
    with tab1:
        st.dataframe(get_db1(1), use_container_width=True)
    with tab2:
        st.dataframe(get_db1(2), use_container_width=True)
    with tab3:
        st.dataframe(get_db1(3), use_container_width=True)
    with tab4:
        st.dataframe(get_db1(4), use_container_width=True)
    with tab5:
        st.dataframe(get_db1(5), use_container_width=True)

    update_db()

    pg_bar = st.progress(0, text="⏩Progress")
    for percent_complete in range(100):
        time.sleep(0.1)
        pg_bar.progress(percent_complete + 1, text="Progress")

    time.sleep(0.1)
    st.success("업데이트가 완료되었습니다.")
    time.sleep(1)
    st.session_state.page = 1
    st.experimental_rerun()

# 배출량 페이지
def get_page2():
    st.header("온실가스 배출량 DB")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["에너지", "산업공정", "AFOLU", "폐기물", "간접배출"])
    with tab1:
        st.dataframe(get_db2(1), use_container_width=True)
    with tab2:
        st.dataframe(get_db2(2), use_container_width=True)
    with tab3:
        st.dataframe(get_db2(3), use_container_width=True)
    with tab4:
        st.dataframe(get_db2(4), use_container_width=True)
    with tab5:
        st.dataframe(get_db2(5), use_container_width=True)
    
    col1, col2, col3 = st.columns([1,5,1])
    with col1:
        go_next = st.button("< Previous", key="previous_button", use_container_width=True)
        if go_next:
            st.session_state.page = 1
            st.experimental_rerun()
    with col3:
        go_next = st.button("Next >", key="next_button", use_container_width=True)
        if go_next:
            st.session_state.page = 3
            st.experimental_rerun()

# 분석결과 페이지
def get_page3():
    st.header("분석 결과")
    df = get_db2(0)
    tab1, tab2, tab3 = st.tabs(['배출통계', '특성분석', '지표분석'])
    with tab1:
        with st.container():
            col1, col2 = st.columns([1,1])
            with col1:
                st.write("**1. 연도별 온실가스 배출량 추이**", unsafe_allow_html=True)
                # fig = px.pie(df, names='lang', values='Sum', title='각 언어별 파이차트')
                # st.plotly_chart(fig)
                st.line_chart(pd.pivot_table(df, index='연도', values='배출량', aggfunc='sum'), use_container_width=True)
            with col2:
                st.write("**2. 시군별 온실가스 배출량 비교**", unsafe_allow_html=True)
        with st.container():
            st.write("**3. 부문별 온실가스 배출량 비율 (시도 간 비교)**", unsafe_allow_html=True)
        with st.container():
            st.write("**4. 부문별 온실가스 배출량 비율 (시군 간 비교)**", unsafe_allow_html=True)
    with tab2:
        col1, col2 = st.columns([1,1])
        with col1:
            st.write("**1. 연도별 온실가스 배출량 추이**", unsafe_allow_html=True)
        with col2:
            st.write("**2. 연도별 온실가스 배출량 추이**", unsafe_allow_html=True)

    with tab3:
        col1, col2 = st.columns([1,1])
        with col1:
            st.write("**1. 연도별 온실가스 배출량 추이**", unsafe_allow_html=True)
        with col2:
            st.write("**2. 연도별 온실가스 배출량 추이**", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1,6])
    with col1:
        go_next = st.button("< Previous", key="previous_button", use_container_width=True)
        if go_next:
            st.session_state.page = 2
            st.experimental_rerun()

# --------------------- 메인 함수 --------------------- #
def main():

  # 페이지 설정
    st.set_page_config(
        page_title="에코아이 | 지자체 온실가스 배출량 정보 시스템",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="auto",
        menu_items={
            'Get Help': 'mailto:donumm64@ecoeye.com',
            'About': "### 에코아이 환경정보사업팀 \n ##### 지자체 온실가스 배출량 정보 시스템 \n 인턴연구원 강지원입니다."
        }
    )

  # 세션 정보
    st.session_state = st.session_state
    if 'input_list' not in st.session_state:
        st.session_state.input_list = ['서울특별시', '전체', 2015, 2023]
    if 'page' not in st.session_state:
        st.session_state.page = 0

  # 고정 영역
    col0, col1, col2, col3 = st.columns([5,1,1,1])
    with col0:
        if st.button('HOME'):
            st.session_state.page = 0
    with col1:
        if st.button('활동자료 DB', use_container_width=True):
            st.session_state.page = 1
    with col2:
        if st.button('배출량 DB', use_container_width=True):
            st.session_state.page = 2
    with col3:
        if st.button('분석 시각화', use_container_width=True):
            st.session_state.page = 3

  # 페이지 이동
    if st.session_state.page == 0:
        get_main_page()
    elif st.session_state.page == 1:
        get_page1()
    elif st.session_state.page == 999:
        get_update_page()
    elif st.session_state.page == 2:
        get_page2()
    elif st.session_state.page == 3:
        get_page3()

  # 사이드바 설정
    image = Image.open('./logo.png')
    st.sidebar.image(image)
    st.sidebar.title(":blue[에코아이] 환경정보사업팀", )
    st.sidebar.write("---")
    st.sidebar.subheader("조회 조건")
    st.sidebar.write(f'지역 : {st.session_state.input_list[0]} {st.session_state.input_list[1]}')
    st.sidebar.write(f'기간 : {st.session_state.input_list[2]}년 - {st.session_state.input_list[3]}년')

if __name__ == "__main__":

    main()