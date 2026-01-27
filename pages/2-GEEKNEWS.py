import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
import re
import yfinance as yf



# --- 0. 시장 데이터 캐싱 (티커용) ---
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

# --- 페이지 설정 ---
st.set_page_config(page_title="Commit Stock Market", page_icon="https://images.therich.io/images/logo/kr/316140.png?timestamp=1748519881", layout="wide")

# --- 커스텀 CSS (Home.py 컨셉 이식) ---
st.markdown("""
<style>
    /* 배경 애니메이션 */
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

    /* 티커 스타일 (Slim Black) */
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

    /* 메인 타이틀 (Shine 효과) */
    .main-title {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 800;
        font-size: 3rem;
        margin-top: 60px;
        margin-bottom: 40px;
        text-align: center;
        background: linear-gradient(to right, #FFFFFF 0%, #FFFFFF 40%, #5edfff 50%, #FFFFFF 60%, #FFFFFF 100%);
        background-size: 200% auto;
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 5s linear infinite;
    }
    @keyframes shine { to { background-position: 200% center; } }

    /* 뉴스 카드 커스텀 (Cyan 포인트) */
    .news-card {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(10px);
        padding: 40px 30px 30px 30px;
        border-radius: 16px;
        border: 1px solid rgba(148, 163, 184, 0.2); 
        margin-bottom: 25px;
        min-height: 220px; 
        display: flex;
        flex-direction: column;
        position: relative;
        transition: all 0.3s ease;
    }
    .news-card:hover {
        border-color: #06b6d4;
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(6, 182, 212, 0.2);
        background: rgba(30, 41, 59, 0.8);
    }

    .rank-badge {
        position: absolute;
        top: 0;
        left: 0;
        background: linear-gradient(90deg, #2563eb 0%, #06b6d4 100%);
        color: white;
        font-weight: 800;
        font-size: 0.75rem;
        padding: 5px 15px;
        border-radius: 16px 0 16px 0;
        letter-spacing: 1px;
    }
    
    .news-title { 
        color: #f8fafc !important; 
        font-size: 1.3rem; 
        font-weight: 700; 
        text-decoration: none !important; 
        line-height: 1.4;
        margin-bottom: 12px;
        transition: color 0.3s ease;
    }
    .news-title:hover { color: #5edfff !important; }
    
    .news-meta { 
        color: #5edfff; 
        font-size: 0.8rem; 
        margin-bottom: 15px;
        font-weight: 600;
        font-family: 'Roboto Mono', monospace;
    }
    
    .news-desc { 
        color: #cbd5e1; 
        font-size: 0.95rem; 
        line-height: 1.6;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
    }

    /* 구분선 스타일 */
    hr { border: 0; height: 1px; background: linear-gradient(to right, transparent, rgba(94, 223, 255, 0.5), transparent); }
</style>
""", unsafe_allow_html=True)

# --- 뉴스 크롤링 로직 ---
@st.cache_data(ttl=600)
def get_cleaned_geeknews():
    base_url = "https://news.hada.io/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(base_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = []
        for topic in soup.select('.topic_row')[:20]:
            title_tag = topic.select_one('.topictitle a')
            if not title_tag: continue
            
            title = title_tag.text.strip()
            link = urljoin(base_url, title_tag['href'])
            
            desc_area = topic.select_one('.topicdesc')
            if desc_area:
                for extra in desc_area.find_all(['div', 'script', 'style', 'br']):
                    extra.decompose()
                desc_text = desc_area.get_text(separator=" ").strip()
                desc_text = re.sub(r'#+', '', desc_text)
            else:
                desc_text = ""
            
            meta_text = topic.select_one('.topicinfo').text.strip() if topic.select_one('.topicinfo') else ""
            items.append({'title': title, 'link': link, 'desc': desc_text, 'meta': meta_text})
        return items
    except:
        return []

# --- 티커 렌더링 ---
market_data = get_market_data()
ticker_html_content = ""
for item in market_data:
    if item['change'] > 0: c, a, s = "up", "▲", "+"
    elif item['change'] < 0: c, a, s = "down", "▼", ""
    else: c, a, s = "flat", "-", ""
    ticker_html_content += f'<span class="ticker-item">{item["name"]}: ${item["price"]} <span class="{c}">{a} {s}{item["change"]:.2f}%</span></span>'

st.markdown(f"""
<div class="ticker-wrap">
    <div class="ticker">
        {ticker_html_content}
        <span class="ticker-item">NEWS: <span class="up">LIVE FEED</span></span>
        <span class="ticker-item">SOURCE: GEEKNEWS</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 메인 레이아웃 ---
st.markdown('<div class="main-title">GEEKNEWS TOP 20</div>', unsafe_allow_html=True)

news_list = get_cleaned_geeknews()

if news_list:
    # 중앙 정렬을 위한 컨테이너 칼럼
    _, mid_col, _ = st.columns([1, 10, 1])
    with mid_col:
        for i in range(0, len(news_list), 2):
            cols = st.columns(2)
            
            # 좌측 카드 (i + 1위)
            with cols[0]:
                n = news_list[i]
                st.markdown(f"""
                    <div class="news-card">
                        <div class="rank-badge">RANK {i+1:02d}</div>
                        <div class="news-meta">{n['meta']}</div>
                        <a href="{n['link']}" target="_blank" class="news-title">{n['title']}</a>
                        <div class="news-desc">{n['desc']}</div>
                    </div>
                """, unsafe_allow_html=True)
                
            # 우측 카드 (i + 2위)
            if i + 1 < len(news_list):
                with cols[1]:
                    n = news_list[i+1]
                    st.markdown(f"""
                        <div class="news-card">
                            <div class="rank-badge">RANK {i+2:02d}</div>
                            <div class="news-meta">{n['meta']}</div>
                            <a href="{n['link']}" target="_blank" class="news-title">{n['title']}</a>
                            <div class="news-desc">{n['desc']}</div>
                        </div>
                    """, unsafe_allow_html=True)
else:
    st.info("데이터를 동기화하는 중입니다...")

st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()
st.caption(f"TERMINAL UPDATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")