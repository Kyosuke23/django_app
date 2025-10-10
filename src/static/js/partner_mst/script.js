$(function () {
    // エクスポートボタン
    $('.export-btn').on('click', function () {
      const url = $(this).data('action');
      const params = $('#search_form').serialize(); // 検索フォームを取得
      if (url) {
        window.location.href = params ? `${url}?${params}` : url;
      }
    });

    // IMPORTボタン
    $('#import-btn').on('click', function (e) {
        e.preventDefault();
        $('#file-input').click();
    });

    // ファイル選択時
    $('#file-input').on('change', function () {
        $().import_data(this); // 既存の処理
    });

    // 一括削除処理
    $('#check-all').checkAll('.check-item');
    $(document).on('click', '#bulk-delete-btn', function() {
        $('#bulk-delete-btn').call_bulk_delete('/partner_mst/bulk_delete/', '取引先');
    });

    // 一覧画面へのSelect2適用
    (($) => {
        $(function() {
            const partner_types = $('#search_partner_type');

            const opt = {
                width: '100%',
                allowClear: true,
                tags: false,
                placeholder: '選択してください',
            };

            partner_types.select2({...opt, placeholder: '-- 全区分 --'});
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
    $(document).modal_form('#partnerModal', function($modal) {
        // 適用先フォームの取得
        const partner_types = $modal.find('#id_partner_type');

        // Select2のオプション設定
        const opt = {
            width: '100%',
            allowClear: true,
            tags: false,
            dropdownParent: $modal,
            placeholder: '選択してください',
        };

        // Select2を適用
        partner_types.select2({ ...opt, placeholder: '取引先区分を選択...' });
    });

    // =====================================================
    // 並べ替え変更時
    // ===================================================
    $('#form-select').on('change', function() {
        $('#search_form').submit(); // 並び順変更時にフォーム送信
    });
});
