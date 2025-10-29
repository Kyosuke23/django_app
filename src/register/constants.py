'''
ユーザー登録に関連する定数
'''

# 性別
GENDER_MALE = '0'
GENDER_FEMALE = '1'
GENDER_OTHER = '2'
GENDER_CHOICES = (
    (GENDER_MALE, '男性')
    , (GENDER_FEMALE, '女性')
    , (GENDER_OTHER, 'その他')
)

GENDER_CHOICES_MAP = (
    ('男性', GENDER_MALE)
    , ('女性', GENDER_FEMALE)
    , ('その他', GENDER_OTHER)
)

# ユーザー権限
PRIVILEGE_SYSTEM = '0'
PRIVILEGE_MANAGER = '1'
PRIVILEGE_EDITOR = '2'
PRIVILEGE_VIEWER = '3'
PRIVILEGE_GUEST = '4'
PRIVILEGE_CHOICES = (
    (PRIVILEGE_SYSTEM, 'システム')
    , (PRIVILEGE_MANAGER, '管理者')
    , (PRIVILEGE_EDITOR, '更新')
    , (PRIVILEGE_VIEWER, '参照')
)

PRIVILEGE_CHOICES_MAP = (
    ('システム', PRIVILEGE_SYSTEM)
    , ('管理者', PRIVILEGE_MANAGER)
    , ('更新', PRIVILEGE_EDITOR)
    , ('参照', PRIVILEGE_VIEWER)
)

# 雇用状態
EMPLOYMENT_STATUS_CHOICES = [
    ('1', '在職中'),
    ('2', '休職中'),
    ('3', '退職'),
]

EMPLOYMENT_STATUS_CHOICES_MAP = [
    ('在職中', '1'),
    ('休職中', '2'),
    ('退職', '3'),
]

POSTAL_API_URL = 'https://zipcloud.ibsnet.co.jp/api/search'