"""
ユーザー登録に関連する定数
"""

# 性別
GENDER_MALE = '0'
GENDER_FEMALE = '1'
GENDER_OTHER = '2'
GENDER_CHOICES = (
    (GENDER_MALE, '男性')
    , (GENDER_FEMALE, '女性')
    , (GENDER_OTHER, 'その他')
)

# ユーザー権限
PRIVILEGE_SYSTEM = '0'
PRIVILEGE_MANAGER = '1'
PRIVILEGE_EDITOR = '2'
PRIVILEGE_REFERENCE = '3'
PRIVILEGE_CHOICES = (
    (PRIVILEGE_SYSTEM, 'システム')
    , (PRIVILEGE_MANAGER, '管理者')
    , (PRIVILEGE_EDITOR, '一般')
    , (PRIVILEGE_REFERENCE, '参照')
)

# 就業ステータス
EMPLOYMENT_STATUS_CHOICES = [
    ('1', '在職中'),
    ('2', '休職中'),
    ('3', '退職済み'),
]

POSTAL_API_URL = 'https://zipcloud.ibsnet.co.jp/api/search'