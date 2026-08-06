from django.shortcuts import render


def stub(request):
    return render(request, 'marketing/stub.html', {'title': 'Marketing — próximamente'})
