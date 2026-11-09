/**
 * Canonicalize legacy /product?item= and /product.html?item= links.
 *
 * The public storefront already has an indexable /p/<slug>/ page for each
 * catalog item. Keep its generic product template noindex as a safe fallback
 * for unknown or ambiguous titles. Redirect ONLY recognized GET/HEAD titles.
 */
const CANONICAL_ORIGIN = "https://www.digitalracer.store";
const LEGACY_TITLES = new Map([
  [
    "X ULTIMATES 👑 ANUKHARA X-SUIT (⭐⭐⭐) ❄️ M416 ROARING IMMOLATION MAXX + UMP ANIVERSARRY COMBO (2x LOOT CRATE) 🏎️ LOTUS EMIRA SPORTS",
    "/p/pubg-mobile-account-anukhara-x-suit-3-m416-roaring-immolation-max/",
  ],
  [
    "( Karambit ) And ( Nine-Tails ) 2 In One Deal 🔥pubg mobile card collection",
    "/p/pubg-mobile-karambit-nine-tails-card-bundle-2-in-1-deal-instant/",
  ],
  [
    "Near to 98 Collection Account World Top 100 Account | Most Rarest Inventory every ||",
    "/p/pubg-mobile-world-top-100-account-near-98-collection-13-maxed-x-suits/",
  ],
]);

const SAFE_PRODUCT_ROUTE = /^\/p\/[a-z0-9]+(?:-[a-z0-9]+)*\/$/;

export function canonicalProductRoute(title, manifest) {
  if (typeof title !== "string" || !title || title.length > 2048 || !Array.isArray(manifest)) {
    return null;
  }
  const matches = manifest.filter(row => row && row.title === title && SAFE_PRODUCT_ROUTE.test(row.url));
  if (matches.length === 1) return matches[0].url;
  if (matches.length > 1) return null; // Multiple listings: do not guess which to send buyers to.
  const alias = LEGACY_TITLES.get(title);
  // Avoid stale aliases when the original listing has been removed.
  return alias && manifest.some(row => row.url === alias) ? alias : null;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (
      (request.method === "GET" || request.method === "HEAD") &&
      (url.pathname === "/product" || url.pathname === "/product.html")
    ) {
      const title = url.searchParams.get("item");
      if (title && title.length <= 2048) {
        try {
          const manifestURL = new URL("/p/index.json", url.origin);
          const response = await env.ASSETS.fetch(new Request(manifestURL));
          if (response.ok) {
            const route = canonicalProductRoute(title, await response.json());
            if (route) {
              return new Response(null, {
                status: 301,
                headers: {
                  Location: CANONICAL_ORIGIN + route,
                  "Cache-Control": "public, max-age=300",
                },
              });
            }
          }
        } catch {
          // A temporary asset read failure must not break normal product browsing.
        }
      }
    }
    return env.ASSETS.fetch(request);
  },
};
