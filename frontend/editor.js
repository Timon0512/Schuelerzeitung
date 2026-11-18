import { Editor } from '@tiptap/core';
import StarterKit from '@tiptap/starter-kit';
import Image from '@tiptap/extension-image';
import { NodeSelection } from '@tiptap/pm/state';
import { mountArticleMedia, mountCoverPicker } from './article-media.js';
import { readCrop, writeCrop } from './crop-dialog.js';

const InternalImage = Image.extend({
  addOptions() {
    return { ...this.parent?.(), isAllowed: () => false, showCrops: false };
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
    }, crop: {
      default: null,
      parseHTML: element => writeCrop(readCrop(element.getAttribute('data-crop'))),
      renderHTML: attrs => attrs.crop ? { 'data-crop': attrs.crop } : {},
    }};
  },
  addNodeView() {
    if (!this.options.showCrops) return this.parent?.();
    return ({ node }) => {
      const dom = document.createElement('div');
      dom.className = 'editor-text-image';
      const frame = document.createElement('div');
      const image = document.createElement('img');
      image.draggable = false;
      frame.append(image);
      dom.append(frame);
      const update = current => {
        if (current.type !== node.type) return false;
        image.src = current.attrs.src;
        image.alt = current.attrs.alt || '';
        const crop = readCrop(current.attrs.crop);
        frame.classList.toggle('is-cropped', Boolean(current.attrs.crop));
        frame.style.setProperty('--text-edit-ratio', crop.ratio.replace('-', ' / '));
        image.style.setProperty('--text-edit-position', crop.x + '% ' + crop.y + '%');
        image.style.setProperty('--text-edit-zoom', crop.zoom / 100);
        return true;
      };
      update(node);
      return { dom, update };
    };
  },
});

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('textarea.kaktus-editor').forEach(textarea => {
    const library = textarea.form.elements.namedItem('hero_image');
    const imageOptions = () => Array.from(library?.options ?? []).filter(option => option.value);
    const config = textarea.form.querySelector('#article-media-config');
    const media = config && library && mountArticleMedia(textarea.form, config, library);
    if (media) mountCoverPicker(textarea.form, library, media);
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
        InternalImage.configure({ showCrops: Boolean(media), isAllowed: id => imageOptions().some(option => option.value === id) }),
      ],
      content: textarea.value,
      editorProps: { attributes: { role: 'textbox', 'aria-multiline': 'true', 'aria-label': 'Artikeltext' } },
      onUpdate: ({ editor }) => {
        textarea.value = editor.getHTML();
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
      },
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
    if (media) {
      const insert = addButton('Bild einfügen', () => {
        const { to } = editor.state.selection;
        media.pick('Bild in den Artikeltext einfügen', item => {
          editor.chain().focus().setTextSelection(to).setImage({
            src: item.src, mediaId: item.id, alt: item.alt,
          }).run();
        });
      });
      insert.classList.add('editor-add-image');
      const selection = () => {
        const current = editor.state.selection;
        return current instanceof NodeSelection && current.node.type.name === 'image' ? current : null;
      };
      const edit = addButton('Bildausschnitt', () => {
        const current = selection();
        if (!current) return;
        const { crop, mediaId } = current.node.attrs;
        media.editCrop(media.info(mediaId), readCrop(crop), false, result => {
          editor.chain().setNodeSelection(current.from).updateAttributes('image', { crop: writeCrop(result) }).run();
        });
      });
      const remove = addButton('Bild entfernen', () => {
        if (selection()) editor.chain().focus().deleteSelection().run();
      });
      const syncActions = () => { edit.hidden = remove.hidden = !selection(); };
      editor.on('selectionUpdate', syncActions);
      syncActions();
      return;
    }
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
