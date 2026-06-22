document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('diagnoseForm');
  const submitBtn = document.getElementById('submitBtn');
  const errorDiv = document.getElementById('error');
  const errorMsg = document.getElementById('errorMsg');
  const resultsDiv = document.getElementById('results');
  const imageUrlInput = document.getElementById('image_url');
  const previewArea = document.getElementById('previewArea');
  const previewImg = document.getElementById('previewImg');

  // Live preview
  imageUrlInput.addEventListener('input', () => {
    const url = imageUrlInput.value.trim();
    if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
      previewImg.src = url;
      previewArea.classList.remove('hidden');
    } else {
      previewArea.classList.add('hidden');
    }
  });
  // Trigger initial preview
  imageUrlInput.dispatchEvent(new Event('input'));

  // Example buttons
  document.querySelectorAll('.example-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      imageUrlInput.value = btn.dataset.url;
      imageUrlInput.dispatchEvent(new Event('input'));
    });
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideError();
    hideResults();
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;

    const payload = {
      image_url: imageUrlInput.value.trim(),
      latitude: parseFloat(document.getElementById('latitude').value) || null,
      longitude: parseFloat(document.getElementById('longitude').value) || null,
    };

    try {
      const res = await fetch('/diagnose-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        showError(data.detail || 'Request failed');
        return;
      }

      if (data.status !== 'success') {
        showError('Diagnosis failed');
        return;
      }

      // Delay to let cards animate in
      setTimeout(() => renderResults(data), 100);
    } catch (err) {
      showError('Network error \u2014 is the server running?');
    } finally {
      submitBtn.classList.remove('loading');
      submitBtn.disabled = false;
    }
  });

  function showError(msg) {
    errorMsg.textContent = Array.isArray(msg) ? msg.map(m => m.msg || m).join(', ') : msg;
    errorDiv.classList.remove('hidden');
    resultsDiv.classList.add('hidden');
  }

  function hideError() {
    errorDiv.classList.add('hidden');
  }

  function hideResults() {
    resultsDiv.classList.add('hidden');
  }

  function renderResults(data) {
    renderVision(data.vision);
    renderWeather(data.weather);
    renderMarket(data.market);
    renderRecommendation(data.recommendation);
    // Reset card animations
    document.querySelectorAll('.card').forEach((card, i) => {
      card.style.animation = 'none';
      card.offsetHeight; // reflow
      card.style.animation = '';
      card.style.animationDelay = (i * 0.1) + 's';
    });
    resultsDiv.classList.remove('hidden');
    resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function renderVision(v) {
    const body = document.querySelector('#visionCard .card-body');
    const confidencePct = (v.confidence * 100).toFixed(0);
    const barColor = confidencePct >= 80 ? '#22c55e' : confidencePct >= 50 ? '#eab308' : '#ef4444';
    body.innerHTML = 
      <div class="label">Crop</div>
      <div class="value"></div>
      <div class="label">Disease</div>
      <div class="value" style="color:#fca5a5"></div>
      <div class="label">Confidence</div>
      <div class="value" style="font-weight:600">%</div>
      <div class="confidence-bar">
        <div class="confidence-fill" style="width:%;background:"></div>
      </div>
      <div class="label">Symptoms</div>
      <div class="value" style="color:#94a3b8;font-size:0.9rem"></div>
    ;
  }

  function renderWeather(w) {
    const body = document.querySelector('#weatherCard .card-body');
    body.innerHTML = 
      <div class="label">Temperature</div>
      <div class="value" style="font-size:1.3rem;font-weight:700"></div>
      <div class="label">Humidity</div>
      <div class="value"></div>
      <div class="label">Forecast</div>
      <div class="value" style="text-transform:capitalize"></div>
    ;
  }

  function renderMarket(m) {
    const trendClass = m.trend === 'increasing' ? 'tag-green'
      : m.trend === 'decreasing' ? 'tag-red'
      : 'tag-yellow';
    const trendIcon = m.trend === 'increasing' ? '\u2191' : m.trend === 'decreasing' ? '\u2193' : '\u2192';

    const body = document.querySelector('#marketCard .card-body');
    body.innerHTML = 
      <div class="label">Crop</div>
      <div class="value"></div>
      <div class="label">Current Price</div>
      <div class="value" style="font-size:1.3rem;font-weight:700;color:#22c55e"></div>
      <div class="label">Trend</div>
      <div class="value"><span class="tag "> </span></div>
    ;
  }

  function renderRecommendation(r) {
    const body = document.querySelector('#recommendationCard .card-body');
    // Format recommendation: split into sections, detect bullet points
    const text = r.replace(/\*\*/g, '').trim();
    let html = '';
    const lines = text.split('\n').map(l => l.trim()).filter(l => l);

    let inList = false;
    for (const line of lines) {
      if (line.startsWith('- ') || line.startsWith('* ') || line.startsWith('\u2022 ')) {
        if (!inList) { html += '<ul>'; inList = true; }
        html += '<li>' + line.replace(/^[-*\u2022]\s*/, '') + '</li>';
      } else if (/^\d+[\.\)]/.test(line)) {
        if (!inList) { html += '<ul>'; inList = true; }
        html += '<li>' + line.replace(/^\d+[\.\)]\s*/, '') + '</li>';
      } else {
        if (inList) { html += '</ul>'; inList = false; }
        html += '<p style="margin-bottom:6px">' + line + '</p>';
      }
    }
    if (inList) html += '</ul>';
    body.innerHTML = html;
  }
});
