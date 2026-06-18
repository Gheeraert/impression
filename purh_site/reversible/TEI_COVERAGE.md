# Reversible TEI Coverage

This file maps the current experimental coverage of `purh_site.reversible`.
It documents what the reversible tree and controlled LaTeX grammar cover today;
it is not a request to route this code into the application.

## Elements

| TEI element | TEI -> tree | tree -> TEI | tree -> LaTeX | LaTeX -> tree | Round-trip tested | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `div` | yes | yes | `teiDiv` environment | yes | yes | Preserves mixed block children and attributes such as `type`, `xml:id`. |
| `head` | yes | yes | `teiHead` macro | yes | yes | Used in `div` and `figure` tests. |
| `p` | yes | yes | `teiP` macro | yes | yes | Preserves mixed inline content. |
| `hi` | yes | yes | `teiHi` macro | yes | yes | Preserves `rend`. |
| `note` | yes | yes | `teiNote` macro | yes | yes | Preserves `place`, `xml:id`, and inline position. |
| `ref` | yes | yes | `teiRef` macro | yes | yes | Preserves `target`. |
| `quote` | yes | yes | `teiQuote` environment | yes | yes | Covered through controlled environment tests. |
| `list` | yes | yes | `teiList` environment | yes | yes | Preserves ordered item children. |
| `item` | yes | yes | `teiItem` macro | yes | yes | Preserves `n` and inline children. |
| `figure` | yes | yes | `teiFigure` environment | yes | yes | Preserves `head` and `graphic` children. |
| `graphic` | yes | yes | `teiGraphic` macro | yes | yes | Empty-content macro with attributes such as `target`. |
| `seg` | yes | yes | generic `teiElement` environment | yes | yes | Not specialized; preserved by fallback. |
| unknown TEI element | yes | yes | generic `teiElement` environment | yes | yes | Preserves name, attributes, children, and mixed content. |
| nested unknown TEI element | yes | yes | nested `teiElement` environment | yes | yes | Preserves nesting and order. |
| `title`, `persName`, `placeName`, `date`, `bibl`, `cit` | yes | yes | generic `teiElement` environment | yes | yes | Realistic-fragment proof only; not specialized yet. |

## Covered Attributes

- `xml:id` is stored as the XML namespace attribute and serialized to controlled LaTeX as `xmlid`.
- `xml:lang` is stored as the XML namespace attribute and serialized to controlled LaTeX as `xmllang`.
- `type`
- `subtype`
- `rend`
- `place`
- `target`
- `n`
- `role`
- simple unknown attributes, preserved as options in controlled LaTeX where possible.

## Elements To Cover Next

These elements are not yet specialized in the controlled LaTeX grammar. They
should continue to round-trip through the generic `teiElement` fallback until a
future pass gives them dedicated semantics.

- `title`
- `foreign`
- `term`
- `name`
- `persName`
- `placeName`
- `orgName`
- `date`
- `num`
- `label`
- `ptr`
- `lb`
- `pb`
- `bibl`
- `cit`
- `q`
- `said`
- `table`
- `row`
- `cell`
