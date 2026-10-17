const guideUrl=new URL('index.html',location.href);guideUrl.search='';guideUrl.hash='';
const embedUrl=new URL('calculator-embed.html',guideUrl);
const local=['localhost','127.0.0.1'].includes(location.hostname)||location.protocol==='file:';
document.getElementById('embed-code').value=local?'Embed code becomes available at the published page address. Open the standalone calculator above to test it here.':`<iframe src="${embedUrl.href}" title="Tablet tooling break-even calculator by PharmaGlobalEng" width="100%" height="1100" loading="lazy" style="border:0"></iframe>
<p>Source: <a href="${guideUrl.href}">PharmaGlobalEng tablet sticking and picking investigation guide</a></p>`;
document.getElementById('embed-status').textContent=local?'Local demonstration: other websites cannot access this computer’s preview. Publish the resource before distributing embed code.':'Keep the source link visible and give the iframe enough height for keyboard navigation.';
document.querySelectorAll('[data-select]').forEach(b=>b.addEventListener('click',()=>{const t=document.getElementById(b.dataset.select);t.focus();t.select();}));
