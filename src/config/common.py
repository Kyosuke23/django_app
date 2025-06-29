import csv
from django.http import HttpResponse
import re
from django.core.paginator import Page
from openpyxl import Workbook
from datetime import datetime

class Common:
    # 共通データカラムリスト
    COMMON_DATA_COLUMNS = ['create_user', 'created_at', 'update_user', 'updated_at']
    
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
    def get_ip_address(cls, request):
        # 'HTTP_X_FORWARDED_FOR'ヘッダを参照して転送経路のIPアドレスを取得する。
        forwarded_addresses = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded_addresses:
            # 'HTTP_X_FORWARDED_FOR'ヘッダがある場合: 転送経路の先頭要素を取得する。
            client_addr = forwarded_addresses.split(',')[0]
        else:
            # 'HTTP_X_FORWARDED_FOR'ヘッダがない場合: 直接接続なので'REMOTE_ADDR'ヘッダを参照する。
            client_addr = request.META.get('REMOTE_ADDR')
        return client_addr
    
    @classmethod
    def get_common_columns(cls, rec):
        """
        出力データの共通カラム部分を取得
        """
        create_user = ''
        if rec.create_user:
            create_user = rec.create_user.username
        created_at = ''
        if rec.created_at:
            created_at = rec.created_at.replace(tzinfo=None)
        update_user = ''
        if rec.update_user:
            update_user = rec.update_user.username
        updated_at = ''
        if rec.updated_at:
            updated_at = rec.updated_at.replace(tzinfo=None)
        # datetime型はtimezoneを削除（Excel出力時にエラーとなるため）
        return [
            create_user
            , created_at
            , update_user
            , updated_at
        ]