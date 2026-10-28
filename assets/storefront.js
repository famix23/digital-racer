/* Shared storefront boundaries: catalog values are text, never executable markup. */
function escapeHTML(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function safeImagePath(value) {
  if (typeof value !== 'string' || !value.trim()) return '';
  const path = value.trim();
  if (/[\\\u0000-\u001f]/.test(path) || path.startsWith('//')) return '';
  if (/^[a-z][a-z0-9+.-]*:/i.test(path)) {
    try { const u = new URL(path); return u.protocol === 'https:' && !u.username && !u.password ? u.href : ''; } catch { return ''; }
  }
  return '/' + path.replace(/^\/+/, '');
}
function matchingProduct(entries, product) {
  return entries.find(p => p.title === product.title && String(p.price) === String(product.price) && p.thumbnail === product.thumbnail)
    || entries.find(p => product.supplier_listing_id && p.id === product.supplier_listing_id);
}
function displayImage(path, size = 480) {
  const safe = safeImagePath(path);
  return (window.DR_IMAGES?.[safe]?.[String(size)]) || safe;
}
