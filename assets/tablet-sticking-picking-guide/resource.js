const citationBox=document.getElementById('citation');
const live=!['localhost','127.0.0.1'].includes(location.hostname)&&location.protocol.startsWith('http');
const source=new URL(location.href);source.hash='';source.search='';
citationBox.value='Jim Demetro. PharmaGlobalEng. “Tablet Sticking and Picking Investigation.” Version 1.5. Updated October 17, 2026.'+(live?' '+source.href:'');
document.getElementById('select-citation').addEventListener('click',()=>{citationBox.focus();citationBox.select();});
document.getElementById('download-bibtex').addEventListener('click',()=>{const text='@misc{demetro2026tablet,\n  author = {Jim Demetro},\n  title = {Tablet Sticking and Picking Investigation},\n  publisher = {PharmaGlobalEng},\n  year = {2026},\n  note = {Version 1.5, updated October 17, 2026}'+(live?',\n  url = {'+source.href+'}':'')+'\n}\n';const u=URL.createObjectURL(new Blob([text],{type:'application/x-bibtex'}));const a=document.createElement('a');a.href=u;a.download='pharmaglobaleng-tablet-guide.bib';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);});
