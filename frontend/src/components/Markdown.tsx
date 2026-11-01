import { lazy, Suspense, type ReactNode } from 'react';

const LazyMathText = lazy(() => import('./Math').then(module => ({ default: module.MathText })));

// Order matters: math and code first so their contents are never re-parsed as emphasis.
const INLINE = /(\$[^$\n]+\$|`[^`\n]+`|\*\*[^*\n]+\*\*|\*[^*\s][^*\n]*\*|\[[^\]\n]+\]\(https?:\/\/[^)\s]+\))/g;

/** Inline markdown subset rendered as React elements: no HTML is ever injected. */
export function InlineMarkdown({ text, allowedUrls }: { text: string; allowedUrls?: string[] }) {
  return <>{text.split(INLINE).map((part, index) => {
    if (!part) return null;
    if (part.length > 2 && part.startsWith('$') && part.endsWith('$')) {
      return <Suspense key={index} fallback={<span>{part}</span>}><LazyMathText formula={part.slice(1, -1)}/></Suspense>;
    }
    if (part.startsWith('`') && part.endsWith('`')) return <code key={index}>{part.slice(1, -1)}</code>;
    if (part.startsWith('**') && part.endsWith('**')) return <strong key={index}>{part.slice(2, -2)}</strong>;
    if (part.length > 2 && part.startsWith('*') && part.endsWith('*')) return <em key={index}>{part.slice(1, -1)}</em>;
    const link = part.match(/^\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)$/);
    if (link) {
      const url = link[2];
      const isAllowed = !allowedUrls || allowedUrls.length === 0 || allowedUrls.some(u => {
        try {
          const a = new URL(u).hostname.replace(/^www\./, '');
          const b = new URL(url).hostname.replace(/^www\./, '');
          return a === b;
        } catch {
          return u === url;
        }
      });
      if (isAllowed) {
        return <a key={index} href={url} target="_blank" rel="noopener noreferrer">{link[1]}</a>;
      }
      return <span key={index} title={`Unverified link: ${url}`}>{link[1]}</span>;
    }
    return <span key={index}>{part}</span>;
  })}</>;
}

/** Block markdown subset for tutor prose: paragraphs, lists, quotes, and headings. */
export function Markdown({ text, allowedUrls }: { text: string; allowedUrls?: string[] }) {
  const blocks: ReactNode[] = [];
  const lines = text.replace(/\r\n?/g, '\n').split('\n');
  let index = 0;
  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) { index++; continue; }
    const key = blocks.length;
    const bullet = /^\s*[-*•]\s+/, numbered = /^\s*\d+[.)]\s+/;
    if (bullet.test(line) || numbered.test(line)) {
      const ordered = numbered.test(line), pattern = ordered ? numbered : bullet, items: string[] = [];
      while (index < lines.length && pattern.test(lines[index])) items.push(lines[index++].replace(pattern, ''));
      const List = ordered ? 'ol' : 'ul';
      blocks.push(<List key={key} className="md-list">{items.map((item, i) => <li key={i}><InlineMarkdown text={item} allowedUrls={allowedUrls}/></li>)}</List>);
    } else if (/^\s*>/.test(line)) {
      const quoted: string[] = [];
      while (index < lines.length && /^\s*>/.test(lines[index])) quoted.push(lines[index++].replace(/^\s*>\s?/, ''));
      blocks.push(<blockquote key={key} className="md-quote"><InlineMarkdown text={quoted.join(' ')} allowedUrls={allowedUrls}/></blockquote>);
    } else if (/^#{1,4}\s+/.test(line)) {
      blocks.push(<p key={key} className="md-heading"><InlineMarkdown text={line.replace(/^#{1,4}\s+/, '')} allowedUrls={allowedUrls}/></p>);
      index++;
    } else {
      const paragraph: string[] = [];
      while (index < lines.length && lines[index].trim() && !bullet.test(lines[index]) && !numbered.test(lines[index]) && !/^\s*>/.test(lines[index]) && !/^#{1,4}\s+/.test(lines[index])) paragraph.push(lines[index++]);
      blocks.push(<p key={key}><InlineMarkdown text={paragraph.join(' ')} allowedUrls={allowedUrls}/></p>);
    }
  }
  return <div className="markdown">{blocks}</div>;
}
