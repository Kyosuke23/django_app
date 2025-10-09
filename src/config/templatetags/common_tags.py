from django import template
import re

register = template.Library()


@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    """
    現在のリクエストのGETパラメータを保持したまま、
    特定のキーを上書き・追加してURLクエリ文字列を返す。

    使用例：
        <a href="{% querystring sort='username' order='desc' %}">
            ユーザー名
        </a>
    """
    request = context.get('request')
    if not request:
        return ''

    # 現在のクエリパラメータをコピー
    params = request.GET.copy()

    # 新しい値を上書き
    for key, value in kwargs.items():
        if value in [None, '']:
            params.pop(key, None)
        else:
            params[key] = value

    query = params.urlencode()
    return '?' + query if query else ''

# -------------------------------------------------------
# 電話番号フォーマット
# -------------------------------------------------------
@register.filter
def format_tel(value):
    '''電話番号をハイフン付きでフォーマット（簡易版）'''
    if not value:
        return ''
    value = re.sub(r'\D', '', value)  # 数字以外を除去

    # 携帯 (090/080/070)
    if re.match(r'^0[789]0', value):
        return f'{value[:3]}-{value[3:7]}-{value[7:]}'
    # 東京・大阪などの2桁市外局番
    elif value.startswith('03') or value.startswith('06'):
        return f'{value[:2]}-{value[2:6]}-{value[6:]}'
    # それ以外（3桁市外局番）
    elif len(value) == 10:
        return f'{value[:3]}-{value[3:6]}-{value[6:]}'
    elif len(value) == 9:
        return f'{value[:2]}-{value[2:5]}-{value[5:]}'
    else:
        return value


# -------------------------------------------------------
# 郵便番号フォーマット
# -------------------------------------------------------
@register.filter
def format_postal(value):
    '''郵便番号を 123-4567 形式にフォーマット'''
    if not value:
        return ''
    value = re.sub(r'\D', '', value)  # 数字以外を除去
    if len(value) == 7:
        return f'{value[:3]}-{value[3:]}'
    return value
