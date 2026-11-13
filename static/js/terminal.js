/* Ebstian shell: deliberately small, client-side command router. */
(() => {
  const form = document.querySelector('#terminal-form');
  const input = document.querySelector('#terminal-input');
  const output = document.querySelector('#terminal-output');
  const clearButton = document.querySelector('#terminal-clear');
  if (!form || !input || !output) return;

  const commands = ['help', 'about', 'music', 'random', 'collections', 'experiments', 'login', 'clear'];
  const write = (text, className = '') => {
    const line = document.createElement('p');
    if (className) line.className = className;
    line.textContent = text;
    output.appendChild(line);
    output.scrollTop = output.scrollHeight;
  };
  const run = raw => {
    const command = raw.trim().toLowerCase().replace(/\s+/g, ' ');
    if (!command) return;
    write(`visitor@ebstian:~$ ${raw}`, 'terminal-command-line');
    const [name, ...args] = command.split(' ');
    switch (name) {
      case 'help':
        write('AVAILABLE COMMANDS');
        commands.forEach(item => write(`  ${item.padEnd(14)} ${descriptions[item]}`));
        write('Tip: use the section names to explore this little corner.');
        break;
      case 'about':
        write('Ebstian is an independent corner of the internet by Sebastián.');
        write('A little bit of music, experiments, collections and curiosity.');
        break;
      case 'music': location.hash = 'music'; write('Opening the soundtrack...'); break;
      case 'collections': location.hash = 'collections'; write('Opening the archive...'); break;
      case 'experiments': case 'lab': location.hash = 'experiments'; write('Entering the lab...'); break;
      case 'random':
        location.hash = 'random';
        document.querySelector('#random-button')?.click();
        write('Something unexpected is waiting above.');
        break;
      case 'login':
        write('Redirecting to the private workspace...');
        window.setTimeout(() => { window.location.href = '/login'; }, 250);
        break;
      case 'clear': output.replaceChildren(); break;
      case 'sudo': write('Nice try. This is a personal website, not your server.'); break;
      case 'whoami': write('visitor — curious human, currently browsing ebstian.com.'); break;
      case 'date': write(new Date().toString()); break;
      case 'echo': write(args.join(' ')); break;
      default: write(`Command not found: ${name}. Type "help" to see available commands.`, 'terminal-error');
    }
  };
  const descriptions = {
    help: 'show available commands', about: 'a little about this place',
    music: 'explore the soundtrack', random: 'find something unexpected',
    collections: 'browse things worth keeping', experiments: 'enter the digital lab',
    login: 'access the private workspace', clear: 'clear the terminal'
  };

  form.addEventListener('submit', event => {
    event.preventDefault();
    const value = input.value;
    input.value = '';
    run(value);
  });
  clearButton?.addEventListener('click', () => { output.replaceChildren(); input.focus(); });
  document.querySelectorAll('[data-command]').forEach(button => {
    button.addEventListener('click', () => { run(button.dataset.command || ''); input.focus(); });
  });
})();
