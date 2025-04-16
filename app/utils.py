def build_spatiotemporal_query(start_date, end_date, bbox):
    """
    Returns a SQL string to filter by date range and bounding box.
    Expects bbox as (xmin, ymin, xmax, ymax).
    """
    query = """
    SELECT * FROM maps
    WHERE acquisition_datetime BETWEEN :start AND :end
      AND ST_Intersects(
            ST_SetSRID(ST_MakeBox2D(
                ST_Point(:xmin, :ymin),
                ST_Point(:xmax, :ymax)
            ), 4326),
            ST_SetSRID(ST_MakePoint(0, 0), 4326) + geom
        )
    """
    return query
