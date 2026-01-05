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
    
    for col in ['방어팀 스순', '방어팀 펫', '공격팀 펫', '공격팀 스순']:
        df[col] = df[col].fillna('').astype(str).str.strip()

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
st.markdown("데이터를 기반으로 최적의 공격 덱을 추천합니다.")

if df is None:
    st.error("데이터 파일('길드전 답지.xlsx' 등)을 찾을 수 없습니다.")
    st.stop()

# --- 사이드바: 필터 ---
with st.sidebar:
    st.header("🔍 검색 및 필터")
    
    # 1. 날짜 필터
    unique_dates = sorted(df['날짜'].unique().tolist(), reverse=True)
    selected_date = st.selectbox("📅 날짜 선택", ["전체 보기"] + unique_dates)
    
    # 2. 검색창
    search_query = st.text_input("상대 캐릭터 검색", placeholder="예: 카구라, 오공...")

# --- 데이터 필터링 로직 ---
# 1. 방어팀 이름 검색
if search_query:
    filtered_df = df[df['방어팀_정렬'].str.contains(search_query)]
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
        
        # 2. 그 공격팀 내 최다 펫
        best_atk_data = group_data[group_data['공격팀_정렬'] == best_atk_team]
        best_pet = best_atk_data['공격팀 펫'].mode()[0]
        
        # 3. 그 공격팀 내 최다 스순
        best_skill = best_atk_data['공격팀 스순'].mode()[0]
        
        # --- UI 표시 ---
        # 컨테이너를 카드처럼 사용
        with st.container(border=True):
            # 헤더: 방어팀 이름 + 승리 횟수
            col1, col2 = st.columns([4, 1])
            with col1:
                st.subheader(f"VS {defense_team}")
            with col2:
                st.markdown(f"<div style='text-align:right; background:#e0e7ff; color:#3730a3; padding:5px; border-radius:5px; font-weight:bold;'>{match_count}승 검증</div>", unsafe_allow_html=True)
            
            # 요약 정보 (공격팀, 펫, 스순)
            s_col1, s_col2, s_col3 = st.columns(3)
            with s_col1:
                st.markdown("**⚔️ 추천 공격팀**")
                st.markdown(f":blue[{best_atk_team}]")
            with s_col2:
                st.markdown("**🐶 추천 펫**")
                st.text(best_pet)
            with s_col3:
                st.markdown("**⚡ 추천 스순**")
                st.markdown(f"{best_skill} <span style='background:#dcfce7; color:#166534; padding:2px 6px; border-radius:4px; font-size:0.8em;'>Best</span>", unsafe_allow_html=True)

            # 상세 정보 (Expander - 접기/펴기)
            with st.expander("🔻 상세 기록 보기"):
                # 상세 데이터 집계
                # (공격팀, 공격펫, 공격스순, 방어펫, 방어스순) 별 빈도
                detail_counts = group_data.groupby(['공격팀_정렬', '공격팀 펫', '공격팀 스순', '방어팀 펫', '방어팀 스순']).size().reset_index(name='빈도')
                detail_counts = detail_counts.sort_values('빈도', ascending=False)
                
                # 테이블 표시를 위해 컬럼명 변경 및 정리
                detail_counts.columns = ['공격팀', '공격 펫', '공격 스순', '상대 펫', '상대 스순', '빈도']
                
                # 데이터프레임 표시 (인덱스 숨김)
                st.dataframe(
                    detail_counts, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "빈도": st.column_config.NumberColumn(format="%d회")
                    }
                )