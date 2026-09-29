const form = document.querySelector('.planner-form');

function formatRupees(value) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value);
}

function makeElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function renderRecommendations(panel, data) {
  panel.replaceChildren();
  const heading = makeElement('div', 'results-heading');
  const headingCopy = document.createElement('div');
  headingCopy.append(makeElement('span', 'step-label', '02  /  YOUR SHORTLIST'), makeElement('h2', '', 'A good place to start.'));
  heading.append(headingCopy, makeElement('span', 'results-budget', `${formatRupees(data.budget)} budget`));
  panel.append(heading);
  const cards = makeElement('div', 'recommendation-cards');
  data.recommendation.items.forEach((item, index) => {
    const card = makeElement('article', 'recommendation-card');
    card.append(makeElement('span', 'recommendation-index', `0${index + 1}`));
    const copy = makeElement('div', 'recommendation-copy');
    copy.append(makeElement('span', 'recommendation-platform', item.platform), makeElement('h3', '', item.title), makeElement('p', '', item.detail));
    const price = makeElement('div', 'recommendation-price');
    price.append(makeElement('strong', '', formatRupees(item.price)), makeElement('small', '', 'estimate'));
    const link = makeElement('a', 'recommendation-link', 'Explore ↗');
    link.href = item.search_url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    card.append(copy, price, link);
    cards.append(card);
  });
  panel.append(cards, makeElement('p', 'results-note', `✳  ${data.recommendation.note}`));
  if (data.id) {
    const historyLink = makeElement('a', 'text-link result-history-link', 'View this saved plan ↗');
    historyLink.href = `/plan/${encodeURIComponent(data.id)}`;
    panel.append(historyLink);
  }
  panel.hidden = false;
}

if (form) {
  const errorBox = form.querySelector('.form-error');
  const resultsPanel = document.querySelector('.results-panel');
  const submitButton = form.querySelector('.submit-button');
  const imageInput = form.querySelector('input[type="file"]');
  imageInput?.addEventListener('change', () => {
    const name = imageInput.files?.[0]?.name || '';
    form.querySelector('.upload-name').textContent = name;
    form.querySelector('.upload-hint').textContent = name ? '✓  Photo ready to include' : '＋  Add a photo · JPG, PNG or WebP · up to 5 MB';
  });
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    errorBox.hidden = true;
    resultsPanel.hidden = true;
    submitButton.disabled = true;
    submitButton.textContent = 'Putting ideas together…';
    try {
      const response = await fetch(form.dataset.endpoint, { method: 'POST', body: new FormData(form), credentials: 'same-origin' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'That plan needs a second look.');
      renderRecommendations(resultsPanel, data);
      resultsPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
      errorBox.textContent = error.message || 'We couldn’t build that plan. Please try again.';
      errorBox.hidden = false;
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = 'Find my ideas ↗';
    }
  });
}

const dateLabel = document.querySelector('#today-label');
if (dateLabel) {
  dateLabel.textContent = new Intl.DateTimeFormat('en-IN', { weekday: 'short', day: 'numeric', month: 'short' }).format(new Date()).toUpperCase();
}