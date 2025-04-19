import requests
from bs4 import BeautifulSoup

def scrape_baseball_score(url):
    print(url)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # ページの取得
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # エラーチェック
        
        # BeautifulSoupオブジェクトの作成
        soup = BeautifulSoup(response.text, 'html.parser')
        if response.status_code == 200:
            print("ページを取得しました")

        return soup

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return None
    


def data_format(soup):
    try:
        gyou = soup.find_all('div', class_='bb-modCommon01')[3]

        block = gyou.find_all('section', class_='bb-splits__item')[1]

        table = block.find_all('tbody')
        tkysu = table[0].find_all('span' , class_='bb-icon__number') # この対戦の打者への投球数
        returnlist = [[] for _ in range(len(tkysu))]

        with open("html/otameshi_ikkyu2.html", "w", encoding="utf-8") as f:
            f.write(table[2].prettify())

        items = table[2].find_all('td')

        for i in range(len(items)):
            if i % 5 == 0:
                items[i] = items[i].text.split("\n")[1]
            elif i % 5 == 4:
                items[i] = items[i].text.split()[0]
            else:
                items[i] = items[i].text
            j = i // 5
            returnlist[j].append(items[i])


        print("データを整形しました")
        print(returnlist)

    except Exception as e:
        print(f"データの整形に失敗しました: {e}")
        return None


        
        
        

        
















def main():
    # 使用例
    url = "https://baseball.yahoo.co.jp/npb/game/2021029136/score?index=0910400"
    result = scrape_baseball_score(url)
    list = data_format(result)

    if result is not None:
        print("Ture")

if __name__ == "__main__":
    main()