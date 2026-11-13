/* Small progressive enhancements for the public homepage. */
(() => {
  const clock = document.querySelector('#local-clock');
  const year = document.querySelector('#year');
  const menuButton = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#site-nav');
  const randomButton = document.querySelector('#random-button');
  const randomThought = document.querySelector('#random-thought');

  if (year) year.textContent = new Date().getFullYear();

  // Display the visitor's local clock without requiring a location service.
  const updateClock = () => {
    if (!clock) return;
    const now = new Date();
    const time = new Intl.DateTimeFormat('en-GB', {
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    }).format(now);
    clock.textContent = `${time} LOCAL TIME`;
  };
  updateClock();
  window.setInterval(updateClock, 1000);

  // Accessible mobile navigation.
  menuButton?.addEventListener('click', () => {
    const isOpen = menuButton.getAttribute('aria-expanded') === 'true';
    menuButton.setAttribute('aria-expanded', String(!isOpen));
    nav?.classList.toggle('is-open', !isOpen);
    menuButton.querySelector('span').textContent = isOpen ? '＋' : '−';
  });
  nav?.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
    nav.classList.remove('is-open');
    menuButton?.setAttribute('aria-expanded', 'false');
    const symbol = menuButton?.querySelector('span');
    if (symbol) symbol.textContent = '＋';
  }));

  const thoughts = [
    'Somewhere, someone is having the best day of their life and doesn\'t even know it yet.',
    'The internet used to feel like a place. Maybe it still can.',
    'A good song can make an ordinary Tuesday feel cinematic.',
    'You are allowed to make things just because they are fun.',
    'There are probably at least seven tabs open in someone\'s brain right now.',
    'Not every interesting thing needs to become a side project.',
    'Take the scenic route. Even when you are just browsing.'
  ];
  let lastThought = -1;
  randomButton?.addEventListener('click', () => {
    if (!randomThought) return;
    let next = Math.floor(Math.random() * thoughts.length);
    if (thoughts.length > 1) while (next === lastThought) next = Math.floor(Math.random() * thoughts.length);
    lastThought = next;
    randomThought.classList.add('is-changing');
    window.setTimeout(() => {
      randomThought.textContent = thoughts[next];
      randomThought.classList.remove('is-changing');
    }, 140);
  });
})();
