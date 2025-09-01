def build_spatiotemporal_query(start_date, end_date, bbox):
    """
    Returns a SQL string to filter by date range.
    Since we don't have spatial indexing yet, this just filters by time.
    Expects bbox as (xmin, ymin, xmax, ymax) for future spatial filtering.
    """
    query = """
    SELECT * FROM maps
    WHERE acquisition_datetime BETWEEN :start AND :end
    ORDER BY acquisition_datetime
    """
    return query
