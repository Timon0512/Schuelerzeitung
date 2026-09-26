"""Presentation contract for package 6; no storage or public POST handler."""
from django import forms
from .models import Category


class SubmissionUIForm(forms.Form):
    name = forms.CharField(label="Dein Name", max_length=120, help_text="Bleibt intern.")
    class_level = forms.CharField(label="Klasse / Jahrgang", max_length=40, help_text="Bleibt intern.")
    title = forms.CharField(label="Titel", max_length=240)
    category = forms.ModelChoiceField(label="Rubrik", queryset=Category.objects.filter(is_active=True), empty_label="Bitte auswählen")
    body = forms.CharField(label="Dein Artikel", max_length=50000, widget=forms.Textarea(attrs={"rows": 12}))
    image = forms.FileField(label="Bild (optional)", required=False, help_text="JPEG, PNG oder WebP · maximal 10 MB und 25 Megapixel.",
                           widget=forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}))
    authorship_confirmed = forms.BooleanField(label="Ich habe den Text selbst geschrieben.")
