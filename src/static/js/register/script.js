$(function () {
    // エクスポートボタン
    $('.export-btn').on('click', function () {
      const url = $(this).data('action');
      if (url) {
        window.location.href = url;
      }
    });

    // IMPORTボタン
    $('#import-btn').on('click', function (e) {
        e.preventDefault();
        $('#file-input').click();
    });

    // ファイル選択時
    $('#file-input').on('change', function () {
        $().import_data(this);
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
    // =====================================================
    // モーダルフォーム共通処理
    // =====================================================
    $(document).modal_form('#userModal', function($modal) {
        // 適用先フォームの取得
        const genders  = $modal.find('#id_gender');
        const privileges = $modal.find('#id_privilege');

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
    });
});
