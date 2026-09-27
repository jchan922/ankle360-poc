/* theme.js — progressive enhancement. Pages work without it.
   Shopify: assets/theme.js (defer). Parts marked PROTOTYPE are replaced by Shopify's
   Cart API and form handling in the theme. */
(() => {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const money = (cents) => `$${(cents / 100).toFixed(2)}`;

  /* ---------- Mobile nav disclosure ---------- */
  const toggle = document.querySelector('[data-menu-toggle]');
  const nav = document.getElementById('site-nav');
  if (toggle && nav) {
    const setOpen = (open) => { toggle.setAttribute('aria-expanded', String(open)); nav.dataset.open = String(open); };
    setOpen(false);
    toggle.addEventListener('click', () => setOpen(toggle.getAttribute('aria-expanded') !== 'true'));
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') { setOpen(false); toggle.focus(); }
    });
  }

  /* ---------- Hero video: reliable autoplay, pause control (WCAG 2.2.2), reduced motion ---------- */
  const heroVideo = document.querySelector('[data-hero-video]');
  const pauseBtn = document.querySelector('[data-hero-pause]');
  if (heroVideo && pauseBtn) {
    const label = pauseBtn.querySelector('.visually-hidden');
    const icon = pauseBtn.querySelector('svg');
    const PAUSE = '<rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/>';
    const PLAY = '<path d="M8 5.5v13l11-6.5z"/>';
    const showState = (paused) => {
      pauseBtn.setAttribute('aria-pressed', String(paused));
      label.textContent = paused ? 'Play background video' : 'Pause background video';
      icon.innerHTML = paused ? PLAY : PAUSE;
    };
    // iOS only autoplays when muted + inline are set as properties, not just attributes.
    heroVideo.muted = true;
    heroVideo.defaultMuted = true;
    heroVideo.playsInline = true;
    if (window.matchMedia('(max-width: 47.99em)').matches) heroVideo.poster = 'assets/video/hero-poster-mobile.jpg';

    const tryPlay = () => heroVideo.play().then(() => showState(false)).catch(() => showState(true));

    // Single-file previews embed the video as a data: URI, which Safari won't stream.
    // Convert it to a blob: URL first. (Not needed on the real site.)
    const inline = [...heroVideo.querySelectorAll('source[src^="data:"]')].find((s) => heroVideo.canPlayType(s.type));
    if (inline) {
      fetch(inline.src).then((r) => r.blob()).then((blob) => {
        heroVideo.src = URL.createObjectURL(blob);
        if (!reduceMotion.matches) tryPlay(); else showState(true);
      });
    } else if (reduceMotion.matches) {
      heroVideo.pause(); showState(true);
    } else {
      tryPlay();
    }

    pauseBtn.addEventListener('click', () => {
      if (heroVideo.paused) tryPlay(); else { heroVideo.pause(); showState(true); }
    });
    reduceMotion.addEventListener('change', (e) => { if (e.matches) { heroVideo.pause(); showState(true); } });
    // Resume after the tab or app comes back (iOS pauses background video)
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && pauseBtn.getAttribute('aria-pressed') === 'false') heroVideo.play().catch(() => {});
    });
  }

  /* ---------- Exploded view: scroll progress 0–1 → layer transforms ----------
     build.py renders the layers separated (the no-JS / reduced-motion view). When motion is
     allowed, data-scroll turns on the tall sticky track and layers start assembled (p = 0).
     SVG transform attributes, not CSS transforms, so it animates in Safari/iOS too.
     --p on the section still drives the progress bar. */
  const exploded = document.querySelector('[data-exploded]');
  if (exploded) {
    const parts = exploded.querySelectorAll('[data-part]');
    const layers = [...exploded.querySelectorAll('[data-shift]')].map((g) => ({
      g, shift: Number(g.dataset.shift), magnets: g.classList.contains('exploded__magnets'),
    }));
    const setLayers = (p) => layers.forEach(({ g, shift, magnets }) => {
      g.setAttribute('transform', `translate(0 ${(shift * p).toFixed(2)})`);
      if (magnets) g.setAttribute('opacity', Math.min(1, Math.max(0, p * 1.6 - 0.3)).toFixed(3));
    });
    let ticking = false;
    const update = () => {
      ticking = false;
      if (!exploded.hasAttribute('data-scroll')) return;
      const rect = exploded.getBoundingClientRect();
      const travel = rect.height - window.innerHeight;
      const p = Math.min(1, Math.max(0, -rect.top / (travel || 1)));
      const eased = Math.min(1, p / 0.7);
      exploded.style.setProperty('--p', eased.toFixed(3));
      setLayers(eased);
      const active = Math.min(parts.length - 1, Math.floor(p * parts.length));
      parts.forEach((el, i) => { el.dataset.active = String(i === active); });
    };
    const onScroll = () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } };
    const setMode = () => {
      if (reduceMotion.matches) {
        exploded.removeAttribute('data-scroll');
        exploded.style.removeProperty('--p');
        setLayers(1);
        parts.forEach((el) => { delete el.dataset.active; });
      } else {
        exploded.setAttribute('data-scroll', '');
        update();
      }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    reduceMotion.addEventListener('change', setMode);
    setMode();
  }

  /* ---------- Cart store ----------
     Shopify: replace with /cart.js, /cart/add.js, /cart/change.js. PROTOTYPE uses localStorage. */
  const CART_KEY = 'a360-cart-v1';
  const cart = {
    read() { try { return JSON.parse(localStorage.getItem(CART_KEY)) || []; } catch { return []; } },
    write(items) { try { localStorage.setItem(CART_KEY, JSON.stringify(items)); } catch { /* storage blocked */ } render(); },
    add(line) {
      const items = cart.read();
      const hit = items.find((i) => i.id === line.id);
      if (hit) hit.quantity = Math.min(10, hit.quantity + line.quantity); else items.push(line);
      cart.write(items);
    },
    set(id, quantity) {
      const items = cart.read().map((i) => (i.id === id ? { ...i, quantity } : i)).filter((i) => i.quantity > 0);
      cart.write(items);
    },
    count() { return cart.read().reduce((n, i) => n + i.quantity, 0); },
  };

  function render() {
    const n = cart.count();
    document.querySelectorAll('[data-cart-count]').forEach((el) => { el.textContent = n; });
    document.querySelectorAll('[data-cart-label]').forEach((el) => { el.textContent = `Cart, ${n} ${n === 1 ? 'item' : 'items'}`; });
    renderCartPage();
  }

  /* ---------- Product: gallery ---------- */
  document.querySelectorAll('[data-gallery]').forEach((gallery) => {
    const main = gallery.querySelector('[data-gallery-main]');
    const thumbs = gallery.querySelectorAll('[data-thumb]');
    thumbs.forEach((thumb) => thumb.addEventListener('click', () => {
      main.src = thumb.dataset.src;
      main.alt = thumb.dataset.alt;
      main.classList.toggle('is-photo', thumb.dataset.photo === 'true');
      thumbs.forEach((t) => t.setAttribute('aria-current', String(t === thumb)));
    }));
  });

  /* ---------- Product: form ---------- */
  document.querySelectorAll('[data-product-form]').forEach((form) => {
    const idInput = form.querySelector('input[name="id"]');
    const output = form.querySelector('[data-colorway-name]');
    const main = document.querySelector('[data-gallery-main]');
    const firstThumb = document.querySelector('[data-thumb]');
    form.querySelectorAll('input[name="colorway"]').forEach((radio) => radio.addEventListener('change', () => {
      if (!radio.checked) return;
      idInput.value = radio.dataset.variantId;
      output.textContent = radio.dataset.label;
      if (main && firstThumb) {
        const src = `assets/img/disc-${radio.value}.svg`;
        const alt = `ANKLE360 disc in ${radio.dataset.label}, top view`;
        Object.assign(firstThumb.dataset, { src, alt });
        firstThumb.querySelector('img').src = src;
        firstThumb.click();
      }
    }));

    const qty = form.querySelector('input[name="quantity"]');
    form.querySelectorAll('[data-qty]').forEach((btn) => btn.addEventListener('click', () => {
      qty.value = Math.max(1, Math.min(10, Number(qty.value || 1) + Number(btn.dataset.qty)));
    }));

    const status = form.querySelector('[data-form-status]');
    const submit = form.querySelector('[type="submit"]');
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (submit.getAttribute('aria-disabled') === 'true') return;
      submit.setAttribute('aria-disabled', 'true');
      status.dataset.state = '';
      status.textContent = 'Adding to cart…';
      try {
        if (window.Shopify && window.Shopify.shop) {
          const res = await fetch('/cart/add.js', { method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' } });
          if (!res.ok) throw new Error((await res.json()).description || 'Could not add to cart.');
        } else {
          const radio = form.querySelector('input[name="colorway"]:checked');
          await new Promise((r) => setTimeout(r, 300));
          cart.add({ id: idInput.value, colorway: radio.value, label: radio.dataset.label, price: Number(form.dataset.price), quantity: Number(qty.value || 1) });
        }
        status.dataset.state = 'success';
        status.innerHTML = 'Added to cart. <a href="cart.html">View cart</a>';
      } catch (err) {
        status.dataset.state = 'error';
        status.textContent = `${err.message} Try again, or refresh the page.`;
      } finally {
        submit.removeAttribute('aria-disabled');
      }
    });
  });

  /* ---------- Cart page (PROTOTYPE; Shopify renders this server-side in main-cart.liquid) ---------- */
  function renderCartPage() {
    const root = document.querySelector('[data-cart-page]');
    if (!root) return;
    const items = cart.read();
    const list = root.querySelector('[data-cart-lines]');
    const empty = root.querySelector('[data-cart-empty]');
    const filled = root.querySelector('[data-cart-filled]');
    empty.hidden = items.length > 0;
    filled.hidden = items.length === 0;
    list.innerHTML = '';
    items.forEach((item) => {
      const li = document.createElement('li');
      li.className = 'cart-line';
      li.innerHTML = `
        <img src="assets/img/disc-${item.colorway}.svg" alt="" width="80" height="80">
        <div class="stack stack--sm">
          <p><a href="product.html">The ANKLE360 Disc</a></p>
          <p class="small muted">${item.label}, ${money(item.price)} each</p>
          <div class="cluster">
            <div class="qty">
              <button type="button" data-step="-1" aria-label="Decrease quantity of ${item.label}">−</button>
              <label class="visually-hidden" for="q-${item.id}">Quantity, ${item.label}</label>
              <input id="q-${item.id}" type="number" min="0" max="10" value="${item.quantity}" inputmode="numeric">
              <button type="button" data-step="1" aria-label="Increase quantity of ${item.label}">+</button>
            </div>
            <button type="button" class="cart-line__remove">Remove<span class="visually-hidden"> ${item.label}</span></button>
          </div>
        </div>
        <p class="price small">${money(item.price * item.quantity)}</p>`;
      li.querySelectorAll('[data-step]').forEach((b) => b.addEventListener('click', () => cart.set(item.id, Math.max(0, Math.min(10, item.quantity + Number(b.dataset.step))))));
      li.querySelector('input').addEventListener('change', (e) => cart.set(item.id, Math.max(0, Math.min(10, Number(e.target.value) || 0))));
      li.querySelector('.cart-line__remove').addEventListener('click', () => cart.set(item.id, 0));
      list.append(li);
    });
    const subtotal = items.reduce((s, i) => s + i.price * i.quantity, 0);
    root.querySelector('[data-subtotal]').textContent = money(subtotal);
    root.querySelector('[data-total]').textContent = money(subtotal);
  }
  const checkout = document.querySelector('[data-checkout]');
  if (checkout) checkout.addEventListener('click', () => {
    document.querySelector('[data-checkout-status]').textContent = 'In the live store, this opens Shopify checkout.';
  });

  /* ---------- Simple forms (PROTOTYPE; Shopify uses {% form 'contact' %} / {% form 'customer' %}) ---------- */
  document.querySelectorAll('[data-demo-form]').forEach((form) => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); return; }
      const status = form.querySelector('[data-form-status]');
      status.dataset.state = 'success';
      status.textContent = form.dataset.success;
      form.reset();
    });
  });

  /* ---------- Device preview (PROTOTYPE page only) ---------- */
  const devices = document.querySelector('[data-devices]');
  if (devices) {
    const select = document.querySelector('[data-device-page]');
    const frames = devices.querySelectorAll('[data-device]');
    const layout = () => frames.forEach((fig) => {
      const [w, h] = fig.dataset.device.split('x').map(Number);
      const scale = Math.min(1, 360 / w, 560 / h);
      const box = fig.querySelector('.device__frame');
      const iframe = fig.querySelector('iframe');
      Object.assign(iframe.style, { width: `${w}px`, height: `${h}px`, transform: `scale(${scale})` });
      Object.assign(box.style, { width: `${w * scale}px`, height: `${h * scale}px` });
    });
    const load = () => frames.forEach((fig) => { fig.querySelector('iframe').src = select.value; });
    select.addEventListener('change', load);
    layout(); load();
  }

  render();
})();
