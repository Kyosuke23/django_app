'''
アクセス管理に関連する定数
'''

# アクセス種別
ACCESSTYPE_LOGIN = 'login'
ACCESSTYPE_LOGOUT = 'logout'
ACCESSTYPE_CHOICES = (
    ('', '')
    , (ACCESSTYPE_LOGIN, 'login')
    , (ACCESSTYPE_LOGOUT, 'logout')
)