import pandas as pd

# CSVデータを読み込む
df = pd.read_csv('csv/1-3:players.csv')

# 重複する前の行数を記録
original_count = len(df)

# player_idの重複を確認し、最初の出現以外を削除
df_no_duplicates = df.drop_duplicates(subset=['player_id'], keep='first')

# 重複削除後の行数を記録
new_count = len(df_no_duplicates)

# 何行削除されたかを表示
removed_count = original_count - new_count
print(f"重複により削除された行数: {removed_count}")

# 結果を新しいCSVファイルに保存
df_no_duplicates.to_csv('players_no_duplicates.csv', index=False)
print("重複を削除したデータをplayers_no_duplicates.csvに保存しました")

# 削除された行があれば表示
if removed_count > 0:
    # 削除された行のplayer_idを特定
    duplicate_ids = df[df.duplicated('player_id')]['player_id'].unique()
    print(f"削除された行のplayer_id: {', '.join(duplicate_ids)}")
else:
    print("重複するplayer_idはありませんでした")