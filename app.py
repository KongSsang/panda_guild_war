import streamlit as st
import pandas as pd
import os

# ---------------------------------------------------------
# 페이지 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="판다 길드전 공격 추천",
    page_icon="🛡️",
    layout="wide"
)

# ---------------------------------------------------------
# CSS 스타일 (모바일 최적화)
# ---------------------------------------------------------
st.markdown("""
    <style>
    /* 전체 폰트 및 배경 설정 */
    .block-container {
        padding-top: 3rem; /* 제목 잘림 방지 */
        padding-bottom: 5rem;
    }
    
    /* 카드 스타일 */
    .custom-card {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    
    /* 헤더 스타일 */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #f3f4f6;
        padding-bottom: 10px;
        margin-bottom: 10px;
    }
    .def-team-name {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1f2937;
    }
    .data-badge {
        background-color: #e0e7ff;
        color: #4338ca;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        white-space: nowrap;
    }

    /* 정보 행 스타일 */
    .info-row {
        margin-bottom: 8px;
    }
    .label {
        font-size: 0.85rem;
        color: #6b7280;
        font-weight: 600;
        margin-bottom: 2px;
    }
    .value {
        font-size: 1rem;
        color: #111827;
        font-weight: 500;
        word-break: keep-all;
    }
    .value-highlight {
        color: #2563eb;
        font-weight: 700;
    }
    
    /* 스킬 순서 박스 */
    .skill-box {
        background-color: #f0fdf4;
        border: 1px solid #dcfce7;
        color: #166534;
        padding: 8px 12px;
        border-radius: 8px;
        font-family: monospace;
        font-weight: 600;
        margin-top: 5px;
    }
    
    /* 제작자 표시 */
    .footer {
        text-align: center;
        color: #9ca3af;
        font-size: 0.8rem;
        margin-top: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. 데이터 로드 및 전처리
# ---------------------------------------------------------
@st.cache_data
def load_data():
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

    def normalize_team(team_str):
        if not isinstance(team_str, str):
            return str(team_str)
        characters = [char.strip() for char in team_str.split(',')]
        characters.sort()
        return ", ".join(characters)

    df['방어팀_정렬'] = df['방어팀'].apply(normalize_team)
    df['공격팀_정렬'] = df['공격팀'].apply(normalize_team)
    
    # 텍스트 컬럼 전처리
    for col in ['방어팀 스순', '방어팀 펫', '공격팀 펫', '공격팀 스순', '속공']:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()
        else:
            df[col] = ''
            
    # [수정] 속공 표기 통일 (선 -> 선공, 후 -> 후공)
    if '속공' in df.columns:
        df['속공'] = df['속공'].replace({'선': '선공', '후': '후공'})

    if '날짜' in df.columns:
        df['날짜'] = df['날짜'].fillna('').astype(str).str.strip()
        df['날짜'] = df['날짜'].apply(lambda x: x.replace('.0', '') if x.endswith('.0') else x)
    else:
        df['날짜'] = 'Unknown'
        
    return df

df = load_data()

# ---------------------------------------------------------
# 2. UI 구성
# ---------------------------------------------------------

st.title("🛡️ 판다 길드전 공격 추천")
st.markdown("<div style='margin-top: -15px; margin-bottom: 20px; color: gray; font-size: 0.9em;'>made by 콩쌍</div>", unsafe_allow_html=True)

if df is None:
    st.error("데이터 파일을 찾을 수 없습니다. GitHub에 파일을 업로드했는지 확인해주세요.")
    st.stop()

# --- 사이드바 ---
with st.sidebar:
    st.header("🔍 필터")
    
    unique_dates = sorted(df['날짜'].unique().tolist(), reverse=True)
    selected_date = st.selectbox("📅 날짜 선택", ["전체 보기"] + unique_dates)
    
    search_query = st.text_input("상대 캐릭터 검색", placeholder="예: 카구라, 오공")

# --- 필터링 로직 ---
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

if selected_date != "전체 보기":
    filtered_df = filtered_df[filtered_df['날짜'] == selected_date]

# --- 메인 리스트 ---
if filtered_df.empty:
    st.info("검색 결과가 없습니다.")
else:
    grouped = filtered_df.groupby('방어팀_정렬')
    
    display_list = []
    for defense, group in grouped:
        display_list.append({
            'defense': defense,
            'count': len(group),
            'data': group
        })
    display_list.sort(key=lambda x: x['count'], reverse=True)

    for item in display_list:
        defense_team = item['defense']
        match_count = item['count']
        group_data = item['data']
        
        # 추천 값 계산
        atk_counts = group_data['공격팀_정렬'].value_counts()
        best_atk_team = atk_counts.idxmax()
        
        best_atk_data = group_data[group_data['공격팀_정렬'] == best_atk_team]
        
        # 펫
        if not best_atk_data['공격팀 펫'].empty:
            best_pet = best_atk_data['공격팀 펫'].mode()[0]
            best_pet_count = best_atk_data[best_atk_data['공격팀 펫'] == best_pet].shape[0]
        else:
            best_pet = "-"
            best_pet_count = 0
            
        # 스순
        if not best_atk_data['공격팀 스순'].empty:
            best_skill = best_atk_data['공격팀 스순'].mode()[0]
            best_skill_count = best_atk_data[best_atk_data['공격팀 스순'] == best_skill].shape[0]
        else:
            best_skill = "-"
            best_skill_count = 0

        # 속공
        if '속공' in best_atk_data.columns and not best_atk_data['속공'].replace('', pd.NA).dropna().empty:
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
        
        # --- [카드 UI 렌더링] ---
        # Streamlit 컨테이너 내부에 HTML/CSS 구조 심기
        with st.container():
            # 카드 시작
            st.markdown(f"""
            <div class="custom-card">
                <div class="card-header">
                    <div class="def-team-name">VS {defense_team}</div>
                    <div class="data-badge">{match_count}개의 데이터</div>
                </div>
            """, unsafe_allow_html=True)
            
            # 1. 공격팀 (한 줄 전체)
            st.markdown(f"""
            <div class="info-row">
                <div class="label">⚔️ 추천 공격팀</div>
                <div class="value value-highlight">{best_atk_team}</div>
            </div>
            """, unsafe_allow_html=True)

            # 2. 펫 & 속공 (2단 컬럼)
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="info-row">
                    <div class="label">🐶 펫 <span style='font-weight:400; font-size:0.8em'>({best_pet_count}회)</span></div>
                    <div class="value">{best_pet}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="info-row">
                    <div class="label">🏃 속공 <span style='font-weight:400; font-size:0.8em'>({best_speed_count}회)</span></div>
                    <div class="value">{best_speed}</div>
                </div>
                """, unsafe_allow_html=True)

            # 3. 스킬 순서 (한 줄 전체 + 박스 스타일)
            st.markdown(f"""
            <div class="info-row">
                <div class="label">⚡ 추천 스순 <span style='font-weight:400; font-size:0.8em'>({best_skill_count}회)</span></div>
                <div class="skill-box">{best_skill}</div>
            </div>
            </div> <!-- 카드 끝 -->
            """, unsafe_allow_html=True)

            # 4. 상세 내역 (Expander)
            with st.expander("🔻 상세 기록 (클릭)"):
                atk_groups = [ (k, v) for k, v in group_data.groupby('공격팀_정렬') ]
                atk_groups.sort(key=lambda x: len(x[1]), reverse=True)

                for atk_team, atk_df in atk_groups:
                    count = len(atk_df)
                    st.markdown(f"**⚔️ {atk_team}** ({count}회 사용)")
                    
                    detail_counts = atk_df.groupby(['공격팀 펫', '공격팀 스순', '속공', '방어팀 펫', '방어팀 스순']).size().reset_index(name='빈도')
                    detail_counts = detail_counts.sort_values('빈도', ascending=False)
                    detail_counts.columns = ['공격 펫', '공격 스순', '속공', '상대 펫', '상대 스순', '빈도']
                    
                    st.dataframe(
                        detail_counts, 
                        use_container_width=True, 
                        hide_index=True,
                        column_config={"빈도": st.column_config.NumberColumn(format="%d회")}
                    )
                st.divider() # 구분선
