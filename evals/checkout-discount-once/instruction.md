Promo orders are exporting totals below the expected amount after a pricing refactor.
Fix the shared cause so both checkout(payload) and export_orders(payloads) apply the
discount exactly once, before tax. Serialization must only format the finalized total
to two decimal places and preserve the account. Direct serialize(order) callers must
also work. Preserve Decimal half-up rounding, non-promo totals, and input objects.
Supported promos and tax regions are defined in src/shop/pricing.py.
