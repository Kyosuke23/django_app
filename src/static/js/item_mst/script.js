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
    $("#file-input").on("change", function () {
        var file = this.files[0];
        if (!file) return;

        var formData = new FormData();
        formData.append('file', file);
        formData.append('csrfmiddlewaretoken', $('[name=csrfmiddlewaretoken]').val());

        // テンプレートから渡された data-url を取得
        var url = $("#import-btn").data('action');

        $.ajax({
            url: url,
            type: 'POST',
            data: formData,
            contentType: false,
            processData: false,
            xhr: function () {
                var xhr = $.ajaxSettings.xhr();
                if (xhr.upload) {
                    xhr.upload.addEventListener("progress", function (e) {
                        if (e.lengthComputable) {
                            var percent = Math.round((e.loaded / e.total) * 100);
                            $(".progress").show();
                            $("#progress-bar").css("width", percent + "%").text(percent + "%");
                        }
                    }, false);
                }
                return xhr;
            }
        })
        .done(function(response) {
            alert("アップロード完了: " + response.message);
            location.reload();
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
            $(".progress-bar")
                .removeClass("bg-success")
                .addClass("bg-danger")
                .text("Import時にエラー発生");
            alert(['アップロード失敗:', jqXHR.responseJSON?.error || '',  jqXHR.responseJSON?.details || ''].join('\n'));
        });
    });

    // モーダル画面を閉じた時の処理
    $('.modal').on('hide.bs.modal', function (e) {
        // 前回のエラー表示をクリア
        $('.errorlist').remove();
        $('.is-invalid').removeClass('is-invalid');
    });
});