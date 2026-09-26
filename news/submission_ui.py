"""Public form, with bounded fields and actual image decoding."""
from django import forms
from django.conf import settings
from .models import Category
from .uploads import decode_image


class SubmissionUIForm(forms.Form):
    name = forms.CharField(label="Dein Name", max_length=120, help_text="Bleibt intern.")
    class_level = forms.CharField(label="Klasse / Jahrgang", max_length=40, help_text="Bleibt intern.")
    title = forms.CharField(label="Titel", max_length=200)
    category = forms.ModelChoiceField(label="Rubrik", queryset=Category.objects.filter(is_active=True), empty_label="Bitte auswählen")
    body = forms.CharField(label="Dein Artikel", max_length=50000, widget=forms.Textarea(attrs={"rows": 12}))
    image = forms.FileField(label="Bild (optional)", required=False, help_text="JPEG, PNG oder WebP · maximal 10 MB und 25 Megapixel.",
                           widget=forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}))
    authorship_confirmed = forms.BooleanField(label="Ich habe den Text selbst geschrieben.")
    website = forms.CharField(required=False, widget=forms.HiddenInput, max_length=200)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image"].help_text = f"JPEG, PNG oder WebP · maximal {settings.IMAGE_MAX_BYTES / 1024 / 1024:g} MB und {settings.IMAGE_MAX_PIXELS / 1000000:g} Megapixel."
        for name, limit in (("name", settings.SUBMISSION_NAME_LIMIT), ("class_level", settings.SUBMISSION_CLASS_LIMIT),
                            ("title", settings.SUBMISSION_TITLE_LIMIT), ("body", settings.SUBMISSION_BODY_LIMIT)):
            self.fields[name] = forms.CharField(label=self.fields[name].label, max_length=limit,
                widget=self.fields[name].widget, help_text=self.fields[name].help_text)
            self.fields[name].widget.attrs["maxlength"] = limit

    def clean_website(self):
        if self.cleaned_data["website"]:
            raise forms.ValidationError("Die Einreichung wurde nicht angenommen. Bitte erneut versuchen.")
        return ""

    def clean_image(self):
        upload = self.cleaned_data.get("image")
        return decode_image(upload) if upload else None
