import assert from 'node:assert/strict';
import test from 'node:test';
import { catalogReferenceText } from '../lib/catalog-reference.mjs';

test('unknown Fette source slots give quotation guidance without changing raw provenance', () => {
  const part = { brand: 'fette', oem: 'Not listed in source catalog' };
  assert.equal(catalogReferenceText(part), 'Confirm reference during quotation');
  assert.equal(part.oem, 'Not listed in source catalog');
  assert.equal(catalogReferenceText({ brand: 'fette', oem: '' }), 'Confirm reference during quotation');
});

test('confirmed Fette references and other brands retain their existing text', () => {
  assert.equal(catalogReferenceText({ brand: 'fette', oem: '3115546' }), '3115546');
  assert.equal(catalogReferenceText({ brand: 'kikusui', oem: 'Not verified; confirm during quotation' }), 'Not verified; confirm during quotation');
  assert.equal(catalogReferenceText({ brand: 'stokes', oem: 'Not listed in source catalog' }), 'Not listed in source catalog');
});
