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

  const formatYen = function(value) {
    return '¥' + Math.round(value).toLocaleString();
  };


  const recalcTotals = function() {
    let subtotal = 0;
    let taxTotal = 0;
    let grandTotal = 0;

    $('table tbody tr').each(function() {
      const $row = $(this);
      const qty = parseFloat($row.find('input[name$="quantity"]').val()) || 0;
      const price = parseFloat($row.find('input[name$="unit_price"]').val()) || 0;
      const taxRate = parseFloat($row.find('select[name$="tax_rate"]').val()) || 0;
      const isTaxExempt = $row.find('input[name$="is_tax_exempt"]').is(':checked');
      const isDeleted = $row.find('input[name$="DELETE"]').is(':checked');
      const hasProduct = $row.find('select[name$="-product"]').val();

      // 小計対象金額（税抜）
      let lineSubtotal = qty * price;
      let lineTax = isTaxExempt ? 0 : Math.floor(lineSubtotal * taxRate);
      let lineTotal = lineSubtotal + lineTax;

      // 削除チェックがONなら除外
      if (!isDeleted) {
        subtotal += lineSubtotal;
        taxTotal += lineTax;
        grandTotal += lineTotal;
      }

      // 金額セルの表示も更新
      if (isDeleted && !hasProduct) {
        // 商品未選択かつ削除チェックONなら空白
        $row.find('.amount').text('');
      } else {
        $row.find('.amount').text(lineTotal > 0 ? '¥' + lineTotal.toLocaleString() : '');
      }
    });

    $('#subtotal').text('¥' + subtotal.toLocaleString());
    $('#tax-total').text('¥' + taxTotal.toLocaleString());
    $('#grand-total').text('¥' + grandTotal.toLocaleString());
  };

  // 入力イベント監視（数量、単価、税率、税対象外）
  $(document).on('input change', 
    'input[name$="quantity"], input[name$="unit_price"], select[name$="tax_rate"], input[name$="is_tax_exempt"], input[name$="DELETE"]', 
    function() {
      recalcTotals();
  });

  // 商品マスタ選択時
  $(document).on('change', 'select[name$="-product"]', function() {
    var productId = $(this).val();
    if (!productId) return;

    var $row = $(this).closest('tr');

    $.ajax({
      url: '/sales_order/product/info/',
      type: 'GET',
      data: { 'product_id': productId },
      dataType: 'json',
      success: function(data) {
        if (data.error) {
          console.warn(data.error);
          return;
        }

        // 単位フィールドに反映
        $row.find('.unit-cell').text(data.unit);

        // 請求単価フィールドに反映
        $row.find('input[name$="-billing_unit_price"]').val(data.unit_price);
      },
      error: function(xhr, status, error) {
        console.error('商品情報取得エラー:', error);
      }
    });
  });

  // 取引先選択時
  $(document).on('change', '#id_partner', function() {
    var partnerId = $(this).val();
    if (!partnerId) {
      $('#partner-info').html('取引先を選択すると情報が表示されます');
      return;
    }

    $.ajax({
      url: '/sales_order/partner/info/',
      type: 'GET',
      data: { 'partner_id': partnerId },
      dataType: 'json',
      success: function(data) {
        if (data.error) {
          $('#partner-info').html('<span class="text-danger">' + data.error + '</span>');
          return;
        }

        // 取引先情報を整形して表示
        var html = (data.postal_code ? '〒' + data.postal_code + '<br>' : '')
                 + (data.address ? '住所: ' + data.address + '<br>' : '')
                 + (data.contact_name ? '担当者: ' + data.contact_name + '<br>' : '')
                 + (data.tel_number ? 'TEL: ' + data.tel_number + '<br>' : '')
                 + (data.email ? 'Email: ' + data.email : '');
        $('#partner-info').html(html);
      },
      error: function(xhr, status, error) {
        $('#partner-info').html('<span class="text-danger">情報取得に失敗しました</span>');
      }
    });
  });

  // =====================================================
  // 明細行追加ボタン処理
  // =====================================================
  $(document).on('click', '#add-row-btn', function () {
    const $detailBody = $('#detail-body');
    const $emptyTemplate = $('#empty-form-template');
    const $totalForms = $('#id_details-TOTAL_FORMS');
    const formCount = parseInt($totalForms.val(), 10);

    // templateの中身（<tr>付き）をDOM化
    const $newRow = $($emptyTemplate.html().replace(/__prefix__/g, formCount).trim());

    // tbody末尾に追加
    $detailBody.append($newRow);

    // Django formset 管理フォーム更新
    $totalForms.val(formCount + 1);

    // No.列を再採番
    $detailBody.find('tr').each(function (i) {
      $(this).find('td:first').text(i + 1);
    });

    // 追加した行を強調（視覚的フィードバック）
    $newRow.hide().fadeIn(200).addClass('table-success');
    setTimeout(() => $newRow.removeClass('table-success'), 800);

    // 自動フォーカス：商品選択フィールドへ
    const $productSelect = $newRow.find('select[name$="-product"]');
    if ($productSelect.length) {
      $productSelect.focus();        // 即座にフォーカス
      $productSelect.select2?.('open'); // select2等を使用していれば自動オープン
    }
  });

  // =====================================================
  // 行削除ボタン処理
  // =====================================================
  $(document).on('click', '.delete-row-btn', function () {
    const $row = $(this).closest('tr');
    const $detailBody = $('#detail-body');
    const $totalForms = $('input[id$="-TOTAL_FORMS"]');
    const prefix = $totalForms.attr('id').replace(/^id_/, '').replace(/-TOTAL_FORMS$/, '');

    // fadeOut後に削除
    $row.fadeOut(150, function () {
      $(this).remove();

      // 行番号を振り直し
      $detailBody.find('tr').each(function (i) {
        $(this).find('td:first').text(i + 1);
      });

      // TOTAL_FORMS の値を再設定（削除後の実行行数に合わせる）
      const currentCount = $detailBody.find('tr').length;
      $totalForms.val(currentCount);

      // ついでにフォームのname/idも整理しておく（__prefix__置換の整合性維持）
      $detailBody.find('tr').each(function (i) {
        $(this)
          .find(':input')
          .each(function () {
            const name = $(this).attr('name');
            const id = $(this).attr('id');
            if (name) $(this).attr('name', name.replace(new RegExp(`${prefix}-\\d+-`), `${prefix}-${i}-`));
            if (id) $(this).attr('id', id.replace(new RegExp(`id_${prefix}-\\d+-`), `id_${prefix}-${i}-`));
          });
      });

      recalcTotals();
    });
  });

});
