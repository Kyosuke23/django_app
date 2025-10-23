from django.test import TestCase
from decimal import Decimal
from product_mst.form import ProductForm, ProductSearchForm, ProductCategoryForm
from product_mst.models import Product, ProductCategory
from register.models import CustomUser
from tenant_mst.models import Tenant


class ProductFormTests(TestCase):

    def setUp(self):
        self.tenant1 = Tenant.objects.create(tenant_name="TenantA")
        self.tenant2 = Tenant.objects.create(tenant_name="TenantB")
        self.user1 = CustomUser.objects.create_user(username="user1", email="user1@example.com", password="pass", tenant=self.tenant1)
        self.user2 = CustomUser.objects.create_user(username="user2", email="user2@example.com", password="pass", tenant=self.tenant2)

        self.category = ProductCategory.objects.create(
            tenant=self.tenant1,
            product_category_name="食品",
            create_user=self.user1,
            update_user=self.user1,
        )
        self.category2 = ProductCategory.objects.create(
            tenant=self.tenant2,
            product_category_name="飲料（T2）",
            create_user=self.user2,
            update_user=self.user2,
        )

        Product.objects.create(
            tenant=self.tenant1,
            product_name="重複商品",
            product_category=self.category,
            unit_price=Decimal("100.00"),
            unit="個",
            description="説明文",
            create_user=self.user1,
            update_user=self.user1,
        )

    # 1-1-1-1
    def test_1_1_1_1(self):
        """全項目正常"""
        form = ProductForm(data={
            'product_name': '正常商品',
            'product_category': self.category.id,
            'unit_price': '100.00',
            'unit': '個',
            'description': '説明',
        }, user=self.user1)
        self.assertTrue(form.is_valid())

    # 1-2-1-1
    def test_1_2_1_1(self):
        """別テナント内重複"""
        form = ProductForm(data={
            'product_name': '重複商品',
            'product_category': self.category2.id,
            'unit_price': '100.00',
            'unit': '個',
            'description': '説明',
        }, user=self.user2)
        self.assertTrue(form.is_valid())

    # 1-2-2-1
    def test_1_2_2_1(self):
        """必須エラー"""
        form = ProductForm(data={
            'product_name': '',
            'product_category': self.category.id,
            'unit_price': '100.00',
            'unit': '個',
            'description': '説明',
        }, user=self.user1)
        self.assertFalse(form.is_valid())
        self.assertIn("この項目は必須です。", form.errors['product_name'])

    # 1-2-2-2
    def test_1_2_2_2(self):
        """文字数超過（101文字）"""
        long_name = 'あ' * 101
        form = ProductForm(data={
            'product_name': long_name,
            'product_category': self.category.id,
            'unit_price': '100.00',
            'unit': '個',
            'description': '説明',
        }, user=self.user1)
        self.assertFalse(form.is_valid())
        expected = f"この値は 100 文字以下でなければなりません( {len(long_name)} 文字になっています)。"
        self.assertIn(expected, form.errors['product_name'][0])

    # 1-2-2-3
    def test_1_2_2_3(self):
        """同一テナント内重複"""
        form = ProductForm(data={
            'product_name': '重複商品',
            'unit_price': '1234.56',
        })
        # ModelFormはDBユニーク制約では即エラーにならないため full_clean() 相当を確認
        self.assertTrue(form.is_valid(), 'フォーム単体では通過するが保存時エラーを想定')

    # 1-3-1-1
    def test_1_3_1_1(self):
        """カテゴリ未選択"""
        form = ProductForm(data={
            'product_name': 'カテゴリなし',
            'product_category': '',
            'unit_price': '100.00',
            'unit': '個',
            'description': '説明',
        }, user=self.user1)
        self.assertTrue(form.is_valid())

    # 1-4-1-1
    def test_1_4_1_1(self):
        """unit_price必須エラー"""
        form = ProductForm(data={
            'product_name': '単価未入力',
            'product_category': self.category.id,
            'unit_price': '',
            'unit': '個',
            'description': '説明',
        }, user=self.user1)
        self.assertFalse(form.is_valid())
        self.assertIn("この項目は必須です。", form.errors['unit_price'][0])

    # 1-4-1-2
    def test_1_4_1_2(self):
        """unit_price数値型以外"""
        form = ProductForm(data={
            'product_name': '単価文字',
            'product_category': self.category.id,
            'unit_price': 'number',
            'unit': '個',
            'description': '説明',
        }, user=self.user1)
        self.assertFalse(form.is_valid())
        self.assertIn("数値を入力してください。", form.errors['unit_price'][0])

    # 1-4-1-3
    def test_1_4_1_3(self):
        """unit_price少数桁不正"""
        form = ProductForm(data={
            'product_name': '単価桁不正',
            'product_category': self.category.id,
            'unit_price': '123.456',
            'unit': '個',
            'description': '説明',
        }, user=self.user1)
        self.assertFalse(form.is_valid())
        self.assertIn("この値は小数点以下が合計 2 桁以内でなければなりません。", form.errors['unit_price'][0])

    # 1-8-1-1
    def test_1_8_1_1(self):
        """unit文字数超過"""
        long_unit = 'あ' * 21
        form = ProductForm(data={
            'product_name': '単位長い',
            'product_category': self.category.id,
            'unit_price': '100.00',
            'unit': long_unit,
            'description': '説明',
        }, user=self.user1)
        self.assertFalse(form.is_valid())
        expected = f"この値は 20 文字以下でなければなりません( {len(long_unit)} 文字になっています)。"
        self.assertIn(expected, form.errors['unit'][0])

    # 1-9-1-1
    def test_1_9_1_1(self):
        """description文字数超過"""
        long_desc = 'あ' * 256
        form = ProductForm(data={
            'product_name': '説明長い',
            'product_category': self.category.id,
            'unit_price': '100.00',
            'unit': '個',
            'description': long_desc,
        }, user=self.user1)
        self.assertFalse(form.is_valid())
        expected = f"この値は 255 文字以下でなければなりません( {len(long_desc)} 文字になっています)。"
        self.assertIn(expected, form.errors['description'][0])


class ProductSearchFormTests(TestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(tenant_name="TenantC")
        self.category = ProductCategory.objects.create(
            tenant=self.tenant,
            product_category_name="飲料",
            create_user=None,
            update_user=None,
        )

    # 2-1-1-1
    def test_2_1_1_1(self):
        """全項目正常"""
        form = ProductSearchForm(data={
            'search_keyword': 'keyword',
            'search_product_name': '商品A',
            'search_category': self.category.id,
            'search_unit': '個',
            'search_unit_price_min': '100',
            'search_unit_price_max': '200',
            'sort': 'product_name',
        })
        self.assertTrue(form.is_valid())

    # 2-2-1-1
    def test_2_2_1_1(self):
        """product_name文字数超過"""
        long_name = 'あ' * 101
        form = ProductSearchForm(data={'search_product_name': long_name})
        self.assertFalse(form.is_valid())
        expected = f"この値は 100 文字以下でなければなりません( {len(long_name)} 文字になっています)。"
        self.assertIn(expected, form.errors['search_product_name'][0])

    # 2-3-1-1
    def test_2_3_1_1(self):
        """カテゴリ未選択"""
        form = ProductSearchForm(data={'search_category': ''})
        self.assertTrue(form.is_valid())

    # 2-4-1-1
    def test_2_4_1_1(self):
        """unit_price（下限）数値型以外"""
        form = ProductSearchForm(data={'search_unit_price_min': 'number'})
        self.assertFalse(form.is_valid())
        self.assertIn("数値を入力してください。", form.errors['search_unit_price_min'][0])

    # 2-5-1-1
    def test_2_5_1_1(self):
        """unit_price（下限）少数桁不正"""
        form = ProductSearchForm(data={'search_unit_price_min': '123.456'})
        self.assertFalse(form.is_valid())
        self.assertIn("この値は小数点以下が合計 2 桁以内でなければなりません。", form.errors['search_unit_price_min'][0])

    # 2-6-1-1
    def test_2_6_1_1(self):
        """unit_price（上限）数値型以外"""
        form = ProductSearchForm(data={'search_unit_price_max': 'number'})
        self.assertFalse(form.is_valid())
        self.assertIn("数値を入力してください。", form.errors['search_unit_price_max'][0])

    # 2-7-1-1
    def test_2_7_1_1(self):
        """unit_price（上限）少数桁不正"""
        form = ProductSearchForm(data={'search_unit_price_max': '123.456'})
        self.assertFalse(form.is_valid())
        self.assertIn("この値は小数点以下が合計 2 桁以内でなければなりません。", form.errors['search_unit_price_max'][0])

    # 2-8-1-1
    def test_2_8_1_1(self):
        """unit文字数超過"""
        long_unit = 'あ' * 21
        form = ProductSearchForm(data={'search_unit': long_unit})
        self.assertFalse(form.is_valid())
        expected = f"この値は 20 文字以下でなければなりません( {len(long_unit)} 文字になっています)。"
        self.assertIn(expected, form.errors['search_unit'][0])



class ProductCategoryFormTests(TestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(tenant_name="TenantD")
        self.category1 = ProductCategory.objects.create(
            tenant=self.tenant,
            product_category_name="既存カテゴリ",
            create_user=None,
            update_user=None
        )

    def test_3_1_1_1(self):
        """新規カテゴリ登録"""
        form = ProductCategoryForm(data={'product_category_name': '新カテゴリ'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['product_category_name'], '新カテゴリ')

    def test_3_1_1_2(self):
        """空入力（削除時用）"""
        form = ProductCategoryForm(data={'product_category_name': '', 'action': 'delete',})
        self.assertTrue(form.is_valid())

    def test_3_1_1_3(self):
        form = ProductCategoryForm(data={
            'selected_category': self.category1.id,
            'product_category_name': '変更後カテゴリ',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['product_category_name'], '変更後カテゴリ')

    def test_3_1_2_1(self):
        form = ProductCategoryForm(data={'product_category_name': ''})
        self.assertFalse(form.is_valid())
        self.assertIn("この項目は必須です。", form.errors['product_category_name'][0])

    def test_3_1_2_2(self):
        form = ProductCategoryForm(data={'product_category_name': 'A' * 101})
        self.assertFalse(form.is_valid())
        self.assertIn("この値は 100 文字以下でなければなりません( 101 文字になっています)。", form.errors['product_category_name'][0])

    def test_3_1_2_3(self):
        """テナント内重複名（フォームではエラーとならない想定）"""
        form = ProductCategoryForm(data={'product_category_name': '既存カテゴリ'})
        self.assertTrue(form.is_valid())