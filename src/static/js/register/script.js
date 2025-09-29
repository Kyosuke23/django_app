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
        $(this).parents('form').attr('action', $(this).data('action'));
    });

    // 住所検索ボタンにイベントリスナーを設定
    $('.btn-search-postal-code').on('click', function(e) {
        // ページのリロードを止める
        e.preventDefault();
        // クリックされた検索ボタンの属性を取得
        const type = this.dataset.type;
        // 入力された郵便番号を取得
        const postal_code = $(`input[name="postal_code"][class~="${type}"]`).val();
        // Ajax処理
        if (postal_code) {
            $.ajax({
                url: 'get_postal_code/',
                type: 'POST',
                data: {'postal_code': postal_code},
                dataType: 'text',
                // formのcsrfトークンが使えないので自力で行う
                beforeSend: function(xhr, settings) {
                    if (!$().csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", $().getCookie('csrftoken'));
                    }
                }
            })
            .done(function(data) {
                // JSON形式の取得結果をオブジェクトに変換
                const data_json = JSON.parse(data);
                // 住所情報を取得
                const results = data_json.address_info.results;
                // 住所情報をフォームに反映
                if (results != null) {
                    $(`input[name="state"][class~="${type}"]`).val(results[0].address1);
                    $(`input[name="city"][class~="${type}"]`).val(results[0].address2);
                    $(`input[name="address"][class~="${type}"]`).val(results[0].address3);
                }
            })
            .fail(function() {
                console.log('ajax error');
            });
        }
    });

    // モーダル画面を閉じた時の処理
    $('.modal').on('hide.bs.modal', function (e) {
        // 前回のエラー表示をクリア
        $('.errorlist').remove();
        $('.is-invalid').removeClass('is-invalid');
    });
});