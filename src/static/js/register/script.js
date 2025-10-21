$(function () {
    // Exportボタン
    $('.export-btn').on('click', function () {
        const url = $(this).data('action');
        const $form = $('#search_form');
        const query = $form.serialize();

        // クエリがあればURLに付加
        const fullUrl = query ? `${url}?${query}` : url;

        // 画面遷移してダウンロード処理実行
        window.location.href = fullUrl;
    });

    // Importボタン
    $('#import-btn').on('click', function (e) {
        e.preventDefault();
        $('#file-input').click();
    });

    // ファイル選択時
    $('#file-input').on('change', function () {
         if (!this.files.length) return;
        $().import_data(this);
        $(this).val(''); // 同一ファイル再選択時にも発火するようにリセ
    });

    // 一括削除処理
    $('#check-all').checkAll('.check-item');
    $(document).on('click', '#bulk-delete-btn', function() {
        $('#bulk-delete-btn').call_bulk_delete('/register/bulk_delete/', 'ユーザー');
    });

    // 一覧画面へのSelect2適用
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

    // 保存／削除ボタンの動的アクション切り替え
    $(document).on("click", "#editForm button[type=submit]", function (e) {
        const form = $("#editForm");
        const action = $(this).data("action");
        const saveUrl = form.data("save-url");
        const deleteUrl = form.data("delete-url");
        const csrf = form.find("input[name=csrfmiddlewaretoken]").val();

        if (action === "delete") {
            e.preventDefault(); // 通常のsubmitは止める
            if (!confirm("本当に削除しますか？")) {
                return;
            }

            // Ajaxで削除リクエスト
            $.ajax({
                url: deleteUrl,
                type: "POST",
                data: { csrfmiddlewaretoken: csrf },
                success: function () {
                    location.reload(); // 削除成功時はリロード
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
            // 保存時は通常のsubmitを利用
            form.attr("action", saveUrl);
        }
    });

    // ユーザーグループ選択時に入力欄へ反映
    $(document).on('change', '#groupId', function () {
        const selectedText = $(this).find('option:selected').text();
        const selectedValue = $(this).val();

        if (selectedValue) {
            // 既存グループ選択時 → 名前を入力欄に反映
            $('#groupName').val(selectedText);
        } else {
            // 新規作成選択時 → 入力欄をクリア
            $('#groupName').val('');
        }
    });

    // =====================================================
    // モーダルフォーム共通処理
    // =====================================================
    $(document).modal_form('#userModal', function($modal) {
        // 適用先フォームの取得
        const genders  = $modal.find('#id_gender');
        const privileges = $modal.find('#id_privilege');
        const groups = $modal.find('#id_groups_custom');

        // Select2のオプション設定
        const opt = {
            width: '100%',
            allowClear: true,
            tags: false,
            dropdownParent: $modal,
            placeholder: '選択してください',
        };

        // Select2を適用
        genders.select2({ ...opt, placeholder: '性別を選択...' });
        privileges.select2({ ...opt, placeholder: '権限を選択...' });
        groups.select2({ ...opt });
    });

    // =====================================================
    // 並べ替え変更時
    // ===================================================
    $('#form-select').on('change', function() {
        $('#search_form').submit(); // 並び順変更時にフォーム送信
    });

    // =====================================================
    // ユーザーグループ管理：削除時 required 無効化
    // =====================================================
    $(document).on('click', 'form[id="group_form"] button[name="action"][value="delete"]', function () {
        const $form = $(this).closest('form');
        const $groupName = $form.find('#groupName');
        $groupName.removeAttr('required');
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
