import streamlit as st
import pandas as pd
import os
from collections import Counter
import json

# ---------------------------------------------------------
# [설정] 페이지 설정 (가장 먼저 실행되어야 함)
# ---------------------------------------------------------
st.set_page_config(
    page_title="판다 길드전 공격 추천",
    page_icon="🛡️",
    layout="wide"
)

# ---------------------------------------------------------
# [라이브러리] Google Gemini AI (없을 경우를 대비해 예외처리)
# ---------------------------------------------------------
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# ---------------------------------------------------------
# [데이터 로드] 외부 데이터 파일 불러오기
# ---------------------------------------------------------
try:
    from matchup_data import MATCHUP_DB
except ImportError:
    MATCHUP_DB = {}

try:
    from notice_data import NOTICE_DB
except ImportError:
    NOTICE_DB = []

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
    
    /* 버튼 스타일: font-weight를 700(Bold)으로 설정 */
    .stButton > button { 
        width: 100%; 
        font-weight: 700 !important; 
    }

    /* 가이드 탭 스타일 */
    .guide-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        margin-top: 15px;
    }
    .guide-title { font-size: 1.1rem; font-weight: 700; color: #1e293b; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;}
    
    /* 덱 세팅 리스트 스타일 */
    .setting-item {
        display: flex;
        align-items: baseline;
        margin-bottom: 8px;
        font-size: 0.95rem;
        border-bottom: 1px dashed #e2e8f0;
        padding-bottom: 4px;
    }
    .setting-name {
        font-weight: 700;
        color: #1e293b;
        margin-right: 10px;
        min-width: 60px; /* 이름 정렬을 위한 최소 너비 */
        flex-shrink: 0;
    }
    .setting-desc {
        color: #475569;
        word-break: break-word; /* 긴 내용 줄바꿈 */
    }
    
    /* 공지사항 스타일 */
    .notice-card {
        background-color: #fff;
        border-left: 4px solid #3b82f6;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .notice-date {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 5px;
    }
    .notice-content {
        color: #334155;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .notice-content li {
        margin-bottom: 4px;
    }

    /* 메타 분석 랭킹 스타일 */
    .rank-row {
        display: flex;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid #f1f5f9;
    }
    .rank-num {
        font-size: 1.1rem;
        font-weight: 800;
        color: #3b82f6;
        width: 30px;
    }
    .rank-name {
        flex: 1;
        font-weight: 600;
        color: #1e293b;
    }
    .rank-value {
        font-size: 0.9rem;
        color: #64748b;
        background-color: #f8fafc;
        padding: 2px 8px;
        border-radius: 12px;
    }

    /* 챗봇 스타일 */
    .chat-container {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        background-color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# [데이터 전처리] 영웅 이름 정렬 함수 (전역 사용)
# ---------------------------------------------------------
def normalize_team_str(team_str):
    if not isinstance(team_str, str): return str(team_str)
    parts = team_str.replace(',', ' ').split()
    parts = [p.strip() for p in parts if p.strip()]
    parts.sort()
    return ", ".join(parts)

# [데이터 전처리] MATCHUP_DB 키 정규화
if MATCHUP_DB:
    NORMALIZED_DB = {}
    for enemy, my_decks in MATCHUP_DB.items():
        norm_enemy = normalize_team_str(enemy)
        NORMALIZED_DB[norm_enemy] = {}
        for my_deck, guide in my_decks.items():
            norm_my_deck = normalize_team_str(my_deck)
            NORMALIZED_DB[norm_enemy][norm_my_deck] = guide
    MATCHUP_DB = NORMALIZED_DB

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
    
    if input_file is None: return None

    try:
        if input_file.endswith('.xlsx'): df = pd.read_excel(input_file)
        else:
            try: df = pd.read_csv(input_file, encoding='cp949')
            except: df = pd.read_csv(input_file, encoding='utf-8')
    except: return None

    df['방어팀_정렬'] = df['방어팀'].apply(normalize_team_str)
    df['공격팀_정렬'] = df['공격팀'].apply(normalize_team_str)
    
    target_cols = ['방어팀 스순', '방어팀 펫', '공격팀 펫', '공격팀 스순', '속공', '상대 길드', '기준']
    for col in target_cols:
        if col in df.columns: df[col] = df[col].fillna('').astype(str).str.strip()
        else: df[col] = ''
            
    if '속공' in df.columns: df['속공'] = df['속공'].replace({'선': '선공', '후': '후공'})
    if '날짜' in df.columns:
        df['날짜'] = df['날짜'].fillna('').astype(str).str.strip()
        df['날짜'] = df['날짜'].apply(lambda x: x.replace('.0', '') if x.endswith('.0') else x)
    else: df['날짜'] = 'Unknown'
        
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

def expand_synonyms(keywords):
    expanded = set(keywords)
    for k in keywords:
        if '브브' in k: expanded.add(k.replace('브브', '쁘'))
        if '쁘' in k: expanded.add(k.replace('쁘', '브브'))
    return list(expanded)

def check_match(target_str, search_terms):
    for term in search_terms:
        synonyms = {term}
        if term in ['브브', '쁘']: synonyms.update(['브브', '쁘'])
        if not any(syn in target_str for syn in synonyms): return False 
    return True

def get_star_rating(score):
    if not isinstance(score, int): return ""
    score = max(0, min(score, 5))
    filled = "★" * score
    empty = "☆" * (5 - score)
    return f"<span style='color: #f59e0b; font-size: 1.1rem; letter-spacing: 2px;'>{filled}{empty}</span>"

def generate_guide_html(enemy_name, my_deck_name, guide):
    setting_html = ""
    if isinstance(guide.get('my_setting'), list):
        for item in guide['my_setting']:
            setting_html += f"""<div class="setting-item"><span class="setting-name">{item['name']}</span><span class="setting-desc">{item['desc']}</span></div>"""
    else:
        setting_html = f"<div style='white-space: pre-line; color: #334155; line-height: 1.6;'>{guide.get('my_setting', '-')}</div>"

    diff_score = guide.get('difficulty', 0)
    star_html = ""
    if diff_score > 0:
        star_html = f"&nbsp;&nbsp;&nbsp;<span style='background-color: #fffbeb; color: #b45309; padding: 2px 8px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; border: 1px solid #fcd34d;'>세팅 난이도 {get_star_rating(diff_score)}</span>"

    return f"""
    <div class="custom-card" style="border-left: 5px solid #ef4444; margin-top: 5px;">
        <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 5px; color: #1f2937;"><span style="color: #ef4444;">VS</span> {enemy_name}</div>
        <div style="font-size: 1.3rem; font-weight: 800; margin-bottom: 15px; color: #2563eb;">⚔️ {my_deck_name}</div>
        <div style="background-color: #eff6ff; padding: 10px; border-radius: 8px; color: #1e40af; font-weight: 600; margin-bottom: 15px;">📌 {guide.get('summary', '')} {star_html}</div>
        <div style="margin-bottom: 15px;"><div class="label" style="margin-bottom:4px;">🛡️ 추천 진형</div><div class="value" style="font-size: 0.95rem; color: #334155;">{guide.get('formation', '-')}</div></div>
        <div style="margin-bottom: 15px;"><div class="label" style="margin-bottom:4px;">⚠️ 상대 특이사항</div><div class="value" style="font-size: 0.95rem; color: #ef4444;">{guide.get('enemy_info', '-')}</div></div>
        <div class="guide-box"><div class="guide-title">⚔️ 덱 세팅</div>{setting_html}</div>
        <div class="guide-box" style="margin-top: 10px;"><div class="guide-title">💡 실전 운영법</div><div style="white-space: pre-line; color: #334155; line-height: 1.6; font-size: 0.95rem;">{guide.get('operate_tips', '-')}</div></div>
    </div>
    """

@st.dialog("📖 매치업 상세 공략", width="large")
def show_guide_popup(enemy_name, my_deck_name, guide):
    html_content = generate_guide_html(enemy_name, my_deck_name, guide)
    st.markdown(clean_html(html_content), unsafe_allow_html=True)

# ---------------------------------------------------------
# [중요] AI 데이터 요약 함수 (검색 및 매칭 로직 강화)
# ---------------------------------------------------------
def get_ai_context(df, matchup_db, user_query=""):
    context = "다음은 세븐나이츠 리버스 길드전 승리 데이터입니다. 이 데이터를 바탕으로 질문에 완벽히 답변하세요.\n\n"
    
    if df.empty:
        return context + "현재 로드된 엑셀 데이터가 없습니다."
        
    # 1. 메타 정보 제공 (데이터베이스의 전체 구조 파악을 위해 길드 및 날짜 정보 제공)
    dates = sorted([d for d in df['날짜'].unique() if d.strip() and d != 'Unknown'], reverse=True)
    guilds = [g for g in df['상대 길드'].unique() if g.strip()]
    
    context += f"📊 [전체 데이터 메타 정보]\n"
    context += f"- 총 기록 건수: {len(df)}건\n"
    if dates: context += f"- 기록된 날짜 범위: {dates[-1]} ~ {dates[0]}\n"
    if guilds: context += f"- 기록된 상대 길드 목록: {', '.join(guilds)}\n\n"

    # 2. 질문 키워드 정제
    # 조사를 분리하여 정확한 키워드만 잡을 수 있도록 특수문자 및 공백 처리
    user_query_clean = user_query.replace('?', ' ').replace('!', ' ').replace(',', ' ')
    raw_keywords = [k.strip() for k in user_query_clean.split() if k.strip()]
    
    # 2-1. 영웅 이름 추출
    all_heroes = set()
    for col in ['방어팀_정렬', '공격팀_정렬']:
        for items in df[col].dropna():
            for h in items.split(','):
                all_heroes.add(h.strip())
                
    # 질문에 존재하는 영웅 이름만 추출 (예: "프레이야로" -> "프레이야" 인식)
    extracted_heroes = [h for h in all_heroes if h in user_query_clean]
    expanded_heroes = expand_synonyms(extracted_heroes)
    
    # 2-2. 길드명 추출 (질문 내 포함 여부 확인)
    # 길드 목록에 있는 이름이 질문에 포함되었거나, '길드'를 뺀 단어가 포함된 경우
    extracted_guilds = [g for g in guilds if g in user_query_clean or g.replace('길드', '').strip() in user_query_clean]

    # 3. 데이터 스코어링 (관련성 높은 데이터 추출)
    def calc_score(row):
        score = 0
        def_str = str(row.get('방어팀_정렬', ''))
        atk_str = str(row.get('공격팀_정렬', ''))
        guild_str = str(row.get('상대 길드', ''))
        row_all_text = " ".join(row.astype(str).values)
        
        # (1) 길드 매칭 점수 (최우선순위)
        if extracted_guilds:
            if any(g in guild_str for g in extracted_guilds):
                score += 50
                
        # (2) 영웅 교차 매칭 점수
        def_matches = sum(1 for h in expanded_heroes if h in def_str)
        atk_matches = sum(1 for h in expanded_heroes if h in atk_str)
        
        if def_matches > 0 and atk_matches > 0:
            score += (def_matches * 10) + (atk_matches * 10) # 오공(방) vs 프레이야(공)
        elif atk_matches > 0:
            score += atk_matches * 5 # 특정 영웅을 공덱으로 썼을 때
        elif def_matches > 0:
            score += def_matches * 5 # 특정 영웅 방덱을 상대할 때
            
        # (3) 일반 텍스트 매칭 (길드/영웅 추출 실패를 대비한 보험)
        if not expanded_heroes and not extracted_guilds:
            for k in raw_keywords:
                if len(k) > 1 and k not in ['길드', '방어덱', '공격덱', '어때', '알려줘']:
                    if k in row_all_text:
                        score += 2
                        
        return score

    temp_df = df.copy()
    temp_df['score'] = temp_df.apply(calc_score, axis=1)
    
    # 0점 이상인 관련 데이터 추출 및 정렬 (최대 50건까지만 컨텍스트에 포함)
    relevant_df = temp_df[temp_df['score'] > 0].sort_values(by='score', ascending=False)
    
    # 4. 컨텍스트 텍스트 생성
    if not relevant_df.empty:
        analyzed_df = relevant_df.head(50)
        context += f"🎯 [질문과 직접 관련된 핵심 데이터 {len(analyzed_df)}건 추출됨]\n"
        
        # 길드 정보 요약
        if extracted_guilds:
            for g in extracted_guilds:
                g_df = analyzed_df[analyzed_df['상대 길드'].astype(str).str.contains(g)]
                if not g_df.empty:
                    context += f"🏰 [상대 길드 '{g}'의 주요 방어덱 및 카운터 정보]\n"
                    top_defs = g_df['방어팀_정렬'].value_counts().head(3)
                    for d_name, d_cnt in top_defs.items():
                        context += f"  - 방어덱: [{d_name}] ({d_cnt}회 등장)\n"
                        sub_df = g_df[g_df['방어팀_정렬'] == d_name]
                        top_atks = sub_df['공격팀_정렬'].value_counts().head(2)
                        for a_name, a_cnt in top_atks.items():
                            context += f"    > 카운터 공덱: [{a_name}] ({a_cnt}회 승리)\n"
                    context += "\n"
                    
        # 매치업(영웅) 정보 요약
        if expanded_heroes or (not extracted_guilds and not expanded_heroes):
            patterns = analyzed_df.groupby(['방어팀_정렬', '공격팀_정렬']).size().reset_index(name='count')
            patterns = patterns.sort_values('count', ascending=False).head(10)
            
            context += "⚔️ [가장 많이 사용된 승리 매치업]\n"
            for _, row in patterns.iterrows():
                context += f"- 상대 방어팀: [{row['방어팀_정렬']}]  VS  우리 공격팀: [{row['공격팀_정렬']}] (총 {row['count']}회 승리)\n"
                
                # 상세 세팅
                subset = analyzed_df[(analyzed_df['방어팀_정렬'] == row['방어팀_정렬']) & (analyzed_df['공격팀_정렬'] == row['공격팀_정렬'])]
                pet, _ = get_mode(subset['공격팀 펫'])
                skill, _ = get_mode(subset['공격팀 스순'])
                context += f"    > 당시 세팅: 펫[{pet}], 스킬순서[{skill}]\n"
    else:
        context += "⚠️ 질문하신 내용(길드, 영웅, 특정 날짜 등)에 정확히 일치하는 기록을 엑셀 데이터에서 찾지 못했습니다.\n"
        top_atk = df['공격팀_정렬'].value_counts().head(5)
        context += f"[참고: 전체 통계상 가장 강력한 공덱 Top 5]\n"
        for atk, cnt in top_atk.items():
            context += f"- {atk} ({cnt}회 승리)\n"

    # 5. 수동 공략 (Matchup DB) 연동
    if matchup_db:
        context += "\n📖 [수동 공략 데이터베이스 가이드]\n"
        found_guide = False
        for enemy, guides in matchup_db.items():
            if any(k in enemy for k in expanded_heroes) or any(k in enemy for k in raw_keywords if len(k)>1 and k not in ['길드', '덱']):
                for atk, info in guides.items():
                    context += f"- VS 방어덱 [{enemy}] -> 추천 공덱 [{atk}]\n"
                    context += f"  * 핵심 요약: {info.get('summary')}\n"
                found_guide = True
        if not found_guide: context += "(관련 상세 가이드 없음)\n"

    return context

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
tab1, tab2, tab3, tab4 = st.tabs(["⚔️ 공격 덱 추천", "📖 매치업 상세 가이드", "🤖 AI 전략가 (Beta)", "📢 안내 및 소식"])

# =========================================================
# TAB 1: 공격 추천
# =========================================================
with tab1:
    with st.sidebar:
        st.header("🔍 필터 옵션")
        view_type = st.radio("데이터 기준", ["전체", "공격 (우리가 공격)", "방어 (상대가 공격)"], horizontal=True)
        st.divider()
        search_query = st.text_input("상대 캐릭터 검색", placeholder="예: 카구라, 오공")
        st.caption("공백으로 구분하여 여러 명 검색 가능")
        st.divider()

        unique_dates = sorted(df['날짜'].unique().tolist(), reverse=True)
        if 'selected_date_list' not in st.session_state:
            st.session_state['selected_date_list'] = unique_dates 
        
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
        st.divider()

        all_atk_heroes = set()
        if not df.empty:
            for team in df['공격팀_정렬'].dropna():
                heroes = [h.strip() for h in team.split(',')]
                all_atk_heroes.update(heroes)
        unique_heroes = sorted(list(all_atk_heroes))
        excluded_heroes = st.multiselect("🚫 사용한 영웅 제외", unique_heroes, placeholder="이미 사용한 영웅을 선택하세요")
        if excluded_heroes: st.caption(f"선택한 영웅({len(excluded_heroes)}명)이 포함된 공격 덱은 제외됩니다.")

    filtered_df = df.copy()
    if "공격" in view_type and view_type != "전체": filtered_df = filtered_df[filtered_df['기준'] == '공격']
    elif "방어" in view_type and view_type != "전체": filtered_df = filtered_df[filtered_df['기준'] == '방어']
        
    if search_query:
        query_terms = [k.strip() for k in search_query.replace(',', ' ').split() if k.strip()]
        if query_terms:
            mask = filtered_df['방어팀_정렬'].apply(lambda x: check_match(x, query_terms))
            filtered_df = filtered_df[mask]
    if selected_dates: filtered_df = filtered_df[filtered_df['날짜'].isin(selected_dates)]
    if selected_guilds: filtered_df = filtered_df[filtered_df['상대 길드'].isin(selected_guilds)]
    
    if excluded_heroes:
        excluded_set = set(excluded_heroes)
        mask = filtered_df['공격팀_정렬'].apply(lambda x: set([h.strip() for h in x.split(',')]).isdisjoint(excluded_set))
        filtered_df = filtered_df[mask]

    if filtered_df.empty: st.info("검색 결과가 없습니다.")
    else:
        grouped = filtered_df.groupby('방어팀_정렬')
        display_list = []
        for defense, group in grouped: display_list.append({'defense': defense, 'count': len(group), 'data': group})
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
            
            # [팝업 체크]
            guide_available = False
            matched_guide = None
            matched_enemy_key = ""
            if defense_team in MATCHUP_DB:
                if best_atk_team in MATCHUP_DB[defense_team]:
                    guide_available = True
                    matched_guide = MATCHUP_DB[defense_team][best_atk_team]
                    matched_enemy_key = defense_team
            
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
                        <div class="progress-container"><div class="progress-bg"><div class="progress-fill" style="width: {pick_rate}%; background-color: {bar_color};"></div></div></div>
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
                
                guide_available_sub = False
                matched_guide_sub = None
                matched_enemy_key_sub = ""
                if defense_team in MATCHUP_DB:
                    if atk_team in MATCHUP_DB[defense_team]:
                        guide_available_sub = True
                        matched_guide_sub = MATCHUP_DB[defense_team][atk_team]
                        matched_enemy_key_sub = defense_team
                        
                expander_title = f"⚔️ {atk_team} ({cnt}회 / {ratio:.1f}%)"
                if guide_available_sub: expander_title += "\u00A0" * 4 + ":violet-background[**📖 공략 있음**]"

                with st.expander(expander_title):
                    if guide_available_sub:
                        if st.button("📖 세팅 디테일 보기", key=f"btn_{defense_team}_{atk_team}"):
                            show_guide_popup(matched_enemy_key_sub, atk_team, matched_guide_sub)
                            
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
# TAB 2: 매치업 상세 가이드
# =========================================================
with tab2:
    st.header("📖 매치업 상세 가이드")
    st.caption("특정 방덱을 상대로 어떤 공덱을 어떻게 써야 하는지 확인하세요.")
    search_query_guide = st.text_input("🛡️ 상대 방덱 검색", placeholder="예: 카구라, 오공 (비워두면 전체 보기)")
    
    all_enemies = list(MATCHUP_DB.keys())
    target_enemies = []
    
    if search_query_guide:
        query_terms = [k.strip() for k in search_query_guide.replace(',', ' ').split() if k.strip()]
        if query_terms: target_enemies = [e for e in all_enemies if check_match(e, query_terms)]
    else: target_enemies = all_enemies
    
    if not target_enemies: st.info("검색 결과가 없습니다.")
    else:
        for enemy_name in target_enemies:
            with st.expander(f"🛡️ VS {enemy_name}", expanded=False):
                my_decks_map = MATCHUP_DB[enemy_name]
                if len(my_decks_map) > 1:
                    tabs = st.tabs([f"⚔️ {name}" for name in my_decks_map.keys()])
                    for i, (my_deck_name, guide) in enumerate(my_decks_map.items()):
                        with tabs[i]:
                            html_content = generate_guide_html(enemy_name, my_deck_name, guide)
                            st.markdown(clean_html(html_content), unsafe_allow_html=True)
                else:
                    my_deck_name = list(my_decks_map.keys())[0]
                    guide = my_decks_map[my_deck_name]
                    html_content = generate_guide_html(enemy_name, my_deck_name, guide)
                    st.markdown(clean_html(html_content), unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# =========================================================
# TAB 3: AI 전략가 (Gemini)
# =========================================================
with tab3:
    st.header("🤖 AI 전략가 (Beta)")
    st.caption("판다 길드전 데이터를 학습한 AI에게 질문해보세요!")

    if not HAS_GENAI:
        st.error("⚠️ `google-generativeai` 라이브러리가 설치되지 않았습니다. 관리자에게 문의하세요.")
        st.stop()
    
    USER_API_KEY = "AIzaSyCVW8xwrXj3QXEMfKRlniDKHWKniPth0I0"
    
    if USER_API_KEY:
        os.environ["GOOGLE_API_KEY"] = USER_API_KEY
        genai.configure(api_key=USER_API_KEY)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("질문을 입력하세요.. (예: 프레이야 사용해서 오공 겔리두스 에이스 덱 잡을 수 있어?)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        if not USER_API_KEY:
             response = "🔒 **API Key가 설정되지 않았습니다.** 관리자에게 문의하세요."
        else:
            try:
                # 데이터 분석 및 요약 생성 (업그레이드된 로직 호출)
                data_context = get_ai_context(df, MATCHUP_DB, user_query=prompt)
                
                candidate_models = [
                    'gemini-3.1-pro-preview', 
                    'gemini-2.0-flash',
                    'gemini-1.5-flash'
                ]
                
                response_text = ""
                error_msg = ""
                
                for model_name in candidate_models:
                    try:
                        model = genai.GenerativeModel(model_name)
                        full_prompt = f"""
                        너는 '세븐나이츠 리버스' 게임의 길드전 전략 전문가야.
                        아래 제공된 [길드전 데이터]를 바탕으로 사용자의 질문에 답변해줘.
                        
                        [답변 원칙]
                        1. **분석된 데이터** (길드 정보, 방어팀/공격팀 매칭 횟수 등)를 최우선 근거로 제시해줘.
                        2. 사용자가 특정 길드(예: 밤빛)를 물어봤다면, 해당 길드의 데이터 요약을 바탕으로 자주 나오는 방덱과 그 카운터 공덱을 분석해줘.
                        3. 사용자가 특정 매치업(A 상대로 B 덱 어때?)을 물어봤다면, 해당 매치업의 승리 횟수나 세팅을 구체적으로 알려줘.
                        4. 데이터가 없다면 "데이터에는 해당 기록이 없습니다"라고 솔직히 말하고, 일반적인 상성 지식을 활용해 조언해줘.
                        5. 답변은 친절하고 간결하게, 가독성 좋게 정리해줘.

                        [길드전 데이터]
                        {data_context}

                        사용자 질문: {prompt}
                        """
                        with st.spinner(f"AI({model_name})가 데이터를 분석 중입니다..."):
                            ai_response = model.generate_content(full_prompt)
                            response_text = ai_response.text
                            break 
                    except Exception as e:
                        error_msg = str(e)
                        continue 
                
                if response_text:
                    response = response_text
                else:
                    response = f"🚫 모든 AI 모델 연결 실패. (Last Error: {error_msg})"

            except Exception as e:
                response = f"🚫 오류가 발생했습니다: {str(e)}"

        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

# =========================================================
# TAB 4: 안내 및 소식
# =========================================================
with tab4:
    help_tab, notice_tab = st.tabs(["📘 사이트 사용법", "📢 공지사항"])
    
    with help_tab:
        st.markdown("#### 👋 환영합니다! 이렇게 사용해보세요.")
        with st.expander("🐼 **사이트 소개 및 활용 가이드**", expanded=True):
            st.markdown("""
            **판다 길드전**의 공격 성공 및 방어 실패 데이터를 분석하여 만든 **전적 통계 사이트**입니다.
            **🎯 이럴 때 활용하세요!**
            - **공격 조합이 고민될 때**: 데이터로 검증된 고승률 공격 조합을 찾아보세요.
            - **영웅이 부족할 때**: "이 조합으로도 잡네?" 싶은 새로운 조커 덱을 발견할 수 있습니다.
            > **⚠️ 주의사항** > 제공되는 정보는 통계 데이터입니다. 상대의 세부 스펙에 따라 결과가 다를 수 있으니, 익숙하지 않은 조합은 반드시 **연습 모드**를 활용해 보세요.
            """)
        with st.expander("🔍 **원하는 상대 방덱을 찾고 싶어요**", expanded=True):
            st.markdown("""<ul style="padding-left: 20px; margin: 0; line-height: 1.6;"><li>왼쪽 사이드바의 <b>'상대 캐릭터 검색'</b> 창에 캐릭터 이름을 입력하세요.</li><li>예: 오공, 카구라 등 핵심 영웅 이름을 입력하면 관련 방덱만 필터링됩니다.</li><li>콤마(,)나 공백으로 구분하여 여러 명을 동시에 검색할 수도 있습니다.</li></ul>""", unsafe_allow_html=True)
        with st.expander("⚔️ **어떤 공격덱이 좋은지 모르겠어요**"):
            st.markdown("""<ul style="padding-left: 20px; margin: 0; line-height: 1.6;"><li><b>'공격 덱 추천' 탭</b>에서 데이터를 확인하세요.</li><li>가장 많이 사용된 공격덱이 상단에 표시됩니다.</li><li><b>'픽률'</b>이 높고 <b>'표본(데이터 수)'</b>이 많은 덱을 사용하는 것을 추천합니다.</li></ul>""", unsafe_allow_html=True)
        with st.expander("📖 **상세한 덱 세팅과 운영법이 궁금해요**"):
            st.markdown("""<ul style="padding-left: 20px; margin: 0; line-height: 1.6;"><li><b>'매치업 상세 가이드' 탭</b>으로 이동해 보세요.</li><li>길드전 사용 빈도가 높은 방어덱을 상대로 어떤 조합, 장비, 펫, 스킬 순서를 써야 하는지 자세히 적혀 있습니다.</li><li>'공격 덱 추천' 탭에서도 <b>'📖 공략 있음'</b> 배지가 있는 경우, 버튼을 눌러 바로 가이드를 볼 수 있습니다.</li></ul>
            <div style="margin-top: 10px; padding: 12px; background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
                <div style="font-weight: bold; color: #334155; margin-bottom: 5px;">🧩 세팅 난이도 가이드</div>
                <ul style="list-style-type: none; padding-left: 0; margin: 0; font-size: 0.9rem; color: #475569;">
                    <li style="margin-bottom: 5px;"><span style="background-color: #dcfce7; color: #166534; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 0.8rem;">★ 1~2개</span> 쉬우면서 승률이 높은 세팅</li>
                    <li style="margin-bottom: 5px;"><span style="background-color: #fef9c3; color: #854d0e; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 0.8rem;">★ 3개</span> 장비 세팅이 까다롭거나 전반 요구도가 있는 세팅</li>
                    <li><span style="background-color: #fee2e2; color: #991b1b; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 0.8rem;">★ 4~5개</span> 세팅이 까다롭고, 확실히 하지 않으면 승률이 낮을 수 있음</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    with notice_tab:
        st.caption("최신 업데이트 내역입니다.")
        if NOTICE_DB:
            for notice in NOTICE_DB:
                with st.expander(f"📅 {notice['date']} 업데이트", expanded=True):
                    st.markdown(notice['content'], unsafe_allow_html=True)
        else:
            st.info("등록된 공지사항이 없습니다.")

# Footer
st.markdown("""
    <div style='text-align: center; color: #9ca3af; font-size: 0.8rem; margin-top: 50px;'>
        데이터 출처: 판다 길드전 내용 | 문의: 콩쌍
    </div>
""", unsafe_allow_html=True)



