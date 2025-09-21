$(function() {

    const CELL_WIDTH = 30;
    const DATASET_DATE_FORMAAT = 'YYYY-MM-DD hh:mm:ss';

    const today = new Date(2025, 6 - 1, 25);
    let disp_date = today;


    const test_data_row = [{
        subject: "subject-a"
        , type: "type-a"
        , start: "2025-06-24 20:00:00"
        , end: "2025-06-25 17:00:00"
    }
    , {
        subject: "subject-b"
        , type: "type-b"
        , start: "2025-06-25 09:15:00"
        , end: "2025-06-25 13:00:00"
    }, {
        subject: "subject-c"
        , type: "type-c"
        , start: "2025-06-25 20:00:00"
        , end: "2025-06-26 4:00:00"
    }];
    const test_data_json = JSON.stringify(test_data_row)
    const test_data = JSON.parse(test_data_json);


    const data = test_data;


    const row_num = test_data.length;
    const col_num = 48;

    let object = document.getElementById('graph');
    let title_dt = document.createElement('h2');
    title_dt.textContent = get_formated_time('YYYY-MM-DD', disp_date);
    object.appendChild(title_dt);


    let div_tbl = document.createElement('div');
    div_tbl.className = 'table_wrap';
    object.appendChild(div_tbl);

    let table = document.createElement('table');

    // Tableを描画
    div_tbl.appendChild(table);

    // Theadタグの生成
    let thead = document.createElement('thead');
    table.appendChild(thead);

    // 先頭行の生成
    let th = document.createElement('th');
    th.classList.add('sticky');
    thead.appendChild(th);
    for (let i = 0; i < col_num; i++) {
        th = document.createElement('th');
        if (i % 2 === 0) {
            th.textContent = (i / 2) + ':00'
            th.colSpan = 2;
            thead.appendChild(th);
        }
    }

    // 2行目以降の生成
    let tbody = document.createElement('tbody');
    table.appendChild(tbody);
    for (let i = 0; i < row_num; i++) {

        let tr = document.createElement('tr');
        let td = document.createElement('td');
        const subject = test_data[i]['subject']
        td.textContent = subject
        td.className = 'subject_th';
        td.classList.add('sticky');
        tr.appendChild(td);

        for (let j = 0; j < col_num; j++) {
            const h =  Math.floor(j / 2);
            const m = j % 2 === 0 ? 0: 30;
            const dt = new Date(disp_date.getFullYear(), disp_date.getMonth(), disp_date.getDate(), h, m, 0);
            td = document.createElement('td');
            td.id = subject + '_' + h + '-' + m;
            td.className = 'cell_td';
            td.classList.add(subject);
            td.dataset.dt = get_formated_time(DATASET_DATE_FORMAAT, dt);
            tr.appendChild(td);
        }
        tbody.appendChild(tr);
    }

    for (let i = 0; i < data.length; i++) {
        // データ値を取得
        const subject = data[i]['subject'];
        const type = data[i]['type'];
        let start = data[i]['start'];
        let end = data[i]['end'];

        // 開始・終了時刻を取得
        let start_dt = new Date(start);
        let end_dt = new Date(end);

        // 昨日以前の開始日時の場合、開始日時を本日の0時にセット
        if (start_dt <= disp_date) {
            start_dt = new Date(disp_date);
            start = get_formated_time(DATASET_DATE_FORMAAT, start_dt);
        }

        // 開始日時の分を0か30に固定
        if (start_dt.getMinutes() < 30) {
            start_dt.setMinutes(0);
        } else {
            start_dt.setMinutes(30);
        }

        // 明日以降の終了日時の場合、終了日時を翌日の0時にセット
        const next_date = new Date(disp_date.getFullYear(), disp_date.getMonth(), disp_date.getDate() + 1);
        if (next_date <= end_dt) {
            end_dt = next_date;
            end = get_formated_time(DATASET_DATE_FORMAAT, end_dt);
        }

        // 終了日時の分を0か30に固定
        if (end_dt.getMinutes() < 30) {
            end_dt.setMinutes(0);
        } else {
            end_dt.setMinutes(30);
        }

        // データの埋め込み先起点セルを検索
        let target_dt = get_formated_time(DATASET_DATE_FORMAAT, start_dt);;
        let target_cell = document.querySelector(`[class~="${subject}"][data-dt="${target_dt}"]`);

        // データのマス数を算出
        const cell_size = get_col_span(start_dt, end_dt, disp_date);

        // データセル要素
        let el = document.createElement('div');
        el.className = 'el';
        el.style.width = (CELL_WIDTH * cell_size + cell_size / 8)+ 'px';
        target_cell.appendChild(el);

        // データのテキスト要素
        let div = document.createElement('div');
        div.textContent = type;
        el.appendChild(div);
    }
});

/**
 * タイムライン上でスケジュール要素を表示させるマス数を取得
 * @param {} rec 
 * @returns 
 */
const get_col_span = function(start_dt, end_dt) {
    // 開始・終了の時間差を算出
    const time_diff = end_dt.getTime() - start_dt.getTime();
    const diff_s = time_diff / 1000;
    const diff_m = diff_s / 60;
    const diff_h = diff_m / 60;

    // タイムラインは30分表示なので、マス数は時間×2となる
    return diff_h * 2;
};

const  get_formated_time = (fmt, dt) => [
        [ 'YYYY', dt.getFullYear()  ],
        [ 'MM',   dt.getMonth() + 1 ], 
        [ 'DD',   dt.getDate()      ],
        [ 'hh',   dt.getHours()     ],
        [ 'mm',   dt.getMinutes()   ],
        [ 'ss',   dt.getSeconds()   ],
        [ 'iii',  dt.getMilliseconds() ],
    ].reduce(
        (s,a) => s.replace( a[0], `${a[1]}`.padStart(a[0].length,'0') ),
        fmt
    )