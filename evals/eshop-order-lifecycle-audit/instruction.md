# Review checkout writes and order-read boundaries

Audit the frozen eShopOnWeb application under `/app/src/eshop`. Trace from
`CheckoutModel.OnPost` to `OrderService.CreateOrderAsync`, and from
`OrderController.Detail` through mediator dispatch to
`GetOrderDetailsHandler.Handle`. Compare the order-list path too. Review quantity
updates, order snapshots, dependency bindings, and the predicates used for reads.
This is a read-only source review, not a repair or a live-service security test.

Write `/app/src/order-lifecycle.json` with exactly `locations` and `decisions`.
Each location is `{"file":"eshop/src/path/File.cs","symbol":"Class.Method"}`.
Paths are relative to `/app/src`; omit namespaces and generic type arguments.
Spell a constructor `Class.Class`. Identify the member containing each
responsibility below. Do not include line numbers.

Include these location keys:

| Key | Responsibility (identify the containing member) |
| --- | --- |
| `checkout_quantities` | Checkout submits posted quantities to the basket service. |
| `checkout_order` | Checkout invokes the order service after quantities are updated. |
| `checkout_delete` | Checkout deletes the basket after order creation. |
| `quantity_write` | Basket item setter writes its validated quantity. |
| `remove_empty` | Basket removes zero-quantity items. |
| `empty_guard` | Custom basket guard throws for an empty checkout. |
| `catalog_snapshot` | Order service constructs the ordered-item description snapshot. |
| `order_line` | Order service constructs the order line using its selected price and quantity. |
| `order_store` | Order service adds the assembled order through its repository. |
| `total_accumulation` | Order aggregate adds one line's contribution to its total. |
| `repository_binding` | Web configuration binds the open generic write repository to its implementation. |
| `order_service_binding` | Web configuration binds the order-service interface. |
| `mediator_registration` | Web configuration registers mediator handlers from an application assembly. |
| `detail_dispatch` | Order controller sends the order-detail request through the mediator. |
| `detail_lookup` | Detail handler queries its repository using the constructed specification. |
| `detail_predicate` | Detail specification applies its order-selection predicate. |
| `list_lookup` | My-orders handler queries its repository using the customer specification. |
| `list_predicate` | Customer specification applies its order-selection predicate. |

Derive these `decisions`:

- `checkout_call_order`: array of `set_quantities`, `create_order`, `delete_basket`
  in the successful POST's order.
- `quantity_guard_minimum`: integer lower bound supplied to the quantity setter's
  out-of-range guard.
- `zero_quantity_removed`: boolean, after basket-service quantity updates.
- `unit_price_origin`: `basket` or `current_catalog` when creating order lines.
- `display_fields_origin`: `catalog_snapshot` or `live_catalog_lookup` for product
  names and pictures in the later order-detail projection.
- `total_uses_order_lines`: boolean; total uses saved order-line price × units.
- `adding_existing_item_reprices`: boolean, when adding more of an existing
  catalog item to a basket at a different supplied unit price.
- `detail_handler_uses_username`: boolean, whether the detail handler uses its
  request's `UserName` in selecting the order.
- `list_spec_filters_buyer`: boolean; explicit BuyerId predicate in the list spec.
- `detail_spec_filters_buyer`: boolean; explicit BuyerId predicate in the detail
  spec. Report the source as written, not what a secure implementation ought to do.
- `missing_detail_response`: `BadRequest`, `NotFound`, or `View` at the controller
  when the detail handler returns null.
- `empty_checkout_redirect`: exact page path returned for the custom empty-basket
  checkout exception.
- `delete_after_create_throws`: boolean; does this POST attempt basket deletion
  if order creation throws?
- `order_service_lifetime`: `singleton`, `scoped`, or `transient` in web DI setup.
- `explicit_checkout_transaction`: boolean; do the checkout POST and order-service
  method explicitly create a transaction spanning their repository operations?

Assume ordinary successful dependencies except the named error cases. The last
question concerns explicit application code, not inferred database atomicity or
transactions inside unbundled dependencies. This fixture is an archived sample,
not a deployment recommendation. Do not modify `src/eshop`. Scratch files elsewhere
in `/app` are allowed; no .NET installation, database, or network is required.
