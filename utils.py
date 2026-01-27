import streamlit as st
import pymysql.cursors
import requests
import pandas as pd
from datetime import datetime, timezone
from sqlalchemy import create_engine

# 1. DB 연결 (기존 INSERT/UPDATE CRUD 작업용)
def init_connection():
    if "mysql" not in st.secrets:
        return None
    return pymysql.connect(**st.secrets["mysql"])

# 2. SQLAlchemy 엔진 연결 (Pandas read_sql 전용 - Warning 해결용)
@st.cache_resource
def init_engine():
    if "mysql" not in st.secrets:
        return None
    db_config = st.secrets["mysql"]
    user = db_config['user']
    pw = db_config['password']
    host = db_config['host']
    db = db_config['database']
    port = db_config.get('port', 3306)
    
    # SQLAlchemy용 URI 문자열 생성
    uri = f"mysql+pymysql://{user}:{pw}@{host}:{port}/{db}"
    return create_engine(uri)

# 3. 유저 추가
def add_user_to_db(conn, nickname, repo_url):
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT IGNORE INTO users (nickname, repo_url) VALUES (%s, %s)", (nickname, repo_url))
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Insert Error: {e}")
        return False

# 4. 데이터 동기화
def sync_missing_data(conn):
    if not conn: return 0
    
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT id, nickname, repo_url FROM users")
    users = cursor.fetchall()
    
    # 1. 헤더 설정 수정 (클래식 토큰은 'token' 접두사가 더 안정적일 수 있음)
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    github_token = st.secrets.get("github", {}).get("token")
    
    if github_token:
        # 클래식 토큰(ghp_...)은 'token' 접두사를 사용하는 것이 표준입니다.
        headers["Authorization"] = f"token {github_token}"
    else:
        print("⚠️ GitHub 토큰이 설정되지 않았습니다. (Rate Limit에 걸릴 수 있음)")
    
    today_dt = datetime.now(timezone.utc)
    since_date_str = (today_dt - pd.Timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    updated_total = 0
    print(f"🔄 동기화 시작 (대상: {len(users)}명)")

    for user in users:
        try:
            clean_url = user['repo_url'].strip().rstrip('/').replace('.git', '')
            parts = clean_url.split('/')
            if len(parts) < 2: continue
            
            owner, repo = parts[-2], parts[-1]
            api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
            params = {"since": since_date_str, "per_page": 100}
            
            response = requests.get(api_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                commits = response.json()
                print(f"✅ {user['nickname']} ({owner}/{repo}): 커밋 {len(commits)}개 발견")
                
                date_counts = {}
                for commit in commits:
                    raw_date = commit['commit']['author']['date'].split('T')[0]
                    date_counts[raw_date] = date_counts.get(raw_date, 0) + 1
                
                batch_data = []
                for i in range(31):
                    target_date = (today_dt.date() - pd.Timedelta(days=i)).strftime('%Y-%m-%d')
                    count = date_counts.get(target_date, 0)
                    batch_data.append((user['id'], target_date, count))
                
                cursor.executemany("""
                    INSERT INTO daily_commits (user_id, commit_date, count)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE count = VALUES(count)
                """, batch_data)
                updated_total += 1
                
            elif response.status_code == 401:
                # 401 에러 발생 시 헤더를 token 대신 Bearer로 한 번 더 시도해볼 수 있도록 로그 출력
                print(f"❌ {user['nickname']} 인증 실패 (401): 토큰 자체가 잘못되었거나 접두사 문제일 수 있습니다.")
                print(f"   현재 사용된 토큰 앞글자: {github_token[:7] if github_token else 'None'}...")
            else:
                print(f"❌ {user['nickname']} 실패 (코드: {response.status_code})")

        except Exception as e:
            print(f"Error ({user.get('nickname')}): {e}")
            continue
            
    conn.commit()
    cursor.close()
    return updated_total