window.onload = function() {
    // 登録ボタンにイベントリスナーを設定
    $('#create_form').submit(function(e) {
        // ページのリロードを止める
        e.preventDefault();
        // 登録処理（非同期）
        post_data($(this));
    });

    // 更新ボタンにイベントリスナーを設定
    $('form[id^="update_form_"]').submit(function(e) {
        // ページのリロードを止める
        e.preventDefault();
        // 登録処理（非同期）
        post_data($(this));
    });

    // モーダル画面を閉じた時の処理
    $('.modal').on('hide.bs.modal', function (e) {
        // 前回のエラー表示をクリア
        $('.errorlist').remove();
        $('.is-invalid').removeClass('is-invalid');
    });

    const post_data = function(form) {
        // 非同期でPOST通信
        $.ajax({
          url: form.prop('action'),
          method: form.prop('method'),
          data: form.serialize(),
          timeout: 10000,
          dataType: 'text',
        })
        // 成功時の処理
        .done(function(data) {
            // バリデーションエラーとなったフィールドを取得
            errors = JSON.parse(data)['errors'];
            // エラーがなければ検索処理にリダイレクト
            if (Object.keys(errors).length == 0) {
                window.location.href = JSON.parse(data)['success_url'];
            }
            // エラーフィールドのループ
            for (let key in errors) {
                // エラーフィールドを取得
                let errorField = $(`input[name='${key}']`);
                // エラーフィールドに警告色を追加
                errorField.addClass('is-invalid');
                // エラーメッセージを出力（エラーが複数ある場合は先頭のエラーのみ表示）
                errorField.after(
                    '<ul class="errorlist">'
                    +   '<li>' + errors[key][0] + '</li>'
                    + '</ul>'
                );
            }
        })
        // 失敗時の処理
        .fail(function() {
            console.log('ajax error');
        });
    };
};

