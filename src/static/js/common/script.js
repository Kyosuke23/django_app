$(function () {
    /**
     * フラッシュメッセージ表示処理
     */
    $.fn.flash_message = function (options) {
        options = $.extend({
            text: '処理が完了しました。',
            how: 'append',
            class_name: 'info',
            delay: 2000
        }, options);

        return this.each(function () {
            const message = $('<span class="flash_message ' + options.class_name + '">' + options.text + '</span>');
            const $this = $(this);

            if (options.how === 'append') {
                $this.append(message);
            } else {
                $this.prepend(message);
            }

            message
                .hide()
                .fadeIn(400)
                .delay(options.delay)
                .fadeOut(800, function () {
                    $(this).remove();
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
        $('.flash_messages').each(function () {
            const msg = $(this).val();
            const cls = $(this).attr('class').split(' ').pop();
            $('#flash_message_area').flash_message({
                text: msg,
                class_name: cls,
                how: 'append',
                delay: 2500
            });
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

    // ----------------------------------------------------------
    // 詳細検索フォームの開閉状態維持＋サイドバー遷移時リセット
    // ----------------------------------------------------------
    const $collapse = $('#detailSearch');
    if ($collapse.length) {
        // 初期化（保存状態を反映）
        const savedState = localStorage.getItem('advancedSearchOpen');
        if (savedState === 'true') {
            $collapse.addClass('show');
        }

        // 開閉イベント監視
        $collapse.on('shown.bs.collapse', function () {
            localStorage.setItem('advancedSearchOpen', 'true');
        });
        $collapse.on('hidden.bs.collapse', function () {
            localStorage.setItem('advancedSearchOpen', 'false');
        });

        // 検索フォーム送信時、状態を維持
        $('#search_form').on('submit', function () {
            const isOpen = $collapse.hasClass('show');
            localStorage.setItem('advancedSearchOpen', isOpen ? 'true' : 'false');
        });
    }

    // サイドバーリンククリック時に状態リセット
    $('#sidebar a, .sidebar a').on('click', function () {
        localStorage.setItem('advancedSearchOpen', 'false');
    });
});
