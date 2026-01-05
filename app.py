import streamlit as st
import pandas as pd
import os

# ---------------------------------------------------------
# 페이지 설정 (가장 먼저 와야 함)
# ---------------------------------------------------------
st.set_page_config(
    page_title="판다 길드전 공격 추천",
    page_icon="🛡️",
    layout="wide"
)

# 스타일 커스텀 (CSS)
st.markdown("""
    <style>
    .main-header {
        text-align: center; 
        color: #4f46e5;
        margin-bottom: 30px;
    }
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .highlight {
        color: #4f46e5;
        font-weight: bold;
    }
    .badge {
        background-color: #dcfce7;
        color: #166534;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8em;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. 데이터 로드 및 전처리
# ---------------------------------------------------------
@st.cache_data # 데이터 캐싱 (속도 향상)
def load_data():
    # Streamlit Cloud 등에서는 파일 경로가 고정적이지 않을 수 있으므로
    # 같은 폴더 내의 파일을 우선 찾습니다.
    possible_filenames = [
        '길드전 답지.xlsx - Sheet1.csv', 
        '길드전_답지.xlsx - Sheet1.csv',
        '길드전 답지.xlsx', 
        '길드전_답지.xlsx'
    ]
    input_file = None

    for fname in possible_filenames:
        if os.path.exists(fname):
            input_file = fname
            break
    
    if input_file is None:
        return None

    try:
        if input_file.endswith('.xlsx'):
            df = pd.read_excel(input_file)
        else:
            try:
                df = pd.read_csv(input_file, encoding='cp949')
            except UnicodeDecodeError:
                df = pd.read_csv(input_file, encoding='utf-8')
    except Exception as e:
        st.error(f"파일 읽기 오류: {e}")
        return None

    # 데이터 정규화 함수
    def normalize_team(team_str):
        if not isinstance(team_str, str):
            return str(team_str)
        characters = [char.strip() for char in team_str.split(',')]
        characters.sort()
        return ", ".join(characters)

    # 전처리
    df['방어팀_정렬'] = df['방어팀'].apply(normalize_team)
    df['공격팀_정렬'] = df['공격팀'].apply(normalize_team)
    
    # 텍스트 컬럼 전처리 ('속공' 추가)
    text_cols = ['방어팀 스순', '방어팀 펫', '공격팀 펫', '공격팀 스순', '속공']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()
        else:
            df[col] = '' # 컬럼이 없을 경우 빈 문자열로 처리

    # 날짜 처리
    if '날짜' in df.columns:
        df['날짜'] = df['날짜'].fillna('').astype(str).str.strip()
        df['날짜'] = df['날짜'].apply(lambda x: x.replace('.0', '') if x.endswith('.0') else x)
    else:
        df['날짜'] = 'Unknown'
        
    return df

df = load_data()

# ---------------------------------------------------------
# 2. UI 구성 (사이드바 & 메인)
# ---------------------------------------------------------

st.title("🛡️ 판다 길드전 공격 추천")
st.caption("made by 콩쌍") # 제작자 표시
st.markdown("데이터를 기반으로 최적의 공격 덱을 추천합니다.")

if df is None:
    st.error("데이터 파일('길드전 답지.xlsx' 등)을 찾을 수 없습니다.")
    st.info("GitHub 저장소에 엑셀 파일을 함께 업로드했는지 확인해주세요.")
    st.stop()

# --- 사이드바: 필터 ---
with st.sidebar:
    st.header("🔍 검색 및 필터")
    
    # 1. 날짜 필터
    unique_dates = sorted(df['날짜'].unique().tolist(), reverse=True)
    selected_date = st.selectbox("📅 날짜 선택", ["전체 보기"] + unique_dates)
    
    # 2. 검색창
    search_query = st.text_input("상대 캐릭터 검색", placeholder="예: 카구라, 오공 (순서 상관없음)")

# --- 데이터 필터링 로직 ---
# 1. 방어팀 이름 검색 (순서 무관, 정확한 이름 일치 로직 적용)
if search_query:
    keywords = [k.strip() for k in search_query.replace(',', ' ').split() if k.strip()]
    
    if keywords:
        def check_exact_match(team_str, search_keywords):
            team_members = [member.strip() for member in team_str.split(',')]
            return all(keyword in team_members for keyword in search_keywords)

        mask = df['방어팀_정렬'].apply(lambda x: check_exact_match(x, keywords))
        filtered_df = df[mask]
    else:
        filtered_df = df
else:
    filtered_df = df

# 2. 날짜 필터링
if selected_date != "전체 보기":
    filtered_df = filtered_df[filtered_df['날짜'] == selected_date]

# --- 메인 리스트 출력 ---
if filtered_df.empty:
    st.info("검색 결과가 없습니다.")
else:
    # 방어팀별로 그룹화
    grouped = filtered_df.groupby('방어팀_정렬')
    
    # 승리 횟수 순으로 정렬하기 위해 리스트로 변환
    display_list = []
    for defense, group in grouped:
        display_list.append({
            'defense': defense,
            'count': len(group),
            'data': group
        })
    display_list.sort(key=lambda x: x['count'], reverse=True)

    # 카드 출력
    for item in display_list:
        defense_team = item['defense']
        match_count = item['count']
        group_data = item['data']
        
        # --- 추천 알고리즘 (계층형) ---
        # 1. 최다 승리 공격팀
        atk_counts = group_data['공격팀_정렬'].value_counts()
        best_atk_team = atk_counts.idxmax()
        
        # 해당 공격팀을 사용한 데이터만 필터링
        best_atk_data = group_data[group_data['공격팀_정렬'] == best_atk_team]
        
        # 2. 그 공격팀 내 최다 펫 + 사용 횟수
        if not best_atk_data['공격팀 펫'].empty:
            best_pet = best_atk_data['공격팀 펫'].mode()[0]
            best_pet_count = best_atk_data[best_atk_data['공격팀 펫'] == best_pet].shape[0]
        else:
            best_pet = "-"
            best_pet_count = 0
        
        # 3. 그 공격팀 내 최다 스순 + 사용 횟수
        if not best_atk_data['공격팀 스순'].empty:
            best_skill = best_atk_data['공격팀 스순'].mode()[0]
            best_skill_count = best_atk_data[best_atk_data['공격팀 스순'] == best_skill].shape[0]
        else:
            best_skill = "-"
            best_skill_count = 0

        # 4. 그 공격팀 내 최다 속공(선/후) + 사용 횟수
        if '속공' in best_atk_data.columns and not best_atk_data['속공'].empty:
            # 빈 값이 아닐 때만 계산
            valid_speed = best_atk_data[best_atk_data['속공'] != '']
            if not valid_speed.empty:
                best_speed = valid_speed['속공'].mode()[0]
                best_speed_count = valid_speed[valid_speed['속공'] == best_speed].shape[0]
            else:
                best_speed = "-"
                best_speed_count = 0
        else:
            best_speed = "-"
            best_speed_count = 0
        
        # --- UI 표시 ---
        with st.container(border=True):
            # 헤더: 방어팀 이름 + 데이터 개수
            col1, col2 = st.columns([4, 1])
            with col1:
                st.subheader(f"VS {defense_team}")
            with col2:
                st.markdown(f"<div style='text-align:right; background:#e0e7ff; color:#3730a3; padding:5px; border-radius:5px; font-weight:bold;'>{match_count}개의 데이터</div>", unsafe_allow_html=True)
            
            # 요약 정보 (공격팀, 펫, 스순, 속공) - 4칸으로 변경
            s_col1, s_col2, s_col3, s_col4 = st.columns(4)
            with s_col1:
                st.markdown("**⚔️ 추천 공격팀**")
                st.markdown(f":blue[{best_atk_team}]")
            with s_col2:
                st.markdown(f"**🐶 추천 펫** <span style='color:gray; font-size:0.8em'>({best_pet_count}회)</span>", unsafe_allow_html=True)
                st.text(best_pet)
            with s_col3:
                st.markdown(f"**⚡ 추천 스순** <span style='color:gray; font-size:0.8em'>({best_skill_count}회)</span>", unsafe_allow_html=True)
                st.markdown(f"{best_skill} <span style='background:#dcfce7; color:#166534; padding:2px 6px; border-radius:4px; font-size:0.8em;'>Best</span>", unsafe_allow_html=True)
            with s_col4:
                # 속공 추천 표시
                st.markdown(f"**🏃 추천 속공** <span style='color:gray; font-size:0.8em'>({best_speed_count}회)</span>", unsafe_allow_html=True)
                st.text(best_speed)

            # 상세 정보 섹션
            st.divider()
            st.caption("🔻 공격팀별 상세 기록 (클릭하여 펼치기)")

            # --- 상세 기록 (공격팀별로 Grouping) ---
            atk_groups = [ (k, v) for k, v in group_data.groupby('공격팀_정렬') ]
            atk_groups.sort(key=lambda x: len(x[1]), reverse=True)

            for atk_team, atk_df in atk_groups:
                count = len(atk_df)
                with st.expander(f"⚔️ {atk_team} ({count}회)"):
                    # 상세 데이터 집계 (속공 포함)
                    detail_counts = atk_df.groupby(['공격팀 펫', '공격팀 스순', '속공', '방어팀 펫', '방어팀 스순']).size().reset_index(name='빈도')
                    detail_counts = detail_counts.sort_values('빈도', ascending=False)
                    
                    detail_counts.columns = ['공격 펫', '공격 스순', '속공', '상대 펫', '상대 스순', '빈도']
                    
                    st.dataframe(
                        detail_counts, 
                        use_container_width=True, 
                        hide_index=True,
                        column_config={
                            "빈도": st.column_config.NumberColumn(format="%d회")
                        }
                    )
