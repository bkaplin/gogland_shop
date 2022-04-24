from django import forms


class CalculateAverageForm(forms.Form):
    data = forms.CharField(widget=forms.Textarea(attrs={'cols': 50, 'rows': 40}))
