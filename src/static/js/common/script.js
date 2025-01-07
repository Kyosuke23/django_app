$(function() {
    /**
     * フラッシュメッセージ表示処理
     * @param {*} options 
     * @returns フラッシュメッセージ
     */
    $.fn.flash_message = function(options) {
        //デフォルト値
        options = $.extend({
            text: '完了しました',
            time: 3000,
            how: 'before',
            class_name: ''
        }, options);

        return $(this).each(function() {
            //指定したセレクタを探して取得
            if ($(this).find('.flash_messages').get(0)) {
                $(this).find('.flash_messages').remove();
            }

            var message = $('<span />', {
                'class': 'flash_messages ' + options.class_name,
                text: options.text
            //フェードイン表示
            });

            $(this)[options.how](message).addClass('show');
            //delayさせてからフェードアウト
            message.delay(options.time).queue(function(){
                $(this).parents('#flash_message_area').removeClass('show');
            });
        });
    };

    /**
     * 非同期通信処理
     * @param {*} form 
     */
    $.fn.post_data = function(form) {
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
                // リダイレクト先設定
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

    // フラッシュメッセージの表示判定 & 実行
    if ($('.flash_messages').length) {
        $('#flash_message_area').flash_message({
            text: $('.flash_messages').val(),
            how: 'append'
        });
    }
});