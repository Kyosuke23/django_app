$(function () {
    /**
     * フラッシュメッセージ表示処理
     */
    $.fn.flash_message = function (options) {
        options = $.extend({
            text: '完了しました',
            time: 3000,
            how: 'before',
            class_name: 'info'
        }, options);

        return $(this).each(function () {
            if ($(this).find('.flash_messages').length) {
                $(this).find('.flash_messages').fadeOut(200, function () {
                    $(this).remove();
                });
            }
            var message = $('<span />', {
                'class': 'flash_messages ' + options.class_name,
                text: options.text
            });
            $(this)[options.how](message).addClass('show');
            message.delay(options.time).queue(function () {
                $(this).parents('#flash_message_area').removeClass('show');
                $(this).remove();
            });
        });
    };

    /**
     * データ登録処理（非同期）
     */
    $.fn.post_data = function (form) {
        form.find('.is-invalid').removeClass('is-invalid');
        form.find('.errorlist').remove();

        $.ajax({
            url: form.prop('action'),
            method: form.prop('method'),
            data: form.serialize(),
            timeout: 10000,
            dataType: 'json',
        })
        .done(function (data) {
            let errors = data.errors || {};
            if (Object.keys(errors).length === 0) {
                window.location.href = data.success_url;
                return;
            }
            for (let key in errors) {
                let errorField = $(`input[name='${key}']`);
                errorField.addClass('is-invalid');
                errorField.after('<ul class="errorlist"><li>' + errors[key][0] + '</li></ul>');
            }
        })
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
     */
    $.fn.import_data = function (input) {
        let file = input.files[0];
        if (!file) return;

        let formData = new FormData();
        formData.append('file', file);
        formData.append('csrfmiddlewaretoken', $('[name=csrfmiddlewaretoken]').val());

        let url = $('#import-btn').data('action');
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
            if (textStatus != 'abort') {
                alert(['アップロード失敗:', jqXHR.responseJSON?.error || '', jqXHR.responseJSON?.details || ''].join('\n'));
                spinner.addClass('d-none');
            }
        })
        .always(function () {
            spinner.addClass('d-none');
        });

        $('#cancel-btn').off('click').on('click', function () {
            if (jqXHR) jqXHR.abort();
            spinner.addClass('d-none');
        });
    };

    /**
     * モーダルフォーム（共通部品）
     */
    $.fn.modal_form = function (modalSelector, afterLoadCallback) {
        const $modal = $(modalSelector);

        $modal.on('show.bs.modal', function (e) {
            const url = $(e.relatedTarget).data('url');
            $.ajax({
                url: url,
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                dataType: 'json',
            })
            .done(function (data) {
                $modal.find('.modal-body').html(data.html);
                afterLoadCallback($modal);
            })
            .fail(function () {
                $('#flash_message_area').flash_message({
                    text: 'フォームの読込に失敗しました',
                    class_name: 'error',
                    how: 'append',
                    time: 4000
                });
            });
        });

        $modal.on('submit', 'form', function (e) {
            e.preventDefault();
            const $form = $(this);

            $.ajax({
                url: $form.attr('action') || window.location.href,
                type: 'POST',
                data: new FormData(this),
                processData: false,
                contentType: false,
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                dataType: 'json'
            })
            .done(function (data) {
                if (data.success) {
                    location.reload();
                } else {
                    $modal.find('.modal-body').html(data.html);
                    afterLoadCallback($modal);
                }
            })
            .fail(function () {
                $('#flash_message_area').flash_message({
                    text: 'サーバー通信に失敗しました',
                    class_name: 'error',
                    how: 'append',
                    time: 4000
                });
            });
        });

        return this;
    };

    // フラッシュメッセージの表示判定
    if ($('.flash_messages').length) {
        $('#flash_message_area').flash_message({
            text: $('.flash_messages').val(),
            how: 'append'
        });
    }

    // CSRF関連
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

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!$.fn.csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader('X-CSRFToken', $.fn.getCookie('csrftoken'));
            }
        }
    });

    // チェックボックス全選択
    $.fn.checkAll = function (itemSelector) {
        const master = this;
        const items = $(itemSelector);
        master.on('change', function () {
            items.prop('checked', master.prop('checked'));
        });
        items.on('change', function () {
            const allChecked = items.length === items.filter(':checked').length;
            master.prop('checked', allChecked);
        });
        return this;
    };

    // 一括削除
    $.fn.call_bulk_delete = function (url, target_nm) {
        let ids = $('.check-item:checked').map(function () {
            return $(this).val();
        }).get();

        if (ids.length === 0) {
            alert(`削除する${target_nm}を選択してください`);
            return;
        }
        if (!confirm(`選択した${target_nm}を一括削除しますか？`)) return;

        $.ajax({
            url: url,
            type: 'POST',
            data: {
                ids: ids,
                csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
            },
            traditional: true,
            success: function (jqXHR) {
                alert(jqXHR.message);
                location.reload();
            },
            error: function (jqXHR) {
                alert([jqXHR.responseJSON?.error || '', jqXHR.responseJSON?.details || ''].join('\n'));
            }
        });
    };

    /**
     * テーマ切り替え機能
     */
    const savedTheme = localStorage.getItem('theme') || 'light';
    $('html').attr('data-theme', savedTheme);

    const $icon = $('#themeToggle i');
    if ($icon.length) {
        $icon.attr('class', savedTheme === 'dark' ? 'bi bi-sun' : 'bi bi-moon');
    }

    $('#themeToggle').on('click', function () {
        const $html = $('html');
        const current = $html.attr('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        $html.attr('data-theme', next);
        localStorage.setItem('theme', next);

        if ($icon.length) {
            $icon.attr('class', next === 'dark' ? 'bi bi-sun' : 'bi bi-moon');
        }
    });
});
