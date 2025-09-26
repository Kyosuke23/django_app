import csv
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from django.db import transaction, IntegrityError
from datetime import datetime
from django.http import HttpResponse
from django.db import models
from django.contrib.auth import get_user_model
import openpyxl


class ExcelExportBaseView(View):
    model_class = None  # 出力対象のモデルクラス
    filename_prefix = 'export'  # サブクラスで指定
    headers: list[str] = []  # 出力ヘッダ定義

    def get(self, request, *args, **kwargs):
        # --- ファイル名設定 ---
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f'{self.filename_prefix}_{timestamp}.xlsx'

        # --- データ取得 ---
        data = self.get_queryset(request)

        # --- Workbook 作成 ---
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'data'

        # --- ヘッダ書き込み ---
        for col, header in enumerate(self.headers, start=1):
            ws.cell(row=1, column=col, value=header)

        # --- データ書き込み ---
        for row_idx, rec in enumerate(data, start=2):
            values = self.row(rec)
            for col_idx, val in enumerate(values, start=1):
                ws.cell(row=row_idx, column=col_idx, value=val)

        # --- レスポンス作成 ---
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f"attachment; filename*=UTF-8''{file_name}"

        wb.save(response)
        return response

    def get_queryset(self, request):
        return self.model_class.objects.all()

    def row(self, rec):
        raise NotImplementedError('サブクラスで row() を実装してください')


class CSVExportBaseView(View):
    model_class = None  # 出力対象のモデルクラス
    filename_prefix = 'export'  # サブクラスで指定
    headers: list[str] = []  # 出力ヘッダ定義

    def get(self, request, *args, **kwargs):
        # --- ファイル名設定 ---
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f'{self.filename_prefix}_{timestamp}.csv'

        # --- データ取得 ---
        data = self.get_queryset(request)

        # --- レスポンス準備 ---
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f"attachment; filename*=UTF-8''{file_name}"

        writer = csv.writer(response)

        # --- ヘッダ出力 ---
        writer.writerow(self.headers)

        # --- データ出力 ---
        for rec in data:
            writer.writerow(self.row(rec))

        return response

    def get_queryset(self, request):
        '''サブクラスで必要に応じてフィルタリングを行う'''
        return self.model_class.objects.all()

    def row(self, rec):
        '''サブクラスで1行分のリストを返す'''
        raise NotImplementedError('サブクラスで row() を実装してください')
    

class CSVImportBaseView(View):
    '''
    CSV Import機能の基底クラス
    全データが正常と判断されてからトランザクション確定。エラー存在時はロールバック。
    '''
    expected_headers: list[str] = []  # サブクラスで設定
    model_class = None  # bulk_create対象のモデル
    unique_field = None  # 重複チェックに使うフィールド名

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'error': 'ファイルが選択されていません'}, status=400)

        # --- decode ---
        file_data = file.read()
        try:
            decoded_data = file_data.decode('utf-8-sig')
        except UnicodeDecodeError:
            decoded_data = file_data.decode('cp932')

        decoded_file = decoded_data.splitlines()
        reader = csv.DictReader(decoded_file)

        # --- ヘッダチェック ---
        if reader.fieldnames is None or any(h not in reader.fieldnames for h in self.expected_headers):
            return JsonResponse({
                'error': 'CSVヘッダが正しくありません',
                'details': f'期待: {self.expected_headers}, 実際: {reader.fieldnames}'
            }, status=400)

        # --- バリデーション ---
        existing = set(self.model_class.objects.values_list(self.unique_field, flat=True))
        objects_to_create = []
        errors = []

        for idx, row in enumerate(reader, start=2):  # 2行目以降がデータ
            obj, err = self.validate_row(row=row, idx=idx, existing=existing, request=request)
            if err:
                errors.append(err)
                continue
            if obj:
                objects_to_create.append(obj)

        if errors:
            return JsonResponse({'error': 'CSVに問題があります', 'details': errors}, status=400)

        # --- bulk insert ---
        try:
            with transaction.atomic():
                self.model_class.objects.bulk_create(objects_to_create)
        except IntegrityError as e:
            return JsonResponse({
                'error': '登録中にDBエラーが発生しました',
                'details': [str(e)]
            }, status=500)

        return JsonResponse({'message': f'{len(objects_to_create)} 件をインポートしました'})

    def validate_row(self, row: dict, idx: int, existing: set, request):
        '''
        サブクラスで必ず実装すること
        戻り値: (modelインスタンス or None, エラーメッセージ or None)
        '''
        raise NotImplementedError

class BaseModel(models.Model):
    """
    共通基底クラス
    - 論理削除
    - 作成日時 / 更新日時
    - 作成者 / 更新者
    """

    tenant = models.ForeignKey('tenant_mst.Tenant', on_delete=models.CASCADE, related_name="%(class)ss", null=False, blank=False, verbose_name='所属テナント')
    is_deleted = models.BooleanField(default=False, verbose_name='削除フラグ')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    create_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_creator",
        verbose_name='作成者'
    )
    update_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_updater",
        verbose_name='更新者'
    )

    class Meta:
        abstract = True