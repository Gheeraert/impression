function buildMarginNotes() {
  const pageGrid = document.querySelector('.page-grid');
  const pageMain = document.querySelector('.page-main');
  const marginContainer = document.getElementById('margin-notes');
  const endnotes = document.querySelector('.endnotes');

  if (!pageGrid || !pageMain || !marginContainer || !endnotes) {
    return;
  }

  marginContainer.innerHTML = '';
  pageGrid.classList.remove('has-margin-notes');

  if (!window.matchMedia('(min-width: 1261px)').matches) {
    return;
  }

  const refs = Array.from(pageMain.querySelectorAll('.note-ref'));
  if (!refs.length) {
    return;
  }

  const mainRect = pageMain.getBoundingClientRect();
  let nextTop = 0;
  let built = 0;

  refs.forEach((ref) => {
    const link = ref.querySelector('a');
    if (!link || !link.hash) return;

    const noteId = link.hash.slice(1);
    const source = document.getElementById(noteId);
    if (!source) return;

    const note = document.createElement('div');
    note.className = 'margin-note';
    note.id = `margin-${noteId}`;

    const number = document.createElement('div');
    number.className = 'margin-note-number';
    number.textContent = `Note ${ref.textContent.trim()}`;
    note.appendChild(number);

    const body = document.createElement('div');
    body.className = 'margin-note-body';
    body.innerHTML = source.innerHTML;
    body.querySelectorAll('a[href^="#noteref-"]').forEach((a) => {
      a.classList.add('margin-note-backlink');
      a.setAttribute('tabindex', '-1');
      a.setAttribute('aria-hidden', 'true');
    });
    note.appendChild(body);

    marginContainer.appendChild(note);

    let top = ref.getBoundingClientRect().top - mainRect.top - 8;
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
    pageGrid.classList.add('has-margin-notes');
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
});

let resizeTimer = null;
window.addEventListener('resize', () => {
  window.clearTimeout(resizeTimer);
  resizeTimer = window.setTimeout(buildMarginNotes, 100);
});
