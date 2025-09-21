from django.views import generic


class GraphIndex(generic.TemplateView):
    template_name = 'demo_app/graph/index.html'