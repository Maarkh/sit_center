import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useIsMobile } from '../useBreakpoint';

describe('useIsMobile', () => {
  const originalInnerWidth = window.innerWidth;

  beforeEach(() => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: originalInnerWidth,
    });
  });

  it('returns true when window width < 768', () => {
    Object.defineProperty(window, 'innerWidth', { value: 500 });
    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(true);
  });

  it('returns false when window width >= 768', () => {
    Object.defineProperty(window, 'innerWidth', { value: 1024 });
    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(false);
  });

  it('returns false when window width is exactly 768', () => {
    Object.defineProperty(window, 'innerWidth', { value: 768 });
    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(false);
  });

  it('responds to window resize events', () => {
    Object.defineProperty(window, 'innerWidth', { value: 1024 });
    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(false);

    act(() => {
      Object.defineProperty(window, 'innerWidth', { value: 500 });
      window.dispatchEvent(new Event('resize'));
    });
    expect(result.current).toBe(true);

    act(() => {
      Object.defineProperty(window, 'innerWidth', { value: 900 });
      window.dispatchEvent(new Event('resize'));
    });
    expect(result.current).toBe(false);
  });

  it('supports custom breakpoint', () => {
    Object.defineProperty(window, 'innerWidth', { value: 1000 });
    const { result } = renderHook(() => useIsMobile(1024));
    expect(result.current).toBe(true);
  });
});
