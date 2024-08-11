from flask import Flask, render_template
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
import threading
import time
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def create_db():
    conn = sqlite3.connect('dcinside.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS galleries (
            id TEXT PRIMARY KEY,
            name TEXT,
            url TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gallery_id TEXT,
            title TEXT,
            link TEXT,
            writer TEXT,
            date TEXT,
            views INTEGER,
            comments INTEGER,
            recommendations INTEGER,
            FOREIGN KEY(gallery_id) REFERENCES galleries(id)
        )
    ''')
    conn.commit()
    conn.close()

def get_posts(gallery_id, gallery_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(gallery_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    posts = []
    for post in soup.select('.ub-content'):
        # 게시물이 설문 또는 공지가 아닌 경우만 처리
        if '설문' in post.select_one('.gall_num').text or '공지' in post.select_one('.gall_num').text:
            continue
        
        title_tag = post.select_one('.gall_tit > a')
        if not title_tag:
            continue
        title = title_tag.text.strip()
        link = "https://gall.dcinside.com" + title_tag['href']
        writer_tag = post.select_one('.gall_writer')
        writer = writer_tag.text.strip() if writer_tag else 'Unknown'
        date_tag = post.select_one('.gall_date')
        date = date_tag.text.strip() if date_tag else 'Unknown'
        views_tag = post.select_one('.gall_count')
        views = int(views_tag.text.strip()) if views_tag else 0
        comments_tag = post.select_one('.reply_numbox')
        if comments_tag:
            comments_text = comments_tag.text.strip().strip('[]')
            comments = int(comments_text.split('/')[0])  # 첫 번째 숫자만 사용
        else:
            comments = 0
        recommendations_tag = post.select_one('.gall_recommend')
        recommendations = int(recommendations_tag.text.strip()) if recommendations_tag else 0
        
        posts.append((gallery_id, title, link, writer, date, views, comments, recommendations))
    
    return posts

def save_posts(posts):
    conn = sqlite3.connect('dcinside.db')
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT INTO posts (gallery_id, title, link, writer, date, views, comments, recommendations)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', posts)
    conn.commit()
    conn.close()

def data_collector():
    create_db()
    galleries = [
        {"id": "comic_new4", "name": "Comic", "url": "https://gall.dcinside.com/board/lists?id=comic_new4"},
        {"id": "baseball_new11", "name": "Baseball", "url": "https://gall.dcinside.com/board/lists?id=baseball_new11"}
        # Add more galleries as needed
    ]
    
    while True:
        for gallery in galleries:
            posts = get_posts(gallery["id"], gallery["url"])
            save_posts(posts)
        time.sleep(3600)  # 1시간마다 데이터 수집

def load_data():
    conn = sqlite3.connect('dcinside.db')
    df_posts = pd.read_sql_query('SELECT * FROM posts', conn)
    df_galleries = pd.read_sql_query('SELECT * FROM galleries', conn)
    conn.close()
    return df_posts, df_galleries

def calculate_scores(df_posts):
    gallery_scores = df_posts.groupby('gallery_id').agg({
        'title': 'count',
        'comments': 'sum',
        'views': 'sum',
        'recommendations': 'sum'
    }).rename(columns={
        'title': 'post_count',
        'comments': 'comment_count',
        'views': 'view_count',
        'recommendations': 'recommendation_count'
    })
    
    # Normalize scores
    for col in ['post_count', 'comment_count', 'view_count', 'recommendation_count']:
        gallery_scores[col] = 100 * (gallery_scores[col] - gallery_scores[col].min()) / (gallery_scores[col].max() - gallery_scores[col].min())
    
    gallery_scores['total_score'] = gallery_scores.sum(axis=1)
    gallery_scores = gallery_scores.sort_values('total_score', ascending=False)
    
    return gallery_scores

@app.route('/')
def index():
    df_posts, df_galleries = load_data()
    gallery_scores = calculate_scores(df_posts)
    
    return render_template('index.html', gallery_scores=gallery_scores.reset_index().to_dict(orient='records'))

@app.route('/<gallery_id>')
def gallery(gallery_id):
    df_posts, df_galleries = load_data()
    gallery_name = df_galleries[df_galleries['id'] == gallery_id]['name'].values[0]
    gallery_posts = df_posts[df_posts['gallery_id'] == gallery_id]
    
    # 시각화
    img = BytesIO()
    plt.figure(figsize=(10, 5))
    sns.countplot(data=gallery_posts, x='date')
    plt.title(f'{gallery_name} Gallery Daily Post Count')
    plt.xlabel('Date')
    plt.ylabel('Number of Posts')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(img, format='PNG')
    img.seek(0)
    trend_url = base64.b64encode(img.getvalue()).decode('utf8')
    
    return render_template('gallery.html', gallery_name=gallery_name, trend_url=trend_url)

if __name__ == '__main__':
    # 데이터 수집 스레드 시작
    collector_thread = threading.Thread(target=data_collector)
    collector_thread.start()
    
    # Flask 웹 서버 실행
    app.run(host='0.0.0.0', port=80, debug=True)
