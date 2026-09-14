// A missing source reference is not evidence that no other reference exists.
export function catalogReferenceText(part) {
  const reference = String(part.oem || '').trim();
  if (part.brand === 'fette' && (!reference || reference === 'Not listed in source catalog')) {
    return 'Confirm reference during quotation';
  }
  return reference;
}
