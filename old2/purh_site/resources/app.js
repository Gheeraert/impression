
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

  if (!window.matchMedia('(min-width: 1241px)').matches) {
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

    const card = document.createElement('div');
    card.className = 'margin-note';
    card.id = `margin-${noteId}`;

    const number = document.createElement('div');
    number.className = 'margin-note-number';
    number.textContent = `Note ${ref.textContent.trim()}`;
    card.appendChild(number);

    const body = document.createElement('div');
    body.className = 'margin-note-body';
    body.innerHTML = source.innerHTML;
    body.querySelectorAll('a[href^="#noteref-"]').forEach((a) => {
      a.classList.add('margin-note-backlink');
      a.setAttribute('tabindex', '-1');
      a.setAttribute('aria-hidden', 'true');
    });
    card.appendChild(body);

    marginContainer.appendChild(card);

    let top = ref.getBoundingClientRect().top - mainRect.top - 8;
    top = Math.max(top, nextTop);
    card.style.top = `${top}px`;
    nextTop = top + card.offsetHeight + 14;

    ref.addEventListener('mouseenter', () => {
      ref.classList.add('is-active');
      card.classList.add('is-active');
    });
    ref.addEventListener('mouseleave', () => {
      ref.classList.remove('is-active');
      card.classList.remove('is-active');
    });
    card.addEventListener('mouseenter', () => {
      ref.classList.add('is-active');
      card.classList.add('is-active');
    });
    card.addEventListener('mouseleave', () => {
      ref.classList.remove('is-active');
      card.classList.remove('is-active');
    });

    built += 1;
  });

  if (built > 0) {
    pageGrid.classList.add('has-margin-notes');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const current = document.querySelector('.nav-item.is-current > a');
  if (current) {
    current.scrollIntoView({ block: 'nearest' });
  }
  buildMarginNotes();
});

let resizeTimer = null;
window.addEventListener('resize', () => {
  window.clearTimeout(resizeTimer);
  resizeTimer = window.setTimeout(buildMarginNotes, 100);
});
