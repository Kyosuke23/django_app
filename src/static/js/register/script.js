$(function () {
    // =====================================================
    // Export
    // =====================================================
    $('.export-btn').on('click', function () {
        const url = $(this).data('action');
        const checkUrl = $(this).data('check-action'); // 件数チェック用URL
        const $form = $('#search_form');
        const query = $form.serialize();

        // 1. まず件数チェックAPIを叩く
        $.get(`${checkUrl}?${query}`, function (res) {
            if (res.warning) {
                // 上限超過メッセージを警告表示
                if (!confirm(res.warning + '\n\n続行して先頭データを出力しますか？')) {
                    return; // ユーザーがキャンセル
                }
            }

            // 2. OKなら実際にエクスポート開始
            const fullUrl = query ? `${url}?${query}` : url;
            window.location.href = fullUrl;
        });
    });


    // =====================================================
    // Importボタン
    // =====================================================
    $('#import-btn').on('click', function (e) {
        e.preventDefault();
        $('#file-input').click();
    });

    $('#file-input').on('change', function () {
        if (!this.files.length) return;
        $().import_data(this);
        $(this).val('');
    });

    // =====================================================
    // 一括削除処理
    // =====================================================
    $('#check-all').checkAll('.check-item');
    $(document).on('click', '#bulk-delete-btn', function() {
        $('#bulk-delete-btn').call_bulk_delete('/register/bulk_delete/', 'ユーザー');
    });

    // =====================================================
    // 一覧画面へのSelect2適用
    // =====================================================
    (($) => {
        $(function() {
            const privileges = $('#search_privilege');
            const employment_statuses = $('#search_employment_status');
            const opt = {
                width: '100%',
                allowClear: true,
                tags: false,
                placeholder: '選択してください',
            };
            privileges.select2({...opt, placeholder: '-- 権限を選択 --'});
            employment_statuses.select2({...opt, placeholder: '-- 雇用状態を選択 --'});
        });
    })(jQuery);

    // =====================================================
    // 保存／削除ボタンの動的アクション切り替え
    // =====================================================
    $(document).on("click", "#editForm button[type=submit]", function (e) {
        const form = $("#editForm");
        const action = $(this).data("action");
        const saveUrl = form.data("save-url");
        const deleteUrl = form.data("delete-url");
        const csrf = form.find("input[name=csrfmiddlewaretoken]").val();

        if (action === "delete") {
            e.preventDefault();
            if (!confirm("本当に削除しますか？")) return;

            $.ajax({
                url: deleteUrl,
                type: "POST",
                data: { csrfmiddlewaretoken: csrf },
                success: function () {
                    location.reload();
                },
                error: function (xhr) {
                    if (xhr.responseJSON && xhr.responseJSON.error) {
                        alert(xhr.responseJSON.error);
                    } else {
                        alert("削除に失敗しました");
                    }
                }
            });
        } else {
            form.attr("action", saveUrl);
        }
    });

    // =====================================================
    // ユーザーグループ選択時に入力欄へ反映
    // =====================================================
    $(document).on('change', '#groupId', function () {
        const selectedText = $(this).find('option:selected').text();
        const selectedValue = $(this).val();
        $('#groupName').val(selectedValue ? selectedText : '');
    });

    // =====================================================
    // モーダルフォーム共通処理
    // =====================================================
    $(document).modal_form('#userModal', function($modal) {
        const genders  = $modal.find('#id_gender');
        const privileges = $modal.find('#id_privilege');
        const groups = $modal.find('#id_groups_custom');
        const opt = {
            width: '100%',
            allowClear: true,
            tags: false,
            dropdownParent: $modal,
            placeholder: '選択してください',
        };
        genders.select2({ ...opt, placeholder: '性別を選択...' });
        privileges.select2({ ...opt, placeholder: '権限を選択...' });
        groups.select2({ ...opt });
    });

    // =====================================================
    // 並べ替え変更時
    // =====================================================
    $('#form-select').on('change', function() {
        $('#search_form').submit();
    });

    // =====================================================
    // ユーザーグループ管理：削除時 required 無効化
    // =====================================================
    $(document).on('click', 'form[id="group_form"] button[name="action"][value="delete"]', function () {
        $(this).closest('form').find('#groupName').removeAttr('required');
    });

    // =====================================================
    // 初期ユーザー登録処理
    // =====================================================
    $(document).on('submit', '#initialUserForm', function(e) {
        e.preventDefault();
        var $form = $(this);
        $.ajax({
            url: $form.attr('action') || window.location.href,
            type: 'POST',
            data: new FormData(this),
            processData: false,
            contentType: false,
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            success: function(data) {
                if (data.success) {
                    location.reload();
                } else {
                    alert(data.error || '送信に失敗しました。');
                }
            },
            error: function() {
                alert('通信エラーが発生しました。');
            }
        });
    });
});
