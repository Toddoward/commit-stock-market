import streamlit as st
import time
import yfinance as yf
# [NEW] 공통 로직 불러오기
from utils import init_connection, add_user_to_db, sync_missing_data

# --- 페이지 설정 ---
st.set_page_config(
    page_title="Commit Stock Market",
    page_icon="https://images.therich.io/images/logo/kr/316140.png?timestamp=1748519881",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 실시간 데이터 가져오기 ---
@st.cache_data(ttl=300)
def get_market_data():
    symbols = ['MSFT', 'NVDA', 'AAPL', 'BTC-USD']
    data_list = []
    try:
        tickers = yf.Tickers(' '.join(symbols))
        for symbol in symbols:
            info = tickers.tickers[symbol].fast_info
            price = info.last_price
            prev_close = info.previous_close
            change_pct = ((price - prev_close) / prev_close) * 100
            name = symbol.replace('-USD', '')
            data_list.append({"name": name, "price": f"{price:,.2f}", "change": change_pct})
    except Exception:
        data_list = [{"name": "SYSTEM", "price": "ONLINE", "change": 0.0}]
    return data_list

# --- 커스텀 CSS (보내주신 디자인 100% 유지) ---
st.markdown("""
<style>
    /* 1. 상단 여백 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* 2. 폰트 설정 */
    .stTextInput input, .stNumberInput input {
        font-family: 'Roboto Mono', 'Courier New', monospace !important;
        font-weight: 600;
    }

    /* 3. 배경 애니메이션 */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(-45deg, #02040a, #0d1117, #010409);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
    }
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }
    
    /* 4. 티커 스타일 (Slim Black) */
    .ticker-wrap {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        overflow: hidden;
        height: 2.0rem;
        background-color: #000000; 
        border-bottom: 1px solid #06b6d4;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
        padding-left: 100%;
        box-sizing: content-box;
        z-index: 9999;
    }
    .ticker {
        display: inline-block;
        height: 2.0rem;
        line-height: 2.0rem;
        white-space: nowrap;
        padding-right: 100%;
        box-sizing: content-box;
        animation: ticker 50s linear infinite;
    }
    .ticker-item {
        display: inline-block;
        padding: 0 2rem;
        font-size: 0.9rem;
        color: #ffffff;
        font-weight: 600;
        font-family: 'Roboto Mono', monospace;
    }
    .up { color: #3fb950; font-weight: 800; } 
    .down { color: #ff6e6e; font-weight: 800; } 
    .flat { color: #8b949e; }

    @keyframes ticker {
        0% { transform: translate3d(0, 0, 0); }
        100% { transform: translate3d(-100%, 0, 0); }
    }

    /* 5. 메인 타이틀 & 서브타이틀 */
    .main-title {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 5px; 
        white-space: nowrap;
        background: linear-gradient(to right, #FFFFFF 0%, #FFFFFF 40%, #5edfff 50%, #FFFFFF 60%, #FFFFFF 100%);
        background-size: 200% auto;
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 5s linear infinite;
    }
    @keyframes shine { to { background-position: 200% center; } }

    .sub-title {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #e0f2fe; 
        font-weight: 500;
        font-size: 1.1rem;
        letter-spacing: 1px;
        text-shadow: 0 0 10px rgba(94, 223, 255, 0.3);
        margin: 0;
    }

    /* 6. 떠다니는 헤더 박스 */
    .floating-header {
        animation: float 6s ease-in-out infinite;
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.95));
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(148, 163, 184, 0.4); 
        border-radius: 16px;
        padding: 30px 40px;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8), 0 0 15px rgba(56, 189, 248, 0.1);
        display: inline-block;
        min-width: 400px;
    }
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-15px); }
        100% { transform: translateY(0px); }
    }
    
    /* 7. UI 요소 스타일 */
    div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(90deg, #2563eb 0%, #06b6d4 100%) !important;
        border: none !important;
        color: white !important;
        font-family: 'Helvetica Neue', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        padding: 0.6rem 1rem !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
    }
    div[data-testid="stFormSubmitButton"] > button:hover {
        background: linear-gradient(90deg, #1d4ed8 0%, #0891b2 100%) !important;
        transform: translateY(-2px);
        box-shadow: 0 0 25px rgba(6, 182, 212, 0.7) !important;
    }
    div[data-testid="stFormSubmitButton"] > button:active {
        transform: translateY(1px);
        box-shadow: none !important;
    }
    
    /* 인원수 입력창 스타일링 */
    div[data-testid="stNumberInput"] label {
        color: #5edfff !important;
        font-family: 'Helvetica Neue', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    div[data-testid="stNumberInput"] > div > div {
        background-color: rgba(20, 24, 35, 0.6) !important;
        border: 1px solid rgba(94, 223, 255, 0.4) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
    }
    div[data-testid="stNumberInput"] input {
        color: #5edfff !important;
        font-family: 'Roboto Mono', monospace !important;
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        background-color: transparent !important;
        text-align: center !important;
    }
    
    /* +/- 버튼 스타일 */
    div[data-testid="stNumberInput"] button {
        color: #e0f2fe !important;
        border-color: rgba(94, 223, 255, 0.2) !important;
        background-color: transparent !important; /* 기본 배경 투명 */
    }
    
    /* 마우스 올렸을 때 */
    div[data-testid="stNumberInput"] button:hover {
        color: #5edfff !important;
        background-color: rgba(94, 223, 255, 0.1) !important; /* 연한 Cyan */
        border-color: #5edfff !important;
    }
    
    /* [핵심] 클릭 중일 때 (Active) + 클릭 후 (Focus) */
    div[data-testid="stNumberInput"] button:active,
    div[data-testid="stNumberInput"] button:focus,
    div[data-testid="stNumberInput"] button:focus-visible {
        color: #ffffff !important;
        background-color: rgba(6, 182, 212, 0.5) !important; /* Cyan 배경 (빨강 대체) */
        border-color: #5edfff !important;
        box-shadow: none !important; /* 빨간 글로우 제거 */
        outline: none !important;
    }

    .stMarkdown h1 a, .stMarkdown h2 a, .stMarkdown h3 a, 
    .stMarkdown h4 a, .stMarkdown h5 a, .stMarkdown h6 a {
        display: none !important;
        pointer-events: none;
    }
</style>
""", unsafe_allow_html=True)

# --- 실제 데이터 생성 ---
market_data = get_market_data()
ticker_html_content = ""

for item in market_data:
    if item['change'] > 0:
        color_class = "up"
        arrow = "▲"
        sign = "+"
    elif item['change'] < 0:
        color_class = "down"
        arrow = "▼"
        sign = ""
    else:
        color_class = "flat"
        arrow = "-"
        sign = ""
    ticker_html_content += f"""<span class="ticker-item">{item['name']}: ${item['price']} <span class="{color_class}">{arrow} {sign}{item['change']:.2f}%</span></span>"""

ticker_html_content += """<span class="ticker-item">GITHUB: <span class="up">OPERATIONAL</span></span><span class="ticker-item">MARKET: <span class="up">OPEN 24/7</span></span>"""

# 티커 렌더링
st.markdown(f"""
<div class="ticker-wrap">
<div class="ticker">
{ticker_html_content}
</div>
</div>
""", unsafe_allow_html=True)

# --- 메인 로직 ---
if 'user_data' not in st.session_state:
    st.session_state['user_data'] = []

try:
    col_header, col_settings = st.columns([3, 1])
except TypeError:
    col_header, col_settings = st.columns([3, 1])

with col_header:
    st.markdown("""
        <div class="floating-header">
            <div class="main-title">Commit Stock Market</div>
            <div class="sub-title">Evaluate your development assets objectively.</div>
        </div>
    """, unsafe_allow_html=True)

with col_settings:
    st.write("") 
    st.write("") 
    st.markdown("<div style='margin-top: 45px;'></div>", unsafe_allow_html=True)
    num_users = st.number_input("PARTICIPANTS", min_value=1, max_value=5, value=2)

st.divider()

with st.form("listing_form"):
    st.markdown('<div style="font-size:1.1rem; font-weight:600; color:#E0E0E0; margin-bottom:1rem;">MARKET ADMISSION DETAILS</div>', unsafe_allow_html=True)
    
    cols = st.columns(int(num_users))
    users_temp = []
    
    for i, col in enumerate(cols):
        with col:
            with st.container(border=True):
                st.markdown(f"**ASSET 0{i+1}**")
                nickname = st.text_input("Nickname", key=f"nick_{i}", placeholder="User ID", label_visibility="collapsed")
                st.caption("Asset Name (ID)")
                repo_url = st.text_input("Repo URL", key=f"repo_{i}", placeholder="Repo URL", label_visibility="collapsed")
                st.caption("Source Code URL")
                users_temp.append({"nickname": nickname, "repo_url": repo_url})
    
    st.write("") 
    submit_btn = st.form_submit_button("CONFIRM LISTING", use_container_width=True, type="primary")

# --- [추가] 제출 버튼 로직 ---
if submit_btn:
    valid_data = [u for u in users_temp if u['nickname'].strip() and u['repo_url'].strip()]
    
    if len(valid_data) < num_users:
        st.toast("⚠️ 모든 자산 정보를 입력해야 상장이 가능합니다.", icon="🚨")
    else:
        # 1. DB 연결 체크
        conn = init_connection()
        if not conn:
            st.error("DB 연결 실패! secrets.toml 설정을 확인하세요.")
        else:
            # 2. UI 효과 (처리 중)
            msg = st.toast("상장 심사 서류 검토 중...", icon="📂")
            progress_bar = st.progress(0)
            
            # 3. 데이터 저장 (Loop)
            for idx, user in enumerate(valid_data):
                # DB에 유저 추가
                add_user_to_db(conn, user['nickname'], user['repo_url'])
                time.sleep(0.3) # 연출용 딜레이
                progress_bar.progress(int((idx + 1) / len(valid_data) * 50))
            
            # 4. 데이터 동기화 (GitHub API)
            msg.toast("자산 가치 평가 중 (GitHub Data Sync)...", icon="⏳")
            sync_missing_data(conn) 
            progress_bar.progress(100)
            
            msg.toast("상장 승인 완료! 시장으로 이동합니다.", icon="✅")
            time.sleep(0.8)
            
            # 5. 페이지 이동 (Ranking.py)
            try:
                st.switch_page("pages/1-Ranking.py")
            except Exception:
                st.error("이동할 페이지(Ranking.py)를 찾을 수 없습니다.")