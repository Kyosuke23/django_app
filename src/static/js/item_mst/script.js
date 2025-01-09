$(function() {
    // 登録ボタンにイベントリスナーを設定
    $('#create_form').submit(function(e) {
        // ページのリロードを止める
        e.preventDefault();
        // 登録処理（非同期）
        $().post_data($(this));
    });

    // 更新ボタンにイベントリスナーを設定
    $('form[id^="update_form_"]').submit(function(e) {
        // ページのリロードを止める
        e.preventDefault();
        // 更新処理（非同期）
        $().post_data($(this));
    });

    // 削除ボタンにイベントリスナーを設定
    $('form[id^="delete_form_"]').submit(function(e) {
        // ページのリロードを止める
        e.preventDefault();
        // 削除処理（非同期）
        $().post_data($(this));
    });

    // Exportボタンにイベントリスナーを設定
    $('.search_form_btn').click(function(e) {
        // // 元のaction属性を保存
        // action_org = $(this).parents('form').attr('action')
        // formのaction属性をExport処理用に変更して実行
        $(this).parents('form').attr('action', $(this).data('action'));
        $(this).parents('form').submit();
        // // action属性を元に戻す
        // $(this).parents('form').attr('action', action_org);
    });
    
    // モーダル画面を閉じた時の処理
    $('.modal').on('hide.bs.modal', function (e) {
        // 前回のエラー表示をクリア
        $('.errorlist').remove();
        $('.is-invalid').removeClass('is-invalid');
    });
});