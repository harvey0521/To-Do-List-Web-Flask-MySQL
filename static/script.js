const taskInput = document.querySelector('#taskInput')
const addButton = document.querySelector('#addButton')
const taskList = document.querySelector('#taskList')
const user_id = document.querySelector('#user_id')
const startButton = document.querySelector('#startButton')
const userIdDisplay = document.querySelector('#userIdDisplay')

//使用者輸入名稱或自動產生名稱 導向首頁
if (user_id) {         //登入頁才有的元素，才做以下的事
    function start() {

        let id = user_id.value.trim() // 取得輸入框的值

        if (!id) {        //如果使用者沒有使用輸入框(系統自動產生)
            id = Math.random().toString(36).substring(2, 8);
        }

        localStorage.setItem('user_id', id)  //user_id 資料儲存在 localStorage

        window.location.href = "/";  //導向瀏覽器的根目錄
    }
    // 當登入按鈕被點擊，執行 start()  
    startButton.addEventListener('click', start);
    // window.start = start; //也可 (<button onclick="start()">開始</button>)

    user_id.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
            start()
        }
    })
}
if (taskList) {         //主頁才有的元素，才做以下的事
    //檢查有沒有登入過（有沒有名稱）
    let id = localStorage.getItem('user_id')

    if (!id) {        //如果沒有，跳轉回 login 頁面
        window.location.href = "/login";
    }

    userIdDisplay.innerText = id;


    // 讀取任務列表（從後端拿資料）
    function fetchTasks() {
        fetch(`/tasks/${id}`)     //從後端拿資料  預設就是 GET // "user_id": id
            .then(function (response) {
                return response.json()  // 將後端回傳的資料轉換成 JSON 格式
            })
            .then(function (data) {       //清空防止按下刪除(執行fetchTasks())時會疊加任務
                taskList.innerHTML = ''; //操作該 taskList 元素(<ul>)內部 HTML 內容的所有 HTML 子元素（像 <li> 等），把裡面的內容清空
                for (let i = 0; i < data.length; i++) {
                    let task = data[i]  // 取出每一個任務物件
                    addTaskToDOM(task);  // 顯示每一個任務
                };
            });
    }

    // 把一個任務加到畫面上
    function addTaskToDOM(task) {
        const taskItem = document.createElement('li');
        taskItem.textContent = task.text;

        //當點擊任務代表完成
        if (task.finished) {   //如果這個任務是完成的（finished === true）
            taskItem.classList.add('finished'); //加上 .finished 的 CSS class
        }

        taskItem.addEventListener('click', function () {
            fetch(`/tasks/${task.id}/toggle`, {    //"id": task_id
                method: 'POST'
            })
                .then(function (response) {
                    return response.json()
                })
                .then(function (update) {
                    taskItem.classList.toggle('finished', update.finished);
                });
        });

        //加入刪除按鈕
        const deleteButton = document.createElement('button')
        deleteButton.innerHTML = `
        <span class="delete-text">刪除</span>
        <i class="fa-solid fa-trash delete-icon"></i>`;
        deleteButton.addEventListener('click', function (event) {
            event.stopPropagation();    //阻止事件冒泡 (點刪除時可能連同「切換完成狀態」也被觸發)
            deleteTask(task.id)    //執行刪除任務的動作
        });

        taskItem.appendChild(deleteButton)  //把剛剛用 createElement('button') 做出來的「刪除按鈕」加進去 <li> 任務項目裡面。
        taskList.appendChild(taskItem)  //把整個任務項目（<li> + 按鈕）加進畫面上的任務清單（<ul>）裡。
    }


    // 點擊按鈕新增任務（送到後端）
    function addtask() {
        const text = taskInput.value.trim(); //把使用者輸入框裡的文字讀出來，並用 .trim() 去除前後空白。
        if (text) {
            fetch('/tasks', {    //後端「POST(送請求)」的方法
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'  //告訴後端這是 JSON（用 Content-Type）
                },
                body: JSON.stringify({
                    "user_id": id,  // 這是從 localStorage 讀取的 ID
                    'text': text
                })  //把資料轉成 JSON 字串送去後端（用 JSON.stringify()）
            })
                .then(function (response) {
                    return response.json() //把後端送回來的「JSON 格式的文字」轉成 JavaScript 能用的物件。
                })
                .then(function (newTask) {
                    addTaskToDOM(newTask)   //之前定義的函數，它會重新顯示所有任務（加上剛剛新增的）
                    taskInput.value = '';  // 清空輸入框
                });
        }
    }

    // 當加入按鈕被點擊，新增任務
    addButton.addEventListener('click', addtask);

    //按下 Enter 鍵時就新增任務
    taskInput.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
            addtask()
        }
    })

    // 刪除任務（通知後端刪除）
    function deleteTask(task_id) {      // "id":task_id
        fetch(`/tasks/${task_id}`, {
            method: 'DELETE'    // 對後端發送 DELETE 請求，刪掉這筆任務
        })
            .then(function () {
                fetchTasks();   // 刪除成功之後，重新抓資料並更新畫面
            })
    }


    // 頁面一開始就讀取現有任務
    fetchTasks();
}