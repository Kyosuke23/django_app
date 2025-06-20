"""
ユーザー登録に関連する定数
"""

# 性別
GENDER_MALE = '0'
GENDER_FEMALE = '1'
GENDER_OTHER = '2'
GENDER_CHOICES = (
    ('', '')
    , (GENDER_MALE, '男性')
    , (GENDER_FEMALE, '女性')
    , (GENDER_OTHER, 'その他')
)

# ユーザー権限
PRIVILEGE_SUPER = '0'
PRIVILEGE_NORMAL = '1'
PRIVILEGE_REFERENCE = '2'
PRIVILEGE_GUEST = '3'
PRIVILEGE_CHOICES = (
    (PRIVILEGE_SUPER, '特権')
    , (PRIVILEGE_NORMAL, '一般')
    , (PRIVILEGE_REFERENCE, '参照')
    , (PRIVILEGE_GUEST, 'ゲスト')
)

POSTAL_API_URL = 'https://zipcloud.ibsnet.co.jp/api/search'