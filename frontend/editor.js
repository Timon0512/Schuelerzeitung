import { Editor } from '@tiptap/core';
import StarterKit from '@tiptap/starter-kit';
import Image from '@tiptap/extension-image';

const InternalImage = Image.extend({
  addOptions() {
    return { ...this.parent?.(), isAllowed: () => false };
  },
  addInputRules() {
    return [];
  },
  parseHTML() {
    return [{ tag: 'img[data-media-id]', getAttrs: element => {
      const id = element.getAttribute('data-media-id');
      return this.options.isAllowed(id) ? null : false;
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
    // The cover image field already lists the media allowed for this article.
    const library = textarea.form.elements.namedItem('hero_image');
    const imageOptions = () => Array.from(library?.options ?? []).filter(option => option.value);
    const wrapper = document.createElement('div');
    wrapper.className = 'editor-wrapper';
    const toolbar = document.createElement('div');
    toolbar.className = 'editor-toolbar';
    toolbar.setAttribute('role', 'group');
    toolbar.setAttribute('aria-label', 'Text formatieren');
    const picker = document.createElement('div');
    picker.id = `${textarea.id}-image-picker`;
    picker.className = 'editor-image-picker';
    picker.hidden = true;
    const surface = document.createElement('div');
    wrapper.append(toolbar, picker, surface);
    textarea.after(wrapper);
    const editor = new Editor({
      element: surface,
      extensions: [
        StarterKit.configure({ heading: { levels: [2, 3] }, code: false, codeBlock: false, horizontalRule: false, strike: false, underline: false, link: { openOnClick: false, protocols: ['http', 'https', 'mailto'] } }),
        InternalImage.configure({ isAllowed: id => imageOptions().some(option => option.value === id) }),
      ],
      content: textarea.value,
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
      return button;
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
    const closePicker = () => {
      picker.hidden = true;
      insertButton.setAttribute('aria-expanded', 'false');
    };
    const insertButton = addButton('Bild einfügen', () => {
      if (!picker.hidden) {
        closePicker();
        return;
      }
      const options = imageOptions();
      if (options.length) {
        picker.replaceChildren(...options.map(option => {
          const choice = document.createElement('button');
          choice.type = 'button';
          choice.textContent = option.textContent;
          choice.addEventListener('click', () => {
            editor.chain().focus().setImage({
              src: `/redaktion/medien/${option.value}`,
              mediaId: option.value,
              alt: option.textContent,
            }).run();
            closePicker();
          });
          return choice;
        }));
      } else {
        const message = document.createElement('p');
        message.tabIndex = -1;
        message.textContent = 'Noch keine Bilder verfügbar. Lade zuerst unter „Bilder“ ein Bild hoch.';
        picker.replaceChildren(message);
      }
      picker.hidden = false;
      insertButton.setAttribute('aria-expanded', 'true');
      picker.firstElementChild.focus();
    });
    insertButton.setAttribute('aria-controls', picker.id);
    insertButton.setAttribute('aria-expanded', 'false');
    wrapper.addEventListener('keydown', event => {
      if (event.key === 'Escape' && !picker.hidden) {
        event.preventDefault();
        closePicker();
        insertButton.focus();
      }
    });
    textarea.form.addEventListener('submit', () => { textarea.value = editor.getHTML(); });
  });
});
