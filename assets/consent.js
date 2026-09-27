/* consent.js — cookie consent for US visitors, with California (CCPA/CPRA) opt-out.
   US is an opt-out model: essential cookies always run; analytics and marketing are
   on by default unless the visitor opts out or sends Global Privacy Control (GPC).
   "Sale or sharing" is off whenever GPC is present, and can always be turned off
   from "Your privacy choices" in the footer.

   In Shopify: prefer the native banner (Settings > Customer privacy) if its styling is
   acceptable. If you keep this custom banner, the adapter below forwards choices to the
   Customer Privacy API so Shopify pixels and apps respect them.
   Not legal advice: have counsel confirm the final wording and defaults. */
(() => {
  const KEY = 'a360-consent-v1';
  const gpc = navigator.globalPrivacyControl === true;
  const defaults = { analytics: true, marketing: !gpc, sale_of_data: !gpc, preferences: true };

  const banner = document.querySelector('[data-consent-banner]');
  const dialog = document.querySelector('[data-consent-dialog]');
  if (!banner || !dialog) return;
  const form = dialog.querySelector('form');

  const read = () => { try { return JSON.parse(localStorage.getItem(KEY)); } catch { return null; } };
  const write = (c) => { try { localStorage.setItem(KEY, JSON.stringify({ ...c, updated: new Date().toISOString() })); } catch { /* storage blocked: choices last for this page view */ } };

  function apply(consent) {
    /* 1. Shopify Customer Privacy API */
    const privacy = window.Shopify && window.Shopify.customerPrivacy;
    if (privacy && typeof privacy.setTrackingConsent === 'function') {
      privacy.setTrackingConsent(
        { analytics: consent.analytics, marketing: consent.marketing, preferences: consent.preferences, sale_of_data: consent.sale_of_data },
        () => {}
      );
    }
    /* 2. Activate gated third-party scripts: <script type="text/plain" data-consent="analytics"> */
    document.querySelectorAll('script[type="text/plain"][data-consent]').forEach((tag) => {
      if (!consent[tag.dataset.consent] || tag.dataset.activated) return;
      const s = document.createElement('script');
      [...tag.attributes].forEach((a) => { if (a.name !== 'type') s.setAttribute(a.name, a.value); });
      s.text = tag.text;
      tag.dataset.activated = 'true';
      tag.after(s);
    });
    document.dispatchEvent(new CustomEvent('consent:updated', { detail: consent }));
  }

  function save(consent) {
    write(consent);
    apply(consent);
    banner.hidden = true;
  }

  function fillForm(consent) {
    ['analytics', 'marketing', 'sale_of_data'].forEach((k) => { form.elements[k].checked = !!consent[k]; });
  }

  function openChoices() {
    fillForm(read() || defaults);
    dialog.querySelector('[data-gpc-note]').hidden = !gpc;
    dialog.showModal();
  }

  /* Banner buttons */
  banner.querySelector('[data-consent-accept]').addEventListener('click', () => save({ analytics: true, marketing: !gpc, sale_of_data: !gpc, preferences: true }));
  banner.querySelector('[data-consent-reject]').addEventListener('click', () => save({ analytics: false, marketing: false, sale_of_data: false, preferences: true }));
  banner.querySelector('[data-consent-manage]').addEventListener('click', openChoices);

  /* Footer "Your privacy choices" */
  document.querySelectorAll('[data-open-privacy-choices]').forEach((btn) => btn.addEventListener('click', openChoices));

  /* Dialog */
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    save({
      analytics: form.elements.analytics.checked,
      marketing: form.elements.marketing.checked,
      sale_of_data: form.elements.sale_of_data.checked,
      preferences: true,
    });
    dialog.close();
  });
  dialog.querySelector('[data-consent-cancel]').addEventListener('click', () => dialog.close());

  /* Init */
  const stored = read();
  if (stored) {
    apply(gpc ? { ...stored, marketing: false, sale_of_data: false } : stored);
  } else {
    apply(defaults);
    banner.querySelector('[data-gpc-banner-note]').hidden = !gpc;
    banner.hidden = false;
  }
})();
