from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from tenant_mst.models import Tenant
from product_mst.models import Product, ProductCategory
from django.utils import timezone
from django.db import IntegrityError
from decimal import Decimal


class ProductModelTests(TestCase):
    '''Productモデル単体テスト'''

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

    def create_product(self, **kwargs):
        '''共通フィールド付きProduct生成'''
        defaults = dict(
            tenant=self.tenant,
            create_user=self.user,
            update_user=self.user,
            product_name='テスト商品',
            unit_price=100,
        )
        defaults.update(kwargs)
        return Product(**defaults)

    # --------------------------
    # product_name
    # --------------------------
    def test_1_1_1_1(self):
        '''product_name 正常登録'''
        p = self.create_product(product_name='有効商品')
        p.full_clean()
        p.save()
        saved = Product.objects.get(pk=p.pk)
        self.assertEqual(saved.product_name, '有効商品')
        self.assertEqual(saved.unit_price, 100)
        self.assertEqual(saved.tenant, self.tenant)

    def test_1_1_1_2(self):
        '''product_name 桁数上限（100文字）'''
        p = self.create_product(product_name='A' * 100)
        p.full_clean()
        p.save()
        self.assertEqual(Product.objects.get(pk=p.pk).product_name, 'A' * 100)

    def test_1_1_1_3(self):
        '''M07: 異なるテナントで同名登録許可'''
        other_tenant = Tenant.objects.create(tenant_name='別テナント', email='other@example.com',)
        Product.objects.create(
            tenant=self.tenant,
            product_name='同名商品',
            unit_price=200,
            create_user=self.user,
            update_user=self.user
        )
        Product.objects.create(
            tenant=other_tenant,
            product_name='同名商品',
            unit_price=200,
            create_user=self.user,
            update_user=self.user
        )
        self.assertEqual(Product.objects.filter(product_name='同名商品').count(), 2)

    def test_1_1_2_1(self):
        '''product_name 必須エラー'''
        p = self.create_product(product_name='')
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_1_1_2_2(self):
        '''product_name 桁数超過（101文字）'''
        p = self.create_product(product_name='A' * 101)
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_1_1_2_3(self):
        '''同一テナント内の重複商品名（IntegrityError）'''
        Product.objects.create(
            tenant=self.tenant,
            product_name='重複商品',
            unit_price=200,
            create_user=self.user,
            update_user=self.user
        )
        with self.assertRaises(ValidationError):
            Product.objects.create(
                tenant=self.tenant,
                product_name='重複商品',
                unit_price=200,
                create_user=self.user,
                update_user=self.user
            )

    # --------------------------
    # product_category
    # --------------------------
    def test_2_1_1_1(self):
        '''product_category 正常登録（カテゴリ紐付け）'''
        p = self.create_product(product_category=self.category)
        p.full_clean()
        p.save()
        saved = Product.objects.get(pk=p.pk)
        self.assertEqual(saved.product_category, self.category)

    def test_2_1_1_2(self):
        '''product_category None許可'''
        p = self.create_product(product_category=None)
        p.full_clean()
        p.save()
        self.assertIsNone(Product.objects.get(pk=p.pk).product_category)

    def test_2_1_2_1(self):
        '''product_category 不正ID'''
        fake = ProductCategory(id=9999)
        p = self.create_product(product_category=fake)
        with self.assertRaises(ValidationError):
            p.full_clean()

    # --------------------------
    # unit
    # --------------------------
    def test_3_1_1_1(self):
        '''unit 正常登録'''
        p = self.create_product(unit='箱')
        p.full_clean()
        p.save()
        self.assertEqual(Product.objects.get(pk=p.pk).unit, '箱')

    def test_3_1_1_2(self):
        '''unit 桁数上限（20文字）'''
        p = self.create_product(unit='A' * 20)
        p.full_clean()
        p.save()
        self.assertEqual(Product.objects.get(pk=p.pk).unit, 'A' * 20)

    def test_3_1_2_1(self):
        '''unit 桁数超過（21文字）'''
        p = self.create_product(unit='A' * 21)
        with self.assertRaises(ValidationError):
            p.full_clean()

    # --------------------------
    # unit_price
    # --------------------------
    def test_4_1_1_1(self):
        '''unit_price 正常登録（小数2桁）'''
        p = self.create_product(unit_price=Decimal('1234.56'))
        p.full_clean()
        p.save()
        self.assertEqual(Product.objects.get(pk=p.pk).unit_price, Decimal('1234.56'))

    def test_4_1_2_1(self):
        '''unit_price 必須エラー'''
        p = self.create_product(unit_price=None)
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_4_1_2_2(self):
        '''unit_price 小数3桁（ValidationError）'''
        p = self.create_product(unit_price=123.456)
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_4_1_2_3(self):
        '''unit_price 数値型以外'''
        p = self.create_product(unit_price='number')
        with self.assertRaises(ValidationError):
            p.full_clean()

    # --------------------------
    # description
    # --------------------------
    def test_5_1_1_1(self):
        '''description 正常登録'''
        p = self.create_product(description='説明文テスト')
        p.full_clean()
        p.save()
        self.assertEqual(Product.objects.get(pk=p.pk).description, '説明文テスト')

    def test_5_1_1_2(self):
        '''description 桁数上限（255文字）'''
        p = self.create_product(description='A' * 255)
        p.full_clean()
        p.save()
        self.assertEqual(len(Product.objects.get(pk=p.pk).description), 255)

    def test_5_1_2_1(self):
        '''description 桁数超過（256文字）'''
        p = self.create_product(description='A' * 256)
        with self.assertRaises(ValidationError):
            p.full_clean()

    # --------------------------
    # save() & timestamp
    # --------------------------
    def test_6_1_1_1(self):
        '''save() により full_clean が実行される'''
        p = self.create_product(product_name='saveテスト')
        p.save()
        self.assertIsNotNone(p.pk)
        self.assertLessEqual(abs((p.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((p.updated_at - timezone.now()).total_seconds()), 5)


class ProductCategoryModelTests(TestCase):
    '''ProductCategoryモデル単体テスト'''

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

    def create_category(self, **kwargs):
        defaults = dict(
            tenant=self.tenant,
            product_category_name='食品',
            create_user=self.user,
            update_user=self.user
        )
        defaults.update(kwargs)
        return ProductCategory(**defaults)

    # --------------------------
    # 正常系
    # --------------------------
    def test_7_1_1_1(self):
        '''正常登録'''
        cat = self.create_category()
        cat.full_clean()
        cat.save()
        saved = ProductCategory.objects.get(pk=cat.pk)
        self.assertEqual(saved.product_category_name, '食品')
        self.assertEqual(saved.tenant, self.tenant)

    def test_7_1_1_2(self):
        '''C02: 桁数上限100文字'''
        cat = self.create_category(product_category_name='A' * 100)
        cat.full_clean()
        cat.save()
        self.assertEqual(ProductCategory.objects.get(pk=cat.pk).product_category_name, 'A' * 100)

    def test_7_1_1_3(self):
        '''同一テナント内でカテゴリ名重複時'''
        ProductCategory.objects.create(
            tenant=self.tenant,
            product_category_name='重複カテゴリ',
            create_user=self.user,
            update_user=self.user
        )
        with self.assertRaises(IntegrityError):
            ProductCategory.objects.create(
                tenant=self.tenant,
                product_category_name='重複カテゴリ',
                create_user=self.user,
                update_user=self.user
            )

    def test_7_1_2_1(self):
        '''C03: Null／空文字は許可されない'''
        cat = self.create_category(product_category_name='')
        with self.assertRaises(ValidationError):
            cat.full_clean()

    def test_7_1_2_2(self):
        '''C04: 桁数超過（101文字）'''
        cat = self.create_category(product_category_name='A' * 101)
        with self.assertRaises(ValidationError):
            cat.full_clean()

    def test_7_1_2_3(self):
        '''C06: 異なるテナントでは同名カテゴリ登録可能'''
        other_tenant = Tenant.objects.create(tenant_name='別テナント', email='other@example.com')
        ProductCategory.objects.create(
            tenant=self.tenant,
            product_category_name='共通カテゴリ',
            create_user=self.user,
            update_user=self.user
        )
        other_user = get_user_model().objects.create_user(
            username='other',
            email='other@example.com',
            password='pass',
            tenant=other_tenant
        )
        ProductCategory.objects.create(
            tenant=other_tenant,
            product_category_name='共通カテゴリ',
            create_user=other_user,
            update_user=other_user
        )
        self.assertEqual(ProductCategory.objects.filter(product_category_name='共通カテゴリ').count(), 2)
