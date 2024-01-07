from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from .models import clInput
from .forms import CheckListRow

# Create your views here.

@login_required
def main(request):
    if request.method == "POST":
        form = CheckListRow(request.POST)
        if form.is_valid():
            # Variables to Update to DB
            user = request.user
            c1 = form.cleaned_data['c1']
            c1_comment = form.cleaned_data['c1_comment']
            c2 = form.cleaned_data['c2']
            c2_comment = form.cleaned_data['c2_comment']
            c3 = form.cleaned_data['c3']
            c3_comment = form.cleaned_data['c3_comment']
            c4 = form.cleaned_data['c4']
            c4_comment = form.cleaned_data['c4_comment']
            c5 = form.cleaned_data['c5']
            c5_comment = form.cleaned_data['c5_comment']
            c6 = form.cleaned_data['c6']
            c6_comment = form.cleaned_data['c6_comment']

            # Update DB
            d = clInput(user=user,
                    c1=c1, c1_comment=c1_comment,
                    c2=c2, c2_comment=c2_comment,
                    c3=c3, c3_comment=c3_comment,
                    c4=c4, c4_comment=c4_comment,
                    c5=c5, c5_comment=c5_comment,
                    c6=c6, c6_comment=c6_comment)
            d.save()

            #return HttpResponse(status=200)
            return HttpResponseRedirect("report")

    else:
        form = CheckListRow()
        return render(request, "checklist/index.html", {"form": form})

@login_required
def report(request):
    query_results = clInput.objects.all().order_by('-date_created')[:15]
    query_users = User.objects.values('id', 'username')
    return render(request, "checklist/report.html", {'clInput': query_results, 'User': query_users})
