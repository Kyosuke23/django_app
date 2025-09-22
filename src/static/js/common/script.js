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
     * データ登録処理（非同期）
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

    /**
     * データのimport処理（非同期）
     * @returns 
     */
    $.fn.import_data = function(form) {
        let file = form.files[0]
        if (!file) return;

        let formData = new FormData();
        formData.append('file', file);
        formData.append('csrfmiddlewaretoken', $('[name=csrfmiddlewaretoken]').val());

        // テンプレートから渡された action-url を取得
        let url = $('#import-btn').data('action');

        $.ajax({
            url: url,
            type: 'POST',
            data: formData,
            contentType: false,
            processData: false,
            xhr: function () {
                var xhr = $.ajaxSettings.xhr();
                if (xhr.upload) {
                    xhr.upload.addEventListener('progress', function (e) {
                        if (e.lengthComputable) {
                            var percent = Math.round((e.loaded / e.total) * 100);
                            $('.progress').show();
                            $('#progress-bar').css('width', percent + '%').text(percent + '%');
                        }
                    }, false);
                }
                return xhr;
            }
        })
        .done(function(response) {
            alert('アップロード完了: ' + response.message);
            location.reload();
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
            $('.progress-bar')
                .removeClass('bg-success')
                .addClass('bg-danger')
                .text('Import時にエラー発生');
            alert(['アップロード失敗:', jqXHR.responseJSON?.error || '',  jqXHR.responseJSON?.details || ''].join('\n'));
        });
    };

    // AjaxのPOST通信に必要な処理 /////////////////////////////////
    $.fn.getCookie = function(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            let cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                let cookie = jQuery.trim(cookies[i]);
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };
    $.fn.csrfSafeMethod = function(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    ///////////////////////////////////////////////////////////
});