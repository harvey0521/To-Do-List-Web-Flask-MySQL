from flask  import Flask, jsonify, request, render_template, Response
from dotenv import load_dotenv
import os
import mysql.connector
from urllib.parse import urlparse
import json

app = Flask(__name__)

#載入 .env 檔案中的環境變數
load_dotenv()

def get_db():
    mysql_url = os.getenv("DB_URL")

    if mysql_url:
        print("👉 使用雲端資料庫")
        # 如果 DB_URL 存在，則解析 DB_URL 並連接雲端資料庫
        parsed_url = urlparse(mysql_url)
        return mysql.connector.connect(
            host = parsed_url.hostname,  # 主機名稱（雲端提供的資料庫地址）
            port = parsed_url.port,  # 端口
            user = parsed_url.username,  # 用戶名
            password = parsed_url.password,  # 密碼
            database = parsed_url.path.lstrip('/'),  # 資料庫名稱
        )
    
    else:
        print("👉 使用本地資料庫")
        # 如果沒有 DB_URL，就使用本地資料庫設定
        return mysql.connector.connect(
            host = os.getenv('DB_HOST'),
            user = os.getenv('DB_USER'),
            password = os.getenv('DB_PASSWORD'),
            database = os.getenv('DB_NAME')
        )

    
#確認有沒有找到我todo_app 資料庫裡手動建立的 tasks 資料表，如沒有就自動再創一個叫 tasks 資料表
def if_tasks_nfound ():
    conn = get_db()  #連結資料
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(50) NOT NULL,
        text VARCHAR(255) NOT NULL,
        finished BOOLEAN DEFAULT FALSE
    )
    ''')
    conn.commit() #提交變更
    cursor.close() #關閉連線
    conn.close()
    print('✅ 資料表創建成功')

if_tasks_nfound()  #執行 if_tasks_nfound()函式

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

#取得(用user_id)
@app.route('/tasks/<id>', methods = ['GET']) 
def get_tasks(id):
    conn = get_db()
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
    SELECT * FROM tasks
    WHERE user_id = %s
    ''', (id,))   # %s, (id,) 不管使用者 id 輸入什麼，系統會把它當作資料，不會被執行成 SQL 指令
    tasks = cursor.fetchall()  #取得所有符合條件的任務
    cursor.close()
    conn.close()
    print("🟢 任務清單被讀取！目前任務數：", len(tasks))    #len(tasks) 計算陣列剩餘數量
    response = json.dumps(tasks)    #jsonify寫法：return jsonify(tasks)
    return Response(response, status=200, mimetype='application/json') # mimetype (只有flask用) 會自動變成 Content-Type (js只能用這個)

#新增
@app.route('/tasks', methods = ['POST'])    
def add_task():
    data = request.get_json() #把前端送過來的資料（通常是 JSON 格式）讀出來，存進 data 這個變數。
    id = data.get('user_id')  #user_id 存在 id 變數裡
    text = data.get('text')
    conn = get_db() #連結資料庫
    cursor = conn.cursor() #連接操作 SQL 建立游標
    #執行新增的動作
    cursor.execute('''
    INSERT INTO tasks (user_id, text)
    VALUES (%s, %s)
    ''',(id,text))
    conn.commit()       ##記得要儲存資料庫
    task_id = cursor.lastrowid
    cursor.close()
    conn.close()
    new_task = {
        "id": task_id,
        "user_id": id,
        "text": text,
        "finished": False
    }
    print(f'➕ 加入了{new_task["text"]}任務')
    return jsonify(new_task),201 #把 Python 的字典（像 { "id": 1, "text": "買牛奶" }）轉成 JSON 格式，這樣前端才能懂你回什麼。

#更新完成狀態 (用id)
@app.route('/tasks/<int:task_id>/toggle', methods = ['POST'])  
def update_task(task_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True) 
    #檢查任務是否存在
    cursor.execute('''
    SELECT * FROM tasks
    WHERE id = %s  
''',(task_id,)) #id = %s： %s 是「佔位符」，它會被下面的變數 task_id 替換掉，系統會把它當作資料，不會被執行成 SQL 指令
    task = cursor.fetchone()  #從查詢結果中拿出一筆資料 （通常 id 是唯一的，所以會只有一筆）
    #執行修改任務狀態的動作
    if task:
        is_finished = not task['finished'] #預設是 False，將任務的完成狀態取反變 True
        cursor.execute('''
        UPDATE tasks SET finished = %s 
        WHERE id = %s
        ''',(is_finished,task_id))  #資料庫傳入 你完成的狀態 針對那個任務的 id (id:task_id)
        conn.commit()
        cursor.close() #關閉操作
        conn.close()   #關閉連線
        task['finished'] = is_finished # 更新任務資訊
        print(f'✔️  完成了{task["text"]}任務')
        return jsonify(task),200 
    # return jsonify({"error": "Task not found"}), 404    #js刪除按鈕沒阻止冒泡，如果按過完成再刪除會顯示沒有任務

#刪除 (用id)
@app.route('/tasks/<int:task_id>', methods = ['DELETE'])    
def delete_task(task_id):   #task_id 是傳進來的參數，代表「要刪掉哪個任務的id」
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    #檢查任務是否存在
    cursor.execute('''   
    SELECT * FROM tasks
    WHERE id = %s
    ''',(task_id,))  #用id (id:task_id)找刪除的任務是否存在
    task = cursor.fetchone()
    if not task:  #如果沒找到這筆任務
        cursor.close()
        conn.close()
        return jsonify({"error": "任務不存在"}), 404
    #執行刪除任務的動作
    cursor.execute('''
        DELETE FROM tasks
        WHERE id = %s
    ''',(task_id,))
    conn.commit()
    cursor.close()  #關掉操作 SQL 的工具，避免記憶體洩漏。
    conn.close()    #關閉資料庫的連線，釋放後端資源。
    response = {    #jsonify寫法：return jsonify({'message': 'deleted'}),200
        f"{task['text']}任務":'已刪除'    #字典 # 買牛奶 : "deleted"
    }
    json_response = json.dumps(response)    #使用 dumps 將 Python 字典轉換成 JSON 字串
    print(f'🔴 {task["text"]}結束了')
    return Response(json_response,status=200, mimetype='application/json') 

if __name__ == '__main__':  #確保只有當這個檔案是直接執行時，才會執行後面的 
    app.run(debug=False)     #啟動 app.py 檔案會開啟 debug 模式，讓開發者能更方便地調試程式碼。
    # python app.py 會執行 Debug mode 
    # flask run 不會執行 Debug mode