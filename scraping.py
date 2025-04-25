import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import traceback

debug = "Test"  # True: デバッグモード,"Test": テストモード, False: 本番モード

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
    return team_data,ground_data,players_data

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

def add_player_id(player_data, player_id, name, team_id, uniform_number, batting_side, pitching_side):
    # 重複チェック
    # 新しい選手データを作成
    try:
        new_player = [player_id, name, team_id, uniform_number, batting_side, pitching_side]

        for player in player_data:
            if player[0] == player_id:
                if debug != False:
                    print(f"選手ID {player_id} が重複しています")
                for i in range(len(player)):
                    if player[i] == None:
                        player[i] = new_player[i]
                        return False
                return False
        
        # メモリ上のデータに追加
        player_data.append(new_player)
    except Exception as e:
        if debug != False:
            print(f"選手データの追加中にエラーが発生しました: {e}")
        return False
    
    # CSVファイルに追加（追記モード）
    try:
        with open("csv/1-3:players.csv", "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            # 既存のファイルに追記するだけなのでヘッダーは書き込まない
            writer.writerow(new_player)
        if debug != False:
            print(f"選手 {name}(ID: {player_id}) を追加しました")
        return True
    
    except Exception as e:
        if debug != False:
            print(f"CSVへの書き込み中にエラーが発生しました: {e}")
        # エラーが発生した場合はメモリ上のデータから削除して整合性を保つ
        player_data.pop()
        return False


def format_bb_gameRound(soup):
    try:
        #matchs5
        bb_gameRound = soup.find('div', class_='bb-gameRound')
        series_game_number = bb_gameRound.find_all('li')[0].text.replace("回戦","")

        
        if debug != False:
            print("試合数 :",series_game_number)

        #matchs1
        date = bb_gameRound.find_all('li')[1].text.split("/")
        if len(date[0]) == 1:
            date[0] = "0"+date[0]
        date[1] = date[1].split("（")[0]
        if len(date[1]) == 1:
            date[1] = "0"+date[1]

        date = f"2025_{date[0]}_{date[1]}"

        if debug != False:
            print("日付 :",date)

        return [series_game_number,date]
    except Exception as e:
        if debug != False:
            print("エラー発生:format_bb_gameRound")
            print(f"試合情報の取得に失敗しました: {e}")
        return None
    

def format_bb_liveBg_bb_liveBg_npb(soup,team_data,ground_data,players_data):
    """at_bats3,4,7,10,11,12 , pitches2,3,11,14,15,16をカバーする"""
    try:
        top_team = soup.find_all('a' ,class_="bb-gameScoreTable__team")[0].text
        bottom_team = soup.find_all('a' ,class_="bb-gameScoreTable__team")[1].text
        team_num = [0,0]
        for i in range(len(team_data)):
            if team_data[i]['team_name'] == top_team:
                team_num[0] = team_data[i]['team_id'] 
            elif team_data[i]['team_name'] == bottom_team:
                team_num[1] = team_data[i]['team_id']
                
        if debug != False:
            print("[表チーム,裏チーム] :",team_num)

        # matchs2,3
        team_id = [team_num[0],team_num[1]]
        if int(team_num[0]) > int(team_num[1]):
            team_id = [team_num[1],team_num[0]]

        if debug != False:
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

        if debug != False:
            print("イニング,表/裏 :",inning,",",top_bottom)


        # at_bats5,6
        on_time_score = sbo.find_all("td")
        on_time_score = [on_time_score[i].text for i in range(len(on_time_score)) if i % 2 == 1]
        if int(team_num[0]) > int(team_num[1]):
            on_time_score = [on_time_score[1],on_time_score[0]]

        if debug != False:
            print("その時の得点 :",on_time_score)
        
        # pitches11
        o = sbo.find('p', class_='o').find('b').text
        oc = len(o)

        if debug != False:
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

        if debug != False:
            print("塁情報 :",base1,base2,base3)

        # at_bats3,4
        pitcherR = score_board.find("div",id = "pitcherR")
        pitchernum = pitcherR.find("span",class_= "playerNo")
        if len(pitchernum.text) == 1:
            pitchernum = "0"+pitchernum.text
        pitchernum = f"2025_{int(team_num[1-top_bottom])}_{(pitchernum.text.replace('#',''))}"
        nm = pitcherR.find("td",class_= "nm")
        pitchername = nm.find('a').text
        p_side = pitcherR.find('td',class_ = 'dominantHand').text.replace("投","")
        if p_side == "左":
            p_side = "0"
        elif p_side == "右":
            p_side = "1"

        if debug != False:
            print("ピッチャー番号 :",pitchernum)
            print("ピッチャー名前 :",pitchername)
            print("ピッチャー投球側 :",p_side)
        add_player_id(players_data, pitchernum, pitchername, team_num[1-top_bottom], pitchernum.split("_")[2], None, p_side)


        batter = score_board.find("div",id = "batter")
        batternum = batter.find("span",class_= "playerNo").text.replace("#","")
        if len(batternum) == 1:
            batternum = "0"+batternum
        batternum = f"2025_{team_num[top_bottom]}_{batternum}"

        nm = batter.find("td",class_= "nm")
        battername = nm.find('a').text
        b_side = batter.find('td',class_ = 'dominantHand').text.replace("打","")
        if b_side == "左":
            b_side = "0"
        elif b_side == "右":
            b_side = "1"
        if debug != False:
            print("バッター打球側 :",b_side)
            print("バッター名前 :",battername)
            print("バッター番号 :",batternum)
        add_player_id(players_data, batternum, battername, team_num[top_bottom], batternum.split("_")[2], b_side, None)

        # at_bats7
        live_footer = score_board.find("div",id = "liveFooter").find("dt")
        butter_number = live_footer.text.replace("打者","")

        if debug != False:
            print("その回の何番目の打者か :", butter_number)

        # matchs4
        stadium = soup.find('ul' ,class_='stadium').find_all('li')[1].text
        for i in range(len(ground_data)):
            if ground_data[i]['ground_name'] == stadium:
                stadium_id = ground_data[i]['ground_id']
                break
        if debug != False:
            print("球場 :",stadium_id)

        return [team_num,team_id,inning,top_bottom,on_time_score,oc,base1,base2,base3,pitchernum,batternum,butter_number,stadium_id]
 
    except Exception as e:
        if debug != False:
            print("エラー発生:format_bb_liveBg_bb_liveBg_npb")
            print(f"スコアボードの取得に失敗しました: {e}")
        traceback.print_exc()
        return None
    

def 未完format_bb_splitsTable_data(soup):
    try:
        bb_splitsTable_data = soup.find_all('section', id='gm_memh', class_ = 'bb-splits__item target_modules')[0].find_all('table')[1].find_all('tbody')[0].find_all('tr')[1].find_all('td')[0].find_all('a')
        # print(bb_splitsTable_data)
        # print(len(bb_splitsTable_data))

        if debug != False:
            print("データを抽出しました:bb_splitsTable_data")
    except Exception as e:
        if debug != False:
            print("エラー発生:format_bb_splitsTable_data")
            print(f"データの抽出に失敗しました: {e}")
        return None
    
def format_dd_splits_table(soup):
    """pitches4~10をカバーする"""
    try:

        # 基本要素の取得
        bb_modCommon01 = soup.find_all('div', class_='bb-modCommon01')[3]
        print(bb_modCommon01)
        bb_splits_item = bb_modCommon01.find_all('section', class_='bb-splits__item')[1]
        tbody = bb_splits_item.find_all('tbody')
        
        # 投球数の取得
        bb_icon_number = tbody[0].find_all('span', class_='bb-icon__number')  # この対戦の打者への投球数
        pitch_count = len(bb_icon_number)
        
        # 投球データを格納するリスト
        returnlist = [[] for _ in range(pitch_count)]
        
        # 投球内容を取得
        items = tbody[2].find_all('td')
        bs_list = [[], []]  # ボール数、ストライク数を記録
        ballC = 0
        strikeC = 0
        
        # 各セルのデータを5つずつのグループとして処理
        for i in range(len(items)):
            pitch_index = i // 5  # 投球のインデックス
            column_index = i % 5  # カラムのインデックス
            
            # 配列の範囲チェック
            if pitch_index >= len(returnlist):
                # 必要に応じて配列を拡張
                returnlist.append([])
            
            # 各カラムのデータをクリーンアップ
            if column_index == 0:  # 1カラム目: カウント
                value = items[i].text.replace("\n", "").strip()
            elif column_index == 4:  # 5カラム目: 結果
                raw_text = items[i].text.strip()
                value = raw_text.split()[0] if raw_text and raw_text.split() else ""
                
                # ボール・ストライクカウントの更新
                if value == "見逃し" or value == "空振り" or value == "ファウル":
                    if not (value == "ファウル" and strikeC == 2):
                        strikeC += 1
                elif value == "ボール":
                    ballC += 1
                    
                # カウントを記録
                if pitch_index < len(returnlist):
                    bs_list[0].append(ballC)
                    bs_list[1].append(strikeC)
            elif column_index == 3:  # 4カラム目: 球速
                value = items[i].text.replace("km/h", "").strip()
            else:  # その他のカラム
                value = items[i].text.strip()
            
            # データをリストに追加
            returnlist[pitch_index].append(value)
        
        if debug != False:
            print("データを抽出しました:dd_splits_table")
            print(returnlist)
        return returnlist, bs_list
    except Exception as e:
        if debug != False:
            print("エラー発生:format_dd_splits_table")
            print(f"データの抽出に失敗しました: {e}")
        traceback.print_exc()
        return None
    
def format_bb_split_table(soup):
    """pitches12,13をカバーする"""
    try:
        bb_splits_item = soup.find_all('section', class_='bb-splits__item')[1]
        bb_splitsTable = bb_splits_item.find_all('table' , class_='bb-splitsTable')[0]
        tbody = bb_splitsTable.find_all('tbody')

        ball_elements = soup.select('.bb-icon__ballCircle')
        half_elements = ball_elements[len(ball_elements)//2:]
        balls_data = []

        for ball in half_elements:
            style = ball.get('style')


            if style:
                top = int(style.split('top:')[1].split('px')[0])
                left = int(style.split('left:')[1].split('px')[0])
                if debug != False:
                    print(f"ボールの座標: {top} : {left}")
                balls_data.append([top, left])
                pass
        if debug != False:
            print(balls_data)

        if debug != False:
            print("データを抽出しました:bb_split_table")
        return balls_data

    except Exception as e:
        if debug != False:
            print("エラー発生:format_bb_split_table")
            print(f"データの抽出に失敗しました: {e}")
        return None


def create_match_pitch_id(pitches_list,at_bats_list,match_list):
    try:
        match_list[0] = f"{match_list[1]}_{match_list[2]}_{match_list[3]}"
        at_bats_list[0] = match_list[0]
        for i in range(len(pitches_list)):
            pitches_list[i][0] = match_list[0]
            pitches_list[i][1] = f"{match_list[0]}_{at_bats_list[1]}_{at_bats_list[2]}_{at_bats_list[7]}_{pitches_list[i][8]}"
    except Exception as e:
        if debug != False:
            print("エラー発生:create_match_pitch_id")
            print(f"試合IDの作成に失敗しました: {e}")
        return None
    
        

def data_format(soup,team_data,ground_data,players_data):
    try:
        bb_gameRound = format_bb_gameRound(soup)
        bb_liveBg_bb_liveBg_npb = format_bb_liveBg_bb_liveBg_npb(soup,team_data,ground_data,players_data)
        dd_splits_table,bs_count = format_dd_splits_table(soup)
        bb_split_table = format_bb_split_table(soup)
        # bb_splitsTable_data = 未完format_bb_splitsTable_data(soup)
        match_list = [0 for _ in range(6)]
        # inning_score_list = [[0 for _ in range(4)]]
        at_bats_list = [0 for _ in range(13)]
        pitches_list = [[0 for _ in range(14)] for _ in range(len(dd_splits_table))]
        try:
            # pitches
            for i in range(len(dd_splits_table)):
                pitches_list[i][2] = bb_liveBg_bb_liveBg_npb[2]
                pitches_list[i][3] = bb_liveBg_bb_liveBg_npb[3]
                pitches_list[i][4] = dd_splits_table[i][2]
                pitches_list[i][5] = dd_splits_table[i][3]
                pitches_list[i][6] = dd_splits_table[i][4]
                pitches_list[i][7] = dd_splits_table[i][1]
                pitches_list[i][8] = dd_splits_table[i][0] 
                pitches_list[i][9] = bs_count[0][i]
                pitches_list[i][10] = bs_count[1][i]
                pitches_list[i][11] = bb_liveBg_bb_liveBg_npb[5]
                pitches_list[i][12] = bb_split_table[i][0]
                pitches_list[i][13] = bb_split_table[i][1]

            # at_bats
            at_bats_list[1] = bb_liveBg_bb_liveBg_npb[2]
            at_bats_list[2] = bb_liveBg_bb_liveBg_npb[3]
            at_bats_list[3] = bb_liveBg_bb_liveBg_npb[10]
            at_bats_list[4] = bb_liveBg_bb_liveBg_npb[9]
            at_bats_list[5] = bb_liveBg_bb_liveBg_npb[4][0]
            at_bats_list[6] = bb_liveBg_bb_liveBg_npb[4][1]
            at_bats_list[7] = bb_liveBg_bb_liveBg_npb[11]
            at_bats_list[8] = None
            at_bats_list[9] = None
            at_bats_list[10] = bb_liveBg_bb_liveBg_npb[6]
            at_bats_list[11] = bb_liveBg_bb_liveBg_npb[7]
            at_bats_list[12] = bb_liveBg_bb_liveBg_npb[8]
            
            # matchs
            match_list[1] = bb_gameRound[1]
            match_list[2] = bb_liveBg_bb_liveBg_npb[1][0]
            match_list[3] = bb_liveBg_bb_liveBg_npb[1][1]
            match_list[4] = bb_liveBg_bb_liveBg_npb[12]
            match_list[5] = bb_gameRound[0]

            create_match_pitch_id(pitches_list,at_bats_list,match_list)
            
            

            if debug != False:
                print(pitches_list)
                print(at_bats_list)
                print(match_list)
                print("データを整形しました")
            return [pitches_list,at_bats_list,match_list]

        except Exception as e:
            if debug != False:
                print("エラー発生:data_format")
                print(f"データの整形に失敗しました: {e}")
            return None
    except Exception as e:
        if debug != False:
            print("エラー発生:data_format")
            print(f"データの整形に失敗しました: {e}")
        return None

def write_csv_file(data,memory_matchs):
    try:
        if debug != False:
            print("ok")
        if memory_matchs == []:
            with open('csv/2-1:matches.csv', 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(data[2])
                    memory_matchs.append(data[2][0])
                    if debug != False:
                        print("新しい試合IDを追加しました")
        else:
            for i in range(len(memory_matchs)):
                if memory_matchs[i] == data[2][0]:
                    if debug != False:
                        print("同じ試合IDが見つかりました")
                else:
                    with open('csv/2-1:matches.csv', 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(data[2])
                        memory_matchs.append(data[2][0])
        with open('csv/2-3:at_bats.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(data[1])
        with open('csv/2-4:pitches.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(data[0])
        if debug != False:
            print("CSVファイルに書き込みました")
    except Exception as e:
        if debug != False:
            print("エラー発生:write_csv_file")
            print(f"CSVファイルへの書き込みに失敗しました: {e}")


def main():

    team_data,ground_data,players_data = read_csv_file()
    memory_matchs = []
    print(f"デバッグモード： {debug}")
    if debug == True:
        with open("html/cache.html", "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        rlist = data_format(soup,team_data,ground_data,players_data)

        write_csv_file(rlist,memory_matchs)

    elif debug == "Test":
        url = "https://baseball.yahoo.co.jp/npb/game/2021029038/score?index=0110100"
        url = "https://baseball.yahoo.co.jp/npb/game/2021029136/score?index=0910400"
        url = "https://baseball.yahoo.co.jp/npb/game/2021029040/score?index=0110100"
        soup = scrape_baseball_score(url)
        rlist = data_format(soup,team_data,ground_data,players_data)

        write_csv_file(rlist,memory_matchs)

        if rlist is not None:
            print(rlist)

    elif debug == False:
        print("本番モードです")
        for i in range(38,170):
            if i < 100:
                i = "0"+str(i)
            for j in range(1,13):
                if j < 10:
                    j = "0"+str(j)
                for k in range(1,3):
                    for l in range(1,20):
                        time.sleep(1)
                        if l < 10:
                            l = "0"+str(l)
                        url = f"https://baseball.yahoo.co.jp/npb/game/2021029{i}/score?index={j}{k}{l}00"
                        soup = scrape_baseball_score(url)
                        if soup is None:
                            print("NG! for ;",url)
                            with open("logs.txt", "a", encoding="utf-8") as f:
                                f.write(f"----------NG !{url}\n")
                            break
                        else:
                            rlist = data_format(soup,team_data,ground_data,players_data)
                            write_csv_file(rlist,memory_matchs)
                            print("OK !",url)
                            with open("logs.txt", "a", encoding="utf-8") as f:
                                f.write(f"OK !{url}\n")

if __name__ == "__main__":
    main()