import csv
from django.http import HttpResponse
import re
from django.core.paginator import Page
from django.http import HttpResponse
from openpyxl import Workbook
from datetime import datetime

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
    
    @classmethod
    def export_excel(cls, model, data, file_name):
        """
        Excel出力用のレスポンスを作成する（全カラムを出力）
        """
        # Excelオブジェクト（ワークブック）を取得
        wb = Workbook()
        ws = wb.active
        # データモデルの全ての列名を取得
        col_nm_list = cls.get_models_field_name_all(model=model)
        # 列名をワークブックに適用
        ws.append(col_nm_list)
        # ワークブックにデータを追加
        for rec in data:
            # 全てのフィールド値を取得
            row = cls.get_models_field_value_all(model=rec)
            # フィールドの型がdatetimeの場合、timezoneを削除（Excel出力時にエラーとなるため）
            for i, v in enumerate(row):
                if type(v) is datetime:
                    row[i] = v.replace(tzinfo=None)
            # ワークブックにデータを追加
            ws.append(row)
        # 保存したワークブックをレスポンスに格納
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        wb.save(response)
        # 処理結果を返却
        return response
    
    @classmethod
    def export_csv(cls, model, data, file_name):
        """
        CSV出力用のレスポンスを作成する（全カラムを出力）
        """
        # CSV出力用のレスポンスを取得
        response = HttpResponse(content_type='text/csv; charset=Shift-JIS')
        response['Content-Disposition'] = 'attachment; filename*=UTF-8\'\'{}'.format(file_name)
        # ヘッダの書き込み
        writer = csv.writer(response)
        writer.writerow(cls.get_models_field_name_all(model=model))
        # データの書き込み
        for rec in data:
            writer.writerow(cls.get_models_field_value_all(model=rec))
        # 処理結果を返却
        return response
    
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