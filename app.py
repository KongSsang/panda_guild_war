import streamlit as st
import pandas as pd
import os
import textwrap  # [추가] 들여쓰기 제거를 위한 모듈

# ---------------------------------------------------------
# 페이지 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="판다 길드전 공격 추천",
    page_icon="🛡️",
    layout="wide"
)

# ---------------------------------------------------------
# CSS 스타일 (모바일 최적화 및 UI 개선)
# ---------------------------------------------------------
st.markdown("""
    <style>
    /* 전체 폰트 및 배경 설정 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 800px; /* 모바일/태블릿 가독성을 위해 최대 폭 제한 */
    }
    
    /* 카드 스타일 */
    .custom-card {
        background-color: white;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .custom-card:hover {
        border-color: #cbd5e1;
    }
    
    /* 헤더 스타일 */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #f3f4f6;
        padding-bottom: 12px;
        margin-bottom: 15px;
    }
    .def-label {
        font-size: 0.8rem;
        color: #ef4444; /* 방어팀은 붉은 계열 */
        font-weight: 700;
        margin-right: 4px;
    }
    
    /* 데이터 배지 (신뢰도) */
    .badge {
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        color: white;
        white-space: nowrap;
    }
    
    /* 영웅 이름 칩(Chip) 스타일 */
    .hero-chip {
        display: inline-block;
        background-color: #f3f4f6;
        border: 1px solid #d1d5db;
        color: #374151;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.9rem;
        font-weight: 600;
        margin-right: 4px;
        margin-bottom: 4px;
    }
    
    /* 정보 행 스타일 */
    .info-row {
        margin-bottom: 12px;
    }
    .label {
        font-size: 0.85rem;
        color: #6b7280;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .value {
        font-size: 1rem;
        color: #111827;
        font-weight: 500;
    }
    
    /* 픽률 프로그래스 바 */
    .progress-container {
        margin-top: 8px;
    }
    .progress-bg {
        background-color: #f3f4f6;
        border-radius: 9999px;
        height: 8px;
        width: 100%;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        border-radius: 9999px;
        transition: width 0.5s ease-in-out;
    }
    .pick-rate-text {
        font-size: 0.8rem;
        color: #6b7280;
        float: right;
    }
    
    /* 스킬 박스 */
    .skill-box {
        background-color: #f0fdf4;
        border: 1px solid #dcfce7;
        color: #15803d;
        padding: 8px 12px;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    
    /* 2열 레이아웃 (모바일 대응) */
    .grid-2 {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
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

    # 영웅 이름 정렬 및 전처리 함수 (빈 값 제거 강화)
    def normalize_team(team_str):
        if not isinstance(team_str, str):
            if pd.isna(team_str): return ""
            return str(team_str)
        # 쉼표로 나누고, 앞뒤 공백 제거 후 빈 문자열 제외
        characters = [char.strip() for char in team_str.split(',') if char.strip()]
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
            
    # 속공 표기 통일
    if '속공' in df.columns:
        df['속공'] = df['속공'].replace({'선': '선공', '후': '후공'})

    if '날짜' in df.columns:
        df['날짜'] = df['날짜'].fillna('').astype(str).str.strip()
        df['날짜'] = df['날짜'].apply(lambda x: x.replace('.0', '') if x.endswith('.0') else x)
    else:
        df['날짜'] = 'Unknown'
        
    # 유효한 데이터만 남기기 (방어팀이나 공격팀 이름이 빈 경우 제외)
    df = df[df['방어팀_정렬'] != ""]
    df = df[df['공격팀_정렬'] != ""]
        
    return df

df = load_data()

# ---------------------------------------------------------
# 2. 헬퍼 함수 (HTML 생성용)
# ---------------------------------------------------------
def format_hero_tags(team_str):
    """콤마로 구분된 영웅 이름을 개별 태그(Chip)로 변환"""
    if not team_str or team_str == '-':
        return "-"
    # 빈 값 필터링을 한 번 더 수행하여 안전하게 처리
    heroes = [h.strip() for h in team_str.split(',') if h.strip()]
    if not heroes:
        return "-"
    tags = "".join([f"<span class='hero-chip'>{h}</span>" for h in heroes])
    return tags

def get_badge_style(count, pick_rate):
    """데이터 개수와 픽률에 따른 배지 스타일 반환"""
    if count < 3:
        return "background-color: #9ca3af;", "🧪 표본 적음" # 회색
    
    if pick_rate >= 30:
        return "background-color: #2563eb;", "🔥 강력 추천" # 파랑
    elif pick_rate >= 20:
        return "background-color: #3b82f6;", "✅ 무난함" # 연한 파랑
    else:
        return "background-color: #f59e0b;", "⚠️ 취향 갈림" # 노랑

# ---------------------------------------------------------
# 3. UI 구성
# ---------------------------------------------------------

st.title("🛡️ 판다 길드전 공격 추천")
st.markdown("<div style='margin-top: -15px; margin-bottom: 25px; color: gray; font-size: 0.9em;'>데이터 기반 승리 공식 (made by 콩쌍)</div>", unsafe_allow_html=True)

if df is None:
    st.error("데이터 파일을 찾을 수 없습니다. (길드전 답지.xlsx 또는 .csv)")
    st.stop()

# --- 사이드바 ---
with st.sidebar:
    st.header("🔍 필터 옵션")
    
    unique_dates = sorted(df['날짜'].unique().tolist(), reverse=True)
    selected_date = st.selectbox("📅 날짜 선택", ["전체 보기"] + unique_dates)
    
    st.divider()
    search_query = st.text_input("상대 캐릭터 검색", placeholder="예: 카구라, 오공")
    st.caption("공백으로 구분하여 여러 명 검색 가능")

# --- 필터링 로직 ---
filtered_df = df.copy()

if selected_date != "전체 보기":
    filtered_df = filtered_df[filtered_df['날짜'] == selected_date]

if search_query:
    keywords = [k.strip() for k in search_query.replace(',', ' ').split() if k.strip()]
    if keywords:
        def check_all_keywords(team_str, search_keywords):
            team_members = [member.strip() for member in team_str.split(',')]
            return all(keyword in team_members for keyword in search_keywords)
        
        mask = filtered_df['방어팀_정렬'].apply(lambda x: check_all_keywords(x, keywords))
        filtered_df = filtered_df[mask]

# --- 메인 리스트 ---
if filtered_df.empty:
    st.info("검색 결과가 없습니다. 조건을 변경해보세요.")
else:
    # 방어팀 기준으로 그룹화
    grouped = filtered_df.groupby('방어팀_정렬')
    
    display_list = []
    for defense, group in grouped:
        display_list.append({
            'defense': defense,
            'count': len(group),
            'data': group
        })
    # 데이터 많은 순 정렬
    display_list.sort(key=lambda x: x['count'], reverse=True)

    # --- 반복문으로 카드 생성 ---
    for item in display_list:
        defense_team = item['defense']
        match_count = item['count']
        group_data = item['data']
        
        # 1. 가장 많이 쓰인 공격팀 찾기
        atk_counts = group_data['공격팀_정렬'].value_counts()
        if atk_counts.empty:
            continue
            
        best_atk_team = atk_counts.idxmax()
        best_atk_count = atk_counts.max()
        
        # 픽률 계산
        pick_rate = (best_atk_count / match_count) * 100
        
        # 해당 공격팀을 사용한 데이터만 추출 (펫, 스순 분석용)
        best_atk_data = group_data[group_data['공격팀_정렬'] == best_atk_team]
        
        # 2. 최빈값(Mode) 계산 함수
        def get_mode(series):
            if series.empty: return "-", 0
            valid = series[series != '']
            if valid.empty: return "-", 0
            mode_val = valid.mode()[0]
            count = valid[valid == mode_val].shape[0]
            return mode_val, count

        best_pet, best_pet_count = get_mode(best_atk_data['공격팀 펫'])
        best_skill, best_skill_count = get_mode(best_atk_data['공격팀 스순'])
        best_speed, best_speed_count = get_mode(best_atk_data['속공'])
        
        # 3. HTML 생성 준비
        def_tags = format_hero_tags(defense_team)
        atk_tags = format_hero_tags(best_atk_team)
        badge_style, badge_text = get_badge_style(match_count, pick_rate)
        
        # 픽률 바 색상 (배지 배경색과 동일하게)
        bar_color = badge_style.split(":")[1].replace(";", "").strip()

        # 4. 카드 렌더링
        # [중요] textwrap.dedent를 사용하여 들여쓰기로 인한 코드 블록 인식 문제를 방지합니다.
        card_html = textwrap.dedent(f"""
            <div class="custom-card">
                <!-- 헤더: 방어팀 + 배지 -->
                <div class="card-header">
                    <div style="flex: 1;">
                        <span class="def-label">VS</span>
                        {def_tags}
                    </div>
                    <div class="badge" style="{badge_style}">{badge_text} ({match_count}건)</div>
                </div>
                
                <!-- 추천 공격팀 & 픽률 -->
                <div class="info-row">
                    <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:5px;">
                        <div class="label">⚔️ 추천 공격팀</div>
                        <div class="pick-rate-text">{pick_rate:.1f}% 픽률</div>
                    </div>
                    <div class="value">{atk_tags}</div>
                    <div class="progress-container">
                        <div class="progress-bg">
                            <div class="progress-fill" style="width: {pick_rate}%; background-color: {bar_color};"></div>
                        </div>
                    </div>
                </div>

                <!-- 펫 & 속공 (2열 그리드) -->
                <div class="grid-2">
                    <div>
                        <div class="label">🐶 펫 <span style='font-weight:400; font-size:0.75em'>({best_pet_count}회)</span></div>
                        <div class="value">{best_pet}</div>
                    </div>
                    <div>
                        <div class="label">🏃 속공 <span style='font-weight:400; font-size:0.75em'>({best_speed_count}회)</span></div>
                        <div class="value">{best_speed}</div>
                    </div>
                </div>

                <!-- 스킬 순서 -->
                <div class="info-row" style="margin-top: 15px;">
                    <div class="label">⚡ 추천 스순 <span style='font-weight:400; font-size:0.8em'>({best_skill_count}회)</span></div>
                    <div class="skill-box">{best_skill}</div>
                </div>
            </div>
        """)
        
        with st.container():
            st.markdown(card_html, unsafe_allow_html=True)

            # 5. 상세 내역 (Expander)
            with st.expander(f"📊 '{defense_team}' 상대 전체 통계 보기"):
                atk_groups = [ (k, v) for k, v in group_data.groupby('공격팀_정렬') ]
                atk_groups.sort(key=lambda x: len(x[1]), reverse=True)

                for atk_team, atk_df in atk_groups:
                    cnt = len(atk_df)
                    ratio = (cnt / match_count) * 100
                    st.markdown(f"**⚔️ {atk_team}** ({cnt}회 / {ratio:.1f}%)")
                    
                    detail_counts = atk_df.groupby(['공격팀 펫', '공격팀 스순', '속공', '방어팀 펫']).size().reset_index(name='빈도')
                    detail_counts = detail_counts.sort_values('빈도', ascending=False)
                    detail_counts.columns = ['공격 펫', '공격 스순', '속공', '상대 펫', '빈도']
                    
                    st.dataframe(
                        detail_counts, 
                        use_container_width=True, 
                        hide_index=True,
                        column_config={"빈도": st.column_config.NumberColumn(format="%d회")}
                    )
                    st.divider()

    # Footer
    st.markdown("""
        <div style='text-align: center; color: #9ca3af; font-size: 0.8rem; margin-top: 30px;'>
            데이터 출처: 길드전 답지 | 문의: 콩쌍
        </div>
    """, unsafe_allow_html=True)
