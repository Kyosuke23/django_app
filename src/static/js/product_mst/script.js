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

    // モーダルフォーム共通処理を有効化
    $(document).modal_form("#productModal");

    // 一括削除処理
    $('#check-all').checkAll('.check-item');
    $(document).on('click', '#bulk-delete-btn', function() {
        $('#bulk-delete-btn').call_bulk_delete('/product_mst/bulk_delete/', '商品');
    });
});
