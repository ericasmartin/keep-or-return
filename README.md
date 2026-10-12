# Keep or Return?

A receipt-style concept that helps you decide whether to keep or return a fashion purchase. I built this to play with Jev.

Paste a product link or describe an item and it scores it across five dimensions:

- **Cost Per Wear** — how often you'd realistically wear it
- **Trend vs Timeless** — whether it'll age well or feel dated
- **Material Quality** — fiber quality, sustainability, durability
- **Dopamine vs Love** — impulse buy or intentional purchase
- **Closet Redundancy** — how likely you already own something similar

Then gives you a verdict: **Keep**, **Return**, or **Sleep On It**.

## Setup

```
cp .env.example .env
# Add your TypeSafe API key
python3 app.py
```

Runs at `http://localhost:8899`
