$(function () {
    // 登録ボタンにイベントリスナーを設定
    $('#create_form').submit(function (e) {
        // ページのリロードを止める
        e.preventDefault();
        // 登録処理（非同期）
        $().post_data($(this));
    });

    // 更新ボタンにイベントリスナーを設定
    $('form[id^="update_form_"]').submit(function (e) {
        // ページのリロードを止める
        e.preventDefault();
        // 更新処理（非同期）
        $().post_data($(this));
    });

    // 削除ボタンにイベントリスナーを設定
    $('form[id^="delete_form_"]').submit(function (e) {
        // ページのリロードを止める
        e.preventDefault();
        // 削除処理（非同期）
        $().post_data($(this));
    });

    // 検索/EXPORTボタンにイベントリスナーを設定
    $('.search_form_btn').click(function (e) {
        $(this).parents('form').attr('action', $(this).data('action'));
    });

    // IMPORTボタンにイベントリスナーを設定
    $('#import-btn').click(function (e) {
        $('#file-input').click();
    });

    // ファイル選択時
    $('#file-input').on('change', function () {
        $().import_data(this);
    });

    // モーダル画面を閉じた時の処理
    $('.modal').on('hide.bs.modal', function (e) {
        // 前回のエラー表示をクリア
        $('.errorlist').remove();
        $('.is-invalid').removeClass('is-invalid');
    });
});