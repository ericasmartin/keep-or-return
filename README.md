# Keep or Return?

Paste a link, get a receipt, and find out if it's a keep. I built this to play with Jev.

![Keep or Return demo](keep-or-return.gif)

## How it works

Paste a product link or describe an item and it scores it across five dimensions:

- **Cost Per Wear** — how often you'd realistically wear it
- **Trend vs Timeless** — whether it'll age well or feel dated
- **Material Quality** — fiber quality, sustainability, durability
- **Dopamine vs Love** — impulse buy or intentional purchase
- **Closet Redundancy** — how likely you already own something similar

Then gives you a verdict: **Keep**, **Return**, or **Sleep On It**.

Could be expanded with vision to analyze product images directly.

## Setup

```
cp .env.example .env
# Add your TypeSafe API key
python3 app.py
```


---

Font: [Monument Grotesk](https://abcdinamo.com/typefaces/monument-grotesk) by ABC Dinamo (not included).
