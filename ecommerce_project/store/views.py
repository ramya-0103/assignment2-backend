from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Product, Order, OrderItem, ShippingAddress
import json
import datetime
from django.contrib.auth.forms import UserCreationForm
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .serializers import ProductSerializer, OrderSerializer


# =========================
# Registration View
# =========================
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


# =========================
# Helper: Cart Data
# =========================
def cartData(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_total': 0, 'get_cart_items': 0}
        cartItems = 0
    return {'cartItems': cartItems, 'order': order, 'items': items}


# =========================
# DRF API ViewSets
# =========================
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all().order_by('name')
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Order.objects.filter(customer=self.request.user).order_by('-date_ordered')
        return Order.objects.none()

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


# =========================
# Traditional Django Views
# =========================
@login_required(login_url='login')
def store(request):
    data = cartData(request)
    products = Product.objects.all()
    context = {'products': products, 'cartItems': data['cartItems']}
    return render(request, 'store/store.html', context)

def view_product(request, slug):
    data = cartData(request)
    product = get_object_or_404(Product, slug=slug)
    context = {'product': product, 'cartItems': data['cartItems']}
    return render(request, 'store/product_detail.html', context)

def cart(request):
    data = cartData(request)
    context = {'items': data['items'], 'order': data['order'], 'cartItems': data['cartItems']}
    return render(request, 'store/cart.html', context)

@login_required(login_url='login')
def checkout(request):
    data = cartData(request)
    context = {'items': data['items'], 'order': data['order'], 'cartItems': data['cartItems']}
    return render(request, 'store/checkout.html', context)

@login_required(login_url='login')
def order_history(request):
    orders = Order.objects.filter(customer=request.user, complete=True).order_by('-date_ordered')
    data = cartData(request)
    context = {'orders': orders, 'cartItems': data['cartItems']}
    return render(request, 'store/order_history.html', context)


# =========================
# AJAX Endpoints
# =========================
@login_required(login_url='login')
def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']

    customer = request.user
    product = Product.objects.get(id=productId)
    
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity += 1
    elif action == 'remove':
        orderItem.quantity -= 1

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()
        
    return JsonResponse({'message': 'Item updated successfully', 'cartItems': order.get_cart_items}, safe=False)


@login_required(login_url='login')
def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    customer = request.user
    order = Order.objects.get(customer=customer, complete=False)

    ShippingAddress.objects.create(
        customer=customer,
        order=order,
        address=data['shipping']['address'],
        city=data['shipping']['city'],
        state=data['shipping']['state'],
        zipcode=data['shipping']['zipcode'],
    )
    
    order.complete = True
    order.transaction_id = transaction_id
    order.save()

    return JsonResponse('Payment complete!', safe=False)
