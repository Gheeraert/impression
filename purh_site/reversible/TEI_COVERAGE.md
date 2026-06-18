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
| `q` | yes | yes | `teiQ` macro | yes | yes | Conserves inline quotation content and attributes. |
| `said` | yes | yes | `teiSaid` macro | yes | yes | Conserves attributes such as `who`. |
| `cit` | yes | yes | `teiCit` environment | yes | yes | Conservative serialization, not an interpreted citation model. |
| `bibl` | yes | yes | `teiBibl` environment | yes | yes | Conservative serialization, not structured bibliography handling. |
| `list` | yes | yes | `teiList` environment | yes | yes | Preserves ordered item children. |
| `item` | yes | yes | `teiItem` macro | yes | yes | Preserves `n` and inline children. |
| `figure` | yes | yes | `teiFigure` environment | yes | yes | Preserves `head` and `graphic` children. |
| `graphic` | yes | yes | `teiGraphic` macro | yes | yes | Empty-content macro with attributes such as `target`. |
| `ptr` | yes | yes | `teiPtr` macro | yes | yes | Empty milestone/link element, preserves placement and attributes. |
| `lb` | yes | yes | `teiLb` macro | yes | yes | Empty line-break milestone, preserves placement and attributes. |
| `pb` | yes | yes | `teiPb` macro | yes | yes | Empty page-break milestone, preserves placement and attributes. |
| `table` | yes | yes | `teiTable` environment | yes | yes | Reversible semantic table serialization, not typographic LaTeX. |
| `row` | yes | yes | `teiRow` environment | yes | yes | Preserves cell order and attributes. |
| `cell` | yes | yes | `teiCell` environment | yes | yes | Preserves mixed content and nested paragraphs. |
| `title` | yes | yes | `teiTitle` macro | yes | yes | Preserves attributes such as `level`. |
| `foreign` | yes | yes | `teiForeign` macro | yes | yes | Scholarly inline macro. |
| `term` | yes | yes | `teiTerm` macro | yes | yes | Scholarly inline macro. |
| `name` | yes | yes | `teiName` macro | yes | yes | Scholarly inline macro. |
| `persName` | yes | yes | `teiPersName` macro | yes | yes | Preserves `ref` and similar attributes. |
| `placeName` | yes | yes | `teiPlaceName` macro | yes | yes | Preserves `ref` and similar attributes. |
| `orgName` | yes | yes | `teiOrgName` macro | yes | yes | Scholarly inline macro. |
| `date` | yes | yes | `teiDate` macro | yes | yes | Preserves date attributes such as `when`. |
| `num` | yes | yes | `teiNum` macro | yes | yes | Preserves attributes such as `type`. |
| `label` | yes | yes | `teiLabel` macro | yes | yes | Preserves attributes such as `n`. |
| `seg` | yes | yes | generic `teiElement` environment | yes | yes | Not specialized; preserved by fallback. |
| unknown TEI element | yes | yes | generic `teiElement` environment | yes | yes | Preserves name, attributes, children, and mixed content. |
| nested unknown TEI element | yes | yes | nested `teiElement` environment | yes | yes | Preserves nesting and order. |

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
- `ref`
- `key`
- `when`
- `from`
- `to`
- `notBefore`
- `notAfter`
- `calendar`
- `level`
- `source`
- `corresp`
- `resp`
- `who`
- `cert`
- `ed`
- `facs`
- `rendition`
- `rows`
- `cols`
- simple unknown attributes, preserved as options in controlled LaTeX where possible.

## Elements To Cover Next

These elements are not yet specialized in the controlled LaTeX grammar. They
should continue to round-trip through the generic `teiElement` fallback until a
future pass gives them dedicated semantics.

- finer bibliographic elements such as `author`, `editor`, `publisher`, `biblScope`, and `idno`
