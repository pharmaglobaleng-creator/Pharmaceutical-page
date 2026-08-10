import fs from 'node:fs';
import path from 'node:path';

function getAttribute(attrs, name) {
  const match = attrs.match(new RegExp(`${name}=["']([^"']+)["']`, 'i'));
  return match ? match[1] : undefined;
}

function readLegacyHomepage() {
  const sourcePath = path.join(process.cwd(), '..', 'index.html');
  const source = fs.readFileSync(sourcePath, 'utf8');

  const bodyMatch = source.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
  const styleBlocks = [...source.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/gi)].map((m) => m[1]);
  const scripts = [...source.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/gi)].map((m) => ({
    attrs: m[1] || '',
    content: m[2] || '',
  }));

  let body = bodyMatch ? bodyMatch[1] : '';
  body = body.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');

  return { body, css: styleBlocks.join('\n'), scripts };
}

export default function HomePage() {
  const { body, css, scripts } = readLegacyHomepage();

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: css }} />
      <div style={{ display: 'contents' }} dangerouslySetInnerHTML={{ __html: body }} />
      {scripts.map((script, index) => {
        const src = getAttribute(script.attrs, 'src');
        const type = getAttribute(script.attrs, 'type');
        if (src) return <script key={index} src={src} type={type} />;
        return <script key={index} type={type} dangerouslySetInnerHTML={{ __html: script.content }} />;
      })}
    </>
  );
}
