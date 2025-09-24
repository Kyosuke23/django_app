$(function () {
    /**
     * フラッシュメッセージ表示処理
     * @param {*} options 
     * @returns フラッシュメッセージ
     */
    $.fn.flash_message = function (options) {
        // デフォルト値
        options = $.extend({
            text: '完了しました',
            time: 3000,
            how: 'before',
            class_name: 'info'
        }, options);

        return $(this).each(function () {
            // 既存のメッセージを削除
            if ($(this).find('.flash_messages').length) {
                $(this).find('.flash_messages').fadeOut(200, function () {
                    $(this).remove();
                });
            }

            // 新しいメッセージ作成
            var message = $('<span />', {
                'class': 'flash_messages ' + options.class_name,
                text: options.text
            });

            $(this)[options.how](message).addClass('show');

            // 指定時間後にフェードアウト
            message.delay(options.time).queue(function () {
                $(this).parents('#flash_message_area').removeClass('show');
                $(this).remove();
            });
        });
    };

    /**
     * データ登録処理（非同期）
     * @param {*} form jQueryオブジェクト
     */
    $.fn.post_data = function (form) {
        // 既存エラーのクリア
        form.find('.is-invalid').removeClass('is-invalid');
        form.find('.errorlist').remove();

        $.ajax({
            url: form.prop('action'),
            method: form.prop('method'),
            data: form.serialize(),
            timeout: 10000,
            dataType: 'json',
        })
            // 成功時の処理
            .done(function (data) {
                let errors = data.errors || {};
                if (Object.keys(errors).length === 0) {
                    // リダイレクト
                    window.location.href = data.success_url;
                    return;
                }

                // エラーフィールドのループ
                for (let key in errors) {
                    let errorField = $(`input[name='${key}']`);
                    errorField.addClass('is-invalid');
                    errorField.after(
                        '<ul class="errorlist"><li>' + errors[key][0] + '</li></ul>'
                    );
                }
            })
            // 失敗時の処理
            .fail(function () {
                $('#flash_message_area').flash_message({
                    text: 'サーバー通信に失敗しました',
                    class_name: 'error',
                    how: 'append',
                    time: 4000
                });
            });
    };

    /**
     * データのimport処理（非同期）
     * @param {*} input type=file のDOM
     */
    $.fn.import_data = function (input) {
        let file = input.files[0];
        if (!file) return;

        let formData = new FormData();
        formData.append('file', file);
        formData.append('csrfmiddlewaretoken', $('[name=csrfmiddlewaretoken]').val());

        let url = $('#import-btn').data('action');

        // スピナー表示
        let spinner = $('#loading-spinner');
        spinner.removeClass('d-none');

        let jqXHR = $.ajax({
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
                            $('.progress').removeClass('d-none');
                            $('#progress-bar')
                                .css('width', percent + '%')
                                .attr('aria-valuenow', percent)
                                .text(percent + '%');
                        }
                    }, false);
                }
                return xhr;
            }
        })
        .done(function (response) {
            alert('アップロード完了: ' + response.message);
            spinner.addClass('d-none');
            setTimeout(() => location.reload(), 2000);
        })
        .fail(function (jqXHR, textStatus) {
            //  キャンセルボタンによる中断の時は何もしない
            if (textStatus != 'abort') {
                alert(['アップロード失敗:', jqXHR.responseJSON?.error || '',  jqXHR.responseJSON?.details || ''].join('\n'));
                spinner.addClass('d-none');
            }
        })
        .always(function () {
            spinner.addClass('d-none');  // 念のため always で非表示
        });

        // キャンセルボタン処理
        $('#cancel-btn').off('click').on('click', function () {
            if (jqXHR) {
                jqXHR.abort();  // 通信を中断
            }
            spinner.addClass('d-none');
        });
    };

    // フラッシュメッセージの表示判定 & 実行
    if ($('.flash_messages').length) {
        $('#flash_message_area').flash_message({
            text: $('.flash_messages').val(),
            how: 'append'
        });
    }

    // CSRFトークン取得
    $.fn.getCookie = function (name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            let cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                let cookie = $.trim(cookies[i]);
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };

    $.fn.csrfSafeMethod = function (method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    };

    // 全てのAjax通信にCSRFトークンを自動付与
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!$.fn.csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader('X-CSRFToken', $.fn.getCookie('csrftoken'));
            }
        }
    });
});
