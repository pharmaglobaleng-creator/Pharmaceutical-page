(() => {
  const makerCards = [...document.querySelectorAll('.makers .maker')];
  const machinesSection = document.getElementById('machines');
  const machineFilter = document.querySelector('.machine-filter');
  const machineGrid = document.querySelector('.machines');
  const machineCrumb = machinesSection?.querySelector('.crumbs');
  const componentHeading = document.querySelector('.components')?.closest('.section')?.querySelector('.section-head h2');
  const exactSection = document.querySelector('.exact-section');

  if (!makerCards.length || !machinesSection || !machineFilter || !machineGrid) return;

  const catalogs = {
    Korsch: {
      models: ['300', '800', 'XL-400', 'XL-800'],
      live: { '300': '/parts/korsch/korsch-300/' },
      images: ['003', '008', '009', '010']
    },
    Fette: {
      models: ['2100', '3100', 'P2090', 'P3000', 'P3090', 'P3200'],
      live: {},
      images: ['015', '016', '017', '018', '019', '020']
    },
    Kilian: {
      models: ['S-250', 'T-400'],
      live: {},
      images: ['021', '022']
    },
    Manesty: {
      models: ['Mark IV', 'Novapress', 'Nova Diamond'],
      live: {},
      images: ['023', '024', '025']
    },
    Riva: {
      models: ['Parts Support'],
      live: {},
      images: ['026']
    }
  };

  const brandForCard = card => {
    if (card.querySelector('.brand-korsch')) return 'Korsch';
    if (card.querySelector('.brand-fette')) return 'Fette';
    if (card.querySelector('.brand-kilian')) return 'Kilian';
    if (card.querySelector('.brand-manesty')) return 'Manesty';
    if (card.querySelector('.brand-riva')) return 'Riva';
    return card.textContent.trim().split(/\s+/)[0];
  };

  const imgFor = (brand, index) => {
    const n = catalogs[brand].images[index % catalogs[brand].images.length];
    return `/assets/images/parts/korsch-300/pge-k300-${n}.webp`;
  };

  function setMakerState(brand) {
    makerCards.forEach(card => {
      const selected = brandForCard(card) === brand;
      card.classList.toggle('selected', selected);
      card.setAttribute('aria-current', selected ? 'true' : 'false');
      card.href = '#machines';
    });
  }

  function renderBrand(brand) {
    const data = catalogs[brand] || catalogs.Korsch;
    setMakerState(brand);

    if (machineCrumb) machineCrumb.textContent = `Home › Parts Store › ${brand} →`;

    machineFilter.innerHTML = `
      <h3>Filter Machines</h3>
      <div class="filter-search">⌕ <span>Search machine model...</span></div>
      <a class="filter-active" href="#machines">All Models <b>›</b></a>
      ${data.models.map(model => `<a href="#machines" data-store-model="${model}">${brand} ${model} <b>›</b></a>`).join('')}
    `;

    machineGrid.innerHTML = data.models.slice(0, 4).map((model, index) => {
      const liveUrl = data.live[model];
      const action = liveUrl ? 'View Parts ›' : 'Select Model ›';
      const note = liveUrl ? 'Catalog available' : 'Model-specific parts support';
      return `<a class="machine" href="${liveUrl || '#machines'}" data-store-brand="${brand}" data-store-model="${model}">
        <div class="machine-photo"><img src="${imgFor(brand, index)}" alt="Representative ${brand} ${model} parts support imagery"></div>
        <h3>${brand} ${model}</h3><p>${note}</p><span>${action}</span>
      </a>`;
    }).join('');

    bindModelClicks(brand);
    machinesSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function showModelState(brand, model) {
    const liveUrl = catalogs[brand]?.live?.[model];
    if (liveUrl) {
      window.location.href = liveUrl;
      return;
    }

    machineFilter.querySelectorAll('[data-store-model]').forEach(link => {
      link.classList.toggle('filter-active', link.dataset.storeModel === model);
    });
    machineGrid.querySelectorAll('[data-store-model]').forEach(card => {
      card.classList.toggle('selected', card.dataset.storeModel === model);
    });

    if (componentHeading) {
      componentHeading.innerHTML = `<span>3.</span> CHOOSE THE COMPONENT <em>(${brand.toUpperCase()} ${model.toUpperCase()})</em>`;
    }

    if (exactSection) {
      const crumb = exactSection.querySelector('.crumbs');
      if (crumb) crumb.textContent = `Home › Parts Store › ${brand} › ${brand} ${model}`;
      const table = exactSection.querySelector('.results-table');
      if (table) table.innerHTML = `<div style="padding:28px;text-align:center"><strong>${brand} ${model} parts selection</strong><p style="color:#9aa9bd">This model catalog is being prepared. Stay in the Parts Store and use Expert Help to request the exact component you need.</p><a href="/contact.html?manufacturer=${encodeURIComponent(brand)}&model=${encodeURIComponent(model)}" style="display:inline-block;margin-top:10px;padding:9px 14px;border-radius:5px;background:linear-gradient(135deg,#6e2ce9,#9e42ff)">Request Parts for ${brand} ${model}</a></div>`;
    }

    document.querySelector('.components')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function bindModelClicks(brand) {
    machineFilter.querySelectorAll('[data-store-model]').forEach(link => {
      link.addEventListener('click', event => {
        event.preventDefault();
        showModelState(brand, link.dataset.storeModel);
      });
    });
    machineGrid.querySelectorAll('[data-store-model]').forEach(card => {
      card.addEventListener('click', event => {
        const model = card.dataset.storeModel;
        const liveUrl = catalogs[brand]?.live?.[model];
        if (!liveUrl) {
          event.preventDefault();
          showModelState(brand, model);
        }
      });
    });
  }

  makerCards.forEach(card => {
    card.addEventListener('click', event => {
      event.preventDefault();
      renderBrand(brandForCard(card));
    });
  });

  document.querySelectorAll('.popular a').forEach(link => {
    if (/Fette/i.test(link.textContent)) {
      link.href = '#machines';
      link.addEventListener('click', event => {
        event.preventDefault();
        renderBrand('Fette');
      });
    }
  });

  bindModelClicks('Korsch');
})();
