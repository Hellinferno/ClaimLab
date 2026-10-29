import type { CSSProperties } from 'react';

const paths = {
  book: <><path d="M4 4h6a3 3 0 0 1 3 3v14a4 4 0 0 0-4-3H4z"/><path d="M13 7a3 3 0 0 1 3-3h5v14h-4a4 4 0 0 0-4 3"/></>,
  board: <><rect x="3" y="4" width="18" height="13" rx="2"/><path d="m8 22 4-5 4 5M7 12l4-4 3 3 3-3"/></>,
  flask: <><path d="M9 3h6M10 3v6l-6 10a1.5 1.5 0 0 0 1.3 2h13.4a1.5 1.5 0 0 0 1.3-2L14 9V3M7.5 15h9"/><path d="M10 18h.01M14 12h.01"/></>,
  chart: <><path d="M4 3v17h17M8 15v-4M13 15V7M18 15v-7"/></>,
  arrow: <path d="M5 12h14m-5-5 5 5-5 5"/>,
  upload: <path d="M12 16V3m-5 5 5-5 5 5M4 16v5h16v-5"/>,
  chevron: <path d="m8 10 4 4 4-4"/>,
  spark: <path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5z"/>,
  check: <path d="m5 12 4 4L19 6"/>,
  play: <path d="m9 5 11 7-11 7z"/>,
  close: <path d="m6 6 12 12M6 18 18 6"/>,
  shield: <><path d="m12 3 8 3v6c0 4-8 9-8 9s-8-5-8-9V6z"/><path d="m8 11 3 3 5-6"/></>,
  info: <><circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10h.01"/></>,
} as const;

export function Icon({ name, size = 20, style }: { name: keyof typeof paths; size?: number; style?: CSSProperties }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={style}>{paths[name]}</svg>;
}
