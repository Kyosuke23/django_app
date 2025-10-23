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
    // Import
    // =====================================================
    // ボタン押下時
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

    // =====================================================
    // 一括削除処理
    // =====================================================
    $('#check-all').checkAll('.check-item');
    $(document).on('click', '#bulk-delete-btn', function() {
        $('#bulk-delete-btn').call_bulk_delete('/product_mst/bulk_delete/', '商品');
    });

    // 一覧画面へのSelect2適用
    (($) => {
        $(function() {
            const product_category_eidtor = $('#categoryId');
            const product_categories = $('#search_product_category');

            const opt = {
                width: '100%',
                allowClear: true,
                tags: false,
                placeholder: '選択してください',
            };

            product_category_eidtor.select2({...opt, placeholder: '--- 新規作成'});
            product_categories.select2({...opt, placeholder: '-- 全カテゴリ --'});
        });
    })(jQuery);

    // 保存／削除ボタンの動的アクション切り替え
    $(document).on('click', '#editForm button[type=submit]', function (e) {
        const form = $('#editForm');
        const action = $(this).data('action');
        const saveUrl = form.data('save-url');
        const deleteUrl = form.data('delete-url');
        const csrf = form.find('input[name=csrfmiddlewaretoken]').val();

        if (action === 'delete') {
            e.preventDefault(); // 通常のsubmitは止める
            if (!confirm('本当に削除しますか？')) {
                return;
            }

            // Ajaxで削除リクエスト
            $.ajax({
                url: deleteUrl,
                type: 'POST',
                data: { csrfmiddlewaretoken: csrf },
                success: function () {
                    location.reload(); // 削除成功時はリロード
                },
                error: function (xhr) {
                    if (xhr.responseJSON && xhr.responseJSON.error) {
                        alert(xhr.responseJSON.error);
                    } else {
                        alert('削除に失敗しました');
                    }
                }
            });
        } else {
            // 保存時は通常のsubmitを利用
            form.attr('action', saveUrl);
        }
    });

    // カテゴリ選択時に入力欄へ反映
    $(document).on('change', '#categoryId', function () {
        const selectedText = $(this).find('option:selected').text();
        const selectedValue = $(this).val();

        if (selectedValue) {
            // 既存カテゴリ選択時 → 名前を入力欄に反映
            $('#categoryName').val(selectedText);
        } else {
            // 新規作成選択時 → 入力欄をクリア
            $('#categoryName').val('');
        }
    });

    // 商品カテゴリ削除時に確認ダイアログを表示
    $(document).on('click', 'button[name="action"][value="delete"]', function (e) {
        if (!confirm('本当に削除しますか？')) {
            e.preventDefault();
        }
    });

    // =====================================================
    // モーダルフォーム共通処理
    // =====================================================
    $(document).modal_form('#productModal', function($modal) {
        // 適用先フォームの取得
        const categories  = $modal.find('#id_product_category');

        // Select2のオプション設定
        const opt = {
            width: '100%',
            allowClear: true,
            tags: false,
            dropdownParent: $modal,
            placeholder: '選択してください',
        };

        // Select2を適用
        categories.select2({ ...opt, placeholder: '商品カテゴリを選択...' });
    });

    // =====================================================
    // 並べ替え変更時
    // ===================================================
    $('#form-select').on('change', function() {
        const sort = $(this).val();
        const baseUrl = new URL(window.location.href);

        // 既存の検索条件を維持
        baseUrl.searchParams.set('sort', sort);

        // そのURLへ遷移（＝GET送信）
        window.location.href = baseUrl.toString();
    });

    // =====================================================
    // 商品カテゴリ管理：削除時 required 無効化
    // =====================================================
    $(document).on('click', 'form[id="category_form"] button[name="action"][value="delete"]', function () {
        const $form = $(this).closest('form');
        const $groupName = $form.find('#categoryName');
        $groupName.removeAttr('required');
    });
});
