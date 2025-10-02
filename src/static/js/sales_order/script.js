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
        $().import_data(this); // 既存の処理
    });

    // モーダルフォーム共通処理を有効化
    $(document).modal_form("#salesOrderModal");

    // 消費税率の再計算処理
    const recalcAmount = function(row) {
      let quantity = parseFloat(row.find('input[name$="quantity"]').val()) || 0;
      let unitPrice = parseFloat(row.find('input[name$="unit_price"]').val()) || 0;
      let taxRate = parseFloat(row.find('select[name$="tax_rate"]').val()) || 0;
      let isTaxExempt = row.find('input[name$="is_tax_exempt"]').is(':checked');

      // 金額計算
      let amount = quantity * unitPrice;
      if (!isTaxExempt) {
        amount = amount * (1 + taxRate);
      }

      // 整数に丸め & カンマ区切り
      let displayAmount = Math.round(amount).toLocaleString();

      // 表示に反映
      row.find('.amount').text('¥' + displayAmount);
    }

    // 消費税率変更時
    $(document).on('change', 'select[name$="tax_rate"]', function() {
      recalcAmount($(this).closest('tr'));
    });

    // 数量・単価変更時
    $(document).on('input', 'input[name$="quantity"], input[name$="unit_price"]', function() {
      recalcAmount($(this).closest('tr'));
    });

    // 税対象外チェックON/OFF時
    $(document).on('change', 'input[name$="is_tax_exempt"]', function() {
      recalcAmount($(this).closest('tr'));
    });
});
