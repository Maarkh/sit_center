import { describe, it, expect } from 'vitest';
import { indicatorStatus, LIGHT_COLOR } from '../dss';

const ind = (id: string, is_active = true) => ({ id, is_active });

describe('indicatorStatus (cockpit traffic-light)', () => {
  it('is idle for an inactive indicator regardless of deviations', () => {
    expect(indicatorStatus(ind('a', false), new Set(['a']), new Set(['a']))).toBe('idle');
  });

  it('is breach when an active deviation exists', () => {
    expect(indicatorStatus(ind('a'), new Set(['a']), new Set())).toBe('breach');
  });

  it('breach takes precedence over a predictive alert', () => {
    expect(indicatorStatus(ind('a'), new Set(['a']), new Set(['a']))).toBe('breach');
  });

  it('is predict when only a predictive alert exists', () => {
    expect(indicatorStatus(ind('a'), new Set(), new Set(['a']))).toBe('predict');
  });

  it('is ok for an active indicator with neither', () => {
    expect(indicatorStatus(ind('a'), new Set(['b']), new Set(['c']))).toBe('ok');
  });

  it('maps every status to a distinct colour', () => {
    const colors = new Set(Object.values(LIGHT_COLOR));
    expect(colors.size).toBe(4);
    expect(LIGHT_COLOR.breach).toBeTruthy();
  });
});
