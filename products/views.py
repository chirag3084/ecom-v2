from django.shortcuts import render
from django.views.generic import ListView, DetailView
from products.models import Product
from django.http import HttpResponse
from .filters import ProductFilter


class Home(ListView):
    model = Product
    template_name = 'products/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = ProductFilter(self.request.GET, queryset=self.get_queryset())
        return context


class ProductDetail(DetailView):
    # Anyone can view a product's detail page - no login required to browse.
    model = Product


from .tasks import send_welcome_email


def my_view(request):
    send_welcome_email.delay("chiragsurti308444@gmail.com")
    return HttpResponse("Task scheduled!")
