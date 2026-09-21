from backend.app.services.content_analysis_service import content_analysis_service

def test_content_analysis_duplicate_detection():
    existing_articles = [
        {"id": 1, "title": "How to Build a Simple Skincare Routine", "primary_keyword": "simple skincare routine"},
        {"id": 2, "title": "Vitamin C Serum Benefits and How to Use It", "primary_keyword": "vitamin c serum benefits"}
    ]

    # Query directly overlapping with existing Vitamin C article
    result = content_analysis_service.check_existing_content(
        "Vitamin C Serum Benefits Guide",
        existing_articles=existing_articles
    )
    assert result["exists"] is True
    assert result["matched_content_id"] == 2
    assert "Vitamin C Serum Benefits and How to Use It" in result["similarity_reason"]

    # Query for product without existing article (e.g. Niacinamide Serum)
    result_new = content_analysis_service.check_existing_content(
        "Niacinamide Serum",
        existing_articles=existing_articles
    )
    assert result_new["exists"] is False
    assert result_new["matched_content_id"] is None
