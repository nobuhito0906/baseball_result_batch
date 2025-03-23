import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import schedule
import time
import os

def get_npb_results(date_str):
    """
    指定した日付のプロ野球試合結果をスクレイピング
    date_str: YYYY-MM-DD形式の日付文字列
    """
    url = f"https://baseball.yahoo.co.jp/npb/schedule/?date={date_str}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    print("URL:", url)
    # file = open('log.txt','w',encoding='utf-8')
    # file.write(str(soup))
    # file.close()
    # print(soup,file=codecs.open('log.txt','w','utf-8'))
    
    # 試合結果を格納するリスト
    results = []
    
    # テーブルのtbodyを取得
    tbodies = soup.select('tbody')
    if not tbodies:
        print("テーブル本体(tbody)が見つかりません")
        return results
    # file = open('tbody.txt','w',encoding='utf-8')
    # file.write(str(tbody))
    # file.close()
    # 結果を保存するリスト
    games_data = []

    # 各tbodyに対して処理を行う
    for tbody in tbodies:
        # 各行を処理
        current_date = None
        
        for tr in tbody.select('tr.bb-scheduleTable__row'):
            game_info = {}
            
            # 日付の取得
            date_element = tr.select_one('th.bb-scheduleTable__head')
            if date_element:
                current_date = date_element.text.strip()
                print("current_date:",current_date)
            # 日付が存在する場合、情報を追加
            if current_date:
                game_info['日付'] = current_date
            
            # ホームチームの取得
            home_team_element = tr.select_one('.bb-scheduleTable__homeName a')
            if home_team_element:
                game_info['ホーム球団'] = home_team_element.text.strip()
            else:
                game_info['ホーム球団'] = "試合なし"
            
            # アウェイチームの取得
            away_team_element = tr.select_one('.bb-scheduleTable__awayName a')
            if away_team_element:
                game_info['アウェイ球団'] = away_team_element.text.strip()
            
            # スコアの取得
            score_element = tr.select_one('.bb-scheduleTable__score')
            if score_element:
                # スコアを改行とスペースを除外して取得
                trimmed_score = score_element.text.strip().replace('\n', '').replace(' ', '')
                game_info['スコア'] = trimmed_score
                print("Score:",game_info['スコア'])
            # 勝ち投手の取得
            win_pitcher_element = tr.select_one('.bb-scheduleTable__player--win')
            if win_pitcher_element:
                game_info['勝ち投手'] = win_pitcher_element.text.strip()
            elif not win_pitcher_element and game_info['ホーム球団'] != "試合なし":
                game_info['勝ち投手'] = "引き分け"
            
            # 負け投手の取得
            lose_pitcher_element = tr.select_one('.bb-scheduleTable__player--lose')
            if lose_pitcher_element:
                game_info['負け投手'] = lose_pitcher_element.text.strip()
            
            # 球場の取得
            stadium_element = tr.select_one('.bb-scheduleTable__data--stadium')
            if stadium_element:
                game_info['試合球場'] = stadium_element.text.strip()
            
            
            games_data.append(game_info) #リストに追加
    
    return games_data


def get_game_details(detail_url):
    """
    試合詳細ページから勝ち投手、負け投手、球場情報を取得
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(detail_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 勝ち投手、負け投手の取得
        win_pitcher = "情報なし"
        lose_pitcher = "情報なし"
        
        pitcher_elems = soup.select('.bb-gameDetail__data--player')
        for elem in pitcher_elems:
            label = elem.select_one('.bb-gameDetail__data--label')
            if label and '勝利投手' in label.text:
                win_pitcher = elem.select_one('.bb-gameDetail__data--name').text.strip()
            elif label and '敗戦投手' in label.text:
                lose_pitcher = elem.select_one('.bb-gameDetail__data--name').text.strip()
        
        # 球場情報の取得
        stadium_elem = soup.select_one('.bb-gameDetail__data--stadium')
        stadium = stadium_elem.text.strip() if stadium_elem else "情報なし"
        
        return win_pitcher, lose_pitcher, stadium
    
    except Exception as e:
        print(f"詳細ページの取得でエラーが発生しました: {e}")
        return "情報なし", "情報なし", "情報なし"

def get_weekly_results_test(date_str):
    """
    過去1週間の試合結果を取得（テスト用関数）
    """
    basedate = datetime.date(2025, 3, 10)
    results = []
    
    date_str = basedate.strftime('%Y-%m-%d')
    daily_results = get_npb_results(date_str)
    results.extend(daily_results)
    return results

def get_weekly_results():
    """
    過去1週間の試合結果を取得
    """
    today = datetime.datetime.now()
    results = []
    
    # 過去7日間の結果を取得
    date_str = today.strftime('%Y-%m-%d')
    daily_results = get_npb_results(date_str)
    results.extend(daily_results)
    return results
    

def export_to_csv(results):
    """
    試合結果をCSVファイルに出力
    """
    try:
        # 出力ディレクトリがなければ作成
        output_dir = "npb_results"
        os.makedirs(output_dir, exist_ok=True)
        
        # 今日の日付をファイル名に含める
        today_str = datetime.datetime.now().strftime('%Y%m%d')
        csv_filename = f"{output_dir}/npb_results_{today_str}.csv"
        
        # DataFrameに変換してCSVに出力
        df = pd.DataFrame(results)
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')  # BOMありUTF-8でExcelでも文字化けしにくい
        
        print(f"CSVファイルに出力しました: {csv_filename}")
        return csv_filename
    
    except Exception as e:
        print(f"CSVファイルの出力でエラーが発生しました: {e}")
        return None

def weekly_job():
    """
    毎週日曜日の夜10時に実行されるジョブ
    """
    print(f"ジョブ開始: {datetime.datetime.now()}")
    results = get_weekly_results()
    
    if results:
        csv_file = export_to_csv(results)
        print(f"ジョブ完了: {datetime.datetime.now()}, 出力ファイル: {csv_file}")
    else:
        print(f"ジョブ完了: {datetime.datetime.now()}, 結果なし")

def main():
    # 毎週日曜日の夜10時にジョブを実行
    schedule.every().sunday.at("18:00").do(weekly_job)
    
    print("スケジューラを開始しました。毎週日曜日の夜10時に実行されます。")
    print("Ctrl+Cで終了できます。")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1分ごとにチェック
    except KeyboardInterrupt:
        print("スケジューラを終了します。")

# スクリプト単体実行時の処理
if __name__ == "__main__":
    # コマンドライン引数でテスト実行も可能にする
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("テスト実行を開始します...")
        results = get_weekly_results_test("dummy")
        csv_file = export_to_csv(results)
        print(f"テスト完了: 出力ファイル: {csv_file}")
    else:
        main()