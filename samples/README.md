# Fictional sample documents

These PDFs are invented. The companies, VAT numbers, IBANs, and line items are not real.

They exist so the app can be tried without an API key or any customer files.

| File | What it is | Intended check |
| --- | --- | --- |
| `nordik-inv-10482.pdf` | Clean invoice | Passes on its own; flagged as a duplicate when the copy is in the same batch |
| `baltic-inv-2201.pdf` | Clean invoice | None |
| `greenfield-inv-5519.pdf` | Clean invoice | None |
| `harbor-dn-4412.pdf` | Clean delivery note | None |
| `nordik-inv-10482-dup.pdf` | Same invoice number as the first Nordik file | Duplicate invoice number |
| `baltic-inv-2208-vat.pdf` | Invoice | VAT does not match the line-item rates |
| `harbor-inv-3308-lines.pdf` | Invoice | Line items do not add up to the printed subtotal |
| `greenfield-dn-6620-no-po.pdf` | Delivery note | Missing purchase order number |

Regenerate with:

```bash
python -m extractor.generate_samples
```
