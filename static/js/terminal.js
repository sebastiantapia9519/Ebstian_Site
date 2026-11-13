/* Ebstian Shell — a safe, client-side command interpreter. */
(() => {
  const form = document.querySelector('#terminal-form');
  const input = document.querySelector('#terminal-input');
  const output = document.querySelector('#terminal-output');
  const clearButton = document.querySelector('#terminal-clear');
  if (!form || !input || !output) return;

  const commandNames = ['help', 'about', 'whoami', 'date', 'music', 'artists', 'collections', 'experiments', 'random', 'login', 'open', 'echo', 'clear'];
  const history = [];
  let historyIndex = 0;
  const descriptions = {
    help: 'show available commands', about: 'a little about this place', whoami: 'who is browsing?',
    date: 'show the current date and time', music: 'jump to the soundtrack', artists: 'list the artists in rotation',
    collections: 'browse things worth keeping', experiments: 'enter the digital lab', random: 'find something unexpected',
    login: 'access the private workspace', open: 'open a section (music/lab/random/collections)',
    echo: 'repeat a message', clear: 'clear the terminal'
  };

  // Always render terminal output as text; user input is never interpreted as HTML.
  const write = (text, className = '') => {
    const line = document.createElement('p');
    if (className) line.className = className;
    line.textContent = text;
    output.appendChild(line);
    output.scrollTop = output.scrollHeight;
  };
  const goTo = id => {
    const target = document.getElementById(id);
    if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };
  const run = raw => {
    const normalized = raw.trim().replace(/\s+/g, ' ');
    if (!normalized) return;
    write(`visitor@ebstian:~$ ${normalized}`, 'terminal-command-line');
    const [name, ...args] = normalized.split(' ');
    const argument = args.join(' ');
    switch (name.toLowerCase()) {
      case 'help':
        write('AVAILABLE COMMANDS');
        commandNames.forEach(command => write(`  ${command.padEnd(14)} ${descriptions[command]}`));
        write('Tip: try `open music` or `open random`.');
        break;
      case 'about':
        write('Ebstian is an independent corner of the internet by Sebastián.');
        write('Developer, music listener, curious human. Built in Monterrey, MX.');
        break;
      case 'whoami': write('visitor — curious human, currently browsing ebstian.com.'); break;
      case 'date': write(new Date().toString()); break;
      case 'music': goTo('music'); write('Opening the soundtrack...'); break;
      case 'artists':
        ['José Madero', 'PXNDX', 'Simple Plan', 'Serbia', 'Nunca Jamás', 'No Te Va Gustar', 'Sabino', 'Genitallica', 'Imagine Dragons', 'Love of Lesbian', 'Los Caligaris'].forEach((artist, index) => write(`${String(index + 1).padStart(2, '0')}  ${artist}`));
        break;
      case 'collections': goTo('collections'); write('Opening the archive...'); break;
      case 'experiments': case 'lab': goTo('lab'); write('Entering the lab...'); break;
      case 'random': goTo('random'); document.querySelector('#random-button')?.click(); write('Something unexpected is waiting above.'); break;
      case 'open': {
        const sections = { music: 'music', lab: 'lab', experiments: 'lab', random: 'random', collections: 'collections', about: 'about', terminal: 'terminal' };
        const section = sections[argument.toLowerCase()];
        if (section) { goTo(section); write(`Opening ${argument}...`); }
        else write('Usage: open music | lab | random | collections | about', 'terminal-error');
        break;
      }
      case 'login': write('Redirecting to the private workspace...'); window.setTimeout(() => { window.location.assign('/login'); }, 220); break;
      case 'echo': write(argument); break;
      case 'clear': output.replaceChildren(); break;
      case 'sudo': write('Nice try. This is a personal website, not your server.'); break;
      default: write(`Command not found: ${name}. Type "help" to see available commands.`, 'terminal-error');
    }
  };

  form.addEventListener('submit', event => {
    event.preventDefault();
    const value = input.value;
    if (value.trim()) { history.push(value); historyIndex = history.length; }
    input.value = '';
    run(value);
  });
  input.addEventListener('keydown', event => {
    if (event.key === 'ArrowUp') {
      event.preventDefault();
      if (historyIndex > 0) input.value = history[--historyIndex];
    } else if (event.key === 'ArrowDown') {
      event.preventDefault();
      if (historyIndex < history.length - 1) input.value = history[++historyIndex];
      else { historyIndex = history.length; input.value = ''; }
    } else if (event.key === 'Tab') {
      event.preventDefault();
      const prefix = input.value.trim().toLowerCase();
      const matches = commandNames.filter(command => command.startsWith(prefix));
      if (matches.length === 1) input.value = matches[0];
      else if (matches.length > 1) write(matches.join('   '));
    }
  });
  clearButton?.addEventListener('click', () => { output.replaceChildren(); input.focus(); });
  document.querySelectorAll('[data-command]').forEach(button => button.addEventListener('click', () => {
    run(button.dataset.command || ''); input.focus();
  }));
})();
