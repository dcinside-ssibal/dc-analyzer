import requests
from bs4 import BeautifulSoup
import sqlite3
import time

def create_db():
    conn = sqlite3.connect('dcinside.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS galleries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            url TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gallery_id INTEGER,
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
    response = requests.get(gallery_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    posts = []
    for post in soup.select('.ub-content'):
        title = post.select_one('.gall_tit > a').text
        link = post.select_one('.gall_tit > a')['href']
        writer = post.select_one('.gall_writer').text.strip()
        date = post.select_one('.gall_date').text.strip()
        views = int(post.select_one('.gall_count').text.strip())
        comments = int(post.select_one('.gall_reply_num').text.strip().strip('[]'))
        recommendations = 0  # Assuming recommendations data is not available in this example
        
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

def main():
    create_db()
    galleries = [
        {"id": 1, "name": "Baseball", "url": "https://gall.dcinside.com/board/lists/?id=baseball"},
        {"id": 2, "name": "Soccer", "url": "https://gall.dcinside.com/board/lists/?id=soccer"}
        # Add more galleries as needed
    ]
    
    while True:
        for gallery in galleries:
            posts = get_posts(gallery["id"], gallery["url"])
            save_posts(posts)
        time.sleep(3600)  # 1시간마다 데이터 수집

if __name__ == '__main__':
    main()
