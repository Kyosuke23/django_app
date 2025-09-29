from django.conf import settings
from register import constants as register_const


def const_str(request):
    """
    HTMLメタデータを渡す
    """
    return {
        # 性別
        'GENDER_MALE': register_const.GENDER_MALE,
        'GENDER_FEMALE': register_const.GENDER_FEMALE,
        'GENDER_OTHER': register_const.GENDER_OTHER,
        'GENDER_CHOICES': register_const.GENDER_CHOICES,

        # ユーザー権限
        'PRIVILEGE_ADMIN': register_const.PRIVILEGE_ADMIN,
        'PRIVILEGE_EDITOR': register_const.PRIVILEGE_EDITOR,
        'PRIVILEGE_REFERENCE': register_const.PRIVILEGE_REFERENCE,
        'PRIVILEGE_GUEST': register_const.PRIVILEGE_GUEST,
        'PRIVILEGE_CHOICES': register_const.PRIVILEGE_CHOICES,
    }