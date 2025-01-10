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

    @classmethod
    def get_models_field_value_all(cls, model):
        """
        モデルのフィールド値をリストで取得
        """
        # モデルフィールドのメタ情報を取得
        fields = model._meta.get_fields()
        # 空の配列にモデルフィールドの名前を追加
        result = list()
        for i, v in enumerate(fields):
            if i > 0:
                result.append(v.value_from_object(model))
        # 処理結果を返却
        return result
    
    @classmethod
    def get_models_field_name_all(cls, model):
        """
        モデルのフィールド名をリストで取得
        """
        # モデルフィールドのメタ情報を取得
        fields = model._meta.get_fields()
        # 空の配列にモデルフィールドの名前を追加
        result = list()
        for i, v in enumerate(fields):
            if i > 0:
                result.append(v.name)
        # 処理結果を返却
        return result