function canShowMarginNotes(pageGrid) {
  if (!pageGrid) return false;
  if (window.innerWidth < 1024) return false;

  const content = document.querySelector('.content');
  const usableWidth = content ? content.clientWidth : pageGrid.clientWidth;
  return usableWidth >= 720;
}

function plainNoteText(noteElement) {
  const clone = noteElement.cloneNode(true);
  clone.querySelectorAll('a[href^="#noteref-"]').forEach((a) => a.remove());
  return (clone.textContent || '').replace(/\s+/g, ' ').trim();
}

function truncateNoteText(text, limit = 145) {
  if (!text) return '';
  if (text.length <= limit) return text;
  const cut = text.slice(0, limit);
  const lastSpace = cut.lastIndexOf(' ');
  const safe = lastSpace > 80 ? cut.slice(0, lastSpace) : cut;
  return `${safe.trim()} (…)`;
}

function buildMarginNotes() {
  const pageGrid = document.querySelector('.page-grid');
  const pageMain = document.querySelector('.page-main');
  const marginContainer = document.getElementById('margin-notes');
  const endnotes = document.querySelector('.endnotes');

  if (!pageGrid || !pageMain || !marginContainer || !endnotes) {
    return;
  }

  marginContainer.innerHTML = '';
  marginContainer.style.removeProperty('--margin-notes-height');
  pageGrid.classList.remove('has-margin-notes');

  if (!canShowMarginNotes(pageGrid)) {
    return;
  }

  const refs = Array.from(pageMain.querySelectorAll('.note-ref'));
  if (!refs.length) {
    return;
  }

  pageGrid.classList.add('has-margin-notes');
  const mainRect = pageMain.getBoundingClientRect();
  let nextTop = 0;
  let built = 0;

  refs.forEach((ref) => {
    const link = ref.querySelector('a');
    if (!link || !link.hash) return;

    const noteId = link.hash.slice(1);
    const source = document.getElementById(noteId);
    if (!source) return;

    const note = document.createElement('aside');
    note.className = 'margin-note';
    note.id = `margin-${noteId}`;

    const noteLink = document.createElement('a');
    noteLink.className = 'margin-note-link';
    noteLink.href = `#${noteId}`;
    noteLink.title = 'Aller à la note complète';

    const number = document.createElement('span');
    number.className = 'margin-note-number';
    number.textContent = `${ref.textContent.trim()}.`;
    noteLink.appendChild(number);

    const body = document.createElement('span');
    body.className = 'margin-note-body';
    body.textContent = truncateNoteText(plainNoteText(source));
    noteLink.appendChild(body);

    note.appendChild(noteLink);
    marginContainer.appendChild(note);

    const refRect = ref.getBoundingClientRect();
    let top = refRect.top - mainRect.top - 8;
    top = Math.max(top, nextTop);
    note.style.top = `${top}px`;
    nextTop = top + note.offsetHeight + 14;

    const activate = () => {
      ref.classList.add('is-active');
      note.classList.add('is-active');
    };
    const deactivate = () => {
      ref.classList.remove('is-active');
      note.classList.remove('is-active');
    };

    ref.addEventListener('mouseenter', activate);
    ref.addEventListener('mouseleave', deactivate);
    note.addEventListener('mouseenter', activate);
    note.addEventListener('mouseleave', deactivate);

    built += 1;
  });

  if (built > 0) {
    marginContainer.style.setProperty('--margin-notes-height', `${Math.max(pageMain.offsetHeight, nextTop)}px`);
  } else {
    pageGrid.classList.remove('has-margin-notes');
  }
}


function ensureLightbox() {
  let root = document.getElementById('site-lightbox');
  if (root) {
    return {
      root,
      backdrop: root.querySelector('.lightbox-backdrop'),
      dialog: root.querySelector('.lightbox-dialog'),
      image: root.querySelector('.lightbox-image'),
      caption: root.querySelector('.lightbox-caption'),
      close: root.querySelector('.lightbox-close'),
      download: root.querySelector('.lightbox-download'),
    };
  }

  root = document.createElement('div');
  root.id = 'site-lightbox';
  root.className = 'lightbox';
  root.hidden = true;
  root.innerHTML = `
  <div class="lightbox-backdrop"></div>
  <div class="lightbox-dialog" role="dialog" aria-modal="true" aria-label="Image agrandie">
    <div class="lightbox-toolbar">
      <a class="lightbox-download" href="#" download>Télécharger l’original</a>
      <button type="button" class="lightbox-close" aria-label="Fermer l'image">×</button>
    </div>
    <figure class="lightbox-figure">
      <img class="lightbox-image" alt="">
      <figcaption class="lightbox-caption" hidden></figcaption>
    </figure>
  </div>
  `;
  document.body.appendChild(root);

  return {
    root,
    backdrop: root.querySelector('.lightbox-backdrop'),
    dialog: root.querySelector('.lightbox-dialog'),
    image: root.querySelector('.lightbox-image'),
    caption: root.querySelector('.lightbox-caption'),
    close: root.querySelector('.lightbox-close'),
    download: root.querySelector('.lightbox-download'),
  };
}

let activeLightboxTrigger = null;
let lightboxHideTimer = null;

function closeLightbox() {
  const lb = ensureLightbox();
  if (lb.root.hidden) return;

  document.body.classList.remove('lightbox-open');
  lb.root.classList.remove('is-open');
  window.clearTimeout(lightboxHideTimer);
  lightboxHideTimer = window.setTimeout(() => {
    lb.root.hidden = true;
    lb.image.removeAttribute('src');
    lb.image.alt = '';
    lb.caption.textContent = '';
    lb.caption.hidden = true;
    lb.download.setAttribute('href', '#');
    lb.download.removeAttribute('download');
  }, 220);

  if (activeLightboxTrigger && typeof activeLightboxTrigger.focus === 'function') {
    activeLightboxTrigger.focus();
  }
  activeLightboxTrigger = null;
}

function openLightbox(trigger) {
  const src = trigger?.dataset?.lightboxSrc;
  if (!src) return;

  const lb = ensureLightbox();
  const image = trigger.querySelector('img');
  const alt = trigger.dataset.lightboxAlt || image?.getAttribute('alt') || '';
  const caption = trigger.dataset.lightboxCaption || alt || '';
  const downloadName = src.split('/').pop() || 'original';

  window.clearTimeout(lightboxHideTimer);
  activeLightboxTrigger = trigger;
  lb.image.src = src;
  lb.image.alt = alt;
  lb.caption.textContent = caption;
  lb.caption.hidden = !caption;
  lb.download.href = src;
  lb.download.setAttribute('download', downloadName);
  lb.root.hidden = false;

  window.requestAnimationFrame(() => {
    lb.root.classList.add('is-open');
    document.body.classList.add('lightbox-open');
    lb.close.focus({ preventScroll: true });
  });
}

function initLightbox() {
  const lb = ensureLightbox();

  lb.backdrop.addEventListener('click', closeLightbox);
  lb.close.addEventListener('click', closeLightbox);
  lb.root.addEventListener('click', (event) => {
    if (event.target === lb.root) closeLightbox();
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      closeLightbox();
    }
  });

  document.querySelectorAll('[data-lightbox-src]').forEach((trigger) => {
    if (trigger.dataset.lightboxBound === '1') return;
    trigger.dataset.lightboxBound = '1';
    trigger.addEventListener('click', (event) => {
      event.preventDefault();
      openLightbox(trigger);
    });
  });
}

function renderConsultationDates() {
  const nodes = document.querySelectorAll('.consultation-date');
  if (!nodes.length) return;

  const now = new Date();
  const formatted = now.toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
  const iso = now.toISOString().split('T')[0];

  nodes.forEach((node) => {
    node.textContent = formatted;
    node.setAttribute('datetime', iso);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const current = document.querySelector('.nav-item.is-current > a');
  if (current) {
    current.scrollIntoView({ block: 'nearest' });
  }
  renderConsultationDates();
  initLightbox();
  buildMarginNotes();
  window.requestAnimationFrame(buildMarginNotes);
});

window.addEventListener('load', buildMarginNotes);

document.fonts?.ready?.then(() => buildMarginNotes());

if (window.ResizeObserver) {
  const pageMain = document.querySelector('.page-main');
  if (pageMain) {
    const ro = new ResizeObserver(() => buildMarginNotes());
    ro.observe(pageMain);
  }
}

let resizeTimer = null;
window.addEventListener('resize', () => {
  window.clearTimeout(resizeTimer);
  resizeTimer = window.setTimeout(buildMarginNotes, 120);
});
