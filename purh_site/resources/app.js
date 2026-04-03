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
