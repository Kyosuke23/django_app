from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from ..form import AjaxTestForm
from django.http import HttpResponse
from django.http import JsonResponse

import json


class AjaxTest(LoginRequiredMixin, generic.FormView):
    template_name = 'demo_app/ajax_test/index.html'
    form_class = AjaxTestForm
    success_url = reverse_lazy('demo_app:ajax_test')

    def post(self, request, *args, **kwargs):
        form = self.get_form(self.form_class)
        if form.is_valid():
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return self.ajax_response(form)
            # Ajax以外のPOSTメソッドの処理
            return self.form_valid(form)
        # フォームデータが正しくない場合の処理
        return JsonResponse(
            {
                'errors': form.errors
            },
            json_dumps_params={'ensure_ascii': False}  # 文字化け対策
        )

    def ajax_response(self, form):
        """jQuery に対してレスポンスを返すメソッド"""
        input = form.cleaned_data.get('input')
        input2 = form.cleaned_data.get('input2')
        return HttpResponse(json.dumps({
            'input': input
            , 'input2': input2
        }))