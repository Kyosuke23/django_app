$(function() {
    /**
	 * フラッシュメッセージ表示処理
	 * @param {*} options 
	 * @returns フラッシュメッセージ
	 */
    $.fn.flash_message = function(options) {
        //デフォルト値
        options = $.extend({
            text: '完了しました',
            time: 3000,
            how: 'before',
            class_name: ''
        }, options);

        return $(this).each(function() {
            //指定したセレクタを探して取得
            if ($(this).find('.flash_message').get(0)) {
                $(this).find('.flash_message').remove();
            }

            var message = $('<span />', {
                'class': 'flash_message ' + options.class_name,
                text: options.text
            //フェードイン表示
            });

            $(this)[options.how](message).addClass('show');
            //delayさせてからフェードアウト
            message.delay(options.time).queue(function(){
                $(this).parents('#flash-msg-area').removeClass('show');
            });
        });
    };

});