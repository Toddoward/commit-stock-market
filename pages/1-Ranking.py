import streamlit as st
import pandas as pd
import colorsys
import yfinance as yf
import pymysql
from datetime import datetime
from utils import init_connection, init_engine, sync_missing_data

# --- 0. 시장 데이터 캐싱 함수 ---
@st.cache_data(ttl=300)
def get_market_data():
    target_symbols = ['MSFT', 'NVDA', 'AAPL', 'GOOGL', 'TSLA', '005930.KS', '000660.KS', 'BTC-USD']
    all_symbols = target_symbols + ['KRW=X']
    data_list = []
    try:
        tickers = yf.Tickers(' '.join(all_symbols))
        try: usd_krw_rate = tickers.tickers['KRW=X'].fast_info.last_price
        except: usd_krw_rate = 1400.0
        for symbol in target_symbols:
            try:
                info = tickers.tickers[symbol].fast_info
                price, prev_close = info.last_price, info.previous_close
                change_pct = ((price - prev_close) / prev_close) * 100
                if '.KS' in symbol: price = price / usd_krw_rate
                if symbol == '005930.KS': name = "SAMSUNG"
                elif symbol == '000660.KS': name = "SK HYNIX"
                else: name = symbol.replace('-USD', '')
                price_str = f"{price:,.2f}"
                data_list.append({"name": name, "price": price_str, "change": change_pct})
            except: continue
    except:
        data_list = [{"name": "SYSTEM", "price": "ONLINE", "change": 0.0}]
    return data_list

# DB 연결 및 엔진 초기화
conn = init_connection()
engine = init_engine()

def get_user_color(user_id):
    base_hues = [210/360, 150/360, 35/360, 0/360, 260/360, 330/360, 190/360]
    cycle, hue_idx = divmod(user_id, len(base_hues))
    h = base_hues[hue_idx]
    s, l = max(0.2, 0.8 - (cycle * 0.2)), min(0.8, 0.6 + (cycle * 0.05))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return '#%02x%02x%02x' % (int(r*255), int(g*255), int(b*255))

# --- 2. 페이지 구성 ---
st.set_page_config(page_title="Commit Stock Market - Ranking", page_icon="https://images.therich.io/images/logo/kr/316140.png?timestamp=1748519881", layout="wide")

if 'initialized' not in st.session_state:
    with st.spinner("최신 데이터 수신 중..."):
        sync_missing_data(conn)
    st.session_state['initialized'] = True

# --- 3. 커스텀 CSS ---
st.markdown("""
<style>
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
    [data-testid="stHeader"] { background-color: transparent !important; }
    .ticker-wrap {
        position: fixed; top: 0; left: 0; width: 100%; overflow: hidden; height: 2.0rem;
        background-color: #000000; border-bottom: 1px solid #06b6d4;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5); padding-left: 100%; box-sizing: content-box; z-index: 9999;
    }
    .ticker {
        display: inline-block; height: 2.0rem; line-height: 2.0rem; white-space: nowrap;
        padding-right: 100%; box-sizing: content-box; animation: ticker 50s linear infinite;
    }
    .ticker-item { display: inline-block; padding: 0 2rem; font-size: 0.9rem; color: #ffffff; font-weight: 600; font-family: 'Roboto Mono', monospace; }
    .up { color: #3fb950; font-weight: 800; } 
    .down { color: #ff6e6e; font-weight: 800; } 
    .flat { color: #8b949e; }
    @keyframes ticker { 0% { transform: translate3d(0, 0, 0); } 100% { transform: translate3d(-100%, 0, 0); } }
    .main-title {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 800; font-size: 3rem;
        margin-top: 40px; margin-bottom: 20px; text-align: center;
        background: linear-gradient(to right, #FFFFFF 0%, #FFFFFF 40%, #5edfff 50%, #FFFFFF 60%, #FFFFFF 100%);
        background-size: 200% auto; background-clip: text; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: shine 5s linear infinite;
    }
    @keyframes shine { to { background-position: 200% center; } }
    .rank-card {
        background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between;
        align-items: center; height: 48px; padding: 0 20px; transition: all 0.3s ease;
    }
    .rank-card:hover { border-color: #06b6d4; background: rgba(30, 41, 59, 0.9); }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Market Admin")
    if st.button("Sync Market Data", use_container_width=True):
        with st.spinner("Updating..."):
            sync_missing_data(conn)
        st.rerun()
    st.divider()
    if st.button("Go to Home", use_container_width=True):
        st.switch_page("Home.py")
    if st.button("Go to GeekNews", use_container_width=True):
        st.switch_page("pages/2-GEEKNEWS.py")

# --- 티커 렌더링 ---
market_data = get_market_data()
ticker_html_content = ""
for item in market_data:
    if item['change'] > 0: c, a, s = "up", "▲", "+"
    elif item['change'] < 0: c, a, s = "down", "▼", ""
    else: c, a, s = "flat", "-", ""
    ticker_html_content += f'<span class="ticker-item">{item["name"]}: ${item["price"]} <span class="{c}">{a} {s}{item["change"]:.2f}%</span></span>'
ticker_html_content += '<span class="ticker-item">GITHUB: <span class="up">OPERATIONAL</span></span><span class="ticker-item">MARKET: <span class="up">OPEN 24/7</span></span>'
st.markdown(f'<div class="ticker-wrap"><div class="ticker">{ticker_html_content}</div></div>', unsafe_allow_html=True)

st.markdown('<div class="main-title">WEEKLY RANKING</div>', unsafe_allow_html=True)

# --- 4. 랭킹 및 차트 섹션 ---
try:
    # 핵심 수정: engine을 사용하여 read_sql 호출 (Warning 해결)
    query = "SELECT u.id, u.nickname, d.commit_date, d.count FROM daily_commits d JOIN users u ON d.user_id = u.id ORDER BY d.commit_date ASC"
    df = pd.read_sql(query, engine)
    
    if not df.empty:
        df['commit_date'] = pd.to_datetime(df['commit_date'])
        chart_data = df.pivot(index='commit_date', columns='nickname', values='count').fillna(0)
        moving_avg_data = chart_data.rolling(window=7, min_periods=1).mean()
        last_date = chart_data.index.max()
        filtered_chart_data = moving_avg_data.loc[last_date - pd.Timedelta(days=14):last_date]
        
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nickname FROM users")
            users_info = cursor.fetchall()
            user_to_id = {u['nickname']: u['id'] for u in users_info}
            
            tile_list = []
            for user in users_info:
                cursor.execute("SELECT count FROM daily_commits WHERE user_id = %s ORDER BY commit_date DESC LIMIT 14", (user['id'],))
                rows = cursor.fetchall()
                counts = [row['count'] for row in rows] + [0]*14
                curr_ma = sum(counts[:7]) / 7
                diff = curr_ma - (sum(counts[7:14]) / 7)
                tile_list.append({'id': user['id'], 'nickname': user['nickname'], 'curr_ma': curr_ma, 'diff': diff})

        tile_list.sort(key=lambda x: x['curr_ma'], reverse=True)
        top_10 = tile_list[:10]

        # 포디움 UI
        p_col = st.columns([1, 1, 1])
        def draw_podium(data, rank, icon, height, m_top):
            c = "#3fb950" if data['diff'] > 0 else "#ff6e6e" if data['diff'] < 0 else "#ffffff"
            st.markdown(f"""
                <div style="height:{m_top}px;"></div>
                <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.9)); border-radius:15px; padding:20px 5px; text-align:center; height:{height}px; border:1px solid rgba(94, 223, 255, 0.3); display:flex; flex-direction:column; justify-content:center; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
                    <div style="font-size:1.5rem;">{icon}</div>
                    <div style="color:#5edfff; font-size:0.75rem; font-weight:700; letter-spacing:1px;">TOP {rank} ASSET</div>
                    <div style="color:white; font-size:1.2rem; font-weight:800; overflow:hidden; margin: 5px 0;">{data['nickname']}</div>
                    <div style="color:white; font-size:2rem; font-weight:900; text-shadow: 0 0 10px rgba(94, 223, 255, 0.5);">{data['curr_ma']:.2f}</div>
                    <div style="color:{c}; font-weight:bold; font-family: 'Roboto Mono', monospace;">{data['diff']:+.2f}</div>
                </div>
            """, unsafe_allow_html=True)

        if len(top_10) >= 3:
            with p_col[0]: draw_podium(top_10[1], 2, "🥈", 260, 40)
            with p_col[1]: draw_podium(top_10[0], 1, "👑", 300, 0)
            with p_col[2]: draw_podium(top_10[2], 3, "🥉", 230, 70)

        st.write("")
        st.divider()

        # 차트 및 리스트
        c1, c2 = st.columns([2.2, 1])
        with c1:
            st.markdown('<p style="color:#5edfff; font-weight:700; margin-bottom:10px;">ASSET PERFORMANCE INDEX (7D MA)</p>', unsafe_allow_html=True)
            names = [t['nickname'] for t in top_10]
            display_chart_data = filtered_chart_data[names].copy()
            final_colors = [get_user_color(user_to_id[name]) for name in names]
            display_chart_data.columns = [f"{'👑' if i==0 else '🥈' if i==1 else '🥉' if i==2 else ''} {n}" for i, n in enumerate(names)]
            st.line_chart(display_chart_data, color=final_colors, height=380)
            
        with c2:
            st.markdown('<p style="color:#5edfff; font-weight:700; margin-bottom:10px;">MARKET QUOTES</p>', unsafe_allow_html=True)
            for i, s in enumerate(top_10[3:]):
                c = "#3fb950" if s['diff'] > 0 else "#ff6e6e" if s['diff'] < 0 else "#ffffff"
                st.markdown(f"""
                    <div class="rank-card" style="border-left: 5px solid {get_user_color(s['id'])};">
                        <span style="color:white; font-weight:600;">{i+4}. {s['nickname']}</span>
                        <span style="color:{c}; font-weight:bold; font-family: 'Roboto Mono', monospace;">{s['curr_ma']:.2f} ({s['diff']:+.2f})</span>
                    </div>
                """, unsafe_allow_html=True)
except Exception as e:
    st.error(f"Error: {e}")