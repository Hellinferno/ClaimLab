import { memo, useLayoutEffect, useMemo, useRef } from 'react';
import katex from 'katex';

/** This module loads only when the lesson actually displays mathematics. */
export const MathText = memo(({ formula }: { formula: string }) => {
  const html = useMemo(() => {
    try {
      return katex.renderToString(formula, {
        throwOnError: false,
        trust: false,
        maxExpand: 100,
        strict: 'error',
      });
    } catch { return null; }
  }, [formula]);
  return html
    ? <span dangerouslySetInnerHTML={{ __html: html }} />
    : <span>{`$${formula}$`}</span>;
});

/** Only KaTeX's untrusted renderer produces HTML. Invalid input stays escaped. */
export const BoardEquation = memo(({ latex }: { latex: string }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLSpanElement>(null);
  const html = useMemo(() => {
    try {
      return katex.renderToString(latex, {
        displayMode: true,
        throwOnError: true,
        trust: false,
        strict: 'error',
        maxExpand: 1000,
      });
    } catch { return null; }
  }, [latex]);
  useLayoutEffect(() => {
    const container = containerRef.current;
    const content = contentRef.current;
    if (!container || !content) return;
    let disposed = false;
    let measuredWidth = -1;
    let pendingFrame: number | null = null;
    let forceFit = false;
    const fit = () => {
      if (disposed) return;
      measuredWidth = container.clientWidth;
      // Measure in the SVG's own CSS coordinates, before its responsive scaling.
      content.style.fontSize = '15px';
      const available = Math.max(1, container.clientWidth - 8);
      const natural = Math.max(1, content.scrollWidth);
      const fontSize = Math.max(10, Math.min(15, Math.floor(15 * available / natural * 10) / 10));
      content.style.fontSize = `${fontSize}px`;
    };
    const scheduleFit = (force = false) => {
      if (disposed || (!force && container.clientWidth === measuredWidth)) return;
      forceFit ||= force;
      if (pendingFrame !== null) return;
      // Font changes can alter the detail panel's height. Never mutate that
      // layout from a ResizeObserver delivery or respond to height alone.
      pendingFrame = requestAnimationFrame(() => {
        pendingFrame = null;
        const shouldFit = forceFit || container.clientWidth !== measuredWidth;
        forceFit = false;
        if (shouldFit) fit();
      });
    };
    const fontsChanged = () => scheduleFit(true);
    fit();
    const observer = new ResizeObserver(() => scheduleFit());
    observer.observe(container);
    // KaTeX's downloaded fonts can change widths after the first measurement.
    void document.fonts.ready.then(fontsChanged);
    document.fonts.addEventListener('loadingdone', fontsChanged);
    return () => {
      disposed = true;
      observer.disconnect();
      if (pendingFrame !== null) cancelAnimationFrame(pendingFrame);
      document.fonts.removeEventListener('loadingdone', fontsChanged);
    };
  }, [html]);
  return html
    ? <div className="board-equation" ref={containerRef}><span className="board-equation-content" ref={contentRef} dangerouslySetInnerHTML={{ __html: html }}/></div>
    : <div className="board-equation">{latex}</div>;
});
