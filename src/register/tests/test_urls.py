from django.test import TestCase
from django.urls import reverse, resolve
from ..views import *

class TestUrlsClass(TestCase):
    def test_urls_01_register_user_index(self):
        '''
        ユーザーマスタの初期表示テスト
        '''
        url = reverse('register:register_user_index')
        self.assertEqual(resolve(url).func.view_class, RegisterUserList)

    def test_urls_02_register_user_create(self):
        '''
        ユーザー登録画面の表示テスト
        '''
        url = reverse('register:register_user_create')
        self.assertEqual(resolve(url).func.view_class, RegisterUserCreate)

    def test_urls_03_register_user_update(self):
        '''
        ユーザー編集画面の表示テスト
        '''
        url = reverse('register:register_user_update', kwargs=dict(pk='1'))
        self.assertEqual(resolve(url).func.view_class, RegisterUserUpdate)

    def test_urls_04_register_user_delete(self):
        '''
        ユーザー削除画面の表示テスト
        '''
        url = reverse('register:register_user_delete', kwargs=dict(pk='1'))
        self.assertEqual(resolve(url).func.view_class, RegisterUserDelete)