(() => {
  const normalize = value => String(value || '')
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/&/g, ' and ')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();

  const compact = value => normalize(value).replace(/\s+/g, '');

  const distance = (a, b) => {
    if (Math.abs(a.length - b.length) > 2) return 3;
    const previous = Array.from({ length: b.length + 1 }, (_, index) => index);
    for (let i = 1; i <= a.length; i += 1) {
      const current = [i];
      let rowMinimum = current[0];
      for (let j = 1; j <= b.length; j += 1) {
        current[j] = Math.min(current[j - 1] + 1, previous[j] + 1, previous[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
        rowMinimum = Math.min(rowMinimum, current[j]);
      }
      if (rowMinimum > 2) return 3;
      previous.splice(0, previous.length, ...current);
    }
    return previous[b.length];
  };

  const matches = (searchable, query) => {
    const haystack = normalize(searchable);
    const needle = normalize(query);
    if (!needle) return true;
    if (haystack.includes(needle) || compact(haystack).includes(compact(needle))) return true;
    if (/\d/.test(needle)) return false;
    const words = haystack.split(' ');
    return needle.split(' ').every(term => words.some(word => word.startsWith(term) || (term.length >= 4 && distance(word, term) <= 2)));
  };

  window.PGEPartsSearch = { normalize, matches };
})();
