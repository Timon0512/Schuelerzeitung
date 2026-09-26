from django import forms
from .content import clean_body
from .models import Article, Media, SlugRedirect
from .services import selectable_media
from .uploads import decode_image


class EditorWidget(forms.Textarea):
    class Media:
        js = ["news/editor.js"]
        css = {"all": ["news/editor.css"]}


class ArticleForm(forms.ModelForm):
    hero_focus_image = forms.CharField(required=False, widget=forms.HiddenInput)
    text_images = forms.ModelMultipleChoiceField(label="Textbilder", queryset=Media.objects.none(), required=False,
        help_text="Bilder auswählen und mit ‚Bild einfügen‘ im Text platzieren. Neue Bilder zuerst unter Bilder hochladen.")

    class Meta:
        model = Article
        fields = ["title", "slug", "excerpt", "category", "author", "hero_image", "hero_focus_x", "hero_focus_y", "hero_focus_image", "text_images", "body"]
        widgets = {"body": EditorWidget(attrs={"class": "kaktus-editor"})}
        labels = {"slug": "Artikeladresse", "author": "Autorendarstellung", "hero_image": "Titelbild"}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.initial["hero_focus_image"] = str(self.instance.hero_image_id or "")
        for name in ("hero_focus_x", "hero_focus_y"):
            self.fields[name].required = False
            self.fields[name].widget.attrs.update({"min": 0, "max": 100, "step": 1})
        self.fields["hero_focus_x"].help_text = "0 = links, 100 = rechts. Ohne JavaScript wird ein neues Titelbild zunächst zentriert; danach speichern und den Fokus einstellen."
        self.fields["hero_focus_y"].help_text = "0 = oben, 100 = unten."
        allowed = selectable_media(user, self.instance)
        for name in ("hero_image", "text_images"):
            self.fields[name].queryset = allowed
            self.fields[name].label_from_instance = lambda image: image.alt_text or "Bild ohne Alternativtext"
        if self.instance.pk:
            self.initial["text_images"] = self.instance.images.all()

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        if SlugRedirect.objects.filter(slug=slug).exclude(article_id=self.instance.pk).exists():
            raise forms.ValidationError("Diese Artikeladresse ist als Weiterleitung reserviert.")
        return slug

    def clean(self):
        data = super().clean()
        selected = str(data["hero_image"].pk) if data.get("hero_image") else ""
        for name in ("hero_focus_x", "hero_focus_y"):
            if name not in self.errors and (data.get(name) is None or selected != data.get("hero_focus_image", "")):
                data[name] = 50
        images = list(data.get("text_images", ()))
        data["body"] = clean_body(data.get("body", ""), images)
        if self.instance.status == "published":
            if not data.get("author"):
                self.add_error("author", "Bitte eine Autorendarstellung auswählen.")
            all_images = images + ([data["hero_image"]] if data.get("hero_image") else [])
            if any(not image.alt_text.strip() for image in all_images):
                self.add_error("text_images", "Alle Bilder benötigen einen Alternativtext.")
        return data

    class Media:
        js = ["news/image-focus.js"]
        css = {"all": ["news/image-focus.css"]}


class MediaForm(forms.ModelForm):
    class Meta:
        model = Media
        fields = ["file", "alt_text", "caption"]
        widgets = {"file": forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp"})}

    def clean_alt_text(self):
        value = self.cleaned_data["alt_text"].strip()
        if not value:
            raise forms.ValidationError("Bitte beschreiben, was auf dem Bild zu sehen ist.")
        return value

    def clean_file(self):
        upload = self.cleaned_data["file"]
        if "file" in self.changed_data:
            file, width, height = decode_image(upload)
            self.instance.width, self.instance.height = width, height
            self.instance.size, self.instance.mime_type = file.size, "image/webp"
            return file
        return upload
