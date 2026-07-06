from pydantic import BaseModel, Field


class CategorySyncRequest(BaseModel):
    store_name: str = Field(default="", description="Target Shopify store domain.")
    mode: str = Field(default="dry-run", description="Execution mode: dry-run or apply.")
    source: str = Field(default="manual", description="Category source provider or pipeline.")
    product_query: str = Field(default="", description="Optional Shopify product query.")
    candidate_category: str = Field(default="", description="Candidate category label or taxonomy path.")
    max_items: int = Field(default=0, ge=0, description="Optional max number of products to inspect.")
    product_ids: list[str] = Field(default_factory=list, description="Optional explicit Shopify product ids.")
    exclude_product_ids: list[str] = Field(
        default_factory=list,
        description="Optional Shopify product ids to skip, used by resume checkpoints.",
    )
    shopify_suggestions: dict[str, dict] = Field(
        default_factory=dict,
        description="Optional externally collected Shopify suggestions keyed by product id.",
    )
    apply_metafields: bool = Field(
        default=True,
        description="Whether apply mode should attempt to write resolved category metafields.",
    )
    force_apply_review_items: bool = Field(
        default=False,
        description="Whether apply mode should bypass manual review gating and attempt to write high-risk decisions.",
    )
