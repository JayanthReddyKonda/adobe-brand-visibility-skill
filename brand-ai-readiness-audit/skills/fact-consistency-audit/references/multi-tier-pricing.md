# False Positive Decision Table: Multi-Tier Pricing Contexts

## Signal
Multiple distinct price values (e.g. $10, $25, $50, $250) appear on the same domain or pricing page.

## Do NOT Report As Defect When:
- Prices correspond to distinct subscription tiers (e.g. "Starter Tier: $10/mo" vs "Pro Tier: $50/mo" vs "Enterprise: $250/mo").
- Prices reflect monthly vs annual billing discounts (e.g. "$12 billed monthly" vs "$10/mo billed annually").
- Prices refer to different individual products in a product catalog or category overview page.
- Prices represent volume discount brackets or regional currency localizations.

## Report As Defect ONLY When:
- **Verified Cross-Page Contradiction**: The exact same product/tier (e.g. "Velocity X9 Drone") is stated at one price on the main product landing page (e.g. "₹5,499") and a different contradictory price on a secondary/legacy page (e.g. "₹4,999") without clear discount or archival context.
- **Markup Discrepancy**: The visible on-page price states "$49", but the JSON-LD `offers.price` schema states `"99"`.

