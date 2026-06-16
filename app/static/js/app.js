(() => {
  const root = document.documentElement;
  const body = document.body;

  const setTheme = (theme) => {
    root.setAttribute('data-theme', theme);
    try {
      localStorage.setItem('ev-theme', theme);
    } catch (e) {}
  };

  const getTheme = () => root.getAttribute('data-theme') || 'light';

  const isMobile = () => window.matchMedia('(max-width: 1100px)').matches;

  const palette = document.querySelector('[data-command-palette]');
  const paletteInput = document.querySelector('[data-command-input]');
  const commandTrigger = document.querySelector('[data-command-trigger]');
  const commandItems = palette ? Array.from(palette.querySelectorAll('[data-command-item]')) : [];

  const openPalette = () => {
    if (!palette) return;
    palette.hidden = false;
    requestAnimationFrame(() => paletteInput && paletteInput.focus());
    document.body.classList.add('palette-open');
  };

  const closePalette = () => {
    if (!palette) return;
    palette.hidden = true;
    document.body.classList.remove('palette-open');
    if (paletteInput) paletteInput.value = '';
    commandItems.forEach((item) => (item.hidden = false));
  };

  const filterCommands = (query) => {
    const q = query.trim().toLowerCase();
    commandItems.forEach((item) => {
      const label = (item.dataset.commandLabel || '').toLowerCase();
      item.hidden = q ? !label.includes(q) : false;
    });
  };

  const toggleSidebar = () => {
    if (isMobile()) {
      body.classList.toggle('sidebar-open');
      return;
    }
    body.classList.toggle('sidebar-collapsed');
  };

  const profileTrigger = document.querySelector('[data-action="profile-toggle"]');
  const profilePanel = document.querySelector('.profile-menu__panel');

  const closeProfile = () => {
    if (!profileTrigger || !profilePanel) return;
    profilePanel.hidden = true;
    profileTrigger.setAttribute('aria-expanded', 'false');
  };

  const toggleProfile = () => {
    if (!profileTrigger || !profilePanel) return;
    const open = profilePanel.hidden;
    profilePanel.hidden = !open;
    profileTrigger.setAttribute('aria-expanded', String(open));
  };

  document.addEventListener('click', (event) => {
    const target = event.target;

    if (target.closest('[data-action="sidebar-toggle"]')) {
      event.preventDefault();
      toggleSidebar();
      return;
    }

    if (target.closest('[data-action="theme-toggle"]')) {
      event.preventDefault();
      setTheme(getTheme() === 'dark' ? 'light' : 'dark');
      return;
    }

    if (target.closest('[data-action="profile-toggle"]')) {
      event.preventDefault();
      toggleProfile();
      return;
    }

    if (target.closest('[data-action="close-command"]')) {
      closePalette();
      return;
    }

    const commandItem = target.closest('[data-command-item]');
    if (commandItem && commandItem.dataset.commandUrl) {
      window.location.href = commandItem.dataset.commandUrl;
      return;
    }

    if (!target.closest('.profile-menu')) {
      closeProfile();
    }

    if (palette && !target.closest('.command-panel') && !target.closest('[data-command-trigger]')) {
      closePalette();
    }
  });

  document.addEventListener('keydown', (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      openPalette();
      return;
    }

    if (event.key === 'Escape') {
      closePalette();
      closeProfile();
      body.classList.remove('sidebar-open');
    }
  });

  if (paletteInput) {
    paletteInput.addEventListener('input', (event) => filterCommands(event.target.value));
  }

  if (commandTrigger) {
    commandTrigger.addEventListener('focus', openPalette);
    commandTrigger.addEventListener('input', (event) => {
      openPalette();
      filterCommands(event.target.value);
    });
  }

  const liveFilters = Array.from(document.querySelectorAll('[data-live-filter]'));
  liveFilters.forEach((input) => {
    const targetSelector = input.dataset.liveFilter;
    const target = document.querySelector(targetSelector);
    if (!target) return;
    const items = Array.from(target.querySelectorAll('[data-filter-item]'));

    input.addEventListener('input', () => {
      const q = input.value.trim().toLowerCase();
      items.forEach((item) => {
        const haystack = (item.dataset.filterText || item.textContent || '').toLowerCase();
        item.hidden = q ? !haystack.includes(q) : false;
      });
    });
  });

  document.querySelectorAll('.alert').forEach((alert) => {
    setTimeout(() => {
      alert.style.transition = 'opacity 220ms ease, transform 220ms ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-6px)';
      setTimeout(() => alert.remove(), 240);
    }, 5200);
  });

  document.querySelectorAll('[data-count-up]').forEach((node) => {
    const targetValue = Number(node.dataset.countUp || node.textContent || 0);
    if (!Number.isFinite(targetValue)) return;
    const duration = 900;
    const start = performance.now();
    const tick = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      node.textContent = Math.round(targetValue * (0.25 + progress * 0.75)).toLocaleString();
      if (progress < 1) requestAnimationFrame(tick);
      else node.textContent = targetValue.toLocaleString();
    };
    requestAnimationFrame(tick);
  });
})();
