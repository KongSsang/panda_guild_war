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
# [추가] 덱 상세 정보 데이터베이스
# ---------------------------------------------------------
DECK_DB = {
    "카구라 밸런스덱": {
        "summary": "안정적인 운영이 가능한 국밥 덱",
        "heroes": ["카구라", "에반", "에이스", "린"],
        "pet": "이린 or 제브",
        "formation": "밸런스 진형 (후열: 카구라)",
        "items": """
        - **카구라**: 속속 / 막막 (치명타 저항)
        - **에반**: 생생 / 막막
        - **에이스**: 치치 / 반반
        - **린**: 속속 / 반반
        """,
        "tips": """
        1. 상대가 선공일 경우 에반 스킬을 먼저 예약하세요.
        2. 카구라의 2스킬을 통해 상대 버프를 제거하는 것이 핵심입니다.
        """
    },
    "오공 극딜덱": {
        "summary": "한방에 보내버리는 시원한 덱",
        "heroes": ["손오공", "여포", "태오", "카일"],
        "pet": "유",
        "formation": "공격 진형 (후열: 손오공)",
        "items": """
        - **손오공**: 치치 / 반반
        - **여포**: 속속 / 생생
        - **태오**: 치치 / 반반
        """,
        "tips": "오공의 분신 타이밍을 잘 계산해야 합니다."
    },
    "즉사 방덱": {
        "summary": "상대를 말려 죽이는 덱",
        "heroes": ["크리스", "녹스", "챈슬러", "루크"],
        "pet": "크리",
        "formation": "방어 진형",
        "items": "전원 생생 / 막막 세팅 추천",
        "tips": "장기전으로 끌고 가는 것이 승리 플랜입니다."
    }
}

# ---------------------------------------------------------
# CSS 스타일
# ---------------------------------------------------------
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 800px;
    }
    
    /* 카드 스타일 */
    .custom-card {
        background-color: white;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 10px;
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
    .def-label { font-size: 0.8rem; color: #ef4444; font-weight: 700; margin-right: 4px; }
    
    /* 배지 및 칩 스타일 */
    .badge { padding: 4px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; color: white; white-space: nowrap; }
    .hero-chip { display: inline-block; background-color: #f3f4f6; border: 1px solid #d1d5db; color: #374151; padding: 2px 8px; border-radius: 12px; font-size: 0.9rem; font-weight: 600; margin-right: 4px; margin-bottom: 4px; }
    
    /* 상세 정보 스타일 */
    .info-row { margin-bottom: 12px; }
    .label { font-size: 0.85rem; color: #6b7280; font-weight: 600; margin-bottom: 4px; }
    .value { font-size: 1rem; color: #111827; font-weight: 500; }
    
    /* 프로그래스 바 */
    .progress-container { margin-top: 8px; }
    .progress-bg { background-color: #f3f4f6; border-radius: 9999px; height: 8px; width: 100%; overflow: hidden; }
    .progress-fill { height: 100%; border-radius: 9999px; transition: width 0.5s ease-in-out; }
    .pick-rate-text { font-size: 0.8rem; color: #6b7280; float: right; }
    
    /* 스킬 박스 */
    .skill-box { background-color: #f0fdf4; border: 1px solid #dcfce7; color: #15803d; padding: 8px 12px; border-radius: 8px; font-family: 'Courier New', monospace; font-weight: 700; letter-spacing: 0.5px; }
    
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
    .stButton > button { width: 100%; }

    /* 가이드 탭 스타일 */
    .guide-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        margin-top: 15px;
    }
    .guide-title { font-size: 1.2rem; font-weight: 700; color: #1e293b; margin-bottom: 10px; }
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
    
    # '상대 길드'와 '기준' 열 추가 전처리
    target_cols = ['방어팀 스순', '방어팀 펫', '공격팀 펫', '공격팀 스순', '속공', '상대 길드', '기준']
    for col in target_cols:
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
# 2. 헬퍼 함수
# ---------------------------------------------------------
def format_hero_tags(team_str):
    if not team_str or team_str == '-': return "-"
    heroes = [h.strip() for h in team_str.split(',') if h.strip()]
    if not heroes: return "-"
    return "".join([f"<span class='hero-chip'>{h}</span>" for h in heroes])

def get_badge_style(count, pick_rate):
    if count < 3: return "background-color: #9ca3af;", "🧪 표본 적음"
    if pick_rate >= 30 and count >= 10: return "background-color: #2563eb;", "🔥 강력 추천"
    elif pick_rate >= 20: return "background-color: #3b82f6;", "✅ 무난함"
    else: return "background-color: #f59e0b;", "⚠️ 취향 갈림"

def clean_html(raw_html):
    return "".join([line.strip() for line in raw_html.splitlines()])

def get_mode(series):
    if series.empty: return "-", 0
    valid = series[series != '']
    if valid.empty: return "-", 0
    mode_val = valid.mode()[0]
    count = valid[valid == mode_val].shape[0]
    return mode_val, count

def get_speed_distribution(series):
    if series.empty: return "-"
    valid = series[series != '']
    if valid.empty: return "-"
    counts = valid.value_counts()
    sun = counts.get('선공', 0)
    hoo = counts.get('후공', 0)
    span_style = "color:#6b7280; font-size:0.8em; font-weight:400;"
    if sun == 0 and hoo == 0:
        mode_val, count = get_mode(series)
        return f"<b>{mode_val}</b> <span style='{span_style}'>({count}회)</span>"
    parts = []
    if sun > 0: parts.append(f"<b>선공</b> <span style='{span_style}'>({sun}회)</span>")
    if hoo > 0: parts.append(f"<b>후공</b> <span style='{span_style}'>({hoo}회)</span>")
    return "&nbsp; ".join(parts)

# ---------------------------------------------------------
# 3. 메인 UI 구성
# ---------------------------------------------------------
st.title("🛡️ 판다 길드전 공격 추천")

last_update_text = ""
if df is not None and not df.empty and '날짜' in df.columns:
    dates = sorted(df['날짜'].unique().tolist(), reverse=True)
    if dates: last_update_text = f"Last Update: {dates[0]}"

st.markdown(f"""
<div style='margin-top: -15px; margin-bottom: 5px; color: gray; font-size: 0.9em;'>데이터 기반 승리 공식 (made by 콩쌍)</div>
<div style='margin-bottom: 25px; color: #9ca3af; font-size: 0.8rem;'>{last_update_text}</div>
""", unsafe_allow_html=True)

if df is None:
    st.error("데이터 파일을 찾을 수 없습니다. (길드전 답지.xlsx 또는 .csv)")
    st.stop()

# --- 탭 구성 ---
tab1, tab2 = st.tabs(["⚔️ 공격 덱 추천", "📖 덱 상세 가이드"])

# =========================================================
# TAB 1: 공격 추천
# =========================================================
with tab1:
    with st.sidebar:
        st.header("🔍 필터 옵션")
        search_query = st.text_input("상대 캐릭터 검색", placeholder="예: 카구라, 오공")
        st.caption("공백으로 구분하여 여러 명 검색 가능")
        st.divider()

        unique_dates = sorted(df['날짜'].unique().tolist(), reverse=True)
        if 'selected_date_list' not in st.session_state:
            st.session_state['selected_date_list'] = unique_dates[:5] if len(unique_dates) >= 5 else unique_dates

        col1, col2 = st.columns(2)
        if col1.button("모두 선택"):
            st.session_state['selected_date_list'] = unique_dates
            st.rerun()
        if col2.button("최근 5번"):
            st.session_state['selected_date_list'] = unique_dates[:5] if len(unique_dates) >= 5 else unique_dates
            st.rerun()
        
        selected_dates = st.multiselect("📅 날짜 선택", unique_dates, key='selected_date_list')
        st.divider()

        unique_guilds = sorted([g for g in df['상대 길드'].unique().tolist() if g])
        selected_guilds = st.multiselect("🏰 상대 길드 선택", unique_guilds)
        st.caption("선택 시 해당 길드를 상대로 공격한 기록만 보여줍니다.")

    filtered_df = df.copy()
    if search_query:
        keywords = [k.strip() for k in search_query.replace(',', ' ').split() if k.strip()]
        if keywords:
            mask = filtered_df['방어팀_정렬'].apply(lambda x: all(k in x.split(', ') for k in keywords))
            filtered_df = filtered_df[mask]
    if selected_dates:
        filtered_df = filtered_df[filtered_df['날짜'].isin(selected_dates)]
    if selected_guilds:
        filtered_df = filtered_df[filtered_df['상대 길드'].isin(selected_guilds)]
        filtered_df = filtered_df[filtered_df['기준'] == '공격']

    if filtered_df.empty:
        st.info("검색 결과가 없습니다.")
    else:
        grouped = filtered_df.groupby('방어팀_정렬')
        display_list = []
        for defense, group in grouped:
            display_list.append({'defense': defense, 'count': len(group), 'data': group})
        display_list.sort(key=lambda x: x['count'], reverse=True)

        for item in display_list:
            defense_team = item['defense']
            match_count = item['count']
            group_data = item['data']
            
            atk_counts = group_data['공격팀_정렬'].value_counts()
            if atk_counts.empty: continue
            
            best_atk_team = atk_counts.idxmax()
            best_atk_count = atk_counts.max()
            pick_rate = (best_atk_count / match_count) * 100
            
            best_atk_data = group_data[group_data['공격팀_정렬'] == best_atk_team]
            best_pet, best_pet_count = get_mode(best_atk_data['공격팀 펫'])
            best_skill, best_skill_count = get_mode(best_atk_data['공격팀 스순'])
            speed_dist = get_speed_distribution(best_atk_data['속공'])
            
            def_tags = format_hero_tags(defense_team)
            atk_tags = format_hero_tags(best_atk_team)
            badge_style, badge_text = get_badge_style(match_count, pick_rate)
            bar_color = badge_style.split(":")[1].replace(";", "").strip()

            raw_html = f"""
                <div class="custom-card">
                    <div class="card-header">
                        <div style="flex: 1;"><span class="def-label">VS</span>{def_tags}</div>
                        <div class="badge" style="{badge_style}">{badge_text} ({match_count}건)</div>
                    </div>
                    <div class="info-row">
                        <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:5px;">
                            <div class="label">⚔️ 추천 공격팀</div>
                            <div class="pick-rate-text">{pick_rate:.1f}% 픽률</div>
                        </div>
                        <div class="value">{atk_tags}</div>
                        <div class="progress-container">
                            <div class="progress-bg"><div class="progress-fill" style="width: {pick_rate}%; background-color: {bar_color};"></div></div>
                        </div>
                    </div>
                    <div class="grid-2">
                        <div><div class="label">🐶 펫 <span style='font-weight:400; font-size:0.75em'>({best_pet_count}회)</span></div><div class="value">{best_pet}</div></div>
                        <div><div class="label">🏃 속공</div><div class="value" style="font-size:0.95rem;">{speed_dist}</div></div>
                    </div>
                    <div class="info-row" style="margin-top: 15px;">
                        <div class="label">⚡ 추천 스순 <span style='font-weight:400; font-size:0.8em'>({best_skill_count}회)</span></div>
                        <div class="skill-box">{best_skill}</div>
                    </div>
                </div>
            """
            st.markdown(clean_html(raw_html), unsafe_allow_html=True)

            st.markdown("<div style='margin-bottom:5px; font-size:0.85rem; color:#6b7280;'>🔻 공격팀별 상세 기록</div>", unsafe_allow_html=True)
            atk_groups = [ (k, v) for k, v in group_data.groupby('공격팀_정렬') ]
            atk_groups.sort(key=lambda x: len(x[1]), reverse=True)

            for atk_team, atk_df in atk_groups:
                cnt = len(atk_df); ratio = (cnt / match_count) * 100
                with st.expander(f"⚔️ {atk_team} ({cnt}회 / {ratio:.1f}%)"):
                    sub_pet, sub_pet_cnt = get_mode(atk_df['공격팀 펫'])
                    sub_skill, sub_skill_cnt = get_mode(atk_df['공격팀 스순'])
                    sub_speed_dist = get_speed_distribution(atk_df['속공'])
                    
                    st.markdown(f"""
                        <div style="background-color: #f9fafb; padding: 12px; border-radius: 8px; margin-bottom: 12px; border: 1px solid #e5e7eb;">
                            <div style="font-size: 0.85rem; font-weight: 600; color: #4b5563; margin-bottom: 8px;">💡 이 조합의 추천 세팅</div>
                            <div style="display: flex; flex-wrap: wrap; gap: 15px; font-size: 0.9rem;">
                                <div>🐶 <b>{sub_pet}</b> <span style="color:#6b7280; font-size:0.8em">({sub_pet_cnt}회)</span></div>
                                <div>🏃 {sub_speed_dist}</div>
                                <div>⚡ <b>{sub_skill}</b> <span style="color:#6b7280; font-size:0.8em">({sub_skill_cnt}회)</span></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    detail_counts = atk_df.groupby(['공격팀 펫', '공격팀 스순', '속공', '방어팀 펫', '방어팀 스순']).size().reset_index(name='빈도')
                    detail_counts = detail_counts.sort_values('빈도', ascending=False)
                    detail_counts.columns = ['공격 펫', '공격 스순', '속공', '상대 펫', '상대 스순', '빈도']
                    st.dataframe(detail_counts, use_container_width=True, hide_index=True, column_config={"빈도": st.column_config.NumberColumn(format="%d회")})
            st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

# =========================================================
# TAB 2: 덱 상세 가이드
# =========================================================
with tab2:
    st.header("📖 덱별 상세 가이드")
    st.caption("주요 덱의 장비 세팅과 운영법을 확인하세요.")
    
    # 덱 선택
    selected_deck_name = st.selectbox("확인할 덱을 선택하세요", list(DECK_DB.keys()))
    
    if selected_deck_name:
        deck_info = DECK_DB[selected_deck_name]
        
        # 덱 요약 카드 표시
        heroes_html = format_hero_tags(",".join(deck_info['heroes']))
        
        st.markdown(f"""
        <div class="custom-card" style="border-left: 5px solid #3b82f6;">
            <div style="font-size: 1.2rem; font-weight: 700; margin-bottom: 5px;">{selected_deck_name}</div>
            <div style="color: #64748b; margin-bottom: 15px;">{deck_info['summary']}</div>
            <div style="margin-bottom: 10px;">
                <span class="label">구성 영웅:</span> {heroes_html}
            </div>
            <div class="grid-2">
                <div><div class="label">🐶 추천 펫</div><div class="value">{deck_info['pet']}</div></div>
                <div><div class="label">🛡️ 진형</div><div class="value">{deck_info['formation']}</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 상세 정보 (2단 컬럼)
        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.markdown("""
            <div class="guide-box">
                <div class="guide-title">⚔️ 장비/잠재 세팅</div>
                <div style="white-space: pre-line; color: #334155; line-height: 1.6;">
            """ + deck_info['items'] + """
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.markdown("""
            <div class="guide-box">
                <div class="guide-title">💡 운영 팁</div>
                <div style="white-space: pre-line; color: #334155; line-height: 1.6;">
            """ + deck_info['tips'] + """
                </div>
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("""
    <div style='text-align: center; color: #9ca3af; font-size: 0.8rem; margin-top: 50px;'>
        데이터 출처: 판다 길드전 내용 | 문의: 콩쌍
    </div>
""", unsafe_allow_html=True)
