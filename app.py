from flask import Flask, render_template
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

app = Flask(__name__)

def load_data():
    conn = sqlite3.connect('dcinside.db')
    df_posts = pd.read_sql_query('SELECT * FROM posts', conn)
    df_galleries = pd.read_sql_query('SELECT * FROM galleries', conn)
    conn.close()
    return df_posts, df_galleries

@app.route('/')
def index():
    df_posts, df_galleries = load_data()
    gallery_scores = calculate_scores(df_posts)
    
    return render_template('index.html', gallery_scores=gallery_scores.to_dict(orient='records'))

@app.route('/<int:gallery_id>')
def galaxy(gallery_id):
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
    
    return render_template('galaxy.html', gallery_name=gallery_name, trend_url=trend_url)

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

if __name__ == '__main__':
    app.run(debug=True)
