import requests
from bs4 import BeautifulSoup
import csv
import time
import traceback

debug = False # Ture キャッシュで実行 "Test" URLを入力 False 本番実行

def scrape_baseball_score(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # エラーチェック
        soup = BeautifulSoup(response.text, 'html.parser')
        if response.status_code == 200:
            if debug != False:
                print("ページを取得しました")
        return soup

    except Exception as e:
        if debug != False:
            print(f"エラーが発生しました: {e}")
        return None

def scrape_player_data(soup):
    player_data = []

    # 選手情報を取得
    numbers = soup.find_all("td", class_ = "bb-playerTable__data bb-playerTable__data--number")
    names = soup.find_all("td", class_="bb-playerTable__data bb-playerTable__data--player")

    for number, name in zip(numbers, names):
        number = number.text.strip()
        name = name.text.strip()
        player_data.append([number, name])
    
    if debug != False:
        print(f"選手情報を取得しました: {len(player_data)}人")
        print(player_data[0])

    return player_data

def save_player_data(year,team,player_data):
    try:
        for player in player_data:
            with open("csv/1_3players.csv", "a", encoding="utf-8", newline="") as f:
                player.append(team)
                player.append(player[0])
                player.append(None)
                player.append(None)
                player[0] = f"{year}_{team}_{player[0]}"
                
                
                writer = csv.writer(f)
                writer.writerow(player)
            if debug != False:
                print(f"選手 {player[0]}(ID: {player[1]}を追加しました")
        return True
    except Exception as e:
        if debug != False:
            print(f"CSVへの書き込み中にエラーが発生しました: {e}")
            traceback.print_exc()
        return False
    

def main():

    if debug == True:
        print("モード：デバックモード")
        with open("html/player_data.html", "r") as f:
            html = f.read()
        soup = BeautifulSoup(html, 'html.parser')
        player_data = scrape_player_data(soup)
        save_player_data(2025,1,player_data)
    elif debug == "Test":
        print("モード：テストモード")
        year = 2025
        team = 1
        style = "p"
        url = f"https://baseball.yahoo.co.jp/npb/teams/{team}/memberlist?kind={style}"
        soup = scrape_baseball_score(url)
        player_data = scrape_player_data(soup)
        save_player_data(year,team,player_data)
    elif debug == False:
        print("モード：本番モード")
        try:
            for team in range(1, 13):
                for style in ["p", "b"]:
                    if team == 10:
                        team = 376
                    year = 2025
                    url = f"https://baseball.yahoo.co.jp/npb/teams/{team}/memberlist?kind={style}"
                    if team == 376:
                        team = 10
                    soup = scrape_baseball_score(url)
                    player_data = scrape_player_data(soup)
                    save_player_data(year,team,player_data)
                    print(f"チーム {team} ,野/投 {style}の選手情報を取得しました")
                    time.sleep(1)
        except Exception as e:
            if debug != False:
                print(f"エラーが発生しました: {e}")

        

if __name__ == "__main__":
    main()