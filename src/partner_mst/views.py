from django.views import generic
from django.urls import reverse_lazy, reverse
from .models import Partner
from .form import PartnerForm
from config.common import Common
from config.base import CSVExportBaseView, CSVImportBaseView, ExcelExportBaseView
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.template.loader import render_to_string

# CSV/Excel の共通出力カラム定義
DATA_COLUMNS = [
    "partner_name", "contact_name",
    "email", "tel_number", "postal_cd", "state",
    "city", "address", "address2"
] + Common.COMMON_DATA_COLUMNS


# -----------------------------
# Partner CRUD (通常画面)
# -----------------------------

class PartnerListView(generic.ListView):
    model = Partner
    template_name = "partner_mst/partner_list.html"
    context_object_name = "partners"
    paginate_by = 20

    def get_queryset(self):
        queryset = Partner.objects.filter(is_deleted=False, tenant=self.request.user.tenant)

        search = self.request.GET.get("search")

        if search:
            queryset = queryset.filter(
                Q(partner_name__icontains=search) |
                Q(contact_name__icontains=search) |
                Q(email__icontains=search)
            )

        return queryset.order_by("partner_name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("search") or ""
        context = Common.set_pagination(context, self.request.GET.urlencode())
        return context


class PartnerCreateView(generic.CreateView):
    model = Partner
    form_class = PartnerForm
    template_name = "partner_mst/partner_edit.html"
    success_url = reverse_lazy("partner_mst:partner_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = False
        return context

    def form_valid(self, form):
        form.instance.create_user = self.request.user
        form.instance.update_user = self.request.user
        form.instance.tenant = self.request.user.tenant
        partner_message(self.request, "登録", form.instance.partner_name)
        return super().form_valid(form)


class PartnerUpdateView(generic.UpdateView):
    model = Partner
    form_class = PartnerForm
    template_name = "partner_mst/partner_edit.html"
    success_url = reverse_lazy("partner_mst:partner_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = True
        return context

    def form_valid(self, form):
        form.instance.update_user = self.request.user
        form.instance.tenant = self.request.user.tenant
        response = super().form_valid(form)
        partner_message(self.request, "更新", self.object.partner_name)
        return response


class PartnerDeleteView(generic.View):
    model = Partner
    template_name = "partner_mst/partner_confirm_delete.html"
    success_url = reverse_lazy("partner_mst:partner_list")

    def post(self, request, *args, **kwargs):
        obj = Partner.objects.get(pk=kwargs["pk"])
        obj.is_deleted = True
        obj.update_user = request.user
        obj.save()
        partner_message(request, "削除", obj.partner_name)
        return HttpResponseRedirect(reverse_lazy("partner_mst:partner_list"))


# -----------------------------
# Partner CRUD (モーダル画面)
# -----------------------------

class PartnerCreateModalView(PartnerCreateView):
    template_name = "partner_mst/partner_form.html"

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        html = render_to_string(
            self.template_name,
            {"form": form, "form_action": reverse("partner_mst:partner_create_modal"), "modal_title": "取引先新規登録"},
            request
        )
        return JsonResponse({"success": True, "html": html})

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.create_user = self.request.user
        self.object.update_user = self.request.user
        self.object.tenant = self.request.user.tenant
        self.object.save()
        partner_message(self.request, "登録", self.object.partner_name)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return super().form_valid(form)


class PartnerUpdateModalView(PartnerUpdateView):
    template_name = "partner_mst/partner_form.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        html = render_to_string(
            self.template_name,
            {"form": form, "form_action": reverse("partner_mst:partner_update_modal", kwargs={"pk": self.object.pk}),
             "modal_title": f"取引先更新: {self.object.partner_name}"},
            request
        )
        return JsonResponse({"success": True, "html": html})

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.update_user = self.request.user
        self.object.tenant = self.request.user.tenant
        self.object.save()
        partner_message(self.request, "更新", self.object.partner_name)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return super().form_valid(form)


# -----------------------------
# Export / Import
# -----------------------------

class ExportExcel(ExcelExportBaseView):
    model_class = Partner
    filename_prefix = "partner_mst"
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return search_data(request=request, query_set=qs)

    def row(self, rec):
        return get_row(rec)


class ExportCSV(CSVExportBaseView):
    model_class = Partner
    filename_prefix = "partner_mst"
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return search_data(request=request, query_set=qs)

    def row(self, rec):
        return get_row(rec)


class ImportCSV(CSVImportBaseView):
    expected_headers = DATA_COLUMNS
    model_class = Partner
    unique_field = "partner_name"

    def validate_row(self, row, idx, existing, request):
        partner_name = row.get("partner_name")
        if not partner_name:
            return None, f"{idx}行目: partner_name が空です"
        if partner_name in existing:
            return None, f"{idx}行目: partner_name '{partner_name}' は既に存在します"

        obj = Partner(
            partner_name=partner_name,
            contact_name=row.get("contact_name"),
            email=row.get("email"),
            tel_number=row.get("tel_number"),
            postal_cd=row.get("postal_cd"),
            state=row.get("state"),
            city=row.get("city"),
            address=row.get("address"),
            address2=row.get("address2"),
            create_user=request.user,
            update_user=request.user,
            tenant=request.user.tenant
        )
        return obj, None


# -----------------------------
# 共通関数
# -----------------------------

def get_row(rec):
    return [
        rec.partner_name,
        rec.contact_name,
        rec.email,
        rec.tel_number,
        rec.postal_cd,
        rec.state,
        rec.city,
        rec.address,
        rec.address2
    ] + Common.get_common_columns(rec=rec)


def search_data(request, query_set):
    keyword = request.GET.get("search") or ""
    if keyword:
        query_set = query_set.filter(
            Q(partner_name__icontains=keyword) |
            Q(contact_name__icontains=keyword) |
            Q(email__icontains=keyword)
        )
    return query_set


def partner_message(request, action, partner_name):
    messages.success(request, f"取引先「{partner_name}」を{action}しました。")
