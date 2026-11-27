// node tools/malachite-index.ts <malachite checkout> <hub>: the hub's index as JSON, by Malachite's own
// code: each note's links (null: one that resolves to nothing), backlinks, tags, number of code cells and
// callout kinds (an alias read as its kind, an unknown one as a note), and the unresolved links listed.
// For a golden check (docs/golden.md) until Malachite has a headless check.
import fs from "node:fs";
const [app, root] = process.argv.slice(2);
const { Hub } = await import(`${app}/server/hub.ts`);
const { Index } = await import(`${app}/server/index.ts`);
const { calloutKind } = await import(`${app}/client/callouts.ts`);
const ix = new Index(new Hub(root)); ix.build();
const notes = [...ix.items.keys()].filter((p: string) => p.endsWith(".md")).sort();
const each = (f: (n: string) => unknown) => Object.fromEntries(notes.map((n: string) => [n, f(n)]));
type Link = { link: string; path: string | null };
// ponytail: a callout is a `> [!kind]` line, also inside a code fence; none of the hubs has one there
const callouts = (n: string) => [...fs.readFileSync(`${root}/${n}`, "utf8").matchAll(/^>\s*\[!([\w-]+)\]/gm)].map((m) => calloutKind(m[1]).kind);
console.log(JSON.stringify({
  notes: notes.length,
  links: each((n) => ix.links(n).map((l: Link) => l.path)),
  backlinks: each((n) => ix.backlinks(n)),
  tags: each((n) => ix.items.get(n).tags),
  cells: each((n) => ix.items.get(n).cells),
  callouts: each(callouts),
  unresolved: notes.flatMap((n: string) => ix.links(n).filter((l: Link) => l.path === null).map((l: Link) => `${n}: ${l.link}`)),
}));
