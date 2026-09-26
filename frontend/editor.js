import { Editor } from '@tiptap/core';
import StarterKit from '@tiptap/starter-kit';
import Image from '@tiptap/extension-image';

const InternalImage = Image.extend({
  parseHTML() {
    return [{ tag: 'img[data-media-id]', getAttrs: element => {
      const id = element.getAttribute('data-media-id');
      const selected = [...document.querySelectorAll('#id_text_images option:checked')].some(option => option.value === id);
      return selected && /^[a-f0-9-]{36}$/.test(id || '') ? null : false;
    }}];
  },
  addAttributes() {
    return { ...this.parent?.(), src: {
      default: null,
      parseHTML: element => `/redaktion/medien/${element.getAttribute('data-media-id')}`,
    }, mediaId: {
      default: null,
      parseHTML: element => element.getAttribute('data-media-id'),
      renderHTML: attrs => ({ 'data-media-id': attrs.mediaId }),
    }};
  },
});

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('textarea.kaktus-editor').forEach(textarea => {
    const wrapper = document.createElement('div');
    wrapper.className = 'editor-wrapper';
    const toolbar = document.createElement('div');
    toolbar.className = 'editor-toolbar';
    toolbar.setAttribute('role', 'group');
    toolbar.setAttribute('aria-label', 'Text formatieren');
    const surface = document.createElement('div');
    wrapper.append(toolbar, surface);
    textarea.after(wrapper);
    const parsed = new DOMParser().parseFromString(textarea.value, 'text/html');
    parsed.querySelectorAll('img').forEach(img => {
      const id = img.getAttribute('data-media-id');
      if (/^[a-f0-9-]{36}$/.test(id || '')) img.src = `/redaktion/medien/${id}`;
      else img.remove();
    });
    const editor = new Editor({
      element: surface,
      extensions: [StarterKit.configure({ heading: { levels: [2, 3] }, code: false, codeBlock: false, horizontalRule: false, strike: false, underline: false, link: { openOnClick: false, protocols: ['http', 'https', 'mailto'] } }), InternalImage],
      content: parsed.body.innerHTML,
      editorProps: { attributes: { role: 'textbox', 'aria-multiline': 'true', 'aria-label': 'Artikeltext' } },
      onUpdate: ({ editor }) => { textarea.value = editor.getHTML(); },
    });
    textarea.hidden = true;
    document.querySelector(`label[for="${textarea.id}"]`)?.addEventListener('click', event => { event.preventDefault(); editor.commands.focus(); });
    const addButton = (label, action, active) => {
      const button = document.createElement('button');
      button.type = 'button'; button.textContent = label;
      button.addEventListener('click', action);
      if (active) {
        const update = () => button.setAttribute('aria-pressed', String(active()));
        editor.on('transaction', update); update();
      }
      toolbar.append(button);
    };
    addButton('Absatz', () => editor.chain().focus().setParagraph().run());
    addButton('Zwischenüberschrift', () => editor.chain().focus().toggleHeading({ level: 2 }).run(), () => editor.isActive('heading'));
    for (const [label, command, mark] of [['Fett', 'toggleBold', 'bold'], ['Kursiv', 'toggleItalic', 'italic'], ['Liste', 'toggleBulletList', 'bulletList'], ['Nummerierung', 'toggleOrderedList', 'orderedList']]) {
      addButton(label, () => editor.chain().focus()[command]().run(), () => editor.isActive(mark));
    }
    addButton('Link', () => {
      const href = window.prompt('Linkadresse (https://, http:// oder mailto:). Leer lassen zum Entfernen.', editor.getAttributes('link').href || 'https://');
      if (href === null) return;
      if (!href) editor.chain().focus().extendMarkRange('link').unsetLink().run();
      else if (/^(https?:\/\/|mailto:)/i.test(href)) editor.chain().focus().extendMarkRange('link').setLink({ href }).run();
      else window.alert('Bitte eine vollständige sichere Linkadresse eingeben.');
    });
    const picker = document.createElement('select');
    picker.setAttribute('aria-label', 'Ausgewähltes Textbild einfügen');
    const refresh = () => {
      picker.replaceChildren(new Option('Textbild auswählen', ''));
      document.querySelectorAll('#id_text_images option:checked').forEach(option => picker.add(new Option(option.textContent, option.value)));
    };
    document.querySelector('#id_text_images')?.addEventListener('change', refresh);
    refresh(); toolbar.append(picker);
    addButton('Bild einfügen', () => {
      if (picker.value) editor.chain().focus().setImage({ src: `/redaktion/medien/${picker.value}`, mediaId: picker.value, alt: picker.selectedOptions[0].textContent }).run();
    });
    textarea.form.addEventListener('submit', () => { textarea.value = editor.getHTML(); });
  });
});
