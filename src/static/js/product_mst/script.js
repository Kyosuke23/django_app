$(function () {

    // 出力ボタンにイベントリスナーを設定
    // 出力ボタンはtype=buttonのためJSでイベントを発火（検索フォームにフォーカス時にEnterキーで検索処理を実行するため）
    document.querySelectorAll('.export-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            let form = document.getElementById('search_form');
            form.action = this.dataset.action;
            form.submit();
        });
    });

    // IMPORTボタンにイベントリスナーを設定
    $('#import-btn').click(function (e) {
        $('#file-input').click();
    });

    // ファイル選択時
    $('#file-input').on('change', function () {
        $().import_data(this);
    });
});