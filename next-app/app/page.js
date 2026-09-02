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
  body = body.replace(/href=["']#about["']/gi, 'href="/about/"');
  body = body.replace(
    'Built for Engineers, Production Teams, Tooling Specialists, and AI Search',
    'Built for Engineers, Production Teams, and Tooling Specialists',
  );
  body = body.replace(
    'The PharmaGlobalEng website will organize your complete keyword research into focused service pages, solution pages, component pages, coating guides, technical articles, case studies, FAQs, and glossary definitions. The homepage introduces the main topics; each supporting page will answer one subject in greater depth without keyword stuffing.',
    'Explore practical technical resources on tablet tooling, sticking and picking, coatings, surface engineering, restoration, replacement parts, and compression performance. Each guide focuses on a specific engineering subject with clear information for pharmaceutical manufacturing teams.',
  );

  const animatedLogoMarkup = `
    <img
      class="pge-animated-logo"
      src="/assets/images/pge-animated-logo.svg"
      width="300"
      height="300"
      loading="eager"
      decoding="async"
      alt="Pharma Global Eng PGE pharmaceutical parts and coating logo"
    >`;

  if (!body.includes('pge-animated-logo')) {
    body = body.replace(
      /(<section class=["']visual-shell["'][^>]*>)/i,
      `$1${animatedLogoMarkup}`,
    );
  }

  const animatedLogoCss = `
.pge-animated-logo {
  position: absolute;
  z-index: 2;
  top: 4.8%;
  right: 2.8%;
  width: clamp(170px, 18vw, 300px);
  height: auto;
  pointer-events: none;
  filter: drop-shadow(0 18px 35px rgba(0,0,0,.6));
}
@media (max-width: 700px) {
  .pge-animated-logo {
    width: 150px;
    top: 2.5%;
    right: 12px;
  }
}
`;

  return { body, css: `${styleBlocks.join('\n')}\n${animatedLogoCss}`, scripts };
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
