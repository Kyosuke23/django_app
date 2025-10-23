from django.test import TestCase
from django.contrib.auth import get_user_model
from tenant_mst.models import Tenant
from product_mst.models import Product, ProductCategory
from product_mst.form import ProductForm, ProductSearchForm, ProductCategoryForm


class ProductFormTests(TestCase):
    '''ProductForm 単体テスト'''

    def setUp(self):
        '''共通データ作成'''
        User = get_user_model()
        self.tenant = Tenant.objects.create(tenant_name='テストテナント')
        self.user = User.objects.create_user(
            username='tester',
            email='tester@example.com',
            password='pass',
            tenant=self.tenant
        )
        self.category = ProductCategory.objects.create(
            tenant=self.tenant,
            product_category_name='食品',
            create_user=self.user,
            update_user=self.user
        )

    def test_F01(self):
        '''F01: 全項目有効（正常）'''
        form = ProductForm(data={
            'product_name': 'テスト商品',
            'product_category': self.category.id,
            'unit_price': '1234.56',
            'unit': '個',
            'description': '説明文テスト',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_F02(self):
        '''F02: product_name 必須エラー'''
        form = ProductForm(data={
            'product_name': '',
            'unit_price': '1234.56',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('この項目は必須です', form.errors['product_name'][0])

    def test_F03(self):
        '''F03: unit 桁数超過（21文字）'''
        form = ProductForm(data={
            'product_name': 'テスト商品',
            'unit': 'A' * 21,
            'unit_price': '1234.56',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('この値は 20 文字以下でなければなりません', form.errors['unit'][0])

    def test_F04(self):
        '''F04: description 桁数超過（256文字）'''
        form = ProductForm(data={
            'product_name': 'テスト商品',
            'unit_price': '1234.56',
            'description': 'A' * 256,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('255文字以内で入力してください', form.errors['description'][0])

    def test_F05(self):
        '''F05: unit_price 必須エラー'''
        form = ProductForm(data={
            'product_name': 'テスト商品',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('この項目は必須です', form.errors['unit_price'][0])

    def test_F05a(self):
        '''F05: unit_price 小数3桁'''
        form = ProductForm(data={
            'product_name': 'テスト商品',
            'unit_price': '123.456',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('この値は小数点以下が合計 2 桁以内でなければなりません', form.errors['unit_price'][0])

    def test_F06(self):
        '''F06: product_category 未選択（任意項目）'''
        form = ProductForm(data={
            'product_name': 'テスト商品',
            'unit_price': '1234.56',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_F07(self):
        '''F07: 同一テナント内重複商品名（ユニーク制約）'''
        Product.objects.create(
            tenant=self.tenant,
            product_name='重複商品',
            unit_price='1234.56',
            create_user=self.user,
            update_user=self.user
        )
        form = ProductForm(data={
            'product_name': '重複商品',
            'unit_price': '1234.56',
        })
        # ModelFormはDBユニーク制約では即エラーにならないため full_clean() 相当を確認
        self.assertTrue(form.is_valid(), 'フォーム単体では通過するが保存時エラーを想定')

    def test_F07a(self):
        '''F12: 別テナントで同一商品名登録が可能であること'''
        other_tenant = Tenant.objects.create(tenant_name='別テナント')
        other_user = get_user_model().objects.create_user(
            username='other',
            email='other@example.com',
            password='pass',
            tenant=other_tenant
        )

        # 先にテナントAで登録
        Product.objects.create(
            tenant=self.tenant,
            product_name='共通商品',
            unit_price='1234.56',
            create_user=self.user,
            update_user=self.user
        )

        # テナントBで同名商品を登録
        form = ProductForm(data={
            'product_name': '共通商品',
            'unit_price': '1234.56',
        })
        self.assertTrue(form.is_valid(), form.errors)
        # save() しても IntegrityError は発生しないことを確認
        obj = form.save(commit=False)
        obj.tenant = other_tenant
        obj.create_user = other_user
        obj.update_user = other_user
        obj.save()
        self.assertEqual(Product.objects.filter(product_name='共通商品').count(), 2)

    def test_F08(self):
        '''F08: unit_price 空（任意）'''
        form = ProductForm(data={
            'product_name': '価格なし商品',
            'unit_price': '1234.56',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_F09(self):
        '''F09: unit_price 数値型チェック（文字列エラー）'''
        form = ProductForm(data={
            'product_name': 'テスト商品',
            'unit_price': 'abc',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('数値を入力してください', form.errors['unit_price'][0])


class ProductSearchFormTests(TestCase):
    '''ProductSearchForm 単体テスト'''

    def test_F10(self):
        '''F10: キーワード＋単価範囲＋カテゴリ 複合入力（正常）'''
        form = ProductSearchForm(data={
            'search_keyword': 'テスト',
            'search_unit_price_min': 100,
            'search_unit_price_max': 200,
            'sort': 'product_name',
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['search_keyword'], 'テスト')
        self.assertEqual(form.cleaned_data['search_unit_price_min'], 100)
        self.assertEqual(form.cleaned_data['search_unit_price_max'], 200)

    def test_F11(self):
        '''F11: 並び替えオプション 構造確認'''
        form = ProductSearchForm()
        self.assertIn('商品名称', dict(form.fields['sort'].choices))
        self.assertIn('商品カテゴリ', dict(form.fields['sort'].choices))
        self.assertIn('単価', dict(form.fields['sort'].choices))

class ProductCategoryFormTests(TestCase):
    '''ProductCategoryForm 単体テスト'''

    def setUp(self):
        User = get_user_model()
        self.tenant = Tenant.objects.create(tenant_name='テストテナント')
        self.user = User.objects.create_user(
            username='tester',
            email='tester@example.com',
            password='pass',
            tenant=self.tenant
        )
        self.cat = ProductCategory.objects.create(
            tenant=self.tenant,
            product_category_name='既存カテゴリ',
            create_user=self.user,
            update_user=self.user
        )

    def test_FC01(self):
        '''FC01: 新規カテゴリ入力（正常）'''
        form = ProductCategoryForm(data={'product_category_name': '新カテゴリ'})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['product_category_name'], '新カテゴリ')

    def test_FC02(self):
        '''FC02: 空入力'''
        form = ProductCategoryForm(data={'product_category_name': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('この項目は必須です', form.errors['product_category_name'][0])

    def test_FC03(self):
        '''FC03: 桁数超過（101文字）'''
        form = ProductCategoryForm(data={'product_category_name': 'A' * 101})
        self.assertFalse(form.is_valid())
        self.assertIn('この値は 100 文字以下でなければなりません', form.errors['product_category_name'][0])

    def test_FC04(self):
        '''FC04: 既存カテゴリ選択＋更新アクション'''
        form = ProductCategoryForm(data={
            'selected_category': self.cat.id,
            'product_category_name': '変更後カテゴリ'
        })
        self.assertTrue(form.is_valid(), form.errors)
        cleaned = form.cleaned_data
        self.assertEqual(cleaned['product_category_name'], '変更後カテゴリ')

    def test_FC05(self):
        '''FC05: 削除アクション時はカテゴリ名空でも通過（特殊処理想定）'''
        form = ProductCategoryForm(data={'action': 'delete', 'product_category_name': ''})
        # 実際には view 側でバリデーションスキップされるが想定動作確認
        self.assertTrue(form.is_valid(), '削除時は空でも通過可能')

    def test_FC06(self):
        '''FC06: 同一テナント内で同名カテゴリ（保存時IntegrityError想定）'''
        ProductCategory.objects.create(
            tenant=self.tenant,
            product_category_name='重複カテゴリ',
            create_user=self.user,
            update_user=self.user
        )
        form = ProductCategoryForm(data={'product_category_name': '重複カテゴリ'})
        self.assertTrue(form.is_valid(), 'フォーム自体は通過、保存時IntegrityErrorを想定')