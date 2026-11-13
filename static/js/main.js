/* Public homepage interactions. No external runtime dependencies. */
(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const clock = $('#local-clock');
  const year = $('#year');
  const menuButton = $('.menu-toggle');
  const nav = $('#navigation');
  const randomButton = $('#random-button');
  const randomThought = $('#random-thought');
  const randomCount = $('#random-count');
  const orbitButton = $('#orbit-button');

  if (year) year.textContent = String(new Date().getFullYear());

  // Visitor-local clock: no geolocation or tracking required.
  const updateClock = () => {
    if (!clock) return;
    clock.textContent = new Intl.DateTimeFormat('en-GB', {
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    }).format(new Date());
  };
  updateClock();
  window.setInterval(updateClock, 1000);

  // Accessible mobile navigation with correct expanded state.
  menuButton?.addEventListener('click', () => {
    const open = menuButton.getAttribute('aria-expanded') === 'true';
    menuButton.setAttribute('aria-expanded', String(!open));
    nav?.classList.toggle('is-open', !open);
    const symbol = menuButton.querySelector('span');
    if (symbol) symbol.textContent = open ? '＋' : '−';
  });
  nav?.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
    nav.classList.remove('is-open');
    menuButton?.setAttribute('aria-expanded', 'false');
    const symbol = menuButton?.querySelector('span');
    if (symbol) symbol.textContent = '＋';
  }));

  const thoughts = [
    'You are allowed to make things just because they are fun.',
    'The internet used to feel like a place. Maybe it still can.',
    'A good song can make an ordinary Tuesday feel cinematic.',
    'Somewhere, someone is having the best day of their life and does not even know it yet.',
    'Not every interesting thing needs to become a side project.',
    'There are probably seven tabs open in somebody’s brain right now.',
    'Take the scenic route. Even when you are just browsing.',
    'The best bookmark is the one you actually visit again.',
    'Build something small. Make it weird. Put it on the internet.'
  ];
  let lastThought = -1;
  let thoughtNumber = 1;
  randomButton?.addEventListener('click', () => {
    if (!randomThought) return;
    let next = Math.floor(Math.random() * thoughts.length);
    while (thoughts.length > 1 && next === lastThought) next = Math.floor(Math.random() * thoughts.length);
    lastThought = next;
    thoughtNumber += 1;
    randomThought.classList.add('is-changing');
    window.setTimeout(() => {
      randomThought.textContent = thoughts[next];
      randomThought.classList.remove('is-changing');
      if (randomCount) randomCount.textContent = `NO. ${String(thoughtNumber).padStart(3, '0')}`;
    }, 150);
  });

  // Small generative visual experiment; intentionally decorative and local-only.
  orbitButton?.addEventListener('click', () => orbitButton.classList.toggle('is-disturbed'));
})();
