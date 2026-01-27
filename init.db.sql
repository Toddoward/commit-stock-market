-- 1. 데이터베이스 생성
CREATE DATABASE commit_stock_db;
USE commit_stock_db;

-- 2. 종목(유저) 테이블 생성
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nickname VARCHAR(50) NOT NULL UNIQUE, -- 종목명
    repo_url VARCHAR(255) NOT NULL,       -- 백준 허브 레포 주소
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 커밋(주가) 이력 테이블 생성
CREATE TABLE daily_commits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    commit_date DATE NOT NULL,
    count INT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY user_date_unique (user_id, commit_date) -- 중복 방지 핵심 설정
);