// node tools/malachite-index.ts <malachite checkout> <hub>: the hub's index as JSON, each note's
// links resolved by Malachite's own Index (null: a link that resolves to nothing), and the
// unresolved ones listed. For a golden check (docs/golden.md) until Malachite has a headless check.
const [app, root] = process.argv.slice(2);
const { Hub } = await import(`${app}/server/hub.ts`);
const { Index } = await import(`${app}/server/index.ts`);
const ix = new Index(new Hub(root)); ix.build();
const notes = [...ix.items.keys()].filter((p: string) => p.endsWith(".md")).sort();
const links = Object.fromEntries(notes.map((n: string) => [n, ix.links(n).map((l: { path: string | null }) => l.path)]));
const unresolved = notes.flatMap((n: string) => ix.links(n).filter((l: { path: string | null }) => l.path === null).map((l: { link: string }) => `${n}: ${l.link}`));
console.log(JSON.stringify({ notes: notes.length, links, unresolved }));
