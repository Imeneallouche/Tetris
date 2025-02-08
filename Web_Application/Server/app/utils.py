# /*//////////////////////////////////////////////////////////////
#                 TRANSPORT COORDINATION WITH PRODUCTION
# //////////////////////////////////////////////////////////////*/
def estimate_warehouse_needs(supplier_id, group):
    """
    Estimate the additional quantities of raw materials (matières premières) needed for the upcoming week.

    The estimation is based on:
      - Historical orders over the past 4 weeks to calculate an average weekly demand per product.
      - The raw material consumption per product (stored in the 'product_matiere' association table).
      - The current stock levels of raw materials (from the Stock table via the 'stock_matiere' association).

    If a supplier is specified (supplier_id), only the raw materials supplied by that supplier are returned.

    Returns:
      A dictionary mapping raw material IDs to the additional quantity needed.
    """
    session = Session()

    # Define the historical window (last 4 weeks)
    four_weeks_ago = datetime.now().date() - timedelta(weeks=4)

    # Query historical orders from the past 4 weeks
    orders = (
        session.query(Command).filter(Command.delivery_date >= four_weeks_ago).all()
    )

    # Calculate total quantity ordered for each product over the period
    product_totals = {}  # {product_id: total_quantity}
    for order in orders:
        for palette in order.palettes:
            pid = palette.product_id
            product_totals[pid] = product_totals.get(pid, 0) + palette.quantity

    # Compute the average weekly demand for each product (divide total by 4 weeks)
    product_weekly_demand = {pid: total / 4.0 for pid, total in product_totals.items()}

    # Now calculate the raw material requirements based on product consumption.
    # The association table 'product_matiere' stores the quantity of raw material consumed per unit of product.
    raw_material_requirements = {}  # {matiere_id: total_required per week}
    for pid, weekly_demand in product_weekly_demand.items():
        # Query the consumption details for this product from the association table.
        query = product_matiere.select().where(product_matiere.c.product_id == pid)
        result = session.execute(query)
        for row in result:
            matiere_id = row.matiere_id
            consumption_per_unit = (
                row.quantity
            )  # Raw material needed per unit of product
            # Accumulate the total weekly requirement for this raw material.
            raw_material_requirements[matiere_id] = raw_material_requirements.get(
                matiere_id, 0
            ) + (weekly_demand * consumption_per_unit)

    # Get current stock of raw materials from the Stock table.
    # Here we assume a single warehouse stock record.
    stock = session.query(Stock).first()
    current_stock = {}  # {matiere_id: quantity_in_stock}
    if stock:
        query = stock_matiere.select().where(stock_matiere.c.stock_id == stock.id)
        result = session.execute(query)
        for row in result:
            matiere_id = row.matiere_id
            quantity_in_stock = row.quantity
            current_stock[matiere_id] = quantity_in_stock

    # Compute the additional raw material needed for each matiere:
    additional_needs = {}
    for matiere_id, required in raw_material_requirements.items():
        in_stock = current_stock.get(matiere_id, 0)
        additional = required - in_stock
        # If we already have enough, no need to order extra.
        if additional < 0:
            additional = 0
        additional_needs[matiere_id] = additional

    # If a supplier is specified, filter the needs to only those raw materials supplied by this supplier.
    if supplier_id:
        supplier = session.query(User).filter(User.id == supplier_id).first()
        if supplier and hasattr(supplier, "materiels"):
            supplied_matiere_ids = {m.id for m in supplier.materiels}
            additional_needs = {
                mat_id: qty
                for mat_id, qty in additional_needs.items()
                if mat_id in supplied_matiere_ids
            }

    session.close()
    return additional_needs
