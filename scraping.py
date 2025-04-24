import requests
from bs4 import BeautifulSoup
import json
import csv


debug = True # True: デバッグモード,"Test": テストモード, False: 本番モード

def read_csv_file():
    with open("csv/1-1:team.json", "r", encoding="utf-8") as f:
        team_data = json.load(f)
    with open("csv/1-2:ground.json", "r", encoding="utf-8") as f:
        ground_data = json.load(f)
    players_data = []
    with open("csv/1-3:players.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        _header = next(reader)  # ヘッダーをスキップ
        for row in reader:
            players_data.append(row)
    print(players_data)
    return team_data,ground_data,players_data

def scrape_baseball_score(url):
    print(url)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # エラーチェック
        soup = BeautifulSoup(response.text, 'html.parser')
        if response.status_code == 200:
            print("ページを取得しました")
        return soup

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return None

def add_player_id(player_data, player_id, name, team_id, uniform_number, batting_side, pitching_side):
    # 重複チェック
    for player in player_data:
        if player[0] == player_id:
            print(f"選手ID {player_id} が重複しています")
            return False
    
    # 新しい選手データを作成
    new_player = [player_id, name, team_id, uniform_number, batting_side, pitching_side]
    
    # メモリ上のデータに追加
    player_data.append(new_player)
    
    # CSVファイルに追加（追記モード）
    try:
        with open("csv/1-3:players.csv", "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            # 既存のファイルに追記するだけなのでヘッダーは書き込まない
            writer.writerow(new_player)
        print(f"選手 {name}(ID: {player_id}) を追加しました")
        return True
    
    except Exception as e:
        print(f"CSVへの書き込み中にエラーが発生しました: {e}")
        # エラーが発生した場合はメモリ上のデータから削除して整合性を保つ
        player_data.pop()
        return False


def format_bb_liveBg_bb_liveBg_npb(soup,team_data,ground_data):
    """at_bats3,4,7,10,11,12 , pitches2,3,11,14,15,16をカバーする"""
    try:
        top_team = soup.find_all('a' ,href="/npb/teams/3/top" ,class_="bb-gameScoreTable__team")[0].text
        bottom_team = soup.find_all('a' ,href="/npb/teams/1/top" ,class_="bb-gameScoreTable__team")[0].text
        team_num = [0,0]
        for i in range(len(team_data)):
            if team_data[i]['team_name'] == top_team:
                team_num[0] = team_data[i]['team_id'] 
            elif team_data[i]['team_name'] == bottom_team:
                team_num[1] = team_data[i]['team_id']
                
        print("[表チーム,裏チーム] :",team_num)

        # matchs2,3
        team_id = [team_num[0],team_num[1]]
        if team_num[0] > team_num[1]:
            team_id = [team_num[1],team_num[0]]

        print("[team1_id,team2_id] :",team_id)

        # pitches(at_bats)2,3
        score_board = soup.find('div', class_='bb-liveBg bb-liveBg--npb')
        live_header = score_board.find('div', id='liveHeader')
        sbo = live_header.find('div', id='sbo')
        live = sbo.find('h4',class_="live")
        inning = live.find('em').text[0]
        top_bottom = live.find('em').text[2]
        if top_bottom == "表":
            top_bottom = 0
        elif top_bottom == "裏":
            top_bottom = 1

        print("イニング,表/裏 :",inning,",",top_bottom)


        # at_bats5,6
        on_time_score = sbo.find_all("td")
        on_time_score = [on_time_score[i].text for i in range(len(on_time_score)) if i % 2 == 1]
        if team_num[0] > team_num[1]:
            on_time_score = [on_time_score[1],on_time_score[0]]

        print("その時の得点 :",on_time_score)
        
        # pitches11
        o = sbo.find('p', class_='o').find('b').text
        oc = len(o)

        print("アウトカウント :",oc)

        # at_bats10,11,12
        try:
            base1 = score_board.find('div', id='base1').find('span').text[0]
            if len(base1) == 1:
                base1 = "0"+base1
            base1 = f"2025_{team_num[top_bottom]}_{base1}"
        except:
            base1 = 0
        try:
            base2 = score_board.find('div', id='base2').find('span').text[0]
            if len(base2) == 1:
                base2 = "0"+base2
            base2 = f"2025_{team_num[top_bottom]}_{base2}"
        except:
            base2 = 0
        try:
            base3 = score_board.find('div', id='base3').find('span').text[0]
            if len(base3) == 1:
                base3 = "0"+base3
            base3 = f"2025_{team_num[top_bottom]}_{base3}"
        except:
            base3 = 0

        print("塁情報 :",base1,base2,base3)

        # at_bats3,4
        pitcherR = score_board.find("div",id = "pitcherR")
        pitchernum = pitcherR.find("span",class_= "playerNo")
        if len(pitchernum.text) == 1:
            pitchernum = "0"+pitchernum.text
        pitchernum = f"2025_{team_num[1-top_bottom]}_{pitchernum.text.replace('#','')}"
        nm = pitcherR.find("td",class_= "nm")
        pitchername = nm.find('a').text
        p_side = pitcherR.find('td',class_ = 'dominantHand').text.replace("投","")
        if p_side == "左":
            p_side = "0"
        elif p_side == "右":
            p_side = "1"

        print("ピッチャー番号 :",pitchernum)
        print("ピッチャー名前 :",pitchername)
        print("ピッチャー投球側 :",p_side)


        batternum = score_board.find("div",id = "batter").find("span",class_= "playerNo")
        if len(batternum.text) == 1:
            batternum = "0"+batternum.text
        batternum = f"2025_{team_num[top_bottom]}_{batternum.text.replace('#','')}"

        print("バッター番号 :",batternum)

        # at_bats7
        live_footer = score_board.find("div",id = "liveFooter").find("dt")
        butter_number = live_footer.text.replace("打者","")

        print("その回の何番目の打者か :", butter_number)

        # matchs4
        stadium = soup.find('ul' ,class_='stadium').find_all('li')[1].text
        for i in range(len(ground_data)):
            if ground_data[i]['ground_name'] == stadium:
                stadium_id = ground_data[i]['ground_id']
                break
        print("球場 :",stadium_id)

        return [team_num,team_id,inning,top_bottom,on_time_score,oc,base1,base2,base3,pitchernum,batternum,butter_number,stadium_id]
 
    except Exception as e:
        print("エラー発生:format_bb_liveBg_bb_liveBg_npb")
        print(f"スコアボードの取得に失敗しました: {e}")
        return None
    
    
def format_dd_splits_table(soup):
    """pitches4~10をカバーする"""
    try:
        gyou = soup.find_all('div', class_='bb-modCommon01')[3]
        block = gyou.find_all('section', class_='bb-splits__item')[1]
        table = block.find_all('tbody')
        tkysu = table[0].find_all('span' , class_='bb-icon__number') # この対戦の打者への投球数
        returnlist = [[] for _ in range(len(tkysu))]
        items = table[2].find_all('td')
        bs_list = [[],[]]
        ballC = 0
        strikeC = 0
        for i in range(len(items)):
            if i % len(returnlist) == 0:
                items[i] = items[i].text.split("\n")[1]
            elif i % len(returnlist) == 4:
                items[i] = items[i].text.split()[0]
                bs_list[0].append(ballC)
                bs_list[1].append(strikeC)
                if items[i] == "見逃し" or items[i] == "空振り" or items[i] == "ファウル":
                    if not (items[i] == "ファウル" and strikeC == 2):
                        strikeC += 1
                elif items[i] == "ボール":
                    ballC += 1
            elif i % len(returnlist) == 3:
                items[i] = items[i].text.replace("km/h", "")
            else:
                items[i] = items[i].text
            j = i // len(returnlist)
            returnlist[j].append(items[i])
        print("データを抽出しました:dd_splits_table")
        return returnlist,bs_list
    except Exception as e:
        print("エラー発生:format_dd_splits_table")
        print(f"データの抽出に失敗しました: {e}")
        return None
    

def create_match_id():
    pass

def create_pitch_id():
    pass
        

def data_format(soup,team_data,ground_data,players_data):
    bb_liveBg_bb_liveBg_npb = format_bb_liveBg_bb_liveBg_npb(soup,team_data,ground_data)
    dd_splits_table,bs_count = format_dd_splits_table(soup)
    match_list = [0 for _ in range(6)]
    inning_score_list = [[0 for _ in range(4)]]
    at_bats_list = [0 for _ in range(13)]
    pitches_list = [[0 for _ in range(14)] for _ in range(len(dd_splits_table))]
    try:
        # pitches
        for i in range(len(dd_splits_table)):

            pitches_list[i][4] = dd_splits_table[i][2]
            pitches_list[i][5] = dd_splits_table[i][3]
            pitches_list[i][6] = dd_splits_table[i][4]
            pitches_list[i][7] = dd_splits_table[i][1]
            pitches_list[i][8] = dd_splits_table[i][0] 
            pitches_list[i][9] = bs_count[0][i]
            pitches_list[i][10] = bs_count[1][i]
    
        
        print(pitches_list)
        print("データを整形しました")
        return 

    except Exception as e:
        print("エラー発生:data_format")
        print(f"データの整形に失敗しました: {e}")
        return None



def main():
    team_data,ground_data,players_data = read_csv_file()
    print(f"デバッグモード： {debug}")
    if debug == True:
        with open("html/cache.html", "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        rlist = data_format(soup,team_data,ground_data,players_data)

        if rlist is not None:
            print(rlist)

    elif debug == "Test":
        url = "https://baseball.yahoo.co.jp/npb/game/2021029136/score?index=0910400"
        soup = scrape_baseball_score(url)
        rlist = data_format(soup)

        if rlist is not None:
            print(rlist)

    elif debug == False:
        print("本番モードです")

if __name__ == "__main__":
    main()