$(function () {
    // =====================================================
    // エクスポートボタン
    // =====================================================
    $('.export-btn').on('click', function () {
        const url = $(this).data('action');
        if (url) window.location.href = url;
    });

    // =====================================================
    // CRUD処理
    // =====================================================
    $(document).on('click', '#editForm button[type=submit]', function (e) {
        e.preventDefault();

        const form = $('#editForm');
        const actionType = $(this).data('action');
        const saveUrl = form.data('save-url');
        const deleteUrl = form.data('delete-url');
        const csrf = form.find('input[name=csrfmiddlewaretoken]').val();
        const manager_comment = $('#id_header-manager_comment').val();

        // ----------------------------------------------------------
        // 削除処理
        // --------------------------------------------------------
        if (actionType === 'delete') {
            if (!confirm('本当に削除しますか？')) {
            return;
            }
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
            return;
        }

        // サーバに送信するデータの取得
        const formData = form.serializeArray();
        formData.push({ name: 'action_type', value: actionType });
        formData.push({ name: 'manager_comment', value: manager_comment });

        // ----------------------------------------------------------
        // 帳票の発行処理（社内）
        // ----------------------------------------------------------
        if (actionType === 'OUTPUT_QUOTATION_IN' || actionType === 'OUTPUT_ORDER_IN') {
            const orderId = form.data('order-id');
            $.ajax({
                url: form.attr('action'),
                type: 'POST',
                data: formData,
                success: function (response) {
                    window.open(`/sales_order/${orderId}/order_sheet/`, '_blank');
                },
                error: function (xhr) {
                    alert('注文書の取得に失敗しました。');
                    console.error(xhr.responseText);
                }
            });
            return;
        }

        // ----------------------------------------------------------
        // 登録・更新処理
        // -------------------------------------------------------
        $.ajax({
            url: saveUrl,
            type: 'POST',
            data: $.param(formData),
            success: function (response) {
                if (response.success) {
                    // success時に html があれば → モーダル再描画（閉じない）
                    if (response.html) {
                        $("#modalBody").html(response.html);
                    } else {
                        // html がなければ → 通常の更新完了（モーダル閉じるなど）
                        $("#modal").modal("hide");
                        location.reload();
                    }
                } else if (response.html) {
                    // バリデーションエラーなど: モーダル内容更新
                    $("#modalBody").html(response.html);
                } else {
                    alert("更新に失敗しました");
                }
                },
                error: function () {
                alert("サーバーエラーが発生しました");
            }
        });
    });

    // =====================================================
    // 消費税率・金額再計算
    // =====================================================
    const recalcAmount = function (row) {
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
    };

    $(document).on('change', 'select[name$="tax_rate"]', function () {
        recalcAmount($(this).closest('tr'));
    });

    $(document).on('input', 'input[name$="quantity"], input[name$="unit_price"]', function () {
        recalcAmount($(this).closest('tr'));
    });

    $(document).on('change', 'input[name$="is_tax_exempt"]', function () {
        recalcAmount($(this).closest('tr'));
    });

    // =====================================================
    // 合計金額再計算
    // =====================================================
    const recalcTotals = function () {
        let subtotal = 0;
        let taxTotal = 0;
        let grandTotal = 0;

        $('table tbody tr').each(function () {
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

            if (!isDeleted) {
                subtotal += lineSubtotal;
                taxTotal += lineTax;
                grandTotal += lineTotal;
            }

            if (isDeleted && !hasProduct) {
                $row.find('.amount').text('');
            } else {
                $row.find('.amount').text(lineTotal > 0 ? '¥' + lineTotal.toLocaleString() : '');
            }
        });

        $('#subtotal').text('¥' + subtotal.toLocaleString());
        $('#tax-total').text('¥' + taxTotal.toLocaleString());
        $('#grand-total').text('¥' + grandTotal.toLocaleString());
    };

    // =====================================================
    // 数量など変更時の単価反映
    // =====================================================
    $(document).on(
        'input change',
        'input[name$="quantity"], input[name$="unit_price"], select[name$="tax_rate"], input[name$="is_tax_exempt"], input[name$="DELETE"]',
        function () {
            recalcTotals();
        }
    );

    // =====================================================
    // 商品選択時の単価反映
    // =====================================================
    $(document).on('change', 'select[name$="-product"]', function () {
        var productId = $(this).val();
        if (!productId) return;

        var $row = $(this).closest('tr');

        $.ajax({
            url: '/sales_order/product/info/',
            type: 'GET',
            data: { product_id: productId },
            dataType: 'json',
            success: function (data) {
                if (data.error) {
                    console.warn(data.error);
                    return;
                }

                $row.find('.unit-cell').text(data.unit);
                $row.find('input[name$="-billing_unit_price"]').val(data.unit_price);
            },
            error: function (xhr, status, error) {
                console.error('商品情報取得エラー:', error);
            }
        });
    });

    // =====================================================
    // 取引先情報の動的表示
    // =====================================================
    $(document).on('change', '#id_header-partner', function () {
        var partnerId = $(this).val();
        if (!partnerId) {
            $('#partner-info').html('取引先を選択すると情報が表示されます');
            return;
        }

        $.ajax({
            url: '/sales_order/partner/info/',
            type: 'GET',
            data: { partner_id: partnerId },
            dataType: 'json',
            success: function (data) {
                if (data.error) {
                    $('#partner-info').html('<span class="text-danger">' + data.error + '</span>');
                    return;
                }

                var html = (data.postal_code ? '〒' + data.postal_code + '<br>' : '')
                    + (data.address ? '住所: ' + data.address + '<br>' : '')
                    + (data.contact_name ? '担当者: ' + data.contact_name + '<br>' : '')
                    + (data.tel_number ? 'TEL: ' + data.tel_number + '<br>' : '')
                    + (data.email ? 'Email: ' + data.email : '');
                $('#partner-info').html(html);
            },
            error: function () {
                $('#partner-info').html('<span class="text-danger">情報取得に失敗しました</span>');
            }
        });
    });

    // =====================================================
    // 明細行追加
    // =====================================================
    $(document).on('click', '#add-row-btn', function () {
        const $detailBody = $('#detail-body');
        const $emptyTemplate = $('#empty-form-template');
        const $totalForms = $('#id_details-TOTAL_FORMS');
        const formCount = parseInt($totalForms.val(), 10);

        const $newRow = $($emptyTemplate.html().replace(/__prefix__/g, formCount).trim());
        $detailBody.append($newRow);
        $totalForms.val(formCount + 1);

        $detailBody.find('tr').each(function (i) {
            $(this).find('td:first').text(i + 1);
        });

        $newRow.hide().fadeIn(200).addClass('table-success');
        setTimeout(() => $newRow.removeClass('table-success'), 800);

        const $productSelect = $newRow.find('select[name$="-product"]');
        if ($productSelect.length) {
            $productSelect.focus();
            $productSelect.select2?.('open');
        }
    });

    // =====================================================
    // 明細行削除
    // =====================================================
    $(document).on('click', '.delete-row-btn', function () {
        const $row = $(this).closest('tr');
        const $detailBody = $('#detail-body');
        const $totalForms = $('input[id$="-TOTAL_FORMS"]');
        const prefix = $totalForms.attr('id').replace(/^id_/, '').replace(/-TOTAL_FORMS$/, '');

        $row.fadeOut(150, function () {
            $(this).remove();

            $detailBody.find('tr').each(function (i) {
                $(this).find('td:first').text(i + 1);
            });

            const currentCount = $detailBody.find('tr').length;
            $totalForms.val(currentCount);

            $detailBody.find('tr').each(function (i) {
                $(this).find(':input').each(function () {
                    const name = $(this).attr('name');
                    const id = $(this).attr('id');
                    if (name) $(this).attr('name', name.replace(new RegExp(`${prefix}-\\d+-`), `${prefix}-${i}-`));
                    if (id) $(this).attr('id', id.replace(new RegExp(`id_${prefix}-\\d+-`), `id_${prefix}-${i}-`));
                });
            });

            recalcTotals();
        });
    });

    // =====================================================
    // モーダルフォーム共通処理
    // =====================================================
    $(document).modal_form('#salesOrderModal', function($modal) {
        // 適用先フォームの取得
        const partners  = $modal.find('#id_header-partner');
        const ref_users  = $modal.find('#id_header-reference_users');
        const ref_groups = $modal.find('#id_header-reference_groups');
        const products  = $modal.find('select[id^="id_details-"][id$="-product"]')

        // Select2のオプション設定
        const opt = {
            width: '100%',
            allowClear: true,
            tags: false,
            dropdownParent: $modal,
            placeholder: '選択してください',
        };

        // Select2を適用
        partners.select2({ ...opt, placeholder: '取引先を選択...' });
        ref_users.select2({ ...opt, placeholder: 'ユーザーを選択...' });
        ref_groups.select2({ ...opt, placeholder: 'グループを選択...' });
        products.select2({ ...opt, placeholder: '商品を選択...' });
    });


    // =====================================================
    // 顧客向けページ専用の処理
    // =====================================================
    $(document).on('click', '#confirmForm button[data-action]', function (e) {

        const form = $('#confirmForm');
        const formData = form.serializeArray();
        const actionType = $(this).data('action');
        const comment = $('#id_header-customer_comment').val();
        formData.push({ name: 'action_type', value: actionType });
        formData.push({ name: 'customer_comment', value: comment });

        // サーバ処理用のパラメータを準備
        $('#action_type').val(actionType);
        $('#customer_comment').val(comment);

        // 見積書のPDF出力
        if (actionType === 'OUTPUT_QUOTATION_OUT' || actionType === 'OUTPUT_ORDER_OUT') {
            e.preventDefault(); // 見積書発行の時だけsubmit中止
            const orderId = $('#order_id').val();
            let template_name = 'quotation_sheet';
            if (actionType === 'OUTPUT_ORDER_OUT') template_name = 'order_sheet';
            $.ajax({
                url: form.attr('action'),
                type: 'POST',
                data: formData,
                success: function (response) {
                    window.open(`/sales_order/${orderId}/${template_name}/`, '_blank');
                },
                error: function (xhr) {
                    alert('見積書の取得に失敗しました。');
                    console.error(xhr.responseText);
                }
            });
            return;
        }
    });
});
