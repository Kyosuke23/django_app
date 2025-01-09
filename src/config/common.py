import re
from django.core.paginator import Page

class Common:
    @classmethod
    def set_pagination(cls, context, url_params):
        """
        ページング部品の値をコンテキストに設定
        """
        page: Page = context['page_obj']
        context['paginator_range'] = page.paginator.get_elided_page_range(
            page.number
            , on_each_side=1
            , on_ends=1
        )
        # ページングのパラメータを削除
        url_params = re.sub('\&page\=\d*', '', url_params)
        # URLパラメータを再設定
        context['query_str'] = url_params
        # 処理結果を返却
        return context