import sqlite3
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import seaborn as sns

def load_data():
    conn = sqlite3.connect('dcinside.db')
    df = pd.read_sql_query('SELECT * FROM posts', conn)
    conn.close()
    return df

def analyze_keywords(df):
    text = ' '.join(df['title'].tolist())
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.show()

def analyze_trends(df):
    df['date'] = pd.to_datetime(df['date'])
    daily_posts = df.resample('D', on='date').size()
    
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=daily_posts)
    plt.title('Daily Post Count')
    plt.xlabel('Date')
    plt.ylabel('Number of Posts')
    plt.show()

def main():
    df = load_data()
    analyze_keywords(df)
    analyze_trends(df)

if __name__ == '__main__':
    main()
